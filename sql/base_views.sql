/*
----------------------------------------------------
Project:
Sales Force Effectiveness Analytics

Author:
Gauravi

Purpose:
Create base reusable database views to centralize joins 
and serve as a single source of truth for downstream queries.

Created:
July 2026

Dependencies:
calls, hcps, reps, territories, prescriptions, sales_targets

Outputs:
vw_calls, vw_prescriptions, vw_sales_targets
----------------------------------------------------
*/

-- Drop existing views if they exist to allow clean recreations
DROP VIEW IF EXISTS vw_calls;
DROP VIEW IF EXISTS vw_prescriptions;
DROP VIEW IF EXISTS vw_sales_targets;

-- 1. Centralized Calls View
-- Joins calls with HCPs, Reps, and Territories. Uses LEFT JOIN on HCPs 
-- to preserve calls with missing/null HCP IDs for data quality auditing.
CREATE VIEW vw_calls AS
SELECT
    c.call_id,
    c.call_date,
    c.planned_vs_actual,
    c.call_status,
    c.call_type,
    c.brand_promoted,
    c.month_id,
    c.hcp_id,
    h.hcp_name,
    h.specialty,
    h.prescribing_decile,
    r.rep_id,
    r.rep_name,
    r.hire_date AS rep_hire_date,
    r.status AS rep_status,
    t.territory_id,
    t.territory_name,
    t.region,
    t.monthly_call_target,
    t.est_market_calls_monthly
FROM calls c
JOIN reps r ON c.rep_id = r.rep_id
JOIN territories t ON r.territory_id = t.territory_id
LEFT JOIN hcps h ON c.hcp_id = h.hcp_id;

-- 2. Centralized Prescriptions View
-- Joins prescriptions with HCPs, Territories, and Reps to link prescribing trends to reps.
CREATE VIEW vw_prescriptions AS
SELECT
    p.hcp_id,
    h.hcp_name,
    h.specialty,
    h.prescribing_decile,
    p.month_id,
    p.brand,
    p.nrx,
    p.trx,
    t.territory_id,
    t.territory_name,
    t.region,
    r.rep_id,
    r.rep_name
FROM prescriptions p
JOIN hcps h ON p.hcp_id = h.hcp_id
JOIN territories t ON h.territory_id = t.territory_id
JOIN reps r ON r.territory_id = t.territory_id;

-- 3. Centralized Sales & Targets View
-- Joins sales targets with territories and reps to evaluate quota attainment.
CREATE VIEW vw_sales_targets AS
SELECT
    st.territory_id,
    t.territory_name,
    t.region,
    r.rep_id,
    r.rep_name,
    st.month_id,
    st.actual_sales,
    st.target_sales
FROM sales_targets st
JOIN territories t ON st.territory_id = t.territory_id
JOIN reps r ON r.territory_id = t.territory_id;
