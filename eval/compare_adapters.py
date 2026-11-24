"""Score externally produced predictions on exactly the same checked cases.
Does not train or load a model. Missing predictions yield blocked rows, never zeros.
"""
import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agriagent.pipeline import ROOT
from eval.matching import counts,f1
from eval.contamination import audit
from eval.heldout import LOCK, load_cases, verify_training

FIELDS=["condition","model_id","adapter_id","case_set_sha256","sample_count","tp","fp","fn","f1","delta_f1","status","failure","prediction_sha256","training_overlap_status"]

def score_predictions(path,index):
    predictions=json.loads(path.read_text(encoding="utf-8"))
    expected={c["case_id"] for c in index}
    if set(predictions)!=expected:
        raise ValueError("Predictions must contain every held-out case exactly; missing/extra case IDs")
    total=[0,0,0]; agents=defaultdict(lambda:[0,0,0])
    for c in index:
        ref=json.loads((ROOT/c["reference"]).read_text(encoding="utf-8"))["records"]
        values=predictions[c["case_id"]]
        if not isinstance(values,list): raise ValueError("Case predictions must be lists")
        ns=counts(values,ref)
        total=[a+b for a,b in zip(total,ns)]
        agents[c["agent"]]=[a+b for a,b in zip(agents[c["agent"]],ns)]
    return total,sum(f1(*ns) for ns in agents.values())/len(agents)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path); p.add_argument("--adapter",type=Path)
    p.add_argument("--run-dir", type=Path, help="Verify and score a complete training workflow export")
    p.add_argument("--model-id",default="not_supplied"); p.add_argument("--adapter-id",default="not_supplied")
    p.add_argument("--output",type=Path,default=ROOT/"output/m18/adapter_comparison.csv")
    args=p.parse_args()
    index_path=LOCK
    index=load_cases()
    verify_training(ROOT, index)
    attested = False
    if args.run_dir:
        work = args.run_dir.resolve(strict=True)
        meta = json.loads((work / "configuration.json").read_text(encoding="utf-8"))
        hashes = json.loads((work / "hashes.json").read_text(encoding="utf-8"))
        required = {"base.json", "adapter.json", "configuration.json", "training_log.json",
                    "base_trace.json", "adapter_trace.json", "adapter/adapter_model.safetensors",
                    "adapter/adapter_config.json"}
        if not required.issubset(hashes):
            raise ValueError("Incomplete training evidence")
        for name, expected_hash in hashes.items():
            artifact = (work / name).resolve(strict=True)
            if not artifact.is_relative_to(work) or hashlib.sha256(artifact.read_bytes()).hexdigest() != expected_hash:
                raise ValueError(f"Training artifact hash differs: {name}")
        if (meta["case_lock_sha256"] != hashlib.sha256(LOCK.read_bytes()).hexdigest()
                or meta["training_sha256"] != hashlib.sha256((ROOT / "data/train/examples.jsonl").read_bytes()).hexdigest()
                or meta["evaluation_cases"] != [case["case_id"] for case in index]):
            raise ValueError("Training export does not match the frozen cohort")
        args.base, args.adapter = work / "base.json", work / "adapter.json"
        args.model_id = meta["base"] + "@" + meta["revision"]
        args.adapter_id = hashes["adapter/adapter_model.safetensors"]
        attested = True
    # Include inputs and references in digest; changing a label changes comparison identity.
    digest=hashlib.sha256(index_path.read_bytes()+b"".join((ROOT/c["input"]).read_bytes()+(ROOT/c["reference"]).read_bytes() for c in index)).hexdigest()
    contamination=audit(ROOT)
    rows=[]
    for name,path in (("base",args.base),("adapter",args.adapter)):
        row=dict(condition=name,model_id=args.model_id,adapter_id=args.adapter_id if name=="adapter" else "none",case_set_sha256=digest,
                 sample_count=0,tp="",fp="",fn="",f1="",delta_f1="",status="blocked",failure="No supplied model weights, adapter, training data, or genuine prediction export",prediction_sha256="",training_overlap_status=contamination["status"])
        if path:
            try:
                if args.model_id=="not_supplied" or (name=="adapter" and args.adapter_id=="not_supplied"):
                    raise ValueError("Supply model and adapter identities")
                numbers,score=score_predictions(path,index)
                row.update(tp=numbers[0],fp=numbers[1],fn=numbers[2],f1=score,sample_count=len(index),
                           status="scored_workflow_export" if attested else "scored_external_predictions",
                           failure="" if attested else "Producer/model execution not attested by this script",
                           prediction_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            except (OSError,ValueError,KeyError,TypeError) as exc:
                row["failure"]=str(exc)
        rows.append(row)
    if all(isinstance(r["f1"],float) for r in rows): rows[1]["delta_f1"]=rows[1]["f1"]-rows[0]["f1"]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print(json.dumps({"conditions":[r["status"] for r in rows],"training":contamination},indent=2))

if __name__=="__main__": main()
