# Third-party components

| Component | Use | Licence |
|---|---|---|
| NumPy | arrays and linear algebra | BSD-3-Clause |
| SciPy | distribution functions (p-values) | BSD-3-Clause |
| pandas | bars and time series | BSD-3-Clause |
| scikit-learn | logistic regression and gradient boosting candidates | BSD-3-Clause |
| Matplotlib | figures | Matplotlib licence (BSD-compatible) |
| python-pptx, Playwright, Pillow, imageio-ffmpeg | building the deck, the video and the PDFs (not needed to run the wallet) | MIT, Apache-2.0, HPND, BSD-2-Clause |
| Pandoc | converting notebooks to HTML | GPL-2.0-or-later, used as an external tool only |

Cryptography (Keccak-256, secp256k1, RLP, EIP-155 signing) is written in this repository and checked against the official EIP-155 test vector. Public market data (Binance BTCUSDT klines) are downloaded by `fetch_data.py` and not redistributed. The statistical methods (Newey-West, Diebold-Mariano, Holm, block bootstrap, ADF, KPSS, Breusch-Pagan, Jarque-Bera, Ljung-Box) are standard published methods, cited in the technical documentation.
