"""Replay the NULL Wallet over real BTC 5-minute data (supply your own copy; see README).  python run_evidence.py <data1.csv> [data2.csv ...] <outdir>"""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nullwallet import bars, court, agent
from nullwallet.ledger import Ledger
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

out = sys.argv[-1]; os.makedirs(out, exist_ok=True)   # any number of OHLCV csv files (same columns) before the output dir
raw = pd.concat([bars.load(f) for f in sys.argv[1:-1]]).reset_index(drop=True); d = bars.clean(raw)
CFG = {12: dict(first=2000, window=4320, step=720, ppy=8760.0, name="1h"), 48: dict(first=500, window=1080, step=180, ppy=2190.0, name="4h")}
summary = {}; fig, ax = plt.subplots(2, 1, figsize=(10, 7))
for i, (k, c) in enumerate(CFG.items()):
    h = bars.resample(d, k); ok, worst = bars.truncation_audit(h.iloc[:4000]); X = bars.make_features(h); r = bars.next_return(h).to_numpy(); y = (r > 0).astype(float)
    proto = court.Protocol(); P = {m: court.walk_forward_proba(X, y, m, c["first"], c["step"]) for m in proto.candidates}
    s0 = c["first"] + c["window"]; e0 = len(h) - 2
    L = Ledger(f"{out}/ledger_{c['name']}.jsonl"); 
    if os.path.exists(L.path): os.remove(L.path); L = Ledger(L.path)
    res = agent.run(P, r, proto, s0, e0, window=c["window"], step=c["step"], ledger=L, ppy=c["ppy"])
    gbm = agent.run(P, r, proto, s0, e0, window=c["window"], step=c["step"], with_court=False, force_candidate="gbm_all", ppy=c["ppy"])
    lg = agent.run(P, r, proto, s0, e0, window=c["window"], step=c["step"], with_court=False, force_candidate="logit_all", ppy=c["ppy"])
    bh = agent.buy_hold(r, s0, e0); verd = [v for _, v, _ in res["decisions"]]
    summary[c["name"]] = {"bars": e0 - s0, "protocol_hash": proto.digest(), "truncation_audit_pass": bool(ok), "chain_valid": L.verify()[0], "ledger_entries": len(L.entries),
        "verdicts": {v: verd.count(v) for v in ("GO", "WATCH", "HOLD")}, "refusals_attested": res["refusals"],
        "final_equity": {"null_wallet": float(res["equity"][-1]), "no_court_gbm": float(gbm["equity"][-1]), "no_court_logit": float(lg["equity"][-1]), "buy_hold_10k": float(bh[-1])},
        "cost_paid_usd": {"null_wallet": res["cost_paid"], "no_court_gbm": gbm["cost_paid"], "no_court_logit": lg["cost_paid"]},
        "max_dd_pct": {n: 100 * float(np.min(e / np.maximum.accumulate(e) - 1)) for n, e in [("null_wallet", res["equity"]), ("no_court_gbm", gbm["equity"]), ("no_court_logit", lg["equity"]), ("buy_hold", bh)]}}
    t = h.date_time.iloc[s0:e0].to_numpy()
    ax[i].plot(t, res["equity"], label="NULL Wallet"); ax[i].plot(t, gbm["equity"], label="no court (GBM)"); ax[i].plot(t, lg["equity"], label="no court (logit)"); ax[i].plot(t, bh, label="buy & hold", alpha=.6)
    ax[i].set_yscale("log"); ax[i].set_title(f"Equity of a $10,000 wallet, {c['name']} bars"); ax[i].legend()
plt.tight_layout(); plt.savefig(f"{out}/equity.png", dpi=130); json.dump(summary, open(f"{out}/summary.json", "w"), indent=1); print(json.dumps(summary, indent=1))
