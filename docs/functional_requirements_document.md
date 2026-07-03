# Functional Requirements Document (FRD)

## Project: Sales Force Effectiveness (SFE) & Market Access Analytics
*   **Version**: 1.0  
*   **Author**: Gauravi  
*   **Date**: July 2026  
*   **Status**: Final  

---

## 1. Data Model & Database Schema

The database `sfe_analytics.db` is built in SQLite. The relationships are structured as a Star Schema centered around geographical territories and healthcare providers.

### Entity Schemas:
1.  **`Dim_Territories`**: Primary key `territory_id`. Contains region name, target call volume, and factors used to calculate territory potential.
2.  **`Dim_Reps`**: Primary key `rep_id`. Foreign key `territory_id` linking 1-to-1 with `Dim_Territories`. Contains representative name and hire date.
3.  **`Dim_HCPs`**: Primary key `hcp_id`. Foreign key `territory_id` linking many-to-1 with `Dim_Territories`. Contains physician name, specialty, and prescribing decile.
4.  **`Fact_Sales_Targets`**: Foreign key `territory_id` and `month_id`. Contains monthly actual and target sales figures.
5.  **`Fact_Call_Adherence`**: Foreign keys `rep_id` and `month_id`. Contains planned calls, completed calls, and adherence percentages.
6.  **`Fact_Market_Share`**: Foreign keys `territory_id` and `month_id`. Contains brand and market-level prescription counts.
7.  **`Fact_Territory_Opportunity`**: Foreign key `territory_id`. Pre-calculated potential sales, actual sales, opportunity gaps, and prioritization ranks.
8.  **`Fact_Underserved_HCPs`**: Foreign keys `hcp_id` and `rep_id`. Actionable targeting metrics for high-value doctors.

---

## 2. KPI Formulas & Calculations

### 2.1 Sales and Quota Attainment
*   **Total Sales**:
    $$\text{Total Sales} = \sum(\text{actual\_sales})$$
*   **Quota Attainment %**:
    $$\text{Quota Attainment \%} = \left( \frac{\sum(\text{actual\_sales})}{\sum(\text{target\_sales})} \right) \times 100$$
*   **Sales Variance**:
    $$\text{Sales Variance} = \text{Total Sales} - \text{Total Target}$$

### 2.2 Call Plan Adherence
*   **Call Adherence %**:
    $$\text{Call Adherence \%} = \left( \frac{\text{Completed Calls}}{\text{Planned Calls}} \right) \times 100$$

### 2.3 Market Share & Detailing Presence
*   **Share of Voice (SOV) %**:
    $$\text{Share of Voice \%} = \left( \frac{\text{Brand Detailing Calls}}{\text{Estimated Total Category Detailing Calls}} \right) \times 100$$
*   **Brand Market Share %**:
    $$\text{Brand Market Share \%} = \left( \frac{\text{Brand TRx}}{\text{Total Market TRx}} \right) \times 100$$

### 2.4 Territory Potential Index (TPI) & Opportunity Gaps
*   **TPI Score** (Standardized 0-100 scale):
    $$\text{TPI Score} = \left( \text{category\_volume\_factor} \times 0.50 + \text{target\_hcp\_count\_factor} \times 0.30 + \text{patient\_volume\_proxy} \times 0.20 \right) \times 100$$
*   **Potential Sales**:
    $$\text{Potential Sales} = \text{TPI Score} \times 800.0$$
*   **Absolute Opportunity Gap**:
    $$\text{Absolute Gap} = \text{Potential Sales} - \text{Predicted Sales}$$
*   **Opportunity Gap %**:
    $$\text{Gap \%} = \left( \frac{\text{Absolute Gap}}{\text{Potential Sales}} \right) \times 100$$

---

## 3. Power BI Dashboard Interactive Specifications

### 3.1 Visual Themes and Colors
*   **Canvas Background**: `#F8F9FA` (Light Grey, 0% transparency).
*   **Theme Color Codes**:
    *   Primary Header/Dark Backgrounds: `#1F4E79` (Deep Navy)
    *   Teal Buttons/Visual Accents: `#00A6A6` (Teal)
    *   Standard Text: Black or Dark Grey
    *   Card Labels: Dark Navy or Charcoal
*   **Status Color Alert Standards (KPI & Attainment)**:
    *   **Success (Emerald)**: `#2ECC71` (Attainment $\ge 100\%$)
    *   **Warning (Amber)**: `#F39C12` (Attainment $80\% - 99\%$)
    *   **Danger (Crimson)**: `#E74C3C` (Attainment $< 80\%$)

### 3.2 Slicers and Filters
*   **Global Filters (Page Sync)**: `Region`, `MonthID`.
*   **Page-Specific Filters**:
    *   `Priority Band` (Critical, High, Medium, Low) on the *Territory Prioritization* page.
    *   `Specialty` (Cardiology, Endocrinology, Primary Care) on the *HCP Targeting* page.

### 3.3 Navigation & Drill-Through Paths
*   **Page Navigation**: Configured as an app-like page navigator bar on the Landing Page.
*   **Territory Drill-Through**: Users can right-click on any territory row in the *Territory Prioritization* matrix, select **Drill-through**, and land on the *Rep Performance* page, which will automatically filter down to the assigned representative and detailed call trends for that territory.

### 3.4 Custom Hover Tooltips
*   Hovering over any territory data point in the opportunity charts must display a popup containing:
    *   `Territory Name`
    *   `Assigned Rep Name`
    *   `Total Sales` vs. `Total Target`
    *   `Sales Variance %`
    *   `Call Adherence %`

---

## 4. Predictive Modeling Functional Specifications

### 4.1 Territory Sales Forecast (Linear Regression)
*   **Model**: Ordinary Least Squares (OLS) Linear Regression.
*   **Features ($X$)**:
    *   `month_idx` (Time trend index)
    *   `lag_1` (Prior month's actual sales)
    *   `rolling_3m_avg` (3-month rolling average of sales)
*   **Target ($y$)**: `actual_sales` (Month $m$ actual sales).
*   **Validation Strategy**: Time Series Cross-Validation (6 folds) on Months 7 through 12, comparing MAPE and MAE against a Naïve Forecast baseline.
*   **Intervals**: 95% Confidence Intervals calculated using Residual Standard Error:
    $$\hat{y} \pm 1.96 \times S_e$$

### 4.2 Rep Performance Risk Projector
*   **Pace Logic** (Run date simulation: November 30):
    $$\text{Projected Q4 Sales} = \text{Oct Actual} + \text{Nov Actual} + \text{Dec Predicted}$$
    $$\text{Projected Attainment \%} = \left( \frac{\text{Projected Q4 Sales}}{\text{Q4 Target}} \right) \times 100$$
*   **Risk Categorization**:
    *   $\ge 100\%$ Attainment $\rightarrow$ `Low Risk`
    *   $90\% - 99.9\%$ Attainment $\rightarrow$ `Moderate Risk`
    *   $80\% - 89.9\%$ Attainment $\rightarrow$ `High Risk`
    *   $< 80\%$ Attainment $\rightarrow$ `Critical`

### 4.3 HCP Prescribing Propensity Classifier (Logistic Regression)
*   **Model**: Binary Logistic Regression.
*   **Features ($X$)**:
    *   `prescribing_decile` (1-10)
    *   `lag_calls` (Brand calls completed in prior month)
    *   `trx_trend` (Brand TRx MoM change: $m-1$ TRx minus $m-2$ TRx)
    *   `specialty` (One-hot encoded)
*   **Target ($y$)**: `increase_next_month` (1 if TRx in month $m > m-1$, else 0).
*   **Evaluation Metrics**: Report Accuracy, Precision, Recall, F1-Score, and ROC-AUC on the Month 12 holdout set.
