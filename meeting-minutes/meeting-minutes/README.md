# 纪要整理

把面试或会议转写整理成 HTML 纪要，并保存结构化 JSON 和原文。页面自包含，可直接在浏览器打开。

完整流程见 [SKILL.md](SKILL.md)。本仓库的输入和归档路径见 [上级目录说明](../CLAUDE.md)。

## 脚本用法

在仓库根目录执行，替换为实际输入路径：

```bash
./run minutes --structured "meeting-minutes/_tmp/记录.json" --transcript "meeting-minutes/_tmp/记录.txt"
```

Windows 使用 `.\run.cmd`。统一入口默认归档到仓库的 `meeting-minutes/纪要档案/`，可用 `--out-dir` 更改位置；`--date` 可指定归档日期。同名目录会追加 `-2`、`-3`，已有记录不会被覆盖。单独调用底层脚本时，其默认输出目录相对于执行位置。

传入非空转写时，归档中包含 `纪要.html`、`structured.json` 和 `transcript.txt`；未提供转写时只生成前两项。

## 参考

- [字段提取](references/field-extraction.md)：不同会议的内容和来源核对
- [JSON 格式](references/artifact-schema.md)：脚本输入字段
- [HTML 质量](references/html-quality.md)：页面结构和检查要点
- [面试示例](examples/interview-minutes.html)与[信息不足示例](examples/info-insufficient.html)：现有页面范本
