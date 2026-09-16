"""dual_class_screen — the BELFA methodology generalized (born 2026-08-30 from the
share_count_vs_eps_denominator + dual_class_vendor_stat_misassignment detector family).

For each liquid US dual-class pair: compute the A/B spread's percentile vs its OWN 6-year
weekly history (measuring vs own mean absorbs structural level differences - dividend
preferences, liquidity tiers). Extremes (<=3rd or >=97th pctile) are court candidates:
the instrument question is "why is the voting/economic relationship at a 6-year extreme,
and which leg is mispriced." Wash-frozen household names (GOOGL) are surfaced but never
enqueued. Run weekly; vendor stat tables NEVER trusted - bars only.
    python3 -m desk.dual_class_screen [--enqueue]
"""
PAIRS=[('GOOGL','GOOG'),('LEN','LEN-B'),('MOG-A','MOG-B'),('BF-A','BF-B'),('HEI','HEI-A'),
       ('CWEN-A','CWEN'),('RUSHA','RUSHB'),('BELFA','BELFB'),('LGF-A','LGF-B'),('UHAL','UHAL-B'),
       ('BIO','BIO-B'),('WSO','WSO-B'),('GEF','GEF-B'),('TAP','TAP-A'),('JW-A','JW-B')]
EXCLUDE_ENQUEUE={'GOOGL','GOOG',  # household wash names
                 'GEF','GEF-B'}   # charter-structural: 1:1.5 cash claims => ratio 1.28 is INSIDE the
                                  # fair band [1.00,1.50]; percentile-vs-own-history fired on a dead
                                  # near-parity regime (GEF_ADJUDICATION_202608311515). Un-exclude only
                                  # after the charter-claims gate (kg: dual_class_charter_claims_gate)
                                  # is implemented: flag spreads OUTSIDE the charter-implied band, not
                                  # extremes vs history alone.
import sys
def run(enqueue=False):
    import yfinance as yf, pandas as pd
    out=[]
    for a,b in PAIRS:
        try:
            ha=yf.Ticker(a).history(period='6y',interval='1wk')['Close']
            hb=yf.Ticker(b).history(period='6y',interval='1wk')['Close']
            df=pd.concat([ha,hb],axis=1,keys=['a','b']).dropna()
            if len(df)<100: continue
            sp=(df['a']/df['b']-1)*100
            cur=float(sp.iloc[-1]); pct=float((sp<cur).mean()*100)
            out.append(dict(pair=f'{a}/{b}',a=a,b=b,spread=round(cur,1),
                mean=round(float(sp.mean()),1),std=round(float(sp.std()),1),pctile=round(pct)))
        except Exception: pass
    ext=[r for r in out if r['pctile']<=3 or r['pctile']>=97]
    for r in sorted(out,key=lambda r:min(r['pctile'],100-r['pctile'])):
        tag='EXTREME' if r in ext else ''
        print(f"{r['pair']:14} {r['spread']:7.1f}% (mean {r['mean']:6.1f}%, {r['pctile']:3.0f}pctile) {tag}")
    if enqueue:
        from desk.court_queue import enqueue_candidates
        cands=[dict(ticker=r['a'],context=(f"dual_class_screen: {r['pair']} spread {r['spread']}% = "
            f"{r['pctile']}th pctile of 6y weekly history (mean {r['mean']}%, std {r['std']}pp). "
            f"BELFA-pattern instrument court: verify share counts at the EPS DENOMINATOR TABLE (never vendor), "
            f"explain the structural relationship (dividend preference/votes/liquidity/index membership), "
            f"then rule which leg is mispriced and the convergence mechanism. Both legs liquid? Bar-computed only."))
            for r in ext if r['a'] not in EXCLUDE_ENQUEUE]
        if cands:
            res=enqueue_candidates(cands,source='dual_class_screen/extremes',stage='REFUTABILITY')
            print('enqueued:',res)
    return out
if __name__=='__main__':
    run(enqueue='--enqueue' in sys.argv)
