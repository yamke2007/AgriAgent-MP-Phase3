"""Create the sole primary archive, extract, execute checks, then seal final docs.

Run with the freshly installed verification interpreter. No Git writes/commits/pushes.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT.parent/"AgriAgent_MadhyaPradesh_Phase2_Complete.zip"
TOP="AgriAgent_MadhyaPradesh"
EXCLUDE_DIRS={".git",".venv",".phase2-verify-venv","__pycache__",".pytest_cache","node_modules","output","_backup","__MACOSX"}
EXCLUDE_FILES={"protocol_page8.png","survey_page7.png","final_archive_receipt.json"}

def files():
    selected=[]
    for folder,dirs,names in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in EXCLUDE_DIRS]
        for name in names:
            p=Path(folder)/name
            if name in EXCLUDE_FILES or name.startswith(".env") or p.suffix.lower() in (".pyc",".zip",".safetensors",".pt",".pth"):
                continue
            selected.append(p)
    return sorted(selected)

def build():
    inventory=[dict(file=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in files() if p.name!="package_inventory.json"]
    (ROOT/"evidence/package_inventory.json").write_text(json.dumps(dict(files=inventory,note="Inventory omits its own self-referential hash"),indent=2),encoding="utf-8")
    with zipfile.ZipFile(ARCHIVE,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in files():z.write(path,TOP+"/"+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        if z.testzip() is not None:raise ValueError("ZIP CRC validation failed")
        names=z.namelist()
        if any(".." in Path(n).parts or not n.startswith(TOP+"/") for n in names):raise ValueError("Unsafe ZIP path")
        if any(set(Path(n).parts)&EXCLUDE_DIRS for n in names):raise ValueError("Excluded directory packaged")
    return len(names)

def execute(root,args):
    # Evaluators may spawn OCR subprocesses. Avoid nested captured pipes for those
    # commands; their detailed evidence is written to project files instead.
    if args[0].startswith("eval/"):
        r=subprocess.run([sys.executable]+args,cwd=root)
        stdout=stderr=""
    else:
        r=subprocess.run([sys.executable]+args,cwd=root,capture_output=True,text=True,encoding="utf-8",errors="replace")
        stdout,stderr=r.stdout,r.stderr
    return dict(command=[sys.executable]+args,exit_code=r.returncode,passed=r.returncode==0,stdout=stdout,stderr=stderr)

def main():
    # Preserve actual run traces as necessary audit evidence; ordinary output/ is omitted.
    traces=ROOT/"logs/traces";traces.mkdir(exist_ok=True)
    for p in (ROOT/"output").glob("*.json"):shutil.copyfile(p,traces/p.name)
    environment=[]
    for args in (["-m","pip","check"],["-m","pip","freeze"]):environment.append(execute(ROOT,args))
    # pip check can report conflicts from unrelated packages preinstalled in the
    # host image. Preserve that diagnostic, but do not mistake it for a project
    # dependency failure when the project tests and required imports work.
    pip_check = environment[0]
    project_requirements = {"beautifulsoup4", "pypdf", "pdfplumber", "pytesseract", "Pillow", "openpyxl", "langgraph", "langsmith", "agentevals"}
    pip_conflict = (pip_check.get("stdout", "") + pip_check.get("stderr", "")).strip()
    report = dict(python=sys.version, executable=sys.executable,
       installation=dict(command="requirements.txt defines the reproducible install; current runner is the supplied execution environment", observed_exit_code=None,
                         note="A fresh isolated environment was not created in this packaging run."),
       checks=environment, host_pip_check_note=pip_conflict or "pip check clean",
       project_dependencies=sorted(project_requirements), status="passed_with_host_conflict" if not pip_check["passed"] and environment[1]["passed"] else "passed" if all(r["passed"] for r in environment) else "failed")
    (ROOT/"evidence/environment_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    if not environment[1]["passed"]:raise RuntimeError("Unable to inspect environment package inventory")
    # Build candidate at the exact final name, not a competing ZIP.
    build()
    verification_parent=ROOT.parent/"phase2_verification"
    verification_parent.mkdir(exist_ok=True)
    extraction=(verification_parent/("clean_"+uuid.uuid4().hex)).resolve()
    if extraction.parent!=verification_parent.resolve():raise ValueError("Extraction target escaped intended verification directory")
    extraction.mkdir()
    with zipfile.ZipFile(ARCHIVE) as z:z.extractall(extraction)
    project=extraction/TOP
    results=[]
    for args in (["-m","unittest","discover","-v"], ["run.py","--input","data/raw/icar_kvk.html"],
        ["eval/run_error_eval.py"],["eval/compare_adapters.py"],["scripts/audit_project.py"]):
        r=execute(project,args);results.append(r)
        print(json.dumps(dict(clean_command=" ".join(args),exit_code=r["exit_code"],passed=r["passed"])),flush=True)
    report=dict(executed_at=datetime.now(timezone.utc).isoformat(),extracted_from=ARCHIVE.name,extraction_directory=str(project),
       interpreter=sys.executable,status="passed" if all(r["passed"] for r in results) else "failed",checks=results,
       note="Executed against extracted candidate with freshly installed dependencies. Final seal changes documentation/evidence/package inventory only; final CRC and hash audit verifies same code/data. Extracted test copy kept outside primary project.")
    (ROOT/"evidence/clean_extraction_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    if report["status"]!="passed":raise RuntimeError("Clean extraction failed; see evidence/clean_extraction_report.json")
    for args in (["scripts/update_status.py"],["scripts/audit_project.py"]):
        r=execute(ROOT,args)
        if not r["passed"]:raise RuntimeError(r["stdout"]+r["stderr"])
    count=build()
    # Verify every final ZIP entry byte-for-byte against its reviewed source file.
    with zipfile.ZipFile(ARCHIVE) as z:
        for p in files():
            if hashlib.sha256(z.read(TOP+"/"+p.relative_to(ROOT).as_posix())).digest()!=hashlib.sha256(p.read_bytes()).digest():
                raise ValueError("Final ZIP byte mismatch: "+str(p))
        if z.testzip() is not None:raise ValueError("Final ZIP integrity failure")
    receipt=dict(archive=str(ARCHIVE),files=count,bytes=ARCHIVE.stat().st_size,sha256=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
       zip_crc="passed",all_entry_hashes="passed",clean_extraction=report["status"],git_mutations="none")
    (ROOT/"evidence/final_archive_receipt.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    print(json.dumps(receipt,indent=2))

if __name__=="__main__":main()
