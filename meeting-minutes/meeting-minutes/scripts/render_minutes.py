# 将结构化纪要 JSON 渲染成 HTML 并保存；提供转写时一并归档原文。
# 仓库入口: ./run minutes --structured x.json [--transcript y.txt] [--out-dir 纪要档案] [--date YYYY-MM-DD]

import argparse
import datetime
import html
import json
import os
import re
import sys

# 语义色 → 商务报告风 CSS 色值
TONE = {
    "green":  "#2e7d32",
    "orange": "#b26a00",
    "red":    "#c62828",
    "blue":   "#1565c0",
    "purple": "#6a1b9a",
    "indigo": "#283593",
    "grey":   "#6b7280",
}
PRIMARY = TONE["indigo"]

CSS = """
* { box-sizing: border-box; }
body {
  margin: 0; padding: 32px 16px;
  background: #f3f4f6;
  font-family: -apple-system, "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
  color: #1f2328; line-height: 1.65;
}
.report {
  max-width: 860px; margin: 0 auto; background: #fff;
  border: 1px solid #e3e6ea; border-radius: 4px;
  padding: 36px 44px 28px; box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.r-head { border-top: 3px solid %PRIMARY%; border-bottom: 3px double %PRIMARY%; padding: 14px 0 12px; }
.r-head h1 { margin: 0; font-size: 22px; font-weight: 700; letter-spacing: .5px; color: #111; }
.r-head .sub { margin-top: 4px; font-size: 13px; color: #6b7280; }
.kpi { display: flex; flex-wrap: wrap; align-items: stretch; margin: 18px 0 6px; }
.kpi .tag { align-self: center; font-size: 12px; font-weight: 700; color: #9ca3af;
  letter-spacing: 2px; padding-right: 14px; }
.kpi .cell { flex: 1 1 0; min-width: 110px; padding: 4px 14px; border-left: 1px solid #e3e6ea; }
.kpi .k-label { font-size: 11px; color: #9ca3af; }
.kpi .k-value { font-size: 15px; font-weight: 700; margin-top: 2px; }
section.block { margin-top: 22px; }
section.block h2 { font-size: 16px; margin: 0 0 8px; color: #111;
  border-bottom: 1px solid #eceef0; padding-bottom: 6px; }
section.block h2 .num { color: %PRIMARY%; font-weight: 700; margin-right: 8px; }
section.block ul { margin: 0; padding-left: 20px; }
section.block li { margin: 4px 0; }
.reco { margin-top: 24px; border: 1px solid #e3e6ea; border-radius: 4px; overflow: hidden; }
.reco .reco-h { background: %PRIMARY%; color: #fff; font-weight: 700; font-size: 14px;
  padding: 8px 16px; }
.reco table { width: 100%; border-collapse: collapse; }
.reco td { padding: 8px 16px; border-top: 1px solid #eceef0; font-size: 14px; vertical-align: top; }
.reco td.f-label { width: 130px; color: #6b7280; font-weight: 600; white-space: nowrap; }
.reco tr.warn td { background: #fff7ed; }
.reco tr.warn td.f-value { color: #b26a00; font-weight: 600; }
.r-foot { margin-top: 26px; padding-top: 12px; border-top: 1px solid #eceef0;
  font-size: 12px; color: #9ca3af; }
details.src { margin-top: 16px; }
details.src summary { cursor: pointer; font-size: 13px; color: #6b7280; user-select: none; }
details.src pre { margin-top: 10px; padding: 14px; background: #f8f9fa; border: 1px solid #eceef0;
  border-radius: 4px; white-space: pre-wrap; word-break: break-word; font-size: 12.5px;
  line-height: 1.6; color: #374151; max-height: 460px; overflow: auto; }
""".replace("%PRIMARY%", PRIMARY)


def md_bold(text):
    # 先转义 HTML,再把 **加粗** 还原成 <strong>
    esc = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)


def render_kpi(kpi):
    if not kpi:
        return ""
    cells = []
    for item in kpi:
        color = TONE.get(item.get("tone", "indigo"), PRIMARY)
        label = html.escape(str(item.get("label", "")))
        value = md_bold(str(item.get("value", "")))
        cells.append(
            f'<div class="cell"><div class="k-label">{label}</div>'
            f'<div class="k-value" style="color:{color}">{value}</div></div>'
        )
    return '<div class="kpi"><div class="tag">KPI</div>' + "".join(cells) + "</div>"


def render_sections(sections):
    out = []
    for i, sec in enumerate(sections or [], 1):
        title = html.escape(str(sec.get("title", "")))
        bullets = "".join(f"<li>{md_bold(str(b))}</li>" for b in sec.get("bullets", []))
        out.append(
            f'<section class="block"><h2><span class="num">{i}.</span>{title}</h2>'
            f"<ul>{bullets}</ul></section>"
        )
    return "".join(out)


def render_reco(reco):
    if not reco:
        return ""
    rows = []
    for f in reco:
        label = html.escape(str(f.get("label", "")))
        raw = str(f.get("value", ""))
        value = md_bold(raw)
        warn = " class=\"warn\"" if "⚠" in raw else ""
        rows.append(
            f"<tr{warn}><td class=\"f-label\">{label}</td>"
            f"<td class=\"f-value\">{value}</td></tr>"
        )
    return (
        '<div class="reco"><div class="reco-h">📋 沟通摘要</div>'
        "<table>" + "".join(rows) + "</table></div>"
    )


def render_html(data, transcript_text):
    title = html.escape(str(data.get("title", "会议纪要")))
    subtitle = html.escape(str(data.get("subtitle", "")))
    gen_at = data.get("generated_at", "")
    src = data.get("source", {}) or {}
    src_desc = "本地会议转写" if src.get("kind") == "transcript" else html.escape(str(src.get("kind", "本地转写")))

    src_block = ""
    if transcript_text:
        src_block = (
            '<details class="src"><summary>展开原始转写</summary>'
            f"<pre>{html.escape(transcript_text)}</pre></details>"
        )

    foot = f"生成时间：{html.escape(str(gen_at))} ｜ 来源：{src_desc}"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="report">
  <div class="r-head">
    <h1>{title}</h1>
    {f'<div class="sub">{subtitle}</div>' if subtitle else ''}
  </div>
  {render_kpi(data.get("kpi"))}
  {render_sections(data.get("sections"))}
  {render_reco(data.get("recommendation"))}
  <div class="r-foot">{foot}</div>
  {src_block}
</div>
</body>
</html>
"""


def safe_name(name):
    return re.sub(r'[\\/:*?"<>|]', "_", str(name)).strip() or "未命名"


def unique_dir(base):
    if not os.path.exists(base):
        return base
    i = 2
    while os.path.exists(f"{base}-{i}"):
        i += 1
    return f"{base}-{i}"


def write_utf8(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def validate_date(value, source):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError(f"{source} 必须是有效的 YYYY-MM-DD 日期")
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{source} 必须是有效的 YYYY-MM-DD 日期") from None
    return value


def main():
    ap = argparse.ArgumentParser(description="结构化纪要 JSON → 商务报告风 HTML + 落盘三件套")
    ap.add_argument("--structured", required=True, help="结构化纪要 JSON 文件路径")
    ap.add_argument("--transcript", help="原始转写文本文件路径(可选,会落盘并内嵌折叠区)")
    ap.add_argument("--out-dir", default="纪要档案", help="落盘根目录(默认 纪要档案)")
    ap.add_argument("--date", help="归档日期 YYYY-MM-DD(默认今天)")
    args = ap.parse_args()

    with open(args.structured, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        cli_date = validate_date(args.date, "--date") if args.date is not None else None
        json_date = validate_date(data["date"], "JSON date") if "date" in data else None
    except ValueError as exc:
        ap.error(str(exc))
    date = cli_date or json_date or datetime.date.today().isoformat()
    data["date"] = date

    transcript_text = ""
    if args.transcript:
        with open(args.transcript, "r", encoding="utf-8") as f:
            transcript_text = f.read()

    candidate = data.get("candidate_name") or data.get("title") or "纪要"
    if not data.get("generated_at"):
        data["generated_at"] = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")

    folder = unique_dir(os.path.join(args.out_dir, f"{date}_{safe_name(candidate)}"))
    os.makedirs(folder, exist_ok=True)

    html_doc = render_html(data, transcript_text)
    write_utf8(os.path.join(folder, "纪要.html"), html_doc)
    write_utf8(os.path.join(folder, "structured.json"),
               json.dumps(data, ensure_ascii=False, indent=2))
    if transcript_text:
        write_utf8(os.path.join(folder, "transcript.txt"), transcript_text)

    print(f"已落盘: {folder}")
    for fn in ("纪要.html", "structured.json", "transcript.txt"):
        p = os.path.join(folder, fn)
        if os.path.exists(p):
            print(f"  - {fn}")


if __name__ == "__main__":
    main()
