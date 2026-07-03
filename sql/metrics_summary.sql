DROP VIEW IF EXISTS vw_metrics_summary;

CREATE VIEW vw_metrics_summary AS
SELECT 
    'Total Sales (USD)' AS kpi_name, 
    ROUND(SUM(actual_sales), 2) AS kpi_value 
FROM sales_targets

UNION ALL

SELECT 
    'Total Apexacare TRx', 
    SUM(trx) 
FROM prescriptions 
WHERE brand = 'Apexacare'

UNION ALL

SELECT 
    'Total Apexacare NRx', 
    SUM(nrx) 
FROM prescriptions 
WHERE brand = 'Apexacare'

UNION ALL

SELECT 
    'Overall Call Adherence %', 
    ROUND((CAST(SUM(completed_planned_calls) AS REAL) / SUM(planned_calls)) * 100, 2)
FROM vw_call_adherence

UNION ALL

SELECT 
    'Overall Share of Voice %', 
    ROUND((CAST(SUM(completed_apex_calls) AS REAL) / SUM(est_market_calls_monthly)) * 100, 2)
FROM vw_market_share

UNION ALL

SELECT 
    'Average Monthly Opportunity Gap (USD)', 
    ROUND(SUM(opportunity_gap) / 12.0, 2)
FROM vw_territory_opportunity

UNION ALL

SELECT 
    'Total Sales Representatives', 
    COUNT(*) 
FROM reps

UNION ALL

SELECT 
    'Total HCPs (CRM Master)', 
    COUNT(DISTINCT hcp_id) 
FROM hcps

UNION ALL

SELECT 
    'Covered HCPs (>= 1 Visit)', 
    COUNT(DISTINCT hcp_id) 
FROM vw_calls 
WHERE call_status = 'Completed' AND hcp_id IS NOT NULL

UNION ALL

SELECT 
    'High-Value Underserved HCPs (Decile 9-10)', 
    COUNT(DISTINCT hcp_id) 
FROM vw_hcp_targeting;
