-- SQLite
SELECT
    location,
    variable,
    value,
    unit,
    locator,
    validation_status
FROM observations
WHERE run_id = 'b8957083-3b1f-4598-b06e-31c5b6144a23'
ORDER BY location, variable;