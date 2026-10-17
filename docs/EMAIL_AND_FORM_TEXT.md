# Final emails and form text (statements only)

## Form fields
- Team name: AskWallet
- Topic: F
- Provisional entry title: NULL Wallet
- Proposal summary (166 words, within the 100-200 limit):

NULL Wallet is an evidence-gated agent wallet for Topic F. Today an AI agent with a wallet is usually controlled only by spend limits and allowlists, which ask whether a transfer is permitted but not whether the reason for it is real. NULL Wallet adds that missing check. Before any value moves, a statistical Evidence Court built from standard econometric tests must reject the null hypothesis of no net edge after costs. It audits look-ahead bias, regression assumptions, forecast skill against a naive benchmark (Diebold-Mariano with Holm correction), robustness to shocks, net edge after costs and a break-even cost margin. The protocol is hashed before the data is examined, every decision and refusal is written to a hash-chained ledger, and the ledger head is anchored on-chain. A deterministic policy engine with strict intents, allowlists, caps, cooldown and kill-switch means language never reaches the key. In 1,000 simulated no-edge markets it never approved a trade, and on real BTC data it refused every monthly decision.

## Single email (registration + submission). Send to: fintechathon@ican-x.com
Subject: International Track Registration – AskWallet – Brandon Haris Effendi

Dear Organising Committee,

We register for the 2026 Shenzhen International FinTech Competition, International Track (Artificial Intelligence), and submit our entry.

Team name: AskWallet
Topic: F (Agent Wallet)
Entry title: NULL Wallet
Team leader: Brandon Haris Effendi
Team email: br5880ha-s@student.lu.se
Members: 3 (Brandon Haris Effendi, team leader; Maulik Bansal; Desylionie Onggani Winata), all at Lund University, Sweden

Attached: the completed and signed Registration Form, passport photo-page images, and proof of enrollment for all members.

Project summary: NULL Wallet is an evidence-gated agent wallet. It pre-registers its protocol, records every decision in a hash-chained ledger, and requires a statistical evidence check to return GO before a policy engine allows any value transfer. Otherwise it refuses and records the refusal.

Submission contents:
1. Technical documentation (PDF and Jupyter notebook)
2. Presentation deck (PPTX) and the slides notebook (HTML and ipynb)
3. Security self-assessment (PDF)
4. Demo video (about 70 seconds)
5. Source code: https://github.com/Brandon962Leong/null-wallet (README, deployment instructions, 51 automated tests, licence)
6. Execution evidence: real on-chain transactions on Base mainnet, zero value, each with calldata 0x4e554c4c31 ("NULL1") followed by the 32-byte ledger hash:
   - attest ledger head: https://basescan.org/tx/0x32979e5b253e18426f8a15384ced20d46a94b67047a488f1d705beb67352961c
   - attested refusal seq=64: https://basescan.org/tx/0xa13ad8007943961bbbfc303e3494bf2de5c9bf354a15e6badec2d38a12a440ae
   - attested refusal seq=66: https://basescan.org/tx/0xfa87dfe124a1c0b4c00cbe5dabe0f483a2c968c7eda3733f720a7af119f4e058
   - attested refusal seq=68: https://basescan.org/tx/0xdedaebaf061ed6ac16015e498f6e2a53e470d70035193121eed65ea784ad2a45
   - attested refusal seq=70: https://basescan.org/tx/0x7dc685ff946cda0f66a650469e6afd9474ad54ab86533d9cf0ef7c5dc7a7899a
   - attested refusal seq=72: https://basescan.org/tx/0x33f08991f78776b2b72348e879c458a9f3fa81e1fc4a3ecf2959d06279472c68

For transparency:
- AI assistance: we used an AI assistant (Claude, by Anthropic) to help design, code and document the project. The team reviewed the work and can explain every part of it. This is also stated in our documentation.
- Software: Python 3, numpy, scipy, pandas, scikit-learn, matplotlib, python-pptx, Jupyter and pandoc. The Ethereum signing code (Keccak, secp256k1, RLP, EIP-155) is our own pure-Python implementation, verified against the official test vector.
- Data: BTC price data from our course, and public BTC data from the Binance public data archive (data.binance.vision). We do not redistribute any course data. Cost figures are stated assumptions. Results are a sandbox replay and simulation, not live trading.
- Verification: an independent rerun of the whole pipeline on a second machine reproduced every verdict; a statistical self-audit (size and power simulations), an originality report and a rules-compliance matrix are in the repository. Each transaction can be checked with verify_onchain.py.
- Resubmission: we may send a corrected version before the deadline. We understand the latest submission before 20 Oct 23:59 (Beijing time) is the one evaluated.
- Track: all 3 of our 3 members are non-Chinese nationals (Indonesia, India, Indonesia), and all are enrolled at universities outside mainland China, Hong Kong, Macao and Taiwan.

We look forward to your confirmation.

Kind regards,
Brandon Haris Effendi
On behalf of team AskWallet
Lund University, Sweden | +46 768659694
