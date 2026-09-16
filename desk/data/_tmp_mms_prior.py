import urllib.request, json, re, html

hdr = {'User-Agent': 'ajay research 4tripathy@gmail.com'}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30).read()

subs = json.loads(get('https://data.sec.gov/submissions/CIK0001032220.json'))
rec = subs['filings']['recent']
cands = []
for form, date, acc, doc in zip(rec['form'], rec['filingDate'], rec['accessionNumber'], rec['primaryDocument']):
    if form == '8-K' and '2026-04-15' <= date <= '2026-06-15':
        cands.append((date, acc, doc))
print('candidate 8-Ks:', cands)
for date, acc, doc in cands:
    accn = acc.replace('-', '')
    idx = json.loads(get(f'https://www.sec.gov/Archives/edgar/data/1032220/{accn}/index.json'))
    names = [it['name'] for it in idx['directory']['item']]
    ex = [n for n in names if 'ex991' in n.lower() or 'ex99' in n.lower()]
    print(date, acc, ex)
    for n in ex:
        raw = get(f'https://www.sec.gov/Archives/edgar/data/1032220/{accn}/{n}').decode('utf-8', 'replace')
        txt = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', raw)))
        for m in re.finditer(r'signed contract awards', txt, re.I):
            print('   ...', txt[max(0, m.start()-200):m.end()+200], '...')
