"""Narrow parsers for published agricultural data and public programme rules."""
import re
from datetime import datetime

from .normalization import MISSING, NA, text

NUMBER = r"([0-9०-९][0-9०-९,]*)"


def observation(variable, value, unit, locator, evidence, *, location="Madhya Pradesh",
                period=MISSING, kind="integer", **metadata):
    return dict(crop=NA, location=location, period=period, variable=variable, value=value,
                unit=unit, value_kind=kind, locator=locator, evidence=evidence, **metadata)


def identify(soup):
    title = text(soup.title.get_text()) if soup.title else ""
    if soup.select_one("#accordionEx #collapseOne1") and "कृषि अभियांत्रिकी संचालनालय" in title:
        return machinery
    if "यंत्र अनुदान" in title and soup.select_one(".page-context .panel-success"):
        return subsidy
    if title == "Features of PM-KISAN Scheme" and soup.select_one("#condiv"):
        return pmkisan
    if "Aspirational Districts" in title and soup.select_one("#madhyapradesh_list table"):
        return aspirational_markets
    if "No. of Unified Licenses" in title and soup.select_one("table.unified"):
        return unified_licenses
    return None


def numeric_fields(soup, definitions, **metadata):
    records, warnings = [], []
    for selector, variable, unit, pattern in definitions:
        hits = []
        for index, element in enumerate(soup.select(selector), 1):
            content = text(element.get_text(" ", strip=True))
            result = re.search(pattern, content, re.I)
            if result:
                value = str(int(result.group(1).replace(",", "")))
                hits.append((value, index, result.group(0)))
        if hits and len({value for value, _, _ in hits}) == 1:
            value, index, evidence = hits[0]
            records.append(observation(variable, value, unit, f"css:{selector}/match:{index}",
                                       evidence, **metadata))
        else:
            warnings.append(f"{variable}: no unique value found in the published format")
    return records, warnings


def machinery(soup):
    rental = "#collapseOne1 li"
    hiring = "#collapseOne3 li"
    plough = "#collapseOne5 li"
    return numeric_fields(soup, [
        (rental, "government_tractor_rental_district_count_as_published", "count", rf"प्रदेश के {NUMBER} जिलों"),
        (rental, "government_tractor_rental_fleet_as_published", "count", rf"में {NUMBER} टे?्रक्टर्स"),
        (hiring, "custom_hiring_subsidy_general_share", "percent", rf"सामान्य श्रेणी के आवेदकों को {NUMBER} प्रतिशत"),
        (hiring, "custom_hiring_subsidy_sc_st_share", "percent", rf"जनजाति के आवेदकों को लागत का {NUMBER} प्रतिशत"),
        (hiring, "custom_hiring_subsidy_cap_lakh_inr", "lakh INR", rf"जनजाति के आवेदकों को लागत का [0-9०-९]+ प्रतिशत अधिकतम राशि रू\. {NUMBER} लाख"),
        (plough, "deep_ploughing_subsidy_share", "percent", rf"लागत का {NUMBER} प्रतिशत"),
        (plough, "deep_ploughing_subsidy_cap_inr", "INR", rf"अधिकतम रूपये {NUMBER}"),
    ], qualifier="Published service or scheme terms; effective date unstated")


def subsidy(soup):
    rules = ".page-context .panel-success li"
    return numeric_fields(soup, [
        (rules, "machinery_subsidy_purchase_deadline", "day", rf"क्रय स्वीकृति आदेश जारी होने के {NUMBER} दिवस"),
        (rules, "machinery_subsidy_inspection_deadline", "day", rf"अपलोड करने के {NUMBER} दिवस में विभागीय"),
        (rules, "machinery_subsidy_reapply_wait_after_rejection", "month", rf"आवेदन निरस्त होने के उपरांत आप को आगामी {NUMBER} माह"),
    ], qualifier="Published procedure; effective date unstated")


def pmkisan(soup):
    stamp = soup.select_one("#thd1")
    stamp_text = text(stamp.get_text(" ", strip=True)) if stamp else ""
    announced = re.search(r"\b[0-9]{1,2} [A-Z]{3} [0-9]{4}\b", stamp_text)
    period = datetime.strptime(announced.group(), "%d %b %Y").date().isoformat() if announced else MISSING
    records, warnings = numeric_fields(soup, [
        ("#condiv p", "pmkisan_annual_assistance", "INR", rf"financial assistance of Rs\.\s*{NUMBER}/- per annum"),
        ("#condiv p", "pmkisan_installment_amount", "INR", rf"4-monthly installments of Rs\.\s*{NUMBER}/- each"),
    ], location="India", period=period, qualifier="As reported in the published parliamentary reply")
    if period == MISSING:
        warnings.append("Parliamentary reply publication date could not be resolved")
    return records, warnings


def tabular_rows(table):
    return [(number, [text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"], recursive=False)])
            for number, row in enumerate(table.find_all("tr"), 1)]


def aspirational_markets(soup):
    selector = "#madhyapradesh_list table"
    rows = tabular_rows(soup.select_one(selector))
    if len(rows) < 3 or rows[0][1][0].casefold() != "state: madhya pradesh" or rows[1][1] != ["District", "Mandis"]:
        return [], ["Unexpected Madhya Pradesh mandi list header"]
    total = re.fullmatch(r"total mandis:\s*(\d+)", rows[0][1][1], re.I)
    records = [
        observation("enam_aspirational_mandi", row[1], "text", f"css:{selector}/row:{number}/col:2",
                    " | ".join(row), location=row[0], kind="text")
        for number, row in rows[2:] if len(row) == 2 and all(row)
    ]
    if total is None or int(total.group(1)) != len(records):
        return records, ["Reported mandi count does not match the extracted list"]
    return records, []


def unified_licenses(soup):
    selector = "table.unified"
    rows = tabular_rows(soup.select_one(selector))
    header = ["Mandis registered on e-NAM", "Registered Traders on e-NAM", "No. of Unified licenses issued by State"]
    if not rows or rows[0][1][2:] != header:
        return [], ["Unexpected state unified license headers"]
    selected = [(number, row) for number, row in rows[1:] if len(row) == 5 and row[1].casefold() == "madhya pradesh"]
    if len(selected) != 1:
        return [], ["Could not locate a unique Madhya Pradesh row"]
    number, row = selected[0]
    records = []
    for col, variable in enumerate(("enam_registered_mandis", "enam_registered_traders", "enam_unified_licenses_issued"), 2):
        if re.fullmatch(r"\d[\d,]*", row[col]):
            records.append(observation(variable, row[col].replace(",", ""), "count",
                                       f"css:{selector}/row:{number}/col:{col+1}", f"{header[col-2]} | {row[col]}"))
    return records, [] if len(records) == 3 else ["One or more reported state counts were missing"]


def published_pdf_fields(pdf, front):
    """Dispatch by verified cover text and verify the body clause or table schema."""
    cover = " ".join(front)
    if "AGRICULTURAL STATISTICS AT A GLANCE" in cover.upper():
        return des_wheat(pdf)
    if all(word in cover.upper() for word in ("PM-KISAN", "OPERATIONAL GUIDELINES")):
        records = []
        revision = re.search(r"REVISED AS ON (\d{2}\.\d{2}\.\d{4})", cover, re.I)
        issued = datetime.strptime(revision.group(1), "%d.%m.%Y").date().isoformat() if revision else MISSING
        for page, content in enumerate(front, 1):
            match = re.search(r"amount of Rs\.\s*([\d,]+)/- per year", content, re.I)
            if match:
                records.append(observation(
                    "pmkisan_annual_assistance", match.group(1).replace(",", ""), "INR",
                    f"page:{page}/char:{match.start(1)}-{match.end(1)}", match.group(0),
                    location="India", period=issued, extraction_scope="annual assistance stated in published guideline",
                ))
                break
        return records, [] if records and revision else ["Could not verify the annual assistance and revision date"]
    return None


def des_wheat(pdf):
    for page_number, page in enumerate(pdf.pages[60:110], 61):
        raw = page.extract_text() or ""
        page_text = text(raw)
        if "Table 2.5 (b): Wheat: Area, Production and Yield during" not in page_text:
            continue
        years = re.search(r"Yield during (\d{4}-\d{2}) and (\d{4}-\d{2})", page_text)
        units = ("Area - Million Hectares", "Production - Million Tonnes", "Yield - Kg./Hectare")
        if not years or not all(unit in page_text for unit in units):
            return [], ["Wheat major-state table years or units could not be verified"]
        matches = [(line, row.split()) for line, row in enumerate(raw.splitlines(), 1)
                   if re.match(r"\s*Madhya Pradesh\s", row, re.I)]
        if len(matches) != 1:
            return [], ["Wheat table has no unique Madhya Pradesh row"]
        line, cells = matches[0]
        values = cells[2:]
        if len(values) != 11 or not all(re.fullmatch(r"\d+(?:\.\d+)?", value) for value in values):
            return [], ["Unexpected wheat major-state column layout"]
        records = []
        for year, start in zip(years.groups(), (0, 5)):
            for variable, unit, offset in (("area", "million hectares", 0), ("production", "million tonnes", 2),
                                            ("yield", "kg/hectare", 4)):
                index = start + offset
                records.append(dict(
                    observation(variable, values[index], unit, f"page:{page_number}/line:{line}/data-column:{index+1}",
                                " ".join(cells), period=year, kind="decimal", extraction_scope="Wheat Table 2.5(b)"),
                    crop="wheat",
                ))
        return records, []
    return [], ["Could not resolve the wheat major-state table in this report edition"]


def des_pdf_type(page_text):
    if "Area, Production & Yield - Reports Major Contributing District" in page_text:
        return "ranking"
    if "Crop Production Statistics" in page_text and "State/Crop/District" in page_text:
        return "apy"
    return None


def des_district_tables(tables, page_text, report_type):
    """Use original DES cells and published units, retaining page and cell locators."""
    if report_type == "ranking":
        crop_title = re.search(r"(?m)^\s*Crop:\s*([^\n]+)", page_text)
        published = tables[0]["rows"] if tables else []
        if (not crop_title or len(published) < 2 or published[0][:3] != ["S.No.", "State", "District"]
                or published[1][-1] != "Production (Tonnes)"):
            return [], ["DES production ranking headers could not be verified"]
        period = financial_year(published[0][-1])
        records = []
        for table in tables:
            for row, cells in enumerate(table["rows"], 1):
                if len(cells) != 4 or not cells[0].isdigit() or cells[1] != "Madhya Pradesh":
                    continue
                if period and cells[2] and re.fullmatch(r"\d[\d,]*(?:\.\d+)?", cells[3]):
                    records.append(district_cell(table, row, 4, cells, crop_title.group(1), cells[2], period,
                                                 "production", "tonne", source_rank=int(cells[0])))
                else:
                    return records, ["A Madhya Pradesh production ranking row had incomplete fields"]
        return records, []

    expected = ["State/Crop/District", "Year", "Season", "Area (Hectare)", "Production (Tonne)", "Yield (Tonne/Hectare)"]
    if not tables or tables[0]["rows"][0] != expected:
        return [], ["DES APY columns or units could not be verified"]
    from .normalization import crop

    district_line = re.compile(r"\d+\.\s+(.+)")
    state, crop_label = "", ""
    records, missing = [], 0
    for table in tables:
        for row, cells in enumerate(table["rows"], 1):
            if len(cells) != 6 or cells == expected or cells[0].startswith("Total"):
                continue
            name = district_line.fullmatch(cells[0])
            if not any(cells[1:]):
                if name:
                    crop_label = crop(name.group(1))
                else:
                    state, crop_label = cells[0], ""
                continue
            if state != "Madhya Pradesh" or crop_label not in {"wheat", "rice", "chickpea", "soybean", "maize"}:
                continue
            period = financial_year(cells[1])
            if not (name and period and cells[2]):
                missing += 1
                continue
            for col, variable, unit in ((4, "area", "hectare"), (5, "production", "tonne"), (6, "yield", "tonne/hectare")):
                if re.fullmatch(r"\d[\d,]*(?:\.\d+)?", cells[col-1]):
                    records.append(district_cell(table, row, col, cells, crop_label, name.group(1), period,
                                                 variable, unit, season=cells[2].casefold()))
                else:
                    missing += 1
    return records, [f"{missing} APY cells or row identifiers could not be validated"] if missing else []


def financial_year(value):
    match = re.fullmatch(r"(\d{4})\s*-\s*(\d{4})", value)
    if match and int(match.group(2)) == int(match.group(1)) + 1:
        return f"{match.group(1)}-{match.group(2)[-2:]}"
    return None


def district_cell(table, row, col, cells, crop, district, period, variable, unit, **metadata):
    loc = f"page:{table['page']}/table:{table['table']}/row:{row}/col:{col}"
    value = cells[col-1].replace(",", "")
    return dict(observation(variable, value, unit, loc, " | ".join(cells), period=period,
                            location=district, kind="decimal", **metadata), crop=crop)
