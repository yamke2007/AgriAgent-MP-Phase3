"""Retrieve and verify the pinned parents for release provenance checks."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/acquisition")
    args = parser.parse_args()
    data = ROOT / "data/production"
    sources = json.loads((data / "sources.json").read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    urls = {}
    for key, filename, digest in (
        ("production", "crop_production.csv", sources["production"]["parent_sha256"]),
        ("boundary", "districts.geojson", hashlib.sha256((data / "mp_districts.geojson").read_bytes()).hexdigest()),
    ):
        url = sources[key]["retrieval_url"]
        urls[key] = url
        path = args.output / filename
        if path.exists():
            content = path.read_bytes()
        else:
            with urllib.request.urlopen(url, timeout=45) as response:
                content = response.read(32 * 1024 * 1024 + 1)
        if hashlib.sha256(content).hexdigest() != digest:
            raise SystemExit(f"Hash differed for {filename}. Use the retained release snapshot.")
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(content)
        print("Verified", path)
    manifest = args.output / "urls.json"
    if not manifest.exists():
        with manifest.open("x", encoding="utf-8") as stream:
            json.dump(urls, stream, indent=2)


if __name__ == "__main__":
    main()
