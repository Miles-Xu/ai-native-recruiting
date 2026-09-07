# 比较不同宽度下的海报换行。输入可为本地 HTML 或 HTTP(S) URL。
# 仓库入口：./run widths jd-poster/jd_poster.html 380,400,420,440,460

import argparse
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description="Compare poster widths for a local HTML file or HTTP(S) URL.")
parser.add_argument("html", help="HTML file path or HTTP(S) URL")
parser.add_argument("widths", help="Comma-separated widths in CSS pixels")
args = parser.parse_args()
try:
    WIDTHS = [int(width) for width in args.widths.split(",")]
except ValueError:
    parser.error("widths must be comma-separated integers")
if any(width <= 0 for width in WIDTHS):
    parser.error("widths must be greater than zero")

if urlsplit(args.html).scheme.lower() in ("http", "https"):
    url = args.html
else:
    source = Path(args.html).expanduser().resolve()
    if not source.is_file():
        parser.error(f"HTML file not found: {source}")
    url = source.as_uri()

MEASURE = r"""
() => {
  const out = [];
  document.querySelectorAll('ul li, .lane p').forEach(el => {
    const box = el.getBoundingClientRect();
    const range = document.createRange();
    range.selectNodeContents(el);
    const rects = [...range.getClientRects()].filter(r => r.width > 1 && r.height > 1);
    if (!rects.length) return;
    const lines = [];
    rects.forEach(r => {
      const hit = lines.find(l => Math.abs(l.top - r.top) < 4);
      if (hit) { hit.left = Math.min(hit.left, r.left); hit.right = Math.max(hit.right, r.right); }
      else lines.push({top: r.top, left: r.left, right: r.right});
    });
    lines.sort((a,b) => a.top - b.top);
    const avail = box.right - lines[0].left;
    const last = lines[lines.length - 1];
    out.push({lines: lines.length, fill: ((last.right - last.left) / avail) * 100});
  });
  // 标题是否一行
  const h1 = document.querySelector('h1');
  const r = document.createRange();
  const first = h1.firstChild;   // 标题主文本节点
  r.selectNodeContents(first);
  const h1lines = [...r.getClientRects()].filter(x => x.height > 1).length;
  return {items: out, h1lines, height: document.body.scrollHeight,
          scrollW: document.documentElement.scrollWidth};
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    for w in WIDTHS:
        ctx = browser.new_context(viewport={'width': w, 'height': 900})
        page = ctx.new_page()
        page.goto(url)
        page.add_style_tag(content=f'body{{width:{w}px !important}}')
        page.wait_for_load_state('networkidle')
        page.evaluate('() => document.fonts.ready')
        d = page.evaluate(MEASURE)
        items = d['items']
        bad = [i for i in items if i['lines'] > 1 and i['fill'] < 30]
        mid = [i for i in items if i['lines'] > 1 and 30 <= i['fill'] < 45]
        avg = sum(i['fill'] for i in items if i['lines'] > 1) / max(1, len([i for i in items if i['lines'] > 1]))
        print(f"w={w:4d} h={d['height']:5d} scrollW={d['scrollW']} h1行={d['h1lines']} 短尾={len(bad)} 次短={len(mid)} 末行均值={avg:.1f}%")
        ctx.close()
    browser.close()
