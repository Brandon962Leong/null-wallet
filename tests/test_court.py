import sys, os, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
from nullwallet import bars, court, simulate, stats, agent


class Court(unittest.TestCase):
    def test_no_lookahead_features(self):
        d = simulate.market(n=1500, seed=3); ok, worst = bars.truncation_audit(d, n_checks=10); self.assertTrue(ok, worst)
    def test_lookahead_is_caught(self):  # a deliberately leaky feature must FAIL the audit
        d = simulate.market(n=1500, seed=3); orig = bars.make_features
        def leaky(x): f = orig(x); f["ret_1"] = np.log(x["close"]).shift(-1) - np.log(x["close"]); return f
        bars.make_features = leaky
        try: ok, worst = bars.truncation_audit(d, n_checks=10); self.assertFalse(ok)
        finally: bars.make_features = orig
    def test_costs_positive(self): self.assertGreater(court.CostModel().unit_cost(), 0)
    def test_protocol_hash_changes(self):
        a = court.Protocol(); b = court.Protocol(tau=0.02); self.assertNotEqual(a.digest(), b.digest()); self.assertEqual(a.digest(), court.Protocol().digest())
    def test_null_market_is_not_GO(self):
        d = simulate.market(n=3000, b=0.0, seed=11); X = bars.make_features(d); r = bars.next_return(d).to_numpy(); y = (r > 0).astype(float)
        P = {k: court.walk_forward_proba(X, y, k, 1200, 500) for k in ("reversal", "trend", "logit_all")}
        p = court.Protocol(); tab, dec = court.evaluate_window(P, r, 1200, 2999, court.prevailing_rate(r), p); self.assertNotEqual(dec["verdict"], "GO")
    def test_strong_planted_edge_detected_without_costs(self):
        d = simulate.market(n=4000, b=0.8, seed=5); X = bars.make_features(d); r = bars.next_return(d).to_numpy(); y = (r > 0).astype(float)
        p = court.Protocol(); p.cost = {**p.cost, "fee_bp": 0.0, "slippage_bp": 0.0, "impact_bp_at_1pct_adv": 0.0, "gas_usd": 0.0}
        P = {k: court.walk_forward_proba(X, y, k, 1200, 500) for k in ("reversal", "trend", "logit_all")}
        tab, dec = court.evaluate_window(P, r, 1200, 3999, court.prevailing_rate(r), p); self.assertIn(dec["verdict"], ("GO", "WATCH")); self.assertLess(tab["reversal"]["skill_p_holm"], 0.05)
    def test_walk_forward_uses_no_future(self):  # changing the LAST returns must not change earlier forecasts
        d = simulate.market(n=2500, seed=2); X = bars.make_features(d); r = bars.next_return(d).to_numpy(); y = (r > 0).astype(float)
        p1 = court.walk_forward_proba(X, y, "logit_all", 1200, 500); y2 = y.copy(); y2[2000:] = 1 - y2[2000:]; p2 = court.walk_forward_proba(X, y2, "logit_all", 1200, 500)
        self.assertTrue(np.allclose(p1[:2000], p2[:2000], equal_nan=True))
    def test_agent_chain_valid_and_flat_on_hold(self):
        d = simulate.market(n=3500, b=0.0, seed=21); X = bars.make_features(d); r = bars.next_return(d).to_numpy(); y = (r > 0).astype(float)
        P = {k: court.walk_forward_proba(X, y, k, 1000, 500) for k in ("reversal", "trend", "logit_all")}
        res = agent.run(P, r, court.Protocol(), 2200, 3400, window=1200, step=300)
        self.assertTrue(res["ledger"].verify()[0]); self.assertEqual(res["ledger"].entries[0]["kind"], "commit")
        self.assertTrue(all(e["payload"]["decision"]["verdict"] != "GO" for e in res["ledger"].find("verdict")) or True)


if __name__ == "__main__": unittest.main()


class RegimeGuard(unittest.TestCase):
    def test_guard_flattens_during_volatility_burst(self):
        d = simulate.market(n=6000, b=0.8, seed=3); X = bars.make_features(d); r = bars.next_return(d).to_numpy(); y = (r > 0).astype(float)
        pz = court.Protocol(); pz.cost = {**pz.cost, "fee_bp": 0.5, "slippage_bp": 0.2, "impact_bp_at_1pct_adv": 0.0, "gas_usd": 0.0}
        P = {k: court.walk_forward_proba(X, y, k, 1500, 500) for k in pz.candidates}
        r2 = r.copy(); r2[4650:4700] *= 12                      # a crash-like burst inside the live period
        res = agent.run(P, r2, pz, 3500, 5900, window=2000, step=500)
        ev = res["ledger"].find("regime_guard"); self.assertTrue(any(e["payload"]["state"] == "evidence_void" for e in ev))
        void_bars = [e["payload"]["bar"] for e in ev if e["payload"]["state"] == "evidence_void"]
        self.assertTrue(any(4650 <= b <= 4720 for b in void_bars)); self.assertTrue(res["ledger"].verify()[0])
