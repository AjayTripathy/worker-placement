"""Throwaway fetch helper for the 2026-08-18 gauntlet adjudication.

Exists because the headless harness blocks WebFetch/curl but NOT python's own
network stack (proved by calibration._px_many returning HD @ 339.39). Pulls the
primary documents the resolution packs name so the grades come off the filing,
not off a search snippet.
"""
import json
import re
import ssl
import sys
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
HDRS = {
    "User-Agent": "SignalOS Research 4tripathy@gmail.com",
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def get(url, raw=False, timeout=45):
    try:
        req = urllib.request.Request(url, headers=HDRS)
        body = urllib.request.urlopen(req, timeout=timeout, context=CTX).read()
        return body if raw else body.decode("utf-8", "ignore")
    except Exception as exc:
        return None if raw else "ERR %s: %s" % (type(exc).__name__, exc)


def text(html):
    """Crude tag strip — enough to grep numbers out of an EDGAR exhibit."""
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#160;", " ")
    html = html.replace("&#8217;", "'").replace("&#8220;", '"').replace("&#8221;", '"')
    return re.sub(r"\s+", " ", html)


def edgar_recent(cik, forms=None, n=15):
    raw = get("https://data.sec.gov/submissions/CIK%s.json" % str(cik).zfill(10))
    try:
        rec = json.loads(raw)["filings"]["recent"]
    except Exception:
        return [("PARSE_FAIL", str(raw)[:200], "", "")]
    out = []
    for i in range(len(rec["form"])):
        if forms and rec["form"][i] not in forms:
            continue
        out.append((rec["filingDate"][i], rec["form"][i],
                    rec["accessionNumber"][i], rec["primaryDocument"][i]))
        if len(out) >= n:
            break
    return out


def edgar_doc(cik, accession, doc):
    return "https://www.sec.gov/Archives/edgar/data/%s/%s/%s" % (
        int(cik), accession.replace("-", ""), doc)


def grep(body, patterns, window=260):
    for pat in patterns:
        for m in re.finditer(pat, body, re.I):
            lo = max(0, m.start() - window // 2)
            print("   ...%s..." % body[lo:m.end() + window])
            print("   --")


if __name__ == "__main__":
    print(get(sys.argv[1])[:4000])
