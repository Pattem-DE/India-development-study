import pandas as pd
import duckdb
import os
from datetime import datetime

RAW_DATA_PATH = "data/raw"
DB_PATH = "data/raw/india_dev.duckdb"

def parse_month(val):
    """Convert Aug-25 to 2025-08-01"""
    try:
        return pd.to_datetime(val, format="%b-%y").strftime("%Y-%m-01")
    except:
        return None

def run():
    filepath = os.path.join(RAW_DATA_PATH, "upi_data_enhanced.csv")
    print("Reading UPI historical data...")

    df = pd.read_csv(filepath)
    print(f"Raw rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # Clean column names
    df.columns = [col.strip() for col in df.columns]

    # Parse month
    df["month_date"] = df["Month"].apply(parse_month)

    # Rename columns to snake_case
    df = df.rename(columns={
        "No. of Banks live on UPI": "banks_live_on_upi",
        "Volume (in Mn)": "volume_mn",
        "Value (in Cr.)": "value_cr",
        "Avg_Txn_Value_INR": "avg_txn_value_inr",
        "MoM_Growth_Volume_%": "mom_growth_volume_pct",
        "MoM_Growth_Value_%": "mom_growth_value_pct",
    })

    # Keep clean columns only
    df = df[[
        "month_date", "banks_live_on_upi", "volume_mn",
        "value_cr", "avg_txn_value_inr",
        "mom_growth_volume_pct", "mom_growth_value_pct"
    ]]

    # Drop unparseable rows
    df = df.dropna(subset=["month_date"])

    # Sort by date ascending
    df = df.sort_values("month_date").reset_index(drop=True)

    # Add metadata
    df["source"] = "Kaggle: syedahmadrayyan/upi-transaction-monthly-data-india-20162025"
    df["ingested_at"] = datetime.now().isoformat()

    print(f"\nDate range: {df['month_date'].min()} to {df['month_date'].max()}")
    print(f"Total rows: {len(df)}")
    print(f"\nSample:")
    print(df.head(3))
    print(df.tail(3))

    # Save to DuckDB
    con = duckdb.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS raw_upi_historical")
    con.execute("""
        CREATE TABLE raw_upi_historical AS
        SELECT * FROM df
    """)

    count = con.execute("SELECT COUNT(*) FROM raw_upi_historical").fetchone()[0]
    print(f"\nSaved {count} rows to raw_upi_historical")
    con.close()
    print("UPI historical ingestion complete.")

if __name__ == "__main__":
    run()
