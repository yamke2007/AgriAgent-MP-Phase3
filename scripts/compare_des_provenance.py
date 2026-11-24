"""Corroborate the preserved crop snapshot against direct official DES exports."""
import argparse
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.normalization import crop, location


def run_records(output, sample):
    path = next(row["run_id"] for row in output if row["input"].endswith(sample))
    return path


def load_run(directory, report, basename):
    run = run_records(report["cases"], basename)
    return json.loads((directory / "runs" / f"{run}.json").read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((args.run / "report.json").read_text(encoding="utf-8"))
    direct = load_run(args.run, report, "S11_wheat_rabi_2022.pdf")
    rank = load_run(args.run, report, "S12_major_report.pdf")
    summer = [load_run(args.run, report, f"S11_summer_2019_{c}.pdf") for c in ("rice", "maize")]
    path = ROOT / "data/production/mp_crop_production_2016_2022.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        old = list(csv.DictReader(stream))
    official = {(row["location"], row["variable"]): row for row in direct["records"]}
    paired = []
    for row in old:
        if (row["Crop_Year"], row["Crop"], row["Season"]) != ("2022", "Wheat", "Rabi"):
            continue
        name = location(row["District_Name"])
        for field in ("area", "production"):
            found = official.get((name, field))
            equal = bool(found and Decimal(found["value"]) == Decimal(row[field.title()]))
            paired.append(dict(district=name, field=field, matched=equal, original_csv_line=row["Original_Row"],
                               des_locator=found["locator"] if found else None))
    published_rank = [row for row in rank["records"] if row["variable"] == "production"]
    rank_checked = [
        dict(district=row["location"], matched=bool(
            (reference := official.get((row["location"], "production")))
            and Decimal(row["value"]) == Decimal(reference["value"])
        )) for row in published_rank
    ]

    summer_index = {
        (row["crop"], row["location"], row["variable"]): row for run in summer for row in run["records"]
    }
    missing = []
    for old_row in old:
        if old_row["Production"]:
            continue
        commodity, district = crop(old_row["Crop"]), location(old_row["District_Name"])
        address = (commodity, district)
        area = summer_index.get((*address, "area"))
        production = summer_index.get((*address, "production"))
        missing.append(dict(
            district=district, crop=commodity, year=old_row["Crop_Year"], season=old_row["Season"],
            original_csv_line=old_row["Original_Row"],
            direct_des_area_locator=area["locator"] if area else None,
            direct_des_area_value=area["value"] if area else None,
            direct_des_production_value=production["value"] if production else None,
            direct_report_production_cell_blank=bool(area and not production),
        ))
    evidence = {
        "wheat_matched_cells": sum(x["matched"] for x in paired), "wheat_checked_cells": len(paired),
        "ranking_matched_production_rows": sum(x["matched"] for x in rank_checked),
        "ranking_checked_rows": len(rank_checked),
        "release_missing_production_cells": len(missing),
        "same_cells_blank_in_direct_des": sum(x["direct_report_production_cell_blank"] for x in missing),
        "paired": paired, "ranking": rank_checked, "missing": missing,
        "official_reports": [{"input": run["input"], "sha256": run["input_sha256"], "source_url": run["source_url"]}
                             for run in (direct, rank, *summer)],
        "limitations": "Wheat comparison covers the 2022-23 Rabi sample. Summer verification covers identified production blanks. Neither proves the bulk mirror's full byte identity.",
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, indent=2, ensure_ascii=False)
    print(json.dumps({key: value for key, value in evidence.items() if isinstance(value, int)}))


if __name__ == "__main__":
    main()
