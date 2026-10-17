"""Download public 5-minute candles from Binance's public data archive (https://data.binance.vision) so the court can be tested on data that is NOT from our course.
  python fetch_data.py BTCUSDT 2023-01 2023-12 data/BTCUSDT_5m.csv        (symbol, first month, last month, output)
Check the archive's terms of use before redistributing; we do NOT commit downloaded data to the repo (data/ is in .gitignore)."""
import sys, io, zipfile, urllib.request, pandas as pd

sym, m0, m1, out = sys.argv[1:5]; rows = []
for p in pd.period_range(m0, m1, freq="M"):
    url = f"https://data.binance.vision/data/spot/monthly/klines/{sym}/5m/{sym}-5m-{p}.zip"
    with urllib.request.urlopen(url, timeout=60) as r: z = zipfile.ZipFile(io.BytesIO(r.read()))
    df = pd.read_csv(z.open(z.namelist()[0]), header=None); rows.append(df); print("ok", p, len(df))
d = pd.concat(rows); d = d.iloc[:, :11]; d.columns = ["t", "open", "high", "low", "close", "base_vol", "ct", "quote_vol", "N", "taker_base", "taker_quote"]
unit = 1e6 if d["t"].iloc[-1] > 1e15 else 1e3            # archives from 2025 use microseconds
res = pd.DataFrame({"date_time": pd.to_datetime(d["t"] * (1 if unit == 1e3 else 1e-3), unit="ms", utc=True), "N": d["N"], "amount": d["quote_vol"],
    "open": d["open"], "high": d["high"], "low": d["low"], "close": d["close"], "V_buy": d["taker_quote"], "V_sell": d["quote_vol"] - d["taker_quote"]})
res.to_csv(out); print("saved", out, len(res))
