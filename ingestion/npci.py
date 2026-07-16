import pandas as pd
import duckdb
import os
from datetime import datetime

# All 11 NPCI CSV files with clean table names
NPCI_FILES = {
    "UPI Monthly Product Statistics Trended.csv": "raw_npci_upi",
    "IMPS Monthly Product Statistics Trended.csv": "raw_npci_imps",
    "AePS - Cash Withdrawal Monthly Product Statistics Trended.csv": "raw_npci_aeps_cash",
    "AePS - Funds Transfer Monthly Product Statistics Trended.csv": "raw_npci_aeps_transfer",
    "AePS - BHIM Aadhaar Pay Monthly Product Statistics Trended.csv": "raw_npci_aeps_bhim",
    "CTS Monthly Product Statistics Trended.csv": "raw_npci_cts",
    "NACH - APBS Monthly Product Statistics Trended.csv": "raw_npci_nach_apbs",
    "NACH - Credit Monthly Product Statistics Trended.csv": "raw_npci_nach_credit",
    "NACH - Debit Monthly Product Statistics Trended.csv": "raw_npci_nach_debit",
    "NETC Monthly Product Statistics Trended.csv": "raw_npci_netc",
    "NFS Monthly Product Statistics Trended.csv": "raw_npci_nfs",
}

RAW_DATA_PATH = "data/raw"
DB_PATH = "data/raw/india_dev.duckdb"

def clean_number(val):
    """Remove commas from numbers like 12,203.02 and convert to float"""
    if pd.isna(val):
        return None
    return float(str(val).replace(",", "").strip())

def parse_month(val):
    """Convert 24-Jan to 2024-01-01 format"""
    try:
        return pd.to_datetime(val, format="%y-%b").strftime("%Y-%m-01")
    except:
        return None

def ingest_file(filename, table_name, con):
    """Read one NPCI CSV and load into DuckDB"""
    filepath = os.path.join(RAW_DATA_PATH, filename)

    if not os.path.exists(filepath):
        print(f"File not found: {filename}")
        return 0

    print(f"Processing {filename}...")
    df = pd.read_csv(filepath)

    # Standardise column names
    df.columns = [col.strip() for col in df.columns]

    # Parse month
    df["month_date"] = df["Month"].apply(parse_month)

    # Clean volume columns — remove commas
    df["volume_mn"] = df["Volume (in Mn.)"].apply(clean_number)
    df["avg_daily_volume_mn"] = df["Avg. Daily Volume (in Mn.)"].apply(clean_number)

    # Add metadata
    df["product"] = filename.replace(" Monthly Product Statistics Trended.csv", "").strip()
    df["source"] = "NPCI official statistics via Kaggle"
    df["ingested_at"] = datetime.now().isoformat()

    # Keep only clean columns
    df = df[["month_date", "volume_mn", "avg_daily_volume_mn", "product", "source", "ingested_at"]]

    # Drop rows where month couldn't be parsed
    df = df.dropna(subset=["month_date"])

    # Save to DuckDB
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.execute(f"""
        CREATE TABLE {table_name} AS 
        SELECT * FROM df
    """)

    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  Saved {count} rows to {table_name}")
    return count

def run():
    print("Starting NPCI ingestion...\n")
    con = duckdb.connect(DB_PATH)

    total = 0
    for filename, table_name in NPCI_FILES.items():
        total += ingest_file(filename, table_name, con)

    print(f"\nAll NPCI files ingested. Total rows across all tables: {total}")

    # Quick summary
    print("\nSummary:")
    for _, table_name in NPCI_FILES.items():
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            latest = con.execute(f"SELECT MAX(month_date) FROM {table_name}").fetchone()[0]
            print(f"  {table_name}: {count} rows, latest: {latest}")
        except:
            pass

    con.close()
    print("\nNPCI ingestion complete.")

if __name__ == "__main__":
    run()
