import datetime
import html
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "meeting-minutes" / "meeting-minutes" / "scripts" / "render_minutes.py"
HTML_NAME = "\u7eaa\u8981.html"


class MinutesCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="minutes-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out_dir = self.root / "archives"

    def run_minutes(self, data, *options, transcript=None):
        structured = self.root / "input.json"
        structured.write_text(json.dumps(data), encoding="utf-8")
        command = [sys.executable, str(SCRIPT), "--structured", str(structured),
                   "--out-dir", str(self.out_dir), *options]
        if transcript is not None:
            source = self.root / "input.txt"
            source.write_bytes(transcript.encode("utf-8"))
            command.extend(["--transcript", str(source)])
        return subprocess.run(command, cwd=self.root, capture_output=True, text=True)

    def assert_archive(self, result, expected_date):
        self.assertEqual(result.returncode, 0, result.stderr)
        folder = self.out_dir / f"{expected_date}_Minutes"
        self.assertTrue(folder.is_dir(), result.stdout)
        self.assertTrue((folder / HTML_NAME).is_file())
        archived = json.loads((folder / "structured.json").read_text(encoding="utf-8"))
        self.assertEqual(archived["date"], expected_date)
        self.assertTrue(archived["generated_at"])
        return folder

    def assert_invalid_date(self, result, field):
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(field, result.stderr)
        self.assertIn("YYYY-MM-DD", result.stderr)
        self.assertFalse(self.out_dir.exists())
        self.assertEqual({p.name for p in self.root.iterdir()}, {"input.json"})

    def test_cli_date_overrides_json_in_directory_and_archive(self):
        result = self.run_minutes({"title": "Minutes", "date": "2000-01-01"},
                                  "--date", "2026-09-07")
        self.assert_archive(result, "2026-09-07")

    def test_cli_date_without_json_date(self):
        result = self.run_minutes({"title": "Minutes"}, "--date", "2026-09-07")
        self.assert_archive(result, "2026-09-07")

    def test_json_date_without_cli_date(self):
        result = self.run_minutes({"title": "Minutes", "date": "2024-02-29"})
        self.assert_archive(result, "2024-02-29")

    def test_default_date_is_today(self):
        before = datetime.date.today().isoformat()
        result = self.run_minutes({"title": "Minutes"})
        after = datetime.date.today().isoformat()
        self.assertEqual(result.returncode, 0, result.stderr)
        folders = list(self.out_dir.iterdir())
        self.assertEqual(len(folders), 1)
        archived = json.loads((folders[0] / "structured.json").read_text(encoding="utf-8"))
        self.assertIn(archived["date"], {before, after})
        self.assert_archive(result, archived["date"])

    def test_invalid_cli_dates_create_no_artifacts(self):
        invalid = ["", "2026-9-07", "2026/09/07", "2026-09-07 ", "2026-02-29",
                   "2026-13-01", "0000-01-01", "../escaped", str(self.root / "escaped")]
        for value in invalid:
            with self.subTest(date=value):
                result = self.run_minutes({"title": "Minutes"}, "--date", value)
                self.assert_invalid_date(result, "--date")

    def test_invalid_json_dates_create_no_artifacts(self):
        invalid = ["", "2026-9-07", "2026/09/07", "2026-09-07 ", "2026-02-29",
                   "2026-13-01", "0000-01-01", "../escaped", str(self.root / "escaped"),
                   None, 20260907, False, [], {}]
        for value in invalid:
            with self.subTest(date=value):
                result = self.run_minutes({"title": "Minutes", "date": value})
                self.assert_invalid_date(result, "JSON date")

    def test_invalid_json_date_is_rejected_even_with_valid_cli_date(self):
        result = self.run_minutes({"title": "Minutes", "date": "../escaped"},
                                  "--date", "2026-09-07")
        self.assert_invalid_date(result, "JSON date")

    def test_transcript_archive_and_summary_heading(self):
        transcript = "HR: <hello> & goodbye\n\u5019\u9009\u4eba: Friday evening.\n"
        data = {"title": "Minutes", "date": "2026-09-07", "recommendation": [
            {"label": "Current status", "value": "Employed"}
        ]}
        result = self.run_minutes(data, transcript=transcript)
        folder = self.assert_archive(result, "2026-09-07")
        self.assertEqual({p.name for p in folder.iterdir()},
                         {HTML_NAME, "structured.json", "transcript.txt"})
        self.assertEqual((folder / "transcript.txt").read_bytes(), transcript.encode("utf-8"))
        rendered = (folder / HTML_NAME).read_text(encoding="utf-8")
        self.assertIn(html.escape(transcript), rendered)
        self.assertIn('<details class="src">', rendered)
        self.assertIn("\u6c9f\u901a\u6458\u8981", rendered)
        self.assertNotIn("\u63a8\u8350\u8bc4\u8bed", rendered)


if __name__ == "__main__":
    unittest.main()
