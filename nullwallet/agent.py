"""The rolling NULL-Wallet loop. Every `step` bars: (1) court on the trailing evidence window, (2) receipt appended to the hash-chained ledger,
(3) if GO the agent may hold the candidate's position for the next `step` bars; otherwise it stays flat and the refusal is attested.
Value moves (reserve -> active) only through the policy engine."""
from __future__ import annotations
import numpy as np
from dataclasses import asdict
from . import court, policy
from .ledger import Ledger
from .sandbox import Sandbox

VAULT = "0x" + "11" * 20


def run(P, r, proto: court.Protocol, start: int, end: int, window: int = 4320, step: int = 720, ledger: Ledger | None = None,
        lim: policy.Limits | None = None, ppy: float = 8760.0, with_court: bool = True, force_candidate: str | None = None, seed: int = 0, active0: float = 2000.0):
    ledger = ledger or Ledger(); lim = lim or policy.Limits(allowlist=(VAULT,), cooldown=1, max_evidence_age=2 * step)
    unit = court.CostModel(**proto.cost).unit_cost(); sb = Sandbox(reserve=10000.0 - active0, active=active0, unit_cost=unit); st = policy.State(bar_per_day=24)
    base = court.prevailing_rate(r)
    ledger.append("commit", {"protocol": asdict(proto), "protocol_hash": proto.digest(), "first_bar": start}, clock=start)
    path = []; ex_path = np.zeros(len(r)); decisions = []; latest_go = None; refusals = 0; regime_events = 0
    for t0 in range(start, end, step):
        t1 = min(t0 + step, end); st.clock = t0
        if with_court:
            tab, dec = court.evaluate_window(P, r, t0 - window, t0, base, proto, seed + t0, ppy)
            body = {"window": [t0 - window, t0], "decision": dec, "why": court.explain(tab, dec, proto),
                    "table": {k: {kk: v[kk] for kk in ("verdict", "skill_p_holm", "net_p_holm", "mean_excess_bp", "excess_ci_bp", "break_even_bp", "trades", "gates")} for k, v in tab.items()}}
            rec = ledger.append("verdict", body, clock=t0); cand = dec.get("candidate") if dec["verdict"] == "GO" else None
            if dec["verdict"] == "GO": latest_go = {"hash": rec["hash"], "clock": t0}
            else:
                refusals += 1; ledger.append("refusal", {"verdict": dec["verdict"], "receipt": rec["hash"], "attest": "NULL1" + rec["hash"]}, clock=t0)
        else:
            cand = force_candidate; dec = {"verdict": "NO_COURT", "candidate": cand}
        decisions.append((t0, dec["verdict"], cand))
        # value movement only with a fresh GO: fund the active bucket
        if with_court and cand:
            it = policy.Intent("move", amount_usd=min(500.0, sb.reserve), to=VAULT, evidence_hash=latest_go["hash"])
            if sb.active < 2000.0 and sb.reserve > 0:
                dd = policy.evaluate(it, lim, st, latest_go); ledger.append("intent", {"intent": asdict(it), "decision": dict(dd)}, clock=t0)
                if dd.ok: sb.move(it.amount_usd, True); policy.commit(it, st)
        base_vol = float(np.nanstd(r[t0 - window:t0])); void = False
        for t in range(t0, t1):
            pr = P[cand][t] if cand else np.nan
            recent = float(np.nanstd(r[max(t - proto.vol_lb, 0):t]))           # only returns already known at bar t
            now_void = bool(cand) and recent > proto.vol_mult * base_vol
            if now_void != void and with_court:
                ledger.append("regime_guard", {"bar": t, "state": "evidence_void" if now_void else "evidence_valid", "recent_vol": recent, "window_vol": base_vol}, clock=t); regime_events += 1
            void = now_void
            want = 1.0 if (cand and np.isfinite(pr) and pr > 0.5 + proto.tau and not st.killed and not void) else 0.0
            if not with_court: want = 1.0 if (cand and np.isfinite(pr) and pr > 0.5 + proto.tau) else 0.0   # no-court baselines have no guards at all
            sb.set_exposure(want); ex_path[t] = want
            if np.isfinite(r[t]): sb.mark(r[t])
            st.clock = t; policy.update_equity(st, lim, sb.equity)
            if st.killed: sb.set_exposure(0.0)
            path.append(sb.equity)
    return {"equity": np.array(path), "exposure": ex_path[start:end], "decisions": decisions, "ledger": ledger, "cost_paid": sb.cost_paid, "refusals": refusals, "killed": st.killed, "regime_events": regime_events}


def buy_hold(r, start, end, capital=10000.0):
    x = np.nan_to_num(r[start:end]); return capital * np.cumprod(1 + x)
