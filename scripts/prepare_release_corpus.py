"""Retain original row numbers while selecting Madhya Pradesh production data."""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/production"
MANIFEST = ROOT / "data/manifest.csv"
CROPS = {"Gram", "Maize", "Rice", "Soyabean", "Wheat"}
FIRST_YEAR = 2016
LAST_YEAR = 2022


def extend_manifest(report):
    with MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        columns = reader.fieldnames
    known = {row["file"] for row in rows}
    new = []
    for name, key, transformation in (
        ("mp_crop_production_2016_2022.csv", "production", "state, crop and year subset; original CSV line retained"),
        ("mp_districts.geojson", "boundary", "server-filtered MP polygons in EPSG:4326"),
    ):
        path = TARGET / name
        meta = report[key]
        new.append(dict(
            file=path.relative_to(ROOT).as_posix(), source="S11-OGD" if key == "production" else "SOI",
            url=meta["retrieval_url"], collection_date=report["retrieved"], language="en",
            license=meta["license_status"], sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            bytes=path.stat().st_size, parent_file=meta["retrieval_url"], transformation=transformation,
            split="production",
        ))
    training = ROOT / "data/train/examples.jsonl"
    for line in training.read_text(encoding="utf-8").splitlines():
        example = json.loads(line)
        path = ROOT / example["source"]
        url = "https://raw.githubusercontent.com/iancovert/Agmarknet/master/" + example["parent"]
        new.append(dict(
            file=example["source"], source="Agmarknet archive", url=url,
            collection_date="unknown (historical acquisition)", language="en",
            license="Publisher terms unverified; academic-use evidence", sha256=example["sha256"],
            bytes=path.stat().st_size, parent_file=url,
            transformation="Selected original CSV lines; archive header restored", split="training",
        ))
    new.append(dict(
        file=training.relative_to(ROOT).as_posix(), source="Agmarknet archive",
        url="https://github.com/iancovert/Agmarknet", collection_date="unknown (historical acquisition)",
        language="en", license="Publisher terms unverified; academic-use evidence",
        sha256=hashlib.sha256(training.read_bytes()).hexdigest(), bytes=training.stat().st_size,
        parent_file="data/train/raw", transformation="Prompt and deterministic cell transcription",
        split="training",
    ))
    for row in new:
        if row["file"] in known:
            previous = next(old for old in rows if old["file"] == row["file"])
            if previous["sha256"] != row["sha256"]:
                raise ValueError(f"Manifest conflict for {row['file']}; retain the previous version")
    pending = [row for row in new if row["file"] not in known]
    if pending:
        with MANIFEST.open("a", encoding="utf-8", newline="") as stream:
            csv.DictWriter(stream, columns).writerows(pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition", type=Path, default=ROOT / "output/acquisition")
    parser.add_argument("--date", required=True, help="Actual local retrieval date, YYYY-MM-DD")
    args = parser.parse_args()
    source = args.acquisition / "crop_production.csv"
    boundary = args.acquisition / "districts.geojson"
    urls = json.loads((args.acquisition / "urls.json").read_text(encoding="utf-8"))
    geometry = json.loads(boundary.read_text(encoding="utf-8"))
    if not geometry.get("features") or any(
        feature["properties"]["state"].casefold() != "madhya pradesh"
        for feature in geometry["features"]
    ):
        raise ValueError("Expected a Madhya Pradesh district FeatureCollection")
    TARGET.mkdir(parents=True, exist_ok=True)
    with source.open(encoding="utf-8-sig", newline="") as raw:
        reader = csv.DictReader(raw)
        rows = [
            dict(row, Original_Row=reader.line_num)
            for row in reader
            if row["State_Name"] == "Madhya Pradesh"
            and row["Crop"] in CROPS
            and FIRST_YEAR <= int(row["Crop_Year"]) <= LAST_YEAR
        ]
        columns = reader.fieldnames
    if not rows:
        raise ValueError("No selected source rows")
    if any((TARGET / filename).exists() for filename in (
        "mp_crop_production_2016_2022.csv", "mp_districts.geojson", "sources.json",
    )):
        parser.error("Release corpus already exists. Retain it before preparing a new version.")
    with (TARGET / "mp_crop_production_2016_2022.csv").open(
        "x", encoding="utf-8", newline=""
    ) as out:
        writer = csv.DictWriter(out, [*columns, "Original_Row"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    shutil.copyfile(boundary, TARGET / "mp_districts.geojson")
    report = {
        "retrieved": args.date,
        "production": {
            "catalog": "https://www.data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997",
            "retrieval_url": urls["production"],
            "parent_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "selected_rows": len(rows),
            "license_status": "OGD catalog lists Government Open Data License India. Mirror byte identity with the portal export is unverified.",
        },
        "boundary": {
            "retrieval_url": urls["boundary"], "provider": "Survey of India via Esri India",
            "vintage": "Published service last edited April 2021", "districts": len(geometry["features"]),
            "license_status": "Copyright Survey of India. Public query access; redistribution terms unverified.",
        },
    }
    (TARGET / "sources.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    extend_manifest(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
