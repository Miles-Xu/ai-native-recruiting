# render_poster.py —— 按指定宽度截 3x 高清整页海报，同时输出每条 bullet 的行数与末行填充率（自动标短尾）
#
# 依赖：本地 http 服务已启动（py -3.12 -m http.server 8877 --directory .）
# 用法：py -3.12 scripts/render_poster.py jd_poster.html 440 输出海报.png
#
# 脚本会注入 body{width:Npx !important}，所以不改 HTML 也能按任意宽度出图；
# scrollW 应等于宽度，不等说明有内容溢出（右侧白条的成因）

import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8877"

HTML = sys.argv[1]
WIDTH = int(sys.argv[2])
OUT = sys.argv[3]

MEASURE = r"""
() => {
  const out = [];
  const nodes = document.querySelectorAll('ul li, .lane p, h1');
  nodes.forEach((el, i) => {
    const box = el.getBoundingClientRect();
    const range = document.createRange();
    range.selectNodeContents(el);
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
    page.goto(f'{BASE_URL}/{HTML}')
    page.add_style_tag(content=f'body{{width:{WIDTH}px !important}}')
    page.wait_for_load_state('networkidle')
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
