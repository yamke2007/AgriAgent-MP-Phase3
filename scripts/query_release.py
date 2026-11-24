"""List or run the Phase 3 queries against the release SQLite database."""
import argparse
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.queries import QUERIES, execute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", choices=[*QUERIES, "list", "all", "verify"])
    parser.add_argument("--db", type=Path, default=ROOT / "output/release/agriagent.sqlite")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.query == "list":
        for code, query in QUERIES.items():
            print(f"{code} [{query.category}] {query.title}")
        return 0
    codes = [args.query] if args.query in QUERIES else list(QUERIES)
    with closing(sqlite3.connect(args.db.resolve(strict=True).as_uri() + "?mode=ro", uri=True)) as db:
        results = {code: execute(db, code) for code in codes}
    report = {"results": results}
    if args.query == "verify":
        expected = json.loads((ROOT / "db/queries_expected.json").read_text(encoding="utf-8"))
        checks = {
            code: {"passed": rows == expected[code], "rows": len(rows), "category": QUERIES[code].category}
            for code, rows in results.items()
        }
        report.update(checks=checks, passed=sum(c["passed"] for c in checks.values()), total=len(checks))
    summary = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as out:
            out.write(summary)
    print(summary, end="")
    return int(args.query == "verify" and report["passed"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
