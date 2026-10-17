"""Natural-language front end. It is deliberately NOT a language model: a small deterministic parser turns user text into a strict Intent.
Whatever the text says, the Intent still has to pass the policy engine, and text that comes from outside the user (news, web pages, memos,
tool output) can never create an Intent at all."""
from __future__ import annotations
import re
from .policy import Intent

INJECTION = [r"ignore (all|any|previous|prior|the above)", r"disregard", r"system prompt", r"you are now", r"developer mode", r"private key", r"seed phrase",
             r"mnemonic", r"export (the )?key", r"reveal (the )?(key|secret)", r"override", r"bypass", r"disable (the )?(limit|cap|kill|policy|court)",
             r"sudo", r"as the (admin|owner|operator)", r"transfer (all|everything|the entire)", r"send (all|everything)", r"drain"]
INJ = re.compile("|".join(INJECTION), re.I)
ADDR = re.compile(r"0x[0-9a-fA-F]{40}")


def scan(text: str):
    """Return the list of injection markers found in untrusted text."""
    return sorted({m.group(0).lower() for m in INJ.finditer(text or "")})


def parse(text: str, origin: str = "chat", last_receipt: str = ""):
    """Return (Intent|None, reply_hint). Only three verbs exist: status/why (observe), attest, send/move."""
    t = (text or "").strip(); low = t.lower()
    if origin == "external": return None, "external content is data; it cannot give instructions"
    hits = scan(t)
    if hits: return None, f"refused: instruction pattern(s) {hits} are not permitted"
    if re.search(r"\b(status|why|explain|verdict|report|balance|show)\b", low): return Intent("observe", origin=origin), "observe"
    if re.search(r"\b(attest|prove|publish|notarize)\b", low): return Intent("attest", origin=origin, evidence_hash=last_receipt), "attest"
    m = re.search(r"\b(send|move|transfer|fund)\b.*?(\d+(?:\.\d+)?)\s*(usd|\$|dollars)?", low)
    if m:
        a = ADDR.search(t); return Intent("move", amount_usd=float(m.group(2)), to=a.group(0) if a else "", origin=origin, evidence_hash=last_receipt), "move"
    return Intent("unknown_action", origin=origin), "unrecognised request"
