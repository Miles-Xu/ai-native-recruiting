# Meeting Minutes Skill(本地 HTML 版)

> **路径:** `meeting-minutes/`
> **版本:** 2.0 (2026-06-30)
> **类型:** 会议/面试转写 → 结构化纪要 → 商务报告风 HTML + 本地归档落盘

把粘贴进来的会议/面试转写文本,自动转换为结构化纪要,产出**商务报告风 HTML**,并落盘归档(原文 + HTML + structured.json 三件套)。适用于面试纪要、技术讨论、产品讨论和通用会议总结。

> 完整规范见 `SKILL.md`;本 README 只是速览。

---

## 核心原则

- **只写转写明确出现的信息**——人名、公司、数字、流程、时间点必须有原文支撑
- **禁止脑补**——面试官名字、对标公司、候选人意图排序、未陈述的结论
- **文档隔离**——每份转写独立处理,不跨文档 carry over
- **信息不足时宁缺毋滥**——缺字段写"未明确提及",不补完句子
- **产物是 HTML**——经 `render_minutes.py` 渲染落盘,不只回一段纯文本
- **发现虚构信息→立即重渲修正版**

---

## 工作流

```
粘贴会议/面试转写文本
    ↓
文档健康检查(是否适合出纪要)
    ↓
分类:interview / technical / product / general
    ↓
字段提取(只从当前转写)
    ↓
组装 structured JSON
    ↓
render_minutes.py → 商务报告风 HTML + 落盘三件套
```

输出分档:
- **A. 完整纪要**——信息充分,KPI + 背景 + 当前进程 + 备注 + 推荐评语
- **B. 简版纪要**——字段不全但核心事实可提炼
- **C. 信息不足**——只写哪些信息不足、为什么不能安全生成、建议补什么

---

## 目录结构

```
meeting-minutes/
├── SKILL.md                    # 主流程、触发条件、分流与验收(完整规范)
├── references/
│   ├── html-quality.md         # 商务报告风 HTML 排版规范(语义色、布局、验收)
│   ├── field-extraction.md     # 字段抽取与降级规则
│   └── artifact-schema.md      # structured JSON 落盘规范
├── examples/
│   ├── interview-minutes.html  # 面试纪要 HTML 示例(脚本真实渲染产物)
│   └── info-insufficient.html  # 信息不足降级示例
└── scripts/
    └── render_minutes.py       # structured JSON → HTML + 原子落盘三件套
```

---

## 快速使用

```bash
py -3.12 meeting-minutes/scripts/render_minutes.py \
  --structured _tmp/候选人.json \
  --transcript _tmp/候选人.txt
```

落盘到 `纪要档案/<YYYY-MM-DD>_<候选人>/`:
- `纪要.html` — 商务报告风成品(自包含,可双击打开)
- `structured.json` — 结构化数据(脚本补齐 date / generated_at)
- `transcript.txt` — 原始转写

可选参数:`--out-dir`(默认 `纪要档案`)、`--date`(默认今天)。脚本自带防覆盖(同名目录追加 `-2`/`-3`),写文件强制 UTF-8 无 BOM。

---

## structured JSON 形状

```json
{
  "type": "interview",
  "candidate_name": "张三",
  "title": "面试纪要 · 张三",
  "subtitle": "算法工程岗 | A司X团队",
  "kpi": [
    {"label": "总包", "value": "60W", "tone": "green"},
    {"label": "当前", "value": "A司 14级", "tone": "blue"},
    {"label": "进度", "value": "⚠️ B司终面等结果", "tone": "orange"},
    {"label": "可约", "value": "下周晚上", "tone": "purple"}
  ],
  "sections": [
    {"title": "个人背景", "bullets": ["AI 数据工程 / 数据管理", "当前在 A司X团队，14级"]},
    {"title": "当前进程", "bullets": ["**B司终面**等结果"]}
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

字段细则见 `references/artifact-schema.md`,语义色见 `references/html-quality.md`。

---

## 语义色

| tone | 含义 |
|--------|------|
| `green`  | 成功 / 强正面 / 高质量 |
| `orange` | 待办 / 进行中 / ⚠️ 需关注 |
| `red`    | 警告 / 风险 / 紧急 |
| `blue`   | 高价值信息 / 关键状态 |
| `purple` | 次要强调(可约时间 / 轮次) |
| `indigo` | 主色(header / 编号 / 推荐评语条),默认 |
| `grey`   | 注脚 / 低优先级 |

---

## 相关文件

- 完整规范:`SKILL.md`
- HTML 质量规范:`references/html-quality.md`
- 字段抽取规则:`references/field-extraction.md`
- structured JSON 规范:`references/artifact-schema.md`
