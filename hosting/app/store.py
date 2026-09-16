"""Durable compare-and-swap documents with per-object envelope encryption."""
import base64
import json
import os
from .auth import AuthFailure

class Conflict(Exception): pass

class CloudStore:
    def __init__(self, bucket, key):
        from google.cloud import storage, kms
        self.bucket = storage.Client().bucket(bucket)
        self.kms = kms.KeyManagementServiceClient()
        self.key = key

    def _seal(self, name, value):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        dek = AESGCM.generate_key(bit_length=256); nonce=os.urandom(12)
        wrapped=self.kms.encrypt(request={'name':self.key,'plaintext':dek,'additional_authenticated_data':name.encode()}).ciphertext
        raw=json.dumps(value,separators=(',',':'),allow_nan=False).encode()
        cipher=AESGCM(dek).encrypt(nonce,raw,name.encode())
        return json.dumps({'v':1,'key':base64.b64encode(wrapped).decode(),'nonce':base64.b64encode(nonce).decode(),'body':base64.b64encode(cipher).decode()}).encode()

    def _open(self,name,raw):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        value=json.loads(raw)
        dek=self.kms.decrypt(request={'name':self.key,'ciphertext':base64.b64decode(value['key']),'additional_authenticated_data':name.encode()}).plaintext
        return json.loads(AESGCM(dek).decrypt(base64.b64decode(value['nonce']),base64.b64decode(value['body']),name.encode()))

    def get(self,name):
        from google.api_core.exceptions import NotFound,PreconditionFailed
        for attempt in range(3):
            b=self.bucket.blob(name)
            try:
                b.reload()
                return self._open(name,b.download_as_bytes(if_generation_match=b.generation)),int(b.generation)
            except NotFound:return None,0
            except PreconditionFailed:continue
        raise AuthFailure('The office is busy. Retry shortly.',409)

    def put(self,name,value,generation=0):
        from google.api_core.exceptions import PreconditionFailed
        try:self.bucket.blob(name).upload_from_string(self._seal(name,value),content_type='application/json',if_generation_match=generation)
        except PreconditionFailed:raise Conflict() from None

    def names(self,prefix):
        return [b.name for b in self.bucket.list_blobs(prefix=prefix)]


def required_store(store):
    if store is None:raise AuthFailure('Cloud storage is being configured. Please try again shortly.',503)
    return store
