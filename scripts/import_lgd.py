"""Convert the official LGD district list into the registry the pipeline uses.

LGD (Local Government Directory, Ministry of Panchayati Raj) is the official
source of district codes. The pipeline never invents a code: a record gets an
lgd_code only when its district name matches exactly one registry entry, and
validate() rejects any code that is not in the registry.

Download one of these (CSV, no login needed in a normal browser):
  * India Data Portal, "LGD Codes", resource "District LGD Codes"
    https://ckandev.indiadataportal.com/dataset/lgd-codes
  * or lgdirectory.gov.in > Download Directory > District (state = Madhya Pradesh)

Then:
    python scripts/import_lgd.py path/to/district_lgd_codes.csv
    # writes config/lgd_mp_districts.json and sets "lgd_registry" in config.json

The script finds the state, district-code and district-name columns by header
words, keeps Madhya Pradesh rows only and reports any of the 55 project
districts that did not get a code (e.g. a spelling difference to add to
DISTRICT_ALIASES in agriagent/normalization.py).
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agriagent.mp_districts import DISTRICTS  # noqa: E402
from agriagent.normalization import location  # noqa: E402


def pick(headers, *need, avoid=()):
    for h in headers:
        low = h.casefold()
        if all(w in low for w in need) and not any(w in low for w in avoid):
            return h
    return None


def registry_from_csv(path, *, scoped_mp=False):
    """Accept official CSV layouts and reject unsafe duplicate or cross-state entries."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        normalized = {re.sub(r"[^a-z0-9]", "", field.casefold()): field for field in headers}
        state_code = next((normalized[k] for k in ("statelgdcode", "statecode") if k in normalized), None)
        state = next((normalized[k] for k in ("statenameenglish", "statename", "stateutname", "statenameinenglish", "state")
                      if k in normalized), None) or pick(headers, "state", avoid=("code", "local"))
        code = next((normalized[k] for k in ("districtlgdcode", "districtcode", "lgddistrictcode") if k in normalized),
                    None) or pick(headers, "lgd", "code")
        name = next((normalized[k] for k in ("districtnameenglish", "districtnameinenglish", "districtname", "district")
                     if k in normalized), None)
        if not (code and name) or not (state or state_code or scoped_mp):
            raise ValueError("Expected district LGD code/name columns and a state column or an explicitly MP-only export")

        registry, names = {}, {}
        for row in reader:
            state_by_name = (row[state] or "").strip().casefold() == "madhya pradesh" if state else None
            state_by_code = (row[state_code] or "").strip() == "23" if state_code else None
            flags = [flag for flag in (state_by_name, state_by_code) if flag is not None]
            if flags and any(flags) and not all(flags):
                raise ValueError(f"Conflicting Madhya Pradesh state identifiers on line {reader.line_num}")
            if flags and not all(flags):
                continue
            key, label = (row[code] or "").strip(), (row[name] or "").strip()
            if not re.fullmatch(r"[1-9][0-9]*", key) or not label:
                raise ValueError(f"Invalid district code/name on line {reader.line_num}")
            district = location(label)
            if (key in registry and location(registry[key]) != district) or (district in names and names[district] != key):
                raise ValueError(f"Conflicting district name or code on line {reader.line_num}")
            registry[key], names[district] = label, key
    if not registry:
        raise ValueError("No Madhya Pradesh district codes found")
    return registry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="config/lgd_mp_districts.json")
    ap.add_argument("--no-config", action="store_true", help="do not edit config.json")
    ap.add_argument("--mp-only-export", action="store_true", help="assert this CSV was explicitly exported for Madhya Pradesh")
    a = ap.parse_args()
    reg = registry_from_csv(a.csv, scoped_mp=a.mp_only_export)
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as stream:
        json.dump(dict(sorted(reg.items())), stream, indent=1, ensure_ascii=False)
    got = {location(v) for v in reg.values()}
    print(f"{len(reg)} MP district codes written to {a.out}")
    missing = sorted(DISTRICTS - got)
    if missing:
        print("project districts without a code (check spelling/aliases):", ", ".join(missing))
    if not a.no_config:
        cfg_path = ROOT / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["lgd_registry"] = a.out
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        print("config.json: lgd_registry =", a.out)


if __name__ == "__main__":
    main()
