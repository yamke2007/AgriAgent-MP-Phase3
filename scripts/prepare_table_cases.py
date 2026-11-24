"""Build evaluation cases for the tables agent from REAL Agmarknet price records.

Source: Agmarknet daily wholesale prices (Directorate of Marketing & Inspection,
Government of India, agmarknet.gov.in), as archived in the public GitHub
repository iancovert/Agmarknet (downloaded from agmarknet.gov.in in June 2017;
one CSV per crop and year, no header row). This is a non-portal, openly
reachable copy of the same official records behind S03/S18/S19 mandi prices.

Each case = header line (Agmarknet's own column names, restored from the
repository README) + 4 unmodified source lines: Madhya Pradesh markets on one
reported date, one market per district. The reference is written by THIS
script from the raw cells with plain string handling. It does not import or
call the pipeline, so labels are not the agent's own output.

    python scripts/prepare_table_cases.py            # writes eval/cases/tables_*.csv + eval/reference/tables_*.json
Parent files are cached outside the repo (~/.cache/agriagent_agmarknet) and
identified by URL + sha256 in eval/case_index.json and data/manifest.csv.
A team member must still check every reference against the source lines
("checked" field) before the protocol counts the case.
"""
import csv
import hashlib
import io
import json
import random
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://raw.githubusercontent.com/iancovert/Agmarknet/master"
HEADER = ["State Name", "District Name", "Market Name", "Variety", "Group", "Arrivals (Tonnes)",
          "Min Price (Rs./Quintal)", "Max Price (Rs./Quintal)", "Modal Price (Rs./Quintal)", "Reported Date"]
CROP = {"Soyabean": "soybean", "Wheat": "wheat", "Maize": "maize"}
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
# tables_01-12 "development": run while building the agent (they exposed one bug, fixed in tables.py).
# tables_13-22 "heldout": generated afterwards from crop-years never used during development, scored once.
PLAN = [("Soyabean", 2012, 0, "development"), ("Soyabean", 2014, 0, "development"), ("Soyabean", 2015, 0, "development"),
        ("Soyabean", 2016, 0, "development"), ("Soyabean", 2016, 1, "development"), ("Wheat", 2012, 0, "development"),
        ("Wheat", 2014, 0, "development"), ("Wheat", 2015, 0, "development"), ("Wheat", 2015, 1, "development"),
        ("Maize", 2012, 0, "development"), ("Maize", 2014, 0, "development"), ("Maize", 2015, 0, "development"),
        ("Soyabean", 2011, 0, "heldout"), ("Soyabean", 2013, 0, "heldout"), ("Soyabean", 2017, 0, "heldout"),
        ("Wheat", 2011, 0, "heldout"), ("Wheat", 2013, 0, "heldout"), ("Wheat", 2013, 1, "heldout"), ("Wheat", 2017, 0, "heldout"),
        ("Maize", 2011, 0, "heldout"), ("Maize", 2013, 0, "heldout"), ("Maize", 2017, 0, "heldout")]
CACHE = Path.home() / ".cache" / "agriagent_agmarknet"


def parent(crop, year):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{crop}_{year}.csv"
    if not p.exists():
        with urllib.request.urlopen(f"{REPO}/{crop}/{year}.csv", timeout=120) as r:
            p.write_bytes(r.read())
    return p


def iso(d):
    day, mon, year = d.split()
    return f"{int(year):04d}-{MONTHS[mon]:02d}-{int(day):02d}"


def num(s):
    return s.replace(",", "")


def main():
    index = json.loads((ROOT / "eval/case_index.json").read_text(encoding="utf-8"))
    index = [c for c in index if c["agent"] != "tables"]
    manifest_rows = []
    for k, (crop, year, pick, split) in enumerate(PLAN, 1):
        src = parent(crop, year)
        raw_lines = src.read_text(encoding="utf-8").splitlines()
        by_date = defaultdict(dict)  # date -> district -> raw line (first market per district)
        for line in raw_lines:
            row = next(csv.reader([line]))
            if len(row) != 10 or row[0] != "Madhya Pradesh" or not all(row[6:9]):
                continue
            by_date[row[9]].setdefault(row[1], line)
        dates = sorted(d for d, v in by_date.items() if len(v) >= 4)
        rng = random.Random(f"{crop}-{year}-{pick}")
        date = rng.choice(dates)
        districts = sorted(by_date[date])[:4] if pick == 0 else sorted(by_date[date])[-4:]
        lines = [by_date[date][d] for d in districts]
        case_id = f"tables_{k:02d}"
        name = f"{case_id}_agmarknet_{crop.lower()}_{year}.csv"
        body = io.StringIO()
        csv.writer(body, lineterminator="\n").writerow(HEADER)
        text = body.getvalue() + "\n".join(lines) + "\n"
        (ROOT / "eval/cases" / name).write_text(text, encoding="utf-8")
        records = []
        for line in lines:
            r = next(csv.reader([line]))
            common = dict(crop=CROP[crop], location=r[1].strip().casefold(), period=iso(r[9]))
            records.append(dict(common, variable="arrivals", value=num(r[5]), unit="tonne",
                                value_kind="decimal" if "." in r[5] else "integer"))
            for var, cell in (("min_price", r[6]), ("max_price", r[7]), ("modal_price", r[8])):
                records.append(dict(common, variable=var, value=num(cell), unit="INR/quintal",
                                    value_kind="decimal" if "." in cell else "integer"))
        input_path = ROOT / "eval/cases" / name
        entry = dict(case_id=case_id, input=f"eval/cases/{name}", reference=f"eval/reference/{case_id}.json",
                     agent="tables", source_group="Database", language="en", split=split,
                     checked="drafted_from_source_lines_by_script_needs_team_check",
                     source=f"{REPO}/{crop}/{year}.csv", source_locator=f"Madhya Pradesh rows dated {r[9]}",
                     input_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
                     parent_sha256=hashlib.sha256(src.read_bytes()).hexdigest(), parent_remote=True,
                     benchmark_limit="real Agmarknet records (official DMI data via public GitHub archive); row extract with restored header; not seen during agent development")
        (ROOT / "eval/reference" / f"{case_id}.json").write_text(json.dumps(
            dict(records=records, evidence=dict(entry, source_lines=lines)), ensure_ascii=False, indent=2), encoding="utf-8")
        index.append(entry)
        manifest_rows.append(dict(file=entry["input"], source="S03/S18/S19 (Agmarknet)", url=entry["source"],
                                  collection_date="2026-10-25", language="en",
                                  license="not stated by archive; Govt of India Agmarknet data; academic use, flagged",
                                  sha256=entry["input_sha256"], bytes=input_path.stat().st_size, parent_file=entry["source"],
                                  transformation="4 unmodified source lines + header restored from Agmarknet column names",
                                  split="evaluation_" + split))
        print(case_id, crop, year, date, districts)
    (ROOT / "eval/case_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    man = ROOT / "data/manifest.csv"
    with man.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if not r["file"].startswith("eval/cases/tables_")]
        fields = list(rows[0].keys())
    rows += [{k: m.get(k, "") for k in fields} for m in manifest_rows]
    with man.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
