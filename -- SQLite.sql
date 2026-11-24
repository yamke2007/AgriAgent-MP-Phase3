-- SQLite
SELECT
    location,
    variable,
    value,
    locator,
    run_id,
    validation_status
FROM observations
WHERE LOWER(location) = 'datia'
LIMIT 10;