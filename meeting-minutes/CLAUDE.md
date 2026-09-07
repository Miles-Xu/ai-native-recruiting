# 纪要整理

将面试或会议转写整理成可回查的纪要。默认生成 HTML，并保存结构化数据和原文；用户指定纯文本或其他交付方式时按其要求处理。

处理前读取 [meeting-minutes/SKILL.md](meeting-minutes/SKILL.md)。字段提取、来源核对和交付检查统一在那里维护。

## 本仓库的路径

- 临时 JSON 和转写：`_tmp/<记录名>.json`、`_tmp/<记录名>.txt`
- 默认归档：`纪要档案/<YYYY-MM-DD>_<候选人或会议主题>/`
- 以上目录均已被 Git 忽略。

从仓库根目录使用统一入口，默认归档路径不受当前工作目录影响：

```bash
./run minutes --structured "meeting-minutes/_tmp/记录.json" --transcript "meeting-minutes/_tmp/记录.txt"
```

需要其他归档位置时，显式传入 `--out-dir`：

```bash
./run minutes --structured "meeting-minutes/_tmp/记录.json" --transcript "meeting-minutes/_tmp/记录.txt" --out-dir "meeting-minutes/_tmp/试跑归档"
```

Windows 将 `./run` 换成 `.\run.cmd`。运行环境见根目录 `README.md`，纪要处理不需要 OCR 或本地 HTTP 服务。
