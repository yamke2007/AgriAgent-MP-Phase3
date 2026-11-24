"""Prepare a blank human verification queue without marking any case reviewed."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/reviewer_queue.csv")
    args = parser.parse_args()
    cases = json.loads((ROOT / "eval/case_index.json").read_text(encoding="utf-8"))
    fields = ("case_id", "agent", "language", "split", "input", "reference", "source", "source_locator",
              "parent_sha256", "reviewer", "checked_on", "verdict", "notes")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fields, extrasaction="ignore")
        writer.writeheader()
        for case in sorted(cases, key=lambda row: row.get("split") != "heldout"):
            writer.writerow(case)
    print(f"Prepared {len(cases)} review slots with blank sign-off fields")


if __name__ == "__main__":
    main()
