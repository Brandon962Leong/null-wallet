---
title: "NULL Wallet: concept one-pager"
---

**Challenge.** 2026 Shenzhen International FinTech Competition, International Track, Topic F (Agent Wallet). Theme: *AI as a Financial Participant*.

## The idea in one sentence
A wallet for AI agents that **must statistically reject "I have no net edge" before it is allowed to move money**, that commits its tests **before** seeing the data, and that **publishes every refusal** as a tamper-evident, on-chain-anchored receipt.

## Why it matters
AI agents are getting wallets. Today's protections (spend limits, allowlists, risk gates) answer *"is this transaction permitted?"*. They cannot answer *"is the reason real?"*. An agent can stay inside every limit and still lose money on a pattern that is noise, and nobody can see why it acted or declined.

## How it works
1. **Pre-register**: candidates, thresholds and costs are hashed into a ledger before the evidence is examined.
2. **Evidence Court** (six gates from our coursework): no look-ahead; assumption tests; skill against a naive forecast (Diebold-Mariano, Holm over all candidates); survives without shock bars; net edge after costs (HAC t, bootstrap); break-even cost at least twice the modelled cost. Verdict **GO / WATCH / HOLD**.
3. **Policy engine**: tiers T0 observe, T1 attest on-chain, T2 move value (fresh GO receipt, allowlist, caps, cooldown, kill-switch), T3 refuse. No language model between a request and the key.
4. **Ledger and chain**: hash-chained receipts; head and refusals anchored by zero-value transactions with calldata `NULL1`+hash.

## What is fresh
Evidence before permission; data-snooping control inside an agent wallet; pre-registration (commit before reveal); refusals as first-class, attested records; a deterministic gate between language and signer. (We did not find the same combination in public descriptions; we cannot prove none exists.)

## Proof
- **No-edge world**: @@H0@@ false GO in 1,000 simulated markets (also with zero costs).
- **Real edge world**: GO rises with edge strength (@@P05@@ weak, @@P20@@ moderate, 100 % strong).
- **Real BTC data**: 36 of 36 monthly decisions were WATCH or HOLD; the same models without the court lost about 20 % of the wallet to costs.
- **Security**: 51 automated tests including prompt injection, address poisoning, replay, runaway loops, ledger tampering and key leakage.
- **Honest limit**: a GO is evidence about the past. We found a failure in stress testing (March 2020), added a regime guard, and disclose that the fix is post hoc.

## Unique to our work
Every gate is a standard method (assumption tests, Monte Carlo, pseudo-out-of-sample evaluation, Diebold-Mariano, net-of-cost edge, break-even cost, data-snooping control), applied to BTC data we cleaned ourselves.
