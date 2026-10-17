# What is new in NULL Wallet (and what is not)

## One sentence
An agent wallet that is **not allowed to move money until it has statistically rejected "I have no net edge"**, that commits its tests **before** looking at the data, and that **publishes every refusal** as a signed, hash-chained receipt.

## The gap we are filling
Agent wallets today ask "is this transaction *permitted*?" (spend limits, allowlists, risk gates). Nobody on the list below asks "is the *reason* for this transaction *real*?". An agent can stay inside every limit and still lose money on a pattern that is noise. NULL Wallet adds that missing layer: **evidence before permission**.

## Five ideas, each tied to our own coursework
| # | Idea | Where it comes from in our work | Why it is not just "a risk limit" |
|---|---|---|---|
| 1 | **Court gates**: skill (Diebold-Mariano), shock robustness, net edge (HAC t, block bootstrap), cost margin | Diebold-Mariano, pseudo-OOS, shock treatment, net-of-cost edge, break-even cost | Limits cap loss size; the court decides whether to trade at all |
| 2 | **Data-snooping control (Holm over all candidates)** | Multiple-testing literature | An agent that tries 5 strategies and shows the best one is cheating itself; Holm prices that in |
| 3 | **Pre-registration (commit before reveal)**: the protocol (candidates, thresholds, costs) is hashed into the ledger first | Standard discipline: state hypotheses before estimation | Stops the agent (or us) from tuning thresholds after seeing results |
| 4 | **Attested refusals**: every HOLD/WATCH is a receipt, anchored on-chain as `NULL1`+hash | New | "No-trade is a result". Most systems only log what they did, never what they declined and why |
| 5 | **Deterministic gate between language and signer** | Security design | No LLM output reaches the key: chat -> strict intent -> policy -> signer |

## Three-verdict language
GO = skill and net edge and cost margin. WATCH = real forecasting skill but not tradable after costs (our finding on BTC). HOLD = nothing proven.

## Prior work we looked at (and could not find the same combination in)
- AgentTrading-style systems: deterministic risk gates and an HMAC-chained audit log. They gate *risk*, not *statistical evidence*.
- arXiv 2601.04583 (agent-wallet survey): intent schemas and policy records. No significance testing or pre-registration.
- Coinbase agentic wallets: spend limits and guardrails.
We state this carefully: **we did not find** a system combining statistical gating, pre-registration and attested refusals. We cannot prove nobody has one. Cite the sources above in the deck and say "to our knowledge".

## What is NOT new (say so honestly)
Walk-forward testing, Diebold-Mariano, Newey-West, block bootstrap, Holm, allowlists, spend caps, hash chains and EIP-155 signing are all standard. The novelty is the **composition and the placement**: classical econometric tests used as a *permission layer* for an on-chain agent.

## Measurable value (what we show, honestly)
1. **False-GO rate** under H0 over 1,000 simulated markets (target: at or below the nominal level).
2. **Power curve**: how large a planted edge must be before the court says GO.
3. **Real BTC replay** vs no-court agents and buy-and-hold: the court's value is *not paying costs on a non-edge*, not beating a bull market.
4. **Red-team suite**: prompt injection, address poisoning, replay, runaway loop, tampered ledger, key leakage.
