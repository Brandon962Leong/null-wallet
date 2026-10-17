"""GO-path demo: a synthetic market with a planted edge, default (realistic) costs. Shows the whole approve path: GO receipt -> policy approves the capped funding move -> trading."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nullwallet import bars, court, agent, simulate
from nullwallet.ledger import Ledger

def run(out="results"):
    os.makedirs(out, exist_ok=True)
    dm = simulate.market(n=9000, b=0.25, seed=3); X = bars.make_features(dm); r = bars.next_return(dm).to_numpy(); y = (r > 0).astype(float); pz = court.Protocol()
    P = {m: court.walk_forward_proba(X, y, m, 1500, 500) for m in pz.candidates}; path = f"{out}/ledger_go_demo.jsonl"
    if os.path.exists(path): os.remove(path)
    L = Ledger(path); g = agent.run(P, r, pz, 3500, 8900, window=2000, step=500, ledger=L, active0=500.0); gv = [v for _, v, _ in g["decisions"]]
    ints = L.find("intent"); eq = g["equity"]
    res = {"planted_edge_b": 0.25, "verdicts": {k: gv.count(k) for k in ("GO", "WATCH", "HOLD")}, "approved_moves": sum(1 for e in ints if e["payload"]["decision"]["ok"]), "refused_moves": sum(1 for e in ints if not e["payload"]["decision"]["ok"]),
           "refusal_codes": sorted({e["payload"]["decision"]["code"] for e in ints if not e["payload"]["decision"]["ok"]}), "final_equity": float(eq[-1]), "min_equity": float(eq.min()), "regime_guard_events": len(L.find("regime_guard")),
           "chain_valid": L.verify()[0], "ledger_entries": len(L.entries), "buy_hold_same_bars": float(agent.buy_hold(r, 3500, 8900)[-1])}
    json.dump(res, open(f"{out}/go_demo.json", "w"), indent=1); return res

if __name__ == "__main__": print(json.dumps(run(), indent=1))
