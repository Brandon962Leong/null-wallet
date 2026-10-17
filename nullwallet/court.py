"""The Evidence Court: before the agent may act it must reject H0 = 'this strategy has no net edge'.

Gates (each one a standard test):
  G0 timing audit      - features are causal (truncation test)
  G1 assumption audit  - heteroskedasticity, autocorrelation, normality, stationarity
  G2 skill duel        - walk-forward log-loss beats a naive constant, Diebold-Mariano
  G3 shock robustness  - the skill survives dropping shock bars (COVID-style regime)
  G4 net edge          - after costs, excess return over an exposure-matched benchmark is > 0
                         (HAC t-test, Holm-adjusted over all candidates, and block-bootstrap lower bound > 0)
  G5 cost margin       - break-even cost is at least `margin` times the modelled cost
Verdicts: GO (all gates), WATCH (statistical skill but not tradable after costs), HOLD (nothing)."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
import numpy as np, pandas as pd
from . import stats as S
from .ledger import sha256_hex

CANDIDATES = {
    "reversal": ["ma10_gap"], "rsi_reversal": ["rsi14"], "trend": ["macd", "ma10_30", "ma50_200"],
    "logit_all": None, "gbm_all": None}                      # None = all features


@dataclass
class CostModel:
    fee_bp: float = 5.0            # exchange / DEX fee per unit traded (assumption, configurable)
    slippage_bp: float = 2.0       # fixed part of the slippage
    impact_bp_at_1pct_adv: float = 3.0   # square-root impact law: impact = k * sqrt(trade / ADV)
    gas_usd: float = 0.50          # fixed network cost per swap (L2-like)
    wallet_usd: float = 10_000.0   # size of the wallet
    adv_usd: float = 5e9           # average daily traded volume of the asset

    def unit_cost(self) -> float:
        """Cost as a fraction of the traded notional for one full switch (0 -> 100% exposure)."""
        impact = self.impact_bp_at_1pct_adv * np.sqrt(self.wallet_usd / self.adv_usd / 0.01)
        return (self.fee_bp + self.slippage_bp + impact) / 1e4 + self.gas_usd / self.wallet_usd


@dataclass
class Protocol:
    """The pre-registered hypothesis set. Its hash is committed BEFORE the evidence window is looked at."""
    name: str = "null-wallet-protocol-v1"
    horizons: tuple = (12, 48)                      # trading bars in units of 5 minutes: 1 hour and 4 hours
    candidates: tuple = ("reversal", "rsi_reversal", "trend", "logit_all", "gbm_all")
    tau: float = 0.01                               # dead-band: long only if p > 0.5 + tau
    alpha: float = 0.05
    shock_alpha: float = 0.10
    margin: float = 2.0                             # break-even cost must be >= margin x modelled cost
    min_trades: int = 10
    vol_mult: float = 3.0                           # live regime guard: evidence is void if recent volatility > vol_mult x the evidence window's
    vol_lb: int = 24                                # bars used for the recent-volatility estimate
    boot_B: int = 1000
    boot_block: int = 24
    seed: int = 7
    cost: dict = field(default_factory=lambda: asdict(CostModel()))

    def digest(self) -> str:
        return sha256_hex(asdict(self))


def make_model(name: str):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler, FunctionTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import HistGradientBoostingClassifier
    if name == "gbm_all":
        return HistGradientBoostingClassifier(max_iter=60, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=300, l2_regularization=10.0, random_state=0)
    return make_pipeline(StandardScaler(), FunctionTransformer(lambda a: np.clip(a, -5, 5)), LogisticRegression(C=0.05, max_iter=300))


def walk_forward_proba(X: pd.DataFrame, y: np.ndarray, name: str, first_pred: int, refit_every: int):
    """Expanding-window pseudo-out-of-sample forecasts. A model fitted at `start` uses only rows < start (targets known at `start`)."""
    cols = list(X.columns) if CANDIDATES[name] is None else CANDIDATES[name]
    A = X[cols].to_numpy(float); n = len(A); p = np.full(n, np.nan)
    for start in range(first_pred, n, refit_every):
        end = min(start + refit_every, n); tr = np.arange(0, start)
        ok = np.isfinite(A[tr]).all(axis=1) & np.isfinite(y[tr]); te = np.arange(start, end); okt = np.isfinite(A[te]).all(axis=1)
        if ok.sum() < 500 or len(np.unique(y[tr][ok])) < 2: continue
        m = make_model(name).fit(A[tr][ok], y[tr][ok].astype(int))
        if okt.any(): p[te[okt]] = m.predict_proba(A[te][okt])[:, 1]
    return p


def log_loss_vec(y, p, eps=1e-6):
    p = np.clip(p, eps, 1 - eps); return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def assumption_audit(r, p):
    """G1. Regress next return on (p - 0.5) and test the Gauss-Markov assumptions; report which standard errors are needed."""
    b, e, _, Xc = S.ols(r, (p - 0.5)[:, None])
    bp = S.breusch_pagan(r, (p - 0.5)[:, None]); jb = S.jarque_bera(e); lb = S.ljung_box(e, 12)
    adf = S.adf(r)[0]; k = S.kpss(r)
    flags = {"heteroskedastic": bp[1] < 0.05, "autocorrelated": lb[1] < 0.05, "non_normal": jb[1] < 0.05,
             "returns_stationary": (adf < -2.86) and (k < 0.463)}
    mode = "HAC (Newey-West)" if (flags["heteroskedastic"] or flags["autocorrelated"]) else "classical"
    return {"bp_p": bp[1], "lb_p": lb[1], "jb_p": jb[1], "adf": adf, "kpss": k, "flags": {k_: bool(v) for k_, v in flags.items()},
            "inference_used": "HAC (Newey-West), always (conservative)", "inference_needed": mode,
            "slope_t_hac": S.hac_t_mean(e * (p - 0.5) / max(np.var(p - 0.5), 1e-12))[0]}


def evaluate_candidate(p, r, base_rate, proto: Protocol, rng_seed: int, ppy: float = 8760.0):
    """All numbers for one candidate on one evidence window (arrays aligned; NaN forecasts are dropped)."""
    ok = np.isfinite(p) & np.isfinite(r); p, r = p[ok], r[ok]; n = len(r); base_rate = np.broadcast_to(np.asarray(base_rate, float), ok.shape)[ok]
    if n < 200: return {"n": int(n), "usable": False}
    y = (r > 0).astype(float); cost = CostModel(**proto.cost).unit_cost()
    d_skill, t_skill, p_skill = S.dm_test(log_loss_vec(y, base_rate), log_loss_vec(y, p))
    s = (p > 0.5 + proto.tau).astype(float); ds = np.abs(np.diff(s, prepend=0.0))
    gross = s * r; net = gross - ds * cost; ebar = float(s.mean()); excess = net - ebar * r
    t_net, p_net = S.hac_t_mean(excess); t_abs, _ = S.hac_t_mean(net)
    lo, hi = S.bootstrap_ci(excess, proto.boot_block, proto.boot_B, 0.95, rng_seed)
    turn = float(ds.mean()); be_bp = float(1e4 * gross.mean() / turn) if turn > 0 else float("nan")
    mad = np.median(np.abs(r - np.median(r))) * 1.4826; keep = np.abs(r - np.median(r)) < 5 * mad
    d_ex, t_ex, p_ex = S.dm_test(log_loss_vec(y[keep], base_rate[keep]), log_loss_vec(y[keep], p[keep]))
    return {"usable": True, "n": int(n), "skill_dlogloss": d_skill, "skill_t": t_skill, "skill_p": p_skill,
            "shock_bars": int((~keep).sum()), "skill_dlogloss_noshock": d_ex, "skill_p_noshock": p_ex,
            "exposure": ebar, "trades": int(ds.sum()), "turnover": turn, "cost_unit_bp": 1e4 * cost,
            "mean_gross_bp": 1e4 * float(gross.mean()), "mean_net_bp": 1e4 * float(net.mean()), "mean_excess_bp": 1e4 * float(excess.mean()),
            "net_t": t_net, "net_p": p_net, "net_abs_t": t_abs, "excess_ci_bp": [1e4 * lo, 1e4 * hi], "break_even_bp": be_bp,
            "auc": float(_auc(y, p)), "hit": float(((p > 0.5) == (y > 0)).mean()), "sharpe_net": S.sharpe(net, ppy),
            "total_net_pct": 100 * float(np.prod(1 + net) - 1), "max_dd_pct": 100 * S.max_drawdown(net)}


def _auc(y, p):
    from sklearn.metrics import roc_auc_score
    return roc_auc_score(y, p) if 0 < y.sum() < len(y) else 0.5


def judge(evals: dict, proto: Protocol):
    """Apply Holm across all candidates (data-snooping control) and the verdict rules. Returns the table and the overall decision."""
    names = [k for k, v in evals.items() if v.get("usable")]
    if not names: return {}, {"verdict": "HOLD", "reason": "not enough data"}
    ps = S.holm([evals[k]["skill_p"] for k in names]); pn = S.holm([evals[k]["net_p"] for k in names]); table = {}
    unit = evals[names[0]]["cost_unit_bp"]
    for i, k in enumerate(names):
        e = evals[k]
        g = {"skill": bool(ps[i] < proto.alpha and e["skill_dlogloss"] > 0),
             "shock": bool(e["skill_dlogloss_noshock"] > 0 and e["skill_p_noshock"] < proto.shock_alpha),
             "net": bool(pn[i] < proto.alpha and e["excess_ci_bp"][0] > 0 and e["mean_excess_bp"] > 0),
             "cost": bool(e["trades"] >= proto.min_trades and e["break_even_bp"] == e["break_even_bp"] and e["break_even_bp"] >= proto.margin * unit)}
        verdict = "GO" if all(g.values()) else ("WATCH" if (g["skill"] and g["shock"]) else "HOLD")
        table[k] = {**e, "skill_p_holm": ps[i], "net_p_holm": pn[i], "gates": g, "verdict": verdict}
    go = [k for k in table if table[k]["verdict"] == "GO"]; watch = [k for k in table if table[k]["verdict"] == "WATCH"]
    if go:
        best = max(go, key=lambda k: table[k]["net_t"]); dec = {"verdict": "GO", "candidate": best}
    elif watch:
        best = max(watch, key=lambda k: table[k]["skill_t"]); dec = {"verdict": "WATCH", "candidate": best}
    else:
        dec = {"verdict": "HOLD", "candidate": None}
    return table, dec


def explain(table: dict, dec: dict, proto: Protocol) -> str:
    """Plain-language reason for the decision, generated only from the numbers in the receipt."""
    if dec["verdict"] == "HOLD" and not table: return "HOLD: not enough usable data in the evidence window."
    unit = next(iter(table.values()))["cost_unit_bp"]
    if dec["verdict"] == "GO":
        e = table[dec["candidate"]]
        return (f"GO with '{dec['candidate']}': it beats the naive forecast (Holm p={e['skill_p_holm']:.3f}), keeps this without shock bars, earns "
                f"{e['mean_excess_bp']:.2f} bp per bar above an exposure-matched benchmark after costs (95% block-bootstrap interval "
                f"[{e['excess_ci_bp'][0]:.2f}, {e['excess_ci_bp'][1]:.2f}] bp), and its break-even cost {e['break_even_bp']:.1f} bp is at least {proto.margin:g} x the modelled cost {unit:.1f} bp.")
    if dec["verdict"] == "WATCH":
        e = table[dec["candidate"]]; fails = [g for g, v in e["gates"].items() if not v]
        return (f"WATCH: '{dec['candidate']}' beats the naive forecast in log-loss (Holm p={e['skill_p_holm']:.3f}) but it is not tradable: failed gate(s) {', '.join(fails)}; "
                f"break-even cost {e['break_even_bp']:.2f} bp against a modelled cost of {unit:.1f} bp (needs {proto.margin:g}x). This is the usual pattern: statistical skill, no economic edge. The wallet stays in reserve.")
    best = min(table, key=lambda k: table[k]["skill_p_holm"])
    return (f"HOLD: no candidate rejects 'no edge'. The most promising ('{best}') has Holm p={table[best]['skill_p_holm']:.3f} for forecasting skill. The wallet stays in reserve.")


def prevailing_rate(r):
    """Prevailing-mean benchmark: share of up-bars known strictly before each bar's forecast is made (a bar's target is known one bar later)."""
    y = (r > 0).astype(float); y[~np.isfinite(r)] = np.nan
    c = np.nancumsum(np.nan_to_num(y)); n = np.cumsum(np.isfinite(y)); out = np.full(len(r), 0.5)
    out[2:] = c[1:-1] / np.maximum(n[1:-1], 1); return out


def evaluate_window(P: dict, r: np.ndarray, a: int, b: int, base_rate, proto: Protocol, seed: int = 0, ppy: float = 8760.0):
    """P: candidate -> walk-forward probability array (full length). Evidence window = rows [a, b)."""
    evals = {k: evaluate_candidate(P[k][a:b], r[a:b], (base_rate[a:b] if np.ndim(base_rate) else base_rate), proto, seed + i, ppy) for i, k in enumerate(P)}
    table, dec = judge(evals, proto)
    return table, dec
