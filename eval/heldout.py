"""Freeze the adapter cohort and audit exact and source-lineage separation."""
import csv
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path

from agriagent.model import prompt_for

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "eval/m18_cases.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parents_for_cases(root, cases):
    lineage = []
    for case in cases:
        parent = case.get("source")
        if not parent or not case.get("source_locator") or not case.get("parent_sha256"):
            raise ValueError(f"Incomplete source lineage for {case['case_id']}")
        relative = "/".join(parent.split("/")[-2:]).casefold()
        lineage.append({"parent": relative, "input": case["input_sha256"], "parent_sha256": case["parent_sha256"]})
        if sha(root / case["input"]) != case["input_sha256"]:
            raise ValueError(f"Input hash mismatch for {case['case_id']}")
    return lineage


def verify_training(root, cases):
    lineage = parents_for_cases(root, cases)
    case_parents = {entry["parent"] for entry in lineage}
    case_hashes = {entry[key] for entry in lineage for key in ("input", "parent_sha256")}
    training = [json.loads(line) for line in (root / "data/train/examples.jsonl").read_text(encoding="utf-8").splitlines()]
    inputs = set()
    for item in training:
        if not item.get("parent") or not item.get("source"):
            raise ValueError("Training source and parent lineage are required")
        path = (root / item["source"]).resolve(strict=True)
        if (not path.is_relative_to((root / "data/train/raw").resolve())
                or item["parent"].casefold() in case_parents or item["sha256"] in case_hashes
                or item["sha256"] in inputs or sha(path) != item["sha256"]):
            raise ValueError(f"Training lineage overlap or tampering: {item['source']}")
        inputs.add(item["sha256"])
        content = path.read_text(encoding="utf-8")
        if item["prompt"] != prompt_for(content, path.name) or item["target"] != source_targets(content, item["parent"]):
            raise ValueError(f"Training prompt or targets differ from their source cells: {item['source']}")
    return training


def source_targets(content, parent):
    price = "INR/quintal"
    columns = (
        ("Arrivals (Tonnes)", "arrivals", "tonne"),
        ("Min Price (Rs./Quintal)", "min_price", price),
        ("Max Price (Rs./Quintal)", "max_price", price),
        ("Modal Price (Rs./Quintal)", "modal_price", price),
    )
    crops = {"Soyabean": "soybean", "Wheat": "wheat", "Maize": "maize"}
    commodity, filename = parent.split("/")
    targets = []
    for row in csv.DictReader(io.StringIO(content)):
        day = datetime.strptime(row["Reported Date"], "%d %b %Y").date()
        if row["State Name"] != "Madhya Pradesh" or filename != f"{day.year}.csv":
            raise ValueError("Training row contradicts its recorded state or parent year")
        for column, variable, unit in columns:
            value = row[column].replace(",", "")
            targets.append(dict(crop=crops[commodity], location=row["District Name"].strip().casefold(),
                                period=day.isoformat(), variable=variable, value=value, unit=unit,
                                value_kind="decimal" if "." in value else "integer"))
    if not targets:
        raise ValueError("Empty training input")
    return targets


def freeze():
    index = json.loads((ROOT / "eval/case_index.json").read_text(encoding="utf-8"))
    cases = [case for case in index if case.get("split") == "heldout"]
    if len(cases) < 10:
        raise ValueError("At least ten held-out inputs required")
    verify_training(ROOT, cases)
    for case in cases:
        case["reference_sha256"] = sha(ROOT / case["reference"])
    with LOCK.open("x", encoding="utf-8") as stream:
        json.dump(cases, stream, indent=2)
        stream.write("\n")


def load_cases(root=ROOT, references=True):
    cases = json.loads((root / "eval/m18_cases.json").read_text(encoding="utf-8"))
    parents_for_cases(root, cases)
    if references and any(sha(root / case["reference"]) != case["reference_sha256"] for case in cases):
        raise ValueError("The frozen references have changed")
    return cases


if __name__ == "__main__":
    freeze()
