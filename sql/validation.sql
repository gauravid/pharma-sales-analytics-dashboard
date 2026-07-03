-- 1. Run Integrity and Business Rule Checks
SELECT 'DATA INTEGRITY & KPI VALIDATION REPORT' AS validation_run;

SELECT 
    'PK_NULL_CHECK_TERRITORIES' AS check_name,
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of NULL primary keys in territories: ' || COUNT(*) AS details
FROM territories WHERE territory_id IS NULL

UNION ALL

SELECT 
    'PK_NULL_CHECK_REPS',
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of NULL primary keys in reps: ' || COUNT(*)
FROM reps WHERE rep_id IS NULL

UNION ALL

SELECT 
    'PK_NULL_CHECK_HCPS',
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of NULL primary keys in hcps: ' || COUNT(*)
FROM hcps WHERE hcp_id IS NULL

UNION ALL

SELECT 
    'DUPLICATE_TERRITORY_IDS',
    CASE WHEN MAX(occurrences) = 1 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Max occurrences of a territory_id: ' || COALESCE(MAX(occurrences), 0)
FROM (
    SELECT territory_id, COUNT(*) AS occurrences 
    FROM territories 
    GROUP BY territory_id
)

UNION ALL

SELECT 
    'COMPLETED_PLANNED_CALLS_LIMIT',
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of records where completed planned calls > planned calls: ' || COUNT(*)
FROM vw_call_adherence
WHERE completed_planned_calls > planned_calls

UNION ALL

SELECT 
    'ADHERENCE_BOUNDS_CHECK',
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of records where adherence is out of 0-100 bounds: ' || COUNT(*)
FROM vw_call_adherence
WHERE adherence_pct < 0 OR adherence_pct > 100

UNION ALL

SELECT 
    'FINANCIAL_NEGATIVES_CHECK',
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of records with negative sales or targets: ' || COUNT(*)
FROM sales_targets
WHERE actual_sales < 0 OR target_sales < 0

UNION ALL

SELECT 
    'ORPHANED_REPS_CHECK',
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of reps assigned to non-existent territories: ' || COUNT(*)
FROM reps 
WHERE territory_id NOT IN (SELECT territory_id FROM territories)

UNION ALL

SELECT 
    'ORPHANED_HCPS_CHECK',
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of HCPs assigned to non-existent territories: ' || COUNT(*)
FROM hcps 
WHERE territory_id NOT IN (SELECT territory_id FROM territories)

UNION ALL

SELECT 
    'ORPHANED_PRESCRIPTIONS_CHECK',
    CASE WHEN COUNT(*) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    'Count of prescriptions for non-existent HCPs: ' || COUNT(*)
FROM prescriptions 
WHERE hcp_id NOT IN (SELECT hcp_id FROM hcps);
