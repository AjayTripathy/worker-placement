"""Shared, immutable research library. Files are data, never executed."""
import json
import os
import re
import time
import zipfile
from pathlib import PurePosixPath
from urllib.parse import urlencode
from .auth import AuthFailure

class Research:
    def __init__(self,bucket,version):
        from google.cloud import storage
        self.bucket=storage.Client().bucket(bucket)
        self.version=version
        self.cache={}
    def document(self,name):
        if name not in self.cache:
            self.cache[name]=json.loads(self.bucket.blob(self.version+'/'+name).download_as_bytes())
        return self.cache[name]
    def catalog(self):return self.document('catalog.json')
    def strategy_packs(self):
        """Only published manifests, loaded from the existing reviewed archive."""
        from officekit.strategy_packs import validate
        if hasattr(self, '_packs'):
            return list(self._packs)
        result = []
        for area in self.catalog()['areas']:
            if not area['id'].startswith('strategies--'):
                continue
            entries = self.entries(area['id'])
            paths = {e['path'] for e in entries}
            for entry in entries:
                if entry['path'].endswith('/pack.json') and entry['size'] <= 32768:
                    pack = json.loads(self.read(area['id'], entry['path']))
                    if not validate(pack):
                        deck_name = pack.get('deck', 'DECK.md')
                        deck = str(PurePosixPath(entry['path']).parent / (deck_name if isinstance(deck_name, str) else 'DECK.md'))
                        result.append({**pack, 'source': 'Shared research library: ' + entry['path'],
                                       'source_href': '/app/research/document?' + urlencode({'area': area['id'], 'path': deck if deck in paths else entry['path']}),
                                       'source_sha256': entry['sha256']})
        self._packs = result
        return list(result)
    def search(self, query, symbol=False):
        """Search published metadata across areas without reading archives.

        Symbol links match path tokens, so ABC does not match ABCD. A
        path match is navigation, never evidence or a current verdict.
        """
        query = str(query).strip()[:200]
        if not query:
            return []
        if not hasattr(self, '_search_cache'):
            self._search_cache = {}
        key = (query.lower(), symbol)
        if key in self._search_cache:
            return list(self._search_cache[key])
        if not hasattr(self, '_search_entries'):
            self._search_entries = [{**entry, 'area': area['id']} for area in self.catalog()['areas']
                                    for entry in self.entries(area['id'])]
        pattern = re.compile(r'(?<![A-Za-z0-9])' + re.escape(query).replace(r'\.', r'[._]') + r'(?![A-Za-z0-9])', re.I) if symbol else None
        result = sorted([e for e in self._search_entries if (pattern.search(e['path']) if pattern else query.lower() in e['path'].lower())],
                        key=lambda e: (e['path'], e['area']))
        if len(self._search_cache) >= 128:
            self._search_cache.pop(next(iter(self._search_cache)))
        self._search_cache[key] = result
        return list(result)
    def entries(self,area):
        if area not in {a['id'] for a in self.catalog()['areas']}:raise AuthFailure('Research area not found.',404)
        return self.document(area+'.json')
    def read(self,area,path):
        entry=next((e for e in self.entries(area) if e['path']==path),None)
        if entry is None:raise AuthFailure('Research document not found.',404)
        if entry['size']>100*1024*1024:raise AuthFailure('This research document is too large for an individual browser download.',413)
        blob=self.bucket.blob(self.version+'/'+area+'.zip');blob.reload()
        with blob.open('rb',chunk_size=256*1024) as source:
            with zipfile.ZipFile(source) as archive:data=archive.read(path)
        from officekit.migration import digest
        if digest(data)!=entry['sha256']:raise AuthFailure('Research integrity check failed.',503)
        return data
