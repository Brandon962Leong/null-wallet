# What to submit (from the official rules) and where each item is

| Required | File / action | Status |
|---|---|---|
| Registration of the team (2-5 overseas full-time students, >=60% non-Chinese, English) | Website registration button | YOU |
| 1. Technical documentation (architecture, core algorithm, security design) | `docs/Technical_Documentation.pdf` | built |
| 2. Presentation deck (<=10 min) | `deliverables/NullWallet_Deck.pptx` | built |
| 3. Demo video (optional, <=5 min) | `deliverables/demo.mp4` | built, you may re-record |
| 4. Source code: README, GitHub link, deployment instructions, test cases | repo + `README.md` + `tests/` | built; GitHub push = YOU |
| 5. Security self-assessment (permission tiers + known-risk list) | `docs/Security_Self_Assessment.pdf` | built |
| 6. Execution evidence (real on-chain tx hashes) | `evidence/onchain_evidence.json` | DONE: 6 transactions on Base mainnet, status 1; `python verify_onchain.py` checks them |
| Bonus 0-5: on-chain exploration (Topic F) | T1 attestations (and a T2 transfer if a GO exists) on Base mainnet | after step 6 |

## Deadline
20 Oct 2026 23:59 Beijing = **17:59 Stockholm**. The latest submission before this counts. Aim to submit by Sunday 18 Oct.

## Before you click submit
- [ ] Every team member's nationality and student status confirmed
- [ ] Base wallet funded with about 0.002 ETH (throwaway wallet, nothing else in it); balance visible on basescan.org
- [ ] Tx hashes pasted; each opens on basescan.org and shows `NULL1...` input data
- [ ] No keys, no `.env`, no course CSV in the repo
- [ ] Course data licence OK (we do not redistribute it)
- [ ] Names, team name and contact in all documents
- [ ] Deck rehearsed under 10 minutes
