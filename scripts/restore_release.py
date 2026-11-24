"""Restore a SQLite SQL dump into a new database and check its integrity."""
import argparse
import contextlib
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", type=Path)
    parser.add_argument("database", type=Path)
    args = parser.parse_args()
    source = args.dump.read_text(encoding="utf-8")
    with contextlib.closing(sqlite3.connect(":memory:")) as db:
        db.executescript(source)
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",) or db.execute(
            "PRAGMA foreign_key_check"
        ).fetchone():
            raise SystemExit("Restored database failed integrity checks")
        with args.database.open("xb"):
            pass
        with contextlib.closing(sqlite3.connect(args.database)) as target:
            db.backup(target)
        print("Restored observations:", db.execute("SELECT count(*) FROM observations").fetchone()[0])


if __name__ == "__main__":
    main()
