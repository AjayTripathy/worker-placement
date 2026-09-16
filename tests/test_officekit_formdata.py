"""formdata — the cgi.FieldStorage replacement (A0; cgi removed in Python 3.13).
The load-bearing behaviors: keep_blank_values (aligned-array parsers), repeated
keys, `in`/`[]` access, and multipart file parts with .filename/.file."""
import io

from officekit import formdata


class H(dict):
    def get(self, k, d=None):
        return super().get(k, d)


def _parse(body, ctype):
    return formdata.parse(io.BytesIO(body),
                          H({"Content-Type": ctype, "Content-Length": str(len(body))}))


def test_urlencoded_keeps_blanks_and_order():
    f = _parse(b"gid=&gid=abc&goal_label=College&goal_label=&sym=VTI",
               "application/x-www-form-urlencoded")
    assert f.getlist("gid") == ["", "abc"]          # blank kept, order kept
    assert f.getlist("goal_label") == ["College", ""]
    assert f.getvalue("sym") == "VTI"
    assert f.getvalue("missing") is None
    assert "sym" in f and "nope" not in f


def test_multipart_file_and_text_fields():
    b = b"BOUNDARYX"
    mp = (b"--" + b + b"\r\n"
          b'Content-Disposition: form-data; name="positions_csv"; filename="p.csv"\r\n'
          b"Content-Type: text/csv\r\n\r\nSymbol,Qty\nVTI,10\r\n"
          b"--" + b + b"\r\n"
          b'Content-Disposition: form-data; name="account"\r\n\r\nbrokerage\r\n'
          b"--" + b + b"\r\n"
          b'Content-Disposition: form-data; name="blank"\r\n\r\n\r\n'
          b"--" + b + b"--\r\n")
    f = _parse(mp, "multipart/form-data; boundary=BOUNDARYX")
    item = f["positions_csv"]                       # the serve.py upload path's exact API
    assert item.filename == "p.csv"
    assert item.file.read() == b"Symbol,Qty\nVTI,10"
    assert f.getvalue("account") == "brokerage"
    assert f.getvalue("blank") == ""


def test_malformed_multipart_degrades_to_empty():
    f = _parse(b"not really multipart", "multipart/form-data; boundary=missing")
    assert f.getvalue("anything") is None


def test_empty_body():
    f = _parse(b"", "application/x-www-form-urlencoded")
    assert f.getlist("x") == []
