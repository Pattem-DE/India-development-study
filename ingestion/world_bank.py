import requests
import pandas as pd
import duckdb
import os
from datetime import datetime

# World Bank API - free, no key needed
BASE_URL = "http://api.worldbank.org/v2"

# Indicators we want to track
INDICATORS = {
    "NY.GDP.MKTP.CD": "gdp_usd",
    "SI.POV.DDAY": "poverty_rate",
    "IT.NET.USER.ZS": "internet_users_pct",
    "IT.CEL.SETS.P2": "mobile_subscriptions_per100",
    "EG.ELC.ACCS.ZS": "electricity_access_pct",
    "SE.PRM.ENRR": "primary_school_enrollment",
    "SP.POP.TOTL": "population"
}

def fetch_indicator(indicator_code, indicator_name, country="IN", start=2000, end=2024):
    """Fetch a single indicator from World Bank API"""
    url = f"{BASE_URL}/country/{country}/indicator/{indicator_code}"
    params = {
        "format": "json",
        "per_page": 100,
        "mrv": end - start + 1,
        "date": f"{start}:{end}"
    }
    
    print(f"Fetching {indicator_name}...")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"Failed to fetch {indicator_name}: {response.status_code}")
        return None
    
    data = response.json()
    
    # World Bank returns [metadata, data]
    if len(data) < 2 or not data[1]:
        print(f"No data for {indicator_name}")
        return None
    
    records = []
    for entry in data[1]:
        if entry["value"] is not None:
            records.append({
                "year": int(entry["date"]),
                "country_code": entry["countryiso3code"],
                "country_name": entry["country"]["value"],
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "value": float(entry["value"]),
                "ingested_at": datetime.now().isoformat()
            })
    
    return pd.DataFrame(records)

def save_to_duckdb(df, table_name, db_path="data/raw/india_dev.duckdb"):
    """Save dataframe to DuckDB"""
    os.makedirs("data/raw", exist_ok=True)
    
    con = duckdb.connect(db_path)
    
    # Drop and recreate - ensures re-running doesn't duplicate data
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.execute(f"""
        CREATE TABLE {table_name} AS
        SELECT * FROM df
    """)
    
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"Saved {len(df)} rows to {table_name}. Total rows: {count}")
    con.close()

def run():
    all_data = []
    
    for code, name in INDICATORS.items():
        df = fetch_indicator(code, name)
        if df is not None and not df.empty:
            all_data.append(df)
    
    if not all_data:
        print("No data fetched. Check your internet connection.")
        return
    
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\nTotal records fetched: {len(combined)}")
    print(combined.head())
    
    save_to_duckdb(combined, "raw_world_bank")
    print("\nWorld Bank ingestion complete.")

if __name__ == "__main__":
    run()
