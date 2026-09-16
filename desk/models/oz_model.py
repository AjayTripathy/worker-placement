"""Integrated OZ model v2 (2026-08-30): multi-year household simulation with the harvest
engine endogenous — losses offset gains year-by-year, excess accumulates as carryforwards,
and the 2032 OZ inclusion is absorbed by whatever ammunition the machine has banked.

Per principal directive: model the deferral-with-harvest interaction properly rather than
bolting absorption fractions onto the single-period model.
Assumptions printed with output; all rates constant (37.1 = 23.8 fed / 13.3 CA); CA never
conforms (taxes the gain in 2026 and the QOF appreciation at exit); Notice-path timing
(invest Jan-2027, inclusion Jan-2032 on 90% of the slice, exit 2037).
"""
T_FED, T_CA = 0.238, 0.133

def run(S, r_oz, r_a, g27=5.0, h0=1.0, h1=0.8, decay=0.90, G=5.0, years_exit=2037):
    """S = OZ slice ($M) from the 2026 gain G; returns terminal 2037 wealth ($M)."""
    pool = 0.0          # liquid, grows at r_a pre-tax; basis tracked for exit tax
    basis = 0.0
    cf_fed = cf_ca = 0.0
    qof = 0.0
    def grow(pool, basis, yrs=1):
        return pool*(1+r_a)**yrs, basis
    def pay(pool, basis, amt):
        # taxes paid from pool reduce basis proportionally (approximation)
        if pool<=0: return pool-amt, basis
        b = basis*min(1, amt/pool) if pool>0 else 0
        return pool-amt, basis-b
    # ---- 2026: gain lands; OZ slice elected (invested Jan-27); CA taxes full gain now
    fed_gain = G - S
    ca_gain  = G
    h = h0
    fed_tax = T_FED*max(0, fed_gain-h); cf_fed += max(0, h-fed_gain)
    ca_tax  = T_CA *max(0, ca_gain -h); cf_ca  += max(0, h-ca_gain)
    pool += G - S - fed_tax - ca_tax
    basis += G - S - fed_tax - ca_tax
    qof = S
    # ---- 2027: second tranche g27 (kept liquid), harvest h1
    pool, basis = grow(pool, basis)
    qof *= (1+r_oz)
    if g27>0:
        fed_t = T_FED*max(0, g27-h1); ca_t = T_CA*max(0, g27-h1)
        cf_fed += max(0, h1-g27); cf_ca += max(0, h1-g27)
        pool += g27 - fed_t - ca_t; basis += g27 - fed_t - ca_t
    else:
        cf_fed += h1; cf_ca += h1
    # ---- 2028-2031: no big gains; harvest accumulates as carryforward
    h = h1
    for yr in range(2028, 2032):
        h *= decay
        cf_fed += h; cf_ca += h
        pool, basis = grow(pool, basis)
        qof *= (1+r_oz)
    # ---- 2032: OZ inclusion on 90% of S (10% step-up), absorbed by fed carryforward first
    incl = 0.9*S
    absorbed = min(cf_fed, incl)
    cf_fed -= absorbed
    cash_tax = T_FED*(incl-absorbed)
    pool, basis = pay(pool, basis, cash_tax)
    # ---- 2033-2036: harvest keeps accumulating; pools grow
    for yr in range(2033, 2037):
        h *= decay
        cf_fed += h; cf_ca += h
        pool, basis = grow(pool, basis)
        qof *= (1+r_oz)
    pool, basis = grow(pool, basis)   # 2037
    qof *= (1+r_oz)                   # ~10y in fund (2027-2037)
    # ---- 2037 exits
    # QOF: federal free; CA taxes appreciation net of CA carryforward
    qof_app = qof - S
    ca_taxable = max(0, qof_app - cf_ca); cf_ca = max(0, cf_ca - qof_app)
    qof_net = qof - T_CA*ca_taxable
    # pool: tax appreciation net of remaining carryforwards
    app = max(0, pool - basis)
    fed_taxable = max(0, app - cf_fed)
    ca_taxable2 = max(0, app - cf_ca)
    pool_net = pool - T_FED*fed_taxable - T_CA*ca_taxable2
    return pool_net + qof_net, absorbed, incl

def breakeven(S, r_a, **kw):
    base,_,_ = run(0.0, 0.0, r_a, **kw)
    lo, hi = 0.0, 0.30
    for _ in range(60):
        mid=(lo+hi)/2
        t,_,_ = run(S, mid, r_a, **kw)
        if t < base: lo=mid
        else: hi=mid
    return mid

if __name__ == '__main__':
    print("INTEGRATED MODEL: required NET fund return, harvest engine endogenous")
    print("(G26=$5M; 2027 tranche $5M; harvest $1.0M'26, $0.8M'27 decaying 10%/yr; Notice path)")
    print(f"{'OZ slice':>9} | r_a=9% | r_a=11% | r_a=13% | 2032 inclusion absorbed by losses")
    for S in (1.0, 1.5, 2.0, 3.0):
        bs=[breakeven(S,ra) for ra in (0.09,0.11,0.13)]
        _,ab,incl = run(S, 0.08, 0.09)
        print(f"  ${S:.1f}M   | {bs[0]*100:5.1f}% | {bs[1]*100:5.1f}%  | {bs[2]*100:5.1f}%  | {ab:.2f} of {incl:.2f} ({ab/incl*100:.0f}%)")
    print("\nSENSITIVITY: no 2027 tranche (losses free up sooner):")
    for S in (1.5, 3.0):
        bs=[breakeven(S,ra,g27=0.0) for ra in (0.09,0.11,0.13)]
        _,ab,incl = run(S, 0.08, 0.09, g27=0.0)
        print(f"  ${S:.1f}M   | {bs[0]*100:5.1f}% | {bs[1]*100:5.1f}%  | {bs[2]*100:5.1f}%  | absorbed {ab/incl*100:.0f}%")
    print("\nSENSITIVITY: harvest engine at half pace:")
    for S in (1.5,):
        bs=[breakeven(S,ra,h0=0.5,h1=0.4) for ra in (0.09,0.11,0.13)]
        _,ab,incl = run(S, 0.08, 0.09, h0=0.5, h1=0.4)
        print(f"  ${S:.1f}M   | {bs[0]*100:5.1f}% | {bs[1]*100:5.1f}%  | {bs[2]*100:5.1f}%  | absorbed {ab/incl*100:.0f}%")
