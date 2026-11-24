"""Verify real-source CSV, XLSX, HTML and PDF paths without mixing their data into SQLite."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import openpyxl
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.normalization import crop, location, text
from agriagent.pipeline import process
from eval.matching import counts


def xlsx_example(parent, output):
    sources = json.loads((ROOT / "data/production/sources.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(parent.read_bytes()).hexdigest()
    if digest != sources["production"]["parent_sha256"]:
        raise ValueError("Original crop production export does not match its recorded hash")
    path = output / "mp_real_values_2015.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Wheat APY"
    sheet.append(["State", "District", "Year", "Crop", "Area (Hectare)", "Production (Tonnes)"])
    rows = []
    with parent.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            if (row["State_Name"], row["Crop_Year"], row["Crop"]) != ("Madhya Pradesh", "2015", "Wheat"):
                continue
            if not row["Area"] or not row["Production"]:
                continue
            sheet.append([row["State_Name"], row["District_Name"], row["Crop_Year"], row["Crop"],
                          float(row["Area"]), float(row["Production"])])
            rows.append((reader.line_num, row))
            if len(rows) == 5:
                break
    if len(rows) != 5:
        raise ValueError("Expected five real original APY rows")
    workbook.save(path)
    references = [dict(crop=crop(row["Crop"]), location=location(row["District_Name"]), period="2015",
                       variable=variable, value=row[column], unit=unit, value_kind="decimal")
                  for _, row in rows for variable, column, unit in
                  (("area", "Area", "hectare"), ("production", "Production", "tonne"))]
    return path, references, [line for line, _ in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, default=ROOT / "output/acquisition/crop_production.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "output/formats")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error("Choose an empty output directory")
    workbook, reference, rows = xlsx_example(args.parent, output)
    report = []
    for path in (
        ROOT / "data/production/mp_crop_production_2016_2022.csv", workbook,
        ROOT / "data/raw/msp_scheme.html", ROOT / "data/raw/mp_economic_survey.pdf",
        ROOT / "data/raw/e_mandi_manual.pdf",
    ):
        result = process(path, persist=False)
        entry = {key: result[key] for key in ("input", "status", "trajectory", "warnings", "errors")}
        entry["records"] = len(result["records"])
        if path == workbook:
            tp, fp, fn = counts(result["records"], reference)
            entry.update(verified=tp == 10 and fp == fn == 0, tp=tp, fp=fp, fn=fn, original_csv_lines=rows,
                         note="Workbook re-encoded from exact real 2015 source cells; scripted comparison")
        elif path.suffix == ".pdf":
            reader = PdfReader(path)
            checks = []
            for record in result["records"]:
                parts = record["locator"].split("/")
                if len(parts) == 2 and parts[0].startswith("page:") and parts[1].startswith("char:"):
                    source_page = int(parts[0].split(":")[1])
                    start, end = map(int, parts[1].split(":")[1].split("-"))
                    value_at_location = text(reader.pages[source_page - 1].extract_text())[start:end]
                    if record["variable"] == "production":
                        supported = value_at_location == "produced 352.7 lakh tonnes of wheat in 2022-23"
                    else:
                        supported = value_at_location == record["value"]
                    checks.append(dict(variable=record["variable"], page=source_page, supported=supported))
            entry.update(verified=bool(checks) and all(check["supported"] for check in checks), source_checks=checks)
        else:
            entry["verified"] = bool(result["records"]) and result["status"] != "failed"
        report.append(entry)
    with (output / "format_checks.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print([(row["input"], row["status"], row["records"], row["verified"]) for row in report])
    return int(not all(row["verified"] for row in report))


if __name__ == "__main__":
    raise SystemExit(main())
