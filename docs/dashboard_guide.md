# SFE Power BI Dashboard Development & Setup Guide

This document is a step-by-step guide for developers to build the **Sales Force Effectiveness (SFE) & Market Access Analytics** Power BI dashboard. It implements a clean Star Schema data model, advanced DAX measures, dynamic drill-throughs, custom tooltips, navigation buttons, and a professional design system.

---

## 1. Design System & Theme

To ensure a polished, professional look, configure the dashboard theme with the following color palette:

*   **Primary (Deep Navy)**: `#1F4E79` (Visual headers, card titles, side navigation bar)
*   **Secondary (Teal)**: `#00A6A6` (Primary data bars, line charts, positive indicators)
*   **Accent (Amber)**: `#F39C12` (Warning alerts, medium-level performance)
*   **Success (Emerald)**: `#2ECC71` (Completed calls, quota attainment $\ge 100\%$)
*   **Danger (Crimson)**: `#E74C3C` (At-risk reps, low call adherence $< 70\%$, quota $< 80\%$)
*   **Background (Light Grey)**: `#F8F9FA` (Canvas background)
*   **Card Background**: `#FFFFFF` (White with subtle borders and shadows)
*   **Typography**: *Segoe UI* or *Arial* (Standard commercial sans-serif)

---

## 2. Data Connection, Refresh & Performance

### Data Import
1.  Open Power BI Desktop.
2.  Select **Get Data** $\rightarrow$ **Text/CSV**.
3.  Load the following 7 CSV files exported from `data/exports/`:
    *   `reps.csv` (Dim_Reps)
    *   `territories.csv` (Dim_Territories)
    *   `hcps.csv` (Dim_HCPs)
    *   `call_adherence.csv` (Fact_Call_Adherence)
    *   `market_share.csv` (Fact_Market_Share)
    *   `territory_opportunity.csv` (Fact_Territory_Opportunity)
    *   `underserved_hcps.csv` (Fact_Underserved_HCPs)

### Automated Data Refresh Process
To update the dashboard monthly with new CRM or claims extracts:
1.  Run the SQL query pipeline using the terminal command:
    ```powershell
    python scripts/run_queries.py
    ```
    This automatically refreshes the tables in the SQLite database and writes new CSV files to `data/exports/`.
2.  In Power BI, click the **Refresh** button in the Home ribbon.
3.  All visuals, KPI cards, tables, and slicers will update automatically with the new data.

### Performance Optimization Best Practices
To ensure fast page load times and optimal memory utilization:
*   **Disable Auto Date/Time**: Go to *File $\rightarrow$ Options and Settings $\rightarrow$ Options $\rightarrow$ Global/Current File $\rightarrow$ Data Load* and uncheck **Auto Date/Time**. This prevents Power BI from generating hidden date tables for every date field, significantly reducing file size.
*   **Hide Surrogate Key Columns**: In the Model View, select key columns (e.g., `territory_id`, `rep_id`, `hcp_id`, `month_id`) in fact tables and select **Is Hidden = True**. This prevents users from selecting keys in visuals, ensuring they use the descriptive columns in the dimension tables.
*   **Use Measures instead of Calculated Columns**: Do not write calculations as calculated columns in fact tables. Write them as DAX measures to keep model sizes small and leverage Power BI's active filter context evaluation.
*   **Keep Relationships Single-Direction**: Unless bidirectional cross-filtering is explicitly needed (such as mapping reps to territories to filter rep details), use a **Single** cross-filter direction pointing from dimensions (1) to facts (*).

---

## 3. Data Model Setup (Star Schema)

We structure our model as a **Star Schema** to optimize performance, simplify DAX writing, and prevent circular dependencies.

```
       [Dim_Date] (1)                  [Dim_Territories] (1)
           │                                 │
           ├─── Fact_Sales_Targets (*)       ├─── Fact_Sales_Targets (*)
           ├─── Fact_Call_Adherence (*)      ├─── Fact_Call_Adherence (*)
           ├─── Fact_Market_Share (*)        ├─── Fact_Market_Share (*)
           └─── Fact_Terr_Opportunity (*)    ├─── Fact_Terr_Opportunity (*)
                                             └─── Dim_Reps (1) [via territory_id]
       
       [Dim_HCPs] (1) ─── Fact_Underserved_HCPs (*) [on hcp_id]
```

### Table Classifications

*   **Dimension Tables (Lookup Tables)**:
    *   `Dim_Date`: Created via DAX (see formulas).
    *   `Dim_Territories`: Imported from `territories.csv` (Key: `territory_id`).
    *   `Dim_Reps`: Imported from `reps.csv` (Key: `rep_id`).
    *   `Dim_HCPs`: Imported from `hcps.csv` (Key: `hcp_id`).
*   **Fact Tables (Transaction Tables)**:
    *   `Fact_Sales_Targets`: Imported from `market_share.csv` (since it contains actual and target sales).
    *   `Fact_Call_Adherence`: Imported from `call_adherence.csv`.
    *   `Fact_Market_Share`: Imported from `market_share.csv`.
    *   `Fact_Territory_Opportunity`: Imported from `territory_opportunity.csv`.
    *   `Fact_Underserved_HCPs`: Imported from `underserved_hcps.csv`.

### Model Relationships (Corrected)
To avoid ambiguity and ensure accurate filter propagation, configure relationships as follows:

1.  **Date Relationships**:
    *   `Dim_Date[MonthID]` (1) $\rightarrow$ `Fact_Sales_Targets[month_id]` (*) [Active, Single]
    *   `Dim_Date[MonthID]` (1) $\rightarrow$ `Fact_Call_Adherence[month_id]` (*) [Active, Single]
    *   `Dim_Date[MonthID]` (1) $\rightarrow$ `Fact_Market_Share[month_id]` (*) [Active, Single]
    *   `Dim_Date[MonthID]` (1) $\rightarrow$ `Fact_Territory_Opportunity[month_id]` (*) [Active, Single]
2.  **Territory Relationships**:
    *   `Dim_Territories[territory_id]` (1) $\rightarrow$ `Fact_Sales_Targets[territory_id]` (*) [Active, Single]
    *   `Dim_Territories[territory_id]` (1) $\rightarrow$ `Fact_Call_Adherence[territory_id]` (*) [Active, Single]
    *   `Dim_Territories[territory_id]` (1) $\rightarrow$ `Fact_Market_Share[territory_id]` (*) [Active, Single]
    *   `Dim_Territories[territory_id]` (1) $\rightarrow$ `Fact_Territory_Opportunity[territory_id]` (*) [Active, Single]
    *   `Dim_Territories[territory_id]` (1) $\rightarrow$ `Dim_Reps[territory_id]` (1) [Active, Both] (Enables filtering reps by territory).
3.  **HCP Relationships**:
    *   `Dim_HCPs[hcp_id]` (1) $\rightarrow$ `Fact_Underserved_HCPs[hcp_id]` (*) [Active, Single]

> [!IMPORTANT]
> Do NOT create a direct relationship between `Dim_Reps` and `Fact_Territory_Opportunity`. Doing so creates redundant paths and filter ambiguity because Reps map to Territories 1-to-1. Allow filters to flow from Reps $\rightarrow$ Territories $\rightarrow$ Opportunity.

---

## 4. Slicer & Filter Design

To give stakeholders self-service drill-down capability, the dashboard implements a standard slicer panel placed on the right or top margin of each page. The filter design utilizes the following global filters:

| Slicer Field | Source Table | Type | Filter Level | Business Objective |
| :--- | :--- | :--- | :--- | :--- |
| **Region** | `Dim_Territories` | Single Select Dropdown | Global | Allows regional managers to view their territory cluster. |
| **Territory** | `Dim_Territories` | Multi-Select Search List | Global | Enables deep dive into individual sales territories. |
| **Month** | `Dim_Date` | Horizontal Button Slicer | Global | Selects the specific reporting month or time period. |
| **Rep** | `Dim_Reps` | Single Select Dropdown | Global / Page 3 | Filters metrics to evaluate specific sales reps. |
| **Product** | `Fact_Market_Share` | Horizontal Buttons | Global / Page 1 & 4 | Toggles between *Apexacare* and competitors (*Competitor_A*, *Competitor_B*). |

---

## 5. DAX Calculations

Create a dedicated measures table named `_Measures` and write the following DAX formulas:

### 1. Date Table Generation
Go to **Modeling** $\rightarrow$ **New Table** and enter:
```dax
Dim_Date = 
ADDCOLUMNS(
    CALENDAR(DATE(2025, 1, 1), DATE(2025, 12, 31)),
    "Year", YEAR([Date]),
    "MonthNum", MONTH([Date]),
    "MonthName", FORMAT([Date], "MMMM"),
    "MonthID", FORMAT([Date], "YYYY-MM"),
    "Quarter", "Q" & FORMAT([Date], "Q")
)
```

### 2. Core SFE Metrics
```dax
Total Sales = SUM(Fact_Sales_Targets[actual_sales])

Total Target = SUM(Fact_Sales_Targets[target_sales])

Sales Variance = [Total Sales] - [Total Target]

Sales Variance % = DIVIDE([Sales Variance], [Total Target], 0) * 100

Quota Attainment % = DIVIDE([Total Sales], [Total Target], 0) * 100

Call Plan Adherence % = AVERAGE(Fact_Call_Adherence[adherence_pct])

Share of Voice % = AVERAGE(Fact_Market_Share[share_of_voice_pct])

Apexacare Market Share % = AVERAGE(Fact_Market_Share[brand_market_share_pct])

Total Opportunity Gap = SUM(Fact_Territory_Opportunity[opportunity_gap])
```

### 3. Advanced SFE Analysis Measures
```dax
Average Sales per Rep = DIVIDE([Total Sales], DISTINCTCOUNT(Dim_Reps[rep_id]), 0)

Territory Sales Rank = RANKX(ALL(Dim_Territories), [Total Sales], , DESC)

At Risk Territory Count = 
CALCULATE(
    DISTINCTCOUNT(Dim_Territories[territory_id]), 
    FILTER(Fact_Call_Adherence, Fact_Call_Adherence[adherence_pct] < 70)
)

Top Performing Rep = 
CALCULATE(
    SELECTEDVALUE(Dim_Reps[rep_name]), 
    TOPN(1, ALL(Dim_Reps), [Quota Attainment %], DESC)
)
```

---

## 6. Page-by-Page Specifications & Visual Mockups

The dashboard contains a Landing Page and 4 analytical pages. Below are the layout configurations and visual mockups.

### Dashboard Landing Page
*   **Purpose**: The entry point for users, giving an overview of the brand and letting them navigate to key areas.
*   **Visual Layout**:
    *   **Header Section**: Title: "Sales Force Effectiveness & Market Access Analytics", Subtitle: "Commercial Performance Executive Dashboard".
    *   **Metadata Card**: "Last Refresh Date: [Latest Month Date]", "Data Quality Status: All Checks Passed (10/10)".
    *   **Navigation Buttons (Large Cards)**:
        1.  *Executive Overview*: Link to Page 1
        2.  *Territory Opportunity*: Link to Page 2
        3.  *Rep Performance*: Link to Page 3
        4.  *HCP Targeting*: Link to Page 4

---

### Page 1: SFE Executive Overview
*   **Purpose**: Provides the VP of Sales with high-level regional sales, attainment, call adherence, and Share of Voice metrics.
*   **Visual Layout**:
    *   **KPI Cards**: `Total Sales` (Formatted as Currency), `Quota Attainment %`, `Call Plan Adherence %`, `Share of Voice %`.
    *   **Bar Chart**: Sales Attainment % by Region (ordered descending, showing Region X at the bottom).
    *   **Scatter Plot**: Share of Voice % (X-Axis) vs. Apexacare Market Share % (Y-Axis), with bubbles representing territories.
    *   **Trend Line**: Monthly Sales vs. Target Trend.

![Page 1 Mockup](file:///C:/Users/Gauravi/.gemini/antigravity/brain/39f934dc-32e1-4b85-9ff5-cb976f9690d5/executive_overview_mockup_1782932233008.png)

---

### Page 2: Territory Prioritization
*   **Purpose**: Helps regional sales managers identify which territories are under-indexing relative to their market potential.
*   **Visual Layout**:
    *   **Horizontal Bar Chart**: Ranked list of territories by `Total Opportunity Gap` (USD).
    *   **KPI Cards**: `Total Opportunity Gap`, `At Risk Territory Count`.
    *   **Matrix Grid**: Territory ID, Territory Name, TPI Score, Potential Sales, Actual Sales, Opportunity Gap, and Priority Band.
    *   **Filters**: Slicers for `Region` and `Priority Band` (`Critical`, `High`, `Medium`, `Low`).

![Page 2 Mockup](file:///C:/Users/Gauravi/.gemini/antigravity/brain/39f934dc-32e1-4b85-9ff5-cb976f9690d5/territory_prioritization_mockup_1782932247912.png)

---

### Page 3: Representative Performance
*   **Purpose**: Focuses on sales rep execution, call activity, quota attainment, and experience.
*   **Visual Layout**:
    *   **Rep Grid Table**: Rep Name, Territory, Hire Date (Tenure), Quota Attainment %, Call Adherence %, Completion Rate %, and No-Show Rate.
    *   **Scatter Plot**: Call Adherence % (X-Axis) vs. Quota Attainment % (Y-Axis) to identify correlation.
    *   **KPI Cards**: `Average Sales per Rep`, `Top Performing Rep`.
    *   **Slicers**: `Region`, `Territory`, and `Month`.

![Page 3 Mockup](file:///C:/Users/Gauravi/.gemini/antigravity/brain/39f934dc-32e1-4b85-9ff5-cb976f9690d5/rep_performance_mockup_1782932260805.png)

---

### Page 4: HCP Targeting
*   **Purpose**: Provides sales reps with an actionable target list of underserved high-prescribing physicians (deciles 9 & 10).
*   **Visual Layout**:
    *   **Actionable Call List (Grid Table)**: HCP Name, Specialty, Prescribing Decile, Completed Calls Count, Territory Median Calls, Days Since Last Visit, Estimated Lost TRx, Potential Lost Revenue (USD), Suggested Calls Next Month.
    *   **Donut Chart**: Specialty Mix of Underserved HCPs (Primary Care vs. Cardiologists vs. Endocrinologists).
    *   **KPI Cards**: `High-Value Underserved HCPs` (Count), `Total Potential Lost Revenue` (USD).
    *   **Slicers**: `Region`, `Territory`, and `Specialty`.

![Page 4 Mockup](file:///C:/Users/Gauravi/.gemini/antigravity/brain/39f934dc-32e1-4b85-9ff5-cb976f9690d5/hcp_targeting_mockup_1782932276335.png)

---

## 7. Step 5: Interactivity, Navigation & Advanced BI Features

To create a premium user experience, implement the following advanced BI configurations:

### 1. Navigation Pane
1.  Build a vertical sidebar on the left side of all pages using standard buttons or bookmarks.
2.  Add navigation links: **Landing Page**, **Executive Summary**, **Territory Opportunity**, **Rep Performance**, and **HCP List**.
3.  Apply hover effects to buttons (change color to `#00A6A6` on hover) to create a responsive, premium app-like feel.

### 2. Drill-Through Path
Set up the following drill-through actions to allow users to investigate performance deficits:
*   **Region $\rightarrow$ Territory**: Right-clicking a Region bar on Page 1 allows the user to drill through to Page 2 (Territory Prioritization) filtered for that region's territories.
*   **Territory $\rightarrow$ Rep**: Right-clicking a Territory on Page 2 drills through to Page 3 (Rep Performance) for that specific territory.
*   **Rep $\rightarrow$ HCP List**: Right-clicking a Rep on Page 3 drills through to Page 4 (HCP Targeting) showing the underserved list specifically for that rep's territory.

### 3. Custom Tooltip Hover Page
Create a custom tooltip page (Page size: *Tooltip*) to display detailed metrics when hovering over the Territory bar charts:
1.  Name the page `tt_territory_details` and enable "Use as tooltip".
2.  Add cards showing: `Sales Variance %`, `Call Plan Adherence %`, and the assigned `Rep Name`.
3.  Add a small table listing the top 3 HCPs in that territory by total prescribing volume.

### 4. Conditional Formatting Rules
Apply color backgrounds to grid cells to immediately highlight performance outliers:
*   **Quota Attainment %**:
    *   $\ge 100\%$ : Light Green (`#D4EFDF` text `#196F3D` / Hex equivalent of Success)
    *   $80\% - 99.9\%$ : Light Yellow (`#FCF3CF` text `#B7950B` / Hex equivalent of Accent)
    *   $< 80\%$ : Light Red (`#FADBD8` text `#943126` / Hex equivalent of Danger)
*   **Call Adherence %**:
    *   $\ge 80\%$ : Light Green
    *   $70\% - 79.9\%$ : Light Yellow
    *   $< 70\%$ : Light Red
*   **Days Since Last Visit**:
    *   $\ge 60$ Days : Light Red (indicates a high-risk relationship lapse)
    *   $30 - 59$ Days : Light Yellow
    *   $< 30$ Days : Light Green
