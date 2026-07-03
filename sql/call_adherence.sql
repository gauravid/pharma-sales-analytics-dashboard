/*
----------------------------------------------------
Project:
Sales Force Effectiveness Analytics

Author:
Gauravi

Purpose:
Create the vw_call_adherence view to calculate call execution 
metrics (adherence, completion, no-show, and cancellation rates).

Created:
July 2026

Dependencies:
vw_calls

Outputs:
View: vw_call_adherence
----------------------------------------------------
*/

DROP VIEW IF EXISTS vw_call_adherence;

CREATE VIEW vw_call_adherence AS
WITH call_metrics AS (
    SELECT
        month_id,
        region,
        territory_id,
        territory_name,
        rep_id,
        rep_name,
        -- Total planned calls in CRM (denominator for adherence)
        SUM(CASE WHEN planned_vs_actual = 'Planned' THEN 1 ELSE 0 END) AS planned_calls,
        
        -- Completed planned calls (numerator for adherence)
        SUM(CASE WHEN planned_vs_actual = 'Planned' AND call_status = 'Completed' THEN 1 ELSE 0 END) AS completed_planned_calls,
        
        -- Completed unplanned calls (drop-ins)
        SUM(CASE WHEN planned_vs_actual = 'Unplanned' AND call_status = 'Completed' THEN 1 ELSE 0 END) AS completed_unplanned_calls,
        
        -- Total completed calls (Planned + Unplanned)
        SUM(CASE WHEN call_status = 'Completed' THEN 1 ELSE 0 END) AS total_completed_calls,
        
        -- No Show calls (planned visits where doctor was unavailable)
        SUM(CASE WHEN call_status = 'No Show' THEN 1 ELSE 0 END) AS no_show_calls,
        
        -- Cancelled calls (planned visits cancelled in advance)
        SUM(CASE WHEN call_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_calls
    FROM vw_calls
    WHERE month_id IS NOT NULL
    GROUP BY month_id, region, territory_id, territory_name, rep_id, rep_name
)
SELECT
    month_id,
    region,
    territory_id,
    territory_name,
    rep_id,
    rep_name,
    planned_calls,
    completed_planned_calls,
    completed_unplanned_calls,
    total_completed_calls,
    no_show_calls,
    cancelled_calls,
    -- Missed planned calls = Planned - Completed Planned
    (planned_calls - completed_planned_calls) AS missed_calls,
    
    -- 1. Call Plan Adherence % = (Completed Planned Calls / Total Planned Calls) * 100
    ROUND(
        (CAST(completed_planned_calls AS REAL) / NULLIF(planned_calls, 0)) * 100, 
        2
    ) AS adherence_pct,
    
    -- 2. Completion Rate % = (Total Completed Calls / Total Planned Calls) * 100 (includes unplanned)
    ROUND(
        (CAST(total_completed_calls AS REAL) / NULLIF(planned_calls, 0)) * 100, 
        2
    ) AS completion_rate,
    
    -- 3. No-Show Rate % = (No Show Calls / Total Planned Calls) * 100
    ROUND(
        (CAST(no_show_calls AS REAL) / NULLIF(planned_calls, 0)) * 100, 
        2
    ) AS no_show_rate,
    
    -- 4. Cancellation Rate % = (Cancelled Calls / Total Planned Calls) * 100
    ROUND(
        (CAST(cancelled_calls AS REAL) / NULLIF(planned_calls, 0)) * 100, 
        2
    ) AS cancellation_rate
FROM call_metrics;
