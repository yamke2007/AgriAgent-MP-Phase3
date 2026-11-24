import argparse
import json
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from agriagent.pipeline import ROOT
from agriagent.storage import dump

def main():
    p=argparse.ArgumentParser(); p.add_argument("--id",type=int);p.add_argument("--dump",action="store_true")
    p.add_argument("--database", type=Path, default=ROOT/"db/agriagent.sqlite")
    p.add_argument("--dump-dir", type=Path, default=ROOT/"output/db-backup")
    a=p.parse_args()
    path=a.database.resolve(strict=True)
    if a.dump:
        if a.dump_dir.exists() and any(a.dump_dir.iterdir()):
            p.error("Choose an empty dump directory")
        dump(path,a.dump_dir); print("Dump exported"); return
    db=sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)
    sql="SELECT id,payload FROM observations WHERE id=?" if a.id else "SELECT id,payload FROM observations ORDER BY id LIMIT 3"
    rows=db.execute(sql,(a.id,) if a.id else ()).fetchall()
    for identity,payload in rows:
        r=json.loads(payload)
        src=db.execute("SELECT url,input_path,file_sha256 FROM sources WHERE source=?",(r["source"],)).fetchone()
        print(json.dumps(dict(id=identity,observation=r,source_url=src[0],input_path=src[1],sha256=src[2]),ensure_ascii=True,indent=2))
    db.close()

if __name__=="__main__":main()
