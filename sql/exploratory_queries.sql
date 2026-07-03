/*
----------------------------------------------------
Project:
Sales Force Effectiveness Analytics

Author:
Gauravi

Purpose:
Perform a comprehensive data quality audit and exploratory 
queries on the SFE database, identifying anomalies.

Created:
July 2026

Dependencies:
territories, reps, hcps, calls, prescriptions, sales_targets

Outputs:
Audit results printed in the runner log
----------------------------------------------------
*/

-- 1. Row Counts for All Tables
SELECT '1. Row Counts' AS audit_step;
SELECT 'territories' AS table_name, COUNT(*) AS row_count FROM territories
UNION ALL
SELECT 'reps', COUNT(*) FROM reps
UNION ALL
SELECT 'hcps', COUNT(*) FROM hcps
UNION ALL
SELECT 'calls', COUNT(*) FROM calls
UNION ALL
SELECT 'prescriptions', COUNT(*) FROM prescriptions
UNION ALL
SELECT 'sales_targets', COUNT(*) FROM sales_targets;

-- 2. Date Range Coverage
SELECT '2. Date Ranges' AS audit_step;
SELECT 
    'calls' AS table_name, 
    MIN(call_date) AS min_date, 
    MAX(call_date) AS max_date 
FROM calls WHERE call_date IS NOT NULL
UNION ALL
SELECT 
    'prescriptions', 
    MIN(month_id) || '-01', 
    MAX(month_id) || '-31' 
FROM prescriptions
UNION ALL
SELECT 
    'sales_targets', 
    MIN(month_id) || '-01', 
    MAX(month_id) || '-31' 
FROM sales_targets;

-- 3. Distinct Business Entity Counts
SELECT '3. Distinct Entity Counts' AS audit_step;
SELECT 
    COUNT(DISTINCT territory_id) AS distinct_territories,
    (SELECT COUNT(DISTINCT rep_id) FROM reps) AS distinct_reps,
    (SELECT COUNT(DISTINCT hcp_id) FROM hcps) AS distinct_hcps,
    (SELECT COUNT(DISTINCT brand) FROM prescriptions) AS distinct_brands
FROM territories;

-- 4. Duplicate ID Check (HCP Master CRM duplicates)
-- This flags duplicate names & specialties which suggest CRM entry errors.
SELECT '4. Duplicate HCP Profiles' AS audit_step;
SELECT hcp_name, specialty, COUNT(*) AS occurrences
FROM hcps
GROUP BY hcp_name, specialty
HAVING COUNT(*) > 1;

-- 5. Orphaned Records / Missing Foreign Keys
SELECT '5. Orphaned Records Check' AS audit_step;
SELECT 
    'calls_without_hcp' AS issue_type, 
    COUNT(*) AS issue_count 
FROM calls 
WHERE hcp_id IS NOT NULL AND hcp_id NOT IN (SELECT hcp_id FROM hcps)
UNION ALL
SELECT 
    'calls_without_rep', 
    COUNT(*) 
FROM calls 
WHERE rep_id NOT IN (SELECT rep_id FROM reps)
UNION ALL
SELECT 
    'prescriptions_without_hcp', 
    COUNT(*) 
FROM prescriptions 
WHERE hcp_id NOT IN (SELECT hcp_id FROM hcps)
UNION ALL
SELECT 
    'reps_without_territory', 
    COUNT(*) 
FROM reps 
WHERE territory_id NOT IN (SELECT territory_id FROM territories);

-- 6. Negative Sales or Target Values
SELECT '6. Financial Anomaly Check' AS audit_step;
SELECT 
    territory_id, 
    month_id, 
    actual_sales, 
    target_sales 
FROM sales_targets 
WHERE actual_sales < 0 OR target_sales < 0;

-- 7. Invalid Dates and Out-of-Period Calls
-- Checks for calls outside our analysis window (Jan 1, 2025 to Dec 31, 2025)
SELECT '7. Out-of-Period Calls' AS audit_step;
SELECT COUNT(*) AS out_of_period_calls_count
FROM calls
WHERE call_date IS NOT NULL 
  AND (call_date < '2025-01-01' OR call_date > '2025-12-31');

-- 8. Null Fields Audit in CRM Calls (Seeded Anomaly check)
SELECT '8. CRM Call Nulls Audit' AS audit_step;
SELECT 
    COUNT(*) - COUNT(call_date) AS null_dates,
    COUNT(*) - COUNT(hcp_id) AS null_hcp_ids,
    COUNT(*) - COUNT(call_status) AS null_statuses
FROM calls;
