"""formdata — a FieldStorage-compatible POST-body parser (A0 packaging).

The stdlib `cgi` module was removed in Python 3.13 (PEP 594); serve.py needs
four behaviors from it — getvalue/getlist, `name in form` / form[name], file
parts with .filename/.file, and keep_blank_values semantics — so this shim
provides them for urlencoded and multipart bodies with no third-party
dependency. Blank values are ALWAYS kept: the aligned-array form parsers
(sleeves, holdings, goals) rely on positional correspondence, and silently
dropping a blank field desyncs every list (the goals-row lesson).
"""
from __future__ import annotations

import email
import email.policy
import io
from urllib.parse import parse_qsl


class FilePart:
    """A multipart file field: .filename + .file (BytesIO), like cgi's."""

    def __init__(self, filename, data):
        self.filename = filename
        self.file = io.BytesIO(data)


class Form:
    def __init__(self, fields):
        self._fields = fields                      # {name: [str|FilePart, ...]} in arrival order

    def __contains__(self, key):
        return key in self._fields

    def __getitem__(self, key):
        return self._fields[key][0]

    def getvalue(self, key, default=None):
        v = self._fields.get(key)
        if not v:
            return default
        return v[0].file.getvalue() if isinstance(v[0], FilePart) else v[0]

    def getlist(self, key):
        return [x.file.getvalue() if isinstance(x, FilePart) else x
                for x in self._fields.get(key, [])]

    def getparts(self, key):
        """Raw FileParts for a multi-file field (filename + bytes intact)."""
        return [x for x in self._fields.get(key, []) if isinstance(x, FilePart)]


def parse(rfile, headers):
    """Read and parse a POST body from an http.server handler. Returns a Form."""
    ctype = headers.get("Content-Type", "") or ""
    try:
        length = int(headers.get("Content-Length") or 0)
    except ValueError:
        length = 0
    body = rfile.read(length) if length > 0 else b""
    fields = {}
    if ctype.lower().startswith("multipart/form-data"):
        msg = email.message_from_bytes(
            b"Content-Type: " + ctype.encode("latin-1") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body,
            policy=email.policy.HTTP)
        if not msg.is_multipart():                 # malformed boundary — nothing to salvage
            return Form(fields)
        for part in msg.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if name is None:
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                payload = b""
            filename = part.get_filename()
            if filename:
                fields.setdefault(name, []).append(FilePart(filename, payload))
            else:
                fields.setdefault(name, []).append(payload.decode("utf-8", "replace"))
    else:
        for k, v in parse_qsl(body.decode("utf-8", "replace"), keep_blank_values=True):
            fields.setdefault(k, []).append(v)
    return Form(fields)
