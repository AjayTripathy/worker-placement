"""Immutable, allowlisted office snapshots. No credentials or executable pages."""
import base64
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import uuid

VERSION = 1
CHUNK = 1024 * 1024
MAX_TOTAL = 64 * CHUNK
MAX_FILES = 1024
ROOT_FILES = {'answers.json', 'balance_sheet.json', 'personal_context.json', 'staging.json',
              'parametric_scorecard.json', 'fund_map_learned.json', 'docket.json', 'adjudications.jsonl',
              'learning.jsonl', 'signals_state.json', 'signals_runs.jsonl', 'draft.json', 'models.json', 'positions.csv'}
RETAINED = {'research', 'attachments', 'documents', 'transcripts', 'strategy_proposals'}
SUFFIXES = {'.json', '.jsonl', '.md', '.txt', '.csv', '.pdf', '.png', '.jpg', '.jpeg', '.webp'}
SECRET = re.compile(rb'(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def safe_path(name):
    if not isinstance(name, str):return False
    p = PurePosixPath(name)
    if not isinstance(name, str) or not name or '\\' in name or p.is_absolute() or str(p) != name or any(x in {'.','..'} or x.startswith('.') for x in p.parts):
        return False
    if len(p.parts) == 1:
        return name in ROOT_FILES
    return p.parts[0] in RETAINED and p.suffix.lower() in SUFFIXES and not re.search(r'(?:credential|secret|token|api.?key)', name, re.I)

def parse_json(data):
    def bad(value): raise ValueError('Non-finite values are not valid office data')
    def finite(value):
        number = float(value)
        if not math.isfinite(number): bad(value)
        return number
    def fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('Duplicate fields are not valid office data')
            if re.fullmatch(r'(?:api_?key|access_?token|refresh_?token|password|client_?secret|private_?key)', key, re.I) and value:
                raise ValueError('Office data contains a credential field; remove it before migrating.')
            result[key] = value
        return result
    return json.loads(data, parse_constant=bad, parse_float=finite, object_pairs_hook=fields)

def inspect_document(name, data):
    if SECRET.search(data):
        raise ValueError(f'{name} contains credential-shaped text; remove it before migrating.')
    if name.endswith('.json'):
        value = parse_json(data)
        if name == 'models.json':
            from officekit_ai.models import validate
            problems = validate(value)
            if problems: raise ValueError('Model configuration contains unsupported or credential fields.')
        return value
    if name.endswith('.jsonl'):
        for line in data.splitlines():
            if line.strip(): parse_json(line)
    return None

def validate_manifest(manifest):
    if not isinstance(manifest, dict) or type(manifest.get('v')) is not int or manifest.get('v') != VERSION:
        raise ValueError('Unsupported migration version.')
    try: uuid.UUID(manifest['office_id'])
    except (ValueError, KeyError, TypeError, AttributeError): raise ValueError('A built office with a stable identity is required.') from None
    files = manifest.get('files')
    if not isinstance(files, list) or not 2 <= len(files) <= MAX_FILES:
        raise ValueError('Unsupported office file count.')
    names = set();total = 0
    for f in files:
        if not isinstance(f,dict) or not safe_path(f.get('path','')) or f['path'] in names:
            raise ValueError('Unsupported or duplicate office document path.')
        names.add(f['path'])
        if type(f.get('size')) is not int or not 0 <= f['size'] <= MAX_TOTAL:
            raise ValueError('Invalid document size.')
        total += f['size']
        if not re.fullmatch('[a-f0-9]{64}',str(f.get('sha256',''))):raise ValueError('Invalid document digest.')
        chunks=f.get('chunks')
        if not isinstance(chunks,list) or len(chunks) != (f['size']+CHUNK-1)//CHUNK or any(not isinstance(c,str) or not re.fullmatch('[a-f0-9]{64}',c) for c in chunks):
            raise ValueError('Invalid document chunks.')
    if not {'answers.json','balance_sheet.json'} <= names or total > MAX_TOTAL:
        raise ValueError('Office data must include answers and balances and fit within 64 MiB.')
    return digest(canonical(manifest))

def validate_documents(manifest, documents):
    validate_manifest(manifest)
    if set(documents) != {f['path'] for f in manifest['files']}:raise ValueError('The office snapshot is incomplete.')
    parsed = {}
    for f in manifest['files']:
        data = documents[f['path']]
        if len(data)!=f['size'] or digest(data)!=f['sha256']:raise ValueError('Document integrity check failed.')
        parsed[f['path']] = inspect_document(f['path'],data)
    answers, balance = parsed['answers.json'], parsed['balance_sheet.json']
    if not isinstance(answers,dict) or not isinstance(balance,dict) or answers.get('office_id') != manifest['office_id'] or balance.get('office_id') != manifest['office_id']:
        raise ValueError('Office identities do not match.')
    from officekit.schema import validate
    if validate(balance):raise ValueError('The saved balance sheet does not satisfy the office schema.')
    if answers.get('as_of') != balance.get('as_of'):raise ValueError('Answers and balances have different as-of dates; rebuild locally first.')
    # Preserve the saved financial model exactly; never resolve external paths or
    # re-import an absolute CSV path supplied by a customer.
    return parsed

def snapshot(folder):
    from officekit.office_lock import locked
    folder = Path(folder).resolve()
    with locked(folder):
        documents={}; fingerprints={}
        for path in sorted(folder.rglob('*')):
            name=path.relative_to(folder).as_posix()
            if not safe_path(name):continue
            if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != folder.parent):
                raise ValueError('Symlinks cannot be migrated.')
            if not path.is_file():continue
            st=path.stat()
            if st.st_size>MAX_TOTAL:raise ValueError('A retained document exceeds the 64 MiB migration limit.')
            data=path.read_bytes();inspect_document(name,data)
            documents[name]=data;fingerprints[name]=(st.st_ino,st.st_size,st.st_mtime_ns)
            if sum(map(len,documents.values()))>MAX_TOTAL:raise ValueError('This office exceeds the 64 MiB migration limit.')
        for name,expected in fingerprints.items():
            st=(folder/name).stat()
            if (st.st_ino,st.st_size,st.st_mtime_ns)!=expected or (folder/name).read_bytes()!=documents[name]:
                raise ValueError('The office changed during migration. Wait for active work to finish and retry.')
        current = {p.relative_to(folder).as_posix() for p in folder.rglob('*')
                   if safe_path(p.relative_to(folder).as_posix()) and p.is_file()}
        if current != set(documents):
            raise ValueError('The office changed during migration. Wait for active work to finish and retry.')
        if 'answers.json' not in documents or 'balance_sheet.json' not in documents:raise ValueError('Build your local office before migrating it.')
        answers=parse_json(documents['answers.json'])
        chunks={}; files=[]
        for name,data in documents.items():
            parts=[]
            for offset in range(0,len(data),CHUNK):
                part=data[offset:offset+CHUNK];h=digest(part);chunks[h]=part;parts.append(h)
            files.append({'path':name,'size':len(data),'sha256':digest(data),'chunks':parts})
        manifest={'v':VERSION,'office_id':answers.get('office_id'),'files':files}
        validate_documents(manifest,documents)
        return manifest,chunks
