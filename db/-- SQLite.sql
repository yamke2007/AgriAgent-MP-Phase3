SELECT
    COUNT(*) AS total_observations,
    SUM(CASE WHEN validation_status = 'valid' THEN 1 ELSE 0 END) AS valid_records,
    SUM(CASE WHEN validation_status = 'invalid' THEN 1 ELSE 0 END) AS invalid_records,
    COUNT(DISTINCT location) AS districts,
    CASE
        WHEN COUNT(*) = 162
         AND SUM(CASE WHEN validation_status = 'valid' THEN 1 ELSE 0 END) = 162
         AND SUM(CASE WHEN validation_status = 'invalid' THEN 1 ELSE 0 END) = 0
        THEN 'VALIDATED'
        ELSE 'CHECK REQUIRED'
    END AS final_status
FROM observations
WHERE run_id = 'b56e3e3d-f2e1-422f-847d-4876cc6eff92';