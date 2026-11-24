"""Execute the frozen genuine-input cohort and verify source claims and M12."""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.pipeline import process, sha
from eval.matching import counts

PLAN = ROOT / "data/source_expansion/cohort.json"
SURVEY_PDF = "data/raw/mp_economic_survey.pdf"
SURVEY_SHA = "3457d6dc615a35d4ee1c61b338845d58deee2e31f67f8dce55f7611e1a5302f4"


def check_fields(records, expected):
    matches = []
    for target in expected:
        found = [row for row in records if all(str(row.get(key)) == str(value) for key, value in target.items())]
        matches.append({"expected": target, "matched": len(found) == 1,
                        "locator": found[0]["locator"] if len(found) == 1 else None})
    return matches


def automation(rows, *, include_upstream_manual=True):
    complete = sum(row["status"] == "complete" and
                   (not include_upstream_manual or row["manual_interventions"] == 0) for row in rows)
    return {"completed_without_manual_intervention": complete, "attempted": len(rows),
            "value": complete / len(rows) if rows else None,
            "status_counts": dict(Counter(row["status"] for row in rows))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lgd-registry", type=Path)
    parser.add_argument("--direct-survey", action="store_true",
                        help="Paired rerun using the original survey PDF for the same ten facts")
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        path = ROOT / item["path"]
        if sha(path) != item["sha256"]:
            raise ValueError(f"Missing or changed frozen input: {item['path']}")
    if args.direct_survey and sha(ROOT / SURVEY_PDF) != SURVEY_SHA:
        raise ValueError("Missing or changed original survey PDF")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = dict(database=str(output / "agriagent.sqlite"), output_dir=str(output / "runs"),
                  automation_log=str(output / "automation.csv"), max_pdf_pages=500)
    if args.lgd_registry:
        config["lgd_registry"] = str(args.lgd_registry.resolve(strict=True))
    records = []
    for item in plan["inputs"]:
        survey = args.direct_survey and item["source_id"] == "S23"
        path = SURVEY_PDF if survey else item["path"]
        result = process(ROOT / path, dict(config, scoped_survey=True) if survey else config,
                         source_url=item["url"],
                         manual_interventions=0 if survey else item.get("manual_interventions", 0),
                         reference_calls=len(item["tools"]) if "tools" in item else None)
        row = {key: result[key] for key in ("status", "run_id", "manual_interventions", "warnings", "errors", "tool_calls")}
        row.update(input=path, input_sha256=result["input_sha256"], source_id=item["source_id"], sample=item["sample"],
                   outputs=len(result["records"]),
                   valid=sum(r["validation_status"] == "valid" for r in result["records"]))
        row["checks"] = check_fields(result["records"], item.get("checks", []))
        row["trajectory"] = [call["tool"] for call in result["trajectory"]]
        row["verified"] = (row["status"] == item["expected_status"] and row["outputs"] == item["expected_count"]
                           and row["valid"] == item.get("expected_valid", item["expected_count"])
                           and all(check["matched"] for check in row["checks"])
                           and ("tools" not in item or row["trajectory"] == item["tools"]))
        if survey:
            with (ROOT / item["path"]).open(encoding="utf-8-sig", newline="") as stream:
                expected = list(csv.DictReader(stream))
            score = counts(result["records"], expected)
            row.update(paired_reference=item["path"], paired_field_counts=dict(zip(("tp", "fp", "fn"), score)))
            row["verified"] = row["verified"] and score == (len(expected), 0, 0)
        records.append(row)
        print(row["source_id"], row["status"], row["outputs"], row["valid"], row["verified"])

    with (output / "automation.csv").open(encoding="utf-8", newline="") as stream:
        logged = list(csv.DictReader(stream))
    if [row["run_id"] for row in logged] != [row["run_id"] for row in records]:
        raise ValueError("Run ledger and input cohort differ")
    baseline = [row for row in records if row["sample"] == "original"]
    from_log = sum(row["status"] == "complete" and int(row["manual_interventions"]) == 0 for row in logged)
    report = {
        "cohort_sha256": sha(PLAN),
        "scope": ("Matched 17-case rerun: original survey PDF replaces the assisted CSV in the same source/facts slot"
                  if args.direct_survey else "Original frozen cohort including historically transcribed input"),
        "m12": automation(records),
        "original_inputs_m12": automation(baseline),
        "original_ingestion_only_comparison": automation(baseline, include_upstream_manual=False),
        "cases": records,
        "verified": sum(row["verified"] for row in records),
        "coverage_candidates_verified": sorted({
            row["source_id"] for row, item in zip(records, plan["inputs"], strict=True)
            if item.get("new_coverage") and row["verified"]
        }),
    }
    if from_log != report["m12"]["completed_without_manual_intervention"]:
        raise ValueError("Automation cannot be reconciled to the log")
    with (output / "report.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
    print(json.dumps({key: report[key] for key in ("m12", "original_inputs_m12", "verified", "coverage_candidates_verified")}))
    return int(report["verified"] != len(records))


if __name__ == "__main__":
    raise SystemExit(main())
