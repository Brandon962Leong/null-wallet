"""Monte Carlo stress test.  python run_mc.py [--quick] [outfile]   (1,000 markets under H0, 300 per planted-edge level; --quick = 40 / 20)"""
import sys, json, time, os, multiprocessing as mp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nullwallet import montecarlo as m

if __name__ == "__main__":
    quick = "--quick" in sys.argv; args = [a for a in sys.argv[1:] if not a.startswith("--")]; outf = args[0] if args else "results/montecarlo.json"
    os.makedirs(os.path.dirname(outf) or ".", exist_ok=True); M = 40 if quick else 1000; out = []
    for b, nc in [(0.0, False), (0.0, True)] + [(b, False) for b in (0.05, 0.1, 0.2, 0.4, 0.8)]:
        mm = M if b == 0.0 else max(M * 3 // 10, 20); t = time.time(); r = m.run(b, mm, nocost=nc, workers=os.cpu_count() or 2); r["sec"] = round(time.time() - t); print(r, flush=True); out.append(r)
        json.dump(out, open(outf, "w"), indent=1)
