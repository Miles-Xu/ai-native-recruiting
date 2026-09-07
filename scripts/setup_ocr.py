"""Install pinned local OCR language data; never uploads input documents."""

import argparse
import hashlib
from pathlib import Path
import sys
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
REVISION = "87416418657359cb625c412a48b6e1d6d41c29bd"
HASHES = {
    "eng": "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2",
    "chi_sim": "a5fcb6f0db1e1d6d8522f39db4e848f05984669172e584e8d76b6b3141e1f730",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--languages", nargs="+", choices=HASHES, default=list(HASHES))
    args = parser.parse_args()
    directory = ROOT / ".cache/tessdata"
    directory.mkdir(parents=True, exist_ok=True)
    for language in args.languages:
        target = directory / f"{language}.traineddata"
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == HASHES[language]:
            print(f"{language}: ready")
            continue
        url = f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{REVISION}/{language}.traineddata"
        try:
            with urlopen(url, timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != HASHES[language]:
                raise ValueError(f"Checksum mismatch for {language}; downloaded data was not installed")
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(target)
            print(f"{language}: installed at {target}")
        except (OSError, URLError, ValueError) as exc:
            print(f"OCR setup failed: {exc}. Check network access; no resume was uploaded.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
