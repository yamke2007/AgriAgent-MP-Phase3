"""Audit LGD district joins on the existing database and published geometry read-only."""
import argparse
import hashlib
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.normalization import location
from scripts.import_lgd import registry_from_csv


def audit(registry, db, geometry):
    valid = {location(label): code for code, label in registry.items()}
    if len(valid) != len(registry):
        raise ValueError("Ambiguous normalized LGD registry")
    with closing(sqlite3.connect(db.resolve(strict=True).as_uri() + "?mode=ro", uri=True)) as conn:
        panel = dict(conn.execute("SELECT district, count(*) FROM district_crop_production GROUP BY district"))
    names = {location(feature["properties"]["district"]) for feature in
             json.loads(geometry.read_text(encoding="utf-8"))["features"]}
    return {
        "registry_districts": len(valid),
        "release_districts_matched": len(set(panel) & valid.keys()),
        "release_districts_total": len(panel),
        "release_panel_rows_matched": sum(count for district, count in panel.items() if district in valid),
        "release_panel_rows_total": sum(panel.values()),
        "release_unmatched": sorted(panel.keys() - valid.keys()),
        "geometry_matched": len(names & valid.keys()),
        "geometry_total": len(names),
        "geometry_unmatched": sorted(names - valid.keys()),
        "registry_districts_outside_historical_geometry": sorted(valid.keys() - names),
        "limitation": "Current code lookup by documented name aliases; no inference about historical boundary changes",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--db", type=Path, default=ROOT / "output/release/agriagent.sqlite")
    parser.add_argument("--geometry", type=Path, default=ROOT / "data/production/mp_districts.geojson")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mp-only-export", action="store_true")
    args = parser.parse_args()
    registry = registry_from_csv(args.registry, scoped_mp=args.mp_only_export)
    report = audit(registry, args.db, args.geometry)
    report.update(source_url=args.source_url, input_sha256=hashlib.sha256(args.registry.read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
