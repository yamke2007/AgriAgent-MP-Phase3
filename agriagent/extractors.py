"""Parsers operate on supplied content, never case IDs or expected answers."""
import csv
import io
import re
from bs4 import BeautifulSoup
from . import public_sources
from .normalization import crop as normalize_crop, text, MISSING, NA

STATS_FIELDS = {"crop", "location", "period", "variable", "value", "unit"}
PRODUCTION_FIELDS = {"State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production"}
TONNE_CROPS = {"chickpea", "maize", "rice", "soybean", "wheat"}

class ExtractionError(ValueError):
    pass

def soup_of(path):
    return BeautifulSoup(path.read_bytes().decode("utf-8-sig"), "html.parser")

IMAGE = (".png", ".jpg", ".jpeg", ".tif", ".tiff")

def detect(path):
    """Primary specialist for an input: (agent, tool, source group). Fixed rules, no model."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("rb") as source:
            head = source.read(4096).decode("utf-8-sig", errors="replace").splitlines()[:1]
        cols = {c.strip() for c in next(csv.reader(head), [])} if head else set()
        if STATS_FIELDS.issubset(cols) or PRODUCTION_FIELDS.issubset(cols) or not head:
            return "statistics", "csv.DictReader", "Database"
        return "tables", "csv.reader", "Database"
    if suffix == ".pdf":
        return "statistics", "pypdf", "Document"
    if suffix in (".xlsx", ".xlsm"):
        return "tables", "openpyxl.read", "Database"
    if suffix in IMAGE:
        return "tables", "tesseract.ocr_tables", "Document"
    if suffix in (".html", ".htm"):
        soup = soup_of(path)
        content = soup.get_text(" ", strip=True)
        if "Host Organization" in content and "Year of Sanction" in content:
            return "directory", "beautifulsoup4", "Document"
        if "योजना का नाम" in content and "विभाग" in content:
            return "scheme", "beautifulsoup4", "Document"
        if public_sources.identify(soup):
            return "scheme", "beautifulsoup4", "Document"
        if "{{" in content:
            raise ExtractionError("Unrendered dynamic template: export actual results; placeholders are not observations")
        if soup.find("table") is None:
            raise ExtractionError("Unsupported HTML structure: no table found")
        return "tables", "beautifulsoup4.tables", "Document"
    raise ExtractionError("Unsupported modality: use HTML, CSV, XLSX, PDF or an image; audio is pending")

def directory(path):
    soup = soup_of(path)
    records = []
    for ti, table in enumerate(soup.find_all("table"), 1):
        if "Year of Sanction" not in table.get_text():
            continue
        for ri, row in enumerate(table.find_all("tr"), 1):
            cells = row.find_all(["td", "th"], recursive=False)
            if len(cells) != 4 or not re.fullmatch(r"\d+\.?", cells[0].get_text(strip=True)):
                continue
            address, host, sanction = [text(c.get_text(" ", strip=True)) for c in cells[1:]]
            district = re.search(r"Distt\.\s*([A-Za-z ]+)", address)
            year = re.search(r"\b(?:19|20)\d{2}\b", sanction)
            locator = f"table:{ti}/row:{ri}"
            common = dict(crop=NA, location=district.group(1).strip(" ,.-") if district else MISSING,
                          period=NA, locator=locator, evidence=text(row.get_text(" ", strip=True)),
                          record_id=cells[0].get_text(strip=True).rstrip("."))
            for variable, value, unit, kind in (("address",address,"text","text"),
                    ("host_organization",host,"text","text"),
                    ("sanction_year",year.group() if year else MISSING,"year","integer")):
                records.append(dict(common,variable=variable,value=value,unit=unit,value_kind=kind))
    if not records:
        raise ExtractionError("No KVK records found")
    return records, []

def scheme(path):
    soup = soup_of(path)
    public_parser = public_sources.identify(soup)
    if public_parser:
        records, warnings = public_parser(soup)
        if not records:
            raise ExtractionError("; ".join(warnings))
        return records, warnings
    records = []
    # Preserve the official Hindi label rather than guess a translated field.
    for ti, table in enumerate(soup.find_all("table"), 1):
        for ri, row in enumerate(table.find_all("tr"), 1):
            cells = row.find_all(["td", "th"], recursive=False)
            if len(cells) != 2:
                continue
            key, value = [text(c.get_text(" ", strip=True)) for c in cells]
            if not key:
                continue
            records.append(dict(crop=NA,location=MISSING,period=MISSING,variable=key,
                value=value or MISSING,unit="text",value_kind="text",locator=f"table:{ti}/row:{ri}",
                evidence=text(row.get_text(" ",strip=True))))
    if not records:
        raise ExtractionError("No two-cell policy rows found")
    return records, []

def statistics(path, max_pages=300, scoped_survey=False):
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        pdf = PdfReader(path)
        if len(pdf.pages) > max_pages:
            raise ExtractionError("PDF page limit exceeded")
        front = [text(page.extract_text() or "") for page in pdf.pages[:3]]
        published = public_sources.published_pdf_fields(pdf, front)
        if scoped_survey and published is None:
            from . import survey_agriculture
            published = survey_agriculture.extract(pdf, front)
        if published is not None:
            records, warnings = published
            if not records:
                raise ExtractionError("; ".join(warnings))
            return records, warnings
        records = []
        # Intentionally conservative grammar; other facts remain unextracted.
        pattern = re.compile(r"produced\s+([\d,.]+)\s+(lakh tonnes|tonnes)\s+of\s+(wheat|paddy|rice|maize|soybean|gram|cotton)\s+in\s+(\d{4}-\d{2})", re.I)
        pages = front + [text(page.extract_text() or "") for page in pdf.pages[3:]]
        state = "Madhya Pradesh" if any("Madhya Pradesh" in page for page in pages[:3]) else MISSING
        for pi, content in enumerate(pages, 1):
            for match in pattern.finditer(content):
                value, unit, crop, year = match.groups()
                records.append(dict(crop=crop, location=state,
                    period=year,variable="production",value=value,unit=unit,value_kind="decimal",
                    locator=f"page:{pi}/char:{match.start()}-{match.end()}",evidence=match.group(),qualifier="source wording; estimates may be provisional"))
        if not records:
            manual = mandi_manual_fields(pages)
            if manual:
                return manual, ["Market workflow documentation only; excludes personal fields and screenshot examples"]
            premiums = pmfby_premium_fields(pages)
            if premiums:
                return premiums, ["Historical PMFBY schedule. Premium caps are conditional on the lower actuarial rate."]
            raise ExtractionError("No supported production sentences; text pages="+str(sum(map(bool, pages)))+"; tables/OCR are left to the tables agent")
        return records, ["Partial PDF grammar: only explicit 'produced X tonnes of CROP in YEAR' sentences; omitted facts are not inferred"]
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig")))
    if PRODUCTION_FIELDS.issubset(reader.fieldnames or []):
        return crop_production(reader)
    if not STATS_FIELDS.issubset(reader.fieldnames or []):
        raise ExtractionError("CSV requires headers: "+", ".join(sorted(STATS_FIELDS)))
    records = []
    for row in reader:
        if None in row:
            raise ExtractionError("Malformed CSV: excess columns")
        record = {k: text(v or MISSING) for k,v in row.items()}
        record.setdefault("value_kind", "decimal")
        record["evidence"] = text(" | ".join(str(v or "") for v in row.values()))
        record["locator"] = f"csv:line:{reader.line_num}"
        records.append(record)
    if not records:
        raise ExtractionError("CSV has no data rows")
    return records, []


def mandi_manual_fields(pages):
    if not pages or "USER MANUAL FOR SECRETARY" not in pages[0] or "(E-MANDI)" not in pages[0]:
        return []
    patterns = {
        "mandi_date_entry_format": re.compile(r"\((dd-MM-yyyy)\)", re.I),
        "mandi_workflow_portal": re.compile(r"\bURL\b.*?(https://(?:www\.)?eanugya\.mp\.gov\.in)(?=[/\s]|$)", re.I),
    }
    records = []
    for variable, pattern in patterns.items():
        for page, content in enumerate(pages, 1):
            match = pattern.search(content)
            if match:
                records.append(dict(
                    crop=NA, location="Madhya Pradesh", period=MISSING, variable=variable,
                    value=match.group(1), unit="text", value_kind="text", locator=f"page:{page}/char:{match.start(1)}-{match.end(1)}",
                    evidence=match.group(), qualifier="Historical public workflow instructions",
                ))
                break
    return records


def pmfby_premium_fields(pages):
    if not pages or not all(term in pages[0] for term in (
        "OPERATIONAL GUIDELINES", "Pradhan Mantri Fasal Bima Yojana",
    )):
        return []
    conditions = (
        ("Kharif", "foodgrains_and_oilseeds_kharif"),
        ("Rabi", "foodgrains_and_oilseeds_rabi"),
        ("Kharif and Rabi", "annual_commercial_horticulture"),
    )
    records = []
    for number, content in enumerate(pages, 1):
        if "Premium Rates and Premium Subsidy" not in content:
            continue
        for season, scope in conditions:
            label = r"Annual Commercial/\s*Annual Horticultural crops" if "annual" in scope else r"All food grain and Oilseeds crops \([^)]*\)"
            match = re.search(
                rf"\b{season}\s+{label}\s+(\d+(?:\.\d+)?)\s*%\s+of SI or Actuarial rate,\s+whichever is less",
                content, re.I,
            )
            if match:
                records.append(dict(
                    crop=NA, location="India", period=MISSING, variable=f"pmfby_premium_cap_{scope}",
                    value=match.group(1), unit="percent", value_kind="decimal",
                    locator=f"page:{number}/char:{match.start(1)}-{match.end(1)}",
                    evidence=match.group(), qualifier="Historical national guideline; lower of cap and actuarial rate",
                ))
        if records:
            return records
    return records


def crop_production(reader):
    """Read the OGD district crop production CSV schema, using crop-specific units."""
    records = []
    missing = 0
    for row in reader:
        if None in row or any(row[key] is None for key in PRODUCTION_FIELDS):
            raise ExtractionError(f"Malformed crop production CSV on line {reader.line_num}")
        if text(row["State_Name"]).casefold() != "madhya pradesh":
            continue
        crop = normalize_crop(row["Crop"])
        if crop not in TONNE_CROPS:
            continue
        origin = row.get("Original_Row", "").strip()
        if origin and (not origin.isdecimal() or int(origin) < 2):
            raise ExtractionError(f"Invalid original row number on line {reader.line_num}")
        for column, variable, unit in (
            ("Area", "area", "hectare"),
            ("Production", "production", "tonne"),
        ):
            value = text(row[column])
            if not value:
                missing += 1
                continue
            record = dict(
                crop=crop, location=row["District_Name"], period=row["Crop_Year"],
                season=text(row["Season"]).casefold(), district_as_reported=row["District_Name"],
                variable=variable, value=value, unit=unit, value_kind="decimal",
                locator=f"csv:line:{reader.line_num}/column:{column}",
                evidence=" | ".join(row[key] for key in reader.fieldnames),
            )
            if origin:
                record["origin_locator"] = f"csv:line:{origin}/column:{column}"
            records.append(record)
    if not records:
        raise ExtractionError("No supported Madhya Pradesh crop production rows")
    return records, [f"{missing} empty area or production cells skipped"] if missing else []
