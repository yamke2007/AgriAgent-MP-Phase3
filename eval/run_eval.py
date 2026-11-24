"""Reproducible local evidence; provisional CSV header (official attachment absent)."""
import argparse
import csv
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agriagent.pipeline import ROOT, process, sha
from agriagent.storage import dump
from eval.matching import counts, f1
from eval.contamination import audit
from eval.agent_metrics import grounded, trajectory_match, workflow_eval

COLUMNS=["metric_id","scope","value","numerator","denominator","floor","target","direction","status","evidence","notes"]
BOUNDS=[(.5,1),(.2,.6),(.5,.85),(.6,.95),(.3,.75),(.6,.9),(.6,.9),(.5,.8),(.5,.9),(.7,.95),(.5,.9),(.3,.8),(.5,.1),(.8,1),(.7,.98),(.1,0),(1,3),(None,None)]

def provenance_ok(case,result):
    """Check local locator resolution; evaluator must independently verify semantic attribution."""
    from bs4 import BeautifulSoup
    path=ROOT/case["input"]
    if sha(path)!=case["input_sha256"] or (not case.get("parent_remote") and sha(ROOT/case["source"])!=case["parent_sha256"]):
        return 0,len(result["records"])
    correct=0
    for r in result["records"]:
        try:
            if r["locator"].startswith("table:"):
                ti,ri=[int(part.split(":")[1])-1 for part in r["locator"].split("/")]
                table=BeautifulSoup(path.read_bytes(),"html.parser").find_all("table")[ti]
                from agriagent.normalization import text
                content=text(table.find_all("tr")[ri].get_text(" ",strip=True))
                correct += str(r["value"]) in content
            elif r["locator"].startswith("csv/row:"):
                # tables agent: row R of the case file must contain the value
                ri=int(r["locator"].split("/")[1].split(":")[1])
                line=path.read_text(encoding="utf-8").splitlines()[ri-1]
                correct += str(r["value"]) in line.replace('"','').replace(",","") or str(r["value"]) in line
            elif r["locator"].startswith("csv:line:"):
                # Header plus one data record in checked fragments; evidence points to exact raw row.
                content=path.read_text(encoding="utf-8")
                correct += str(r["value"]) in content and int(r["locator"].split(":")[-1])<=len(content.splitlines())
        except (IndexError,ValueError):
            pass
    return correct,len(result["records"])

def evaluate():
    index=json.loads((ROOT/"eval/case_index.json").read_text(encoding="utf-8"))
    groups=defaultdict(list); evidence=[]
    for case in index:
        if sha(ROOT/case["input"])!=case["input_sha256"]:
            raise ValueError("Changed case: "+case["case_id"])
        ref=json.loads((ROOT/case["reference"]).read_text(encoding="utf-8"))["records"]
        result=process(ROOT/case["input"])
        tp,fp,fn=counts(result["records"],ref)
        if case["agent"]=="tables":
            expected=[dict(tool="csv.reader",arguments=dict(input_sha256=case["input_sha256"],schema="observation-v1"))]
        else:
            tool="csv.DictReader" if case["agent"]=="statistics" else "beautifulsoup4"
            expected=[dict(tool=tool,arguments=dict(input_sha256=case["input_sha256"],schema="observation-v1",max_pages=None))]
        calls=result["trajectory"]
        completion=bool(result["records"]) and all(r["validation_status"]=="valid" for r in result["records"]) and result["status"]=="complete"
        pc,pn=provenance_ok(case,result)
        row=dict(case_id=case["case_id"],agent=case["agent"],source_group=case["source_group"],language=case["language"],
                 tp=tp,fp=fp,fn=fn,f1=f1(tp,fp,fn),provenance_correct=pc,provenance_total=pn,
                 tool_correct=sum(c["tool"]==expected[0]["tool"] for c in calls),
                 input_correct=sum(c["arguments"]==expected[0]["arguments"] for c in calls),calls=len(calls),
                 trajectory_correct=int(trajectory_match(calls,expected,"strict","exact")),complete=int(completion),run_id=result["run_id"],
                 grounded_ok=sum(grounded(r) for r in result["records"]),grounded_n=len(result["records"]),
                 latency_seconds=result["latency_seconds"],status=result["status"])
        evidence.append(row)
        for scope in (case["agent"],case["source_group"],"end_to_end","language:"+case["language"])+(("split:"+case["split"],) if case.get("split") else ()):
            groups[scope].append(row)
    (ROOT/"eval/results.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
    metrics=[]
    def add(mid,scope,value=None,num=None,den=None,status="measured_local",notes="",evidence_path="eval/results.json"):
        lo,hi=BOUNDS[mid-1]
        metrics.append(dict(zip(COLUMNS,["M"+str(mid),scope,value,num,den,lo,hi,"lower" if mid in (13,16) else "higher",status,evidence_path,notes])))
    with (ROOT/"docs/source_agent_map.csv").open(encoding="utf-8-sig",newline="") as f:
        mapping=list(csv.DictReader(f))
    add(1,"end_to_end",sum(bool(r["agent"]) for r in mapping)/len(mapping),sum(bool(r["agent"]) for r in mapping),len(mapping),evidence_path="docs/source_agent_map.csv")
    add(2,"end_to_end",sum(r["status"] in ("done","partial") for r in mapping)/len(mapping),sum(r["status"] in ("done","partial") for r in mapping),len(mapping),evidence_path="docs/source_agent_map.csv")
    for scope,rs in groups.items():
        total=lambda k:sum(r[k] for r in rs)
        add(3,scope,f1(total("tp"),total("fp"),total("fn")),2*total("tp"),2*total("tp")+total("fp")+total("fn"),notes="Field tuples; source-derived fragments; CSV cases measure import, not PDF extraction")
        add(4,scope,total("provenance_correct")/total("provenance_total") if total("provenance_total") else None,total("provenance_correct"),total("provenance_total"),status="local_locator_proxy",notes="Local source resolver; evaluator source-value check still required")
        for mid,key,den in ((6,"tool_correct","calls"),(7,"input_correct","calls")):
            add(mid,scope,total(key)/total(den) if total(den) else None,total(key),total(den),notes="Deterministic exact reference comparison; no LLM judge / external service")
        add(8,scope,total("trajectory_correct")/len(rs),total("trajectory_correct"),len(rs),notes="AgentEvals create_trajectory_match_evaluator, mode=strict, tool_args=exact")
        add(9,scope,total("complete")/len(rs),total("complete"),len(rs),notes="All records valid, explicit missing codes allowed; required value cannot be missing")
        add(10,scope,total("grounded_ok")/total("grounded_n") if total("grounded_n") else None,total("grounded_ok"),total("grounded_n"),notes="Deterministic: exact value string present in the source evidence returned by the tool for that locator; no LLM judge, so no judge calibration")
    # Mandatory scored aggregation: equal weight for the three agents, independent of output volume.
    agents=sorted({c["agent"] for c in index})
    for mid in (3,4,6,7,8,9,10):
        values=[r["value"] for r in metrics if r["metric_id"]=="M"+str(mid) and r["scope"] in agents and r["value"] is not None]
        add(mid,"macro_agents",sum(values)/len(values),status="measured_local" if mid!=4 else "local_locator_proxy",notes="Arithmetic mean across implemented agents; benchmark limitations apply")
    add(5,"surprise",status="awaiting_instructor",notes="Requires three instructor items and checked answer key")
    wf=workflow_eval(ROOT,process)
    (ROOT/"eval/workflow_results.json").write_text(json.dumps(wf,indent=2,ensure_ascii=False),encoding="utf-8")
    fault=[w for w in wf if w["fault"]]
    real=[w for w in wf if not w["synthetic"]]
    add(11,"end_to_end",sum(w["correct"] for w in wf)/len(wf),sum(w["correct"] for w in wf),len(wf),evidence_path="eval/workflow_results.json",
        notes=f"LangGraph supervisor runs reaching the expected terminal status and agent plan; real inputs {sum(w['correct'] for w in real)}/{len(real)}; fault injection handled: {'yes' if fault and all(w['correct'] for w in fault) else 'no'}; set LANGSMITH_TRACING=true to record traces")
    with (ROOT/"logs/automation_log.csv").open(encoding="utf-8",newline="") as f:
        logs=list(csv.DictReader(f))
    automated=sum(r["status"]=="complete" and int(r["manual_interventions"])==0 for r in logs)
    add(12,"end_to_end",automated/len(logs),automated,len(logs),evidence_path="logs/automation_log.csv",notes="All persisted attempts including partial/failure attempts; evaluated at report time")
    calls=sum(int(r["tool_calls"]) for r in logs); refs=sum(int(r["reference_calls"]) for r in logs)
    add(13,"end_to_end",(calls-refs)/calls if calls else None,calls-refs,calls,evidence_path="logs/automation_log.csv",notes="Reference calls declared for supported routes; retries="+str(sum(int(r["retries"]) for r in logs))+"; routing/validation not extractor calls")
    db=sqlite3.connect(ROOT/"db/agriagent.sqlite")
    count=db.execute("SELECT count(*) FROM observations").fetchone()[0]
    mandatory="source source_type agent run_id locator crop location period unit".split()
    complete=db.execute("SELECT count(*) FROM observations WHERE "+" AND ".join(f"{k} IS NOT NULL AND length(trim({k}))>0" for k in mandatory)).fetchone()[0]
    valid=db.execute("SELECT count(*) FROM observations WHERE validation_status='valid'").fetchone()[0]
    duplicated=db.execute("SELECT coalesce(sum(n),0) FROM (SELECT count(*) n FROM observations GROUP BY source,locator,crop,location,period,variable HAVING count(*)>1)").fetchone()[0]
    for mid,num,note in ((14,complete,"Explicit MISSING codes count as filled; not evidence of known values"),(15,valid,"Declared rules; no supplied LGD registry; location name accuracy unverified"),(16,duplicated,"Rows in duplicate natural-key groups / stored rows; insertion duplicates rejected, attempts retained")):
        add(mid,"end_to_end",num/count if count else None,num,count,evidence_path="db/dump/agriagent.sql",notes=note)
    db.close()
    add(17,"end_to_end",status="awaiting_instructor",notes="Evaluator randomly selects 3 database rows live")
    add(18,"end_to_end",status="blocked",notes="No model/adapter/training evidence; see adapter_comparison.csv")
    contamination=audit(ROOT)
    (ROOT/"eval/contamination_report.json").write_text(json.dumps(contamination,indent=2),encoding="utf-8")
    with (ROOT/"eval/phase2_metrics.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS); w.writeheader(); w.writerows(metrics)
    dump(ROOT/"db/agriagent.sqlite",ROOT/"db/dump")
    print(json.dumps(dict(cases=len(index),agents={k:len(v) for k,v in groups.items() if k in ("directory","scheme","statistics")},
         macro_f1=next(r["value"] for r in metrics if r["metric_id"]=="M3" and r["scope"]=="macro_agents"),
         metrics_rows=len(metrics),contamination=contamination),indent=2))

if __name__=="__main__":
    evaluate()
