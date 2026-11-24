"""Read-only Phase 3 query catalogue for the release database."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Query:
    category: str
    title: str
    sql: str


QUERIES = {
    "q01": Query("spatial", "Five largest district wheat producers in 2022", """
        SELECT district, ROUND(tonnes, 2) AS tonnes
        FROM district_crop_production WHERE crop='wheat' AND season='rabi' AND year=2022
        ORDER BY tonnes DESC, district LIMIT 5
    """),
    "q02": Query("spatial", "Five highest observed district soybean yields in 2022", """
        SELECT district, ROUND(tonnes/hectares, 3) AS tonnes_per_ha
        FROM district_crop_production
        WHERE crop='soybean' AND season='kharif' AND year=2022 AND hectares>0
        ORDER BY tonnes/hectares DESC, district LIMIT 5
    """),
    "q03": Query("temporal", "Annual observed wheat production and district coverage", """
        SELECT year, ROUND(SUM(tonnes), 2) AS tonnes, COUNT(*) AS districts
        FROM district_crop_production WHERE crop='wheat' AND season='rabi'
        GROUP BY year ORDER BY year
    """),
    "q04": Query("temporal", "Sehore wheat yield by year", """
        SELECT year, ROUND(tonnes/hectares, 3) AS tonnes_per_ha
        FROM district_crop_production
        WHERE district='sehore' AND crop='wheat' AND season='rabi' AND hectares>0
        ORDER BY year
    """),
    "q05": Query("provenance", "Original row and field for Sehore's 2022 wheat production", """
        SELECT p.district, p.year, p.tonnes, s.url AS source_url,
               json_extract(o.payload, '$.origin_locator') AS original_locator,
               s.input_path AS local_snapshot, o.locator AS local_locator, s.file_sha256
        FROM district_crop_production p
        JOIN observations o ON o.id=p.production_id JOIN sources s USING(source)
        WHERE p.district='sehore' AND p.crop='wheat' AND p.season='rabi' AND p.year=2022
    """),
    "q06": Query("comparison", "Area-weighted Kharif yields for each crop in 2022", """
        SELECT crop, ROUND(SUM(tonnes)/SUM(hectares), 3) AS tonnes_per_ha, COUNT(*) AS districts
        FROM district_crop_production WHERE season='kharif' AND year=2022 AND hectares>0
        GROUP BY crop ORDER BY crop
    """),
    "q07": Query("spatial", "Largest district changes in Rabi wheat output, 2016 to 2022", """
        SELECT a.district, ROUND(b.tonnes-a.tonnes, 2) AS change_tonnes
        FROM district_crop_production a
        JOIN district_crop_production b USING(district, crop, season)
        WHERE a.year=2016 AND b.year=2022 AND a.crop='wheat' AND a.season='rabi'
        ORDER BY b.tonnes-a.tonnes DESC, a.district LIMIT 5
    """),
    "q08": Query("comparison", "Districts where 2022 Kharif maize yield exceeded soybean yield", """
        SELECT COUNT(*) AS maize_higher,
          (SELECT COUNT(*) FROM district_crop_production c
             JOIN district_crop_production d USING(district, year, season)
             WHERE c.year=2022 AND c.season='kharif' AND c.crop='maize' AND d.crop='soybean'
               AND c.hectares>0 AND d.hectares>0) AS paired_districts
        FROM district_crop_production a JOIN district_crop_production b USING(district, year, season)
        WHERE a.year=2022 AND a.season='kharif' AND a.crop='maize' AND b.crop='soybean'
          AND a.hectares>0 AND b.hectares>0 AND a.tonnes/a.hectares>b.tonnes/b.hectares
    """),
    "q09": Query("coverage", "Number of districts with both area and production, by crop and year", """
        SELECT crop, year, COUNT(DISTINCT district) AS districts
        FROM district_crop_production GROUP BY crop, year ORDER BY crop, year
    """),
    "q10": Query("provenance", "Economic Survey wheat and rice estimates and PDF page", """
        SELECT o.crop, o.period, CAST(o.value AS REAL) AS lakh_tonnes,
               json_extract(o.payload,'$.origin_source') AS pdf,
               json_extract(o.payload,'$.origin_locator') AS page
        FROM observations o JOIN sources s USING(source)
        WHERE s.input_path='data/derived/survey_agriculture_transcription.csv'
          AND o.variable='production' AND o.crop IN ('rice','wheat') AND o.unit='lakh tonnes'
          AND o.validation_status='valid'
        ORDER BY o.crop, o.period
    """),
}


def execute(db, code):
    cursor = db.execute(QUERIES[code].sql)
    columns = [item[0] for item in cursor.description]
    return [dict(zip(columns, row)) for row in cursor]
