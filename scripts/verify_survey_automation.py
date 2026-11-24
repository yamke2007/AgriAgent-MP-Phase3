"""Check the direct PDF route against the previously retained manual transcription."""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.pipeline import process
from eval.matching import counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = dict(database=str(output / "agriagent.sqlite"), output_dir=str(output / "runs"),
                  automation_log=str(output / "automation.csv"), scoped_survey=True)
    report = process(ROOT / "data/raw/mp_economic_survey.pdf", config, reference_calls=1)
    with (ROOT / "data/derived/survey_agriculture_transcription.csv").open(encoding="utf-8-sig", newline="") as stream:
        expected = list(csv.DictReader(stream))
    tp, fp, fn = counts(report["records"], expected)
    verification = {
        "source_url": report["source_url"], "input_sha256": report["input_sha256"],
        "status": report["status"], "true_positives": tp, "false_positives": fp, "false_negatives": fn,
        "manual_interventions": report["manual_interventions"], "run_id": report["run_id"],
        "trajectory": report["trajectory"], "warnings": report["warnings"],
        "scope": "Separate automation pilot for the survey agriculture section; original M12 cohort remains fixed",
    }
    (output / "report.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(json.dumps(verification, indent=2))
    return int(report["status"] != "complete" or fp != 0 or fn != 0)


if __name__ == "__main__":
    raise SystemExit(main())
