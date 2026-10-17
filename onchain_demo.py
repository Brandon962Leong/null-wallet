"""Produce REAL on-chain evidence (run this yourself; it needs a small amount of funded ETH on the chosen network).

Default network: BASE mainnet (chain 8453): a real, value-bearing blockchain; about 0.002 ETH is plenty; hashes verifiable on basescan.org.
  export NULLWALLET_RPC=https://mainnet.base.org      # public RPC (or a free Base URL from Alchemy / Infura / QuickNode)
  export NULLWALLET_KEY=<64 hex chars of a BRAND-NEW throwaway wallet that holds only a few USD of ETH on Base>
  python onchain_demo.py results/ledger_1h.jsonl            # dry run: signs offline, prints hashes, sends nothing
  python onchain_demo.py results/ledger_1h.jsonl --send     # really broadcasts

Other networks: NULLWALLET_CHAIN_ID=11155111 (Sepolia testnet, free test ETH)  |  42161 (Arbitrum One)  |  10 (Optimism)

What it does (only tier-1 actions unless you explicitly allow more):
  1) attests the ledger head, 2) attests the last 5 refusals (T1: zero-value self-transactions, calldata = 'NULL1' + hash).
  3) a value transfer (T2) happens ONLY if the ledger contains a GO receipt AND NULLWALLET_VAULT is set AND, on a real network, NULLWALLET_ALLOW_TRANSFER=1.
Safety: before sending it checks that the RPC really is the expected chain, that the wallet can pay, and that the worst-case total fee is under 0.0005 ETH.
Results are written to evidence/onchain_evidence.json - paste the explorer links into the submission."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nullwallet import onchain, policy
from nullwallet.ledger import Ledger

CHAIN = int(os.environ.get("NULLWALLET_CHAIN_ID", onchain.BASE)); EXPL = onchain.EXPLORER.get(CHAIN, ""); REAL_NET = CHAIN != onchain.SEPOLIA
path = sys.argv[1]; send = "--send" in sys.argv; L = Ledger(path); assert L.verify()[0], "ledger chain is broken"
rpc = onchain.Rpc(os.environ.get("NULLWALLET_RPC", "")) if send else None; signer = onchain.Signer()
assert signer.address, "set NULLWALLET_KEY (a brand-new throwaway key)"
if not send: print("NOTE: dry-run hashes use placeholder nonce 0 and gas price 1 gwei; real hashes (printed with --send) will differ. Do not submit dry-run hashes.")
print(f"wallet {signer.address} | chain {CHAIN} ({'REAL NETWORK' if REAL_NET else 'testnet'}) | {'SEND' if send else 'DRY RUN'}")
refusals = L.find("refusal")[-5:]; n_tx = 1 + len(refusals)
if send:
    info = onchain.preflight(rpc, signer, CHAIN, n_tx + 1); print("preflight ok:", info)
evid = []
def rec(label, r):
    r["label"] = label
    if r["broadcast"]: r.update({"receipt": onchain.wait_receipt(rpc, r["tx_hash"]), "explorer": EXPL + r["tx_hash"]})
    evid.append(r); print(label, r["tx_hash"], r.get("explorer", "(not broadcast)"), r.get("receipt", ""))
rec("attest ledger head", onchain.attest(rpc, signer, L.entries[-1]["hash"], chain_id=CHAIN, dry_run=not send))
for e in refusals: rec(f"attested refusal seq={e['seq']}", onchain.attest(rpc, signer, e["payload"]["receipt"], chain_id=CHAIN, dry_run=not send))
dest = os.environ.get("NULLWALLET_VAULT", ""); goes = [e for e in L.find("verdict") if e["payload"]["decision"]["verdict"] == "GO"]
if dest and goes:
    lim = policy.Limits(allowlist=(dest.lower(),)); st = policy.State(clock=goes[-1]["clock"] + 1); it = policy.Intent("move", 10.0, dest, evidence_hash=goes[-1]["hash"])
    d = policy.evaluate(it, lim, st, {"hash": goes[-1]["hash"], "clock": goes[-1]["clock"]}); print("policy:", dict(d))
    if d.ok and (not REAL_NET or os.environ.get("NULLWALLET_ALLOW_TRANSFER") == "1"): rec("T2 vault transfer", onchain.transfer(rpc, signer, dest, int(0.0002e18), chain_id=CHAIN, dry_run=not send))
    elif d.ok: print("T2 transfer approved by policy but NOT sent: set NULLWALLET_ALLOW_TRANSFER=1 to allow a value transfer on a real network")
else: print("No GO receipt (or NULLWALLET_VAULT unset): no value is moved. This is the wallet working as designed.")
os.makedirs("evidence", exist_ok=True); json.dump(evid, open("evidence/onchain_evidence.json", "w"), indent=1); print("written evidence/onchain_evidence.json")
