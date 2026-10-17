"""Run the court on many synthetic markets and report the false-GO rate (b=0) and the power curve (b>0)."""
from __future__ import annotations
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')   # one thread per worker: avoids oversubscription, ~4x faster on small machines
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import numpy as np, sys, json
import multiprocessing as mp
from . import bars, court, simulate

CANDS = ("reversal", "rsi_reversal", "trend", "logit_all", "gbm_all")


def one(args):
    b, seed, n, first, nocost = args
    d = simulate.market(n=n, b=b, seed=seed); X = bars.make_features(d); r = bars.next_return(d).to_numpy(); y = (r > 0).astype(float)
    proto = court.Protocol(candidates=CANDS, boot_B=400)
    if nocost: proto.cost = {**proto.cost, "fee_bp": 0.0, "slippage_bp": 0.0, "impact_bp_at_1pct_adv": 0.0, "gas_usd": 0.0}
    P = {k: court.walk_forward_proba(X, y, k, first, 500) for k in CANDS}
    tab, dec = court.evaluate_window(P, r, first, n - 1, court.prevailing_rate(r), proto, seed)
    naive = any((v["net_p"] < 0.05 and v["mean_excess_bp"] > 0) for v in tab.values())   # best-of-N picker with no multiple-testing control
    return {"b": b, "seed": seed, "naive": bool(naive), "verdict": dec["verdict"], "cand": dec.get("candidate"),
            "min_skill_p": min(v["skill_p_holm"] for v in tab.values()) if tab else 1.0}


def run(b, m, n=3000, first=1200, workers=4, nocost=False, seed0=0):
    with mp.get_context('spawn').Pool(workers) as p: res = p.map(one, [(b, seed0 + i, n, first, nocost) for i in range(m)], chunksize=4)
    v = [x["verdict"] for x in res]
    return {"b": b, "markets": m, "GO": v.count("GO") / m, "WATCH": v.count("WATCH") / m, "HOLD": v.count("HOLD") / m,
            "NAIVE_TRADE": sum(x["naive"] for x in res) / m, "min_skill_p_median": float(np.median([x["min_skill_p"] for x in res])), "nocost": nocost}
