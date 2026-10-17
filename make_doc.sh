#!/bin/bash
# builds docs/NullWallet_Technical_Documentation.{ipynb,html,pdf}
set -e
python3 build_notebook.py
cd docs; rm -rf figs; cp -r ../figs figs
pandoc NullWallet_Technical_Documentation.ipynb -f ipynb -t html5 -s --mathml --toc --toc-depth=2 -c doc.css --embed-resources --metadata title="NULL Wallet Technical Documentation" -o /tmp/doc_raw.html
python3 - <<'P'
import re
h = open("/tmp/doc_raw.html").read()
h = re.sub(r'<div class="sourceCode"[^>]*>(?:(?!</div>).)*?display\(Image.*?</div>', '', h, flags=re.S)
open("NullWallet_Technical_Documentation.html", "w").write(h)
P
python3 ../render_pdf.py $(pwd)/NullWallet_Technical_Documentation.html $(pwd)/NullWallet_Technical_Documentation.pdf
pdfinfo NullWallet_Technical_Documentation.pdf | grep Pages
