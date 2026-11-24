PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sources (
 source TEXT PRIMARY KEY, url TEXT NOT NULL, file_sha256 TEXT NOT NULL, input_path TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
 run_id TEXT PRIMARY KEY, source TEXT NOT NULL REFERENCES sources(source),
 started_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('complete','partial','failed')),
 agent TEXT NOT NULL, error TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
 id INTEGER PRIMARY KEY, source TEXT NOT NULL REFERENCES sources(source),
 source_type TEXT NOT NULL, agent TEXT NOT NULL, run_id TEXT NOT NULL REFERENCES runs(run_id),
 locator TEXT NOT NULL CHECK(length(locator)>0), crop TEXT NOT NULL, location TEXT NOT NULL,
 period TEXT NOT NULL, variable TEXT NOT NULL, value TEXT NOT NULL, unit TEXT NOT NULL,
 validation_status TEXT NOT NULL CHECK(validation_status IN ('valid','invalid')),
 payload TEXT NOT NULL,
 UNIQUE(source,locator,crop,location,period,variable)
);
CREATE TABLE IF NOT EXISTS attempts (
 run_id TEXT PRIMARY KEY REFERENCES runs(run_id), attempted INTEGER NOT NULL,
 inserted INTEGER NOT NULL, duplicates INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS observation_crop_location ON observations(crop,location,period);
CREATE VIEW IF NOT EXISTS district_crop_production AS
SELECT o.location AS district, o.crop, CAST(o.period AS INTEGER) AS year,
       json_extract(o.payload, '$.season') AS season,
       MAX(CASE WHEN o.variable='area' THEN CAST(o.value AS REAL) END) AS hectares,
       MAX(CASE WHEN o.variable='production' THEN CAST(o.value AS REAL) END) AS tonnes,
       MAX(CASE WHEN o.variable='production' THEN o.id END) AS production_id
FROM observations o JOIN sources s USING(source)
WHERE o.validation_status='valid'
  AND s.input_path='data/production/mp_crop_production_2016_2022.csv'
  AND o.variable IN ('area','production')
GROUP BY o.source, o.location, o.crop, o.period, json_extract(o.payload, '$.season')
HAVING COUNT(DISTINCT o.variable)=2 AND COUNT(*)=2;
