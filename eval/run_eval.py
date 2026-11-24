"""Reproducible local evidence; provisional CSV header (official attachment absent)."""
import argparse
import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agriagent.pipeline import ROOT, process, sha
from agriagent.storage import dump
from eval.matching import counts, f1
from eval.contamination import audit
from eval.agent_metrics import trajectory_match, workflow_eval
from eval.source_checks import archive_support, input_support

COLUMNS=["metric_id","scope","value","numerator","denominator","floor","target","direction","status","evidence","notes"]
BOUNDS=[(.5,1),(.2,.6),(.5,.85),(.6,.95),(.3,.75),(.6,.9),(.6,.9),(.5,.8),(.5,.9),(.7,.95),(.5,.9),(.3,.8),(.5,.1),(.8,1),(.7,.98),(.1,0),(1,3),(None,None)]

def provenance_ok(case, result, parents, survey_sources):
    """Resolve comparable records at the source locator and check the normalized tuple."""
    if case.get("parent_remote"):
        parent = parents / (case["parent_sha256"] + ".csv") if parents else None
        if parent and parent.is_file():
            if sha(parent) != case["parent_sha256"]:
                raise ValueError("Changed remote source: " + case["source"])
            records = result["records"]
            return sum(archive_support(ROOT / case["input"], parent, r["locator"], r)
                       for r in records), len(records)
        return 0, 0
    if case["agent"] == "statistics":
        parent = ROOT / case["source"]
        if parent not in survey_sources:
            if sha(parent) != case["parent_sha256"]:
                raise ValueError("Changed original source: " + case["source"])
            survey_sources[parent] = process(parent, {"scoped_survey": True}, persist=False)["records"]
        page_records = [row for row in survey_sources[parent] if row.get("origin_locator") == case["source_locator"]]
        return counts(result["records"], page_records)[0], len(result["records"])
    if case["agent"] not in {"directory", "scheme"}:
        return 0, 0
    parent = ROOT / case["source"]
    if sha(parent) != case["parent_sha256"]:
        raise ValueError("Changed original source: " + case["source"])
    records = result["records"]
    correct = sum(
        input_support(ROOT / case["input"], r["locator"], case["agent"], r)
        and input_support(parent, case["source_locator"], case["agent"], r)
        for r in records
    )
    return correct, len(records)

def evaluate(output, production_db=None, parents=None):
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Choose an empty evaluation output directory to preserve prior evidence")
    config = {
        "database": str(output / "agriagent.sqlite"),
        "output_dir": str(output / "runs"),
        "automation_log": str(output / "automation.csv"),
    }
    index=json.loads((ROOT/"eval/case_index.json").read_text(encoding="utf-8"))
    groups=defaultdict(list); evidence=[]
    survey_sources = {}
    for case in index:
        if sha(ROOT/case["input"])!=case["input_sha256"]:
            raise ValueError("Changed case: "+case["case_id"])
        ref=json.loads((ROOT/case["reference"]).read_text(encoding="utf-8"))["records"]
        if case["agent"]=="tables":
            expected=[dict(tool="csv.reader",arguments=dict(input_sha256=case["input_sha256"],schema="observation-v1"))]
        else:
            tool="csv.DictReader" if case["agent"]=="statistics" else "beautifulsoup4"
            expected=[dict(tool=tool,arguments=dict(input_sha256=case["input_sha256"],schema="observation-v1",max_pages=None))]
        result=process(ROOT/case["input"], config=config, reference_calls=len(expected))
        tp,fp,fn=counts(result["records"],ref)
        calls=result["trajectory"]
        aligned = [(actual, wanted) for actual, wanted in zip_longest(calls, expected)
                   if actual is not None and wanted is not None]
        completion=bool(result["records"]) and all(r["validation_status"]=="valid" for r in result["records"]) and result["status"]=="complete"
        pc,pn=provenance_ok(case, result, parents, survey_sources)
        row=dict(case_id=case["case_id"],agent=case["agent"],source_group=case["source_group"],language=case["language"],
                 tp=tp,fp=fp,fn=fn,f1=f1(tp,fp,fn),provenance_correct=pc,provenance_total=pn,
                 tool_correct=sum(actual["tool"] == wanted["tool"] for actual, wanted in aligned),
                 input_correct=sum(actual == wanted for actual, wanted in aligned), calls=len(calls),
                 trajectory_correct=int(trajectory_match(calls,expected,"strict","exact")),complete=int(completion),run_id=result["run_id"],
                 grounded_ok=sum(input_support(ROOT / case["input"], r["locator"], case["agent"], r)
                                 for r in result["records"]),grounded_n=len(result["records"]),
                 latency_seconds=result["latency_seconds"],status=result["status"],
                 retries=result["retries"], llm_calls=result.get("llm_calls", 0),
                 llm_tokens=None, model_cost=None,
                 errors=result["errors"], warnings=result["warnings"],
                 validation_errors=[error for r in result["records"] for error in r["validation_errors"]])
        evidence.append(row)
        for scope in (case["agent"],case["source_group"],"end_to_end","language:"+case["language"])+(("split:"+case["split"],) if case.get("split") else ()):
            groups[scope].append(row)
    (output/"results.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
    summary = {
        "status_counts": Counter(row["status"] for row in evidence),
        "validation_errors": Counter(error for row in evidence for error in row["validation_errors"]),
        "extraction_errors": Counter(error.split(":", 1)[0] for row in evidence for error in row["errors"]),
        "false_positives": sum(row["fp"] for row in evidence),
        "false_negatives": sum(row["fn"] for row in evidence),
        "unresolved_original_records": sum(row["grounded_n"] - row["provenance_total"] for row in evidence),
        "retries": sum(row["retries"] for row in evidence),
        "llm_calls": sum(row["llm_calls"] for row in evidence),
    }
    (output/"error_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    metrics=[]
    def add(mid,scope,value=None,num=None,den=None,status="measured_local",notes="",evidence_path="results.json"):
        lo,hi=BOUNDS[mid-1]
        metrics.append(dict(zip(COLUMNS,["M"+str(mid),scope,value,num,den,lo,hi,"lower" if mid in (13,16) else "higher",status,evidence_path,notes])))
    with (ROOT/"docs/source_agent_map.csv").open(encoding="utf-8-sig",newline="") as f:
        mapping=list(csv.DictReader(f))
    add(1,"end_to_end",sum(bool(r["agent"]) for r in mapping)/len(mapping),sum(bool(r["agent"]) for r in mapping),len(mapping),evidence_path="docs/source_agent_map.csv")
    add(2,"end_to_end",sum(r["status"] in ("done","partial") for r in mapping)/len(mapping),sum(r["status"] in ("done","partial") for r in mapping),len(mapping),evidence_path="docs/source_agent_map.csv")
    for scope,rs in groups.items():
        total=lambda k:sum(r[k] for r in rs)
        add(3,scope,f1(total("tp"),total("fp"),total("fn")),2*total("tp"),2*total("tp")+total("fp")+total("fn"),notes="Field tuples; source-derived fragments; CSV cases measure import, not PDF extraction")
        add(4,scope,total("provenance_correct")/total("provenance_total") if total("provenance_total") else None,total("provenance_correct"),total("provenance_total"),status="local_locator_check",notes=f"Resolved HTML rows, survey PDF page and available CSV archives. Checked {total('provenance_total')}/{total('grounded_n')} records; evaluator verification pending")
        for mid,key,den in ((6,"tool_correct","calls"),(7,"input_correct","calls")):
            add(mid,scope,total(key)/total(den) if total(den) else None,total(key),total(den),notes="Deterministic exact reference comparison; no LLM judge / external service")
        add(8,scope,total("trajectory_correct")/len(rs),total("trajectory_correct"),len(rs),notes="AgentEvals create_trajectory_match_evaluator, mode=strict, tool_args=exact")
        add(9,scope,total("complete")/len(rs),total("complete"),len(rs),notes="All records valid, explicit missing codes allowed; required value cannot be missing")
        add(10,scope,total("grounded_ok")/total("grounded_n") if total("grounded_n") else None,total("grounded_ok"),total("grounded_n"),notes="Match variable, context, unit and value in resolved input cells; no LLM judge")
    # Weight each represented agent equally, independent of output volume.
    agents=sorted({c["agent"] for c in index})
    for mid in (3,4,6,7,8,9,10):
        values=[r["value"] for r in metrics if r["metric_id"]=="M"+str(mid) and r["scope"] in agents and r["value"] is not None]
        add(mid,"macro_agents",sum(values)/len(values) if len(values)==len(agents) else None,
            den=len(agents),status="measured_local" if len(values)==len(agents) else "incomplete_coverage",
            notes=f"Arithmetic mean across implemented agents; {len(values)}/{len(agents)} scored")
    add(5,"surprise",status="awaiting_instructor",notes="Requires three instructor items and checked answer key")
    wf=workflow_eval(ROOT,process)
    (output/"workflow_results.json").write_text(json.dumps(wf,indent=2,ensure_ascii=False),encoding="utf-8")
    fault=[w for w in wf if w["fault"]]
    multi = [w for w in wf if len(w["expected_plan"]) > 1 and not w["fault"]]
    complete = sum(w["correct"] and w["status"] == "complete" for w in multi)
    add(11,"end_to_end",complete/len(multi) if multi else None,complete,len(multi),status="local_mixed_cohort",
        evidence_path="workflow_results.json",notes=f"All planned multi-agent runs including partial/failed outcomes; local fault demonstrated separately: {bool(fault and all(w['correct'] for w in fault))}; live LangSmith pending")
    with (output/"automation.csv").open(encoding="utf-8",newline="") as f:
        logs=list(csv.DictReader(f))
    automated=sum(r["status"]=="complete" and int(r["manual_interventions"])==0 for r in logs)
    add(12,"end_to_end",automated/len(logs),automated,len(logs),evidence_path="automation.csv",notes="Positive benchmark cohort; see separate robustness and release traces")
    calls=sum(int(r["tool_calls"]) for r in logs)
    refs=sum(int(row["reference_calls"]) for row in logs)
    add(13,"end_to_end",(calls-refs)/calls if calls else None,calls-refs,calls,evidence_path="automation.csv",
        notes="Reference call count from the declared case trajectories; LLM calls are included in tool_calls; retries="+str(sum(int(r["retries"]) for r in logs)))
    db_path = (production_db or (output / "agriagent.sqlite")).resolve(strict=True)
    db=sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)
    count=db.execute("SELECT count(*) FROM observations").fetchone()[0]
    mandatory="source source_type agent run_id locator crop location period unit".split()
    complete=db.execute("SELECT count(*) FROM observations WHERE "+" AND ".join(f"{k} IS NOT NULL AND length(trim({k}))>0" for k in mandatory)).fetchone()[0]
    valid=db.execute("SELECT count(*) FROM observations WHERE validation_status='valid'").fetchone()[0]
    duplicated=db.execute("SELECT coalesce(sum(n),0) FROM (SELECT count(*) n FROM observations GROUP BY source,locator,crop,location,period,variable HAVING count(*)>1)").fetchone()[0]
    for mid,num,note in ((14,complete,"Explicit MISSING codes count as filled; not evidence of known values"),(15,valid,"Declared rules; no supplied LGD registry; location name accuracy unverified"),(16,duplicated,"Rows in duplicate natural-key groups / stored rows; insertion duplicates rejected, attempts retained")):
        add(mid,"end_to_end",num/count if count else None,num,count,
            evidence_path=str(db_path.relative_to(ROOT) if db_path.is_relative_to(ROOT) else db_path),notes=note)
    db.close()
    add(17,"end_to_end",status="awaiting_instructor",notes="Evaluator randomly selects 3 database rows live")
    add(18,"end_to_end",status="separate_evaluation",notes="Use compare_adapters.py --run-dir output/m18 and the verified M18 evidence snapshot")
    contamination=audit(ROOT)
    (output/"contamination_report.json").write_text(json.dumps(contamination,indent=2),encoding="utf-8")
    with (output/"phase2_metrics.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS); w.writeheader(); w.writerows(metrics)
    dump(output/"agriagent.sqlite",output/"dump")
    print(json.dumps(dict(cases=len(index),agents={k:len(v) for k,v in groups.items() if k in ("directory","scheme","statistics")},
         macro_f1=next(r["value"] for r in metrics if r["metric_id"]=="M3" and r["scope"]=="macro_agents"),
         metrics_rows=len(metrics),contamination=contamination),indent=2))

if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/evaluation")
    parser.add_argument("--production-db", type=Path)
    parser.add_argument("--parents", type=Path, default=ROOT / "output/eval-parents")
    args = parser.parse_args()
    evaluate(args.output.resolve(), args.production_db, args.parents)
