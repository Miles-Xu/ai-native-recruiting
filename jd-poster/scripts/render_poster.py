# 按指定宽度输出 3x PNG，并打印换行诊断。输入可为本地 HTML 或 HTTP(S) URL。
# 仓库入口：./run poster jd-poster/jd_poster.html 440 jd-poster/_tmp/海报.png

import argparse
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description="Render a local HTML file or HTTP(S) URL as a poster.")
parser.add_argument("html", help="HTML file path or HTTP(S) URL")
parser.add_argument("width", type=int, help="Poster width in CSS pixels")
parser.add_argument("output", type=Path, help="Output PNG path")
args = parser.parse_args()
if args.width <= 0:
    parser.error("width must be greater than zero")

if urlsplit(args.html).scheme.lower() in ("http", "https"):
    url = args.html
else:
    source = Path(args.html).expanduser().resolve()
    if not source.is_file():
        parser.error(f"HTML file not found: {source}")
    url = source.as_uri()

WIDTH = args.width
OUT = args.output.expanduser()
OUT.parent.mkdir(parents=True, exist_ok=True)

MEASURE = r"""
() => {
  const out = [];
  const nodes = document.querySelectorAll('ul li, .lane p, h1');
  nodes.forEach((el, i) => {
    const box = el.getBoundingClientRect();
    const range = document.createRange();
    // h1 只量主标题文本节点，与 sweep_width.py 口径一致
    // （模板的 h1 里含 .sub 副标题 span，整体量会恒为 2 行，让"标题 1 行"自检永远误报）
    if (el.tagName === 'H1' && el.firstChild) range.selectNodeContents(el.firstChild);
    else range.selectNodeContents(el);
    const rects = [...range.getClientRects()].filter(r => r.width > 1 && r.height > 1);
    if (!rects.length) return;
    // 按 top 聚成行
    const lines = [];
    rects.forEach(r => {
      const hit = lines.find(l => Math.abs(l.top - r.top) < 4);
      if (hit) { hit.left = Math.min(hit.left, r.left); hit.right = Math.max(hit.right, r.right); }
      else lines.push({top: r.top, left: r.left, right: r.right});
    });
    lines.sort((a,b) => a.top - b.top);
    const avail = box.right - lines[0].left;
    const last = lines[lines.length - 1];
    out.push({
      i, tag: el.tagName, lines: lines.length,
      lastFill: +(((last.right - last.left) / avail) * 100).toFixed(1),
      text: el.textContent.trim().slice(0, 22)
    });
  });
  return out;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={'width': WIDTH, 'height': 400}, device_scale_factor=3)
    page = context.new_page()
    page.goto(url)
    page.add_style_tag(content=f'body{{width:{WIDTH}px !important}}')
    page.wait_for_load_state('networkidle')
    page.evaluate('() => document.fonts.ready')
    height = page.evaluate('() => document.body.scrollHeight')
    page.set_viewport_size({'width': WIDTH, 'height': height})
    stats = page.evaluate(MEASURE)
    scroll_w = page.evaluate('() => document.documentElement.scrollWidth')
    page.screenshot(full_page=False, path=OUT, type='png')
    context.close()
    browser.close()

print(f'{WIDTH}x{height} scrollW={scroll_w} -> {OUT}')
for s in stats:
    flag = '  <-- 短尾' if s['lines'] > 1 and s['lastFill'] < 30 else ''
    print(f"  [{s['tag']}] {s['lines']}行 末行{s['lastFill']}%  {s['text']}{flag}")
