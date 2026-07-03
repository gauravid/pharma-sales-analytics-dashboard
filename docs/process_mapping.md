# Process Mapping & Root-Cause Analysis

This document outlines the business process improvement from the current manual reporting method to our automated analytics solution, and defines the diagnostic framework for analyzing Region X's underperformance.

---

## 1. As-Is Process Map (Current State)

Currently, territory performance reviews are retrospective, manual, and slow. The process takes several weeks, meaning insights are acted upon when they are already outdated.

```mermaid
graph TD
    A[Quarter Ends] --> B[Request CRM data from IT & Claims data from Vendor]
    B --> C{Data Received? <br/> Wait 1-2 Weeks}
    C -- Yes --> D[Manual Excel Reconciliation <br/> VLOOKUPs, Pivots, Manual Error Corrections]
    C -- No --> B
    D --> E[Create Static PowerPoint Deck]
    E --> F[Email PDF Reports to Regional Managers]
    F --> G[Retrospective Review Meeting <br/> ~3-4 Weeks Post-Quarter]
    G --> H[Reactions are Lagging <br/> Cannot recover lost sales]
```

---

## 2. To-Be Process Map (Future State)

The future state automates the data ingestion and transformation, providing daily/weekly self-service dashboard access, drill-down capabilities, and predictive risk alerts.

```mermaid
graph TD
    A[CRM & Claims Data Source] -->|Automated Load| B[(sfe_analytics.db)]
    B -->|SQL Pipeline| C[Calculate KPIs <br/> Adherence, NRx/TRx, SOV, TPI]
    C -->|Automatic Refresh| D[Power BI Dashboard]
    D --> E[Self-Service Exploration]
    
    E --> F1[VP of Sales: <br/> High-level Regional Attainment & TPI]
    E --> F2[Regional Managers: <br/> Rep Adherence & At-Risk Flags]
    E --> F3[Sales Reps: <br/> Underserved High-Decile HCP Lists]
    
    C -->|Python Predictive Model| G[Forecast Next-Month Sales & Flag At-Risk Reps]
    G -->|Import| D
    
    F2 & G --> H[Proactive Coaching & Resource Allocation]
```

---

## 3. Root-Cause Issue Tree: Why is Region X Underperforming?

To diagnose the sales deficit in Region X, we structure our hypotheses into four primary branches. The SQL queries in Phase 2 and the dashboard in Phase 3 will validate which of these branches are the true drivers.

```mermaid
graph TD
    Root["Region X Sales Deficit <br/> (Sales vs. Target Gap)"] --> Branch1["Sales Force Execution"]
    Root --> Branch2["Market Access / Payer"]
    Root --> Branch3["Targeting & Message Mix"]
    Root --> Branch4["External Market Factors"]

    %% Branch 1 Details
    Branch1 --> B1_1["Low Call Plan Adherence <br/> (Reps not making planned visits)"]
    Branch1 --> B1_2["High Rep Turnover / Vacancies <br/> (New hires, open territories)"]
    Branch1 --> B1_3["Poor Rep Skill / Science Knowledge"]

    %% Branch 2 Details
    Branch2 --> B2_1["Formulary Exclusions <br/> (Apexacare blocked or non-preferred)"]
    Branch2 --> B2_2["High Patient Co-pays <br/> (Prior-authorization hurdles)"]

    %% Branch 3 Details
    Branch3 --> B3_1["Under-indexing High-Decile HCPs <br/> (Reps visiting low-volume doctors)"]
    Branch3 --> B3_2["Low Share of Voice <br/> (Competitors out-calling our reps)"]
    Branch3 --> B3_3["Ineffective detailing messages"]

    %% Branch 4 Details
    Branch4 --> B4_1["Local Competitor Launch <br/> (Aggressive pricing/rebates)"]
    Branch4 --> B4_2["Demographic / Disease Prevalence shifts <br/> (Fewer target patients)"]
```
Work in Phase 2 will focus on using SQL queries to test these hypotheses, specifically comparing Region X's **Call Adherence (B1_1)**, **Rep Tenure (B1_2)**, **Share of Voice (B3_2)**, and **HCP Coverage (B3_1)** against other regions.
