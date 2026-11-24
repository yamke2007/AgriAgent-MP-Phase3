"""Resolve evaluated fields by cell and context, independent of extraction output evidence."""
import csv
import re
from datetime import datetime
from functools import lru_cache

from bs4 import BeautifulSoup

from agriagent.normalization import MISSING, NA, crop, location, period, text
from eval.matching import matches

PRICE_COLUMNS = {
    "Arrivals (Tonnes)": ("arrivals", "tonne"),
    "Min Price (Rs./Quintal)": ("min_price", "INR/quintal"),
    "Max Price (Rs./Quintal)": ("max_price", "INR/quintal"),
    "Modal Price (Rs./Quintal)": ("modal_price", "INR/quintal"),
}


@lru_cache(maxsize=16)
def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.reader(stream))


@lru_cache(maxsize=16)
def html_rows(path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8-sig"), "html.parser")
    return [
        [
            [text(cell.get_text(" ", strip=True)) for cell in row.find_all(["td", "th"], recursive=False)]
            for row in table.find_all("tr")
        ]
        for table in soup.find_all("table")
    ]


def cell_observation(path, locator, agent, variable):
    def at(index):
        if int(index) < 1:
            raise ValueError("Locators are one-based")
        return int(index) - 1

    if agent in {"directory", "scheme"}:
        table, row = re.fullmatch(r"table:(\d+)/row:(\d+)", locator).groups()
        cells = html_rows(path)[at(table)][at(row)]
        if agent == "scheme":
            label, value = cells
            return dict(crop=NA, location=MISSING, period=MISSING, variable=label,
                        value=value or MISSING, unit="text", value_kind="text")
        _, address, host, sanction = cells
        district = re.search(r"Distt\.\s*([A-Za-z ]+)", address)
        year = re.search(r"\b(?:19|20)\d{2}\b", sanction)
        values = {
            "address": (address, "text", "text"),
            "host_organization": (host, "text", "text"),
            "sanction_year": (year.group() if year else MISSING, "year", "integer"),
        }
        value, unit, kind = values[variable]
        return dict(crop=NA, location=location(district.group(1)) if district else MISSING,
                    period=NA, variable=variable, value=value, unit=unit, value_kind=kind)
    rows = csv_rows(path)
    if agent == "statistics":
        line, = re.fullmatch(r"csv:line:(\d+)", locator).groups()
        ref = dict(zip(rows[0], rows[at(line)], strict=True))
        ref.update(crop=crop(ref["crop"]), location=location(ref["location"]), period=period(ref["period"]))
        return ref
    line, column = re.fullmatch(r"csv/row:(\d+)/col:(\d+)", locator).groups()
    row = rows[at(line)]
    ref = dict(zip(rows[0], row, strict=True))
    variable, unit = PRICE_COLUMNS[rows[0][at(column)]]
    value = row[at(column)].replace(",", "")
    commodity = path.stem.split("_")[-2]
    if ref["State Name"] != "Madhya Pradesh":
        raise ValueError("Source row is outside Madhya Pradesh")
    return dict(crop=crop(commodity), location=location(ref["District Name"]),
                period=datetime.strptime(ref["Reported Date"], "%d %b %Y").date().isoformat(),
                variable=variable, value=value, unit=unit,
                value_kind="decimal" if "." in value else "integer")


def input_support(path, locator, agent, record):
    try:
        reference = cell_observation(path, locator, agent, record["variable"])
        return reference["value"] != MISSING and matches(record, reference)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return False


@lru_cache(maxsize=20)
def parent_csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {
            tuple(row) for row in csv.reader(stream)
            if row and row[0] == "Madhya Pradesh"
        }


def archive_support(path, parent, locator, record):
    if not input_support(path, locator, "tables", record):
        return False
    line = int(re.fullmatch(r"csv/row:(\d+)/col:(\d+)", locator).group(1))
    return tuple(csv_rows(path)[line - 1]) in parent_csv_rows(parent)
