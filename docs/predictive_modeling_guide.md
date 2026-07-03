# SFE Predictive Layer Developer & Validation Guide

This document provides a comprehensive overview of the machine learning predictive layer developed for the **Sales Force Effectiveness (SFE) & Market Access Analytics** project. It details the pre-training audits, cross-validation metrics, regression coefficients, classification odds ratios, and the business logic behind our proactive decision-support systems.

---

## 1. Machine Learning Architecture

The predictive pipeline is built entirely in Python using standard libraries (`pandas`, `numpy`, `scikit-learn`) and integrates back into the SQLite database. The workflow consists of four major layers:

```
   Raw CRM & Claims
         │
         ▼
   Data Quality Audit ────► [Outlier / NULL Checks]
         │
         ▼
   Feature Ingestion
         │
         ├──► Sales Trend (month_idx, lag_1, rolling_3m) ────► [Linear Regression]
         └──► HCP Detailing (decile, lag_calls, trx_trend) ──► [Logistic Regression]
         │
         ▼
   Validation & Training ──► [Time Series Cross-Validation / Holdout Testing]
         │
         ▼
   CSV Output Exports ────► [model_metrics.csv, territory_forecast.csv, rep_risk_flags.csv]
```

---

## 2. Pre-Training Data Quality Audit

Before model training, the automated audit script (`predictive_modeling.py`) validates the database tables:
1.  **Missing Values (NULLs)**: Checks key columns in `sales_targets`, `calls`, and `prescriptions` to ensure no training features are empty. Missing values in `calls` (seeded CRM late entries) are filled with zero for modeling.
    *   *Audit Result*: Found `0` missing values in sales targets, `2074` missing values in calls (correctly handled as 0 completed calls), and `0` in prescriptions.
2.  **Outlier Detection (Z-Score)**: Scans monthly territory sales for values $> 3$ standard deviations from the mean:
    $$\text{Z-Score} = \frac{\text{Sales}_{t,m} - \mu}{\sigma}$$
    *   *Audit Result*: Found `0` records exceeding the Z-Score threshold, confirming database statistical integrity.
3.  **Completeness Check**: Confirms that all 40 territories have exactly 12 months of sales records, guaranteeing sufficient history for lag and rolling calculations.
    *   *Audit Result*: Found `0` territories with incomplete histories.

---

## 3. Sales Forecasting & Validation (Linear Regression)

### Feature Engineering
For each territory, the model predicts sales in month $m$ using three features:
1.  `month_idx`: An integer time index (1 to 12) capturing seasonal growth or decline.
2.  `lag_1`: Actual actual sales in month $m-1$.
3.  `rolling_3m_avg`: Average actual sales over the prior 3 months ($m-3$, $m-2$, $m-1$).

### Time Series Cross-Validation (Rolling Window)
Rather than a standard random train/test split (which violates time-dependency), we evaluate model accuracy using a rolling window validation:
*   *Fold 1*: Train on Months 4-6 $\rightarrow$ Test on Month 7
*   *Fold 2*: Train on Months 4-7 $\rightarrow$ Test on Month 8
*   *Fold 3*: Train on Months 4-8 $\rightarrow$ Test on Month 9
*   *Fold 4*: Train on Months 4-9 $\rightarrow$ Test on Month 10
*   *Fold 5*: Train on Months 4-10 $\rightarrow$ Test on Month 11
*   *Fold 6*: Train on Months 4-11 $\rightarrow$ Test on Month 12

### Performance Evaluation vs. Naïve Baseline
We compare our Linear Regression model against a **Naïve Baseline** (which assumes next month's sales will equal this month's sales, i.e., $Sales_m = Sales_{m-1}$). The average errors across all 6 validation folds are:

| Model | Mean Absolute Error (MAE) | Mean Absolute Percentage Error (MAPE) |
| :--- | :---: | :---: |
| **Naïve Forecast (Baseline)** | **$6,066.69** | **5.74%** |
| **Linear Regression** | **$5,143.86** | **4.82%** |

*   *Verdict*: The Linear Regression model outperforms the baseline by **15.2% in MAE** and **16.0% in MAPE**, proving that incorporating the 3-month rolling average and time indexes significantly improves forecasting accuracy.

### Regression Coefficients & Feature Importance
The final regression model trained on all 12 months of data has the following equation:
$$\text{Projected Sales} = (161.23 \times \text{month\_idx}) + (0.1014 \times \text{lag\_1}) + (0.8643 \times \text{rolling\_3m\_avg}) + 2494.39$$

*   **Interpretation**:
    *   **Time Trend (`month_idx`)**: Adds $161.23 in sales each month (organic growth trend).
    *   **Prior Month Sales (`lag_1`)**: Every $1.00 increase in last month's sales predicts an additional $0.10 increase next month.
    *   **Rolling Average (`rolling_3m_avg`)**: Captures medium-term momentum. Since the coefficient is **0.8643**, it is the most critical feature in predicting sales.

### Confidence Intervals
To avoid presenting predictions as "absolute truths", we export 95% Confidence Intervals calculated from the standard deviation of training residuals ($S_e = \$5,207.24$):
$$\text{Lower Estimate} = \max\left(0, \hat{y} - 1.96 \times S_e\right)$$
$$\text{Upper Estimate} = \hat{y} + 1.96 \times S_e$$

---

## 4. Q4 Sales Projection & Rep Risk Bands

To simulate a mid-quarter review on **November 30, 2025**, we project Q4 attainment for each rep by combining actual sales (October and November) with predicted sales for December (from our forecasting model):
$$\text{Projected Q4 Sales} = \text{Actual Oct} + \text{Actual Nov} + \text{Projected Dec}$$
$$\text{Projected Attainment \%} = \left( \frac{\text{Projected Q4 Sales}}{\text{Q4 Target Quota}} \right) \times 100$$

Reps are categorized into **Granular Risk Bands**:
*   **Low Risk**: Projected Attainment $\ge 100\%$ (sales force performing at quota).
*   **Moderate Risk**: Attainment $90\% - 99.9\%$ (close to quota, needs minor push).
*   **High Risk**: Attainment $80\% - 89.9\%$ (lagging, requires intervention).
*   **Critical**: Attainment $< 80\%$ (severely under-quota, requires urgent action).

---

## 5. HCP Prescribing Propensity Model (Logistic Regression)

*   **Objective**: Predict whether a physician will increase their brand prescribing volume (*Apexacare*) next month.
*   **Target Variable**: `increase_next_month` (1 if TRx in month $m > m-1$, else 0).
*   **Features**:
    *   `prescribing_decile`: 1 to 10.
    *   `lag_calls`: Number of completed Apexacare calls received in month $m-1$.
    *   `trx_trend`: Difference in brand prescriptions between $m-1$ and $m-2$.
    *   `specialty`: One-hot encoded.

### Model Evaluation (Month 12 Holdout Set)
Evaluating the classifier on the Month 12 holdout fold yields these metrics:
*   **Accuracy**: **71.57%** (correctly predicts prescribing growth MoM).
*   **Precision**: **70.55%** (when predicting a doctor will increase prescribing, the model is correct 70.6% of the time).
*   **Recall**: **70.55%** (captures 70.6% of all physicians who actually increase prescribing).
*   **F1-Score**: **70.55%** (balanced metric).
*   **ROC-AUC**: **76.49%** (strong discriminative power).

### Odds Ratios & Coefficients
The final logistic regression weights are converted to **Odds Ratios** ($Odds Ratio = e^{\beta}$):

| Feature | Coefficient ($\beta$) | Odds Ratio ($e^{\beta}$) | Business Interpretation |
| :--- | :---: | :---: | :--- |
| **`prescribing_decile`** | 0.0196 | **1.0197** | High-decile HCPs are 2.0% more likely to grow MoM due to high base prescribing capacity. |
| **`lag_calls`** | -0.3632 | **0.6955** | Short-term saturation: Each additional call in the immediate prior month reduces the odds of growth slightly. |
| **`trx_trend`** | -0.0489 | **0.9523** | Indicates a stabilization/consolidation phase after a month of high prescribing growth. |
| **`specialty_Primary Care`**| 0.0484 | **1.0496** | Primary Care physicians are **5.0% more likely** to increase prescriptions MoM. |
| **`specialty_Endocrinology`**| 0.0078 | **1.0079** | Endocrinologists are **0.8% more likely** to increase prescriptions. |

---

## 6. Actionable SFE Business Recommendations

The pipeline exports a decision-support table `business_recommendations.csv` divided into three key categories for regional managers:

### 1. Top Territory Growth Opportunities (Jan 2026)
*   **Actionable List**: Territories projected to exceed their target sales.
*   *Example*: **T02 New York Territory** (Rep: Noah Rhodes) projected to achieve **261.03% attainment** in Month 13.
*   *Business Action*: Reallocate local marketing budgets to capitalize on high-attainment momentum.

### 2. Quota Risk Alerts (At-Risk Reps)
*   **Actionable List**: Sales reps in the *High Risk* or *Critical* bands for Q4.
*   *Example*: **R34 Nathan Maldonado** (Milwaukee Territory, Region X) projected at **79.6% Q4 Attainment** (Critical).
*   *Business Action*: Schedule immediate ride-alongs with the Regional Manager to coach on call execution.

### 3. High-Value Underserved Doctors
*   **Actionable List**: Decile 9 & 10 physicians with high prescribing propensity scores ($> 70\%$) but below-median call frequencies.
*   *Example*: A decile 10 cardiologist in a territory with a propensity score of **82.4/100** who has only been visited once.
*   *Business Action*: Direct the assigned rep to make **3 suggested calls** next month to secure the account.
