import os
import sqlite3
import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# 1. Setup Logging
os.makedirs("data/exports", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)

log_filename = "data/logs/predictive_modeling.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("Initializing SFE Predictive Layer Pipeline...")

db_path = "data/sfe_analytics.db"
if not os.path.exists(db_path):
    logging.critical(f"Database not found at {db_path}. Run generate_data.py and run_queries.py first.")
    exit(1)

# Connect to SQLite
conn = sqlite3.connect(db_path)

# ==========================================
# PHASE 4.1: DATA QUALITY AUDIT (PRE-TRAINING)
# ==========================================
logging.info("Starting Pre-Training Data Quality Audit...")

# A. Missing Values Check
df_sales_raw = pd.read_sql_query("SELECT * FROM sales_targets;", conn)
df_calls_raw = pd.read_sql_query("SELECT * FROM calls;", conn)
df_rx_raw = pd.read_sql_query("SELECT * FROM prescriptions;", conn)
df_hcps_raw = pd.read_sql_query("SELECT * FROM hcps;", conn)

null_sales = df_sales_raw.isnull().sum().sum()
null_calls = df_calls_raw.isnull().sum().sum()
null_rx = df_rx_raw.isnull().sum().sum()

logging.info(f"Missing Values: sales_targets={null_sales}, calls={null_calls} (expected due to CRM late logging), prescriptions={null_rx}")

# B. Outlier Detection (Z-Score on Actual Sales)
mean_sales = df_sales_raw["actual_sales"].mean()
std_sales = df_sales_raw["actual_sales"].std()
df_sales_raw["sales_z_score"] = (df_sales_raw["actual_sales"] - mean_sales) / std_sales
outliers = df_sales_raw[df_sales_raw["sales_z_score"].abs() > 3.0]
logging.info(f"Outlier Detection: Found {len(outliers)} records with actual_sales Z-Score > 3.0")
if len(outliers) > 0:
    for idx, row in outliers.iterrows():
        logging.warning(f"Outlier detected: Territory {row['territory_id']} Month {row['month_id']} Sales=${row['actual_sales']:,.2f} (Z={row['sales_z_score']:.2f})")

# C. Complete History Check
history_counts = df_sales_raw.groupby("territory_id")["month_id"].count()
incomplete_history = history_counts[history_counts != 12]
logging.info(f"History Check: {len(incomplete_history)} territories have incomplete history (expected 12 months)")
if len(incomplete_history) > 0:
    logging.error(f"Incomplete history found for: {incomplete_history.index.tolist()}")

logging.info("Data Quality Audit complete. Proceeding to Model Training.")

# ==========================================
# PHASE 4.2: SALES FORECASTING MODEL (LINEAR REGRESSION)
# ==========================================
logging.info("Pre-processing Sales Data for Forecasting...")

# Sort sales data and create lags
df_sales = df_sales_raw.sort_values(by=["territory_id", "month_id"]).copy()
df_sales["month_idx"] = df_sales.groupby("territory_id").cumcount() + 1

# Generate Lag 1 and Rolling 3-Month Average
df_sales["lag_1"] = df_sales.groupby("territory_id")["actual_sales"].shift(1)
df_sales["rolling_3m_avg"] = df_sales.groupby("territory_id")["actual_sales"].shift(1).rolling(window=3).mean()

# Drop rows without complete lag data (Months 1, 2, 3)
df_ml_sales = df_sales.dropna().copy()

# A. Time Series Cross-Validation (Rolling Window Folds)
# Folds: Test Month 7, 8, 9, 10, 11, 12
validation_folds = range(7, 13)
regression_errors_mae = []
regression_errors_mape = []
baseline_errors_mae = []
baseline_errors_mape = []

for test_month in validation_folds:
    # Split train and test
    train_fold = df_ml_sales[df_ml_sales["month_idx"] < test_month]
    test_fold = df_ml_sales[df_ml_sales["month_idx"] == test_month]
    
    if len(test_fold) == 0:
        continue
        
    X_train = train_fold[["month_idx", "lag_1", "rolling_3m_avg"]]
    y_train = train_fold["actual_sales"]
    X_test = test_fold[["month_idx", "lag_1", "rolling_3m_avg"]]
    y_test = test_fold["actual_sales"]
    
    # Train Linear Regression
    model_fold = LinearRegression()
    model_fold.fit(X_train, y_train)
    y_pred_reg = model_fold.predict(X_test)
    
    # Naïve Baseline Forecast (Next Month Sales = Previous Month Sales)
    y_pred_base = test_fold["lag_1"].values
    
    # Calculate MAE and MAPE
    mae_reg = np.mean(np.abs(y_test - y_pred_reg))
    mape_reg = np.mean(np.abs((y_test - y_pred_reg) / y_test)) * 100
    mae_base = np.mean(np.abs(y_test - y_pred_base))
    mape_base = np.mean(np.abs((y_test - y_pred_base) / y_test)) * 100
    
    regression_errors_mae.append(mae_reg)
    regression_errors_mape.append(mape_reg)
    baseline_errors_mae.append(mae_base)
    baseline_errors_mape.append(mape_base)
    
    logging.info(f"Time Series CV Fold (Month {test_month:02d}) | Reg MAPE: {mape_reg:.2f}% vs. Base MAPE: {mape_base:.2f}%")

avg_reg_mae = np.mean(regression_errors_mae)
avg_reg_mape = np.mean(regression_errors_mape)
avg_base_mae = np.mean(baseline_errors_mae)
avg_base_mape = np.mean(baseline_errors_mape)

logging.info(f"\n--- SALES FORECAST MODEL VALIDATION SUMMARY ---")
logging.info(f"Baseline (Naïve) Forecast   | Average MAE: ${avg_base_mae:,.2f} | Average MAPE: {avg_base_mape:.2f}%")
logging.info(f"Linear Regression Model     | Average MAE: ${avg_reg_mae:,.2f} | Average MAPE: {avg_reg_mape:.2f}%")

# B. Train Final Model and Predict Month 13 (Jan 2026)
logging.info("Training Final Sales Forecast Model on Full 12 Months...")
X_full = df_ml_sales[["month_idx", "lag_1", "rolling_3m_avg"]]
y_full = df_ml_sales["actual_sales"]

model_sales = LinearRegression()
model_sales.fit(X_full, y_full)

# Calculate Residual Standard Error (Se) for 95% Confidence Intervals
residuals = y_full - model_sales.predict(X_full)
std_residuals = np.std(residuals)

# Generate features for Month 13 (Jan 2026) per territory
month_13_features = []
df_m12 = df_sales[df_sales["month_idx"] == 12]

for idx, row in df_m12.iterrows():
    t_id = row["territory_id"]
    # Get last 3 months of actual sales to calculate Month 13 rolling average
    t_sales_hist = df_sales[df_sales["territory_id"] == t_id].sort_values(by="month_idx")["actual_sales"].values
    lag_1 = t_sales_hist[-1] # Month 12 sales
    rolling_3m = np.mean(t_sales_hist[-3:]) # Average of Months 10, 11, 12
    
    month_13_features.append({
        "territory_id": t_id,
        "month_idx": 13,
        "lag_1": lag_1,
        "rolling_3m_avg": rolling_3m
    })

df_m13 = pd.DataFrame(month_13_features)
X_m13 = df_m13[["month_idx", "lag_1", "rolling_3m_avg"]]
df_m13["predicted_sales"] = model_sales.predict(X_m13)

# Add 95% Confidence Intervals
df_m13["lower_estimate"] = (df_m13["predicted_sales"] - 1.96 * std_residuals).clip(lower=0)
df_m13["upper_estimate"] = df_m13["predicted_sales"] + 1.96 * std_residuals

# Map Potential Sales (TPI Score * 800) and Calculate Opportunity Gaps
df_tpi = pd.read_sql_query("SELECT territory_id, territory_name, region, category_volume_factor, target_hcp_count_factor, patient_volume_proxy FROM territories;", conn)
df_tpi["tpi_score"] = (df_tpi["category_volume_factor"] * 0.50 + df_tpi["target_hcp_count_factor"] * 0.30 + df_tpi["patient_volume_proxy"] * 0.20) * 100
df_tpi["potential_sales"] = df_tpi["tpi_score"] * 800.0

df_forecast = pd.merge(df_m13, df_tpi, on="territory_id")
df_rep_map = pd.read_sql_query("SELECT territory_id, rep_id, rep_name FROM reps;", conn)
df_forecast = pd.merge(df_forecast, df_rep_map, on="territory_id")

# Calculate Predicted Opportunity Gaps
df_forecast["absolute_gap"] = df_forecast["potential_sales"] - df_forecast["predicted_sales"]
df_forecast["gap_pct"] = (df_forecast["absolute_gap"] / df_forecast["potential_sales"]) * 100

# Rank territories by opportunity gap
df_forecast["opportunity_rank"] = df_forecast["absolute_gap"].rank(ascending=False, method="dense").astype(int)
df_forecast["priority_band"] = pd.qcut(df_forecast["opportunity_rank"], 4, labels=["Critical", "High", "Medium", "Low"])

# Export Sales Forecast
df_forecast_export = df_forecast[[
    "territory_id", "territory_name", "region", "rep_id", "rep_name", 
    "predicted_sales", "lower_estimate", "upper_estimate", 
    "potential_sales", "absolute_gap", "gap_pct", "opportunity_rank", "priority_band"
]]
df_forecast_export.to_csv("data/exports/territory_forecast.csv", index=False)
logging.info("Month 13 Sales Forecast successfully exported.")

# ==========================================
# PHASE 4.3: GRANULAR REP PERFORMANCE & RISK PROJECTOR
# ==========================================
logging.info("Projecting Q4 Rep Performance & Risk Flags...")

# Simulate date: Nov 30, 2025 (Known Oct and Nov sales, projecting Dec using the LR model)
df_oct = df_sales[df_sales["month_idx"] == 10][["territory_id", "actual_sales", "target_sales"]].rename(columns={"actual_sales": "oct_actual", "target_sales": "oct_target"})
df_nov = df_sales[df_sales["month_idx"] == 11][["territory_id", "actual_sales", "target_sales"]].rename(columns={"actual_sales": "nov_actual", "target_sales": "nov_target"})
df_dec_target = df_sales[df_sales["month_idx"] == 12][["territory_id", "target_sales"]].rename(columns={"target_sales": "dec_target"})

# Dec actual is predicted by our regression model
df_dec_pred = df_forecast[["territory_id", "predicted_sales"]].rename(columns={"predicted_sales": "dec_projected"})

# Merge Q4 data
df_q4 = pd.merge(df_oct, df_nov, on="territory_id")
df_q4 = pd.merge(df_q4, df_dec_target, on="territory_id")
df_q4 = pd.merge(df_q4, df_dec_pred, on="territory_id")

# Calculate Projected Q4 metrics
df_q4["projected_q4_sales"] = df_q4["oct_actual"] + df_q4["nov_actual"] + df_q4["dec_projected"]
df_q4["q4_target"] = df_q4["oct_target"] + df_q4["nov_target"] + df_q4["dec_target"]
df_q4["projected_q4_attainment_pct"] = (df_q4["projected_q4_sales"] / df_q4["q4_target"]) * 100

# Assign Granular Risk Bands
# Low: >= 100% | Moderate: 90-100% | High: 80-90% | Critical: < 80%
def assign_risk_band(attainment):
    if attainment >= 100.0:
        return "Low Risk"
    elif attainment >= 90.0:
        return "Moderate Risk"
    elif attainment >= 80.0:
        return "High Risk"
    else:
        return "Critical"

df_q4["risk_band"] = df_q4["projected_q4_attainment_pct"].apply(assign_risk_band)

df_rep_risk = pd.merge(df_q4, df_rep_map, on="territory_id")
df_rep_risk = pd.merge(df_rep_risk, df_tpi[["territory_id", "region"]], on="territory_id")

df_rep_risk_export = df_rep_risk[[
    "rep_id", "rep_name", "region", "territory_id", 
    "projected_q4_sales", "q4_target", "projected_q4_attainment_pct", "risk_band"
]]
df_rep_risk_export.to_csv("data/exports/rep_risk_flags.csv", index=False)
logging.info("Q4 Rep Risk Projector successfully exported.")

# ==========================================
# PHASE 4.4: HCP PRESCRIBING PROPENSITY MODEL (LOGISTIC REGRESSION)
# ==========================================
logging.info("Preparing HCP Prescribing Dataset...")

# We calculate calls and prescription counts per HCP and month
df_hcp_calls = pd.read_sql_query("""
    SELECT month_id, hcp_id, COUNT(*) AS completed_calls
    FROM calls
    WHERE call_status = 'Completed' AND brand_promoted = 'Apexacare' AND hcp_id IS NOT NULL
    GROUP BY month_id, hcp_id;
""", conn)

df_hcp_rx = pd.read_sql_query("""
    SELECT month_id, hcp_id, hcp_name, specialty, prescribing_decile, trx
    FROM vw_prescriptions
    WHERE brand = 'Apexacare'
""", conn)

# Merge calls and prescription data
df_hcp_data = pd.merge(df_hcp_rx, df_hcp_calls, on=["month_id", "hcp_id"], how="left")
df_hcp_data["completed_calls"] = df_hcp_data["completed_calls"].fillna(0)

# Sort and generate lags
df_hcp_data = df_hcp_data.sort_values(by=["hcp_id", "month_id"])
df_hcp_data["prev_month_trx"] = df_hcp_data.groupby("hcp_id")["trx"].shift(1)
df_hcp_data["prev_2_month_trx"] = df_hcp_data.groupby("hcp_id")["trx"].shift(2)

# Features:
# 1. lag_calls: calls received in prior month (m-1) to predict Rx increase in month m
df_hcp_data["lag_calls"] = df_hcp_data.groupby("hcp_id")["completed_calls"].shift(1)
# 2. trx_trend: trend in prior month (m-1 vs m-2)
df_hcp_data["trx_trend"] = df_hcp_data["prev_month_trx"] - df_hcp_data["prev_2_month_trx"]

# Target: 1 if Month m TRx > Month m-1 TRx, else 0
df_hcp_data["increase_next_month"] = (df_hcp_data["trx"] > df_hcp_data["prev_month_trx"]).astype(int)

# Drop rows without complete lag history (Months 1, 2)
df_ml_hcp = df_hcp_data.dropna().copy()

# One-hot encode specialty
df_ml_hcp = pd.get_dummies(df_ml_hcp, columns=["specialty"], drop_first=True)

# Specialty column names check
spec_cols = [c for c in df_ml_hcp.columns if c.startswith("specialty_")]

# A. Evaluate Classifier on Month 12 Holdout Set
train_hcp = df_ml_hcp[df_ml_hcp["month_id"] < "2025-12"]
test_hcp = df_ml_hcp[df_ml_hcp["month_id"] == "2025-12"]

features_hcp = ["prescribing_decile", "lag_calls", "trx_trend"] + spec_cols
X_train_hcp = train_hcp[features_hcp]
y_train_hcp = train_hcp["increase_next_month"]
X_test_hcp = test_hcp[features_hcp]
y_test_hcp = test_hcp["increase_next_month"]

classifier = LogisticRegression(random_state=42)
classifier.fit(X_train_hcp, y_train_hcp)
y_pred_hcp = classifier.predict(X_test_hcp)
y_prob_hcp = classifier.predict_proba(X_test_hcp)[:, 1]

# Calculate classification metrics on the holdout fold
accuracy = accuracy_score(y_test_hcp, y_pred_hcp)
precision = precision_score(y_test_hcp, y_pred_hcp)
recall = recall_score(y_test_hcp, y_pred_hcp)
f1 = f1_score(y_test_hcp, y_pred_hcp)
roc_auc = roc_auc_score(y_test_hcp, y_prob_hcp)

logging.info(f"\n--- HCP CLASSIFICATION MODEL METRICS (HOLDOUT) ---")
logging.info(f"Accuracy : {accuracy:.4f}")
logging.info(f"Precision: {precision:.4f}")
logging.info(f"Recall   : {recall:.4f}")
logging.info(f"F1-Score : {f1:.4f}")
logging.info(f"ROC-AUC  : {roc_auc:.4f}")

# B. Predict Propensity for Month 13 (Jan 2026)
logging.info("Training Final Classifier and Predicting Month 13 Probabilities...")
classifier_final = LogisticRegression(random_state=42)
classifier_final.fit(df_ml_hcp[features_hcp], df_ml_hcp["increase_next_month"])

# Prepare Month 13 features (using Month 12 data as prior-month history)
df_m12_hcp = df_ml_hcp[df_ml_hcp["month_id"] == "2025-12"].copy()

# Features for Month 13:
# lag_calls_m13 = actual calls in Month 12
df_m12_hcp["lag_calls_m13"] = df_m12_hcp["completed_calls"]
# trx_trend_m13 = Month 12 actual - Month 11 actual
df_m12_hcp["trx_trend_m13"] = df_m12_hcp["trx"] - df_m12_hcp["prev_month_trx"]

# Construct Month 13 input dataframe
df_m13_hcp_inputs = df_m12_hcp[["hcp_id", "hcp_name", "prescribing_decile", "lag_calls_m13", "trx_trend_m13"] + spec_cols].copy()
df_m13_hcp_inputs = df_m13_hcp_inputs.rename(columns={"lag_calls_m13": "lag_calls", "trx_trend_m13": "trx_trend"})

# Predict Month 13 probabilities
probs_m13 = classifier_final.predict_proba(df_m13_hcp_inputs[features_hcp])[:, 1]
df_m13_hcp_inputs["propensity_score"] = (probs_m13 * 100).round(1)

# Merge back HCP and Territory information
df_hcp_rep_territory = pd.read_sql_query("""
    SELECT h.hcp_id, h.specialty, t.territory_id, t.territory_name, t.region, r.rep_id, r.rep_name
    FROM hcps h
    JOIN territories t ON h.territory_id = t.territory_id
    JOIN reps r ON r.territory_id = t.territory_id
""", conn)

df_hcp_propensity = pd.merge(df_m13_hcp_inputs, df_hcp_rep_territory, on="hcp_id")

# Export HCP Scores
df_hcp_propensity_export = df_hcp_propensity[[
    "hcp_id", "hcp_name", "specialty", "prescribing_decile", "territory_id", 
    "territory_name", "region", "rep_id", "rep_name", "lag_calls", "propensity_score"
]]
df_hcp_propensity_export.to_csv("data/exports/hcp_prescribing_score.csv", index=False)
logging.info("Month 13 HCP Prescribing Propensity Scores successfully exported.")

# ==========================================
# PHASE 4.5: MODEL PERFORMANCE & FEATURE IMPORTANCE
# ==========================================
# Save all metrics to model_metrics.csv
model_metrics_data = [
    {"Model": "Sales Forecast (Linear Regression)", "Metric": "TS-CV Average MAE (USD)", "Value": avg_reg_mae, "Baseline (Naïve) Value": avg_base_mae},
    {"Model": "Sales Forecast (Linear Regression)", "Metric": "TS-CV Average MAPE", "Value": avg_reg_mape, "Baseline (Naïve) Value": avg_base_mape},
    {"Model": "HCP Classifier (Logistic Regression)", "Metric": "Holdout Accuracy", "Value": accuracy, "Baseline (Naïve) Value": 0.5000},
    {"Model": "HCP Classifier (Logistic Regression)", "Metric": "Holdout Precision", "Value": precision, "Baseline (Naïve) Value": 0.5000},
    {"Model": "HCP Classifier (Logistic Regression)", "Metric": "Holdout Recall", "Value": recall, "Baseline (Naïve) Value": 0.5000},
    {"Model": "HCP Classifier (Logistic Regression)", "Metric": "Holdout F1-Score", "Value": f1, "Baseline (Naïve) Value": 0.5000},
    {"Model": "HCP Classifier (Logistic Regression)", "Metric": "Holdout ROC-AUC", "Value": roc_auc, "Baseline (Naïve) Value": 0.5000}
]
df_metrics = pd.DataFrame(model_metrics_data)
df_metrics.to_csv("data/exports/model_metrics.csv", index=False)

# Log Coefficients and Odds Ratios
logging.info(f"\n--- SALES FORECAST COEFFICIENTS ---")
for feat, coef in zip(X_full.columns, model_sales.coef_):
    logging.info(f"Feature: {feat:<15} | Coefficient: {coef:.4f}")
logging.info(f"Intercept: {model_sales.intercept_:.4f}")

logging.info(f"\n--- HCP CLASSIFIER COEFFICIENTS & ODDS RATIOS ---")
for feat, coef in zip(features_hcp, classifier_final.coef_[0]):
    odds_ratio = np.exp(coef)
    logging.info(f"Feature: {feat:<22} | Coefficient: {coef:.4f} | Odds Ratio: {odds_ratio:.4f}")

# ==========================================
# PHASE 4.6: BUSINESS RECOMMENDATIONS & DECISION-SUPPORT
# ==========================================
logging.info("Generating SFE Business Recommendations...")

# 1. Top 5 Territories expected to exceed Target in Month 13
df_t13_attainment = df_forecast.copy()
# Assume Month 13 target is set equal to Month 12 target
df_m12_targets = df_sales[df_sales["month_idx"] == 12][["territory_id", "target_sales"]].rename(columns={"target_sales": "m13_target"})
df_t13_attainment = pd.merge(df_t13_attainment, df_m12_targets, on="territory_id")
df_t13_attainment["projected_m13_attainment_pct"] = (df_t13_attainment["predicted_sales"] / df_t13_attainment["m13_target"]) * 100

top_territories = df_t13_attainment.sort_values(by="projected_m13_attainment_pct", ascending=False).head(5)

# 2. Top 10 at-risk reps in Q4 (High Risk or Critical)
at_risk_reps = df_rep_risk[df_rep_risk["risk_band"].isin(["Critical", "High Risk"])].sort_values(by="projected_q4_attainment_pct", ascending=True).head(10)

# 3. Top 20 high-probability HCPs who are underserved (calls below median)
# Underserved list from Phase 2
df_underserved = pd.read_csv("data/exports/underserved_hcps.csv")
# Join propensity scores
df_hcp_rec = pd.merge(df_underserved, df_hcp_propensity[["hcp_id", "propensity_score"]], on="hcp_id")
top_hcps = df_hcp_rec.sort_values(by=["propensity_score", "potential_lost_revenue"], ascending=[False, False]).head(20)

# Compile and export recommendations
recs = []

for idx, row in top_territories.iterrows():
    recs.append({
        "category": "Top Territory Growth Opportunity",
        "entity": f"Territory: {row['territory_name']} ({row['territory_id']})",
        "owner": f"Rep: {row['rep_name']} ({row['rep_id']})",
        "metric_desc": "Projected Month 13 Attainment",
        "metric_value": f"{row['projected_m13_attainment_pct']:.2f}%",
        "actionable_insight": "Exceeding potential. Consider increasing targets or allocating additional budget to support regional marketing."
    })

for idx, row in at_risk_reps.iterrows():
    recs.append({
        "category": "Sales Rep Alert (At-Risk Quota)",
        "entity": f"Representative: {row['rep_name']} ({row['rep_id']})",
        "owner": f"Territory: {row['territory_id']}",
        "metric_desc": "Projected Q4 Quota Attainment",
        "metric_value": f"{row['projected_q4_attainment_pct']:.2f}% ({row['risk_band']})",
        "actionable_insight": "Projected to miss quarterly targets. Trigger manager ride-alongs and run detailing workshops focused on key cardiologists."
    })

for idx, row in top_hcps.iterrows():
    recs.append({
        "category": "High-Value Underserved Doctor (Priority Target)",
        "entity": f"Physician: {row['hcp_name']} ({row['specialty']}) in {row['territory_name']}",
        "owner": f"Assigned Rep: {row['rep_name']}",
        "metric_desc": "Prescribing Propensity Score",
        "metric_value": f"{row['propensity_score']}/100 | Lost Rev: ${row['potential_lost_revenue']:,.2f}",
        "actionable_insight": f"High propensity to increase prescriptions, but visited below territory median. Action: Schedule {row['suggested_calls_next_month']} calls next month."
    })

df_recs = pd.DataFrame(recs)
df_recs.to_csv("data/exports/business_recommendations.csv", index=False)
logging.info("Business Recommendations successfully exported.")

# Close connection
conn.close()
logging.info("SFE Predictive Layer execution complete. Ready for Power BI integration.")
