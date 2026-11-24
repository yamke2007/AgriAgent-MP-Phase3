"""Explicit corpus refresh; TLS verification stays enabled; never overwrites by default."""
import argparse
import csv
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES={"icar_kvk.html":"https://icar.org.in/en/node/15044",
 "msp_scheme.html":"https://cmhelpline.mp.gov.in/Schmedetail.aspx?Schemeid=112",
 "mp_economic_survey.pdf":"https://aiggpa.mp.gov.in/uploads/project/MPES_2022-23_Highlights_English.pdf",
 "e_mandi_manual.pdf":"https://eanugya.mp.gov.in/HR/Doc/User_ManualForMandiSecretary.pdf",
 "evikas_calculator.html":"https://evikas.mpkrishi.mp.gov.in/OFRDHome/FarmerFertilizer_Calculator",
 "des_apy.html":"https://data.desagri.gov.in/website/apy-query-report-web"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--replace",action="store_true");a=p.parse_args()
    rows=[]
    for name,url in SOURCES.items():
        dest=ROOT/"data/raw"/name
        if dest.exists() and not a.replace:
            print("Preserved:",name);continue
        with tempfile.TemporaryDirectory() as d:
            temp=Path(d)/name
            result=subprocess.run(["curl","--fail","--location","--silent","--show-error","--max-time","40","--output",str(temp),url],capture_output=True,text=True)
            row=dict(attempted_at=datetime.now(timezone.utc).isoformat(),file="data/raw/"+name,url=url,status="failed",sha256="",error=result.stderr)
            if result.returncode==0 and temp.is_file():
                content=temp.read_bytes()
                if name.endswith(".pdf") and not content.startswith(b"%PDF"):
                    row["error"]="Response not PDF; no file replaced"
                else:
                    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
                    row.update(status="downloaded",sha256=hashlib.sha256(content).hexdigest())
            rows.append(row)
    if rows:
        log=ROOT/"logs/acquisition_attempts.csv";exists=log.exists()
        with log.open("a",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]))
            if not exists:w.writeheader()
            w.writerows(rows)
    print(json.dumps(rows,indent=2))

if __name__=="__main__":main()
