# AI Native 招聘工作流

用本地文件保存岗位要求、筛选结论和沟通记录，通过 AI 助手完成简历筛选、纪要整理和招聘海报制作。仓库包含工作说明、示例和 Python 脚本，没有独立的应用界面。

## 三个工作流

| 工作流 | 输入 | 默认产物 | 说明 |
|--------|------|----------|------|
| 简历筛选 | 简历 PDF、岗位 JD、已确认的筛选要求 | Markdown 结论和待确认问题 | [简历筛选](resume-screening/CLAUDE.md) |
| 纪要整理 | 面试或会议转写 | HTML 纪要、结构化 JSON、转写原文 | [纪要整理](meeting-minutes/CLAUDE.md) |
| JD 海报 | JD、品牌素材、投递方式 | PNG 海报 | [JD 海报](jd-poster/CLAUDE.md) |

可以在仓库根目录发起任务，指定文件路径和希望得到的结果。例如：

```text
按 resume-screening/jobs/ 里的示例岗位，试筛 resume-screening/examples/resume_王五.pdf。
把 meeting-minutes/_tmp/沟通记录.txt 整理成面试纪要。
用 jd-poster/_tmp/JD.txt 做招聘海报，品牌素材也在这个目录。
```

`AGENTS.md` 和 `CLAUDE.md` 都指向同一套流程。首次使用的 AI 助手先读根目录入口，再读对应工作流；PDF 另有专门的[读取规范](docs/pdf-reading.md)。

## 环境准备

先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。仓库入口自动选择 Python 3.12，在本地 `.venv/` 中同步 `uv.lock` 锁定的依赖；不需要激活虚拟环境或单独安装 Python 包。

macOS / Linux 在根目录执行：

```bash
./run doctor
./run setup-ocr
./run setup-browser
./run doctor --browser
```

Windows 使用同样的参数，将 `./run` 换成 `.\run.cmd`。入口同时设置 UTF-8 编码，避免系统区域设置影响中文输出。第一次同步环境及下载 OCR 语言包、浏览器需要联网；文件处理在本机进行。只整理纪要时，执行 `doctor` 即可。

`doctor` 显示实际 Python 路径、包版本和浏览器安装状态；`doctor --browser` 还会真正启动 Chromium，区分“已安装”和“能运行”。如果报 sandbox、Permission denied 或 MachPort 错误，应处理执行权限，不能靠重装 Python 解决。

## 运行命令

以下命令从仓库根目录执行，输入路径可以是绝对路径；相对路径以当前执行目录为基准。输出位置以参数或对应工作流约定为准。

```bash
./run pdf "resume-screening/examples/resume_王五.pdf"
./run minutes --structured "meeting-minutes/_tmp/记录.json" --transcript "meeting-minutes/_tmp/记录.txt"
./run widths "jd-poster/_tmp/岗位.html" 400,440,480
./run poster "jd-poster/_tmp/岗位.html" 440 "jd-poster/_tmp/岗位.png"
./run test -v
```

PDF 命令输出逐页 PNG、文本和提取报告，普通 PDF 与扫描页的处理详见[PDF 读取路径](docs/pdf-reading.md)。纪要默认归档到仓库的 `meeting-minutes/纪要档案/`。海报可读取本地 HTML 或 HTTP(S) URL；自包含模板不需要先启动服务。

`./run test -v` 运行 PDF 和纪要等回归测试。未安装 OCR 语言包时，真实 OCR 测试会显示跳过；完整验证前先执行 `setup-ocr`。浏览器运行能力由 `doctor --browser` 单独检查。

`doctor --browser` 成功后，设置 `RECRUITING_BROWSER_TESTS=1` 再运行测试，可验证真实 PNG 导出及图像尺寸、非空像素。仓库的 GitHub Actions 配置在 Linux、macOS 和 Windows 上执行这组完整检查；本地修改提交并推送后才会触发。

每个平台还会导出公共海报模板，并在该次 Actions 运行的 Artifacts 中保留 PNG 14 天，便于检查字体和排版差异。

## 示例与真实资料

`resume-screening/jobs/` 中带 `example: true` 的岗位，以及 `resume-screening/examples/` 中的候选人、公司、学校和筛选结论，都是虚构演示数据。示例里的评分和用人偏好不代表通用招聘标准，正式使用时按自己的岗位要求配置。

海报目录保留了现有品牌模板和范本，用于展示排版。制作正式海报前，替换或确认品牌、JD、工作地点和投递方式；范本不代表当前仍在招聘。

候选人原始资料和临时产物放各流程的 `_tmp/`，归档路径见对应说明。`.gitignore` 已忽略这些默认路径；使用其他保存位置时需另行检查是否会被 Git 跟踪。
