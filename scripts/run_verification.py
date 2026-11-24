"""Execute functional checks and preserve their actual process results."""
import json
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    commands=[(["-m","unittest","discover","-v"],0),
       (["run.py","--input","data/raw/icar_kvk.html"],0),
       (["run.py","--input","data/raw/msp_scheme.html"],2),
       (["run.py","--input","data/raw/mp_economic_survey.pdf"],2),
       (["run.py","--input","data/derived/survey_agriculture_transcription.csv","--manual-interventions","1"],0),
       (["run.py","--input","data/raw/evikas_calculator.html"],1),
       (["run.py","--input","data/raw/icar_kvk.html","--fault","extract"],1),
       (["run.py","--input","data/raw/icar_kvk.html","--fault","database"],1),
       (["eval/compare_adapters.py"],0),
       (["scripts/db_cli.py","--id","1"],0),(["scripts/db_cli.py","--dump"],0)]
    results=[]
    report_path=ROOT/"evidence/test_report.json"
    for args,expected in commands:
        try:
            # Evaluators invoke Tesseract subprocesses. Let their output inherit the
            # console instead of capturing nested process pipes, which can hang on
            # some OCR/runtime combinations. Other checks retain captured evidence.
            if args[0].startswith("eval/"):
                run=subprocess.run([sys.executable]+args,cwd=ROOT,timeout=90)
                stdout=stderr=""
            else:
                run=subprocess.run([sys.executable]+args,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=90)
                stdout,stderr=run.stdout,run.stderr
            item=dict(command=[sys.executable]+args,exit_code=run.returncode,expected_exit_code=expected,
                      passed=run.returncode==expected,stdout=stdout,stderr=stderr)
        except subprocess.TimeoutExpired as exc:
            item=dict(command=[sys.executable]+args,exit_code=None,expected_exit_code=expected,passed=False,
                      stdout=(exc.stdout or "")[-4000:],stderr=(exc.stderr or "")[-4000:],error="Timed out after 90 seconds")
        results.append(item)
        report=dict(executed_at=datetime.now(timezone.utc).isoformat(),python=sys.version,checks=results,
                    status="passed" if len(results)==len(commands) and all(r["passed"] for r in results) else "in_progress_or_failed")
        report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps(dict(command=" ".join(args),exit_code=item["exit_code"],passed=item["passed"])),flush=True)
    report["status"]="passed" if all(r["passed"] for r in results) else "failed"
    report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
    return 0 if report["status"]=="passed" else 1

if __name__=="__main__":raise SystemExit(main())
