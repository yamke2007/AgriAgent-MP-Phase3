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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="config/lgd_mp_districts.json")
    ap.add_argument("--no-config", action="store_true", help="do not edit config.json")
    a = ap.parse_args()
    with open(a.csv, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("empty CSV")
    h = list(rows[0])
    state = pick(h, "state", "name") or pick(h, "state", avoid=("code",))
    code = pick(h, "district", "code") or pick(h, "lgd", "code")
    name = (pick(h, "district", "name", avoid=("local", "hindi")) or pick(h, "district", avoid=("code",)))
    if not (code and name):
        sys.exit(f"could not find district code/name columns in {h}")
    reg = {}
    for r in rows:
        if state and "madhya pradesh" not in r[state].casefold():
            continue
        c, n = r[code].strip(), r[name].strip()
        if c and n:
            reg[c] = n
    if not reg:
        sys.exit("no Madhya Pradesh rows found")
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(sorted(reg.items())), indent=1, ensure_ascii=False), encoding="utf-8")
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
