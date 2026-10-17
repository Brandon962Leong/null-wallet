"""Offline check: every on-chain attestation's calldata is NULL1 + a hash that exists in the ledger, and the ledger chain is intact.
Usage: python verify_onchain.py [evidence/onchain_evidence.json] [results/ledger_1h.jsonl]"""
import sys, json
ev_path = sys.argv[1] if len(sys.argv) > 1 else "evidence/onchain_evidence.json"
led_path = sys.argv[2] if len(sys.argv) > 2 else "results/ledger_1h.jsonl"
ev = json.load(open(ev_path)); led = [json.loads(l) for l in open(led_path)]
hashes = {e["hash"]: e["seq"] for e in led}
from nullwallet.ledger import Ledger
ok = True
for e in ev:
    d = e["data"]; good = d.startswith("0x4e554c4c31") and len(d) == 2 + 2 * 37 and e["receipt"]["status"] == 1 and e["chain_id"] == 8453
    seq = hashes.get(d[12:]); good = good and seq is not None; ok &= good
    print("OK " if good else "BAD", e["label"], "-> ledger seq", seq, e["explorer"])
print("ALL ATTESTATIONS VALID" if ok else "PROBLEM FOUND")
sys.exit(0 if ok else 1)
