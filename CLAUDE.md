# AI Native 招聘工作流 — 根目录

本仓库有三条独立工作流，各自的 SOP 在子目录的 `CLAUDE.md` 里：

- **简历筛选** → `cd resume-screening` 后再工作
- **纪要整理** → `cd meeting-minutes` 后再工作
- **JD 海报** → `cd jd-poster` 后再工作

## 如果用户在根目录直接发起任务

- 甩简历 PDF 路径 / 说要筛简历 → 提示用户进入 `resume-screening/` 目录操作（那里的 CLAUDE.md 才有完整 SOP 和岗位库）；如果用户坚持在根目录做，读取 `resume-screening/CLAUDE.md` 后按其规范执行
- 粘贴会议/面试转写 → 同理，指向 `meeting-minutes/`
- 说要做 JD 海报 / 招聘海报 → 指向 `jd-poster/`（那里有模板和出图脚本，且需要先起本地 http 服务）
- 问这个仓库是什么 → 读 `README.md` 回答

## 通用约定

- 所有候选人数据、临时文件放各子目录的 `_tmp/`，永不提交 git
