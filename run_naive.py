import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nullwallet import montecarlo as m
if __name__ == "__main__":
    out = []
    for b in (0.0, 0.05, 0.1, 0.2):
        t = time.time(); r = m.run(b, 300, workers=2); r["sec"] = round(time.time() - t); print(r, flush=True); out.append(r); json.dump(out, open("evidence/mc_naive.json", "w"), indent=1)
