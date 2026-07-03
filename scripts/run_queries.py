import os
import sqlite3
import logging
import pandas as pd
from datetime import datetime

# 1. Create directories
os.makedirs("data/exports", exist_ok=True)
os.makedirs("data/logs", exist_ok=True)

# 2. Configure logging
log_filename = f"data/logs/query_execution.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("Starting SFE SQL query execution pipeline...")

# 3. Define the database path and execution order
db_path = "data/sfe_analytics.db"
sql_files_order = [
    "sql/base_views.sql",
    "sql/indexes.sql",
    "sql/exploratory_queries.sql",
    "sql/call_adherence.sql",
    "sql/prescription_trends.sql",
    "sql/market_share_potential.sql",
    "sql/hcp_targeting.sql",
    "sql/root_cause_validation.sql",
    "sql/ranking_queries.sql",
    "sql/validation.sql",
    "sql/metrics_summary.sql"
]

# 4. Define views to export to CSV
exports_map = {
    "vw_call_adherence": "data/exports/call_adherence.csv",
    "vw_territory_opportunity": "data/exports/territory_opportunity.csv",
    "vw_hcp_targeting": "data/exports/underserved_hcps.csv",
    "vw_prescription_trends": "data/exports/prescription_trends.csv",
    "vw_market_share": "data/exports/market_share.csv",
    "vw_root_cause": "data/exports/root_cause_summary.csv",
    "vw_metrics_summary": "data/exports/dashboard_summary.csv"
}

def execute_sql_file(conn, file_path):
    """Parses and executes a SQL file, printing SELECT results in a formatted table."""
    logging.info(f"Executing script: {file_path}")
    if not os.path.exists(file_path):
        logging.error(f"SQL file not found: {file_path}")
        return False
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
            
        # Split by semicolon to execute individual statements, ignoring comments
        statements = sql_content.split(";")
        cursor = conn.cursor()
        
        for statement in statements:
            clean_statement = statement.strip()
            if not clean_statement:
                continue
                
            # Execute statement
            cursor.execute(clean_statement)
            
            # If it's a SELECT statement, display the results in the log/console
            if clean_statement.upper().startswith("SELECT"):
                # Fetch column names
                cols = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                if rows:
                    df = pd.DataFrame(rows, columns=cols)
                    # Generate a clean text table representation
                    table_str = df.to_string(index=False)
                    logging.info(f"\nQuery Results:\n{table_str}\n" + "-"*50)
                else:
                    logging.info(f"Query returned 0 rows.\n" + "-"*50)
                    
        conn.commit()
        logging.info(f"Successfully completed: {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error executing {file_path}: {str(e)}")
        return False

def main():
    if not os.path.exists(db_path):
        logging.error(f"Database not found at {db_path}. Please run generate_data.py first.")
        return
        
    conn = sqlite3.connect(db_path)
    
    # Execute all SQL files in order
    for sql_file in sql_files_order:
        execute_sql_file(conn, sql_file)
        
    # Export views to CSV
    logging.info("Starting CSV exports for Power BI dashboard...")
    for view_name, export_path in exports_map.items():
        try:
            query = f"SELECT * FROM {view_name};"
            df = pd.read_sql_query(query, conn)
            df.to_csv(export_path, index=False)
            logging.info(f"Exported {view_name} -> {export_path} ({len(df)} rows)")
        except Exception as e:
            logging.error(f"Failed to export {view_name}: {str(e)}")
            
    conn.close()
    logging.info("SFE SQL query pipeline execution complete.")

if __name__ == "__main__":
    main()
