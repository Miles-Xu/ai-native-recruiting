# AI Native 招聘工作流 — 根目录

本仓库有两条独立工作流,各自的 SOP 在子目录的 `CLAUDE.md` 里:

- **简历筛选** → `cd resume-screening` 后再开 Claude Code
- **纪要整理** → `cd meeting-minutes` 后再开 Claude Code

## 如果用户在根目录直接发起任务

- 甩简历 PDF 路径 / 说要筛简历 → 提示用户进入 `resume-screening/` 目录操作(那里的 CLAUDE.md 才有完整 SOP 和岗位库);如果用户坚持在根目录做,读取 `resume-screening/CLAUDE.md` 后按其规范执行
- 粘贴会议/面试转写 → 同理,指向 `meeting-minutes/`
- 问这个仓库是什么 → 读 `README.md` 回答

## 通用约定

- 所有候选人数据、临时文件放各子目录的 `_tmp/`,永不提交 git
- 本仓库的示例岗位、人名、公司均为虚构(见 README 虚构声明)
