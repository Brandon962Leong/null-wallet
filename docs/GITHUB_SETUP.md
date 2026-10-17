# GitHub: step by step (about 10 minutes)

1. Create an account at github.com if you do not have one. Create a **new repository** named `null-wallet`, visibility **Public** (judges must open the link; if the rules allow private, add the organisers as collaborators instead), tick "Add a README: No" (we already have one).
2. On your computer, unzip `NullWallet_Submission.zip` and open a terminal in the `null-wallet` folder.
3. Run:
   ```
   git init
   git add .
   git commit -m "NULL Wallet: evidence-gated agent wallet"
   git branch -M main
   git remote add origin https://github.com/<your-username>/null-wallet.git
   git push -u origin main
   ```
   When asked for a password, use a **personal access token** (GitHub > Settings > Developer settings > Tokens), not your password.
4. Open the repo page and check: README renders, `tests/` is there, **no `.env` or key file**, **no course CSV data**.
5. Copy the repo URL into the submission form.
6. After any later change: `git add . && git commit -m "update" && git push`. The **latest submission before the deadline counts**, so re-submit if you change files.

## Run it (what judges will do)
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests          # 41 tests, no network needed
python -m nullwallet.webapp results/ledger_1h.jsonl     # UI on http://localhost:8000
```
## Never commit
Private keys, RPC URLs with API keys, the course CSVs. Keys go only in environment variables.

## Do not commit
`throwaway_wallet.key`, any private key, the course data files, raw Binance downloads. Add them to `.gitignore` before the first commit:

```
throwaway_wallet.key
*.key
data/
*.pkl
```
