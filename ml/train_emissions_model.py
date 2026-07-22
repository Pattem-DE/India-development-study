import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from features import get_yearly_development_features

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def train():
    df = get_yearly_development_features()

    # Fit a simple trend line: emissions_intensity ~ year
    X = df[['year']].values
    y = df['emissions_intensity'].values

    model = LinearRegression()
    model.fit(X, y)

    slope = model.coef_[0]
    r2 = model.score(X, y)

    # Overall change from first to last year
    first_year_intensity = df['emissions_intensity'].iloc[0]
    last_year_intensity = df['emissions_intensity'].iloc[-1]
    pct_change = ((last_year_intensity - first_year_intensity) / first_year_intensity) * 100

    # GDP growth vs emissions growth (total, not per-capita/per-GDP)
    gdp_total_growth = ((df['gdp_trillion_usd'].iloc[-1] - df['gdp_trillion_usd'].iloc[0])
                         / df['gdp_trillion_usd'].iloc[0]) * 100
    emissions_total_growth = ((df['total_co2e_mt'].iloc[-1] - df['total_co2e_mt'].iloc[0])
                               / df['total_co2e_mt'].iloc[0]) * 100

    print("=== Model 2: GDP vs Emissions Decoupling ===")
    print(f"Emissions intensity trend slope: {slope:.2f} per year (R²={r2:.3f})")
    print(f"Emissions intensity change {df['year'].min()}-{df['year'].max()}: {pct_change:+.1f}%")
    print(f"\nGDP total growth: {gdp_total_growth:+.1f}%")
    print(f"Emissions total growth: {emissions_total_growth:+.1f}%")

    if slope < 0:
        verdict = (f"India shows signs of DECOUPLING: emissions intensity fell "
                   f"{abs(pct_change):.1f}% while GDP grew {gdp_total_growth:.1f}%. "
                   f"The economy is growing more efficiently per unit of emissions.")
    else:
        verdict = (f"India shows NO decoupling yet: emissions intensity rose "
                   f"{pct_change:.1f}% alongside GDP growth of {gdp_total_growth:.1f}%. "
                   f"Growth is still emissions-heavy.")

    print(f"\nVerdict: {verdict}")

    joblib.dump(model, os.path.join(MODEL_DIR, "emissions_trend.joblib"))
    joblib.dump({
        "slope": slope, "r2": r2, "pct_change": pct_change,
        "gdp_total_growth": gdp_total_growth,
        "emissions_total_growth": emissions_total_growth,
        "verdict": verdict
    }, os.path.join(MODEL_DIR, "emissions_trend_metrics.joblib"))

    print(f"\nModel saved to {MODEL_DIR}/emissions_trend.joblib")

if __name__ == "__main__":
    train()
