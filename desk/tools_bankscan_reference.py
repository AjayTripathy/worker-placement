#!/usr/bin/env python3
import urllib.parse, urllib.request, json, time, sys

UA = {"User-Agent": "Mozilla/5.0 signalos-research"}
BASE = "https://api.fdic.gov/banks"

# (ticker, bank subsidiary name to search, holdco note)
BANKS = [
    ("PLBC","Plumas Bank"),
    ("OVLY","Oak Valley Community Bank"),
    ("PCB","PCB Bank"),
    ("OPBK","Open Bank"),
    ("BMRC","Bank of Marin"),
    ("BCML","United Business Bank"),
    ("CALB","California Bank of Commerce"),
    ("FMBL","Farmers and Merchants Bank of Long Beach"),
    ("BSRR","Bank of the Sierra"),
    ("HTBK","Heritage Bank of Commerce"),
    ("FMNB","Farmers National Bank of Canfield"),
    ("PWOD","Jersey Shore State Bank"),
    ("FRAF","Farmers and Merchants Trust Company of Chambersburg"),
    ("MPB","Mid Penn Bank"),
    ("CFBK","CFBank"),
    ("OVBC","Ohio Valley Bank"),
    ("LARK","Landmark National Bank"),
    ("CCBG","Capital City Bank"),
    ("RRBI","Red River Bank"),
    ("BSVN","Bank7 Oklahoma City"),
    ("ESQ","Esquire Bank"),
    ("MCBS","Metro City Bank Doraville"),
    ("OPHC","OptimumBank"),
    ("CZWI","Citizens Community Federal"),
    ("FBIZ","First Business Bank"),
    ("FISI","Five Star Bank"),
    ("CZNC","Citizens and Northern Bank"),
    ("NECB","NorthEast Community Bank"),
    ("PFIS","Peoples Security Bank and Trust"),
    ("CARE","Carter Bank"),
]

def get(path, params):
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(1)
    return {"data": []}

def resolve(name):
    j = get("institutions", {"search": f"NAME:{name}", "fields":"NAME,CERT,ASSET,CITY,STALP,ACTIVE",
            "limit":6, "format":"json"})
    cands = [d["data"] for d in j.get("data",[])]
    active = [c for c in cands if c.get("ACTIVE")==1]
    return active[0] if active else (cands[0] if cands else None)

FIN = "REPDTE,ASSET,EQ,DEP,NIMY,EEFFR,NCLNLSR,NPERFV,BRO,LNLSNET,RBCT1J,RBCT2,RWAJT,RBCRWAJ,SC,SCHA,SCAF,INTAN,LNATRES,LNRECONS,LNREMULT,LNRENROT,LNRENROW,ROA,ROE,RBC1RWAJ"

def fin(cert):
    j = get("financials", {"filters":f"CERT:{cert}","fields":FIN,
            "sort_by":"REPDTE","sort_order":"DESC","limit":1,"format":"json"})
    return j["data"][0]["data"] if j.get("data") else None

rows=[]
for tk, nm in BANKS:
    inst = resolve(nm)
    if not inst:
        print(f"{tk:6} UNRESOLVED ({nm})"); continue
    cert = inst["CERT"]
    f = fin(cert)
    if not f:
        print(f"{tk:6} CERT={cert} {inst['NAME']} NO-FIN"); continue
    A=f.get("ASSET") or 0; EQ=f.get("EQ") or 0; DEP=f.get("DEP") or 0
    INTAN=f.get("INTAN") or 0
    rbct = (f.get("RBCT1J") or 0)+(f.get("RBCT2") or 0)
    tce = EQ-INTAN; ta = A-INTAN
    tce_ta = 100*tce/ta if ta else None
    # proper supervisory CRE: construction + multifamily + NON-owner-occ nonfarm-nonres
    cre = (f.get("LNRECONS") or 0)+(f.get("LNREMULT") or 0)+(f.get("LNRENROT") or 0)
    cre_cap = 100*cre/rbct if rbct else None
    cd_cap = 100*(f.get("LNRECONS") or 0)/rbct if rbct else None
    SC=f.get("SC") or 0; SCHA=f.get("SCHA") or 0
    htm_share = 100*SCHA/SC if SC else None  # HTM % of securities book (hidden-mark exposure)
    brod=f.get("BRO") or 0
    brod_pct = 100*brod/DEP if DEP else None
    rows.append(dict(tk=tk,cert=cert,name=inst["NAME"],city=inst.get("CITY"),st=inst.get("STALP"),
        rep=f.get("REPDTE"),asset=A,tce=tce,tce_ta=tce_ta,nim=f.get("NIMY"),eff=f.get("EEFFR"),
        npl=f.get("NCLNLSR"),brod=brod_pct,cre_cap=cre_cap,cd_cap=cd_cap,htm_share=htm_share,
        roa=f.get("ROA"),roe=f.get("ROE"),t1=f.get("RBC1RWAJ")))
    time.sleep(0.15)

hdr=f"{'TK':5}{'CERT':7}{'A$M':>7} {'TCE/TA':>6} {'NIM':>5} {'EFF':>5} {'NPL':>5} {'BROD':>5} {'CRE%c':>6} {'C&D%c':>6} {'HTM%s':>6} {'ROA':>5}  NAME"
print(hdr); print("-"*len(hdr))
for r in sorted(rows,key=lambda x:x['asset']):
    def g(v,f="{:.1f}"):
        return f.format(v) if v is not None else "  -"
    print(f"{r['tk']:5}{r['cert']:<7}{r['asset']/1000:>7.0f} {g(r['tce_ta']):>6} {g(r['nim']):>5} {g(r['eff']):>5} {g(r['npl'],'{:.2f}'):>5} {g(r['brod']):>5} {g(r['cre_cap'],'{:.0f}'):>6} {g(r['cd_cap'],'{:.0f}'):>6} {g(r['htm_share'],'{:.0f}'):>6} {g(r['roa'],'{:.2f}'):>5}  {r['name']} ({r['city']},{r['st']}) {r['rep']}")

json.dump(rows, open("/private/tmp/claude-501/-Users-ajay-exalted-signalos/4358a8fb-7ef0-47c6-b39e-0042f0c79b96/scratchpad/bankrows.json","w"), indent=1)
print(f"\nresolved {len(rows)} banks")
