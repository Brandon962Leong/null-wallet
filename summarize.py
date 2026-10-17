import pickle, json, numpy as np
S = pickle.load(open("results/series.pkl", "rb")); dd = lambda e: 100 * float(np.min(np.asarray(e) / np.maximum.accumulate(np.asarray(e)) - 1))
out = {"replay_period": [str(S["time"][0]), str(S["time"][-1])], "hourly_bars": int(len(S["time"])), "protocol_hash": S["protocol_hash"], "ledger_entries": S["n_ledger"], "ledger_chain_valid": bool(S["ledger_ok"]),
       "verdicts_36_windows": {k: sum(w["verdict"] == k for w in S["windows"]) for k in ("GO", "WATCH", "HOLD")},
       "final_equity_usd": {k: float(np.asarray(S[k])[-1]) for k in ("wallet", "nocourt_gbm_all", "nocourt_logit_all", "nocourt_reversal", "nocourt_trend", "nocourt_rsi_reversal", "buyhold")},
       "max_drawdown_pct": {k: dd(S[k]) for k in ("wallet", "nocourt_gbm_all", "nocourt_logit_all", "buyhold")},
       "cost_sweep": {str(m): {k: (v[k] if k != "equity" else float(v["equity"][-1])) for k in ("GO", "WATCH", "HOLD", "unit_bp", "equity")} for m, v in S["sweep"].items()}, "g1_assumption_audit": S["g1"],
       "note": "sandbox replay with assumed costs; buy&hold is fully invested ($10,000) while the wallet's active bucket is $2,000; regime guard added post hoc"}
json.dump(out, open("results/summary_for_submission.json", "w"), indent=1, default=float); print(json.dumps(out["verdicts_36_windows"]), out["final_equity_usd"]["wallet"])
