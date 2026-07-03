DROP VIEW IF EXISTS vw_market_share;
DROP VIEW IF EXISTS vw_territory_opportunity;

-- ==========================================
-- 1. MARKET SHARE & SHARE OF VOICE VIEW
-- ==========================================
CREATE VIEW vw_market_share AS
WITH constants AS (
    SELECT '2025' AS analysis_year
),
monthly_market_rx AS (
    -- Aggregate NRx and TRx by brand and territory
    SELECT
        month_id,
        region,
        territory_id,
        territory_name,
        rep_id,
        rep_name,
        SUM(CASE WHEN brand = 'Apexacare' THEN nrx ELSE 0 END) AS apex_nrx,
        SUM(CASE WHEN brand = 'Apexacare' THEN trx ELSE 0 END) AS apex_trx,
        SUM(nrx) AS total_market_nrx,
        SUM(trx) AS total_market_trx
    FROM vw_prescriptions
    GROUP BY month_id, region, territory_id, territory_name, rep_id, rep_name
),
monthly_calls AS (
    -- Count completed calls promoting Apexacare
    SELECT
        month_id,
        territory_id,
        SUM(CASE WHEN call_status = 'Completed' AND brand_promoted = 'Apexacare' THEN 1 ELSE 0 END) AS completed_apex_calls
    FROM vw_calls
    GROUP BY month_id, territory_id
),
monthly_sales AS (
    -- Get sales and targets
    SELECT
        month_id,
        territory_id,
        actual_sales,
        target_sales
    FROM vw_sales_targets
),
consolidated_metrics AS (
    -- Combine Rx, Calls, and Sales
    SELECT
        m.month_id,
        m.region,
        m.territory_id,
        m.territory_name,
        m.rep_id,
        m.rep_name,
        m.apex_nrx,
        m.apex_trx,
        m.total_market_nrx,
        m.total_market_trx,
        COALESCE(c.completed_apex_calls, 0) AS completed_apex_calls,
        t.est_market_calls_monthly,
        s.actual_sales,
        s.target_sales
    FROM monthly_market_rx m
    JOIN territories t ON m.territory_id = t.territory_id
    LEFT JOIN monthly_calls c ON m.month_id = c.month_id AND m.territory_id = c.territory_id
    LEFT JOIN monthly_sales s ON m.month_id = s.month_id AND m.territory_id = s.territory_id
),
lagged_metrics AS (
    -- Calculate lags for MoM changes
    SELECT
        *,
        -- Prior Month Market Share
        LAG(ROUND((CAST(apex_trx AS REAL) / NULLIF(total_market_trx, 0)) * 100, 2), 1) OVER (
            PARTITION BY territory_id ORDER BY month_id
        ) AS prev_market_share,
        -- Prior Month Actual Sales
        LAG(actual_sales, 1) OVER (
            PARTITION BY territory_id ORDER BY month_id
        ) AS prev_actual_sales,
        -- Prior Month Category TRx
        LAG(total_market_trx, 1) OVER (
            PARTITION BY territory_id ORDER BY month_id
        ) AS prev_total_market_trx
    FROM consolidated_metrics
)
SELECT
    month_id,
    region,
    territory_id,
    territory_name,
    rep_id,
    rep_name,
    apex_nrx,
    apex_trx,
    total_market_nrx,
    total_market_trx,
    completed_apex_calls,
    est_market_calls_monthly,
    actual_sales,
    target_sales,
    
    -- 1. Share of Voice % = (Apexacare Calls / Est. Market Calls) * 100
    ROUND(
        (CAST(completed_apex_calls AS REAL) / NULLIF(est_market_calls_monthly, 0)) * 100, 
        2
    ) AS share_of_voice_pct,
    
    -- 2. Brand Market Share % = (Apexacare TRx / Total Market TRx) * 100
    ROUND(
        (CAST(apex_trx AS REAL) / NULLIF(total_market_trx, 0)) * 100, 
        2
    ) AS brand_market_share_pct,
    
    -- 3. Sales Growth %
    ROUND(
        (CAST(actual_sales - prev_actual_sales AS REAL) / NULLIF(prev_actual_sales, 0)) * 100, 
        2
    ) AS sales_growth_pct,
    
    -- 4. Category (Market) Growth %
    ROUND(
        (CAST(total_market_trx - prev_total_market_trx AS REAL) / NULLIF(prev_total_market_trx, 0)) * 100, 
        2
    ) AS category_growth_pct,
    
    -- 5. Share Gain/Loss = Current Market Share - Prior Market Share
    ROUND(
        ROUND((CAST(apex_trx AS REAL) / NULLIF(total_market_trx, 0)) * 100, 2) - COALESCE(prev_market_share, 0),
        2
    ) AS share_gain_loss
FROM lagged_metrics;


-- ==========================================
-- 2. TERRITORY POTENTIAL & OPPORTUNITY VIEW
-- ==========================================
CREATE VIEW vw_territory_opportunity AS
WITH constants AS (
    -- Centralize weights and scaling factor
    SELECT 
        0.50 AS wt_category_vol,
        0.30 AS wt_target_hcps,
        0.20 AS wt_patient_density,
        800.0 AS potential_sales_scalar -- Scaler to convert TPI (0-100) to potential sales in USD
),
territory_tpi AS (
    -- Calculate the Territory Potential Index (TPI) for each territory
    SELECT
        t.territory_id,
        t.territory_name,
        t.region,
        t.category_volume_factor,
        t.target_hcp_count_factor,
        t.patient_volume_proxy,
        -- TPI Score = 50% Category Volume + 30% Target HCPs + 20% Patient Density
        ROUND(
            (c.wt_category_vol * t.category_volume_factor + 
             c.wt_target_hcps * t.target_hcp_count_factor + 
             c.wt_patient_density * t.patient_volume_proxy) * 100, 
            2
        ) AS tpi_score,
        -- Potential Sales in USD = TPI Score * Scalar
        ROUND(
            (c.wt_category_vol * t.category_volume_factor + 
             c.wt_target_hcps * t.target_hcp_count_factor + 
             c.wt_patient_density * t.patient_volume_proxy) * 100 * c.potential_sales_scalar, 
            2
        ) AS potential_sales
    FROM territories t
    CROSS JOIN constants c
),
monthly_opportunity AS (
    -- Join TPI with monthly actual sales to calculate opportunity gaps
    SELECT
        st.month_id,
        tpi.region,
        tpi.territory_id,
        tpi.territory_name,
        st.rep_id,
        st.rep_name,
        tpi.tpi_score,
        tpi.potential_sales,
        st.actual_sales,
        st.target_sales,
        -- Opportunity Gap = Potential Sales - Actual Sales
        -- Measures the dollar amount of untapped market potential
        ROUND(tpi.potential_sales - st.actual_sales, 2) AS opportunity_gap
    FROM vw_sales_targets st
    JOIN territory_tpi tpi ON st.territory_id = tpi.territory_id
),
ranked_opportunity AS (
    -- Rank territories by opportunity gap per month
    SELECT
        *,
        DENSE_RANK() OVER (
            PARTITION BY month_id 
            ORDER BY opportunity_gap DESC
        ) AS opportunity_rank
    FROM monthly_opportunity
)
SELECT
    month_id,
    region,
    territory_id,
    territory_name,
    rep_id,
    rep_name,
    tpi_score,
    potential_sales,
    actual_sales,
    target_sales,
    opportunity_gap,
    opportunity_rank,
    -- Assign Priority Bands based on Rank (10 territories per band)
    CASE 
        WHEN opportunity_rank <= 10 THEN 'Critical'
        WHEN opportunity_rank <= 20 THEN 'High'
        WHEN opportunity_rank <= 30 THEN 'Medium'
        ELSE 'Low'
    END AS priority_band
FROM ranked_opportunity;
