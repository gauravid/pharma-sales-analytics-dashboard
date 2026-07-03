-- 1. Top 10 Territories by Total Actual Sales (Full Year 2025)
SELECT '1. Top 10 Territories by Sales' AS ranking_step;
SELECT 
    territory_id,
    territory_name,
    region,
    rep_name,
    ROUND(SUM(actual_sales), 2) AS total_sales,
    ROUND(AVG(actual_sales / target_sales) * 100, 2) AS avg_attainment_pct
FROM vw_sales_targets
GROUP BY territory_id, territory_name, region, rep_name
ORDER BY total_sales DESC
LIMIT 10;

-- 2. Top 10 Reps by Quota Attainment (Full Year 2025 Average)
SELECT '2. Top 10 Reps by Quota Attainment' AS ranking_step;
SELECT 
    rep_id,
    rep_name,
    territory_name,
    region,
    ROUND(SUM(actual_sales), 2) AS total_sales,
    ROUND((SUM(actual_sales) / SUM(target_sales)) * 100, 2) AS attainment_pct
FROM vw_sales_targets
GROUP BY rep_id, rep_name, territory_name, region
ORDER BY attainment_pct DESC
LIMIT 10;

-- 3. Bottom 10 Reps by Quota Attainment (Full Year 2025 Average)
SELECT '3. Bottom 10 Reps by Quota Attainment' AS ranking_step;
SELECT 
    rep_id,
    rep_name,
    territory_name,
    region,
    ROUND(SUM(actual_sales), 2) AS total_sales,
    ROUND((SUM(actual_sales) / SUM(target_sales)) * 100, 2) AS attainment_pct
FROM vw_sales_targets
GROUP BY rep_id, rep_name, territory_name, region
ORDER BY attainment_pct ASC
LIMIT 10;

-- 4. Fastest Growing Territories (Top 5 by Sales Growth % in the Last Quarter of 2025)
-- We compare Q4 (Months 10, 11, 12) sales vs. Q3 (Months 7, 8, 9) sales
SELECT '4. Fastest Growing Territories (Q3 to Q4)' AS ranking_step;
WITH quarterly_sales AS (
    SELECT
        territory_id,
        territory_name,
        region,
        SUM(CASE WHEN month_id IN ('2025-07', '2025-08', '2025-09') THEN actual_sales ELSE 0 END) AS q3_sales,
        SUM(CASE WHEN month_id IN ('2025-10', '2025-11', '2025-12') THEN actual_sales ELSE 0 END) AS q4_sales
    FROM vw_sales_targets
    GROUP BY territory_id, territory_name, region
)
SELECT
    territory_id,
    territory_name,
    region,
    ROUND(q3_sales, 2) AS q3_sales,
    ROUND(q4_sales, 2) AS q4_sales,
    ROUND(((q4_sales - q3_sales) / NULLIF(q3_sales, 0)) * 100, 2) AS growth_pct
FROM quarterly_sales
ORDER BY growth_pct DESC
LIMIT 5;

-- 5. Highest Opportunity Territories (Top 10 by Cumulative Opportunity Gap in 2025)
SELECT '5. Highest Opportunity Territories' AS ranking_step;
SELECT
    territory_id,
    territory_name,
    region,
    rep_name,
    tpi_score,
    ROUND(SUM(potential_sales), 2) AS total_potential_sales,
    ROUND(SUM(actual_sales), 2) AS total_actual_sales,
    ROUND(SUM(opportunity_gap), 2) AS total_opportunity_gap
FROM vw_territory_opportunity
GROUP BY territory_id, territory_name, region, rep_name, tpi_score
ORDER BY total_opportunity_gap DESC
LIMIT 10;
