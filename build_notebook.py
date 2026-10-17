import json, pickle, base64, io, contextlib, os, re, sys, numpy as np
sys.path.insert(0, ".")
S = pickle.load(open("results/series.pkl", "rb")); FN = json.load(open("results/figure_numbers.json"))
mcf = "evidence/mc_final.json" if os.path.exists("evidence/mc_final.json") and len(json.load(open("evidence/mc_final.json"))) >= 7 else "evidence/montecarlo.json"; MC = json.load(open(mcf))

_nv = {m["b"]: m["NAIVE_TRADE"] for m in (json.load(open("evidence/mc_naive.json")) if os.path.exists("evidence/mc_naive.json") else []) if "NAIVE_TRADE" in m}
for _m in MC:
    if not _m["nocost"] and _m["b"] in _nv: _m["NAIVE_TRADE"] = _nv[_m["b"]]
RS = json.load(open("evidence/replay_summary_v1.json")); W = S["windows"]
def dd(e): e = np.asarray(e); return 100 * float(np.min(e / np.maximum.accumulate(e) - 1))
vc = {k: sum(w["verdict"] == k for w in W) for k in ("GO", "WATCH", "HOLD")}
fin = {k: float(np.asarray(S[k])[-1]) for k in ("wallet", "nocourt_gbm_all", "nocourt_logit_all", "buyhold")}
h0 = [m for m in MC if m["b"] == 0 and not m["nocost"]][0]; h0n = [m for m in MC if m["b"] == 0 and m["nocost"]][0]; pw = {m["b"]: m for m in MC if not m["nocost"]}
sw = S["sweep"]; naive = "NAIVE_TRADE" in h0
N = {"periodstart": str(S["time"][0])[:10], "periodend": str(S["time"][-1])[:10], "nbars": f"{len(S['time']):,}",
     "go": vc["GO"], "watch": vc["WATCH"], "hold": vc["HOLD"], "w_final": f"{fin['wallet']:,.0f}", "g_final": f"{fin['nocourt_gbm_all']:,.0f}", "l_final": f"{fin['nocourt_logit_all']:,.0f}", "bh_final": f"{fin['buyhold']:,.0f}",
     "g_dd": f"{dd(S['nocourt_gbm_all']):.1f}", "l_dd": f"{dd(S['nocourt_logit_all']):.1f}", "bh_dd": f"{dd(S['buyhold']):.1f}", "g_cost": f"{RS['1h']['cost_paid_usd']['no_court_gbm']:,.0f}", "l_cost": f"{RS['1h']['cost_paid_usd']['no_court_logit']:,.0f}",
     "h0m": f"{h0['markets']:,}", "h0go": f"{100*h0['GO']:.1f}", "h0w": f"{100*h0['WATCH']:.1f}", "h0nc": f"{100*h0n['GO']:.1f}", "h0ncw": f"{100*h0n['WATCH']:.1f}",
     "p05": f"{100*pw[0.05]['GO']:.1f}", "p10": f"{100*pw[0.1]['GO']:.0f}", "p20": f"{100*pw[0.2]['GO']:.0f}", "p40": f"{100*pw[0.4]['GO']:.0f}", "s10": f"{100*(pw[0.1]['GO']+pw[0.1]['WATCH']):.0f}", "s05": f"{100*(pw[0.05]['GO']+pw[0.05]['WATCH']):.0f}",
     "mmax": f"{pw[0.2]['markets']}", "unit": f"{FN['cost_bp']:.1f}", "f0": FN["funnel"][0], "f1": FN["funnel"][1], "f2": FN["funnel"][2], "f3": FN["funnel"][3], "f4": FN["funnel"][4],
     "be_rev": f"{FN['median_break_even']['reversal']:.1f}", "be_gbm": f"{FN['median_break_even']['gbm_all']:.1f}", "be_tr": f"{FN['median_break_even']['trend']:.1f}", "be_lg": f"{FN['median_break_even']['logit_all']:.1f}", "be_rsi": f"{FN['median_break_even']['rsi_reversal']:.1f}",
     "swgo0": sw[0.0]["GO"], "sweq0": f"{sw[0.0]['equity'][-1]:,.0f}", "swgo25": sw[0.25]["GO"], "sweq25": f"{sw[0.25]['equity'][-1]:,.0f}", "g1bp": f"{S['g1']['bp_p']:.1e}", "g1lb": f"{S['g1']['lb_p']:.1e}", "g1adf": f"{S['g1']['adf']:.1f}", "g1kpss": f"{S['g1']['kpss']:.3f}",
     "ntests": sum(FN["tests"].values()), "proto": S["protocol_hash"][:16], "naive": (f"{100*h0['NAIVE_TRADE']:.1f}" if naive else "n/a"), "naive05": (f"{100*pw[0.05]['NAIVE_TRADE']:.0f}" if naive else "n/a"), "naive10": (f"{100*pw[0.1]['NAIVE_TRADE']:.0f}" if naive and 'NAIVE_TRADE' in pw[0.1] else "n/a"), "nledger": S["n_ledger"], "mcfile": os.path.basename(mcf)}
OC = json.load(open("evidence/out_of_course_binance2023/summary.json")); o1, o4 = OC["1h"], OC["4h"]
N.update({"oc1h": o1["bars"], "oc4h": o4["bars"], "oc1v": "GO %d / WATCH %d / HOLD %d" % tuple(o1["verdicts"][k] for k in ("GO","WATCH","HOLD")), "oc4v": "GO %d / WATCH %d / HOLD %d" % tuple(o4["verdicts"][k] for k in ("GO","WATCH","HOLD")), "ocg": f"{o1['final_equity']['no_court_gbm']:,.0f}", "ocl": f"{o1['final_equity']['no_court_logit']:,.0f}"})
GD = json.load(open("results/go_demo.json")); N.update({"gd_go": GD["verdicts"]["GO"], "gd_n": sum(GD["verdicts"].values()), "gd_moves": GD["approved_moves"], "gd_final": f"{GD['final_equity']:,.0f}", "gd_bh": f"{GD['buy_hold_same_bars']:,.0f}", "gd_guard": GD["regime_guard_events"], "gd_min": f"{GD['min_equity']:,.0f}"})
cells = []
def md(t): cells.append(("md", t.strip("\n")))
def code(t): cells.append(("code", t.strip("\n")))
def fig(name, cap=""): code(f'from IPython.display import Image, display\ndisplay(Image("figs/{name}.png"))' + (f"\n# {cap}" if cap else ""))
exec(open("notebook_text.py").read())
# mini executor: embeds figures, captures printed output
ns = {}; out_cells = []; cnt = 0
for kind, src in cells:
    if kind == "md":
        for k, v in N.items(): src = src.replace(f"@@{k}@@", str(v))
        out_cells.append({"cell_type": "markdown", "metadata": {}, "source": src.splitlines(True)})
    else:
        cnt += 1; outs = []; m = re.search(r'figs/([\w\-]+)\.png', src)
        if m: outs.append({"output_type": "display_data", "metadata": {}, "data": {"image/png": base64.b64encode(open(f"figs/{m.group(1)}.png", "rb").read()).decode(), "text/plain": ["<IPython.core.display.Image object>"]}})
        else:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf): exec(src, ns)
            if buf.getvalue(): outs.append({"output_type": "stream", "name": "stdout", "text": buf.getvalue().splitlines(True)})
        out_cells.append({"cell_type": "code", "execution_count": cnt, "metadata": {}, "source": src.splitlines(True), "outputs": outs})
nb = {"cells": out_cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open("docs/NullWallet_Technical_Documentation.ipynb", "w"), indent=1); print("cells", len(out_cells), "N sample", {k: N[k] for k in ("h0go", "p10", "p20", "naive", "mcfile")})
