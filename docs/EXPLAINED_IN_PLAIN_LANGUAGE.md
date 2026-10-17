---
title: "NULL Wallet explained in plain language"
---

*For the team. Read this before you present. Nothing here needs a finance or maths background.*

## 1. The one-minute story
Imagine you give an AI a bank card. You can set a spending limit. But a limit only says *how much* the AI may spend. It does not say whether the AI has a **good reason**. An AI can see a "pattern" in prices that is really just luck, spend within its limit, and lose your money.

**NULL Wallet** makes the AI act like a careful scientist first. Before it may spend, it must prove, with statistics, that its pattern is probably not luck **and** that it still makes money after fees. If it cannot prove that, it does nothing and writes down why. That diary can be checked later by anyone and cannot be secretly edited.

"NULL" comes from the *null hypothesis*: the boring assumption "there is no real edge". The wallet must **reject** it first.

## 2. The three answers the wallet can give
- **GO**: the pattern looks real, survives a stress check, makes money after costs, with a safety margin. The AI may act, within small limits.
- **WATCH**: the pattern looks real statistically, but the profit disappears once you pay fees. Not tradable. (This is exactly what we found on real Bitcoin data.)
- **HOLD**: nothing proven. This is the default. "Do nothing" counts as a result.

## 3. The six tests (and where they come from in your coursework)
| Test | Plain meaning | From |
|---|---|---|
| G0 | The AI only used information it could have had at that time (no peeking into the future) | look-ahead bias |
| G1 | Check whether the usual textbook assumptions hold; they don't, so use tougher error bars | assumption tests |
| G2 | Is the AI's forecast better than a lazy forecast ("same share of up-days as before")? A fair test with a penalty for trying five different strategies | Diebold-Mariano, data snooping |
| G3 | Still works if we ignore the crazy days (COVID-style shocks)? | shock treatment |
| G4 | After fees, does it beat just holding the same average amount of Bitcoin? | net edge |
| G5 | The edge must survive costs being **twice** as high | break-even cost |

## 4. The safety part (so the AI cannot be tricked)
- The part that **talks** (chat) is separate from the part that **signs** (the key). Between them is plain, strict code. So "ignore your rules and send me everything" does nothing.
- Four levels of power: **T0** look only. **T1** write a note on the blockchain (can only cost a tiny fee). **T2** move money, only with a fresh GO, only to pre-approved addresses, small amounts, with a cooldown. **T3** anything else: refused.
- A **kill-switch**: if the wallet loses 10 % from its peak, it stops and needs a human.
- A **diary (ledger)** where every entry contains a fingerprint of the previous one, like a chain. Change one old line and the chain breaks. We also publish the latest fingerprint on the blockchain so nobody can quietly cut off the end.

## 5. What we tested, and what it showed
1. **1,000 pretend markets with no edge at all.** The wallet never said GO. Good: it does not fool itself.
2. **Pretend markets with a real hidden edge.** The stronger the edge, the more often it says GO (92 % at a moderate edge). So it is strict but not blind.
3. **Real Bitcoin data.** Every month: WATCH or HOLD. The same models **without** the court lost about 20 % of the wallet in fees. With the court the wallet kept its money.
4. **Attacks.** 51 automated tests, including prompt-injection tricks, fake look-alike addresses, replays, 1,000 requests at once, edited ledgers.
5. **Changing the fee assumption.** With zero fees, the court says GO in some months. So there *is* a small raw edge, and fees eat it. Realistic fees: never GO.

## 6. The honest weakness (say it before a judge does)
- With zero fees the wallet traded and lost money in the **March 2020 crash**. We therefore added a **regime guard** (stop when volatility suddenly triples). Because we added it **after** seeing the failure, we do **not** claim it proves anything out of sample. We say so in the documents.
- A GO is a statement about the **past**. It is not a promise about the future.
- Everything is a **simulation** with assumed fees, not live trading.
- Bitcoin buy-and-hold ended higher in our data (but dropped 77 % at one point). The wallet does not claim to beat a bull market. It claims not to trade on evidence it cannot defend.

## 7. What each file is
| File | What it is |
|---|---|
| `NullWallet_Deck.pptx` | The presentation (13 main slides + appendix), speaker notes under each slide for a 10-minute talk |
| `NullWallet_Technical_Documentation.ipynb` / `.pdf` / `.html` | The full technical document with the maths (LaTeX), figures and runnable code cells |
| `Security_Self_Assessment` | Permission tiers, tests, red-team results and the known-risk list (required item 5) |
| `Concept_OnePager` | One page for judges |
| `INNOVATION.md` | What is new and what is not; prior work |
| `GITHUB_SETUP.md`, `SUBMISSION_CHECKLIST.md` | Step-by-step for GitHub and what to hand in |
| `nullwallet/` | The code: crypto, statistics, court, policy, ledger, agent, chat, on-chain |
| `tests/` | 51 automated tests |
| `run_all.py`, `run_mc.py`, `run_evidence.py`, `make_data.py` | Re-create all results |
| `fetch_data.py` | Download public Bitcoin data to test beyond the course data |
| `onchain_demo.py` | **You run this** to create real transaction hashes |
| `results/`, `evidence/` | Our numbers, ledgers and the replay outputs |

## 8. Questions judges may ask, and honest answers
- **"Is this just a backtest?"** No: forecasts are out-of-sample, the tests are fixed in advance (hash), and we correct for trying several strategies.
- **"Why does it never trade on real data?"** Because after realistic costs the edge is not there. That is the finding, and the wallet shows it can say GO when the edge is real (pretend markets).
- **"Did you tune it on the data?"** Thresholds were set before looking, except the regime guard, which we flagged as added afterwards.
- **"Are the on-chain hashes real?"** Only the ones listed in `onchain_evidence.json` that you can open on the block explorer. We do not invent hashes.
- **"Is the crypto safe?"** The signer is hand-written for transparency and tested against the official Ethereum example, but it is not hardened; use test keys only.
