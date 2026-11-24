"""Evaluate real image-only English forecast cells and legacy-font Hindi passages."""
import argparse
import json
import sys
import time
from pathlib import Path

from pypdf import PdfReader
import pypdfium2
import pytesseract

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.normalization import text
from agriagent.pipeline import process, sha
from scripts.verify_source_expansion import PLAN, check_fields

HINDI = [
    ("date_format", (0.080, 0.080, 0.955, 0.150),
     "1. किसी भी दिनांक वाली फील्ड में दिनांक (dd-MM-yyyy) वाले प्रारूप में ही डाले। जैसे कि - (03-01-2019)"),
    ("numeric_entry", (0.080, 0.157, 0.960, 0.221),
     "2. नंबर वाली फील्ड को हिंदी के नंबर में एंट्री न करे। जैसे कि “2200” को हिंदी में २२०० न डाले ।"),
    ("publisher_name", (0.051, 0.923, 0.566, 0.955), "म.प्र. राज्य कृषि विपणन (मंडी) बोर्ड"),
]


def distance(a, b):
    previous = list(range(len(b) + 1))
    for i, left in enumerate(a, 1):
        current = [i]
        for j, right in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[-1] + 1, previous[j-1] + (left != right)))
        previous = current
    return previous[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output directory")
    args.output.mkdir(parents=True)
    all_cases = json.loads(PLAN.read_text(encoding="utf-8"))["inputs"]
    entry = next(case for case in all_cases if case["source_id"] == "S10")
    path = ROOT / entry["path"]
    report = json.loads((args.source_run / "report.json").read_text(encoding="utf-8"))
    run_id = next(case["run_id"] for case in report["cases"] if case["source_id"] == "S10")
    trace = json.loads((args.source_run / "runs" / f"{run_id}.json").read_text(encoding="utf-8"))
    if sha(path) != entry["sha256"] or trace["input_sha256"] != entry["sha256"]:
        raise ValueError("OCR source or tool trace differs from the frozen bulletin")
    checks = check_fields(trace["records"], entry["checks"])
    english = {
        "source_url": entry["url"], "source_sha256": entry["sha256"], "source_page": 1,
        "native_text_characters_per_page": [len(text(page.extract_text() or "")) for page in PdfReader(path).pages],
        "exact_cells": sum(check["matched"] for check in checks), "sample_cells": len(checks),
        "records": checks, "tool_trace": trace["trajectory"], "latency_seconds": trace["latency_seconds"],
    }
    hindi_path = ROOT / "data/raw/e_mandi_manual.pdf"
    baseline_text = text(PdfReader(hindi_path).pages[1].extract_text() or "")
    with pypdfium2.PdfDocument(str(hindi_path)) as doc:
        image = doc[1].render(scale=300 / 72).to_pil().copy()
    regions = []
    for label, bounds, reference in HINDI:
        ref = text(reference)
        crop = image.crop(tuple(round(part * (image.width if i % 2 == 0 else image.height))
                                for i, part in enumerate(bounds)))
        start = time.perf_counter()
        predicted = text(pytesseract.image_to_string(crop, lang="hin+eng", config="--psm 6", timeout=10))
        elapsed = time.perf_counter() - start
        regions.append(dict(region=label, bounds=list(bounds), expected=ref, actual=predicted,
                            text_layer_exact=ref in baseline_text, exact=ref == predicted,
                            reference_characters=len(ref), char_edits=distance(ref, predicted),
                            reference_words=len(ref.split()), word_edits=distance(ref.split(), predicted.split()),
                            latency_seconds=elapsed))
    hindi = dict(source_path=hindi_path.relative_to(ROOT).as_posix(), source_sha256=sha(hindi_path), source_page=2,
                 regions=regions, exact_regions=sum(item["exact"] for item in regions),
                 text_layer_exact_regions=sum(item["text_layer_exact"] for item in regions),
                 cer=sum(item["char_edits"] for item in regions) / sum(item["reference_characters"] for item in regions),
                 wer=sum(item["word_edits"] for item in regions) / sum(item["reference_words"] for item in regions))

    des = next(item for item in all_cases if item["source_id"] == "S12")
    fault = process(ROOT / des["path"], persist=False, inject_tool="pdfplumber.extract_tables")
    fault_checks = check_fields(fault["records"], des["checks"])
    workflow = {
        "source": des["url"], "input_sha256": fault["input_sha256"], "engine": fault["orchestrator"],
        "recovered": fault["status"] == "complete" and len(fault["records"]) == des["expected_count"]
        and fault["retries"] == 1 and all(check["matched"] for check in fault_checks),
        "retries": fault["retries"], "records": len(fault["records"]),
        "trajectory": fault["trajectory"], "agent_trace": fault["agent_trace"], "notes": fault["notes"],
    }
    results = {"tesseract": str(pytesseract.get_tesseract_version()),
               "references": "Source-image inspection by implementer. Independent human review pending.",
               "english_image_only": english, "hindi_legacy_pdf": hindi, "real_des_fault": workflow}
    (args.output / "report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(dict(english_exact=english["exact_cells"], english_sample=english["sample_cells"],
                          hindi_cer=hindi["cer"], hindi_wer=hindi["wer"], hindi_exact=hindi["exact_regions"],
                          hindi_text_layer_exact=hindi["text_layer_exact_regions"], fault_recovered=workflow["recovered"])))
    return int(english["exact_cells"] != english["sample_cells"] or not workflow["recovered"])


if __name__ == "__main__":
    raise SystemExit(main())
