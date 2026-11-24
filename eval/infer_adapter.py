"""Optional local model runner. No downloads or training; never reads reference values."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agriagent.model import MAX_GENERATION, load_local, predict
from eval.heldout import load_cases

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True,type=Path)
    p.add_argument("--adapter",type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--max-new-tokens",type=int,default=MAX_GENERATION)
    a=p.parse_args()
    missing=[m for m in ("torch","transformers")+( ("peft",) if a.adapter else ()) if importlib.util.find_spec(m) is None]
    reasons=[]
    if missing: reasons.append("Missing packages: "+", ".join(missing))
    if not a.model.is_dir():reasons.append("Local base model directory unavailable")
    if a.adapter and not (a.adapter/"adapter_config.json").is_file():reasons.append("Local PEFT adapter_config.json unavailable")
    if reasons:
        print(json.dumps(dict(status="blocked",reasons=reasons)));return 2
    from eval.heldout import ROOT
    index=load_cases()
    if a.output.exists() or a.output.with_suffix(".metadata.json").exists():
        p.error("Choose a new output file to retain prior inference evidence")
    model, tokenizer = load_local(str(a.model.resolve()), str(a.adapter.resolve()) if a.adapter else None)
    predictions={}; failures=[]; usage={}
    for c in index:
        try:
            records, usage[c["case_id"]] = predict(model, tokenizer, ROOT/c["input"], a.max_new_tokens)
            predictions[c["case_id"]]=records
        except Exception as exc:
            predictions[c["case_id"]]=[];failures.append(dict(case_id=c["case_id"],error=str(exc)))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(predictions,ensure_ascii=False,indent=2),encoding="utf-8")
    a.output.with_suffix(".metadata.json").write_text(json.dumps(dict(model=str(a.model),adapter=str(a.adapter),device="cpu",do_sample=False,max_new_tokens=a.max_new_tokens,failures=failures,token_usage=usage,training="not_performed",case_count=len(index)),indent=2),encoding="utf-8")
    print(json.dumps(dict(status="executed",cases=len(index),failures=len(failures))))
    return 0

if __name__=="__main__":raise SystemExit(main())
