"""Synthetic markets for stress-testing the court (Monte Carlo). Returns have GARCH(1,1) volatility clustering, fat tails (Student-t),
rare jumps (shock bars) and an optional PLANTED edge b: next return = noise - b * (price/MA10 - 1), i.e. a mean-reversion signal that really exists.
b = 0 is the null world H0: no tradable (and no forecastable) structure at all."""
from __future__ import annotations
import numpy as np, pandas as pd


def market(n=4200, b=0.0, seed=0, sigma=0.004, df=4, jump_p=0.003, jump_sd=0.03, start=20000.0):
    rng = np.random.default_rng(seed); omega, a, g = sigma**2 * 0.05, 0.08, 0.87
    eps = rng.standard_t(df, n) / np.sqrt(df / (df - 2)); jumps = (rng.random(n) < jump_p) * rng.normal(0, jump_sd, n)
    c = np.empty(n + 1); c[0] = start; v = sigma**2; r = np.zeros(n)
    for t in range(n):
        if t >= 10: gap = c[t] / c[t - 9:t + 1].mean() - 1
        else: gap = 0.0
        shock = np.sqrt(v) * eps[t]
        r[t] = shock - b * gap + jumps[t]
        c[t + 1] = c[t] * (1 + max(r[t], -0.5)); v = omega + a * shock**2 + g * v
    C = c[1:]; O = c[:-1]; hi = np.maximum(O, C) * (1 + np.abs(rng.normal(0, sigma / 3, n))); lo = np.minimum(O, C) * (1 - np.abs(rng.normal(0, sigma / 3, n)))
    vol = np.exp(rng.normal(10, 0.4, n)); vb = vol * np.clip(0.5 + rng.normal(0, 0.05, n), 0, 1)
    return pd.DataFrame({"date_time": pd.date_range("2020-01-01", periods=n, freq="1h", tz="UTC"), "N": 100, "amount": vol, "open": O, "high": hi, "low": lo, "close": C, "V_buy": vb, "V_sell": vol - vb})
