"""Extract and render every PDF page, reporting incomplete text explicitly."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

try:
    import pymupdf
except ImportError:
    print("PyMuPDF is unavailable in this Python. Use ./run pdf (Windows: run.cmd pdf).", file=sys.stderr)
    raise SystemExit(5)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TESSDATA = ROOT / ".cache/tessdata"


def meaningful_chars(text):
    return sum(char.isalnum() for char in text)


def image_coverage(page):
    area = page.rect.width * page.rect.height
    if not area:
        return 0
    covered = 0
    for info in page.get_image_info():
        rectangle = pymupdf.Rect(info["bbox"]) & page.rect
        covered += max(0, rectangle.width) * max(0, rectangle.height)
    return min(1.0, covered / area)


def extract_page(page, directory, args):
    number = page.number + 1
    result = {"page": number, "status": "needs_review", "method": "text_layer", "warnings": []}
    image = directory / f"page-{number:03d}.png"
    page.get_pixmap(dpi=args.dpi, alpha=False).save(image)
    result["image"] = image.name
    text = page.get_text("text", sort=True)
    coverage = image_coverage(page)
    garbled = text.count("\ufffd") > max(2, len(text) * 0.02)
    needs_ocr = meaningful_chars(text) < 40 or coverage > 0 or garbled
    result["image_coverage"] = round(coverage, 3)
    if args.ocr == "force" or (args.ocr == "auto" and needs_ocr):
        languages = args.language.split("+")
        missing = [language for language in languages if not (args.tessdata / f"{language}.traineddata").is_file()]
        if missing:
            result["warnings"].append("OCR language data missing: " + ", ".join(missing) + ". Run setup-ocr or provide --tessdata.")
        else:
            try:
                full_page = args.ocr == "force" or meaningful_chars(text) < 40 or garbled
                textpage = page.get_textpage_ocr(
                    language=args.language, dpi=200, full=full_page,
                    tessdata=str(args.tessdata),
                )
                text = page.get_text("text", textpage=textpage, sort=True)
                result["method"] = "ocr"
                result["ocr_mode"] = "full_page" if full_page else "image_regions"
                garbled = text.count("\ufffd") > max(2, len(text) * 0.02)
                if meaningful_chars(text) >= 40 and not garbled:
                    result["status"] = "extracted"
                result["warnings"].append("Check OCR names, dates, employers and numbers against the page image.")
            except Exception as exc:
                result["warnings"].append("OCR failed: " + str(exc))
    elif not needs_ocr:
        result["status"] = "extracted"
    else:
        result["warnings"].append("Text may be incomplete; OCR is disabled. Inspect the page image.")
    if meaningful_chars(text) < 40:
        result["warnings"].append("Very little text was extracted; this may be a scan, a sparse page or a blank page.")
    result["text_chars"] = len(text)
    return text, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_text", nargs="?", type=Path, help="Optional legacy text output path")
    parser.add_argument("--out-dir", type=Path, help="Empty artifact directory; otherwise create a unique directory in resume-screening/_tmp")
    parser.add_argument("--ocr", choices=("auto", "off", "force"), default="auto")
    parser.add_argument("--language", default="eng+chi_sim")
    parser.add_argument("--tessdata", type=Path, default=DEFAULT_TESSDATA)
    parser.add_argument("--dpi", type=int, default=144, help="Page preview DPI (72-300)")
    parser.add_argument("--password-env", help="Environment variable containing the password; the value is not printed")
    args = parser.parse_args()
    if not 72 <= args.dpi <= 300:
        parser.error("--dpi must be between 72 and 300")
    if not all(re.fullmatch(r"[A-Za-z0-9_]+", language) for language in args.language.split("+")):
        parser.error("--language must contain language names separated by +")
    source = args.pdf.expanduser().resolve()
    if not source.is_file():
        parser.error(f"PDF file not found: {source}")
    args.tessdata = args.tessdata.expanduser().resolve()
    if args.output_text and args.output_text.expanduser().exists():
        parser.error("Text output already exists; choose a new path to preserve the previous result.")

    try:
        with pymupdf.open(source) as document:
            if not document.is_pdf:
                parser.error("Input is not a PDF.")
            if document.needs_pass:
                password = os.environ.get(args.password_env, "") if args.password_env else ""
                if not password or not document.authenticate(password):
                    print("PDF is encrypted. Supply its password with --password-env VARIABLE_NAME.", file=sys.stderr)
                    return 4
            if document.page_count == 0:
                parser.error("PDF contains no pages.")
            if args.out_dir:
                directory = args.out_dir.expanduser().resolve()
                if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
                    parser.error("Artifact directory must be empty; choose a new --out-dir.")
            else:
                base = ROOT / "resume-screening/_tmp"
                base.mkdir(parents=True, exist_ok=True)
                directory = Path(tempfile.mkdtemp(prefix=source.stem + "-", dir=base))
            if args.output_text:
                output = args.output_text.expanduser().resolve()
                if output == directory or directory in output.parents:
                    parser.error("Legacy text output must be outside the artifact directory; use its text.txt instead.")
            directory.mkdir(parents=True, exist_ok=True)
            pages = []
            texts = []
            for page in document:
                try:
                    text, result = extract_page(page, directory, args)
                except Exception as exc:
                    text = ""
                    result = {"page": page.number + 1, "status": "needs_review", "method": "failed", "warnings": [str(exc)], "text_chars": 0}
                pages.append(result)
                texts.append(f"## Page {page.number + 1}\n\n{text.rstrip()}")
            complete = all(page["status"] == "extracted" for page in pages)
            report = {
                "source": str(source), "page_count": document.page_count,
                "status": "ready_for_review" if complete else "needs_review",
                "pages": pages,
                "review": "Inspect every page image for reading order, names, dates, employers and numbers before screening.",
            }
            text = f"# {source.name}\n\n" + "\n\n".join(texts) + "\n"
            (directory / "text.txt").write_text(text, encoding="utf-8")
            (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if args.output_text:
                output = args.output_text.expanduser()
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(text, encoding="utf-8")
            print(json.dumps({
                "status": report["status"], "pages": document.page_count,
                "artifacts": str(directory), "text": str(directory / "text.txt"),
                "report": str(directory / "report.json"),
                "unresolved_pages": [page["page"] for page in pages if page["status"] != "extracted"],
            }, ensure_ascii=False, indent=2))
            return 0 if complete else 3
    except (pymupdf.FileDataError, RuntimeError, OSError, ValueError) as exc:
        print(f"PDF processing failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
