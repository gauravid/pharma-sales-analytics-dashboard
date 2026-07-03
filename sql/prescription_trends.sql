DROP VIEW IF EXISTS vw_prescription_trends;

CREATE VIEW vw_prescription_trends AS
WITH monthly_territory_brand AS (
    -- Aggregate raw HCP prescription data to Territory-Brand-Month level
    SELECT
        month_id,
        region,
        territory_id,
        territory_name,
        rep_id,
        rep_name,
        brand,
        SUM(nrx) AS nrx,
        SUM(trx) AS trx
    FROM vw_prescriptions
    GROUP BY month_id, region, territory_id, territory_name, rep_id, rep_name, brand
),
trend_calculations AS (
    -- Calculate window functions for trends, rolling metrics, and cumulative volume
    SELECT
        month_id,
        region,
        territory_id,
        territory_name,
        rep_id,
        rep_name,
        brand,
        nrx,
        trx,
        -- Prior Month TRx (MoM comparison)
        LAG(trx, 1) OVER (
            PARTITION BY territory_id, brand 
            ORDER BY month_id
        ) AS prev_month_trx,
        
        -- Prior Month NRx
        LAG(nrx, 1) OVER (
            PARTITION BY territory_id, brand 
            ORDER BY month_id
        ) AS prev_month_nrx,
        
        -- Rolling 3-Month TRx (current month + 2 preceding months)
        SUM(trx) OVER (
            PARTITION BY territory_id, brand 
            ORDER BY month_id 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS rolling_3m_trx,
        
        -- Rolling 6-Month TRx (current month + 5 preceding months)
        SUM(trx) OVER (
            PARTITION BY territory_id, brand 
            ORDER BY month_id 
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS rolling_6m_trx,
        
        -- Cumulative YTD TRx
        SUM(trx) OVER (
            PARTITION BY territory_id, brand 
            ORDER BY month_id 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_trx
    FROM monthly_territory_brand
)
SELECT
    month_id,
    region,
    territory_id,
    territory_name,
    rep_id,
    rep_name,
    brand,
    nrx,
    trx,
    prev_month_trx,
    rolling_3m_trx,
    rolling_6m_trx,
    cumulative_trx,
    
    -- Month-over-Month TRx Growth %
    ROUND(
        (CAST(trx - prev_month_trx AS REAL) / NULLIF(prev_month_trx, 0)) * 100, 
        2
    ) AS mom_trx_growth_pct,
    
    -- Month-over-Month NRx Growth %
    ROUND(
        (CAST(nrx - prev_month_nrx AS REAL) / NULLIF(prev_month_nrx, 0)) * 100, 
        2
    ) AS mom_nrx_growth_pct
FROM trend_calculations;
