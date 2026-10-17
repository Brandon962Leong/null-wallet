# Rules compliance matrix

Source: the official International Track rules (Topic F, Agent Wallet). Status is "Met" only when a file in the repository shows it.

| Rule or requirement | Status | Evidence in the repository |
|---|---|---|
| Topic F: AI wallet agent doing on-chain operations (asset management, execution, risk control) | Met | `nullwallet/policy.py`, `agent.py`, `onchain.py`; tiers T0 to T3 |
| Deliverable 1: technical documentation (architecture, core algorithm, security design) | Met | `docs/NullWallet_Technical_Documentation.{ipynb,html,pdf}`, Sections 3 to 6 |
| Deliverable 2: deck of at most 10 minutes | Met | `NullWallet_Deck.pptx`, 15 main slides with timed speaker notes, appendix not presented; slides notebook for Canva |
| Deliverable 3: demo video of at most 5 minutes (optional) | Met | `NullWallet_Demo.mp4` |
| Deliverable 4: source code with README, GitHub link, deployment instructions, test cases | Met once the GitHub link is added | `README.md`, `docs/GITHUB_SETUP.md`, `tests/` (51 tests) |
| Deliverable 5: security self-assessment (permission tiers and known-risk list) | Met | `docs/Security_Self_Assessment.pdf` |
| Deliverable 6: real on-chain transaction hashes (on-chain topic) | Met | `evidence/onchain_evidence.json`: 6 transactions on Base mainnet (chain id 8453), status 1; `python verify_onchain.py` |
| Scoring: task completion 40% | Addressed | Working pipeline, replay, 1,000-market Monte Carlo, independent rerun, out-of-course test |
| Scoring: security and compliance 30% | Addressed | Policy caps, allowlist, kill-switch, key isolation, injection tests, preflight, two live bugs found, fixed and logged |
| Scoring: innovation and interaction 30% | Addressed | `docs/INNOVATION.md`; chat and web demo |
| Bonus 0 to 5: on-chain exploration | Addressed | T1 attestations of the ledger head and five refusals on mainnet |
| Entries completed independently, free of plagiarism | Addressed, team to confirm | `results/originality_report.json`, `results/originality_vs_hwa.json`; AI assistance disclosed in the email and in the documentation |
| Third-party data, code and open-source components properly licensed | Addressed, team to confirm | `LICENSE` (MIT), `THIRD_PARTY.md`; the course data are not redistributed; Binance public market data used for the out-of-course test |
| At least 60% of the team non-Chinese nationals | Team to confirm | Registration form |
| Latest submission prevails; no changes after the deadline (20 Oct 2026 23:59 Beijing, 17:59 Stockholm) | Process | Send the single email before the deadline |
| Contact: info@ican-x.com | Process | Put in copy of the email |

## Items only the team can confirm

1. All team members agree on the origin and reuse of the work.
2. The course data licence permits using the data for this entry (they are not redistributed here).
3. The use of an AI assistant (Claude) for drafting and coding is permitted under "completed independently" and is disclosed in the email.
4. The Binance public data terms allow this use.
