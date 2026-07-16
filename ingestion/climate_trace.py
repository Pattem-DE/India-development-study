import requests
import pandas as pd
import duckdb
import time
from datetime import datetime

DB_PATH = "data/raw/india_dev.duckdb"
BASE_URL = "https://api.climatetrace.org/v6"

SECTORS = [
    "power",
    "transportation",
    "manufacturing",
    "fossil-fuel-operations",
    "agriculture",
    "buildings",
    "waste",
    "forestry-and-land-use"
]

YEARS = list(range(2015, 2025))

def fetch_emissions(sector, year, country="IND"):
    """Fetch emissions for a specific sector and year"""
    url = f"{BASE_URL}/country/emissions"
    params = {
        "countries": country,
        "sectors": sector,
        "since": year,
        "to": year
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return None

        data = response.json()
        if not data:
            return None

        entry = data[0]
        emissions = entry.get("emissions", {})

        return {
            "year": year,
            "country_code": country,
            "sector": sector,
            "rank": entry.get("rank"),
            "co2_tonnes": emissions.get("co2", 0),
            "ch4_tonnes": emissions.get("ch4", 0),
            "n2o_tonnes": emissions.get("n2o", 0),
            "co2e_100yr_tonnes": emissions.get("co2e_100yr", 0),
            "co2e_20yr_tonnes": emissions.get("co2e_20yr", 0),
            "source": "Climate TRACE API v6",
            "ingested_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"  Error {sector} {year}: {e}")
        return None

def run():
    print("Starting Climate TRACE ingestion — India 2015-2024\n")
    records = []

    for sector in SECTORS:
        print(f"Fetching sector: {sector}")
        for year in YEARS:
            record = fetch_emissions(sector, year)
            if record:
                records.append(record)
                print(f"  {year}: co2e={record['co2e_100yr_tonnes']:,.0f} tonnes")
            time.sleep(2)  # polite rate limiting — 2 sec gap between calls

    if not records:
        print("No data fetched.")
        return

    df = pd.DataFrame(records)
    print(f"\nTotal rows: {len(df)}")
    print(f"Sectors: {df['sector'].nunique()}")
    print(f"Years: {df['year'].min()} to {df['year'].max()}")
    print(f"\nSample:")
    print(df.head(5))

    # Save to DuckDB
    con = duckdb.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS raw_climate_trace")
    con.execute("CREATE TABLE raw_climate_trace AS SELECT * FROM df")
    count = con.execute("SELECT COUNT(*) FROM raw_climate_trace").fetchone()[0]
    print(f"\nSaved {count} rows to raw_climate_trace")
    con.close()
    print("\nClimate TRACE ingestion complete.")

if __name__ == "__main__":
    run()
