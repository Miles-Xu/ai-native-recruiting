# Repository Workflows

Read `CLAUDE.md` for task routing and the relevant workflow instructions before acting.

- Run scripts through `./run` on macOS/Linux or `.\run.cmd` on Windows. This uses the repository's locked Python environment; do not substitute system Python, global pip installs, or guessed Python versions when a command fails.
- Run `./run doctor` to inspect dependencies. Poster tasks also need `./run doctor --browser`, which tests actual browser launch. A sandbox denial is not a missing Python package.
- Before reading or screening a PDF, read `docs/pdf-reading.md` and use `./run pdf`. Inspect `report.json` and every page image; a text file by itself does not establish complete extraction.
- Preserve real recruitment preferences as examples unless the user explicitly adopts or changes them. Keep facts, unverified claims and missing information distinct.
- Test data and generated artifacts belong in the workflow's ignored `_tmp/` directory or a temporary directory. Do not modify the public examples during a routine workflow run.
