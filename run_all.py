"""ONE command that produces every result file we need.  python run_all.py <ohlcv.csv> [more.csv ...]   (add --quick for a 5-minute smoke version)
Outputs go to results/ and are zipped to results_for_claude.zip - send that zip back."""
import sys, os, json, time, zipfile, subprocess, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nullwallet import bars, court, agent, simulate, montecarlo
from nullwallet.ledger import Ledger
quick = "--quick" in sys.argv; files = [a for a in sys.argv[1:] if not a.startswith("--")]; R = "results"; os.makedirs(R, exist_ok=True); T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)

# 1. tests
log("1/5 unit + red-team tests"); t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], capture_output=True, text=True); open(f"{R}/tests.txt", "w").write(t.stderr + t.stdout); log(t.stderr.strip().splitlines()[-1])

# 2. real-data replay (1h bars) + cost sweep
log("2/5 replay on your data"); raw = pd.concat([bars.load(f) for f in files]).reset_index(drop=True); d = bars.clean(raw); h = bars.resample(d, 12)
X = bars.make_features(h); r = bars.next_return(h).to_numpy(); y = (r > 0).astype(float); proto = court.Protocol(); first, win, step = 2000, 4320, 720
P = {m: court.walk_forward_proba(X, y, m, first, step) for m in proto.candidates}; s0, e0 = first + win, len(h) - 2
L = Ledger(f"{R}/ledger_1h.jsonl"); os.path.exists(L.path) and os.remove(L.path); L = Ledger(L.path)
res = agent.run(P, r, proto, s0, e0, window=win, step=step, ledger=L); nc = agent.run(P, r, proto, s0, e0, window=win, step=step, with_court=False, force_candidate="gbm_all")
bh = agent.buy_hold(r, s0, e0); vv = [v for _, v, _ in res["decisions"]]
out = {"period": [str(h.date_time.iloc[0]), str(h.date_time.iloc[-1])], "bars": e0 - s0, "verdicts": {k: vv.count(k) for k in ("GO", "WATCH", "HOLD")}, "chain_valid": L.verify()[0],
       "equity": {"null_wallet": float(res["equity"][-1]), "no_court_gbm": float(nc["equity"][-1]), "buy_hold": float(bh[-1])}, "cost_paid": {"null_wallet": res["cost_paid"], "no_court": nc["cost_paid"]}}
log("   verdicts", out["verdicts"])
sweep = {}
for mult in (0.0, 0.25, 0.5, 1.0):
    p2 = court.Protocol(); p2.cost = {**p2.cost, "fee_bp": 5 * mult, "slippage_bp": 2 * mult, "impact_bp_at_1pct_adv": 3 * mult, "gas_usd": 0.5 * mult}
    rs = agent.run(P, r, p2, s0, e0, window=win, step=step); v2 = [v for _, v, _ in rs["decisions"]]
    sweep[str(mult)] = {"verdicts": {k: v2.count(k) for k in ("GO", "WATCH", "HOLD")}, "final_equity": float(rs["equity"][-1])}
out["cost_sweep"] = sweep; json.dump(out, open(f"{R}/real_summary.json", "w"), indent=1); log("   cost sweep", {k: v["verdicts"] for k, v in sweep.items()})

# 3. GO-path demo on a market with a planted edge (shows the full approve path)
log("3/5 GO-path demo"); import go_demo; log("   ", go_demo.run(R))

# 4. Monte Carlo (separate process: spawn-safe)
M = 40 if quick else 1000; log(f"4/5 Monte Carlo ({M} markets per scenario) - several minutes")
subprocess.run([sys.executable, "run_mc.py"] + (["--quick"] if quick else []) + [f"{R}/montecarlo.json"], check=True)

# 5. zip
log("5/5 zipping"); 
with zipfile.ZipFile("results_for_claude.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in os.listdir(R): z.write(f"{R}/{f}")
log("DONE -> results_for_claude.zip")
