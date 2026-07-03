# Stakeholder Requirements & Project Scope

This document establishes the business context, stakeholder needs, requirements log, and KPI definitions for the **Sales Force Effectiveness (SFE) & Market Access Analytics** project.

---

## 1. Stakeholder Interview Script

Below are the transcript summaries from the requirement-gathering interviews conducted with key commercial stakeholders.

### Interview 1: VP of Sales (Executive Sponsor)
*   **Context**: The VP needs high-level visibility into field force execution and territory-level sales performance to make strategic resource allocation decisions.
*   **Q: What is your primary pain point with the current reporting setup?**
    *   *A*: "It takes my operations team three weeks after the end of a quarter to tell me which territories underperformed and why. By then, the data is stale, and we've lost another month of sales. I need to see which regions and territories are lagging *during* the quarter, and I need a way to easily identify which sales reps are struggling to meet their call plans before it impacts our market share."
*   **Q: What specific questions do you want this dashboard to answer?**
    *   *A*: "I want to know: Which regions are driving our growth? Which territories have the highest untapped potential where we are under-indexing? And most importantly, can we predict which territories will miss their quarterly targets so we can intervene early?"

### Interview 2: Brand Manager (Marketing & Market Access)
*   **Context**: The Brand Manager focuses on market share, competitor dynamics, Share of Voice (SOV), and HCP targeting.
*   **Q: How do you evaluate whether the sales team is executing the brand strategy?**
    *   *A*: "We look at Share of Voice (SOV). We need to ensure our reps are reaching the high-prescribing physicians (Deciles 8–10) in their territories. Right now, I don't know if our low market share in certain areas is because doctors aren't prescribing our drug, or because our reps simply aren't calling on the right doctors. I need to see the overlap between high-decile HCPs and actual rep call frequency."
*   **Q: What metric is most critical for you to track?**
    *   *A*: "Share of Voice (SOV) and HCP coverage. If a high-volume cardiologist hasn't been visited in 60 days, that's a massive risk. I want to see a list of high-potential HCPs who are being underserved by our field force."

### Interview 3: Field Sales Operations Manager
*   **Context**: Operations manages the CRM (Veeva/Salesforce), territory alignments, call plans, and data integrity.
*   **Q: What data quality issues do you frequently encounter?**
    *   *A*: "Reps sometimes log calls late, leading to missing records or duplicates. We also have duplicate HCP profiles in the CRM because of spelling differences (e.g., 'Dr. John Smith' vs. 'John Smith MD'). Any pipeline we build needs to handle these anomalies without breaking."
*   **Q: How do you measure rep execution?**
    *   *A*: "Call Plan Adherence. Every rep has a target number of calls they are supposed to make to target HCPs each month. We measure their completed calls against this plan. I need this calculated at the rep, territory, and regional levels."

### Interview 4: Regional Sales Manager (Region X)
*   **Context**: Represents the field managers who coach reps and execute the sales plan locally.
*   **Q: What challenges are your reps facing in the field?**
    *   *A*: "In Region X, we've had high rep turnover, which means many territories are vacant or covered by new hires who are still learning the science. We suspect our call adherence is low, but we don't have a clear way to show leadership how much of our sales deficit is due to vacancies/adherence versus market access issues (e.g., local formulary exclusions)."

---

## 2. MoSCoW Requirements Log

Based on the stakeholder interviews, the project requirements are prioritized as follows:

| Req ID | Requirement Description | Category | Priority | Stakeholder |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-001** | Calculate monthly Call Plan Adherence % at Rep, Territory, and Regional levels. | Functional | **Must Have** | Field Ops / VP Sales |
| **REQ-002** | Reconcile and clean CRM call logs, handling duplicate HCP IDs and missing call records. | Data | **Must Have** | Field Ops |
| **REQ-003** | Track monthly New Prescriptions (NRx) and Total Prescriptions (TRx) trends by HCP and Territory. | Functional | **Must Have** | Brand Manager |
| **REQ-004** | Calculate Share of Voice (SOV) % per territory. | Functional | **Must Have** | Brand Manager |
| **REQ-005** | Build a Territory Potential Index to rank territories based on market opportunity. | Analytics | **Must Have** | VP Sales |
| **REQ-006** | Identify and list "Underserved High-Potential HCPs" (Deciles 9-10 with below-median call frequency). | Functional | **Must Have** | Brand Manager |
| **REQ-007** | Build an interactive Power BI dashboard with Executive, Territory, and Rep views. | UI | **Must Have** | VP Sales / Regional Mgr |
| **REQ-008** | Enable dynamic filtering by Region, Territory, Rep, and Month across the dashboard. | UI | **Should Have** | Regional Mgr |
| **REQ-009** | Build a predictive model to forecast next-month territory sales. | Analytics | **Should Have** | VP Sales |
| **REQ-010** | Flag at-risk reps whose projected quarterly attainment is below 90% of target. | Analytics | **Should Have** | Field Ops / Regional Mgr |
| **REQ-011** | Analyze and isolate the root cause of Region X's underperformance. | Analysis | **Should Have** | VP Sales / Region X Mgr |
| **REQ-012** | Implement hover-over tooltips explaining KPI calculations on dashboard cards. | UI | **Could Have** | Field Ops |

---

## 3. KPI Definitions

To ensure consistency, the following mathematical formulas will be used throughout the SQL and dashboard layers:

### 1. Call Plan Adherence (%)
Measures the percentage of planned HCP visits that were actually completed.
$$\text{Call Plan Adherence} = \left( \frac{\text{Completed Calls}}{\text{Planned Calls}} \right) \times 100$$
*   *Note*: Completed calls are identified where the call status is 'Completed' and the date is valid.

### 2. Share of Voice (SOV %)
Measures the brand's share of promotional activity (calls) relative to the estimated total category activity.
$$\text{Share of Voice (SOV)} = \left( \frac{\text{Brand Calls}}{\text{Estimated Total Category Calls}} \right) \times 100$$
*   *Note*: Estimated Total Category Calls is modeled based on the territory's market size and average competitor activity.

### 3. Territory Potential Index (TPI)
A weighted composite score (0 to 100) representing the sales opportunity of a territory.
$$\text{TPI} = (0.5 \times \text{Scaled Category TRx Volume}) + (0.3 \times \text{Target Specialty HCP Count Score}) + (0.2 \times \text{Patient Volume Proxy Score})$$

### 4. Territory Opportunity Gap
Identifies territories where sales are lagging relative to their market potential.
$$\text{Opportunity Gap} = \text{Territory Potential Index (scaled to sales units)} - \text{Actual Sales}$$
*   *Interpretation*: A high positive gap indicates an under-indexed territory with high growth potential.

### 5. Sales Target Attainment (%)
Measures sales performance against the set quota.
$$\text{Sales Target Attainment} = \left( \frac{\text{Actual Sales}}{\text{Target Sales}} \right) \times 100$$
