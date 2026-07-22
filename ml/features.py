import duckdb
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "india_dev.duckdb")

def get_upi_monthly_features():
    """
    Feature set for Model 1: UPI Volume Forecaster
    Builds lag features, rolling averages, and seasonality from monthly UPI data
    """
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT month_date, volume_mn, value_cr, avg_txn_value_inr, banks_live_on_upi
        FROM stg_upi_historical
        ORDER BY month_date
    """).df()
    con.close()

    df['month_date'] = pd.to_datetime(df['month_date'])
    df['month_num'] = df['month_date'].dt.month
    df['year'] = df['month_date'].dt.year
    df['time_index'] = range(len(df))  # simple trend index

    # Lag features
    for lag in [1, 3, 6, 12]:
        df[f'volume_lag_{lag}'] = df['volume_mn'].shift(lag)

    # Rolling averages
    df['volume_roll_3'] = df['volume_mn'].rolling(3).mean()
    df['volume_roll_6'] = df['volume_mn'].rolling(6).mean()

    # Drop rows with NaN from lag/rolling (first 12 months)
    df = df.dropna().reset_index(drop=True)

    return df


def get_yearly_development_features():
    """
    Feature set for Model 2 (GDP-Emissions decoupling) and 
    Model 3 (Development eras clustering)
    """
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT year, gdp_trillion_usd, poverty_rate_pct, internet_users_pct,
               mobile_per_100, electricity_access_pct, upi_volume_mn,
               upi_value_cr, total_co2e_mt, gdp_yoy_growth_pct
        FROM mart_india_development
        ORDER BY year
    """).df()
    con.close()

    # Emissions intensity = emissions per trillion USD of GDP
    df['emissions_intensity'] = df['total_co2e_mt'] / df['gdp_trillion_usd']

    # YoY change in emissions intensity (for decoupling model)
    df['emissions_intensity_yoy_pct'] = df['emissions_intensity'].pct_change() * 100

    return df


if __name__ == "__main__":
    print("=== UPI Monthly Features (Model 1) ===")
    upi_df = get_upi_monthly_features()
    print(f"Shape: {upi_df.shape}")
    print(upi_df.tail(5))

    print("\n=== Yearly Development Features (Models 2 & 3) ===")
    yearly_df = get_yearly_development_features()
    print(f"Shape: {yearly_df.shape}")
    print(yearly_df.to_string(index=False))
