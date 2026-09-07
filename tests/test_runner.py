import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def test_entrypoint_uses_project_environment_from_another_directory(self):
        if os.name == "nt":
            command = ["cmd", "/d", "/c", str(ROOT / "run.cmd"), "doctor"]
        else:
            command = [str(ROOT / "run"), "doctor"]
        with tempfile.TemporaryDirectory(prefix="runner-test-") as directory:
            result = subprocess.run(command, cwd=directory, capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["python"].startswith("3.12."))
        executable = Path(report["executable"])
        self.assertIn(ROOT / ".venv", executable.parents)
        self.assertEqual(report["pymupdf"], "1.26.5")
        self.assertEqual(report["browser_launch"], "not_checked")


if __name__ == "__main__":
    unittest.main()
