"""Generate reproducible district-level analysis, charts and maps."""
import argparse
import json
import sqlite3
from collections import defaultdict
from contextlib import closing
from pathlib import Path
from statistics import correlation
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from matplotlib.path import Path as PlotPath
from matplotlib.patches import PathPatch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.normalization import location


def weighted(rows):
    return sum(row["tonnes"] for row in rows) / sum(row["hectares"] for row in rows)


def load_rows(path):
    with closing(sqlite3.connect(path.resolve(strict=True).as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        return list(db.execute("""
            SELECT district,crop,year,season,hectares,tonnes FROM district_crop_production
            WHERE hectares>0 ORDER BY crop,season,year,district
        """))


def analysis(rows):
    data = defaultdict(dict)
    for row in rows:
        data[row["crop"], row["season"], row["year"]][row["district"]] = row
    years = sorted({row["year"] for row in rows})
    wheat = [data["wheat", "rabi", year] for year in years]
    balanced = set.intersection(*(set(panel) for panel in wheat))
    wheat_series = [{
        "year": year, "districts": len(balanced),
        "tonnes": sum(panel[district]["tonnes"] for district in sorted(balanced)),
        "weighted_tonnes_per_ha": weighted([panel[district] for district in sorted(balanced)]),
    } for year, panel in zip(years, wheat)]
    first, last = wheat_series[0], wheat_series[-1]
    changes = {district: wheat[-1][district]["tonnes"] - wheat[0][district]["tonnes"]
               for district in sorted(balanced)}
    maize = data["maize", "kharif", years[-1]]
    soy = data["soybean", "kharif", years[-1]]
    districts = sorted(maize.keys() & soy.keys())
    matched = [[maize[d]["tonnes"]/maize[d]["hectares"], soy[d]["tonnes"]/soy[d]["hectares"]]
               for d in districts]
    x, y = zip(*matched)
    rice = data["rice", "kharif", years[-1]]
    rice_districts = sorted(rice.keys() & wheat[-1].keys())
    wheat_yield = [wheat[-1][d]["tonnes"]/wheat[-1][d]["hectares"] for d in rice_districts]
    rice_yield = [rice[d]["tonnes"]/rice[d]["hectares"] for d in rice_districts]
    report = {
        "coverage": {"eligible_district_crop_year_season_rows": len(rows), "years": years,
                     "districts": len({row["district"] for row in rows})},
        "wheat_balanced_panel": {
            "method": "Rabi district intersection across all years. Crop-level yield is summed production divided by summed area.",
            "districts": sorted(balanced), "series": wheat_series,
            "output_change_percent": 100 * (last["tonnes"] / first["tonnes"] - 1),
            "increasing_districts": sum(change > 0 for change in changes.values()),
            "largest_increase": max(changes.items(), key=lambda item: item[1]),
        },
        "maize_soybean_paired": {
            "year": years[-1], "method": "Same district and Kharif season. Pearson correlation on district yields.",
            "n": len(districts), "districts": districts, "pearson_r": correlation(x, y),
            "maize_higher_districts": sum(a > b for a, b in matched),
        },
        "wheat_rice_paired": {
            "year": years[-1],
            "method": "Same district and crop year across Rabi wheat and Kharif rice. Pearson correlation on district yields.",
            "n": len(rice_districts), "districts": rice_districts,
            "pearson_r": correlation(wheat_yield, rice_yield),
        },
        "limitations": [
            "Historical crop-production snapshots, not current forecasts.",
            "Empty cells and rows without positive observed area are excluded from yield calculations.",
            "Districts are harmonized by documented names. District splits and topology changes are not reconstructed.",
            "Descriptive associations do not control for crop mix, weather, irrigation, soil or farm practices.",
            "Maps use one historical Survey of India service layer for every frame. Unmatched districts are reported."
        ],
    }
    return report, data, matched


def draw_charts(output, report, matched):
    series = report["wheat_balanced_panel"]["series"]
    fig, ax = plt.subplots(figsize=(8, 4.2), layout="constrained")
    ax.plot([r["year"] for r in series], [r["weighted_tonnes_per_ha"] for r in series],
            marker="o", color="#287960")
    ax.set(title=f"Rabi wheat yield in a balanced panel of {series[0]['districts']} districts",
           xlabel="Crop year", ylabel="Tonnes per hectare")
    ax.grid(alpha=0.25)
    fig.savefig(output / "wheat_yield_series.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.5, 5), layout="constrained")
    x, y = zip(*matched)
    ax.scatter(x, y, color="#287960", edgecolor="white")
    pair = report["maize_soybean_paired"]
    ax.set(title=f"Kharif district yields in {pair['year']} (n={pair['n']})",
           xlabel="Maize tonnes per hectare", ylabel="Soybean tonnes per hectare")
    ax.grid(alpha=0.25)
    fig.savefig(output / "maize_soybean_yield.png", dpi=150)
    plt.close(fig)


def district_paths(geojson):
    features = json.loads(geojson.read_text(encoding="utf-8"))["features"]
    patches = []
    for feature in features:
        geometry = feature["geometry"]
        polygons = geometry["coordinates"]
        if geometry["type"] == "Polygon":
            polygons = [polygons]
        elif geometry["type"] != "MultiPolygon":
            raise ValueError("District geometry must be polygonal")
        rings = [PlotPath(ring, closed=True) for polygon in polygons for ring in polygon]
        patches.append((location(feature["properties"]["district"]), PlotPath.make_compound_path(*rings)))
    if len({name for name, _ in patches}) != len(patches):
        raise ValueError("Multiple features normalize to the same district")
    return patches


def draw_maps(output, geojson, report, data):
    paths = district_paths(geojson)
    names = {name for name, _ in paths}
    years = report["coverage"]["years"]
    panels = [{district: row["tonnes"]/row["hectares"] for district, row in
               data["wheat", "rabi", year].items()} for year in years]
    scale = Normalize(0, max(value for panel in panels for value in panel.values()))
    frames = []
    report["map_join"] = []
    for year, panel in zip(years, panels):
        fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
        cmap = plt.colormaps["YlGn"]
        shapes = PatchCollection([PathPatch(path) for _, path in paths],
                                 facecolor=[cmap(scale(panel[name])) if name in panel else "#d2d6d4"
                                            for name, _ in paths],
                                 edgecolor="#3a4b44", linewidth=0.4)
        ax.add_collection(shapes)
        ax.autoscale_view()
        ax.set_aspect(1.10)
        ax.set_axis_off()
        joined = names & panel.keys()
        ax.set_title(f"Madhya Pradesh · Rabi wheat yield · {year}\n"
                     f"{len(joined)}/{len(names)} mapped districts with data")
        fig.colorbar(plt.cm.ScalarMappable(norm=scale, cmap=cmap), ax=ax, label="Tonnes per hectare")
        fig.text(0.03, 0.02, "Boundaries: Survey of India via Esri India, 2021 service layer. Grey: no matched data.", fontsize=8)
        frame = output / f"wheat_yield_map_{year}.png"
        fig.savefig(frame, dpi=135)
        plt.close(fig)
        with Image.open(frame) as image:
            frames.append(image.convert("RGB"))
        report["map_join"].append({"year": year, "mapped_districts": len(joined),
                                   "districts_without_shape": sorted(panel.keys() - names),
                                   "shapes_without_data": sorted(names - panel.keys())})
    frames[0].save(output / "wheat_yield_2016_2022.gif", save_all=True, append_images=frames[1:],
                   duration=1100, loop=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ROOT / "output/release/agriagent.sqlite")
    parser.add_argument("--geometry", type=Path, default=ROOT / "data/production/mp_districts.geojson")
    parser.add_argument("--output", type=Path, default=ROOT / "output/analysis")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("Choose an empty analysis directory to preserve previous artifacts")
    report, data, matched = analysis(load_rows(args.db))
    draw_charts(args.output, report, matched)
    draw_maps(args.output, args.geometry, report, data)
    (args.output / "findings.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Analysis saved to {args.output}")


if __name__ == "__main__":
    main()
