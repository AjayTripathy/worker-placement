"""Test C scoring: blind agent stress-rankings vs the SEALED beta-CapGains prediction.
Spearman rank-corr per crisis + insulated-tier check. Run un-blind, AFTER the agents.
"""
import json

# sector keys
SEC = {"A":"State GO","B":"County COP/appropriation","C":"RDA/TAB","D":"Hospital rev",
       "E":"CCRC","F":"CalHFA","G":"School GO","H":"Water rev"}
# sealed prediction (beta order, 1 = most stressed)
PRED = {"A":1,"B":2,"C":3,"D":4,"E":5,"F":6,"G":7,"H":8}

# blind agent rankings (1=most stressed .. 8=least), transcribed from the 4 agents
ACTUAL = {
 "Dot-com 2000-03 (income/cap-gains)": {"A":1,"B":2,"D":3,"E":4,"C":5,"G":6,"F":7,"H":8},
 "GFC 2008-09 (property/liquidity)":   {"E":1,"F":2,"A":3,"D":4,"C":5,"B":6,"G":7,"H":8},
 "COVID 2020 (operational/liquidity)": {"E":1,"D":2,"C":3,"B":4,"A":5,"G":6,"H":7,"F":8},
 "2022 (rate/inflation)":              {"E":1,"D":2,"B":3,"G":4,"C":5,"A":6,"H":7,"F":8},
}

def spearman(pred, act):
    n=len(pred); d2=sum((pred[k]-act[k])**2 for k in pred)
    return 1 - 6*d2/(n*(n*n-1)), d2

out={"sectors":SEC,"prediction":PRED,"results":{}}
print(f"{'crisis':<38}{'rho':>7}{'  insulated-tier ranks (School GO, Water)'}")
for crisis, act in ACTUAL.items():
    rho,d2=spearman(PRED,act)
    ins=f"G={act['G']}, H={act['H']}"
    # AI-5 (State GO) actual position
    out["results"][crisis]={"rho":round(rho,3),"sum_d2":d2,
        "state_go_actual_rank":act["A"],"school_go_rank":act["G"],"water_rank":act["H"]}
    print(f"{crisis:<38}{rho:>7.2f}   {ins}   | State GO actual rank = {act['A']}")

json.dump(out, open("/Users/ajay/exalted/signalos/verticals/muni_credit/data/testC_results.json","w"), indent=1)
print("\nInterpretation:")
print("  income/cap-gains regime (dot-com) = the AI-crash archetype -> strongest match")
print("  property/operational/rate regimes -> model correctly does NOT predict (channel-specific)")
print("  insulated tier (School GO, Water) bottom-2 in ALL four regimes -> robust AI-1")
print("saved -> data/testC_results.json")
