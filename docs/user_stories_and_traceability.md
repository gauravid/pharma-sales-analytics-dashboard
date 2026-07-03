# User Stories, Acceptance Criteria & Traceability Matrix

## Project: Sales Force Effectiveness (SFE) & Market Access Analytics
*   **Version**: 1.0  
*   **Author**: Gauravi  
*   **Date**: July 2026  
*   **Status**: Final  

---

## 1. User Stories & Acceptance Criteria

### US-01: Executive Regional Attainment (VP of Sales)
*   **User Story**: As a VP of Sales, I want to view high-level regional quota attainment and call adherence KPIs on a single page, so that I can instantly identify underperforming regions and align detailing strategies.
*   **Acceptance Criteria**:
    *   **AC-01.1**: Given the Executive Overview page is loaded, When no filters are active, Then the Regional Sales Attainment bar chart must show all regions, with the lowest-attaining region sorted to the bottom.
    *   **AC-01.2**: Given the regional bar chart, When a user clicks on "Region X", Then the entire page's KPI cards and scatter plot must filter to display only Region X's data.

### US-02: Territory Drill-Through (Regional Manager)
*   **User Story**: As a Regional Sales Manager, I want to right-click on an underperforming territory and drill down into the rep's detailed profile, so that I can review call activities and tenure history.
*   **Acceptance Criteria**:
    *   **AC-02.1**: Given the Territory Prioritization grid, When the user right-clicks on a territory row and selects "Drill-through", Then Power BI must open the Rep Performance page.
    *   **AC-02.2**: When the Rep Performance page opens via drill-through, Then the page must be automatically filtered to show only the assigned representative's tenure, month-by-month sales, and call adherence.

### US-03: Share of Voice vs. Market Share (Brand Manager)
*   **User Story**: As a Brand Manager, I want to see a scatter plot comparing Share of Voice (SOV) against brand market share by territory, so that I can check if higher detailing presence correlates with market share gains.
*   **Acceptance Criteria**:
    *   **AC-03.1**: Given the Executive Overview page, When viewing the scatter plot, Then the X-axis must represent `Share of Voice %`, the Y-axis must represent `Apexacare Market Share %`, and each bubble must represent an individual territory.
    *   **AC-03.2**: When a bubble is hovered over, Then a tooltip must display the Territory Name, Representative Name, and total sales.

### US-04: Underserved HCP Identification (Field Ops Analyst)
*   **User Story**: As a Field Ops Analyst, I want to extract a list of high-volume HCPs (prescribing deciles 9 & 10) who are visited less than the territory median frequency, so that we can target under-served physicians.
*   **Acceptance Criteria**:
    *   **AC-04.1**: Given the HCP Targeting table visual, When filters are applied, Then the list must display only HCPs in prescribing decile 9 or 10.
    *   **AC-04.2**: The grid table must display `Completed Calls Count` side-by-side with the `Territory Median Calls` and `Potential Lost Revenue (USD)` to verify the target opportunity.

### US-05: Mid-Quarter Rep Performance Projections (Regional Manager)
*   **User Story**: As a Regional Sales Manager, I want to see a projection of reps' quarter-end quota attainment, so that I can proactively identify and coach reps flagged in the "Critical" or "High Risk" bands.
*   **Acceptance Criteria**:
    *   **AC-05.1**: Given the Forecast & Risk page, When viewing the rep risk table, Then the projected Q4 attainment % must combine actual Oct/Nov sales with the December forecast.
    *   **AC-05.2**: The visual must highlight reps with projected attainment $< 80\%$ as `Critical` and $80\% - 89.9\%$ as `High Risk` using red and orange warning indicators.

### US-06: Forecast Accuracy Transparency (Field Ops Analyst)
*   **User Story**: As a Field Ops Analyst, I want to review the validation metrics of our forecasting model compared to a naïve baseline, so that I can explain and justify the model's accuracy to sales leadership.
*   **Acceptance Criteria**:
    *   **AC-06.1**: Given the model performance logs, When reviewing the cross-validation metrics, Then the average MAE and MAPE of the Linear Regression model must be displayed side-by-side with the Naïve Baseline.
    *   **AC-06.2**: The Linear Regression model must demonstrate a lower MAPE than the Naïve baseline to be approved for dashboard import.

### US-07: SFE Business Recommendations (Regional Manager)
*   **User Story**: As a Regional Sales Manager, I want a dedicated list of automated business recommendations, so that I can quickly review growth opportunities, rep alerts, and doctor call suggestions.
*   **Acceptance Criteria**:
    *   **AC-07.1**: Given the business recommendations visual, When a user filters by "Sales Rep Alert", Then the list must show reps in the critical and high-risk bands, sorted by projected attainment ascending.
    *   **AC-07.2**: When a user filters by "High-Value Underserved Doctor", Then the list must display physicians with a prescribing propensity score $> 70\%$ who are visited below the territory median.

---

## 2. Traceability Matrix

This matrix traces requirements from initial business needs through functional specifications, user stories, test cases, and dashboard implementations.

| Req ID | Business Requirement Description | Functional Spec ID | User Story ID | Test Case ID | Dashboard Visual / Implementation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BR-01** | Reconcile CRM logs and actual sales | FR-1.1 (Data Schema) | US-01 | TC-01 | SQL Joins / Power BI Data Model Relationship View |
| **BR-02** | Track monthly call adherence | FR-2.2 (Adherence KPI)| US-01 | TC-02 | `Fact_Call_Adherence[adherence_pct]` KPI Card & Table |
| **BR-03** | Ranks sales territories by potential | FR-2.4 (TPI Formula) | US-02 | TC-03 | `Fact_Territory_Opportunity` Matrix Grid & Bar Chart |
| **BR-04** | Identify underserved decile 9 & 10 HCPs| FR-2.4 (HCP Targeting)| US-04 | TC-04 | *HCP Targeting* Page Table Grid Visual |
| **BR-05** | Track market share vs. detailing | FR-2.3 (SOV / Share)  | US-03 | TC-05 | *Executive Overview* page Scatter Plot Chart |
| **BR-06** | Forecast next month's territory sales | FR-4.1 (Regression)   | US-06 | TC-06 | `territory_forecast.csv` loaded to Power BI |
| **BR-07** | Generate 95% forecast intervals | FR-4.1 (Confidence CI)| US-06 | TC-07 | Table showing Lower/Forecast/Upper estimates |
| **BR-08** | Flag reps at risk mid-quarter | FR-4.2 (Pace logic)   | US-05 | TC-08 | *Forecast & Risk* page Rep Risk Table & Donut |
| **BR-09** | Display model performance and comparison| FR-4.3 (Metrics)      | US-06 | TC-09 | `model_metrics.csv` loaded to Power BI table visual |
| **BR-10** | Provide automated decision recommendations| FR-4.3 (Recommendations)| US-07 | TC-10 | List of Growth, Rep, and HCP Actionable recommendations |
| **BR-11** | Enable territory drill-through | FR-3.3 (Drill-through)| US-02 | TC-11 | Drill-through configuration from Prioritization to Rep |
| **BR-12** | Display hover tooltip context | FR-3.4 (Tooltips)     | US-03 | TC-12 | Custom Tooltip page containing rep details, sales gap |
