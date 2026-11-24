"""Build an isolated database from the explicitly selected real corpus."""
import argparse
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agriagent.pipeline import ROOT, process
from agriagent.storage import dump

CORPUS = (
    "data/raw/icar_kvk.html",
    "data/raw/msp_scheme.html",
    "data/derived/survey_agriculture_transcription.csv",
    "data/production/mp_crop_production_2016_2022.csv",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/release")
    parser.add_argument("--lgd-registry", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Choose an empty output directory to preserve existing runs.")
    config = {
        "database": str(output / "agriagent.sqlite"),
        "output_dir": str(output / "runs"),
        "automation_log": str(output / "automation.csv"),
    }
    if args.lgd_registry:
        config["lgd_registry"] = str(args.lgd_registry.resolve(strict=True))
    runs = [process(ROOT / name, config) for name in CORPUS]
    if any(not result["records"] or result["status"] == "failed" for result in runs):
        raise SystemExit("Release ingestion failed. See the retained run traces.")
    with closing(sqlite3.connect(config["database"])) as db:
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",) or db.execute(
            "PRAGMA foreign_key_check"
        ).fetchone():
            raise SystemExit("Release database integrity check failed")
    dump(config["database"], output / "dump")
    with closing(sqlite3.connect(":memory:")) as restored:
        restored.executescript((output / "dump/agriagent.sql").read_text(encoding="utf-8"))
        count = restored.execute("SELECT count(*) FROM observations").fetchone()[0]
        if restored.execute("PRAGMA foreign_key_check").fetchone() or count != sum(
            run["storage"]["inserted"] for run in runs
        ):
            raise SystemExit("Release dump restore check failed")
    report = {
        "observations": count,
        "dump_restore": "passed",
        "inputs": [
            {key: run[key] for key in ("input", "input_sha256", "status", "run_id", "storage")}
            for run in runs
        ],
    }
    (output / "build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
