"""Builds docs/NullWallet_Slides.ipynb (one markdown cell per slide, inline-styled HTML + LaTeX)
and docs/NullWallet_Slides.html (same slides with MathML, 1280x720 cards for screenshots)."""
import json, base64, io, re, subprocess, os
EV = json.load(open('evidence/onchain_evidence.json')); TXS = '6 mined txs, status 1: ' + ', '.join(e['tx_hash'][:10] + '…' for e in EV)
SA = json.load(open('results/stats_audit.json'))['size_power']
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
NUM = json.load(open("results/figure_numbers.json"))
TEAM = os.environ.get("TEAM", "[TEAM NAME]"); MEMBERS = os.environ.get("MEMBERS", "[MEMBER NAMES, UNIVERSITY]"); CONTACT = os.environ.get("CONTACT", "[CONTACT EMAIL]")
NAVY, TEAL, ORANGE, MAGENTA, VIOLET, GREY, LIGHT, GREEN, RED = "#0B1F3A", "#00A6A6", "#FF7A1A", "#D6336C", "#6F42C1", "#5B6B7F", "#F2F6FA", "#2EB872", "#E03131"
FONT = "font-family:'Segoe UI',Helvetica,Arial,sans-serif;"

def img(name, h=380, w=None):
    im = Image.open(f"figs/{name}.png").convert("RGB"); r = 1100 / im.width
    if r < 1: im = im.resize((1100, int(im.height * r)))
    b = io.BytesIO(); im.save(b, "PNG", optimize=True)
    st = f"max-height:{h}px;max-width:{w or 100}%;" if not w else f"max-height:{h}px;max-width:{w}px;"
    return f'<img src="data:image/png;base64,{base64.b64encode(b.getvalue()).decode()}" style="{st}display:block;margin:0 auto;border-radius:6px;"/>'

def tile(big, cap, col): return f'<div style="flex:1;background:{col};border-radius:14px;padding:16px 14px;color:white;text-align:center;"><div style="font-size:44px;font-weight:800;line-height:1.05;">{big}</div><div style="font-size:15px;margin-top:6px;opacity:.95;">{cap}</div></div>'
def card(head, text, col): return f'<div style="background:{LIGHT};border-left:7px solid {col};border-radius:8px;padding:10px 14px;margin-bottom:9px;"><div style="font-weight:700;color:{col};font-size:16px;">{head}</div><div style="font-size:15px;color:{NAVY};line-height:1.35;">{text}</div></div>'
def sowhat(t, col): return f'<div style="background:{col};color:white;border-radius:10px;padding:11px 18px;font-size:17px;font-weight:600;margin-top:8px;"><span style="opacity:.8;">So what:</span> {t}</div>'
def math(t): return f'<div style="background:white;border:2px solid #DDE5EE;border-radius:10px;padding:8px 12px;margin-bottom:8px;font-size:19px;color:{NAVY};text-align:center;">{t}</div>'
def cols(*parts, gap=18, widths=None):
    ws = widths or [1] * len(parts)
    return f'<div style="display:flex;gap:{gap}px;align-items:stretch;">' + "".join(f'<div style="flex:{w};min-width:0;">{p}</div>' for p, w in zip(parts, ws)) + "</div>"
def table(rows, col, widths=None):
    h = "".join(f'<th style="background:{col};color:white;padding:8px 10px;text-align:left;font-size:15px;">{c}</th>' for c in rows[0])
    b = "".join("<tr>" + "".join(f'<td style="padding:7px 10px;font-size:14px;border-bottom:1px solid #DDE5EE;color:{NAVY};background:{"#fff" if i % 2 else LIGHT};">{c}</td>' for c in r) + "</tr>" for i, r in enumerate(rows[1:]))
    return f'<table style="border-collapse:collapse;width:100%;">{"<tr>"+h+"</tr>"+b}</table>'

def slide(n, tag, title, body, source, col):
    return (f'<div style="{FONT}width:1280px;height:720px;box-sizing:border-box;background:white;border:1px solid #CBD5E1;position:relative;overflow:hidden;">'
            f'<div style="position:absolute;left:0;top:0;bottom:0;width:14px;background:linear-gradient(180deg,{col},{NAVY});"></div>'
            f'<div style="position:absolute;right:0;top:0;width:340px;height:8px;background:linear-gradient(90deg,{ORANGE},{MAGENTA},{VIOLET});"></div>'
            f'<div style="padding:26px 44px 0 46px;"><span style="background:{col};color:white;border-radius:20px;padding:3px 14px;font-size:13px;font-weight:700;letter-spacing:1px;">{tag}</span>'
            f'<div style="font-size:29px;font-weight:800;color:{NAVY};line-height:1.2;margin:10px 0 14px 0;">{title}</div>'
            f'<div style="height:548px;overflow:hidden;">{body}</div></div>'
            f'<div style="position:absolute;left:46px;right:44px;bottom:12px;display:flex;justify-content:space-between;font-size:11.5px;color:{GREY};border-top:1px solid #DDE5EE;padding-top:6px;"><span>Source: {source}</span><span><b style="color:{col};">NULL Wallet</b> &nbsp;|&nbsp; {n}</span></div></div>')

S = []
# 1 title
S.append(f'<div style="{FONT}width:1280px;height:720px;box-sizing:border-box;background:linear-gradient(135deg,{NAVY} 0%,#13386B 55%,{VIOLET} 100%);color:white;position:relative;overflow:hidden;padding:90px 80px;">'
  f'<div style="position:absolute;right:-120px;top:-120px;width:460px;height:460px;border-radius:50%;background:{ORANGE};opacity:.85;"></div><div style="position:absolute;right:120px;bottom:-160px;width:340px;height:340px;border-radius:50%;background:{TEAL};opacity:.8;"></div><div style="position:absolute;right:360px;top:60px;width:120px;height:120px;border-radius:50%;background:{MAGENTA};opacity:.9;"></div>'
  f'<div style="font-size:16px;letter-spacing:3px;font-weight:700;color:{ORANGE};">2026 SHENZHEN INTERNATIONAL FINTECH COMPETITION | INTERNATIONAL TRACK | TOPIC F</div>'
  f'<div style="font-size:92px;font-weight:900;margin-top:50px;line-height:1;">NULL Wallet</div>'
  f'<div style="font-size:34px;font-weight:600;margin-top:22px;max-width:760px;line-height:1.25;">The AI wallet that must reject &ldquo;no edge&rdquo; before it moves money</div>'
  f'<div style="font-size:21px;margin-top:34px;opacity:.9;">$H_0$: no net edge after costs &nbsp;&rarr;&nbsp; reject with evidence, or refuse and record the refusal</div>'
  f'<div style="position:absolute;left:80px;bottom:60px;font-size:18px;line-height:1.6;">Theme: AI as a Financial Participant<br/>Team: {TEAM} &nbsp;|&nbsp; {MEMBERS} &nbsp;|&nbsp; {CONTACT}</div></div>')
# 2 exec summary
S.append(slide(2, "EXECUTIVE SUMMARY", "AI agents with wallets need proof, not just permission: NULL Wallet moves money only after rejecting &ldquo;no edge&rdquo;",
  cols(card("The gap", "Spend limits and allowlists ask <i>is this transfer permitted?</i> Nobody asks <i>is the reason real?</i> An agent can obey every limit and still trade on noise.", RED) +
       card("Our answer", "A wallet that must reject $H_0$ (no net edge after costs) with pre-registered, multiplicity-corrected tests before value moves. Every refusal is a hash-chained, on-chain-anchored record.", TEAL) +
       card("Result", "Strict where nothing exists to find, sensitive where something does, and honest about both.", VIOLET),
       f'<div style="display:flex;flex-direction:column;gap:12px;height:430px;"><div style="display:flex;gap:12px;flex:1;">{tile("0.0%","false GO in 1,000 no-edge simulated markets",TEAL)}{tile("92%","GO when a moderate edge truly exists",ORANGE)}</div><div style="display:flex;gap:12px;flex:1;">{tile("0 of 36","monthly verdicts on real BTC allowed trading",VIOLET)}{tile("-20%","wallet loss of the same models run without the court",MAGENTA)}</div></div>', widths=[1.05, 1]) +
  sowhat("evidence before permission makes an AI agent&rsquo;s wallet auditable, and refusing to trade becomes a result you can prove.", NAVY),
  "Team analysis; Monte Carlo of 1,000 simulated markets; replay of real BTC hourly data 2019-12-18 to 2022-11-14 (sandbox, assumed costs)", TEAL))
# 3 problem
S.append(slide(3, "PROBLEM", "Six families of causes make agents trade on false edges, and each one has a control in NULL Wallet",
  img("05_fishbone", 440) + sowhat("most losses come from acting on a pattern that was never real; the controls act on the <i>reason</i>, not only on the transfer.", RED),
  "Team root-cause analysis (fishbone); controls map to code modules in the repository", RED))
# 4 architecture
S.append(slide(4, "SOLUTION", "Two separated pipes decide <i>whether</i> to act and <i>how</i> to act, and meet only at the latest GO receipt",
  cols(img("01_architecture", 360),
       math(r"$$a_t=\mathbb{1}\left[\mathrm{GO}_{t}^{\,\mathrm{fresh}}\right]\cdot\mathbb{1}\left[\pi(i_t)=\mathrm{allow}\right]$$") +
       card("Evidence pipe", "Decides whether the strategy deserves capital.", TEAL) + card("Action pipe", "Decides whether this move is allowed. Plain code, no model.", VIOLET) +
       card("Ledger", "Hash-chained; head anchored on-chain.", ORANGE), widths=[1.45, 1]) +
  sowhat("a compromised or confused language layer still cannot sign anything the policy engine $\\pi$ does not approve.", TEAL),
  "NULL Wallet architecture (nullwallet/ package)", TEAL))
# 5 court
S.append(slide(5, "SOLUTION", "The Evidence Court turns six tools from our own assignments into one verdict: GO, WATCH or HOLD",
  cols(
    math(r"$d_t=\ell_t^{\mathrm{bench}}-\ell_t^{\mathrm{model}},\quad \mathrm{DM}=\dfrac{\bar d}{\sqrt{\widehat{\mathrm{LRV}}(d)/T}}$") +
    math(r"$\widehat{\mathrm{LRV}}=\hat\gamma_0+2\sum_{k=1}^{L}\left(1-\dfrac{k}{L+1}\right)\hat\gamma_k$ <span style='font-size:13px;color:#5B6B7F;'>(Newey-West)</span>") +
    math(r"$\mathrm{reject}\ H_{(i)}\iff p_{(i)}\le\dfrac{\alpha}{K-i+1}\ \ \text{for all } j\le i,\ K=5$ <span style='font-size:13px;color:#5B6B7F;'>(Holm)</span>") +
    math(r"$x_t=s_{t-1}r_t-\bar s\,r_t-c\,|s_t-s_{t-1}|,\quad c^{*}=\dfrac{\overline{s_{t-1}r_t-\bar s\,r_t}}{\overline{|s_t-s_{t-1}|}}$"),
    table([["Gate", "Question", "Pass rule"], ["G0", "Any look-ahead?", "truncation audit = 0"], ["G1", "Do OLS assumptions hold?", "always HAC / bootstrap"], ["G2", "Skill vs prevailing mean", "DM, Holm over 5"], ["G3", "Robust to shocks?", "drop beyond $5\\cdot1.4826\\,\\mathrm{MAD}$"], ["G4", "Net edge after cost", "HAC t, bootstrap LB $>0$"], ["G5", "Cost margin", "$c^{*}\\ge 2c$, trades $\\ge 10$"]], VIOLET), widths=[1.15, 1]) +
  sowhat("&ldquo;no trade&rdquo; is the default, and every GO has to survive data-snooping control and a $2\\times$ cost margin.", VIOLET),
  "Diebold-Mariano (1995), Newey-West (1987), Holm (1979), White (2000)", VIOLET))
# 6 pre-registration & ledger
S.append(slide(6, "SECURITY", "Pre-registration and a hash chain make every decision, and every refusal, tamper-evident",
  cols(math(r"$$h_0=\mathrm{SHA256}\!\left(\mathrm{canon}(\mathcal{P})\right)\quad\text{(protocol committed before data)}$$") +
       math(r"$$h_t=\mathrm{SHA256}\!\left(h_{t-1}\,\Vert\,\mathrm{canon}(e_t)\right)$$") +
       math(r"$$\mathrm{calldata}=\texttt{NULL1}\,\Vert\,h_t\quad\Rightarrow\quad\text{0-value self-transaction}$$") +
       card("Why it matters", "Edit, delete or reorder any entry and every later hash changes. Anchoring $h_t$ on-chain stops the tail from being cut silently.", ORANGE),
       img("04_ledger_chain", 330), widths=[1.1, 1]) +
  sowhat("the record of <i>why</i> the wallet acted, or refused, cannot be rewritten after the fact.", ORANGE),
  "nullwallet/ledger.py; nullwallet/onchain.py; tests/test_redteam.py (LedgerTamper)", ORANGE))
# 7 tiers
S.append(slide(7, "SECURITY", "Authority grows only as evidence grows: four tiers, and anything unknown is refused",
  cols(img("03_tiers", 330),
       math(r"$$\pi(i)=\mathrm{allow}\iff\bigwedge\begin{cases}\mathrm{schema}(i)\ \text{valid}\\ i.\mathrm{to}\in\mathcal{A}\ \text{(exact match)}\\ v\le 500,\ \ \textstyle\sum_{\mathrm{day}}v\le 1500\\ \mathrm{cooldown},\ \mathrm{fresh}\ \mathrm{GO}\ \mathrm{hash\ match}\\ \mathrm{drawdown}<10\%\end{cases}$$"), widths=[1.2, 1]) +
  cols(card("Isolated signer", "Key only in an environment variable; never in logs or receipts.", VIOLET), card("Strict intent schema", "Unknown fields are rejected; look-alike addresses fail.", VIOLET)) +
  sowhat("a request that is not on the allowlist, not fresh, or over a cap is refused by default.", VIOLET),
  "NULL Wallet policy engine (nullwallet/policy.py); tests/test_redteam.py", VIOLET))
# 8 bowtie
S.append(slide(8, "SECURITY", "Five threats are blocked before the event and four consequences are limited after it, backed by 51 tests",
  cols(img("06_bowtie", 380), img("18_tests", 380), widths=[1.3, 1]) + sowhat("even when the text parser is fooled, the policy engine still refuses (tested).", VIOLET),
  "Team bow-tie risk analysis; unittest results (51 passing)", VIOLET))
# 9 MC
S.append(slide(9, "EVIDENCE 1: STRESS TEST", "In 1,000 no-edge markets the court never approved a trade, yet it approves 92% when a moderate edge truly exists",
  cols(math(r"$r_t=\mu_t+\sigma_t\varepsilon_t,\quad \varepsilon_t\sim t_4,\quad \mu_t=-b\,r_{t-1}$") +
       math(r"$\sigma_t^2=\omega+\alpha\,\epsilon_{t-1}^2+\beta\,\sigma_{t-1}^2$ + jumps") +
       math(r"$\widehat{\mathrm{size}}=\dfrac{0}{1000}=0.0\%,\quad \Pr(\mathrm{false\ GO})\le 1-0.05^{1/1000}\approx 0.30\%$ <span style='font-size:13px;color:#5B6B7F;'>(95% bound)</span>") +
       card("Power as the edge $b$ grows", "0.7% (weak), 14%, 92%, 100%.", ORANGE) +
       card("Versus a naive picker", "Any-of-5 with raw $p<0.05$ and no cost margin trades in 2.4% of no-edge markets and 11.3% at weak edge.", RED),
       img("17_power", 400), widths=[1.1, 1]) +
  sowhat("strict where there is nothing to find, sensitive where there is something, with the trade-off shown openly.", ORANGE),
  "Monte Carlo (GARCH volatility, Student-t shocks, jumps; planted mean-reversion edge b); 1,000 markets at b=0, 300 per other level", ORANGE))
# 10 real data
S.append(slide(10, "EVIDENCE 2: REAL DATA", "On real BTC the court refused all 36 monthly decisions and avoided the 20% loss the same models suffered",
  cols(img("10_equity", 380), f'<div style="display:flex;flex-direction:column;gap:10px;">{tile("USD 10,000","NULL Wallet final value (held in reserve)",TEAL)}{tile("USD 8,000","same models without the court",MAGENTA)}{tile("0 of 36","windows with GO",VIOLET)}</div>', widths=[1.6, 1]) +
  sowhat("the court&rsquo;s value is not paying costs for an edge that does not survive them. Buy-and-hold (USD 24,778, max drawdown -77.1%) is not like-for-like.", TEAL),
  "BTC 5-min data aggregated to hourly, replay 2019-12-18 to 2022-11-14; sandbox with assumed costs, not live trading", TEAL))
# 11 skill vs edge
S.append(slide(11, "EVIDENCE 2: REAL DATA", "The models do beat a naive forecast, but their edge never reaches twice the cost: a result we reproduced",
  cols(img("14_breakeven", 390),
       math(r"$c=7.54\ \mathrm{bp}$ per switch <span style='font-size:13px;color:#5B6B7F;'>(fee, slippage, square-root impact, gas)</span>") +
       math(r"$\mathrm{GO}\iff \mathrm{G0..G5\ pass},\quad c^{*}\ge 2c$") +
       card("Funnel (36 windows)", "93 of 180 candidate tests show skill; none pass the net-edge gate or the cost margin.", ORANGE) +
       card("WATCH is a result", "The pattern is statistically there but not tradable, so the wallet stays in reserve.", VIOLET), widths=[1.4, 1]) +
  sowhat("statistical skill $\\neq$ economic edge: the break-even cost $c^{*}$ is the number that decides.", ORANGE),
  "Court receipts on real BTC; modelled cost 7.54 bp per switch, 2x margin required", ORANGE))
# 12 limits
S.append(slide(12, "EVIDENCE 3: HONEST LIMITS", "Stress-testing exposed a weakness that we fixed and disclose: a GO is evidence about the past, not a guarantee",
  cols(img("15_cost_sweep", 380),
       card("Cost sweep", "GO in 8 to 10 of 36 windows at zero cost (two machines), 1 at $0.25c$, none at $0.5c$ or above.", ORANGE) +
       card("A failure we found", "The zero-cost run lost money in the March 2020 crash.", RED) +
       math(r"$\hat\sigma_{24}>3\,\hat\sigma_{W}\ \Rightarrow\ s_t=0$ <span style='font-size:13px;color:#5B6B7F;'>(regime guard)</span>") +
       card("Disclosure", "The guard was added after the fact, so we claim no out-of-sample benefit.", VIOLET), widths=[1.4, 1]) +
  sowhat("caps, kill-switch and guard are essential; the honesty of the receipt is the product.", ORANGE),
  "Cost sweep on real BTC; regime guard added after the first replay (post hoc)", ORANGE))
# 13 innovation
S.append(slide(13, "INNOVATION", "What is new: evidence before permission, pre-registered and attested, with refusals as first-class records",
  cols(img("08_positioning", 400),
       card("1. Court gates", "Classical econometrics as a permission layer.", MAGENTA) + card("2. Data-snooping control", "Holm over every candidate tried.", MAGENTA) +
       card("3. Pre-registration", "Protocol hashed before the data is examined.", MAGENTA) + card("4. Attested refusals", "Every HOLD and WATCH is a receipt, anchored on-chain.", MAGENTA) +
       card("5. Language never reaches the key", "Typed intents and a deterministic gate.", MAGENTA), widths=[1.25, 1]) +
  sowhat("the standard tests are old; putting them in front of an agent&rsquo;s key, with proof of refusal, is the new part.", MAGENTA),
  "Public descriptions of agent-wallet products and arXiv 2601.04583 (survey); positioning is our qualitative judgement", MAGENTA))
# 14 coursework
S.append(slide(14, "INNOVATION", "Every gate is built from our own coursework, so the idea is unique to our work and we can defend each line",
  table([["Assignment", "What we did", "Where it lives in NULL Wallet"],
         ["Assumptions", "Assumption tests (Breusch-Pagan, Jarque-Bera, Ljung-Box), endogeneity, Monte Carlo of size and power", "G1 assumption audit; G0 look-ahead audit; the 1,000-market stress test"],
         ["Forecasting", "Pseudo-out-of-sample forecasts, Diebold-Mariano, ADF/KPSS, COVID dummies", "G2 skill duel; G3 shock robustness; walk-forward models"],
         ["Costs and multiple testing", "Net-of-cost edge, break-even cost, data snooping, neutral zone, HOLD/WATCH", "G4 net edge; G5 cost margin; Holm over candidates; dead-band; verdicts"],
         ["New", "Policy tiers, pre-registration, ledger, on-chain attestation", "Security and execution layers"]], MAGENTA) +
  sowhat("each statistic is one we derived and tested ourselves, which is why we can explain every number.", MAGENTA),
  "Standard methods", MAGENTA))
# 15 execution
S.append(slide(15, "EXECUTION AND NEXT STEPS", "Execution evidence is reproducible in three commands, and the roadmap moves from sandbox to live paper trading",
  cols(f'<div style="background:{NAVY};color:#E6EEF8;border-radius:10px;padding:14px 18px;font-family:Consolas,Menlo,monospace;font-size:14px;line-height:1.7;">pip install -r requirements.txt<br/>python -m unittest discover -s tests<br/>python run_all.py &lt;ohlcv.csv&gt;<br/>python -m nullwallet.webapp ledger.jsonl<br/>python onchain_demo.py ledger.jsonl --send</div>' +
       card("On-chain (Base mainnet)", "Zero-value attestations of the ledger head and refusals (T1). A capped vault transfer only if a GO exists (T2). Hashes: " + TXS + "", TEAL) +
       card("Ask", "Feedback on cost assumptions and a path to live paper trading with licensed data.", ORANGE), img("09_roadmap", 370), widths=[1, 1.15]) +
  sowhat("every claim can be re-run by a judge in minutes.", TEAL),
  "Repository README and docs; six Base mainnet transactions listed in evidence/onchain_evidence.json; check with verify_onchain.py", TEAL))
# appendix
S.append(slide(16, "APPENDIX", "Appendix A: classical regression assumptions fail on real BTC returns, so the court always uses robust inference",
  img("19_assumptions", 440) + sowhat("the court never trusts textbook standard errors: it uses HAC and block-bootstrap inference.", GREY), "Gate G1 on the real BTC sample", GREY))
S.append(slide(17, "APPENDIX", "Appendix B: after costs, the mean excess return of the GBM and reversal models is below zero in 36 and 35 of 36 windows",
  img("16_excess_ci", 440) + sowhat("95% block-bootstrap intervals per 30-day window sit below zero after costs.", GREY), "95% block-bootstrap intervals per 30-day window", GREY))
S.append(slide(18, "APPENDIX", "Appendix C: known risks and limits we state openly",
  table([["Limitation", "Mitigation or plan"], ["Sandbox, not live trading; costs are assumptions", "Cost sweep; live paper trading next"], ["A GO is evidence about the past", "Regime guard (post hoc), caps, kill-switch"], ["Monthly tests repeat, inflating false positives over time", "Four-gate rule; alpha-spending planned"], ["One main real dataset", "Synthetic markets; downloader for public data"], ["Ledger tail can be cut unless anchored", "On-chain head attestation"], ["Pure-Python signer is not constant-time", "Throwaway low-balance keys only; hardware/MPC signer for production"], ["Parser patterns can be evaded", "Policy engine is the real barrier"]], GREY),
  "docs/Security_Self_Assessment and technical documentation, Section 10", GREY))

S.append(slide(19, "APPENDIX", "Appendix D: the six Base mainnet transactions are mined, and each one carries a hash that exists in the ledger",
  table([["Label", "Block", "Transaction"]] + [[e['label'], str(e['receipt']['block']), e['tx_hash']] for e in EV], TEAL),
  "evidence/onchain_evidence.json; chain id 8453; calldata NULL1 + 32-byte hash; checked by verify_onchain.py", TEAL))
S.append(slide(20, "APPENDIX", "Appendix E: our tests match reference code to rounding error, and the HAC test is slightly oversized, which the extra gates compensate for",
  table([["Test", "Simulated size or power"]] + [[k, f"{v:.3f}"] for k, v in list(SA.items())[:9]], VIOLET) + sowhat("HAC one-sided size is 0.058 (iid) and 0.073 (AR(1)); G4 therefore also requires a bootstrap lower bound above zero and break-even cost of at least twice the cost.", VIOLET),
  "audit_stats.py; results/stats_audit.json", VIOLET))
S.append(slide(21, "APPENDIX", "Appendix F: the submission is checked against each point of the competition rules",
  table([["Rule or criterion", "Where it is met"], ["International Track, Topic F (Agent Wallet)", "Policy tiers T0 to T3, signer, ledger"], ["Task completion (40%)", "Working code, 51 tests, replay, 1,000-market Monte Carlo"], ["Security and compliance (30%)", "Security self-assessment, red-team tests, caps, allowlist, kill-switch"], ["Innovation and interaction (30%)", "Evidence-gated permission, attested refusals, chat and web demo"], ["On-chain bonus (0 to 5)", "6 real Base mainnet transactions"], ["Original work, licensed components", "Overlap report; open-source licences listed; AI assistance disclosed"], ["Deck at most 10 minutes", "15 main slides with timed notes; appendix excluded"]], GREY),
  "docs/RULES_COMPLIANCE.md", GREY))

# ---------------- notebook ----------------
head = ("# NULL Wallet: slides as a notebook\nEach cell below is one 16:9 slide (1280 x 720 px) written as HTML with LaTeX, so it renders in Jupyter. "
        "For screenshots open `NullWallet_Slides.html` in Chrome (same slides, math as MathML) and capture each card. "
        "Fill in the bracketed placeholders (team, names, links) by editing the cell text, or re-run `build_slides_nb.py` with `TEAM`, `MEMBERS`, `CONTACT` set.")
nb = {"cells": [{"cell_type": "markdown", "metadata": {}, "source": head.splitlines(True)}] + [{"cell_type": "markdown", "metadata": {"tags": ["slide"]}, "source": s.splitlines(True)} for s in S],
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open("docs/NullWallet_Slides.ipynb", "w"), indent=1)

# ---------------- html with MathML via pandoc ----------------
pat = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$", re.S)
def to_mathml(slides):
    forms = []
    def grab(m): forms.append(m.group(0)); return f"@@M{len(forms)-1}@@"
    stripped = [pat.sub(grab, s) for s in slides]
    src = "\n\n".join(forms); open("/tmp/_m.md", "w").write(src)
    out = subprocess.run(["pandoc", "/tmp/_m.md", "-f", "markdown", "-t", "html5", "--mathml"], capture_output=True, text=True, check=True).stdout
    ps = re.findall(r"<p>(.*?)</p>", out, re.S); assert len(ps) == len(forms), (len(ps), len(forms))
    ps = [p.replace('display="inline"', 'display="inline"') for p in ps]
    return [re.sub(r"@@M(\d+)@@", lambda m: ps[int(m.group(1))], s) for s in stripped]
H = to_mathml(S)
page = ("<!doctype html><html lang='en'><head><meta charset='utf-8'><title>NULL Wallet slides</title><style>body{margin:0;background:#CBD5E1;padding:30px 0;}.s{margin:0 auto 34px auto;width:1280px;box-shadow:0 4px 18px rgba(0,0,0,.25);}math{font-size:1.05em;}math[display=block]{display:block math;margin:4px 0;}</style></head><body>"
        + "".join(f"<div class='s' id='slide{i+1}'>{h}</div>" for i, h in enumerate(H)) + "</body></html>")
open("docs/NullWallet_Slides.html", "w").write(page)
print("slides", len(S), "html KB", len(page) // 1024)
