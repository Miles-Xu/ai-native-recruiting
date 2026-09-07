import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "resume-screening/scripts/extract_resume.py"
SAMPLE = ROOT / "resume-screening/examples/resume_王五.pdf"
OCR_READY = all((ROOT / ".cache/tessdata" / f"{name}.traineddata").is_file() for name in ("eng", "chi_sim"))


class PdfWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="recruiting-pdf-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)

    def run_pdf(self, source, *args, code=0, env=None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", timeout=90, env=env,
        )
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def test_text_pdf_unicode_paths_and_page_preview(self):
        source = self.base / "测试 简历.pdf"
        source.write_bytes(SAMPLE.read_bytes())
        out = self.base / "新的目录" / "提取 结果"
        result = self.run_pdf(source, "--out-dir", out)
        self.assertEqual(json.loads(result.stdout)["status"], "ready_for_review")
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["page_count"], 1)
        self.assertEqual(report["pages"][0]["method"], "text_layer")
        self.assertIn("王五", (out / "text.txt").read_text(encoding="utf-8"))
        self.assertIn("Kubernetes", (out / "text.txt").read_text(encoding="utf-8"))
        pixels = pymupdf.Pixmap(str(out / "page-001.png"))
        self.assertGreater(pixels.width, 500)
        self.assertGreater(max(pixels.samples) - min(pixels.samples), 100)

    def test_legacy_text_output_creates_parent_directory(self):
        output = self.base / "new" / "resume.txt"
        self.run_pdf(SAMPLE, output, "--out-dir", self.base / "pages")
        self.assertIn("王五", output.read_text(encoding="utf-8"))

    def test_blank_page_cannot_succeed(self):
        source = self.base / "blank.pdf"
        with pymupdf.open() as document:
            document.new_page()
            document.save(source)
        out = self.base / "blank-output"
        result = self.run_pdf(source, "--out-dir", out, "--ocr", "off", code=3)
        self.assertEqual(json.loads(result.stdout)["unresolved_pages"], [1])
        self.assertTrue((out / "page-001.png").exists())

    def make_mixed_pdf(self):
        source = self.base / "mixed.pdf"
        with pymupdf.open(SAMPLE) as original, pymupdf.open() as document:
            document.insert_pdf(original)
            page = original[0]
            raster = page.get_pixmap(dpi=160).tobytes("png")
            scanned = document.new_page(width=page.rect.width, height=page.rect.height)
            scanned.insert_image(scanned.rect, stream=raster)
            document.save(source)
        return source

    @unittest.skipUnless(OCR_READY, "Run setup-ocr to enable the real OCR regression")
    def test_mixed_text_and_scanned_pdf_runs_real_ocr(self):
        out = self.base / "mixed-output"
        self.run_pdf(self.make_mixed_pdf(), "--out-dir", out)
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["page_count"], 2)
        self.assertEqual([page["method"] for page in report["pages"]], ["text_layer", "ocr"])
        self.assertGreater(report["pages"][1]["text_chars"], 500)
        second_page = (out / "text.txt").read_text(encoding="utf-8").split("## Page 2", 1)[1]
        self.assertIn("GPU", second_page)
        self.assertTrue((out / "page-002.png").exists())

    def test_missing_ocr_data_reports_partial_result(self):
        out = self.base / "partial"
        self.run_pdf(self.make_mixed_pdf(), "--out-dir", out, "--tessdata", self.base / "missing-data", code=3)
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "needs_review")
        self.assertEqual(report["pages"][0]["status"], "extracted")
        self.assertIn("OCR language data missing", " ".join(report["pages"][1]["warnings"]))

    def make_partial_image_pdf(self):
        source = self.base / "partial-image.pdf"
        with pymupdf.open() as snippet:
            image_page = snippet.new_page(width=500, height=160)
            image_page.insert_text((20, 50), "HiddenCorp 2021-2026", fontsize=22)
            image_page.insert_text((20, 90), "GPU platform engineering", fontsize=20)
            raster = image_page.get_pixmap(dpi=160).tobytes("png")
            with pymupdf.open() as document:
                page = document.new_page(width=595, height=842)
                page.insert_textbox(
                    pymupdf.Rect(30, 30, 560, 200),
                    "Candidate resume profile. Software engineer with Python and C++ experience. Education and contact information.",
                    fontsize=16,
                )
                page.insert_image(pymupdf.Rect(30, 240, 530, 400), stream=raster)
                document.save(source)
        return source

    @unittest.skipUnless(OCR_READY, "Run setup-ocr to enable the real OCR regression")
    def test_small_image_inside_text_page_is_read(self):
        out = self.base / "partial-image-output"
        self.run_pdf(self.make_partial_image_pdf(), "--out-dir", out)
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertLess(report["pages"][0]["image_coverage"], 0.5)
        self.assertEqual(report["pages"][0]["ocr_mode"], "image_regions")
        text = (out / "text.txt").read_text(encoding="utf-8")
        self.assertIn("HiddenCorp", text)
        self.assertIn("2021-2026", text)
        self.assertIn("Candidate resume profile", text)

    def test_small_image_without_ocr_is_not_complete(self):
        out = self.base / "partial-image-unresolved"
        self.run_pdf(self.make_partial_image_pdf(), "--out-dir", out, "--ocr", "off", code=3)
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "needs_review")

    def test_encrypted_pdf_requires_password_and_accepts_env(self):
        source = self.base / "encrypted.pdf"
        with pymupdf.open(SAMPLE) as document:
            document.save(source, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner-test", user_pw="fixture-password")
        out = self.base / "decrypted"
        self.run_pdf(source, "--out-dir", out, code=4)
        self.assertFalse(out.exists())
        env = dict(os.environ, RECRUITING_TEST_PDF_PASSWORD="fixture-password")
        self.run_pdf(source, "--out-dir", out, "--password-env", "RECRUITING_TEST_PDF_PASSWORD", env=env)
        self.assertIn("王五", (out / "text.txt").read_text(encoding="utf-8"))

    def test_invalid_inputs_do_not_create_output(self):
        out = self.base / "invalid-output"
        self.run_pdf(self.base / "missing.pdf", "--out-dir", out, code=2)
        broken = self.base / "broken.pdf"
        broken.write_bytes(b"not a PDF")
        self.run_pdf(broken, "--out-dir", out, code=2)
        self.assertFalse(out.exists())

    def test_existing_outputs_are_preserved(self):
        out = self.base / "existing"
        out.mkdir()
        sentinel = out / "text.txt"
        sentinel.write_text("previous result")
        self.run_pdf(SAMPLE, "--out-dir", out, code=2)
        self.assertEqual(sentinel.read_text(), "previous result")
        self.run_pdf(SAMPLE, sentinel, code=2)
        self.assertEqual(sentinel.read_text(), "previous result")

    def test_legacy_text_output_cannot_replace_artifacts(self):
        for name in ("report.json", "page-001.png", "text.txt"):
            with self.subTest(name=name):
                out = self.base / name.replace(".", "-")
                result = self.run_pdf(SAMPLE, out / name, "--out-dir", out, code=2)
                self.assertIn("outside the artifact directory", result.stderr)
                self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
