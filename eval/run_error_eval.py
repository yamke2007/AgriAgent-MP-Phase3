"""Report source-backed robustness checks separately from extraction F1."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agriagent.pipeline import ROOT,process
from agriagent.normalization import MISSING

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/robustness")
    args = parser.parse_args()
    target = args.output.resolve()
    target.mkdir(parents=True, exist_ok=True)
    if any(target.iterdir()):
        parser.error("Choose an empty output directory")
    config = {"database": str(target / "agriagent.sqlite"), "output_dir": str(target / "runs"),
              "automation_log": str(target / "automation.csv")}
    cases=json.loads((ROOT/"eval/error_cases/index.json").read_text(encoding="utf-8"))
    rows=[]
    for c in cases:
        result=process(ROOT/c["input"],config=config,fault=c.get("fault"))
        passed=result["status"]==c["expected_status"]
        if "error_contains" in c:passed &= any(c["error_contains"] in e for e in result["errors"])
        if "missing_values" in c:passed &= sum(r["value"]==MISSING for r in result["records"])==c["missing_values"]
        if "allowed_variables" in c:
            passed &= {row["variable"] for row in result["records"]} == set(c["allowed_variables"])
        rows.append(dict(case_id=c["case_id"],run_id=result["run_id"],input_sha256=result["input_sha256"],expected=c["expected_status"],actual=result["status"],passed=bool(passed),errors=result["errors"]))
    report=dict(checks=rows,passed=sum(r["passed"] for r in rows),total=len(rows),note="Robustness evidence, not positive extraction examples or extraction F1")
    (target/"error_results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["passed"]==report["total"] else 1

if __name__=="__main__":raise SystemExit(main())
