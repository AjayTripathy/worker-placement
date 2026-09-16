"""Tenant-scoped device grants and immutable, verified office revisions."""
import base64
from datetime import datetime, timezone
import hashlib
import hmac
import re
import secrets
import time
import uuid
from .auth import AuthFailure
from .store import Conflict, required_store
from officekit.migration import canonical, digest, CHUNK, validate_manifest, validate_documents


def identifier(value, pattern='[a-f0-9]{64}'):
    if not isinstance(value,str) or not re.fullmatch(pattern,value):raise AuthFailure('Invalid request identifier.')
    return value

def tenant(uid):return hashlib.sha256(uid.encode()).hexdigest()

def stamp():return datetime.now(timezone.utc).isoformat()

class Offices:
    def __init__(self,store):self.store=store

    def db(self):return required_store(self.store)

    def start(self,proof,origin):
        identifier(proof,'[A-Za-z0-9_-]{64}')
        device=str(uuid.uuid4());code=secrets.token_hex(4).upper()
        self.db().put('devices/'+device,{'proof':digest(proof.encode()),'code':code,'expires':time.time()+900,'status':'pending'})
        return {'device':device,'code':code,'url':origin+'/cli?device='+device+'&code='+code}

    def device(self,device):
        identifier(device,'[a-f0-9-]{36}')
        value,generation=self.db().get('devices/'+device)
        if value is None or value['expires']<time.time():raise AuthFailure('This device request expired. Run ./wp login again.',410)
        return value,generation

    def approve(self,device,code,claims,cookie):
        value,generation=self.device(device)
        if not isinstance(code,str) or not hmac.compare_digest(code,value['code']):raise AuthFailure('The device code does not match.',403)
        if value['status']=='approved':
            if value['uid']!=claims['uid']:raise AuthFailure('This request was already approved by another account.',409)
            return {'status':'approved'}
        value.update(status='approved',uid=claims['uid'],email=claims['email'],token=cookie,expires_at=claims.get('exp',time.time()+300))
        try:self.db().put('devices/'+device,value,generation)
        except Conflict:raise AuthFailure('This request changed. Reload and review it.',409) from None
        return {'status':'approved'}

    def poll(self,device,proof):
        identifier(proof,'[A-Za-z0-9_-]{64}')
        value,_=self.device(device)
        if not hmac.compare_digest(value['proof'],digest(proof.encode())):raise AuthFailure('Invalid device proof.',403)
        if value['status']=='approved':
            return {k:value[k] for k in ('status','email','token','expires_at')}
        return {'status':'pending'}

    def transfer_key(self,uid,sid):
        return 'transfers/'+tenant(uid)+'/'+identifier(sid)+'/'

    def transfer(self,uid,sid):
        key=self.transfer_key(uid,sid);value,_=self.db().get(key+'manifest')
        if value is None or value['expires']<time.time():raise AuthFailure('This upload expired. Run ./wp migrate again.',404)
        return key,value

    def begin(self,uid,manifest):
        try:sid=validate_manifest(manifest)
        except (ValueError,TypeError,AttributeError):raise AuthFailure('The migration manifest is invalid or unsupported.') from None
        key=self.transfer_key(uid,sid)
        old,generation=self.db().get(key+'manifest')
        if old is None or old['expires']<time.time():
            try:self.db().put(key+'manifest',{'manifest':manifest,'expires':time.time()+86400},generation)
            except Conflict:pass
        chunks={h for f in manifest['files'] for h in f['chunks']}
        existing={p.rsplit('/',1)[-1] for p in self.db().names(key+'chunks/')}
        return {'digest':sid,'missing':sorted(chunks-existing)}

    def upload(self,uid,sid,h,encoded):
        key,value=self.transfer(uid,sid);identifier(h)
        if h not in {c for f in value['manifest']['files'] for c in f['chunks']}:raise AuthFailure('This chunk is not part of the approved manifest.')
        try:data=base64.b64decode(encoded,validate=True)
        except (ValueError,TypeError):raise AuthFailure('Invalid upload encoding.') from None
        if len(data)>CHUNK or digest(data)!=h:raise AuthFailure('Upload checksum mismatch.')
        try:self.db().put(key+'chunks/'+h,{'data':encoded})
        except Conflict:pass
        return {'status':'stored'}

    def prefix(self,uid,oid):
        try:oid=str(uuid.UUID(oid))
        except (ValueError,AttributeError,TypeError):raise AuthFailure('Invalid office identity.') from None
        return 'offices/'+tenant(uid)+'/'+oid+'/'

    def activate(self,uid,sid,replace_revision=None):
        key,transfer=self.transfer(uid,sid);manifest=transfer['manifest'];oid=manifest['office_id'];prefix=self.prefix(uid,oid)
        current,generation=self.db().get(prefix+'active')
        if current and current['digest']==sid:return current
        if current and replace_revision!=current['digest']:
            raise AuthFailure('This office already has a different hosted revision. Review it, then use --replace-revision '+current['digest']+' if you intend to replace it.',409)
        if not current and replace_revision is not None:raise AuthFailure('The hosted revision no longer matches your replacement request.',409)
        documents={}
        for f in manifest['files']:
            parts=[]
            for h in f['chunks']:
                value,_=self.db().get(key+'chunks/'+h)
                if value is None:raise AuthFailure('The upload is incomplete. Rerun ./wp migrate to resume.',409)
                data=base64.b64decode(value['data'])
                if digest(data)!=h:raise AuthFailure('A stored upload failed its integrity check.',409)
                parts.append(data)
            documents[f['path']]=b''.join(parts)
        try:parsed=validate_documents(manifest,documents)
        except (ValueError,TypeError,AttributeError):raise AuthFailure('The uploaded office failed document, identity or financial validation. Rebuild locally and retry.') from None
        record={'manifest':manifest,'documents':{n:base64.b64encode(b).decode() for n,b in documents.items()}}
        try:self.db().put(prefix+'revisions/'+sid,record)
        except Conflict:pass
        a=parsed['answers.json'];name=a.get('owner') or 'Your office'
        if not isinstance(name,str):name='Your office'
        receipt={'status':'active','office_id':oid,'digest':sid,'activated_at':stamp(),'path':'/app/offices/'+oid,
                 'name':name[:180], 'as_of':parsed['balance_sheet.json']['as_of'],'documents':len(documents)}
        try:self.db().put(prefix+'active',receipt,generation)
        except Conflict:
            winner,_=self.db().get(prefix+'active')
            if winner and winner['digest']==sid:return winner
            raise AuthFailure('Another upload changed the hosted office. Reload and review before replacing it.',409) from None
        return receipt

    def listing(self,uid):
        rows=[]
        for name in self.db().names('offices/'+tenant(uid)+'/'):
            if name.endswith('/active'):
                value,_=self.db().get(name)
                if value:rows.append(value)
        return sorted(rows,key=lambda r:r['activated_at'],reverse=True)

    def read(self,uid,oid):
        prefix=self.prefix(uid,oid);receipt,_=self.db().get(prefix+'active')
        if receipt is None:raise AuthFailure('Office not found.',404)
        record,_=self.db().get(prefix+'revisions/'+receipt['digest'])
        if record is None:raise AuthFailure('The office could not be loaded. Try again shortly.',503)
        return receipt,record
