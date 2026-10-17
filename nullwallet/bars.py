"""Market data: loading, cleaning (fixed rules), resampling to a trading horizon, and causal features.
Every feature at row t uses only bars <= t; `truncation_audit` proves it by recomputing on truncated history."""
from __future__ import annotations
import numpy as np, pandas as pd

UNIT_SWITCH = pd.Timestamp("2019-11-07", tz="UTC")


def load(path):
    d = pd.read_csv(path, index_col=0, parse_dates=["date_time"])
    return d.sort_values("date_time").reset_index(drop=True)


def clean(raw, half_window=6, tol=0.15):
    """Cleaning: prices more than 15% away from the median of the surrounding 13 highs are errors; repaired from the next open.
    Volume before 2019-11-07 is in BTC and is converted to USD; absurd volume spikes are replaced by the rolling median."""
    d = raw.copy(); ref = d["high"].rolling(2 * half_window + 1, center=True, min_periods=1).median()
    bad = {c: ((d[c] / ref - 1).abs() > tol) for c in ["open", "high", "low", "close"]}
    o, h, c_ = (d[c].where(~bad[c]) for c in ["open", "high", "close"])
    nxt_open = o.shift(-1); c_ = c_.fillna(nxt_open)
    mism = c_.notna() & nxt_open.notna() & ((c_ / nxt_open - 1).abs() > 0.02)
    c_ = c_.where(~(mism & ((nxt_open - ref).abs() < (c_ - ref).abs())), nxt_open)
    c_ = c_.ffill().bfill(); o = c_.shift(1).fillna(c_); h = pd.concat([h, o, c_], axis=1).max(axis=1)
    d["open"], d["close"], d["high"] = o, c_, h; d["low"] = pd.concat([o, c_], axis=1).min(axis=1)
    pre = d["date_time"] < UNIT_SWITCH
    for v in ["amount", "V_buy", "V_sell"]: d.loc[pre, v] = d.loc[pre, v] * d.loc[pre, "close"]
    med = d["amount"].rolling(288, min_periods=20).median().shift(1); spike = d["amount"] > 100 * med
    share = (d["V_buy"] / d["amount"]).where(spike, np.nan)
    d.loc[spike, "amount"] = med[spike]; d.loc[spike, "V_buy"] = med[spike] * share[spike].clip(0, 1); d.loc[spike, "V_sell"] = med[spike] - d.loc[spike, "V_buy"]
    return d


def resample(d, k: int):
    """Aggregate k consecutive 5-minute bars into one trading bar (k=12: one hour)."""
    if k == 1: return d.reset_index(drop=True)
    g = np.arange(len(d)) // k; n = (len(d) // k) * k; d = d.iloc[:n]; g = g[:n]
    agg = d.groupby(g).agg(date_time=("date_time", "first"), open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
                           amount=("amount", "sum"), N=("N", "sum"), V_buy=("V_buy", "sum"), V_sell=("V_sell", "sum"))
    return agg.reset_index(drop=True)


def rsi(close, n=14):
    ch = close.diff(); up = ch.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-ch.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


FEATURES = ["ret_1", "ret_3", "ret_12", "ret_48", "ma10_gap", "ma30_gap", "ma10_30", "ma50_200", "macd", "rsi14", "vol12", "range", "ofi", "ofi_12", "rel_volume"]


def make_features(d):
    C, H, O = d["close"], d["high"], d["open"]; f = pd.DataFrame(index=d.index); lc = np.log(C)
    f["ret_1"] = lc.diff()
    for n in (3, 12, 48): f[f"ret_{n}"] = lc.diff(n)
    s = {n: C.rolling(n).mean() for n in (10, 30, 50, 200)}
    f["ma10_gap"] = C / s[10] - 1; f["ma30_gap"] = C / s[30] - 1; f["ma10_30"] = s[10] / s[30] - 1; f["ma50_200"] = s[50] / s[200] - 1
    f["macd"] = (C.ewm(span=12, adjust=False).mean() - C.ewm(span=26, adjust=False).mean()) / C
    f["rsi14"] = rsi(C, 14); f["vol12"] = f["ret_1"].rolling(12).std(); f["range"] = (H - pd.concat([O, C], axis=1).min(axis=1)) / C
    tot = (d["V_buy"] + d["V_sell"]).replace(0, np.nan); f["ofi"] = (d["V_buy"] - d["V_sell"]) / tot; f["ofi_12"] = f["ofi"].rolling(12).mean()
    f["rel_volume"] = np.log(d["amount"] / d["amount"].rolling(288).median())
    return f[FEATURES].replace([np.inf, -np.inf], np.nan)


def next_return(d):
    """Simple return from the close of bar t to the close of bar t+1 (what a position held over bar t+1 earns)."""
    return d["close"].shift(-1) / d["close"] - 1


def truncation_audit(d, n_checks=25, seed=0, tail=400):
    """Look-ahead audit (look-ahead bias): recompute the features on history that ends at t
    and compare with the features computed on the full data. Any difference means a feature used the future. Returns (passed, max_abs_diff)."""
    full = make_features(d); rng = np.random.default_rng(seed); worst = 0.0
    lo = min(len(d) - 1, 400)
    for t in rng.integers(lo, len(d), size=n_checks):
        part = make_features(d.iloc[: t + 1]).iloc[-1]; ref = full.iloc[t]
        mism = part.isna() != ref.isna()          # value on one side and NaN on the other = the feature depends on the future
        diff = np.inf if mism.any() else float((part - ref).abs().fillna(0).max()); worst = max(worst, float(diff))
    return worst < 1e-9, worst
