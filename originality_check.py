"""Originality check (not a substitute for Turnitin): shingle overlap of (a) our texts against the official rules text and (b) our code against locally installed Python packages."""
import re, os, sys, glob, json, tokenize, io, site
def shingles(tokens, k): return {tuple(tokens[i:i + k]) for i in range(len(tokens) - k + 1)}
def words(t): return re.findall(r"[a-z0-9']+", t.lower())
res = {}
# (a) text vs rules
rules = words(open("rules.txt").read()) if os.path.exists("rules.txt") else []
texts = {}
for f in glob.glob("docs/*.md") + ["README.md"]: texts[f] = open(f).read()
import json as J
nb = J.load(open("docs/NullWallet_Technical_Documentation.ipynb")); texts["technical notebook (markdown)"] = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
R8 = shingles(rules, 8); txt = {}
for n, t in texts.items():
    w = words(t); sh = shingles(w, 8); hit = sh & R8; txt[n] = {"words": len(w), "8gram_overlap_with_rules": len(hit), "share_%": round(100 * len(hit) / max(len(sh), 1), 2), "examples": [" ".join(h) for h in list(hit)[:2]]}
res["text_vs_rules"] = txt
# (b) code vs installed packages
def code_tokens(path):
    try:
        toks = [t.string for t in tokenize.generate_tokens(io.StringIO(open(path, errors="ignore").read()).readline) if t.type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER)]
        return toks
    except Exception: return []
ours = {f: code_tokens(f) for f in glob.glob("nullwallet/*.py") + glob.glob("*.py") if "originality" not in f}
K = 25; our_sh = {f: shingles(t, K) for f, t in ours.items() if len(t) > K}
allour = {}
for f, s in our_sh.items():
    for x in s: allour.setdefault(x, set()).add(f)
sp = [p for p in site.getsitepackages()]; hits = {f: 0 for f in our_sh}; scanned = 0; where = {}
for root in sp:
    for pkg in ("statsmodels", "scipy", "sklearn", "numpy", "pandas", "Crypto", "Cryptodome", "ecdsa", "eth_hash", "eth_keys", "eth_account", "pysha3", "sympy", "arch", "rlp", "coincurve", "cryptography"):
        for path in glob.glob(os.path.join(root, pkg, "**", "*.py"), recursive=True):
            t = code_tokens(path); scanned += 1
            if len(t) < K: continue
            for i in range(len(t) - K + 1):
                key = tuple(t[i:i + K])
                if key in allour:
                    for f in allour[key]: hits[f] += 1; where.setdefault(f, set()).add(os.path.relpath(path, root))
res["code_vs_packages"] = {"files_scanned": scanned, "shingle_size_tokens": K, "overlaps": {f: {"matching_25token_windows": n, "in": sorted(where.get(f, []))[:3]} for f, n in hits.items() if n}, "total_our_files": len(our_sh)}
json.dump(res, open("results/originality_report.json", "w"), indent=1); print(json.dumps(res, indent=1)[:3000])
