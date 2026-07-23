import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from prophet import Prophet
from sklearn.metrics import mean_absolute_percentage_error
import joblib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from features import get_upi_monthly_features

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def recursive_backtest(df, n_windows=3, window_size=6):
    """Honest evaluation: forecast forward from a real cutoff point, matching production behavior"""
    mapes = []
    for w in range(n_windows):
        end = len(df) - w * window_size
        start = end - window_size
        if start < 30:
            break
        train_df = df.iloc[:start].copy()
        test_df = df.iloc[start:end].copy()

        prophet_df = train_df[['month_date', 'volume_mn']].rename(columns={'month_date': 'ds', 'volume_mn': 'y'})
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(prophet_df)

        future = m.make_future_dataframe(periods=window_size, freq='MS')
        forecast = m.predict(future)
        preds = forecast['yhat'].tail(window_size).values

        mapes.append(mean_absolute_percentage_error(test_df['volume_mn'], preds) * 100)
    return mapes


def train():
    df = get_upi_monthly_features()

    mapes = recursive_backtest(df)
    avg_mape = np.mean(mapes)

    print("=== Model 1: UPI Volume Forecaster (Prophet) ===")
    print(f"Honest recursive MAPE across {len(mapes)} windows: {[f'{m:.2f}%' for m in mapes]}")
    print(f"Average MAPE: {avg_mape:.2f}%")

    # Train final production model on ALL available data
    prophet_df = df[['month_date', 'volume_mn']].rename(columns={'month_date': 'ds', 'volume_mn': 'y'})
    final_model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    final_model.fit(prophet_df)

    joblib.dump(final_model, os.path.join(MODEL_DIR, "upi_forecaster.joblib"))
    joblib.dump({
        "rolling_mapes": mapes,
        "avg_mape": avg_mape,
        "method": "Facebook Prophet (piecewise trend + yearly seasonality)",
        "evaluation_method": "recursive rolling 6-month backtest across 3 windows",
        "history": "Started with GBM on log(volume) - flatlined on long-horizon recursive forecasts "
                   "since tree models cannot extrapolate beyond training range (10.75% recursive MAPE). "
                   "Tried linear detrend (17.05%, overshot) and quadratic detrend (15.90%, unstable "
                   "extrapolation, predicted decline). Compared against purpose-built time-series methods: "
                   "Holt's Damped Trend (3.76%) and Prophet (3.17%) - both dramatically outperformed "
                   "hand-built approaches, confirming tree-based models are the wrong tool for trend "
                   "extrapolation regardless of feature engineering."
    }, os.path.join(MODEL_DIR, "upi_forecaster_metrics.joblib"))

    print(f"\nFinal Prophet model trained on all {len(df)} months, saved to {MODEL_DIR}/upi_forecaster.joblib")

if __name__ == "__main__":
    train()
