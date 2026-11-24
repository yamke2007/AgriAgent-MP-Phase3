"""Read the ruled first-page forecast table of image-only IMD district bulletins."""
import re
from datetime import date
from decimal import Decimal

from .public_sources import observation

FIELDS = {
    "rainfall": ("forecast_rainfall", "mm"),
    "tmax": ("forecast_daily_max_temperature", "degree C"),
    "tmin": ("forecast_daily_min_temperature", "degree C"),
}


def line_centers(values):
    from itertools import groupby

    return [
        (run[0] + run[-1]) // 2
        for _, group in groupby(enumerate(values), key=lambda item: item[1] - item[0])
        if (run := [int(position) for _, position in group])
    ]


def locate_grid(image):
    import numpy as np

    dark = np.asarray(image.convert("L")) < 85
    height, width = dark.shape
    start = round(height * 0.20)
    region = dark[start:round(height * 0.48)]
    rows = line_centers(np.flatnonzero(region.sum(axis=1) > width * 0.55) + start)
    if len(rows) < 5:
        return None
    typical = float(np.median(np.diff(rows)))
    groups = np.split(rows, np.flatnonzero(np.abs(np.diff(rows) - typical) > typical * 0.22) + 1)
    rows = max(groups, key=len)
    if len(rows) < 5 or typical < height * 0.008:
        return None
    body = dark[rows[0]:rows[-1]]
    columns = line_centers(np.flatnonzero(body.sum(axis=0) > len(body) * 0.77))
    if len(columns) != 7 or columns[-1] - columns[0] < width * 0.55:
        return None
    return list(map(int, rows)), columns


def header(image, top):
    import pytesseract

    chunk = image.crop((0, 0, image.width, top))
    raw = pytesseract.image_to_string(chunk, lang="eng", config="--psm 6", timeout=8)
    content = " ".join(raw.split())
    if not all(label in content.casefold() for label in ("agromet advisory bulletin", "madhya pradesh")):
        return None
    match = re.search(r"Weather Forecast of District ([A-Z ]+) \(Madhya Pradesh\) Issued On\s*:\s*(\d{4}-\d{2}-\d{2})",
                      content, re.I)
    if not match:
        return None
    district, issued = match.groups()
    try:
        date.fromisoformat(issued)
    except ValueError:
        return None
    return district, issued


def read_cells(image, grid):
    """Remove the grid and associate OCR words with the original cell positions."""
    from PIL import Image
    import pytesseract

    rows, columns = grid
    padding = 20
    height = max(b - a for a, b in zip(rows, rows[1:])) + padding
    columns_out = [x - columns[0] + i * padding for i, x in enumerate(columns)]
    canvas = Image.new("L", (columns_out[-1], height * 4), "white")
    margin = max(4, int(image.width * .004))
    for row in range(4):
        for col in range(6):
            roi = image.crop((columns[col] + margin, rows[row] + margin,
                              columns[col+1] - margin, rows[row+1] - margin)).convert("L")
            canvas.paste(roi, (columns_out[col] + padding // 2, row * height + padding // 2))
    data = pytesseract.image_to_data(canvas, lang="eng", config="--psm 6",
                                    output_type=pytesseract.Output.DICT, timeout=8)
    result = [[[] for _ in range(6)] for _ in range(4)]
    for i, word in enumerate(data["text"]):
        if not word.strip():
            continue
        row = (data["top"][i] + data["height"][i] // 2) // height
        x = data["left"][i] + data["width"][i] // 2
        col = next((c for c in range(6) if columns_out[c] <= x < columns_out[c+1]), None)
        if 0 <= row < 4 and col is not None:
            result[row][col].append(word.strip())
    return [[" ".join(cell) for cell in row] for row in result]


def observations(rows, district, issued, page):
    days = rows[0][1:]
    try:
        parsed = [date.fromisoformat(day) for day in days]
        issued_day = date.fromisoformat(issued)
        valid = len(parsed) == 5 and all((day - issued_day).days == i for i, day in enumerate(parsed, 1))
    except ValueError:
        valid = False
    if not valid:
        return [], ["IMD forecast-day headers were missing or inconsistent with the issued date"]
    result = []
    for ri, row in enumerate(rows[1:], 2):
        label = re.sub(r"[^a-z]", "", row[0].casefold())
        field = next((key for key in FIELDS if label.startswith(key)), None)
        if field is None:
            continue
        variable, unit = FIELDS[field]
        for col, (day, value) in enumerate(zip(days, row[1:]), 2):
            if re.fullmatch(r"-?\d+(?:\.\d+)?", value) and (
                (unit == "degree C" and -100 <= Decimal(value) <= 70)
                or (unit == "mm" and 0 <= Decimal(value) <= 2000)
            ):
                result.append(observation(
                    variable, value, unit, f"page:{page}/ocr/forecast/row:{ri}/col:{col}",
                    f"{row[0]} | {day} | {value}", location=district, period=day, kind="decimal",
                    issued_on=issued, qualifier="Forecast, not observed weather",
                ))
    return result, [] if len(result) == 15 else ["One or more of the fifteen IMD forecast cells could not be read"]
