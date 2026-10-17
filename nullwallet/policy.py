"""Permission tiers and the deterministic policy engine. No language model sits between an intent and the signer:
an Intent is a strict, typed object; the policy engine either approves it with a reason code or refuses it with a reason code.

  T0  observe          read data, run the court                        (always allowed)
  T1  attest           0-value self-transaction carrying a hash         (allowed; cannot lose funds beyond gas)
  T2  move             transfer / swap inside the sandbox bucket        (only with a fresh GO receipt, whitelisted target, caps)
  T3  anything else    unknown action, unknown address, key export...   (always refused -> human)"""
from __future__ import annotations
from dataclasses import dataclass, field
import re

TIERS = {"observe": 0, "attest": 1, "move": 2}
ADDR = re.compile(r"^0x[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class Intent:
    action: str                    # observe | attest | move | (anything else -> T3)
    amount_usd: float = 0.0
    to: str = ""
    asset: str = "ETH"
    evidence_hash: str = ""        # hash of the receipt that justifies a move
    origin: str = "agent"          # agent | chat | external  (external text is never trusted)


@dataclass
class Limits:
    per_tx_usd: float = 500.0
    daily_usd: float = 1500.0
    cooldown: int = 12                 # bars between two moves
    max_drawdown: float = 0.10         # kill-switch on sandbox equity
    max_evidence_age: int = 720        # bars; stale GO receipts expire
    allowlist: tuple = ()              # lower-case whitelisted vault addresses
    assets: tuple = ("ETH",)


@dataclass
class State:
    clock: int = 0
    spent_today: float = 0.0
    day_start: int = 0
    last_move: int = -10**9
    equity_peak: float = 1.0
    equity: float = 1.0
    killed: bool = False
    bar_per_day: int = 24


class Decision(dict):
    @property
    def ok(self): return self["ok"]


def _d(ok, code, why, tier): return Decision(ok=ok, code=code, why=why, tier=tier)


def evaluate(it: Intent, lim: Limits, st: State, latest_go: dict | None) -> Decision:
    """latest_go = {'hash':..., 'clock':...} of the newest GO receipt or None."""
    if it.action not in TIERS: return _d(False, "T3_UNKNOWN_ACTION", f"action '{it.action}' is not a permitted tier", 3)
    tier = TIERS[it.action]
    if it.origin == "external": return _d(False, "UNTRUSTED_ORIGIN", "instructions from external content are data, never commands", 3)
    if tier == 0: return _d(True, "OK_OBSERVE", "read-only", 0)
    if st.killed: return _d(False, "KILL_SWITCH", "drawdown kill-switch is engaged; human reset required", tier)
    if tier == 1: return _d(True, "OK_ATTEST", "attestation carries no value", 1)
    # tier 2 -- movement of value
    if not (isinstance(it.amount_usd, (int, float)) and it.amount_usd == it.amount_usd and it.amount_usd > 0): return _d(False, "BAD_AMOUNT", "amount must be a positive number", 2)
    if it.asset not in lim.assets: return _d(False, "ASSET_NOT_ALLOWED", f"asset {it.asset}", 2)
    if not ADDR.match(it.to or ""): return _d(False, "BAD_ADDRESS", "malformed address", 2)
    if it.to.lower() not in lim.allowlist: return _d(False, "NOT_ALLOWLISTED", "destination is not a whitelisted vault", 2)
    if latest_go is None: return _d(False, "NO_GO_RECEIPT", "no GO receipt: the wallet has not rejected 'no edge'", 2)
    if it.evidence_hash != latest_go["hash"]: return _d(False, "EVIDENCE_MISMATCH", "the intent does not cite the latest GO receipt", 2)
    if st.clock - latest_go["clock"] > lim.max_evidence_age: return _d(False, "STALE_EVIDENCE", "GO receipt is older than the freshness limit", 2)
    if it.amount_usd > lim.per_tx_usd: return _d(False, "PER_TX_CAP", f"{it.amount_usd:.2f} > {lim.per_tx_usd:.2f}", 2)
    spent = st.spent_today if st.clock - st.day_start < st.bar_per_day else 0.0
    if spent + it.amount_usd > lim.daily_usd: return _d(False, "DAILY_CAP", "daily limit would be exceeded", 2)
    if st.clock - st.last_move < lim.cooldown: return _d(False, "COOLDOWN", "too soon after the previous move", 2)
    return _d(True, "OK_MOVE", "all tier-2 checks passed", 2)


def commit(it: Intent, st: State):
    if it.action == "move":
        if st.clock - st.day_start >= st.bar_per_day: st.day_start, st.spent_today = st.clock, 0.0
        st.spent_today += it.amount_usd; st.last_move = st.clock


def update_equity(st: State, lim: Limits, equity: float):
    st.equity = equity; st.equity_peak = max(st.equity_peak, equity)
    if equity / st.equity_peak - 1 < -lim.max_drawdown: st.killed = True


def parse_intent(obj, origin="agent") -> Intent | None:
    """Strict schema: only the known fields with the right types; anything else is rejected (returns None)."""
    allowed = {"action", "amount_usd", "to", "asset", "evidence_hash"}
    if not isinstance(obj, dict) or set(obj) - allowed or "action" not in obj: return None
    try:
        return Intent(action=str(obj["action"]), amount_usd=float(obj.get("amount_usd", 0.0)), to=str(obj.get("to", "")),
                      asset=str(obj.get("asset", "ETH")), evidence_hash=str(obj.get("evidence_hash", "")), origin=origin)
    except (TypeError, ValueError): return None
