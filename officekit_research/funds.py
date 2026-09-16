"""Primary issuer pages for fund research; no synthetic fees or prices."""
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen

FUND_PAGES = {
    "VDC": "https://advisors.vanguard.com/investments/products/vdc/vanguard-consumer-staples-etf",
    "XLP": "https://www.ssga.com/us/en/individual/etfs/state-street-consumer-staples-select-sector-spdr-etf-xlp",
    "SGOV": "https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf",
    "DBMF": "https://www.imgp.com/us/fund/US53700T8273/",
    "KMLM": "https://kraneshares.com/etf/kmlm/",
    "TAIL": "https://www.cambriafunds.com/tail",
    "VTI": "https://investor.vanguard.com/investment-products/etfs/profile/vti",
    "VXUS": "https://investor.vanguard.com/investment-products/etfs/profile/vxus",
    "VGSH": "https://investor.vanguard.com/investment-products/etfs/profile/vgsh",
    "VTIP": "https://investor.vanguard.com/investment-products/etfs/profile/vtip",
    "BND": "https://investor.vanguard.com/investment-products/etfs/profile/bnd",
    "VTEB": "https://investor.vanguard.com/investment-products/etfs/profile/vteb",
    "SHY": "https://www.ishares.com/us/products/239452/ishares-13-year-treasury-bond-etf",
    "MUB": "https://www.ishares.com/us/products/239766/ishares-national-amtfree-muni-bond-etf",
    "IAU": "https://www.ishares.com/us/products/239561/ishares-gold-trust-fund",
    "SPY": "https://www.ssga.com/us/en/individual/etfs/spdr-sp-500-etf-trust-spy",
    "QQQ": "https://www.invesco.com/qqq-etf/en/home.html",
    "TLT": "https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf",
}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


def fund_profile(symbol, ctx):
    url = FUND_PAGES.get(symbol.upper())
    if not url:
        raise ValueError("No primary issuer page registered for this fund")
    request = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
    with urlopen(request, timeout=20) as response:
        raw = response.read(1_000_000).decode("utf-8", errors="replace")
    parser = _Text()
    parser.feed(raw)
    body = "\n".join(parser.parts)
    if len(body) < 500 or symbol.upper() not in body.upper():
        raise RuntimeError("Issuer page did not expose sufficient fund evidence; verify the prospectus manually")
    return {"url": url, "fetched_at": datetime.now(timezone.utc).isoformat(),
            "text": body[:18000], "truncated": len(body) > 18000,
            "note": "Issuer document excerpt. Verify the effective dates of every numerical claim; retrieved date is not a quote date."}
