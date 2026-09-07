"""Run repository workflows in the locked project environment."""

import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = {
    "pdf": ROOT / "resume-screening/scripts/extract_resume.py",
    "minutes": ROOT / "meeting-minutes/meeting-minutes/scripts/render_minutes.py",
    "poster": ROOT / "jd-poster/scripts/render_poster.py",
    "widths": ROOT / "jd-poster/scripts/sweep_width.py",
}


def doctor(args):
    parser = argparse.ArgumentParser(prog="run doctor")
    parser.add_argument("--browser", action="store_true", help="Also attempt to launch Chromium")
    options = parser.parse_args(args)
    report = {"python": sys.version.split()[0], "executable": sys.executable}
    for package in ("pymupdf", "playwright"):
        report[package] = importlib.metadata.version(package)
    tessdata = ROOT / ".cache/tessdata"
    report["ocr_languages"] = [p.stem for p in tessdata.glob("*.traineddata")]

    from playwright.sync_api import sync_playwright

    status = 0
    with sync_playwright() as playwright:
        browser_path = Path(playwright.chromium.executable_path)
        report["chromium"] = str(browser_path)
        report["browser_installed"] = browser_path.is_file()
        report["browser_launch"] = "not_checked"
        if options.browser:
            try:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.set_content("<title>Workflow check</title><p>Browser ready</p>")
                assert page.title() == "Workflow check"
                browser.close()
                report["browser_launch"] = "ok"
            except Exception as exc:
                report["browser_launch"] = "failed"
                report["browser_error"] = str(exc)
                report["next_step"] = (
                    "Run setup-browser first."
                    if not browser_path.is_file()
                    else "Check execution permissions and browser_error; do not reinstall Python to fix a sandbox denial."
                )
                status = 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=[*SCRIPTS, "doctor", "setup-browser", "setup-ocr", "test"])
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor(args.args)
    if args.command == "setup-browser":
        return subprocess.call([sys.executable, "-m", "playwright", "install", "chromium", *args.args])
    if args.command == "setup-ocr":
        return subprocess.call([sys.executable, str(ROOT / "scripts/setup_ocr.py"), *args.args])
    if args.command == "test":
        return subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), *args.args])
    if args.command == "minutes" and not any(arg == "--out-dir" or arg.startswith("--out-dir=") for arg in args.args):
        args.args += ["--out-dir", str(ROOT / "meeting-minutes/纪要档案")]
    return subprocess.call([sys.executable, str(SCRIPTS[args.command]), *args.args])


if __name__ == "__main__":
    raise SystemExit(main())
