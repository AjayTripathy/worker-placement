"""Explicit authenticated exchange transport. Credentials never enter research."""
from urllib.parse import urlsplit

from officekit_research import exchange, general
from officekit_research.admission import check_receipt


class Client:
    def __init__(self, http, bearer):
        # http supplies get/post (httpx or an isolated hosted-app TestClient).
        # The caller owns its lifetime and authenticated origin.
        origin = urlsplit(str(http.base_url))
        if origin.scheme != "https" or not origin.hostname or origin.username or origin.password:
            raise ValueError("Research exchange requires an HTTPS origin")
        self.http = http
        self.headers = {"Authorization": "Bearer " + bearer}

    def request(self, method, path, **kwargs):
        try:
            response = getattr(self.http, method)(path, headers=self.headers, follow_redirects=False, **kwargs)
        except Exception as exc:
            # Keep completed research when publication transport fails. Never
            # echo request URLs, headers or provider exception bodies.
            raise ValueError(f"Hosted research {method} unavailable ({type(exc).__name__})") from None
        if response.status_code != 200:
            # Do not echo bodies, headers or credentials from remote failures.
            raise ValueError(f"Hosted research {method} failed (HTTP {response.status_code})")
        try:
            return response.json()
        except ValueError:
            raise ValueError("Hosted research returned an invalid response") from None

    def submit(self, record, contributor=None):
        if exchange.is_private(record):
            raise ValueError("Private research requires a separate explicit release")
        return self.request("post", "/api/research/general", json={"record": record, "contributor": contributor})

    def find(self, symbol, instrument, protocol_hash, **kwargs):
        import re
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9.^-]{0,14}", symbol):
            raise ValueError("Invalid research symbol")
        base = "/api/research/general/" + symbol
        listing = self.request("get", base)["research"]
        records, origins = [], {}
        for row in listing:
            if row["instrument"] != instrument or row["protocol_hash"] != protocol_hash:
                continue
            from officekit_research.cases import HASH
            if not HASH.fullmatch(str(row["id"])):
                raise ValueError("Invalid hosted research identity")
            record = general.validate(self.request("get", base + "/" + row["id"]))
            if record["id"] != row["id"] or record["subject"]["symbol"] != symbol:
                raise ValueError("Hosted research identity mismatch")
            provenance = self.request("get", base + "/" + row["id"] + "/provenance")
            check_receipt(record, provenance["admission"])
            records.append(record)
            origins[record["id"]] = provenance
        record, state = exchange.select(records, instrument, protocol_hash, **kwargs)
        return record, state, origins.get(record["id"]) if record else None
