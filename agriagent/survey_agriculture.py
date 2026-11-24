"""Extract the scoped agriculture facts represented in the retained survey transcription."""
import re

from .normalization import NA, text

NUMBER = r"\d+(?:\.\d+)?"
YEAR = r"\d{4}-\d{2}"


def extract(pdf, front):
    if not all(value in " ".join(front) for value in ("Economic Survey", "Madhya Pradesh")):
        return None
    for page, body in enumerate(pdf.pages[:15], 1):
        raw = body.extract_text() or ""
        content = text(re.sub(r"(\d{4}-)\s+(?=\d{2}\b)", r"\1", raw))
        if not content.startswith("Agriculture, Food Management & Natural Resources"):
            continue
        clauses = {}
        anchors = list(re.finditer(r"(?<!\S)([1-7])\. (?=[A-Z])", content))
        for i, match in enumerate(anchors):
            end = anchors[i+1].start() if i+1 < len(anchors) else len(content)
            clauses[int(match.group(1))] = (content[match.end():end].strip(), match.end())
        return records_for_clauses(clauses, page)
    return None


def records_for_clauses(clauses, page):
    records = []

    def match(number, pattern):
        content, _ = clauses.get(number, ("", 0))
        return re.search(pattern, content, re.I)

    def add(number, found, value_group, variable, unit, *, crop=NA, period=NA, qualifier=""):
        value = found.group(value_group)
        base = clauses[number][1]
        start, end = found.span(value_group)
        records.append(dict(crop=crop, location="Madhya Pradesh", period=period, variable=variable,
                            value=value, unit=unit, value_kind="decimal", qualifier=qualifier,
                            locator=f"page:{page}/char:{base+start}-{base+end}", origin_locator=f"page:{page}",
                            evidence=found.group(), extraction_scope="Selected reported data in the agriculture highlights"))

    wheat = match(1, rf"produced ({NUMBER}) lakh tonnes of wheat in ({YEAR}) \(advance estimates\) as compared to ({NUMBER}) lakh tonnes in ({YEAR})")
    rice = match(1, rf"production of paddy has increased from ({NUMBER}) lakh to ({NUMBER}) lakh tonnes during this period")
    if wheat:
        add(1, wheat, 1, "production", "lakh tonnes", crop="wheat", period=wheat[2], qualifier="advance estimate")
        add(1, wheat, 3, "production", "lakh tonnes", crop="wheat", period=wheat[4], qualifier="comparison year")
        if rice:
            add(1, rice, 2, "production", "lakh tonnes", crop="rice", period=wheat[2], qualifier="same period as preceding wheat comparison")
            add(1, rice, 1, "production", "lakh tonnes", crop="rice", period=wheat[4], qualifier="same period as preceding wheat comparison")
    area = match(2, rf"Compared to the year ({YEAR}),.*?increase of ({NUMBER}) percent in the cropped area during the year ({YEAR})")
    if area:
        add(2, area, 2, "cropped_area_growth", "percent", period=area[3], qualifier=f"compared with {area[1]}")
    production = match(3, rf"Compared to the year ({YEAR}), an increase of ({NUMBER}) percent .*?production of total crops in the year ({YEAR})")
    if production:
        add(3, production, 2, "crop_production_growth", "percent", period=production[3], qualifier=f"compared with {production[1]}")
    insured = match(5, rf"In ({YEAR}), crops of more than ({NUMBER}) lakh farmers were insured")
    if insured:
        add(5, insured, 2, "insured_farmers_lower_bound", "lakh farmers", period=insured[1], qualifier="more than")
    irrigation = match(7, rf"Irrigation capacity has increased by ({NUMBER}) percent.*?more than ({NUMBER}) lakh hectare \(in the year (\d{{4}})\).*?target is to increase it to ({NUMBER}) lakh hectare by the year (\d{{4}})")
    if irrigation:
        add(7, irrigation, 1, "irrigation_capacity_growth", "percent", qualifier="period not explicit in same clause")
        add(7, irrigation, 2, "irrigation_capacity_lower_bound", "lakh hectare", period=irrigation[3], qualifier="more than")
        add(7, irrigation, 4, "irrigation_capacity_target", "lakh hectare", period=irrigation[5], qualifier="target; not observed")
    return records, [] if len(records) == 10 else ["Some fields in the survey agriculture scope could not be verified"]
