"""Ethereum JSON-RPC client (urllib only) and the two on-chain actions: T1 attestation and T2 vault transfer.
The signer lives here, in its own module: the chat / agent layers never see the private key, they only hand over a validated Intent.
dry_run=True builds and signs the transaction and prints its hash but does not broadcast (works offline)."""
from __future__ import annotations
import json, os, urllib.request, binascii
from . import ethtx
from .keccak import keccak256

SEPOLIA = 11155111
BASE = 8453
L2_CHAINS = {8453, 10, 42161}          # rollups add an L1 data fee on top of gas*price, so we reserve a buffer
L1_BUFFER_WEI = 5 * 10**13              # 0.00005 ETH per transaction (generous)
EXPLORER = {11155111: 'https://sepolia.etherscan.io/tx/', 8453: 'https://basescan.org/tx/', 10: 'https://optimistic.etherscan.io/tx/', 42161: 'https://arbiscan.io/tx/', 1: 'https://etherscan.io/tx/'}


class Rpc:
    """Minimal JSON-RPC client. `url` may be ONE url or several separated by commas: the next one is tried when a provider
    refuses (HTTP 403/429/5xx or a network error). A browser-like User-Agent is sent because some public RPC providers block
    Python's default one with HTTP 403."""
    UA = "Mozilla/5.0 (compatible; NullWallet/1.0)"
    def __init__(self, url):
        self.urls = [u.strip() for u in str(url).split(",") if u.strip()]; self.url = self.urls[0] if self.urls else ""; self.n = 0
    def call(self, method, params):
        import urllib.error
        self.n += 1; body = json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}).encode(); errs = []
        for u in [self.url] + [x for x in self.urls if x != self.url]:
            req = urllib.request.Request(u, body, {"Content-Type": "application/json", "User-Agent": self.UA, "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r: out = json.loads(r.read())
            except (urllib.error.URLError, OSError, ValueError) as e:
                errs.append(f"{u}: {e}"); continue
            if "error" in out: raise RuntimeError(out["error"])
            self.url = u; return out["result"]
        raise RuntimeError("no RPC endpoint answered: " + " | ".join(errs))


    def chain_id(self): return int(self.call("eth_chainId", []), 16)
    def balance(self, addr): return int(self.call("eth_getBalance", [addr, "latest"]), 16)
    def gas_price(self): return int(self.call("eth_gasPrice", []), 16)


def preflight(rpc, signer, chain_id, n_tx, data_len=37, max_fee_wei=5 * 10**14):
    """Safety checks BEFORE anything is broadcast: the RPC must really be the chain we think it is, the wallet must be able to pay,
    and the worst-case total fee must stay under a hard cap (default 0.0005 ETH). Raises RuntimeError on any failure."""
    got = rpc.chain_id()
    if got != chain_id: raise RuntimeError(f"RPC is chain {got}, expected {chain_id}: refusing to send")
    gas = 21000 + 40 * data_len + 2000; price = int(rpc.gas_price() * 1.2); worst = (gas * price + (L1_BUFFER_WEI if chain_id in L2_CHAINS else 0)) * n_tx; bal = rpc.balance(signer.address)
    if worst > max_fee_wei: raise RuntimeError(f"worst-case fee {worst/1e18:.6f} ETH exceeds the cap {max_fee_wei/1e18:.6f} ETH: refusing to send")
    if bal < 2 * worst: raise RuntimeError(f"balance {bal/1e18:.6f} ETH is below twice the worst-case fee {worst/1e18:.6f} ETH: fund the wallet a little more")
    return {"chain_id": got, "balance_eth": bal / 1e18, "worst_case_total_fee_eth": worst / 1e18, "gas_price_gwei": price / 1e9}


def wait_receipt(rpc, tx_hash, timeout=180):
    import time
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = rpc.call("eth_getTransactionReceipt", [tx_hash])
        if r: return {"status": int(r["status"], 16), "block": int(r["blockNumber"], 16), "gas_used": int(r["gasUsed"], 16)}
        time.sleep(3)
    return {"status": None, "note": "no receipt yet; check the explorer"}


class Signer:
    """Holds the key. The key is read from an environment variable only; __repr__ never shows it."""
    def __init__(self, env="NULLWALLET_KEY"):
        k = os.environ.get(env, ""); self._k = int(k, 16) if k else None
        self.address = ethtx.address_of(self._k) if self._k else None
    def __repr__(self): return f"Signer(address={self.address})"
    def sign(self, **kw): return ethtx.sign_legacy(self._k, **kw)


def _send(rpc, signer, to, value_wei, data, chain_id, dry_run, nonce=None, gas_price=None):
    if dry_run: nonce = 0 if nonce is None else nonce; gas_price = 10**9 if gas_price is None else gas_price
    else: nonce = int(rpc.call("eth_getTransactionCount", [signer.address, "pending"]), 16); gas_price = int(int(rpc.call("eth_gasPrice", []), 16) * 1.2)
    gas = 21000 + 40 * len(data) + 2000
    raw = signer.sign(nonce=nonce, gas_price=gas_price, gas_limit=gas, to=to, value=value_wei, data=data, chain_id=chain_id)
    h = ethtx.tx_hash(raw)
    if not dry_run: assert rpc.call("eth_sendRawTransaction", ["0x" + raw.hex()]) == h
    return {"tx_hash": h, "raw": "0x" + raw.hex(), "to": to, "value_wei": value_wei, "data": "0x" + data.hex(), "broadcast": not dry_run, "chain_id": chain_id}


def attest(rpc, signer, receipt_hash_hex, chain_id=SEPOLIA, dry_run=True, **kw):
    """T1: zero-value self-transaction with calldata 'NULL1' + 32-byte receipt hash. Anyone can read it on a block explorer."""
    data = b"NULL1" + bytes.fromhex(receipt_hash_hex); return _send(rpc, signer, signer.address, 0, data, chain_id, dry_run, **kw)


def transfer(rpc, signer, to, value_wei, chain_id=SEPOLIA, dry_run=True, **kw):
    """T2: plain ETH transfer. Must only be called with an approved Intent from the policy engine."""
    return _send(rpc, signer, to, value_wei, b"", chain_id, dry_run, **kw)
