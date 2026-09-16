"""Apply deployment rules to forward-test pilots.

Group A — HIGH-CONVICTION SHORT:
  composite >= 0.50 AND has SEVERE/RED finding with M_source matching form4 or insider_vs_calendar

Group B — LONG CANDIDATE:
  composite in [0.50, 1.30] AND has insider BUY signal AND no external-M SEVERE finding

  (Composite >=0.50 means framework flagged as SHORT. Insider buy + no external corroboration
  of distress = "management committing capital despite filing-stress narrative".)

Group C — Framework LONG (composite <0.30): standard LONG tier from framework.

Group D — No deployment signal.
"""
import json
import re
import statistics
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
            return True, m.group(0)
    return False, None


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
        if comp is None:
            continue
        mani = MANIFEST.get(tk, {})
        rows.append({
            'ticker': tk,
            'composite': comp,
            'drawdown': mani.get('drawdown_2026_05_25', None),
            'price': mani.get('price_2026_05_25', None),
            'sector': mani.get('sector', ''),
            'has_form4_severe': has_form4_severe(pilot),
            'has_ext_severe': has_external_severe(pilot),
            'has_insider_buy': has_insider_buy(pilot)[0],
        })

    # Classify
    group_a = []  # High-conv SHORT
    group_b = []  # LONG candidate
    group_c = []  # Framework LONG
    group_d = []  # No signal

    for r in rows:
        if r['composite'] >= 0.50 and r['has_form4_severe']:
            group_a.append(r)
        elif (0.50 <= r['composite'] <= 1.30
              and r['has_insider_buy']
              and not r['has_ext_severe']):
            group_b.append(r)
        elif r['composite'] < 0.30:
            group_c.append(r)
        else:
            group_d.append(r)

    print("=" * 90)
    print(f"FORWARD-TEST DEPLOYMENT PICKS — cutoff 2026-05-25, measurement 2027-05-25 (12m) / 2028-05-25 (24m)")
    print("=" * 90)
    print()
    print(f"Total scored: {len(rows)}")
    print(f"Group A (HIGH-CONVICTION SHORT — form4 SEVERE): {len(group_a)}")
    print(f"Group B (LONG CANDIDATE — insider buy + no ext-M):  {len(group_b)}")
    print(f"Group C (framework STRICT/LOOSE LONG):              {len(group_c)}")
    print(f"Group D (no deployment signal):                     {len(group_d)}")
    print()

    print("=" * 90)
    print("GROUP A — HIGH-CONVICTION SHORT (buy puts / aggressive hedge):")
    print("=" * 90)
    print(f"  {'TK':6}  {'comp':>5}  {'dd':>7}  {'price':>8}  sector")
    for r in sorted(group_a, key=lambda x: -x['composite']):
        print(f"  {r['ticker']:6}  {r['composite']:>5.2f}  {(r['drawdown'] or 0)*100:>+6.1f}%  ${r['price']:>6.2f}  {r['sector']}")

    print()
    print("=" * 90)
    print("GROUP B — LONG CANDIDATE (consider long position):")
    print("=" * 90)
    print(f"  {'TK':6}  {'comp':>5}  {'dd':>7}  {'price':>8}  sector")
    for r in sorted(group_b, key=lambda x: x['composite']):
        print(f"  {r['ticker']:6}  {r['composite']:>5.2f}  {(r['drawdown'] or 0)*100:>+6.1f}%  ${r['price']:>6.2f}  {r['sector']}")

    print()
    print("=" * 90)
    print("GROUP C — FRAMEWORK STRICT/LOOSE LONG (composite <0.30):")
    print("=" * 90)
    print(f"  {'TK':6}  {'comp':>5}  {'dd':>7}  {'price':>8}  sector")
    for r in sorted(group_c, key=lambda x: x['composite']):
        print(f"  {r['ticker']:6}  {r['composite']:>5.2f}  {(r['drawdown'] or 0)*100:>+6.1f}%  ${r['price']:>6.2f}  {r['sector']}")

    print()
    print("=" * 90)
    print("GROUP D — NO DEPLOYMENT SIGNAL (skip):")
    print("=" * 90)
    print(f"  Count: {len(group_d)}")
    for r in sorted(group_d, key=lambda x: -x['composite']):
        flags = []
        if r['has_form4_severe']: flags.append('form4_sev')
        if r['has_ext_severe']: flags.append('ext_sev')
        if r['has_insider_buy']: flags.append('buy')
        print(f"  {r['ticker']:6}  comp={r['composite']:.2f}  dd={(r['drawdown'] or 0)*100:+.1f}%  flags={','.join(flags) or 'none'}")

    # Save
    out = {
        'cutoff': '2026-05-25', 'measurement_12m': '2027-05-25', 'measurement_24m': '2028-05-25',
        'group_a_high_conv_short': group_a,
        'group_b_long_candidate': group_b,
        'group_c_framework_long': group_c,
        'group_d_no_signal': group_d,
    }
    (HERE / 'forward_test_picks.json').write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {HERE / 'forward_test_picks.json'}")


if __name__ == "__main__":
    main()
