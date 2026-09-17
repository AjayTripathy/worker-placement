"""Cross-account boundaries, immutable activation and resumable device/migration flows."""
import base64
from copy import deepcopy
import json
import threading
import time
import uuid
import pytest
from fastapi.testclient import TestClient
from hosting.app.main import create_app,CSRF,SESSION
from hosting.app.auth import AuthFailure
from hosting.app.offices import Offices
from hosting.app.store import Conflict
from officekit.migration import snapshot,validate_manifest,canonical,digest,validate_documents

ORIGIN='https://office.example'

class MemoryStore:
    def __init__(self):self.rows={};self.lock=threading.Lock()
    def get(self,key):return deepcopy(self.rows.get(key,(None,0)))
    def put(self,key,value,generation=0):
        with self.lock:
            actual=self.rows.get(key,(None,0))[1]
            if generation!=actual:raise Conflict()
            self.rows[key]=(deepcopy(value),actual+1)
    def names(self,prefix):return [p for p in self.rows if p.startswith(prefix)]

class Backend:
    def verify(self,cookie):
        if cookie not in {'alice','bob'}:raise AuthFailure('Sign in.',401)
        return {'uid':cookie,'email':cookie+'@example.com','email_verified':True,'exp':time.time()+3600}

@pytest.fixture
def office(tmp_path):
    from officekit.intake import build_from_answers
    folder=tmp_path/'office';folder.mkdir()
    answers={'office_id':str(uuid.uuid4()),'owner':'Test household','as_of':'2026-09-15','profile':{},'positions':{'rows':[{'symbol':'CASH','value':10000,'category':'cash'}]},'goals':[]}
    data=build_from_answers(answers)
    (folder/'answers.json').write_text(json.dumps(answers));(folder/'balance_sheet.json').write_text(json.dumps(data))
    (folder/'personal_context.json').write_text(json.dumps({'private':'only Alice'}))
    (folder/'research').mkdir();(folder/'research'/'memo.md').write_text('Retained diligence')
    return folder

@pytest.fixture
def client():
    store=MemoryStore()
    with TestClient(create_app(Backend(),ORIGIN,store=store),base_url=ORIGIN) as c:
        c.store=store
        yield c

def send(c,path,data,who='alice'):
    return c.post(path,json=data,headers={'Authorization':'Bearer '+who})

def upload(c,folder,who='alice'):
    m,chunks=snapshot(folder)
    r=send(c,'/api/migrations',{'manifest':m},who);assert r.status_code==200,r.text
    sid=r.json()['digest']
    for h in r.json()['missing']:
        assert send(c,'/api/migrations/'+sid+'/chunks',{'sha256':h,'data':base64.b64encode(chunks[h]).decode()},who).status_code==200
    return m,sid

def test_resumable_immutable_private_activation_and_export(client,office):
    m,sid=upload(client,office)
    assert send(client,'/api/migrations',{'manifest':m}).json()['missing']==[]
    r=send(client,'/api/migrations/'+sid+'/activate',{})
    assert r.status_code==200,r.text
    receipt=r.json()
    assert send(client,'/api/migrations/'+sid+'/activate',{}).json()==receipt
    assert client.get(receipt['path'],headers={'Authorization':'Bearer alice'}).status_code==200
    assert client.get(receipt['path'],headers={'Authorization':'Bearer bob'}).status_code==404
    assert send(client,'/api/migrations/'+sid+'/activate',{},'bob').status_code==404
    assert client.get('/api/offices',headers={'Authorization':'Bearer bob'}).json()=={'offices':[]}
    assert client.get(receipt['path']+'/document',params={'path':'personal_context.json'},headers={'Authorization':'Bearer alice'}).content==b'{"private": "only Alice"}'
    assert client.get(receipt['path']+'/document',params={'path':'personal_context.json'},headers={'Authorization':'Bearer bob'}).status_code==404
    exported=client.get(receipt['path']+'/export',headers={'Authorization':'Bearer alice'})
    import zipfile,io
    with zipfile.ZipFile(io.BytesIO(exported.content)) as z:
        assert z.read('balance_sheet.json')==(office/'balance_sheet.json').read_bytes()
        assert z.read('research/memo.md')==b'Retained diligence'

def test_missing_corrupt_chunks_and_revision_conflict(client,office):
    manifest,chunks=snapshot(office)
    sid=send(client,'/api/migrations',{'manifest':manifest}).json()['digest']
    assert send(client,'/api/migrations/'+sid+'/activate',{}).status_code==409
    h=next(iter(chunks))
    assert send(client,'/api/migrations/'+sid+'/chunks',{'sha256':h,'data':base64.b64encode(b'wrong').decode()}).status_code==400
    _,sid=upload(client,office);assert send(client,'/api/migrations/'+sid+'/activate',{}).status_code==200
    (office/'research'/'memo.md').write_text('A new retained finding')
    _,new=upload(client,office)
    assert new!=sid
    assert send(client,'/api/migrations/'+new+'/activate',{}).status_code==409
    assert send(client,'/api/migrations/'+new+'/activate',{'replace_revision':'wrong'}).status_code==409
    assert send(client,'/api/migrations/'+new+'/activate',{'replace_revision':sid}).status_code==200
    assert send(client,'/api/migrations/'+sid+'/activate',{}).status_code==409

def test_browser_cookie_cannot_trigger_migration(client,office):
    client.cookies.set(SESSION,'alice')
    m,_=snapshot(office)
    assert client.post('/api/migrations',json={'manifest':m}).status_code==401

def test_device_needs_browser_approval_matching_code_and_local_proof(client):
    proof='x'*64
    r=client.post('/api/cli/start',json={'proof':proof});assert r.status_code==200
    d=r.json()
    assert client.post('/api/cli/poll',json={'device':d['device'],'proof':proof}).json()=={'status':'pending'}
    assert client.post('/api/cli/poll',json={'device':d['device'],'proof':'y'*64}).status_code==403
    assert client.post('/api/cli/approve',json={'device':d['device'],'code':d['code']}).status_code==403
    client.cookies.set(SESSION,'alice');client.get(d['url'])
    headers={'Origin':ORIGIN,'X-CSRF-Token':client.cookies.get(CSRF)}
    assert client.post('/api/cli/approve',json={'device':d['device'],'code':'BAD'},headers=headers).status_code==403
    assert client.post('/api/cli/approve',json={'device':d['device'],'code':d['code']},headers=headers).status_code==200
    approved=client.post('/api/cli/poll',json={'device':d['device'],'proof':proof}).json()
    assert approved['email']=='alice@example.com' and approved['token']=='alice'
    client.cookies.set(SESSION,'bob')
    assert client.post('/api/cli/approve',json={'device':d['device'],'code':d['code']},headers=headers).status_code==409

def test_expired_device_cannot_be_approved(client):
    d=client.post('/api/cli/start',json={'proof':'x'*64}).json()
    key='devices/'+d['device'];value,g=client.store.get(key);value['expires']=0;client.store.put(key,value,g)
    assert client.post('/api/cli/poll',json={'device':d['device'],'proof':'x'*64}).status_code==410

def test_snapshot_excludes_credentials_pages_and_unrelated_repo(office):
    (office/'.env').write_text('SECRET=value');(office/'pages').mkdir();(office/'pages'/'office.html').write_text('<script>bad</script>')
    (office/'login.json').write_text('{"token":"private"}');(office/'unrelated.py').write_text('raise Exception()')
    m,_=snapshot(office)
    assert {f['path'] for f in m['files']}=={'answers.json','balance_sheet.json','personal_context.json','research/memo.md'}

def test_symlinks_and_embedded_secrets_fail(office,tmp_path):
    target=tmp_path/'private.txt';target.write_text('private')
    (office/'research'/'external.txt').symlink_to(target)
    with pytest.raises(ValueError,match='Symlink'):snapshot(office)
    (office/'research'/'external.txt').unlink()
    (office/'research'/'memo.md').write_text('sk-ant-'+'x'*30)
    with pytest.raises(ValueError,match='credential'):snapshot(office)

@pytest.mark.parametrize('path',['../answers.json','/answers.json','research/../answers.json','research/evil.html','research\\x.json','research/.env'])
def test_manifest_traversal_and_executable_content_rejected(office,path):
    m,_=snapshot(office);m['files'][0]['path']=path
    with pytest.raises(ValueError):validate_manifest(m)

def test_snapshot_waits_for_writer_transaction(office):
    from officekit.office_lock import locked
    acquired=threading.Event();release=threading.Event();done=threading.Event()
    def writer():
        with locked(office):acquired.set();release.wait(5)
    t=threading.Thread(target=writer);t.start();assert acquired.wait(2)
    def reader():snapshot(office);done.set()
    r=threading.Thread(target=reader);r.start()
    assert not done.wait(.1)
    release.set();t.join(3);r.join(3);assert done.is_set()

def test_unverified_cookie_cannot_access_shared_research(client):
    assert client.get('/app/research',follow_redirects=False).status_code==303
    assert client.get('/app/research/document').status_code==401

@pytest.mark.parametrize('data',[b'{"amount":1e999}',b'{"amount":NaN}',b'{"amount":1,"amount":2}',b'{"nested":{"api_key":"private-value"}}'])
def test_invalid_numbers_duplicate_fields_and_credentials_refused(office,data):
    (office/'research'/'bad.json').write_bytes(data)
    with pytest.raises(ValueError):snapshot(office)


def test_snapshot_cross_process_barrier(office):
    import subprocess,sys
    from officekit.office_lock import locked
    code='from pathlib import Path; from officekit.office_lock import locked; import sys; print("waiting",flush=True);\nwith locked(Path(sys.argv[1])): print("acquired",flush=True)'
    with locked(office):
        process=subprocess.Popen([sys.executable,'-c',code,str(office)],stdout=subprocess.PIPE,text=True)
        assert process.stdout.readline().strip()=='waiting'
        time.sleep(.1)
        assert process.poll() is None
    output,_=process.communicate(timeout=5)
    assert process.returncode==0 and output.strip()=='acquired'


def test_envelope_integrity_binds_object_identity():
    from types import SimpleNamespace
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
    from hosting.app.store import CloudStore
    master=AESGCM.generate_key(bit_length=256)
    class KMS:
        def encrypt(self,request):
            return SimpleNamespace(ciphertext=AESGCM(master).encrypt(b'0'*12,request['plaintext'],request['additional_authenticated_data']))
        def decrypt(self,request):
            return SimpleNamespace(plaintext=AESGCM(master).decrypt(b'0'*12,request['ciphertext'],request['additional_authenticated_data']))
    store=object.__new__(CloudStore);store.kms=KMS();store.key='test-key'
    sealed=store._seal('alice/office',{'private':'financial facts'})
    assert b'financial facts' not in sealed
    assert store._open('alice/office',sealed)=={'private':'financial facts'}
    with pytest.raises(InvalidTag):store._open('bob/office',sealed)
    altered=json.loads(sealed);raw=bytearray(base64.b64decode(altered['body']));raw[0]^=1
    altered['body']=base64.b64encode(raw).decode()
    with pytest.raises(InvalidTag):store._open('alice/office',json.dumps(altered).encode())


def test_cli_refuses_mismatched_receipt(office,monkeypatch):
    from officekit import cloud
    m,_=snapshot(office)
    monkeypatch.setattr(cloud,'credentials',lambda:{'origin':ORIGIN,'token':'private'})
    def request(origin,path,payload=None,token=None):
        if path=='/api/me':return {'email':'alice@example.com'}
        if path=='/api/migrations':return {'digest':validate_manifest(m),'missing':[]}
        return {'digest':'wrong','office_id':m['office_id'],'status':'active'}
    monkeypatch.setattr(cloud,'request',request)
    with pytest.raises(ValueError,match='receipt'):cloud.migrate(office,open_browser=False)
    assert not (office/'.hosted-receipt.json').exists()


def test_local_credential_permissions_and_exclusion(office,monkeypatch):
    from officekit import cloud
    monkeypatch.setenv('WORKER_PLACEMENT_CONFIG_DIR',str(office/'.config'))
    cloud.save_private(cloud.config_path(),{'token':'private'})
    assert cloud.config_path().stat().st_mode & 0o777==0o600
    assert all('.config' not in f['path'] for f in snapshot(office)[0]['files'])
