"""Acquire or verify the exact raw snapshots used by the expanded source checks."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/source_expansion/cohort.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windows-trust", action="store_true", help="verify TLS with the native Windows root store")
    args = parser.parse_args()
    if args.windows_trust:
        import truststore
        truststore.inject_into_ssl()
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    failures = 0
    for item in plan["inputs"]:
        path = ROOT / item["path"]
        try:
            if path.is_file():
                content = path.read_bytes()
            elif item["sample"] != "original":
                request = urllib.request.Request(item["url"], headers={"User-Agent": "AgriAgent coursework source check"})
                with urllib.request.urlopen(request, timeout=25) as response:
                    content = response.read(24 * 1024**2 + 1)
            else:
                raise FileNotFoundError(path)
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ValueError("Published bytes have changed; use the retained snapshot for this cohort")
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    stream.write(content)
            print(f"{item['source_id']} {path.name} verified")
        except (OSError, ValueError) as exc:
            failures += 1
            print(f"{path.name}: {exc}")
    return int(failures != 0)


if __name__ == "__main__":
    raise SystemExit(main())
