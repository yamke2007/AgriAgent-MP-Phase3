"""Fetch public annual Agmarknet archives used by the evaluation cases."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/eval-parents")
    args = parser.parse_args()
    index = json.loads((ROOT / "eval/case_index.json").read_text(encoding="utf-8"))
    parents = {case["parent_sha256"]: case["source"] for case in index if case.get("parent_remote")}
    args.output.mkdir(parents=True, exist_ok=True)
    failed = []
    for expected, url in parents.items():
        path = args.output / (expected + ".csv")
        try:
            if path.exists():
                data = path.read_bytes()
            else:
                with urllib.request.urlopen(url, timeout=25) as response:
                    data = response.read(48 * 1024 * 1024 + 1)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("Archive hash differs from the case manifest")
            if not path.exists():
                with path.open("xb") as out:
                    out.write(data)
        except (OSError, ValueError) as exc:
            failed.append(url)
            print(f"Unavailable {url}: {exc}")
    print(f"Verified {len(parents)-len(failed)}/{len(parents)} parent files")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
