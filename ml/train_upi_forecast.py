import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_percentage_error
import joblib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from features import get_upi_monthly_features

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_COLS = [
    'time_index', 'month_num',
    'volume_lag_1', 'volume_lag_3', 'volume_lag_6', 'volume_lag_12',
    'volume_roll_3', 'volume_roll_6'
]

def rolling_backtest(df, n_windows=4, window_size=6):
    """Evaluate model across multiple historical windows for a reliable accuracy estimate"""
    mapes = []
    for i in range(n_windows):
        end = len(df) - i * window_size
        start = end - window_size
        if start < 30:
            break
        train_df, test_df = df.iloc[:start], df.iloc[start:end]
        X_train, y_train = train_df[FEATURE_COLS], train_df['log_volume']
        X_test, y_test_actual = test_df[FEATURE_COLS], test_df['volume_mn']

        model = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)
        model.fit(X_train, y_train)
        preds = np.exp(model.predict(X_test))
        mapes.append(mean_absolute_percentage_error(y_test_actual, preds) * 100)
    return mapes

def train():
    df = get_upi_monthly_features()
    df['log_volume'] = np.log(df['volume_mn'])

    # Rolling backtest for a reliable accuracy estimate
    mapes = rolling_backtest(df)
    avg_mape = np.mean(mapes)

    print("=== Model 1: UPI Volume Forecaster ===")
    print(f"Rolling backtest MAPE across {len(mapes)} windows: {[f'{m:.2f}%' for m in mapes]}")
    print(f"Average MAPE: {avg_mape:.2f}%")

    # Train final production model on ALL available data
    X_full, y_full_log = df[FEATURE_COLS], df['log_volume']
    final_model = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)
    final_model.fit(X_full, y_full_log)

    joblib.dump(final_model, os.path.join(MODEL_DIR, "upi_forecaster.joblib"))
    joblib.dump(FEATURE_COLS, os.path.join(MODEL_DIR, "upi_forecaster_features.joblib"))
    joblib.dump({
        "rolling_mapes": mapes,
        "avg_mape": avg_mape,
        "log_transformed": True,
        "evaluation_method": "rolling 6-month backtest across 4 windows"
    }, os.path.join(MODEL_DIR, "upi_forecaster_metrics.joblib"))

    print(f"\nFinal model trained on all {len(df)} months, saved to {MODEL_DIR}/upi_forecaster.joblib")

if __name__ == "__main__":
    train()
