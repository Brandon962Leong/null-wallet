"""Statistics used by the Evidence Court. numpy/scipy only (no statsmodels).
OLS and the Gauss-Markov assumptions (heteroskedasticity, normality); HAC / Diebold-Mariano, ADF/KPSS;
block bootstrap, Newey-West t-statistics, multiple testing (data snooping)."""
from __future__ import annotations
import math
import numpy as np
from scipy import stats as _st


def norm_sf(z: float) -> float:
    return 0.5 * math.erfc(z / math.sqrt(2))


def ols(y, X, const=True):
    y = np.asarray(y, float); X = np.asarray(X, float)
    if X.ndim == 1: X = X[:, None]
    if const: X = np.column_stack([np.ones(len(y)), X])
    XtXi = np.linalg.pinv(X.T @ X); b = XtXi @ X.T @ y; e = y - X @ b
    return b, e, XtXi, X


def newey_west_var(u: np.ndarray, L: int) -> float:
    """Long-run variance of a series u (already demeaned) with Bartlett weights."""
    n = len(u); v = float(u @ u) / n
    for k in range(1, min(L, n - 1) + 1):
        v += 2 * (1 - k / (L + 1)) * float(u[k:] @ u[:-k]) / n
    return v


def default_lags(n: int) -> int:
    return max(1, int(np.floor(4 * (n / 100) ** (2 / 9))))        # Newey-West (1994) plug-in rule


def hac_t_mean(x, L: int | None = None):
    """t-statistic of H0: mean(x) = 0 with a Newey-West variance, and one-sided p-value for mean > 0."""
    x = np.asarray(x, float); n = len(x)
    if n < 30 or np.std(x) == 0: return 0.0, 1.0
    L = L or default_lags(n); u = x - x.mean(); v = newey_west_var(u, L)
    t = x.mean() / math.sqrt(max(v, 1e-30) / n)
    return float(t), float(norm_sf(t))


def dm_test(loss_base, loss_model, L: int | None = None):
    """Diebold-Mariano on per-observation losses. d = loss_base - loss_model, so d > 0 means the model is better.
    Returns (mean d, t, one-sided p for 'model better')."""
    d = np.asarray(loss_base, float) - np.asarray(loss_model, float)
    t, p = hac_t_mean(d, L)
    return float(d.mean()), t, p


def breusch_pagan(y, X):
    """Heteroskedasticity: LM test, regress e^2 on X, LM = n R^2 ~ chi2(k)."""
    b, e, _, Xc = ols(y, X); n, k = Xc.shape[0], Xc.shape[1] - 1
    e2 = e ** 2; b2, r2e, _, _ = ols(e2, Xc[:, 1:])
    ss_res = float(r2e @ r2e); ss_tot = float(((e2 - e2.mean()) ** 2).sum())
    R2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    lm = n * R2
    return float(lm), float(_st.chi2.sf(lm, max(k, 1)))


def jarque_bera(e):
    """Non-normality: JB = n/6 (S^2 + (K-3)^2/4) ~ chi2(2)."""
    e = np.asarray(e, float); n = len(e); z = e - e.mean(); s2 = (z ** 2).mean()
    S = (z ** 3).mean() / s2 ** 1.5; K = (z ** 4).mean() / s2 ** 2
    jb = n / 6 * (S ** 2 + (K - 3) ** 2 / 4)
    return float(jb), float(_st.chi2.sf(jb, 2))


def ljung_box(e, lags=12):
    """Autocorrelation: Q = n(n+2) sum rho_k^2/(n-k) ~ chi2(lags)."""
    e = np.asarray(e, float) - np.mean(e); n = len(e); d = float(e @ e)
    if d == 0: return 0.0, 1.0
    q = 0.0
    for k in range(1, lags + 1):
        rk = float(e[k:] @ e[:-k]) / d; q += rk * rk / (n - k)
    q *= n * (n + 2)
    return float(q), float(_st.chi2.sf(q, lags))


def adf(y, maxlag=24):
    """Augmented Dickey-Fuller t-statistic with constant, lag by AIC. 5% critical value about -2.86."""
    y = np.asarray(y, float); dy = np.diff(y); maxlag = min(maxlag, max(1, len(dy) // 20))

    def fit(p, start):
        yy = dy[start:]; Z = [y[start:-1]] + [dy[start - i:len(dy) - i] for i in range(1, p + 1)]
        Z = np.column_stack([np.ones(len(yy))] + Z); b = np.linalg.lstsq(Z, yy, rcond=None)[0]
        e = yy - Z @ b; m = len(yy); s2 = e @ e / (m - Z.shape[1]); cov = s2 * np.linalg.inv(Z.T @ Z)
        return m * (np.log(2 * np.pi) + np.log(e @ e / m) + 1) + 2 * Z.shape[1], b[1] / np.sqrt(cov[1, 1])
    p = min((fit(p, maxlag)[0], p) for p in range(maxlag + 1))[1]
    return float(fit(p, p)[1]), int(p)


def kpss(y):
    """Level-stationarity KPSS statistic (5% critical value 0.463)."""
    y = np.asarray(y, float); n = len(y); e = y - y.mean(); S = np.cumsum(e)
    l = int(12 * (n / 100) ** 0.25); s = e @ e / n
    for k in range(1, l + 1): s += 2 * (1 - k / (l + 1)) * (e[k:] @ e[:-k]) / n
    return float((S @ S) / n ** 2 / s)


def block_bootstrap_mean(x, block: int, B: int, rng: np.random.Generator):
    """Circular block bootstrap (Politis-Romano style, fixed block length) of the mean. Returns the B bootstrap means."""
    x = np.asarray(x, float); n = len(x)
    if n == 0: return np.zeros(B)
    block = max(1, min(block, n)); nb = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(B, nb)); idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % n
    return x[idx.reshape(B, -1)[:, :n]].mean(axis=1)


def bootstrap_ci(x, block=24, B=1000, level=0.95, seed=0):
    rng = np.random.default_rng(seed); m = block_bootstrap_mean(x, block, B, rng); a = (1 - level) / 2
    return float(np.quantile(m, a)), float(np.quantile(m, 1 - a))


def holm(pvals):
    """Holm step-down adjustment (controls the family-wise error rate; protects against data snooping, White 2000)."""
    p = np.asarray(pvals, float); m = len(p); order = np.argsort(p); adj = np.empty(m); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i]); adj[i] = min(1.0, run)
    return adj.tolist()


def sharpe(r, bars_per_year):
    r = np.asarray(r, float); s = r.std(ddof=1) if len(r) > 1 else 0.0
    return float(r.mean() / s * math.sqrt(bars_per_year)) if s > 0 else 0.0


def max_drawdown(r):
    w = np.cumprod(1 + np.asarray(r, float)); return float((w / np.maximum.accumulate(w) - 1).min()) if len(w) else 0.0
