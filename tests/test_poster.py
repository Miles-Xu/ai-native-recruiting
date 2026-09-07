import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts/workflow.py"
TEMPLATE = ROOT / "jd-poster/jd_poster.html"


class PosterCliTests(unittest.TestCase):
    def run_command(self, *args):
        return subprocess.run([sys.executable, str(ENTRY), *map(str, args)], capture_output=True, text=True, encoding="utf-8", timeout=60)

    def test_invalid_width_and_missing_file_report_usage_errors(self):
        cases = [
            ("poster", [TEMPLATE, "0", "unused.png"], "greater than zero"),
            ("widths", [TEMPLATE, "400,bad"], "comma-separated integers"),
            ("widths", [TEMPLATE, "400,0"], "greater than zero"),
            ("poster", [ROOT / "missing.html", "440", "unused.png"], "HTML file not found"),
        ]
        for command, args, message in cases:
            with self.subTest(command=command, args=args):
                result = self.run_command(command, *args)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    @unittest.skipUnless(os.environ.get("RECRUITING_BROWSER_TESTS") == "1", "Set RECRUITING_BROWSER_TESTS=1 after doctor --browser succeeds")
    def test_local_html_and_unicode_path_render_nonblank_png(self):
        with tempfile.TemporaryDirectory(prefix="poster-test-") as directory:
            source = Path(directory) / "招聘 海报.html"
            source.write_bytes(TEMPLATE.read_bytes())
            output = Path(directory) / "new" / "海报.png"
            scan = self.run_command("widths", source, "400,440")
            self.assertEqual(scan.returncode, 0, scan.stderr)
            self.assertIn("scrollW=440", scan.stdout)
            result = self.run_command("poster", source, "440", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("scrollW=440", result.stdout)
            image = pymupdf.Pixmap(str(output))
            self.assertEqual(image.width, 1320)
            self.assertGreater(image.height, 1000)
            self.assertGreater(max(image.samples) - min(image.samples), 100)


if __name__ == "__main__":
    unittest.main()
