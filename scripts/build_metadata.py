import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def csv_write(path,rows,fields=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    with (ROOT/"Source_Inventory/source_inventory.csv").open(encoding="utf-8-sig",newline="") as f:
        inventory=list(csv.DictReader(f))
    assignments={1:"fertilizer",2:"fertilizer",3:"market",4:"market",5:"procurement",6:"scheme",7:"service_directory",8:"machinery",9:"machinery",10:"advisory",11:"statistics",12:"statistics",13:"statistics",14:"scheme",15:"insurance",16:"scheme",17:"excluded_personal",18:"market",19:"market",20:"scheme",21:"directory",22:"directory",23:"statistics"}
    limitations={6:"Hindi HTML table operational; empty fields explicit; no procurement quantities",21:"All 54 rows processed; historical spellings retained; freshness/LGD unverified",23:"One production sentence extracted from PDF; full tables pending; manual transcription importer tested"}
    rows=[]
    for i,r in enumerate(inventory,1):
        rows.append(dict(source_id=f"S{i:02}",source_name=r["Source Name"],url=r["URL"],agent=assignments[i],status="partial" if i in limitations else "pending",reason=limitations.get(i,"Excluded person-level lookup per TA scope" if i==17 else "No source-specific operational extraction demonstrated; metadata/index/template access is insufficient")))
    csv_write(ROOT/"docs/source_agent_map.csv",rows)
    urls={"icar_kvk.html":("S21","https://icar.org.in/en/node/15044","en"),
          "msp_scheme.html":("S06","https://cmhelpline.mp.gov.in/Schmedetail.aspx?Schemeid=112","hi"),
          "mp_economic_survey.pdf":("S23","https://aiggpa.mp.gov.in/uploads/project/MPES_2022-23_Highlights_English.pdf","en"),
          "e_mandi_manual.pdf":("S04","https://eanugya.mp.gov.in/HR/Doc/User_ManualForMandiSecretary.pdf","hi/en"),
          "evikas_calculator.html":("S02","https://evikas.mpkrishi.mp.gov.in/OFRDHome/FarmerFertilizer_Calculator","hi"),
          "des_apy.html":("S11","https://data.desagri.gov.in/website/apy-query-report-web","en")}
    index=json.loads((ROOT/"eval/case_index.json").read_text(encoding="utf-8"))
    by_file={c["input"]:c for c in index}
    manifest=[]
    paths=list((ROOT/"data/raw").glob("*"))+list((ROOT/"data/derived").glob("*"))+list((ROOT/"eval/cases").glob("*"))
    for path in sorted(paths):
        if not path.is_file(): continue
        relative=path.relative_to(ROOT).as_posix()
        case=by_file.get(relative)
        original=Path(case["source"]).name if case else "mp_economic_survey.pdf" if "derived" in relative else path.name
        source,url,lang=urls[original]
        parent=case["source"] if case else "data/raw/mp_economic_survey.pdf" if "derived" in relative else ""
        manifest.append(dict(file=relative,source=source,url=url,collection_date="2026-10-25",language=case["language"] if case else lang,
            license="not verified",sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,parent_file=parent,
            transformation="source-derived benchmark fragment" if case else "manual transcription of page 7; reviewed against source text" if parent else "downloaded source snapshot",
            split="evaluation_development_visible" if case else "source_development_visible"))
    csv_write(ROOT/"data/manifest.csv",manifest)
    tracked=subprocess.check_output(["git","ls-tree","-r","--name-only","496bbf6"],cwd=ROOT,text=True).splitlines()
    baseline=[]
    for name in tracked:
        blob=subprocess.check_output(["git","show","496bbf6:"+name],cwd=ROOT)
        preserved="docs/Phase1/README_original.md" if name=="README.md" else name
        working=(ROOT/preserved).read_bytes()
        if working.replace(b"\r\n",b"\n") != blob.replace(b"\r\n",b"\n"):
            raise ValueError("Phase 1 content changed: "+name)
        baseline.append(dict(original=name,preserved=preserved,sha256=hashlib.sha256(working).hexdigest(),git_blob_sha256=hashlib.sha256(blob).hexdigest(),note="Git core.autocrlf checkout line endings retained"))
    (ROOT/"evidence/phase1_baseline.json").write_text(json.dumps(baseline,indent=2),encoding="utf-8")
    print("Source map:",len(rows),"Manifest:",len(manifest),"Baseline files:",len(baseline))

if __name__=="__main__":main()
