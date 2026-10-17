"""Statistical self-audit of every test the Evidence Court relies on (run: python audit_stats.py).
(1) cross-checks our implementations against independent reference code (scipy / numpy), (2) simulates size (false-positive rate under the null)
and power (rejection when the null is false). Writes results/stats_audit.json. Reps are modest so it runs in about a minute."""
import os, sys, json, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scipy import stats as st
from nullwallet import stats as S
rng = np.random.default_rng(2026); out = {"crosschecks": {}, "size_power": {}}

# ---------- (1) cross-checks against independent code ----------
x = rng.standard_normal((500, 3)); y = x @ [0.5, -1.0, 2.0] + 0.3 + rng.standard_normal(500)
b, e, _, _ = S.ols(y, x); ref = np.linalg.lstsq(np.column_stack([np.ones(500), x]), y, rcond=None)[0]
out["crosschecks"]["OLS vs numpy.lstsq (max |diff|)"] = float(np.abs(b - ref).max())
z = rng.standard_t(5, 1000); out["crosschecks"]["Jarque-Bera vs scipy.stats.jarque_bera (|diff|)"] = abs(S.jarque_bera(z)[0] - float(st.jarque_bera(z).statistic))
e = rng.standard_normal(800); e2 = e - e.mean(); ac = [float(np.sum(e2[k:] * e2[:-k]) / np.sum(e2 ** 2)) for k in range(1, 13)]
q_ref = 800 * 802 * sum(a * a / (800 - k) for k, a in enumerate(ac, 1)); out["crosschecks"]["Ljung-Box vs direct formula (|diff|)"] = abs(S.ljung_box(e, 12)[0] - q_ref)
u = rng.standard_normal(600); u -= u.mean(); L = 8
g = [float(np.sum(u[k:] * u[:len(u) - k]) / len(u)) for k in range(L + 1)]; nw_ref = g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))
out["crosschecks"]["Newey-West variance vs autocovariance sum (|diff|)"] = abs(S.newey_west_var(u, L) - nw_ref)
p = rng.uniform(size=7); m = len(p); order = sorted(range(m), key=lambda i: p[i]); ref_adj = [0.0] * m; run = 0.0
for rank, i in enumerate(order): run = max(run, (m - rank) * p[i]); ref_adj[i] = min(1.0, run)
out["crosschecks"]["Holm vs step-down reference (max |diff|)"] = float(np.abs(np.array(S.holm(p)) - np.array(ref_adj)).max())
bm = S.block_bootstrap_mean(rng.standard_normal(500), 24, 2000, np.random.default_rng(1)); out["crosschecks"]["Block-bootstrap mean sd vs iid theory 1/sqrt(n) (ratio)"] = float(bm.std() / (1 / math.sqrt(500)))

# ---------- (2) size and power ----------
def rate(fn, R): return float(np.mean([fn(i) for i in range(R)]))
def ar1(n, rho, r):
    a = r.standard_normal(n + 100); 
    for t in range(1, len(a)): a[t] += rho * a[t - 1]
    return a[100:]
R = 1500; n = 720
sp = out["size_power"]
sp["HAC t (one-sided 5%), iid null, n=720: size"] = rate(lambda i: S.hac_t_mean(np.random.default_rng(i).standard_normal(n))[1] < 0.05, R)
sp["HAC t (one-sided 5%), AR(1) rho=0.3 null: size"] = rate(lambda i: S.hac_t_mean(ar1(n, 0.3, np.random.default_rng(10 ** 6 + i)))[1] < 0.05, 600)
sp["HAC t (one-sided 5%), mean=0.1 sd: power"] = rate(lambda i: S.hac_t_mean(np.random.default_rng(2 * 10 ** 6 + i).standard_normal(n) + 0.1)[1] < 0.05, R)
sp["Diebold-Mariano (one-sided 5%), equal skill: size"] = rate(lambda i: S.dm_test(np.random.default_rng(3 * 10 ** 6 + i).standard_normal(n) ** 2, np.random.default_rng(4 * 10 ** 6 + i).standard_normal(n) ** 2)[2] < 0.05, R)
sp["Jarque-Bera (5%), normal: size"] = rate(lambda i: S.jarque_bera(np.random.default_rng(5 * 10 ** 6 + i).standard_normal(n))[1] < 0.05, R)
sp["Jarque-Bera (5%), t(4): power"] = rate(lambda i: S.jarque_bera(np.random.default_rng(6 * 10 ** 6 + i).standard_t(4, n))[1] < 0.05, R)
sp["Ljung-Box (5%, 12 lags), iid: size"] = rate(lambda i: S.ljung_box(np.random.default_rng(7 * 10 ** 6 + i).standard_normal(n), 12)[1] < 0.05, R)
sp["Ljung-Box (5%, 12 lags), AR(1) 0.15: power"] = rate(lambda i: S.ljung_box(ar1(n, 0.15, np.random.default_rng(8 * 10 ** 6 + i)), 12)[1] < 0.05, 600)
def bp(i, het):
    r = np.random.default_rng(9 * 10 ** 6 + i); xx = r.standard_normal(n); sd = np.exp(0.6 * xx) if het else 1.0
    return S.breusch_pagan(0.2 * xx + sd * r.standard_normal(n), xx)[1] < 0.05
sp["Breusch-Pagan (5%), homoskedastic: size"] = rate(lambda i: bp(i, False), R); sp["Breusch-Pagan (5%), heteroskedastic: power"] = rate(lambda i: bp(i, True), R)
sp["ADF (stat < -2.86), random walk: size"] = rate(lambda i: S.adf(np.cumsum(np.random.default_rng(11 * 10 ** 6 + i).standard_normal(n)), 12)[0] < -2.86, 500)
sp["ADF (stat < -2.86), AR(1) 0.5: power"] = rate(lambda i: S.adf(ar1(n, 0.5, np.random.default_rng(12 * 10 ** 6 + i)), 12)[0] < -2.86, 500)
sp["KPSS (stat > 0.463), iid: size"] = rate(lambda i: S.kpss(np.random.default_rng(13 * 10 ** 6 + i).standard_normal(n)) > 0.463, R)
sp["KPSS (stat > 0.463), random walk: power"] = rate(lambda i: S.kpss(np.cumsum(np.random.default_rng(14 * 10 ** 6 + i).standard_normal(n))) > 0.463, 500)
sp["Holm family-wise error, 5 true nulls (target <= 0.05)"] = rate(lambda i: min(S.holm(np.random.default_rng(15 * 10 ** 6 + i).uniform(size=5))) < 0.05, 4000)
def cover(i):
    xx = np.random.default_rng(16 * 10 ** 6 + i).standard_normal(500); lo, hi = S.bootstrap_ci(xx, block=24, B=500, seed=i); return lo <= 0 <= hi
sp["Block-bootstrap 95% CI coverage, iid mean 0 (target 0.95)"] = rate(cover, 300)
json.dump(out, open("results/stats_audit.json", "w"), indent=1)
for k, v in out["crosschecks"].items(): print(f"{k:70s} {v:.3g}")
for k, v in sp.items(): print(f"{k:70s} {v:.3f}")
