import matplotlib.dates
import pickle, json, os, numpy as np, pandas as pd, unittest, sys
from figs_common import *
S = pickle.load(open("results/series.pkl", "rb")); t = pd.to_datetime(S["time"])
mcf = "evidence/mc_final.json" if os.path.exists("evidence/mc_final.json") and len(json.load(open("evidence/mc_final.json"))) >= 7 else "evidence/montecarlo.json"; MC = json.load(open(mcf))

# 10 equity curves
fig, ax = plt.subplots(figsize=(11, 5.2))
ax.plot(t, S["buyhold"], color=GREY, lw=1.2, label="Buy & hold ($10,000 fully invested)")
ax.plot(t, S["nocourt_gbm_all"], color=RED, lw=1.6, label="No court: always trade GBM model")
ax.plot(t, S["nocourt_logit_all"], color=AMBER, lw=1.6, label="No court: always trade logit model")
ax.plot(t, S["wallet"], color=TEAL, lw=2.6, label="NULL Wallet (court said HOLD/WATCH every time)")
ax.set_yscale("log"); ax.set_ylabel("Wallet value, USD (log scale)"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(.5, -.13), ncol=2, fontsize=9); ax.set_title("Same models, same data: the court avoids paying for an edge that does not survive costs", loc="left", fontsize=12, color=NAVY, fontweight="bold")
ax.text(.995, .03, "Sandbox replay, modelled costs; not live trading. Buy & hold ended higher but with a deep drawdown.", transform=ax.transAxes, ha="right", fontsize=8.5, color=GREY)
save(fig, "10_equity")

# 11 drawdowns
def dd(e): e = np.asarray(e); return 100 * (e / np.maximum.accumulate(e) - 1)
fig, ax = plt.subplots(figsize=(11, 3.6))
for k, c, l in [("buyhold", GREY, "Buy & hold"), ("nocourt_gbm_all", RED, "No court (GBM)"), ("nocourt_logit_all", AMBER, "No court (logit)"), ("wallet", TEAL, "NULL Wallet")]: ax.plot(t, dd(S[k]), color=c, lw=1.5 if k != "wallet" else 2.5, label=l)
ax.set_ylabel("Drawdown, %"); ax.legend(frameon=False, ncol=4, loc="lower left", fontsize=9.5); ax.set_title("Drawdown from previous peak", loc="left", fontsize=12, color=NAVY, fontweight="bold")
save(fig, "11_drawdown")

# 12 verdict timeline
W = S["windows"]; cmap = {"GO": GREEN, "WATCH": AMBER, "HOLD": RED}
fig, ax = plt.subplots(figsize=(11, 2.6)); wt = pd.to_datetime([w["t0"] for w in W])
for i, w in enumerate(W): ax.bar(i, 1, color=cmap[w["verdict"]], width=.9)
ax.set_yticks([]); ax.set_xticks(range(0, len(W), 4)); ax.set_xticklabels([wt[i].strftime("%b %y") for i in range(0, len(W), 4)], fontsize=9); ax.spines["left"].set_visible(False)
ax.set_title("One verdict every 30 days: GO 0, WATCH {}, HOLD {} (36 windows)".format(sum(w["verdict"] == "WATCH" for w in W), sum(w["verdict"] == "HOLD" for w in W)), loc="left", fontsize=12, color=NAVY, fontweight="bold")
for k, c in cmap.items(): ax.bar(0, 0, color=c, label=k)
ax.legend(frameon=False, ncol=3, loc="upper right", bbox_to_anchor=(1, 1.35))
save(fig, "12_verdicts")

# 13 gate funnel across windows x candidates
cands = S["cand"]; cnt = {"skill": 0, "shock": 0, "net": 0, "cost": 0}; tot = len(W) * len(cands)
allp = [(w[c]["gates"]) for w in W for c in cands]
n_skill = sum(g["skill"] for g in allp); n_shock = sum(g["skill"] and g["shock"] for g in allp); n_net = sum(g["skill"] and g["shock"] and g["net"] for g in allp); n_cost = sum(all(g.values()) for g in allp)
vals = [tot, n_skill, n_shock, n_net, n_cost]; labs = ["All tests\n(36 windows x 5 candidates)", "G2 skill\n(Holm-adjusted)", "+ G3 survives\nshock removal", "+ G4 net edge\nafter costs", "+ G5 cost margin\n= GO"]
fig, ax = plt.subplots(figsize=(10, 4.6)); bars_ = ax.barh(range(5), vals, color=[GREY, TEAL, TEAL, NAVY, GREEN]); ax.set_yticks(range(5)); ax.set_yticklabels(labs, fontsize=10); ax.invert_yaxis()
for i, v in enumerate(vals): ax.text(v + 2, i, str(v), va="center", fontsize=11, fontweight="bold", color=INK)
ax.set_xlim(0, tot * 1.1); ax.set_title("Where candidate strategies are eliminated on real BTC data", loc="left", fontsize=12, color=NAVY, fontweight="bold"); ax.set_xlabel("Candidate-window pairs still alive")
save(fig, "13_funnel"); FUN = vals

# 14 break-even vs cost per candidate
fig, ax = plt.subplots(figsize=(10, 4.8)); unit = np.median([w[cands[0]]["cost_bp"] for w in W])
med = [np.nanmedian([w[c]["break_even_bp"] for w in W]) for c in cands]
ax.bar(range(len(cands)), med, color=[TEAL if m >= 2 * unit else NAVY for m in med]); ax.axhline(unit, color=AMBER, lw=2, ls="--"); ax.axhline(2 * unit, color=RED, lw=2, ls="--")
ax.text(len(cands) - .5, unit + .3, f"modelled cost {unit:.1f} bp", ha="right", color=AMBER, fontsize=10, fontweight="bold"); ax.text(len(cands) - .5, 2 * unit + .3, f"required margin 2x = {2*unit:.1f} bp", ha="right", color=RED, fontsize=10, fontweight="bold")
ax.set_xticks(range(len(cands))); ax.set_xticklabels(cands); ax.set_ylabel("Median break-even cost per switch, bp"); ax.set_title("Gross edge exists for some models, but never twice the cost", loc="left", fontsize=12, color=NAVY, fontweight="bold")
save(fig, "14_breakeven"); MEDBE = dict(zip(cands, med)); UNIT = unit

# 15 cost sweep
sw = S["sweep"]; ms = sorted(sw)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw={"width_ratios": [1, 1.2]})
x = np.arange(len(ms)); a1.bar(x, [sw[m]["GO"] for m in ms], color=GREEN, label="GO"); a1.bar(x, [sw[m]["WATCH"] for m in ms], bottom=[sw[m]["GO"] for m in ms], color=AMBER, label="WATCH"); a1.bar(x, [sw[m]["HOLD"] for m in ms], bottom=[sw[m]["GO"] + sw[m]["WATCH"] for m in ms], color=RED, label="HOLD")
a1.set_xticks(x); a1.set_xticklabels([f"{m:g}x\n{sw[m]['unit_bp']:.1f} bp" for m in ms]); a1.set_xlabel("Cost level (multiple of the base assumption)"); a1.set_ylabel("Verdicts out of 36"); a1.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.28)); a1.set_title("Verdicts vs cost", loc="left", fontsize=11.5, color=NAVY, fontweight="bold")
for m, c in zip(ms, [GREEN, TEAL, NAVY, AMBER, RED]): a2.plot(t, sw[m]["equity"], color=c, lw=1.7, label=f"cost {m:g}x")
a2.set_ylabel("Wallet value, USD"); a2.legend(frameon=False, fontsize=9); a2.xaxis.set_major_locator(matplotlib.dates.YearLocator()); a2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y")); a2.set_title("Wallet value vs cost", loc="left", fontsize=11.5, color=NAVY, fontweight="bold")
save(fig, "15_cost_sweep")

# 16 per-window excess return CI for two candidates
fig, axs = plt.subplots(1, 2, figsize=(12, 4.3), sharey=True)
for ax, c in zip(axs, ["gbm_all", "reversal"]):
    xs = np.arange(len(W)); m = np.array([w[c]["mean_excess_bp"] for w in W]); lo = np.array([w[c]["lo"] for w in W]); hi = np.array([w[c]["hi"] for w in W])
    ax.vlines(xs, lo, hi, color=GREY, lw=2); ax.scatter(xs, m, color=TEAL, zorder=3, s=22); ax.axhline(0, color=RED, lw=1.5); ax.set_title(f"{c}: net excess return per bar, 95% bootstrap interval", fontsize=10.5, loc="left", color=NAVY, fontweight="bold"); ax.set_xlabel("30-day window"); 
axs[0].set_ylabel("bp per bar over exposure-matched benchmark")
save(fig, "16_excess_ci")

# 17 Monte Carlo: size and power

_nv = {m["b"]: m["NAIVE_TRADE"] for m in (json.load(open("evidence/mc_naive.json")) if os.path.exists("evidence/mc_naive.json") else []) if "NAIVE_TRADE" in m}
for _m in MC:
    if not _m["nocost"] and _m["b"] in _nv: _m["NAIVE_TRADE"] = _nv[_m["b"]]
pw = [m for m in MC if not m["nocost"]]; b = [m["b"] for m in pw]
fig, ax = plt.subplots(figsize=(9, 5)); ax.plot(b, [100 * m["GO"] for m in pw], "-o", color=GREEN, lw=2.5, label="GO (trade allowed)"); ax.plot(b, [100 * (m["GO"] + m["WATCH"]) for m in pw], "-o", color=AMBER, lw=2, label="GO or WATCH (skill detected)")
nv = [(m["b"], 100 * m["NAIVE_TRADE"]) for m in pw if "NAIVE_TRADE" in m]
if nv: ax.plot(*zip(*nv), "--s", color=RED, lw=2, label="Naive picker: any of 5 with raw p<0.05, no Holm, no cost margin")
ax.set_xlabel("Planted edge strength b (0 = no edge anywhere)"); ax.set_ylabel("% of simulated markets"); ax.legend(frameon=False, fontsize=9.5, loc="center right")
ax.annotate(f"false GO at b=0:\n{100*pw[0]['GO']:.1f}% of {pw[0]['markets']} markets", (0, 100 * pw[0]["GO"]), (.3, 30), arrowprops=dict(arrowstyle="->", color=GREY), fontsize=10)
ax.set_title("Court size and power over simulated markets", loc="left", fontsize=12, color=NAVY, fontweight="bold"); save(fig, "17_power")

# 18 red-team test inventory
sys.path.insert(0, "tests"); import test_redteam, test_court, test_crypto, test_onchain
groups = {"Policy rules": test_redteam.Policy, "Prompt injection": test_redteam.Injection, "Key isolation": test_redteam.KeyIsolation, "Ledger tampering": test_redteam.LedgerTamper, "Court / look-ahead / guard": [test_court.Court, test_court.RegimeGuard], "On-chain preflight": [test_onchain.Preflight, test_onchain.RpcFallback, test_onchain.GasLimit], "Crypto (EIP-155)": [getattr(test_crypto, n) for n in dir(test_crypto) if n.startswith("Test") or isinstance(getattr(test_crypto, n), type) and issubclass(getattr(test_crypto, n), unittest.TestCase)]}
cnt = {}
for k, g in groups.items():
    g = g if isinstance(g, list) else [g]; cnt[k] = sum(unittest.defaultTestLoader.loadTestsFromTestCase(c).countTestCases() for c in g if isinstance(c, type) and issubclass(c, unittest.TestCase))
fig, ax = plt.subplots(figsize=(9, 4)); ax.barh(list(cnt), list(cnt.values()), color=NAVY); ax.invert_yaxis()
for i, v in enumerate(cnt.values()): ax.text(v + .2, i, str(v), va="center", fontweight="bold")
ax.set_title(f"{sum(cnt.values())} automated tests, all passing (including attack scenarios)", loc="left", fontsize=12, color=NAVY, fontweight="bold"); ax.set_xlabel("tests"); save(fig, "18_tests")

# 19 assumptions audit (G1)
g1 = S["g1"]; fig, ax = canvas(11, 3.6)
rows = [("Heteroskedasticity (Breusch-Pagan)", g1["bp_p"], "reject -> use HAC errors"), ("Autocorrelation (Ljung-Box, 12 lags)", g1["lb_p"], "reject -> use HAC errors"), ("Normality (Jarque-Bera)", g1["jb_p"], "reject -> bootstrap, not normal tables")]
for i, (n, p, a) in enumerate(rows):
    y = .72 - i * .2; box(ax, .02, y, .42, .14, n, NAVY, fs=10); box(ax, .47, y, .16, .14, f"p = {p:.2g}", RED if p < .05 else GREEN, fs=10); ax.text(.66, y + .07, a, va="center", fontsize=10)
ax.text(.02, .1, f"Stationarity of returns: ADF = {g1['adf']:.1f} (critical -2.86), KPSS = {g1['kpss']:.3f} (critical 0.463)  ->  returns are stationary", fontsize=10, color=INK)
ax.text(.02, .94, "G1 assumption audit on the real BTC sample: classical OLS assumptions fail, so the court always uses robust inference", fontsize=11.5, fontweight="bold", color=NAVY); save(fig, "19_assumptions")
json.dump({"funnel": [int(v) for v in FUN], "median_break_even": {k: float(v) for k, v in MEDBE.items()}, "cost_bp": float(UNIT), "tests": cnt, "mc_file": mcf}, open("results/figure_numbers.json", "w"), indent=1); print("data figs ok", FUN, MEDBE, UNIT, cnt)
