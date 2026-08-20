# extract_resume.py —— 把简历 PDF 抽成纯文本，供后续分析读取
#
# 为什么需要这个：Claude Code 的 Read 工具在部分环境下依赖外部工具渲染 PDF，
# 缺依赖时会直接失败。简历筛选的入口就是读 PDF，所以用 pymupdf 兜底抽文本。
#
# 依赖：py -3.12 -m pip install pymupdf
# 用法：py -3.12 scripts/extract_resume.py 候选人简历.pdf [输出.txt]
#      不给输出路径时直接打印到 stdout

import pathlib
import sys

import fitz

SRC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None

doc = fitz.open(SRC)
pages = [page.get_text() for page in doc]
doc.close()

text = f"# {SRC.stem}\n\n" + "\n\n----- 分页 -----\n\n".join(pages)

if OUT:
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"{SRC.name}: {len(pages)} 页, {len(text)} 字符 -> {OUT}")
else:
    print(text)
