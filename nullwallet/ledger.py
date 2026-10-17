"""Append-only, hash-chained ledger (the audit trail of every commitment, verdict, order, refusal and attestation)."""
from __future__ import annotations
import hashlib, json, os, time


def canon(obj) -> bytes:
    """Canonical JSON: sorted keys, no spaces, floats rounded to 10 significant digits so that the hash is reproducible."""
    def fix(o):
        if isinstance(o, float): return float(f"{o:.10g}")
        if isinstance(o, dict): return {str(k): fix(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [fix(v) for v in o]
        if hasattr(o, "item"): return fix(o.item())
        return o
    return json.dumps(fix(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256_hex(obj) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


class Ledger:
    GENESIS = "0" * 64

    def __init__(self, path: str | None = None):
        self.path = path; self.entries: list[dict] = []
        if path and os.path.exists(path):
            with open(path) as f: self.entries = [json.loads(l) for l in f if l.strip()]

    def append(self, kind: str, payload: dict, clock=None) -> dict:
        prev = self.entries[-1]["hash"] if self.entries else self.GENESIS
        body = {"seq": len(self.entries), "kind": kind, "clock": clock if clock is not None else len(self.entries), "prev": prev, "payload": payload}
        body["hash"] = sha256_hex(body)
        self.entries.append(body)
        if self.path:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "a") as f: f.write(json.dumps(body, sort_keys=True) + "\n")
        return body

    def verify(self) -> tuple[bool, int | None]:
        prev = self.GENESIS
        for i, e in enumerate(self.entries):
            body = {k: e[k] for k in ("seq", "kind", "clock", "prev", "payload")}
            if e["prev"] != prev or e["seq"] != i or sha256_hex(body) != e["hash"]: return False, i
            prev = e["hash"]
        return True, None

    def find(self, kind: str):
        return [e for e in self.entries if e["kind"] == kind]
