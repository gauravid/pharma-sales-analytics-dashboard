import os
import sqlite3
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)
fake = Faker()
Faker.seed(42)

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

print("Starting synthetic data generation...")

# ---------------------------------------------------------
# 1. GENERATE TERRITORIES
# ---------------------------------------------------------
regions = ["East", "West", "Midwest", "South", "Region_X"]
territories_per_region = 8
territories_data = []

# Map regions to geographical areas for realistic names
region_cities = {
    "East": ["Boston", "New York", "Philadelphia", "Washington", "Atlanta", "Miami", "Boston_North", "NY_West"],
    "West": ["Seattle", "Portland", "San Francisco", "Los Angeles", "San Diego", "Phoenix", "Denver", "Salt Lake"],
    "Midwest": ["Chicago", "Detroit", "Minneapolis", "St Louis", "Cleveland", "Indianapolis", "Cincinnati", "Kansas City"],
    "South": ["Dallas", "Houston", "Austin", "New Orleans", "Nashville", "Charlotte", "Tampa", "Birmingham"],
    "Region_X": ["Chicago_South", "Milwaukee", "Indianapolis_West", "Detroit_East", "Cleveland_South", "Grand Rapids", "Madison", "Peoria"]
}

territory_id_counter = 1
for region in regions:
    cities = region_cities[region]
    for i in range(territories_per_region):
        t_id = f"T{territory_id_counter:02d}"
        t_name = f"{cities[i]} Territory"
        
        # Monthly call plan target (60 to 80 calls)
        call_target = random.randint(60, 80)
        
        # Market potential inputs for Territory Potential Index (TPI)
        category_volume_factor = round(random.uniform(0.3, 1.0), 2)
        target_hcp_count_factor = round(random.uniform(0.4, 1.0), 2)
        patient_volume_proxy = round(random.uniform(0.2, 1.0), 2)
        
        # Estimated total category calls (market calls) per month
        # Competitors are also active, so market calls are much higher than a single rep's capacity
        est_market_calls_monthly = random.randint(250, 350)
        
        territories_data.append({
            "territory_id": t_id,
            "territory_name": t_name,
            "region": region,
            "monthly_call_target": call_target,
            "category_volume_factor": category_volume_factor,
            "target_hcp_count_factor": target_hcp_count_factor,
            "patient_volume_proxy": patient_volume_proxy,
            "est_market_calls_monthly": est_market_calls_monthly
        })
        territory_id_counter += 1

df_territories = pd.DataFrame(territories_data)

# ---------------------------------------------------------
# 2. GENERATE REPS (with high turnover in Region X)
# ---------------------------------------------------------
reps_data = []
rep_id_counter = 1

for idx, row in df_territories.iterrows():
    r_id = f"R{rep_id_counter:02d}"
    name = fake.name()
    t_id = row["territory_id"]
    region = row["region"]
    
    # In Region X, we simulate high turnover (short tenure)
    # 4 out of 8 reps in Region X will have tenure < 4 months
    if region == "Region_X" and rep_id_counter % 2 == 0:
        # Hired recently (between 10 and 90 days before the start of our 12-month window)
        # Our window is Jan 2025 to Dec 2025. Start is 2025-01-01.
        days_before = random.randint(10, 90)
        hire_date = datetime(2025, 1, 1) - timedelta(days=days_before)
    else:
        # Standard tenure (1 to 6 years before 2025-01-01)
        days_before = random.randint(365, 365 * 6)
        hire_date = datetime(2025, 1, 1) - timedelta(days=days_before)
        
    reps_data.append({
        "rep_id": r_id,
        "rep_name": name,
        "territory_id": t_id,
        "hire_date": hire_date.strftime("%Y-%m-%d"),
        "status": "Active"
    })
    rep_id_counter += 1

df_reps = pd.DataFrame(reps_data)

# ---------------------------------------------------------
# 3. GENERATE HCPS (with some duplicate CRM entries)
# ---------------------------------------------------------
hcps_data = []
hcp_id_counter = 1
specialties = ["Cardiology", "Endocrinology", "Primary Care"]
specialty_weights = [0.25, 0.25, 0.50]

# Generate ~600 HCPs (~15 per territory)
for idx, row in df_territories.iterrows():
    t_id = row["territory_id"]
    num_hcps = random.randint(13, 17)
    
    for _ in range(num_hcps):
        h_id = f"H{hcp_id_counter:03d}"
        # Doctor name
        h_name = f"Dr. {fake.last_name()}"
        spec = random.choices(specialties, weights=specialty_weights)[0]
        
        # Prescribing decile (1 to 10)
        # High decile (8-10) are the high-value prescribers
        decile = random.choices(
            list(range(1, 11)), 
            weights=[0.05, 0.07, 0.08, 0.10, 0.12, 0.15, 0.15, 0.13, 0.10, 0.05]
        )[0]
        
        hcps_data.append({
            "hcp_id": h_id,
            "hcp_name": h_name,
            "specialty": spec,
            "territory_id": t_id,
            "prescribing_decile": decile
        })
        hcp_id_counter += 1

# Inject ~5 duplicate HCP records (CRM spelling/entry errors)
duplicates = []
hcp_ids_to_dup = random.sample(range(1, hcp_id_counter), 5)
for dup_id in hcp_ids_to_dup:
    original = next(h for h in hcps_data if h["hcp_id"] == f"H{dup_id:03d}")
    # Create duplicate with slightly different name spelling
    dup_name = original["hcp_name"] + " MD" if random.choice([True, False]) else original["hcp_name"].replace("Dr. ", "Dr.  ")
    # New ID to represent a duplicate record in CRM
    new_id = f"H{hcp_id_counter:03d}"
    duplicates.append({
        "hcp_id": new_id,
        "hcp_name": dup_name,
        "specialty": original["specialty"],
        "territory_id": original["territory_id"],
        "prescribing_decile": original["prescribing_decile"]
    })
    hcp_id_counter += 1

hcps_data.extend(duplicates)
df_hcps = pd.DataFrame(hcps_data)

# ---------------------------------------------------------
# 4. GENERATE CALL LOGS (12 Months, Jan 2025 - Dec 2025)
# ---------------------------------------------------------
# We will generate call logs. 
# Adherence in normal regions: 80-90%
# Adherence in Region X: 60-70%
# We also inject ~5% missing/corrupted records in the call logs.

months = [datetime(2025, m, 1) for m in range(1, 13)]
calls_data = []
call_id_counter = 1

for month in months:
    month_str = month.strftime("%Y-%m")
    days_in_month = (datetime(month.year, month.month + 1, 1) - timedelta(days=1)).day if month.month < 12 else 31
    
    for idx, rep in df_reps.iterrows():
        r_id = rep["rep_id"]
        t_id = rep["territory_id"]
        region = df_territories.loc[df_territories["territory_id"] == t_id, "region"].values[0]
        call_target = df_territories.loc[df_territories["territory_id"] == t_id, "monthly_call_target"].values[0]
        
        # Get HCPs in this territory
        t_hcps = df_hcps[df_hcps["territory_id"] == t_id]["hcp_id"].tolist()
        if not t_hcps:
            continue
            
        # Determine completed calls based on region adherence
        if region == "Region_X":
            # Underperforming region: 60% to 70% adherence
            adherence_rate = random.uniform(0.60, 0.70)
        else:
            # Normal regions: 80% to 92% adherence
            adherence_rate = random.uniform(0.80, 0.92)
            
        completed_calls_count = int(call_target * adherence_rate)
        
        # Generate planned calls
        # We plan exactly the target calls
        planned_hcps = random.choices(t_hcps, k=call_target)
        
        # Select which planned calls were actually completed
        completed_indices = set(random.sample(range(call_target), completed_calls_count))
        
        for i in range(call_target):
            h_id = planned_hcps[i]
            is_completed = i in completed_indices
            
            # Call date (distributed across the month)
            call_day = random.randint(1, days_in_month)
            call_date = datetime(2025, month.month, call_day)
            
            # Status
            if is_completed:
                status = "Completed"
            else:
                status = random.choice(["No Show", "Cancelled"])
                
            call_type = random.choices(["In-Person", "Virtual", "Phone"], weights=[0.70, 0.20, 0.10])[0]
            
            # Brand promoted: Apexacare (our brand), Competitor A, Competitor B, or None
            # If the call is completed, we promoted our brand 80% of the time, others 20%
            if status == "Completed":
                brand_promoted = random.choices(["Apexacare", "None"], weights=[0.85, 0.15])[0]
            else:
                brand_promoted = "None"
                
            calls_data.append({
                "call_id": f"C{call_id_counter:06d}",
                "rep_id": r_id,
                "hcp_id": h_id,
                "call_date": call_date.strftime("%Y-%m-%d"),
                "planned_vs_actual": "Planned",
                "call_status": status,
                "call_type": call_type,
                "brand_promoted": brand_promoted,
                "month_id": month_str
            })
            call_id_counter += 1
            
        # Add a few "Unplanned" calls (reps drop-in)
        num_unplanned = random.randint(2, 5)
        unplanned_hcps = random.choices(t_hcps, k=num_unplanned)
        for h_id in unplanned_hcps:
            call_day = random.randint(1, days_in_month)
            call_date = datetime(2025, month.month, call_day)
            calls_data.append({
                "call_id": f"C{call_id_counter:06d}",
                "rep_id": r_id,
                "hcp_id": h_id,
                "call_date": call_date.strftime("%Y-%m-%d"),
                "planned_vs_actual": "Unplanned",
                "call_status": "Completed",
                "call_type": "In-Person",
                "brand_promoted": "Apexacare",
                "month_id": month_str
            })
            call_id_counter += 1

df_calls = pd.DataFrame(calls_data)

# Inject ~5% missing/corrupted data in the call logs
# We will set call_date, hcp_id, or call_status to None for 5% of records
mask_missing = np.random.rand(len(df_calls)) < 0.05
df_calls.loc[mask_missing, "call_status"] = None
# For 1% of records, set hcp_id to None
mask_missing_hcp = np.random.rand(len(df_calls)) < 0.01
df_calls.loc[mask_missing_hcp, "hcp_id"] = None

# ---------------------------------------------------------
# 5. GENERATE PRESCRIPTION DATA (12 Months, Jan 2025 - Dec 2025)
# ---------------------------------------------------------
# Prescriptions are generated monthly per HCP.
# Total market prescriptions (Apexacare + Competitor A + Competitor B) are based on HCP decile.
# Apexacare share is driven by:
#  - Base share (25%)
#  - Call frequency in that month (more completed calls = higher share)
#  - Specialty (Cardiology has higher base share for Apexacare, Endocrinology is medium, Primary Care is lower)
#  - Region X will naturally have lower Apexacare share due to lower call adherence.

prescriptions_data = []

for month in months:
    month_str = month.strftime("%Y-%m")
    
    # Calculate completed calls per HCP in this month to drive prescription volume
    # Filter completed calls with valid HCP IDs
    completed_calls_this_month = df_calls[
        (df_calls["month_id"] == month_str) & 
        (df_calls["call_status"] == "Completed") & 
        (df_calls["brand_promoted"] == "Apexacare") &
        (df_calls["hcp_id"].notna())
    ]
    hcp_call_counts = completed_calls_this_month.groupby("hcp_id").size().to_dict()
    
    for idx, hcp in df_hcps.iterrows():
        h_id = hcp["hcp_id"]
        decile = hcp["prescribing_decile"]
        spec = hcp["specialty"]
        t_id = hcp["territory_id"]
        region = df_territories.loc[df_territories["territory_id"] == t_id, "region"].values[0]
        
        # Base market volume (TRx) per month based on decile
        # Decile 10: 150-200 TRx, Decile 1: 5-10 TRx
        market_trx = int(decile * random.randint(15, 22))
        if market_trx == 0:
            market_trx = 5
            
        # NRx is typically 20-30% of TRx
        market_nrx = int(market_trx * random.uniform(0.20, 0.30))
        if market_nrx == 0:
            market_nrx = 1
            
        # Determine Apexacare share based on calls and specialty
        calls_received = hcp_call_counts.get(h_id, 0)
        
        # Specialty base share
        if spec == "Cardiology":
            base_share = 0.35
        elif spec == "Endocrinology":
            base_share = 0.25
        else:
            base_share = 0.18
            
        # Call impact: each completed call increases share by 5% (up to a max of 20% additional share)
        call_impact = min(calls_received * 0.05, 0.20)
        
        # Region X has a market access penalty (formulary restriction reduces share by 8% absolute)
        access_penalty = 0.08 if region == "Region_X" else 0.0
        
        apex_share = max(0.05, base_share + call_impact - access_penalty)
        # Add small monthly fluctuation/noise
        apex_share += random.uniform(-0.03, 0.03)
        apex_share = min(max(apex_share, 0.05), 0.70) # Bound between 5% and 70%
        
        # Competitor shares
        comp_a_share = (1 - apex_share) * random.uniform(0.50, 0.60)
        comp_b_share = 1 - apex_share - comp_a_share
        
        # Calculate NRx and TRx for each brand
        apex_trx = int(market_trx * apex_share)
        comp_a_trx = int(market_trx * comp_a_share)
        comp_b_trx = market_trx - apex_trx - comp_a_trx
        
        apex_nrx = int(market_nrx * apex_share)
        comp_a_nrx = int(market_nrx * comp_a_share)
        comp_b_nrx = market_nrx - apex_nrx - comp_a_nrx
        
        # Ensure non-negative
        apex_trx = max(0, apex_trx)
        comp_a_trx = max(0, comp_a_trx)
        comp_b_trx = max(0, comp_b_trx)
        apex_nrx = max(0, apex_nrx)
        comp_a_nrx = max(0, comp_a_nrx)
        comp_b_nrx = max(0, comp_b_nrx)
        
        # Append records for our brand and competitors
        prescriptions_data.append({
            "hcp_id": h_id,
            "month_id": month_str,
            "brand": "Apexacare",
            "nrx": apex_nrx,
            "trx": apex_trx
        })
        prescriptions_data.append({
            "hcp_id": h_id,
            "month_id": month_str,
            "brand": "Competitor_A",
            "nrx": comp_a_nrx,
            "trx": comp_a_trx
        })
        prescriptions_data.append({
            "hcp_id": h_id,
            "month_id": month_str,
            "brand": "Competitor_B",
            "nrx": comp_b_nrx,
            "trx": comp_b_trx
        })

df_prescriptions = pd.DataFrame(prescriptions_data)

# ---------------------------------------------------------
# 6. GENERATE SALES & TARGET DATA (12 Months, Jan 2025 - Dec 2025)
# ---------------------------------------------------------
# Sales are recorded at the territory level.
# Actual sales are calculated based on territory TRx * $150 (price per TRx) + institutional sales (15% base + noise).
# Target sales are set based on the territory's Potential Index (TPI) with a growth factor.
# For Region X, targets are set aggressively high, and because of low adherence and market access penalty, 
# actual sales will lag significantly behind targets.

sales_targets_data = []

for month in months:
    month_str = month.strftime("%Y-%m")
    
    # Calculate TRx by territory for this month
    # First map HCP to territory
    hcp_territory_map = df_hcps.set_index("hcp_id")["territory_id"].to_dict()
    df_apex_rx = df_prescriptions[(df_prescriptions["brand"] == "Apexacare") & (df_prescriptions["month_id"] == month_str)].copy()
    df_apex_rx["territory_id"] = df_apex_rx["hcp_id"].map(hcp_territory_map)
    territory_trx = df_apex_rx.groupby("territory_id")["trx"].sum().to_dict()
    
    for idx, territory in df_territories.iterrows():
        t_id = territory["territory_id"]
        region = territory["region"]
        
        # Get Rx-based sales (TRx * $150)
        t_rx_volume = territory_trx.get(t_id, 0)
        rx_sales = t_rx_volume * 150
        
        # Add institutional sales (hospitals, clinics) which are ~15-20% of retail sales
        inst_sales = rx_sales * random.uniform(0.15, 0.25)
        actual_sales = round(rx_sales + inst_sales, 2)
        
        # Calculate baseline potential for targets
        # Target = potential volume * price * growth factor
        # Potential volume is driven by category volume factor
        tpi_score = (territory["category_volume_factor"] * 50 + 
                     territory["target_hcp_count_factor"] * 30 + 
                     territory["patient_volume_proxy"] * 20)
                     
        # Expected sales based on TPI
        expected_monthly_sales = tpi_score * 800
        
        # Set target. 
        # Region X has targets set very high (e.g. 110% of potential) to simulate aggressive quotas
        if region == "Region_X":
            target_sales = round(expected_monthly_sales * 1.15, 2)
        else:
            target_sales = round(expected_monthly_sales * random.uniform(0.95, 1.05), 2)
            
        # Ensure targets are reasonably aligned with actuals for normal regions,
        # but Region X will have a massive gap
        if region == "Region_X":
            # Actual sales are lower due to low adherence and access penalty
            # Attainment should be around 70-80%
            pass
        else:
            # Attainment around 95-105%
            # If actual sales are too far from target, adjust target slightly to maintain realism
            if actual_sales / target_sales < 0.85:
                target_sales = round(actual_sales * random.uniform(0.95, 1.05), 2)
                
        sales_targets_data.append({
            "territory_id": t_id,
            "month_id": month_str,
            "actual_sales": actual_sales,
            "target_sales": target_sales
        })

df_sales_targets = pd.DataFrame(sales_targets_data)

# ---------------------------------------------------------
# 7. SAVE TO CSV AND SQLITE
# ---------------------------------------------------------
# Save CSVs
df_territories.to_csv("data/territories.csv", index=False)
df_reps.to_csv("data/reps.csv", index=False)
df_hcps.to_csv("data/hcps.csv", index=False)
df_calls.to_csv("data/calls.csv", index=False)
df_prescriptions.to_csv("data/prescriptions.csv", index=False)
df_sales_targets.to_csv("data/sales_targets.csv", index=False)

print("CSVs successfully written to data/ folder.")

# Connect to SQLite
db_path = "data/sfe_analytics.db"
if os.path.exists(db_path):
    os.remove(db_path) # Start fresh

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables with primary keys and relationships
cursor.execute("""
CREATE TABLE territories (
    territory_id TEXT PRIMARY KEY,
    territory_name TEXT NOT NULL,
    region TEXT NOT NULL,
    monthly_call_target INTEGER NOT NULL,
    category_volume_factor REAL NOT NULL,
    target_hcp_count_factor REAL NOT NULL,
    patient_volume_proxy REAL NOT NULL,
    est_market_calls_monthly INTEGER NOT NULL
);
""")

cursor.execute("""
CREATE TABLE reps (
    rep_id TEXT PRIMARY KEY,
    rep_name TEXT NOT NULL,
    territory_id TEXT NOT NULL,
    hire_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (territory_id) REFERENCES territories(territory_id)
);
""")

cursor.execute("""
CREATE TABLE hcps (
    hcp_id TEXT PRIMARY KEY,
    hcp_name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    territory_id TEXT NOT NULL,
    prescribing_decile INTEGER NOT NULL,
    FOREIGN KEY (territory_id) REFERENCES territories(territory_id)
);
""")

cursor.execute("""
CREATE TABLE calls (
    call_id TEXT PRIMARY KEY,
    rep_id TEXT NOT NULL,
    hcp_id TEXT,
    call_date TEXT,
    planned_vs_actual TEXT NOT NULL,
    call_status TEXT,
    call_type TEXT,
    brand_promoted TEXT,
    month_id TEXT NOT NULL,
    FOREIGN KEY (rep_id) REFERENCES reps(rep_id),
    FOREIGN KEY (hcp_id) REFERENCES hcps(hcp_id)
);
""")

cursor.execute("""
CREATE TABLE prescriptions (
    hcp_id TEXT NOT NULL,
    month_id TEXT NOT NULL,
    brand TEXT NOT NULL,
    nrx INTEGER NOT NULL,
    trx INTEGER NOT NULL,
    PRIMARY KEY (hcp_id, month_id, brand),
    FOREIGN KEY (hcp_id) REFERENCES hcps(hcp_id)
);
""")

cursor.execute("""
CREATE TABLE sales_targets (
    territory_id TEXT NOT NULL,
    month_id TEXT NOT NULL,
    actual_sales REAL NOT NULL,
    target_sales REAL NOT NULL,
    PRIMARY KEY (territory_id, month_id),
    FOREIGN KEY (territory_id) REFERENCES territories(territory_id)
);
""")

conn.commit()

# Load DataFrames into SQLite tables
df_territories.to_sql("territories", conn, if_exists="append", index=False)
df_reps.to_sql("reps", conn, if_exists="append", index=False)
df_hcps.to_sql("hcps", conn, if_exists="append", index=False)
df_calls.to_sql("calls", conn, if_exists="append", index=False)
df_prescriptions.to_sql("prescriptions", conn, if_exists="append", index=False)
df_sales_targets.to_sql("sales_targets", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print("SQLite database successfully created and populated at data/sfe_analytics.db.")

# ---------------------------------------------------------
# 8. VERIFY AND PRINT STATISTICS
# ---------------------------------------------------------
print("\n--- DATA GENERATION VERIFICATION ---")
print(f"Territories Count : {len(df_territories)}")
print(f"Reps Count        : {len(df_reps)}")
print(f"HCPs Count        : {len(df_hcps)} (including duplicates)")
print(f"Calls Count       : {len(df_calls)} (including missing/cancelled)")
print(f"Prescriptions Rows: {len(df_prescriptions)}")
print(f"Sales Rows        : {len(df_sales_targets)}")

# Check Region X Adherence vs Others
print("\n--- ADHERENCE CHECK ---")
# Completed calls where planned_vs_actual is 'Planned' and status is 'Completed'
df_planned_calls = df_calls[(df_calls["planned_vs_actual"] == "Planned") & (df_calls["call_status"] == "Completed")].copy()
df_planned_calls["region"] = df_planned_calls["rep_id"].map(df_reps.set_index("rep_id")["territory_id"]).map(df_territories.set_index("territory_id")["region"])

# Total planned calls (both completed and cancelled/no show)
df_total_planned = df_calls[df_calls["planned_vs_actual"] == "Planned"].copy()
df_total_planned["region"] = df_total_planned["rep_id"].map(df_reps.set_index("rep_id")["territory_id"]).map(df_territories.set_index("territory_id")["region"])

completed_by_region = df_planned_calls.groupby("region").size()
total_by_region = df_total_planned.groupby("region").size()
adherence_by_region = (completed_by_region / total_by_region) * 100

for reg, adh in adherence_by_region.items():
    print(f"Region: {reg:<12} | Call Adherence: {adh:.2f}%")

# Check Sales Attainment by Region
print("\n--- SALES ATTAINMENT CHECK ---")
df_sales_with_region = df_sales_targets.copy()
df_sales_with_region["region"] = df_sales_with_region["territory_id"].map(df_territories.set_index("territory_id")["region"])
sales_by_region = df_sales_with_region.groupby("region")[["actual_sales", "target_sales"]].sum()
sales_by_region["attainment_pct"] = (sales_by_region["actual_sales"] / sales_by_region["target_sales"]) * 100

for reg, row in sales_by_region.iterrows():
    print(f"Region: {reg:<12} | Sales Attainment: {row['attainment_pct']:.2f}% | Actual: ${row['actual_sales']:,.2f} | Target: ${row['target_sales']:,.2f}")

print("\nData generation is complete. Ready for SQL analysis.")
