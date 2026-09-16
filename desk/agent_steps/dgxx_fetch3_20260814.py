"""Fetch DGXX 8-K press release exhibit 99.1 and dump as text."""
import sys, re, html

sys.path.insert(0, ".")
from desk.sec_fetch import fetch

base = "https://www.sec.gov/Archives/edgar/data/1854368/000121390026089450/"
raw = fetch(base + "ea030173001ex99-1.htm")
# strip tags crudely
txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
txt = re.sub(r"<br[^>]*>", "\n", txt, flags=re.I)
txt = re.sub(r"</(p|div|tr|table|h\d|li)>", "\n", txt, flags=re.I)
txt = re.sub(r"<td[^>]*>", " | ", txt, flags=re.I)
txt = re.sub(r"<[^>]+>", "", txt)
txt = html.unescape(txt)
txt = re.sub(r"[ \t\xa0]+", " ", txt)
txt = re.sub(r"\n\s*\n+", "\n", txt)
open("desk/agent_steps/dgxx_ex991_20260814.txt", "w").write(txt)
print(txt[:6000])
