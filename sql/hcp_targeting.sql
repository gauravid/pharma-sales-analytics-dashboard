DROP VIEW IF EXISTS vw_hcp_targeting;

CREATE VIEW vw_hcp_targeting AS
WITH constants AS (
    SELECT 
        150.0 AS price_per_trx,
        '2025-12-31' AS analysis_end_date
),
hcp_call_stats AS (
    -- Calculate total completed calls and last visit date for each HCP
    SELECT
        hcp_id,
        COUNT(CASE WHEN call_status = 'Completed' AND brand_promoted = 'Apexacare' THEN 1 END) AS completed_apex_calls,
        MAX(call_date) AS last_visit_date
    FROM vw_calls
    WHERE hcp_id IS NOT NULL
    GROUP BY hcp_id
),
hcp_rx_stats AS (
    -- Calculate total NRx and TRx for Apexacare and Competitors per HCP
    SELECT
        hcp_id,
        SUM(CASE WHEN brand = 'Apexacare' THEN trx ELSE 0 END) AS apex_trx,
        SUM(trx) AS total_category_trx
    FROM vw_prescriptions
    GROUP BY hcp_id
),
regional_share AS (
    -- Calculate the average Apexacare market share for each region
    SELECT
        region,
        ROUND((CAST(SUM(CASE WHEN brand = 'Apexacare' THEN trx ELSE 0 END) AS REAL) / NULLIF(SUM(trx), 0)) * 100, 2) AS regional_avg_share_pct
    FROM vw_prescriptions
    GROUP BY region
),
territory_call_counts AS (
    -- Get list of all HCPs and their call counts to calculate medians
    SELECT
        h.hcp_id,
        h.territory_id,
        COALESCE(c.completed_apex_calls, 0) AS call_count
    FROM hcps h
    LEFT JOIN hcp_call_stats c ON h.hcp_id = c.hcp_id
),
territory_medians AS (
    -- Calculate median call frequency per territory using ROW_NUMBER()
    WITH ranked_calls AS (
        SELECT
            hcp_id,
            territory_id,
            call_count,
            ROW_NUMBER() OVER (PARTITION BY territory_id ORDER BY call_count) AS row_num,
            COUNT(*) OVER (PARTITION BY territory_id) AS total_count
        FROM territory_call_counts
    )
    SELECT
        territory_id,
        -- Take the call count at the middle row as the median
        AVG(call_count) AS territory_median_calls
    FROM ranked_calls
    WHERE row_num IN (total_count / 2, (total_count / 2) + 1)
    GROUP BY territory_id
),
hcp_detailed_list AS (
    -- Combine HCP info, call stats, Rx stats, and territory medians
    SELECT
        h.hcp_id,
        h.hcp_name,
        h.specialty,
        h.prescribing_decile,
        h.territory_id,
        t.territory_name,
        t.region,
        r.rep_id,
        r.rep_name,
        COALESCE(cs.completed_apex_calls, 0) AS completed_calls_count,
        ROUND(tm.territory_median_calls, 1) AS territory_median_calls,
        cs.last_visit_date,
        COALESCE(rx.apex_trx, 0) AS apex_trx,
        COALESCE(rx.total_category_trx, 0) AS total_category_trx,
        -- HCP Brand Share %
        ROUND((CAST(COALESCE(rx.apex_trx, 0) AS REAL) / NULLIF(COALESCE(rx.total_category_trx, 0), 0)) * 100, 2) AS hcp_share_pct,
        rs.regional_avg_share_pct
    FROM hcps h
    JOIN territories t ON h.territory_id = t.territory_id
    JOIN reps r ON r.territory_id = t.territory_id
    JOIN territory_medians tm ON t.territory_id = tm.territory_id
    LEFT JOIN hcp_call_stats cs ON h.hcp_id = cs.hcp_id
    LEFT JOIN hcp_rx_stats rx ON h.hcp_id = rx.hcp_id
    JOIN regional_share rs ON t.region = rs.region
)
SELECT
    hcp_id,
    hcp_name,
    specialty,
    prescribing_decile,
    territory_id,
    territory_name,
    region,
    rep_id,
    rep_name,
    completed_calls_count,
    territory_median_calls,
    last_visit_date,
    
    -- Days since last visit (relative to the end of the analysis window)
    CAST(
        JULIANDAY((SELECT analysis_end_date FROM constants)) - JULIANDAY(last_visit_date) 
        AS INTEGER
    ) AS days_since_last_visit,
    
    total_category_trx,
    apex_trx,
    hcp_share_pct,
    regional_avg_share_pct,
    
    -- 1. Estimated Lost Prescriptions (TRx)
    -- If HCP share is below regional average, calculate what they would have prescribed at regional average share
    CAST(
        MAX(0, (regional_avg_share_pct - hcp_share_pct) / 100.0 * total_category_trx) 
        AS INTEGER
    ) AS est_lost_trx,
    
    -- 2. Potential Revenue = Lost TRx * $150
    ROUND(
        MAX(0, (regional_avg_share_pct - hcp_share_pct) / 100.0 * total_category_trx) * (SELECT price_per_trx FROM constants), 
        2
    ) AS potential_lost_revenue,
    
    -- 3. Suggested Calls Next Month to catch up to the territory median frequency
    -- If they are below median, we suggest visits to close the gap over the next quarter (monthly rate)
    CAST(
        CEIL(MAX(0, territory_median_calls - completed_calls_count) / 12.0) 
        AS INTEGER
    ) AS suggested_calls_next_month
FROM hcp_detailed_list
-- Filter for High-Value (Deciles 9 & 10) and Underserved (calls below territory median)
WHERE prescribing_decile >= 9 
  AND completed_calls_count < territory_median_calls;
