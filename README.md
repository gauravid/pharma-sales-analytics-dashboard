# Sales Force Effectiveness (SFE) & Market Access Analytics

This project builds an end-to-end analytics pipeline designed to help a VP of Sales at a pharmaceutical company optimize field force execution, target high-potential Healthcare Providers (HCPs), and diagnose territory-level sales performance. 

Rather than relying on retrospective, manual spreadsheet reconciliations that take weeks to compile, this solution implements a repeatable data pipeline using **SQL** and **Python** to calculate core pharma commercial KPIs, visualize them in a self-service **Power BI** dashboard, and apply a predictive **Linear Regression** model to forecast sales and identify reps at risk of missing their quotas.

---

## Project Repository Structure

```
c:\Users\Gauravi\Desktop\ba_pro\
├── data/
│   ├── sfe_analytics.db         # SQLite database file containing all cleaned tables
│   ├── territories.csv          # Territory Master raw extract
│   ├── reps.csv                 # Sales Representative Master raw extract
│   ├── hcps.csv                 # Healthcare Provider Master raw extract
│   ├── calls.csv                # CRM Call Activity Log raw extract
│   ├── prescriptions.csv        # Claims / Prescription Data raw extract
│   └── sales_targets.csv        # Territory Monthly Sales & Target Quotas
├── docs/
│   ├── stakeholder_requirements.md  # Simulated interviews, MoSCoW log, and KPI formulas
│   ├── data_dictionary.md       # Full table schemas, column types, and Mermaid ER diagram
│   └── process_mapping.md       # As-Is/To-Be process flows and Root-Cause Issue Tree
├── scripts/
│   └── generate_data.py         # Python script using Faker to generate synthetic data
├── venv/                        # Python virtual environment (ignored by git)
├── requirements.txt             # Python project dependencies
└── README.md                    # Main project documentation
```

---

## Technology Stack

*   **Data Generation**: Python (Pandas, NumPy, Faker)
*   **Database Layer**: SQLite (file-based database)
*   **Analytics Layer**: SQL (SQLite syntax)
*   **Visualization Layer**: Power BI Desktop
*   **Predictive Layer**: Python (Scikit-Learn, Statsmodels)
*   **Process Modeling**: Mermaid / Markdown

---

## Phase 1: Foundation, Stakeholders & Dataset

In this first phase, we established the business requirements and generated a realistic, messy dataset containing intentional commercial anomalies.

### Key Activities Completed
1.  **Stakeholder Requirement Gathering**: Compiled interviews with the VP of Sales, Brand Manager, Field Ops, and a Regional Manager to define the project scope.
2.  **MoSCoW Prioritization**: Organized 12 core requirements into Must, Should, and Could categories.
3.  **KPI Definitions**: Formulated math equations for **Call Plan Adherence %**, **Share of Voice (SOV) %**, **Territory Potential Index**, and **Territory Opportunity Gap**.
4.  **Data Modeling**: Designed a relational schema of 6 tables and documented it in a Data Dictionary with an ER diagram.
5.  **Process Mapping**: Mapped the manual As-Is process vs. the automated To-Be pipeline, and drew a Root-Cause Issue Tree for diagnosing underperforming territories.
6.  **Data Generation**: Created a Python script using `Faker` and `pandas` to generate 12 months of CRM and claims data with built-in anomalies.

### Seeded Data Anomalies (For Realistic Analysis)
To simulate a real-world pharmaceutical sales environment, the generated dataset contains the following deliberate issues:
*   **Region X Underperformance**: Reps in Region X are seeded with lower Call Plan Adherence (~65% completed calls vs. ~85% in other regions) and a local market access penalty (reducing market share by 8% due to formulary restrictions).
*   **High Rep Turnover**: 4 out of 8 territories in Region X have reps hired within the last 3 months, representing vacancies and training lags.
*   **Duplicate HCP Records**: Approximately 1% of HCP records contain duplicate profiles (e.g., spelling differences like `Dr. Name` vs `Name MD`) to test data cleaning.
*   **Missing CRM Log Data**: Approximately 5% of records in the `calls` table have missing dates, statuses, or HCP IDs, representing late entries and sync glitches.

---

## How to Set Up and Run

### Prerequisites
*   Python 3.8 or higher installed on your system.

### 1. Set Up Virtual Environment & Install Dependencies
Run the following commands in your terminal from the project root:

```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment (Windows)
.\venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Generate the Dataset
Execute the data generator script to create the raw CSV files and the SQLite database:

```powershell
python scripts/generate_data.py
```

### Expected Output of Data Generation
Upon successful execution, the script will output verification metrics showing the row counts for each table and regional statistics:
*   **Call Adherence Check**: Confirming `Region_X` has ~65% adherence while others have 80-92%.
*   **Sales Attainment Check**: Confirming `Region_X` has lower sales attainment (~70-80%) compared to others (95-105%).
*   **Database Verification**: Confirming the creation of `data/sfe_analytics.db` with all tables populated.
