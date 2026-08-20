# sweep_width.py —— 扫描多个海报宽度，按「短尾数量」挑最优宽度（只测量，不截图）
#
# 依赖：本地 http 服务已启动（py -3.12 -m http.server 8877 --directory .）
# 用法：py -3.12 scripts/sweep_width.py jd_poster.html 380,400,420,440,460
#
# 输出每个宽度的：整页高度 / 标题行数 / 短尾条数 / 次短条数 / 末行填充均值
# 挑宽度的判据：标题必须 1 行；短尾=0 优先；再看末行填充均值大的

import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8877"

HTML = sys.argv[1]
WIDTHS = [int(w) for w in sys.argv[2].split(",")]

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
        page.goto(f'{BASE_URL}/{HTML}')
        page.add_style_tag(content=f'body{{width:{w}px !important}}')
        page.wait_for_load_state('networkidle')
        d = page.evaluate(MEASURE)
        items = d['items']
        bad = [i for i in items if i['lines'] > 1 and i['fill'] < 30]
        mid = [i for i in items if i['lines'] > 1 and 30 <= i['fill'] < 45]
        avg = sum(i['fill'] for i in items if i['lines'] > 1) / max(1, len([i for i in items if i['lines'] > 1]))
        print(f"w={w:4d} h={d['height']:5d} h1行={d['h1lines']} 短尾={len(bad)} 次短={len(mid)} 末行均值={avg:.1f}%")
        ctx.close()
    browser.close()
