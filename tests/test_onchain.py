import sys, os, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from nullwallet import onchain


class FakeRpc:
    def __init__(self, chain=8453, bal=10**16, price=10**7): self.c, self.b, self.p = chain, bal, price
    def chain_id(self): return self.c
    def balance(self, a): return self.b
    def gas_price(self): return self.p


class Sgn: address = "0x" + "11" * 20


class Preflight(unittest.TestCase):
    def test_ok(self): self.assertEqual(onchain.preflight(FakeRpc(), Sgn, 8453, 7)["chain_id"], 8453)
    def test_wrong_chain_refused(self):
        with self.assertRaises(RuntimeError): onchain.preflight(FakeRpc(chain=1), Sgn, 8453, 7)
    def test_poor_wallet_refused(self):
        with self.assertRaises(RuntimeError): onchain.preflight(FakeRpc(bal=10**9), Sgn, 8453, 7)
    def test_fee_cap(self):
        with self.assertRaises(RuntimeError): onchain.preflight(FakeRpc(price=10**13), Sgn, 8453, 7)   # absurd gas price
    def test_l1_buffer_counted_on_rollups(self):
        r = onchain.preflight(FakeRpc(), Sgn, 8453, 7); self.assertGreater(r["worst_case_total_fee_eth"], 7 * 5e-5 * .99)
    def test_explorer_known(self): self.assertIn("basescan", onchain.EXPLORER[8453])


if __name__ == "__main__": unittest.main()


class RpcFallback(unittest.TestCase):
    def test_falls_back_to_next_url_and_sends_user_agent(self):
        import io, json, urllib.error, urllib.request
        from unittest import mock
        seen = []
        def fake(req, timeout=0):
            seen.append((req.full_url, req.get_header("User-agent")))
            if "bad" in req.full_url: raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)
            return io.BytesIO(json.dumps({"jsonrpc": "2.0", "id": 1, "result": "0x2105"}).encode())
        with mock.patch("urllib.request.urlopen", fake):
            r = onchain.Rpc("https://bad.example, https://good.example")
            self.assertEqual(r.chain_id(), 8453)
        self.assertEqual([u for u, _ in seen], ["https://bad.example", "https://good.example"])
        self.assertTrue(all(ua and "Python-urllib" not in ua for _, ua in seen))
    def test_all_fail_gives_clear_error(self):
        import urllib.error
        from unittest import mock
        def fake(req, timeout=0): raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)
        with mock.patch("urllib.request.urlopen", fake):
            with self.assertRaises(RuntimeError) as c: onchain.Rpc("https://a.example,https://b.example").chain_id()
        self.assertIn("no RPC endpoint answered", str(c.exception))


class GasLimit(unittest.TestCase):
    def test_gas_limit_covers_eip7623_calldata_floor(self):
        """Base/Ethereum (Pectra, EIP-7623) reject txs whose gas limit is below 21000 + 10*(zero_bytes + 4*nonzero_bytes)."""
        from unittest import mock
        os.environ["NULLWALLET_KEY"] = "11" * 32; seen = {}
        def fake_sign(self, **kw): seen.update(kw); return b"\x01" * 10
        with mock.patch.object(onchain.Signer, "sign", fake_sign):
            onchain.attest(None, onchain.Signer(), "ff" * 32, chain_id=8453, dry_run=True)
        data = seen["data"]; tokens = sum(1 if b == 0 else 4 for b in data)
        self.assertGreaterEqual(seen["gas_limit"], 21000 + 10 * tokens)
        self.assertGreaterEqual(seen["gas_limit"], 21000 + 16 * len(data))
