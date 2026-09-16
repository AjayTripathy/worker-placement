"""Shared, immutable research library. Files are data, never executed."""
import json
import os
import re
import time
import zipfile
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
