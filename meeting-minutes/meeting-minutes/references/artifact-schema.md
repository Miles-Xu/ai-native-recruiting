# Structured JSON 落盘规范(本地版)

`render_minutes.py` 的输入。一份纪要对应一个 structured JSON,渲染后随 HTML、原文一起落盘到 `纪要档案/<日期>_<候选人>/structured.json`,供后续看板/程序读取,无需解析 HTML。

## 落盘目录

```
纪要档案/
└── <YYYY-MM-DD>_<候选人或会议主题>/
    ├── transcript.txt     # 原始转写
    ├── 纪要.html          # 商务报告风成品
    └── structured.json    # 本结构化数据(脚本会补齐 date / generated_at)
```

- 日期默认当天(可用 `--date` 覆盖,或写在 JSON 的 `date` 字段)
- 候选人名取 `candidate_name`;不明确时回退到 `title`
- 同名目录已存在 → 脚本自动追加 `-2`/`-3`,不覆盖

## JSON 形状

```json
{
  "type": "interview",
  "candidate_name": "张三",
  "title": "面试纪要 · 张三",
  "subtitle": "大模型评测岗 | 模型评测 / 平台开发",
  "date": "2026-01-15",
  "kpi": [
    {"label": "总包", "value": "60W", "tone": "green"},
    {"label": "当前", "value": "A司 14级", "tone": "blue"},
    {"label": "进度", "value": "⚠️ B司终面等结果", "tone": "orange"},
    {"label": "可约", "value": "下周晚上", "tone": "purple"}
  ],
  "sections": [
    {
      "title": "个人背景",
      "bullets": [
        "AI 数据工程 / 数据管理",
        "当前在 A司X团队，14级"
      ]
    },
    {
      "title": "当前进程",
      "bullets": ["**B司终面**等结果", "面试安排可继续推进"]
    }
  ],
  "recommendation": [
    {"label": "目前状态", "value": "在职"},
    {"label": "目前&期望地点", "value": "西安 → 上海"},
    {"label": "基本情况", "value": "AI 数据工程 / 数据管理，当前在 A司X团队，14级"},
    {"label": "当前流程", "value": "⚠️ B司终面等结果"},
    {"label": "看机会原因", "value": "期望更大平台发展"}
  ],
  "source": {"kind": "transcript", "file": "transcript.txt"}
}
```

## 字段说明

- `type`:`interview` / `technical` / `product` / `general`
- `candidate_name`:候选人名;不明确时用占位(如「候选人（姓名未明确）」),脚本会回退到 title 命名目录
- `title` / `subtitle`:header 两行
- `kpi[]`:4 项以内,每项 `{label, value, tone}`;`tone` 见 `html-quality.md` 语义色表,缺省 indigo
- `sections[]`:每个 `{title, bullets[]}`;bullet 支持 `**加粗**`(渲染成 `<strong>`)
- `recommendation[]`:推荐评语 5 字段,`{label, value}`;`value` 含 `⚠` 的行自动高亮
- `source`:`{"kind": "transcript", "file": "transcript.txt"}`(本地转写,无外部平台 token/url)
- `date` / `generated_at`:可不填,脚本自动补(日期默认今天,生成时间为本机当前时刻)

## Hard Rules

- structured JSON 必须反映**最终 HTML 内容**,不藏更大草稿
- 措辞与 HR 实际看到的一致
- 不加原文不支持的隐藏字段
- 模糊事实保留原粒度
- `kpi` 与 `sections[].bullets` 用数组,方便看板灵活渲染
