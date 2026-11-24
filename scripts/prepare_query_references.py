"""Compute expected query answers directly from source rows without SQLite."""
import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from itertools import groupby
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.normalization import crop, location

FILE = "data/production/mp_crop_production_2016_2022.csv"
SURVEY = "data/derived/survey_agriculture_transcription.csv"


def expected(raw_parent):
    local = ROOT / FILE
    sources = json.loads((local.parent / "sources.json").read_text(encoding="utf-8"))
    parent = sources["production"]
    if hashlib.sha256(raw_parent.read_bytes()).hexdigest() != parent["parent_sha256"]:
        raise ValueError("Original source hash differs")
    with local.open(encoding="utf-8", newline="") as stream:
        subset = list(csv.DictReader(stream))
    origin = {int(row["Original_Row"]): row for row in subset}
    if len(origin) != len(subset):
        raise ValueError("Duplicate original row")
    with raw_parent.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        checked = 0
        for original in reader:
            current = origin.get(reader.line_num)
            if current:
                if any(current[key] != value for key, value in original.items()):
                    raise ValueError(f"Original row mismatch at line {reader.line_num}")
                checked += 1
        if checked != len(subset):
            raise ValueError("Some selected rows could not be verified against the parent")
    usable = []
    for line, row in enumerate(subset, 2):
        if not all(row[key] for key in ("Area", "Production")):
            continue
        usable.append({
            "district": location(row["District_Name"]), "year": int(row["Crop_Year"]),
            "crop": crop(row["Crop"]), "season": row["Season"].strip().casefold(),
            "hectares": float(row["Area"]), "tonnes": float(row["Production"]),
            "local_line": line, "original_line": int(row["Original_Row"]),
        })
    wheat = [row for row in usable if row["crop"] == "wheat" and row["season"] == "rabi"]
    latest = [row for row in usable if row["year"] == 2022]
    soy = [row for row in latest if row["crop"] == "soybean" and row["season"] == "kharif" and row["hectares"] > 0]
    kharif = [row for row in latest if row["season"] == "kharif" and row["hectares"] > 0]
    sehore = sorted((row for row in wheat if row["district"] == "sehore"), key=lambda row: row["year"])
    selected, = [row for row in sehore if row["year"] == 2022]

    def yield_of(row):
        return row["tonnes"] / row["hectares"]

    def by_year(row):
        return row["year"]

    def by_crop(row):
        return row["crop"]

    changes = []
    before = {row["district"]: row for row in wheat if row["year"] == 2016}
    for row in wheat:
        if row["year"] == 2022 and row["district"] in before:
            changes.append((row["tonnes"] - before[row["district"]]["tonnes"], row["district"]))
    maize = {row["district"]: yield_of(row) for row in kharif if row["crop"] == "maize"}
    paired = [maize[row["district"]] > yield_of(row) for row in soy if row["district"] in maize]
    coverage = defaultdict(set)
    for row in usable:
        coverage[row["crop"], row["year"]].add(row["district"])
    with (ROOT / SURVEY).open(encoding="utf-8", newline="") as stream:
        survey = [
            {"crop": row["crop"], "period": row["period"], "lakh_tonnes": float(row["value"]),
             "pdf": row["origin_source"], "page": row["origin_locator"]}
            for row in csv.DictReader(stream) if row["variable"] == "production"
        ]
    return {
        "q01": [
            {"district": row["district"], "tonnes": round(row["tonnes"], 2)}
            for row in sorted(
                (row for row in wheat if row["year"] == 2022),
                key=lambda row: (-round(row["tonnes"], 2), row["district"]),
            )[:5]
        ],
        "q02": [
            {"district": row["district"], "tonnes_per_ha": round(yield_of(row), 3)}
            for row in sorted(soy, key=lambda row: (-yield_of(row), row["district"]))[:5]
        ],
        "q03": [
            {"year": year, "tonnes": round(sum(row["tonnes"] for row in rows), 2), "districts": len(rows)}
            for year, group in groupby(sorted(wheat, key=by_year), key=by_year) if (rows := list(group))
        ],
        "q04": [{"year": row["year"], "tonnes_per_ha": round(yield_of(row), 3)} for row in sehore],
        "q05": [{
            "district": "sehore", "year": 2022, "tonnes": selected["tonnes"],
            "source_url": parent["retrieval_url"], "local_snapshot": FILE,
            "original_locator": f"csv:line:{selected['original_line']}/column:Production",
            "local_locator": f"csv:line:{selected['local_line']}/column:Production",
            "file_sha256": hashlib.sha256(local.read_bytes()).hexdigest(),
        }],
        "q06": [
            {"crop": name, "tonnes_per_ha": round(sum(row["tonnes"] for row in rows) /
             sum(row["hectares"] for row in rows), 3), "districts": len(rows)}
            for name, group in groupby(sorted(kharif, key=by_crop), key=by_crop) if (rows := list(group))
        ],
        "q07": [{"district": district, "change_tonnes": round(change, 2)}
                for change, district in sorted(changes, key=lambda entry: (-entry[0], entry[1]))[:5]],
        "q08": [{"maize_higher": sum(paired), "paired_districts": len(paired)}],
        "q09": [{"crop": name, "year": year, "districts": len(districts)}
                for (name, year), districts in sorted(coverage.items())],
        "q10": sorted(survey, key=lambda row: (row["crop"], row["period"])),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, default=ROOT / "output/acquisition/crop_production.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "db/queries_expected.json")
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(expected(args.parent), stream, indent=2)
        stream.write("\n")
