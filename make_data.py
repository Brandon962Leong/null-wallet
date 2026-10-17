"""Replay once and save every series needed for the figures: python make_data.py <csv>... -> results/series.pkl"""
import sys, os, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nullwallet import bars, court, agent, simulate
from nullwallet.ledger import Ledger
files = sys.argv[1:]; os.makedirs("results", exist_ok=True)
raw = pd.concat([bars.load(f) for f in files]).reset_index(drop=True); d = bars.clean(raw); h = bars.resample(d, 12)
X = bars.make_features(h); r = bars.next_return(h).to_numpy(); y = (r > 0).astype(float); proto = court.Protocol(); first, win, step = 2000, 4320, 720
P = {m: court.walk_forward_proba(X, y, m, first, step) for m in proto.candidates}; s0, e0 = first + win, len(h) - 2; base = court.prevailing_rate(r)
S = {"time": h.date_time.iloc[s0:e0].to_numpy(), "close": h.close.iloc[s0:e0].to_numpy(), "ret": r[s0:e0]}
LP = 'results/ledger_1h.jsonl'; os.path.exists(LP) and os.remove(LP); L = Ledger(LP); res = agent.run(P, r, proto, s0, e0, window=win, step=step, ledger=L); S["wallet"] = res["equity"]
for nm in ("gbm_all", "logit_all", "reversal", "trend", "rsi_reversal"): S["nocourt_" + nm] = agent.run(P, r, proto, s0, e0, window=win, step=step, with_court=False, force_candidate=nm)["equity"]
S["buyhold"] = agent.buy_hold(r, s0, e0); S["decisions"] = res["decisions"]
# per-window table for the last window and every window (for heatmaps)
rows = []
for t0 in range(s0, e0, step):
    tab, dec = court.evaluate_window(P, r, t0 - win, t0, base, proto, t0)
    rows.append({"t0": h.date_time.iloc[t0], "verdict": dec["verdict"], **{k: {"skill_p_holm": v["skill_p_holm"], "mean_excess_bp": v["mean_excess_bp"], "break_even_bp": v["break_even_bp"], "cost_bp": v["cost_unit_bp"], "net_p_holm": v["net_p_holm"], "gates": v["gates"], "lo": v["excess_ci_bp"][0], "hi": v["excess_ci_bp"][1], "auc": v["auc"], "exposure": v["exposure"]} for k, v in tab.items()}})
S["windows"] = rows; S["cand"] = list(proto.candidates)
# assumption audit on the whole real sample (G1)
ok = np.isfinite(P["logit_all"]) & np.isfinite(r); S["g1"] = court.assumption_audit(r[ok], P["logit_all"][ok])
# cost sweep (equity + verdict counts)
sw = {}
for mult in (0.0, 0.25, 0.5, 0.75, 1.0):
    p2 = court.Protocol(); p2.cost = {**p2.cost, "fee_bp": 5 * mult, "slippage_bp": 2 * mult, "impact_bp_at_1pct_adv": 3 * mult, "gas_usd": 0.5 * mult}
    rs = agent.run(P, r, p2, s0, e0, window=win, step=step); v = [x[1] for x in rs["decisions"]]
    sw[mult] = {"GO": v.count("GO"), "WATCH": v.count("WATCH"), "HOLD": v.count("HOLD"), "equity": rs["equity"], "unit_bp": 1e4 * court.CostModel(**p2.cost).unit_cost()}
S["sweep"] = sw; S["protocol_hash"] = proto.digest(); S["ledger_ok"] = L.verify()[0]; S["n_ledger"] = len(L.entries)
pickle.dump(S, open("results/series.pkl", "wb")); print("saved", {k: (len(v) if hasattr(v, "__len__") else v) for k, v in S.items() if k in ("time", "windows", "n_ledger")}, S["g1"]["flags"])
