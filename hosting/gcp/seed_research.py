"""Package a reviewed Git revision of shared research; never read a live office."""
import argparse
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

try:
    from .research_privacy import AccountRedactor
except ImportError:
    from research_privacy import AccountRedactor

ROOT=Path(__file__).resolve().parents[2]
EXCLUDED=re.compile(r'(?:^|/)(?:\.[^/]*|[^/]*(?:credential|password|secret|api[_-]?key|(?:^|_)token)[^/]*)(?:/|$)',re.I)
SECRET=re.compile(rb'(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|["\x27](?:api_key|access_token|refresh_token|password)["\x27]\s*[:=]\s*["\x27][A-Za-z0-9_./+\-=]{24,}["\x27])')


def build(destination,revision='HEAD'):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    revision=subprocess.check_output(['git','rev-parse',revision],cwd=ROOT,text=True).strip()
    rows=subprocess.check_output(['git','ls-tree','-r','-l',revision,'verticals','strategies'],cwd=ROOT,text=True).splitlines()
    groups=defaultdict(list);excluded=[]
    for row in rows:
        meta,path=row.split('\t',1);mode,kind,oid,size=meta.split()
        if kind!='blob' or mode=='120000' or EXCLUDED.search(path) or Path(path).suffix in {'.log','.pyc'}:
            excluded.append({'path':path,'reason':'not a shared research document'});continue
        area='/'.join(path.split('/')[:2]) if len(path.split('/'))>2 else path.split('/')[0]
        groups[area].append((path,oid,int(size)))
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    catalog={'v':1,'revision':revision,'created_at':datetime.now(timezone.utc).isoformat(),'areas':[],'excluded_count':0,'account_redactions':0}
    # The operator's private registry supplies confirmed brokerage identifiers.
    # Do not mistake public property IDs, dataset keys or tickers for accounts.
    registry=json.loads(subprocess.check_output(['git','show',revision+':desk/data/accounts.json'],cwd=ROOT))
    identifiers=[r['account_id'] for r in registry['accounts'].values() if r.get('account_id')]
    redactor=AccountRedactor(identifiers)
    for area,items in sorted(groups.items()):
        aid=area.replace('/','--');entries=[];archive=destination/(aid+'.zip')
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
            for name,oid,size in items:
                process.stdin.write((oid+'\n').encode());process.stdin.flush()
                header=process.stdout.readline().split()
                data=process.stdout.read(int(header[2]));process.stdout.read(1)
                if SECRET.search(data):
                    excluded.append({'path':name,'reason':'credential-shaped content; needs review'});continue
                try:
                    public_name,_=redactor.clean(name.encode())
                    data,count=redactor.clean(data)
                except ValueError:
                    excluded.append({'path':name,'reason':'account identifier in binary content; needs review'});continue
                name=public_name.decode()
                catalog['account_redactions']+=count
                z.writestr(name,data)
                entries.append({'path':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        (destination/(aid+'.json')).write_text(json.dumps(entries,separators=(',',':')))
        catalog['areas'].append({'id':aid,'title':area,'files':len(entries),'bytes':sum(e['size'] for e in entries),'archive_bytes':archive.stat().st_size})
        print(area,len(entries),'files',flush=True)
    process.stdin.close();process.wait()
    catalog['excluded_count']=len(excluded)
    (destination/'catalog.json').write_text(json.dumps(catalog,indent=2))
    # Kept outside published directory for operator review; never includes values.
    destination.with_suffix('.excluded.json').write_text(json.dumps(excluded,indent=2))
    return catalog

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination');p.add_argument('--revision',default='HEAD');a=p.parse_args()
    c=build(a.destination,a.revision)
    print('Ready:',sum(x['files'] for x in c['areas']),'files;',c['excluded_count'],'excluded for review')
