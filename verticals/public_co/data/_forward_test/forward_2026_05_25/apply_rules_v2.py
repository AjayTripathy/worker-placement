"""Refined deployment rules — v2.

The v1 rule produced Group A=34 because agents elevated form4 findings more
aggressively in the forward test (vs historical 7% rate). The historical
form4-SEVERE signal had 75% catastrophe precision on a SMALL sample (8 names).

V2 stratifies by composite + signal direction:

GROUP A (HIGH-CONV SHORT): composite >= 1.30 AND form4 SEVERE
  -> Top-conviction shorts. Tight composite floor matches historical
     catastrophe distribution (those names had mean comp ~1.55).

GROUP A2 (MEDIUM-CONV SHORT): composite >= 0.50 AND form4 SEVERE AND composite < 1.30
  -> Lighter hedge candidates. Less conviction.

GROUP B (DISTRESSED LONG): composite in [0.50, 1.30] AND insider buy AND no ext-M SEVERE
  -> Framework flagged distress, insiders disagree — asymmetric upside bet.

GROUP B2 (CONSERVATIVE LONG): composite < 0.50 AND insider buy
  -> Framework doesn't see distress + insiders buying = solid LONG.

GROUP C (PASS): everything else.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SCORES = HERE / "scores"
MANIFEST = json.load(open(HERE / "forward_agent_manifest.json"))

SEV_W = {"PASS": 0, "UNVERIFIABLE": 0, "MODERATE_UNDERDELIVERY": 1,
         "SEVERE_UNDERDELIVERY": 2, "RED_FLAG_NEGATIVE": 3}

EXTERNAL_M_RE = re.compile(
    r'form4|insider_vs_calendar|edgar_fts|usaspending|fdic|\bfda\b|openfda'
    r'|uspto|google_patents|ucc_proxy|megacap_namecheck|clinical_trials|finra',
    re.IGNORECASE
)
FORM4_RE = re.compile(r'form4|insider_vs_calendar', re.IGNORECASE)

TIGHT_BUY_PATTERNS = [
    r'\bcode\s+P\b(?!\s*\d{3})',
    r'\bcode-?P\s+(?:purchase|buy|acquisition)',
    r'\bP[\s-]code\s+(?:purchase|buy|acquisition|filing)',
    r'(?:CEO|CFO|Chairman|Chair|President|COO|director|founder|10%\s+holder|10%\s+owner)\s+[A-Z][a-zA-Z]+\s+(?:bought|purchas)',
    r'(?:CEO|CFO|Chairman|Chair|President|COO|director|founder)\s+(?:executed\s+(?:an\s+)?|made\s+(?:an\s+)?)?(?:open[\s-]market\s+)?(?:purchase|buy)',
    r'(?:insider|director|officer|CEO|CFO|chairman|founder)\s+(?:bought|purchas)(?:ed)?\s+(?:approximately\s+|~)?\$[\d.]+[KMB]?',
    r'(?:cluster|coordinated|wave)\s+of\s+(?:insider\s+)?(?:purchas|buy)',
    r'directors?\s+(?:added|accumulated|put\s+\$[\d.]+M)',
    r'insider(?:s)?\s+(?:are|were)\s+(?:net\s+)?buy(?:ers|ing)',
    r'open[\s-]market\s+(?:purchas|buy)(?:es|ing)?\s+(?:by|of)\s+(?:CEO|CFO|Chairman|directors?|officers?|founders?|insiders?)',
]


def has_insider_buy(pilot):
    bits = [pilot.get('summary', '') or '']
    for t in pilot.get('rfm_tuples', []):
        for k in ('R', 'f', 'M_value', 'interpretation'):
            v = t.get(k, '')
            if isinstance(v, str): bits.append(v)
    text = ' '.join(bits)
    for pat in TIGHT_BUY_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            ctx = text[max(0,m.start()-80):min(len(text),m.end()+80)]
            if re.search(r'\b(?:buyback|repurchase|treasury\s+stock|ASR|share\s+repurchase|tender\s+offer|10b-?18)', ctx, re.IGNORECASE):
                continue
            return True
    return False


def has_form4_severe(pilot):
    for t in pilot.get('rfm_tuples', []):
        if t.get('severity') not in ('SEVERE_UNDERDELIVERY', 'RED_FLAG_NEGATIVE'): continue
        if FORM4_RE.search(t.get('M_source', '') or ''):
            return True
    return False


def has_external_severe(pilot):
    for t in pilot.get('rfm_tuples', []):
        if t.get('severity') not in ('SEVERE_UNDERDELIVERY', 'RED_FLAG_NEGATIVE'): continue
        if EXTERNAL_M_RE.search(t.get('M_source', '') or ''):
            return True
    return False


def composite(pilot):
    tuples = pilot.get('rfm_tuples', [])
    if not tuples: return None
    return sum(SEV_W.get(t.get('severity', 'PASS'), 0) for t in tuples) / len(tuples)


def main():
    rows = []
    for p in sorted(SCORES.glob('pilot_*.json')):
        pilot = json.load(open(p))
        tk = pilot.get('ticker') or p.stem.replace('pilot_', '')
        comp = composite(pilot)
        if comp is None: continue
        mani = MANIFEST.get(tk, {})
        rows.append({
            'ticker': tk, 'composite': comp,
            'drawdown': mani.get('drawdown_2026_05_25', None),
            'price': mani.get('price_2026_05_25', None),
            'sector': mani.get('sector', ''),
            'has_form4_severe': has_form4_severe(pilot),
            'has_ext_severe': has_external_severe(pilot),
            'has_insider_buy': has_insider_buy(pilot),
        })

    high_conv_short = []
    med_conv_short = []
    distressed_long = []
    conservative_long = []
    pass_pool = []

    for r in rows:
        if r['composite'] >= 1.30 and r['has_form4_severe']:
            high_conv_short.append(r)
        elif r['composite'] >= 1.30 and r['has_insider_buy'] and not r['has_ext_severe']:
            distressed_long.append(r)
        elif r['composite'] >= 0.50 and r['has_form4_severe']:
            med_conv_short.append(r)
        elif r['composite'] >= 0.50 and r['has_insider_buy'] and not r['has_ext_severe']:
            distressed_long.append(r)
        elif r['composite'] < 0.50 and r['has_insider_buy']:
            conservative_long.append(r)
        else:
            pass_pool.append(r)

    print("=" * 90)
    print("FORWARD-TEST DEPLOYMENT — Refined v2 rules")
    print("Cutoff: 2026-05-25  |  Measurement: 2027-05-25 (12m) / 2028-05-25 (24m)")
    print("=" * 90)
    print()
    print(f"Total scored: {len(rows)}")
    print(f"  HIGH-CONVICTION SHORT (composite >= 1.30 + form4 SEVERE): {len(high_conv_short)}")
    print(f"  MED-CONVICTION SHORT (0.50 <= comp < 1.30 + form4 SEVERE): {len(med_conv_short)}")
    print(f"  DISTRESSED LONG (comp >= 0.50 + insider buy + no ext-M):  {len(distressed_long)}")
    print(f"  CONSERVATIVE LONG (comp < 0.50 + insider buy):            {len(conservative_long)}")
    print(f"  PASS:                                                    {len(pass_pool)}")
    print()

    def show(label, group):
        print("=" * 90)
        print(label)
        print("=" * 90)
        print(f"  {'TK':6}  {'comp':>5}  {'dd':>7}  {'price':>8}  sector")
        for r in sorted(group, key=lambda x: -x['composite']):
            print(f"  {r['ticker']:6}  {r['composite']:>5.2f}  {(r['drawdown'] or 0)*100:>+6.1f}%  ${r['price']:>6.2f}  {r['sector']}")
        print()

    show("HIGH-CONVICTION SHORT — buy 12m OTM puts at -25% strike, sized ~1-2% portfolio each", high_conv_short)
    show("MED-CONVICTION SHORT — light hedge / smaller put position", med_conv_short)
    show("DISTRESSED LONG — asymmetric upside bet, sized ~2-3% portfolio each", distressed_long)
    show("CONSERVATIVE LONG — solid LONG candidate (no asymmetric flag)", conservative_long)
    print("=" * 90)
    print(f"PASS pool ({len(pass_pool)} names): skip")
    print("=" * 90)
    for r in sorted(pass_pool, key=lambda x: -x['composite']):
        flags = ''
        if r['has_form4_severe']: flags += 'F4s '
        if r['has_ext_severe']: flags += 'extS '
        if r['has_insider_buy']: flags += 'buy '
        print(f"  {r['ticker']:6}  comp={r['composite']:.2f}  dd={(r['drawdown'] or 0)*100:+.1f}%  flags={flags.strip() or 'none'}")

    out = {
        'cutoff': '2026-05-25', 'measurement_12m': '2027-05-25', 'measurement_24m': '2028-05-25',
        'high_conv_short': high_conv_short,
        'med_conv_short': med_conv_short,
        'distressed_long': distressed_long,
        'conservative_long': conservative_long,
        'pass_pool': pass_pool,
    }
    (HERE / 'forward_test_picks_v2.json').write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {HERE / 'forward_test_picks_v2.json'}")


if __name__ == "__main__":
    main()
