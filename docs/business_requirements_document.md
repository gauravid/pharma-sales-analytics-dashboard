# Business Requirements Document (BRD)

## Project: Sales Force Effectiveness (SFE) & Market Access Analytics
*   **Version**: 1.0  
*   **Author**: Gauravi  
*   **Date**: July 2026  
*   **Status**: Final  

---

## 1. Executive Summary & Background

In the pharmaceutical commercial sector, sales leadership must quickly identify and address underperformance in geographical sales territories, sales representative execution, and prescribing physician targeting. 

Currently, sales performance reviews are manual, retroactive, and siloed:
*   Sales representatives log CRM activities (Veeva CRM/Salesforce) in isolation from patient-level prescription claims.
*   Market Access teams track brand formulary tier standings independently of field-force activities.
*   Analyzing a single underperforming region (like Region X) takes between **one to three weeks** of manual spreadsheet reconciliation, resulting in delayed coaching, lost revenue, and poor market alignment.

This project delivers an automated **Sales Force Effectiveness & Market Access Analytics platform** that integrates claims, CRM, and target data to provide regional managers and VPs of Sales with real-time, actionable insights.

---

## 2. Business Objectives

The key business goals of this analytics platform are:
1.  **Reduce Manual Reporting Overhead**: Eliminate manual Excel tracking. Automate the end-to-end extraction, transformation, and visual reporting of SFE metrics, reducing latency from weeks to minutes.
2.  **Optimize Field Resource Allocation**: Ranks sales territories based on a standardized **Territory Potential Index (TPI)** to identify under-indexing territories and target resources where the market opportunity is highest.
3.  **Prevent Revenue Leakage**: Proactively identify high-value prescribers (Deciles 9 & 10) who are underserved (visited less than the territory median call frequency) to recover lost prescription volume.
4.  **Proactive Risk Management**: Flag sales representatives at risk of missing quarterly targets by November 30 (mid-Q4), allowing regional managers to provide targeted field coaching before the quarter ends.
5.  **Explainable Forecasting**: Deliver monthly territory-level sales forecasts with 95% confidence intervals, giving commercial teams an explainable, forward-looking view to adjust inventory and quotas.

---

## 3. Project Scope Boundaries

### In-Scope:
*   Ingestion of sales targets, sales representative tenure, CRM call logs, and prescription claims.
*   Transformation and calculation of SFE KPIs (Call Adherence %, MoM TRx Change %, Share of Voice %, and TPI Gaps).
*   Development of a self-service, interactive Power BI dashboard featuring executive, territory, representative, and HCP views.
*   Implementation of lightweight, explainable machine learning models (Linear Regression for forecasting, Logistic Regression for physician prescribing likelihood).
*   Exporting predictive model outputs and actionable recommendations to flat tables for dashboard integration.

### Out-of-Scope:
*   Direct read/write synchronization with live CRM production databases (data is ingested via scheduled file extracts/staged databases).
*   Direct processing of physician orders or sample tracking.
*   Updating physician license details or medical registry profiles.
*   Automated scheduling of field activities or automated email notifications to HCPs.

---

## 4. Key SFE Performance Metrics (KPIs)

The platform will calculate and report the following core KPIs:
*   **Quota Attainment %**: Measures actual territory sales performance against quotas.
*   **Call Plan Adherence %**: Tracks the percentage of planned detailing calls that are successfully completed.
*   **Share of Voice (SOV) %**: Measures our brand's detailing presence relative to the total competitive market detailing.
*   **Territory Potential Index (TPI)**: A standardized weight-based score representing the commercial capacity of a territory.
*   **Opportunity Gap (USD)**: The financial difference between a territory's calculated commercial potential and its actual sales.
*   **Projected Q4 Quota Attainment**: A predictive mid-quarter projection of a representative's quarter-end target attainment.

---

## 5. Business Risks & Mitigation Strategies

| Risk Description | Impact | Probability | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **Data Quality & Late Detailing Logs**: Sales reps logging CRM visits late or incomplete call plans. | High | Medium | Implement automated pre-training data audits checking for missing records and Z-score outliers. Map missing entries to a baseline (e.g. 0 calls) to protect calculation integrity. |
| **User Adoption Lag**: Field managers bypassing the dashboard and reverting to manual Excel tracking. | High | Low | Design the dashboard with a clean Landing Page, single-click Page Navigator buttons, and interactive drill-through paths to make navigation simple and intuitive. |
| **ML Model "Black-Box" Distrust**: Leadership rejecting forecasts or risk flags due to lack of explainability. | Medium | Medium | Use simple, explainable models (Linear and Logistic Regression) and document their exact coefficients and odds ratios in the developer guide. Report accuracy compared to a Naïve Baseline. |

---

## 6. Project Success Criteria

*   **100% Data Reconciliation**: The database must pass all 10 automated data integrity and business rules audits before reporting.
*   **Visual Response Time**: Dashboards must load and filter in less than **2 seconds** upon slicing.
*   **Forecasting Accuracy**: The territory sales forecasting model must achieve a Mean Absolute Percentage Error (MAPE) of **$< 10\%$** on validation sets.
*   **Actionable Impact**: The platform must automatically identify and extract a prioritized list of high-value, underserved HCPs and critical opportunity territories during every monthly run.
