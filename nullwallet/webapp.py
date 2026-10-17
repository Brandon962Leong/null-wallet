"""Demo web UI (standard library only): ledger viewer + chat box wired to the real parser and policy engine.
Run:  python -m nullwallet.webapp evidence/ledger.jsonl   then open http://localhost:8000"""
from __future__ import annotations
import json, sys, html
from http.server import BaseHTTPRequestHandler, HTTPServer
from . import chat, policy
from .ledger import Ledger

LEDGER = None; LIM = policy.Limits(allowlist=("0x" + "11" * 20,)); ST = policy.State(clock=10**6)

PAGE = """<!doctype html><meta charset=utf-8><title>NULL Wallet</title><style>
body{font:15px system-ui;margin:0;background:#0f1419;color:#e6e6e6}header{padding:14px 24px;background:#161c24;border-bottom:1px solid #2a3340}
h1{margin:0;font-size:20px}main{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:16px 24px}@media(max-width:800px){main{grid-template-columns:1fr}}
.card{background:#161c24;border:1px solid #2a3340;border-radius:8px;padding:12px;max-height:75vh;overflow:auto}
.v{padding:2px 8px;border-radius:10px;font-weight:600}.GO{background:#1e7a3c}.WATCH{background:#9a7b12}.HOLD{background:#7a2a2a}
input{width:75%;padding:8px;background:#0f1419;color:#e6e6e6;border:1px solid #2a3340;border-radius:6px}button{padding:8px 14px}
.m{margin:8px 0;padding:8px;border-radius:6px;background:#0f1419}.ok{border-left:4px solid #1e7a3c}.no{border-left:4px solid #b03a3a}code{font-size:12px;color:#8fb}</style>
<header><h1>NULL Wallet <small>- the wallet that must reject "no edge" before it moves money</small></h1></header>
<main><section class=card><h3>Evidence ledger <span id=chain></span></h3><div id=led></div></section>
<section class=card><h3>Ask the wallet</h3><div id=log></div><p><input id=q placeholder="why are you on hold? / send 100 usd to 0x... / ignore previous instructions"><button onclick=ask()>Send</button></p></section></main>
<script>
async function led(){let r=await (await fetch('/api/ledger')).json();document.getElementById('chain').innerHTML=r.valid?'<span class="v GO">chain valid</span>':'<span class="v HOLD">TAMPERED at '+r.bad+'</span>';
document.getElementById('led').innerHTML=r.entries.slice(-40).reverse().map(e=>{let p=e.payload,t='';if(e.kind=='verdict')t='<span class="v '+p.decision.verdict+'">'+p.decision.verdict+'</span> '+p.why;else if(e.kind=='refusal')t='attested refusal <code>'+p.attest.slice(0,24)+'..</code>';else if(e.kind=='intent')t=p.decision.code+' - '+p.decision.why;else if(e.kind=='regime_guard')t='regime guard: '+p.state;else if(e.kind=='commit')t='protocol hash <code>'+p.protocol_hash.slice(0,16)+'..</code>';else t=e.kind;
return '<div class=m><b>#'+e.seq+' '+e.kind+'</b> <code>'+e.hash.slice(0,12)+'</code><br>'+t+'</div>'}).join('')}
async function ask(){let q=document.getElementById('q').value;let r=await (await fetch('/api/chat',{method:'POST',body:JSON.stringify({text:q})})).json();
document.getElementById('log').innerHTML='<div class="m '+(r.ok?'ok':'no')+'"><b>'+q.replace(/</g,'&lt;')+'</b><br>'+r.reply.replace(/</g,'&lt;')+'<br><code>'+r.code+'</code></div>'+document.getElementById('log').innerHTML;document.getElementById('q').value=''}
led()</script>"""


def last_verdict():
    v = LEDGER.find("verdict"); return v[-1] if v else None


def answer(text):
    lv = last_verdict(); rec = lv["hash"] if lv else ""
    if lv: ST.clock = lv["clock"] + 1                      # "now" = just after the newest receipt
    it, hint = chat.parse(text, last_receipt=rec)
    if it is None: return {"ok": False, "code": "REFUSED", "reply": hint}
    go = {"hash": rec, "clock": lv["clock"]} if lv and lv["payload"]["decision"]["verdict"] == "GO" else None
    d = policy.evaluate(it, LIM, ST, go)
    if it.action == "observe": return {"ok": True, "code": d["code"], "reply": lv["payload"]["why"] if lv else "No verdict yet."}
    if it.action == "attest": return {"ok": d.ok, "code": d["code"], "reply": "Attestation allowed: would write NULL1+receipt hash on-chain." if d.ok else d["why"]}
    return {"ok": d.ok, "code": d["code"], "reply": ("Approved by policy (simulation)." if d.ok else "Refused: " + d["why"])}


class H(BaseHTTPRequestHandler):
    def _send(self, body, ct="text/html"):
        b = body.encode(); self.send_response(200); self.send_header("Content-Type", ct + "; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/api/ledger":
            ok, bad = LEDGER.verify(); self._send(json.dumps({"valid": ok, "bad": bad, "entries": LEDGER.entries}), "application/json")
        else: self._send(PAGE)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        self._send(json.dumps(answer(str(body.get("text", "")))), "application/json")
    def log_message(self, *a): pass


def main():
    global LEDGER
    LEDGER = Ledger(sys.argv[1] if len(sys.argv) > 1 else "evidence/ledger.jsonl"); port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    print(f"NULL Wallet UI on http://localhost:{port}  ({len(LEDGER.entries)} ledger entries)"); HTTPServer(("0.0.0.0", port), H).serve_forever()


if __name__ == "__main__": main()
