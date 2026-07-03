DROP VIEW IF EXISTS vw_root_cause;

CREATE VIEW vw_root_cause AS
WITH constants AS (
    SELECT '2025-12-31' AS analysis_end_date
),
regional_sales AS (
    -- Aggregate actual sales and targets by region
    SELECT
        region,
        SUM(actual_sales) AS total_actual_sales,
        SUM(target_sales) AS total_target_sales,
        ROUND((SUM(actual_sales) / NULLIF(SUM(target_sales), 0)) * 100, 2) AS sales_attainment_pct
    FROM vw_sales_targets
    GROUP BY region
),
regional_calls AS (
    -- Calculate call adherence and Share of Voice at the regional level
    SELECT
        region,
        SUM(CASE WHEN planned_vs_actual = 'Planned' THEN 1 ELSE 0 END) AS planned_calls,
        SUM(CASE WHEN planned_vs_actual = 'Planned' AND call_status = 'Completed' THEN 1 ELSE 0 END) AS completed_planned_calls,
        SUM(CASE WHEN call_status = 'Completed' AND brand_promoted = 'Apexacare' THEN 1 ELSE 0 END) AS completed_apex_calls,
        SUM(est_market_calls_monthly) AS total_est_market_calls
    FROM vw_calls
    GROUP BY region
),
regional_tenure AS (
    -- Calculate average rep tenure in days
    SELECT
        t.region,
        ROUND(AVG(JULIANDAY((SELECT analysis_end_date FROM constants)) - JULIANDAY(r.hire_date)), 1) AS avg_rep_tenure_days
    FROM reps r
    JOIN territories t ON r.territory_id = t.territory_id
    GROUP BY t.region
),
regional_rx AS (
    -- Calculate market share and total volume
    SELECT
        region,
        SUM(CASE WHEN brand = 'Apexacare' THEN trx ELSE 0 END) AS apex_trx,
        SUM(trx) AS total_market_trx,
        ROUND((CAST(SUM(CASE WHEN brand = 'Apexacare' THEN trx ELSE 0 END) AS REAL) / NULLIF(SUM(trx), 0)) * 100, 2) AS market_share_pct
    FROM vw_prescriptions
    GROUP BY region
),
regional_hcp_coverage AS (
    -- Calculate the HCP coverage gap: % of High-Decile HCPs (8-10) who received 0 completed calls
    SELECT
        t.region,
        COUNT(h.hcp_id) AS total_high_value_hcps,
        SUM(CASE WHEN COALESCE(c.completed_calls, 0) = 0 THEN 1 ELSE 0 END) AS uncalled_high_value_hcps
    FROM hcps h
    JOIN territories t ON h.territory_id = t.territory_id
    LEFT JOIN (
        -- Count completed calls per HCP
        SELECT hcp_id, COUNT(*) AS completed_calls
        FROM vw_calls
        WHERE call_status = 'Completed'
        GROUP BY hcp_id
    ) c ON h.hcp_id = c.hcp_id
    WHERE h.prescribing_decile >= 8
    GROUP BY t.region
)
SELECT
    rs.region,
    rs.total_actual_sales,
    rs.total_target_sales,
    rs.sales_attainment_pct,
    
    -- Call Adherence % = (Completed Planned / Total Planned) * 100
    ROUND(
        (CAST(rc.completed_planned_calls AS REAL) / NULLIF(rc.planned_calls, 0)) * 100, 
        2
    ) AS call_adherence_pct,
    
    -- Share of Voice % = (Apexacare Calls / Est. Market Calls) * 100
    ROUND(
        (CAST(rc.completed_apex_calls AS REAL) / NULLIF(rc.total_est_market_calls, 0)) * 100, 
        2
    ) AS share_of_voice_pct,
    
    rx.market_share_pct,
    rt.avg_rep_tenure_days,
    
    -- HCP Coverage Gap % = (Uncalled High-Value HCPs / Total High-Value HCPs) * 100
    ROUND(
        (CAST(rhc.uncalled_high_value_hcps AS REAL) / NULLIF(rhc.total_high_value_hcps, 0)) * 100, 
        2
    ) AS hcp_coverage_gap_pct,
    
    -- Opportunity Gap = Potential Sales - Actual Sales (Summed for the region)
    -- We can calculate this by summing up the gaps from our territory opportunity view
    (
        SELECT ROUND(SUM(opportunity_gap), 2) 
        FROM vw_territory_opportunity 
        WHERE vw_territory_opportunity.region = rs.region
    ) AS regional_opportunity_gap
FROM regional_sales rs
JOIN regional_calls rc ON rs.region = rc.region
JOIN regional_tenure rt ON rs.region = rt.region
JOIN regional_rx rx ON rs.region = rx.region
JOIN regional_hcp_coverage rhc ON rs.region = rhc.region;
