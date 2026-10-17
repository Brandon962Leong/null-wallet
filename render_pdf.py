import sys, asyncio
from playwright.sync_api import sync_playwright
src, out = sys.argv[1:3]
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.goto("file://" + src); pg.wait_for_timeout(1500)
    pg.pdf(path=out, format="A4", print_background=True, margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"}, display_header_footer=True,
           header_template="<div></div>", footer_template='<div style="font-size:8px;color:#6B7785;width:100%;text-align:center;">NULL Wallet - technical documentation - page <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
    b.close()
