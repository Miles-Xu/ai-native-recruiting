# Field Extraction Reference

## Interview Minutes Fields

- `name`: document title first; otherwise explicit self-introduction in transcript; if absent use `候选人（姓名未明确）`
- `role`: current or recent company + team/role explicitly stated in transcript
- `loc`: current city, expected base, or remote preference explicitly stated
- `bg`: stack / domain / education / years of experience explicitly mentioned
- `expect`: only explicit salary numbers or ranges
- `avail`: explicit interview availability
- `process`: explicit current pipeline status, offer status, or ongoing company process
- `rounds`: explicit completed rounds or planned rounds with evaluation style
- `notes`: explicit risks, conflicts, time pressure, location limits, salary gap, urgency
- `date`: document date if available

## 📋 推荐评语段（HARD — 每次纪要末尾必出）

格式固定，5 字段各自独立不交叉：

- **目前状态**：在职/离职（仅此一处出现，其他字段不重复）
- **目前&期望地点**：城市
- **基本情况**：精简客观事实 + 职级（原文明确的写在里面，其他字段不再提职级）
- **当前流程**：⚠️ 靠后阶段必须标竞争压力/offer情况/deadline
- **看机会原因**：原文明确的动机

**禁止字段间重复**：每个字段写自己那件事，不跨字段复述。如基本情况写了职级，状态/流程/动机不再提职级。
**不做风险判断**：推荐评语是对业务方的客观摘要，只呈现原文关键细节，不加「稳定性差/跳槽频繁/建议观望」这类主观判断。

### 当前流程 写法规则

- 流程靠前（刚投/初面）：简述即可，如「刚启动面试」「流程偏早期」
- 流程靠中（在面多家）：列出已知公司名
- 流程靠后（已有 offer/终面）：**必须加 ⚠️ 前缀**，写明 offer 数量、公司类型、deadline 压力
- 若原文未提及任何流程信息：写「未明确提及」

## Hard Extraction Rules

- Only extract facts from the current document
- Do not carry facts across documents
- Do not infer location from company city
- Do not infer salary from level/title
- Do not convert vague wishes into numbers
- Do not output recommendation/reject/waiting unless the transcript says so
- **Speaker disambiguation (HARD):** HR（访谈方）说的观点/介绍/卖点不得写成候选人认同或期待；HR 抛的信息只能标注为「HR 介绍/同步」，不能用「候选人认可/看好/期待」等措辞

## Missing Fields

Use `未明确提及` when a field is missing.

If more than half of the key interview fields are missing, downgrade output:
- use a brief minutes card
- or use an information-insufficient card

例外：推荐评语的 5 个字段即使部分为「未明确提及」，仍需全部列出，不可因缺失而跳过整个推荐评语段。

## Classification Hints

- `interview`: candidate background, salary, rounds, offer, availability
- `technical`: architecture, design, performance, trade-off, implementation debate
- `product`: PRD, priority, user need, schedule, product decision
- `general`: everything else

Priority order:
1. interview
2. technical
3. product
4. general

## Downgrade Conditions

Use information-insufficient mode when:
- transcript is only title or greeting
- transcript is heavily truncated
- transcript has severe speaker confusion and almost no stable facts
- transcript does not contain enough material for safe summarization
