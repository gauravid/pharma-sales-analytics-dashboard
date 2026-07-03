/*
----------------------------------------------------
Project:
Sales Force Effectiveness Analytics

Author:
Gauravi

Purpose:
Create database indexes on foreign keys and frequently 
filtered columns to optimize query execution speeds.

Created:
July 2026

Dependencies:
calls, prescriptions, sales_targets, hcps, reps

Outputs:
Indexes: idx_calls_rep, idx_calls_hcp, idx_calls_date,
idx_prescriptions_hcp, idx_sales_territory, idx_hcps_territory
----------------------------------------------------
*/

-- 1. Optimize CRM call log queries (heavy table)
CREATE INDEX IF NOT EXISTS idx_calls_rep ON calls(rep_id);
CREATE INDEX IF NOT EXISTS idx_calls_hcp ON calls(hcp_id);
CREATE INDEX IF NOT EXISTS idx_calls_date ON calls(call_date);
CREATE INDEX IF NOT EXISTS idx_calls_month ON calls(month_id);

-- 2. Optimize Prescription / Claims queries (heavy table)
CREATE INDEX IF NOT EXISTS idx_prescriptions_hcp ON prescriptions(hcp_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_month ON prescriptions(month_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_brand ON prescriptions(brand);

-- 3. Optimize Sales & Target queries
CREATE INDEX IF NOT EXISTS idx_sales_territory ON sales_targets(territory_id);
CREATE INDEX IF NOT EXISTS idx_sales_month ON sales_targets(month_id);

-- 4. Optimize HCP & Rep master queries
CREATE INDEX IF NOT EXISTS idx_hcps_territory ON hcps(territory_id);
CREATE INDEX IF NOT EXISTS idx_reps_territory ON reps(territory_id);
