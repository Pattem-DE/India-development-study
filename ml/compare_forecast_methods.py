import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_percentage_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from features import get_upi_monthly_features

FEATURE_COLS = ['time_index', 'month_num', 'volume_lag_1', 'volume_lag_3',
                'volume_lag_6', 'volume_lag_12', 'volume_roll_3', 'volume_roll_6']


def eval_gbm_baseline(df, n_windows=3, window_size=6):
    """Our current baseline - GBM directly on log(volume), recursive"""
    mapes = []
    for w in range(n_windows):
        end = len(df) - w * window_size
        start = end - window_size
        if start < 30:
            break
        train_df = df.iloc[:start].copy()
        test_df = df.iloc[start:end].copy()
        train_df['log_volume'] = np.log(train_df['volume_mn'])

        gbm = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)
        gbm.fit(train_df[FEATURE_COLS], train_df['log_volume'])

        history = train_df['volume_mn'].tolist()
        month_start = test_df.iloc[0]['month_date'].month
        preds = []
        for i in range(window_size):
            month_num = ((month_start + i - 1) % 12) + 1
            feat = pd.DataFrame([{
                'time_index': train_df['time_index'].iloc[-1] + 1 + i, 'month_num': month_num,
                'volume_lag_1': history[-1], 'volume_lag_3': history[-3],
                'volume_lag_6': history[-6], 'volume_lag_12': history[-12],
                'volume_roll_3': np.mean(history[-3:]), 'volume_roll_6': np.mean(history[-6:]),
            }])
            pred_vol = np.exp(gbm.predict(feat[FEATURE_COLS])[0])
            history.append(pred_vol)
            preds.append(pred_vol)
        mapes.append(mean_absolute_percentage_error(test_df['volume_mn'], preds) * 100)
    return mapes


def eval_holt_damped(df, n_windows=3, window_size=6):
    """Holt's damped trend - built specifically for decelerating growth curves"""
    mapes = []
    for w in range(n_windows):
        end = len(df) - w * window_size
        start = end - window_size
        if start < 30:
            break
        train_df = df.iloc[:start].copy()
        test_df = df.iloc[start:end].copy()

        model = ExponentialSmoothing(
            train_df['volume_mn'].values,
            trend='add', damped_trend=True, seasonal=None
        ).fit()
        preds = model.forecast(window_size)
        mapes.append(mean_absolute_percentage_error(test_df['volume_mn'], preds) * 100)
    return mapes


def eval_prophet(df, n_windows=3, window_size=6):
    """Facebook Prophet - piecewise trend with automatic changepoint detection"""
    mapes = []
    for w in range(n_windows):
        end = len(df) - w * window_size
        start = end - window_size
        if start < 30:
            break
        train_df = df.iloc[:start].copy()
        test_df = df.iloc[start:end].copy()

        prophet_df = train_df[['month_date', 'volume_mn']].rename(
            columns={'month_date': 'ds', 'volume_mn': 'y'})

        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(prophet_df)

        future = m.make_future_dataframe(periods=window_size, freq='MS')
        forecast = m.predict(future)
        preds = forecast['yhat'].tail(window_size).values

        mapes.append(mean_absolute_percentage_error(test_df['volume_mn'], preds) * 100)
    return mapes


if __name__ == "__main__":
    df = get_upi_monthly_features()

    print("=== Comparing 3 forecasting approaches (honest recursive evaluation) ===\n")

    gbm_mapes = eval_gbm_baseline(df)
    print(f"1. GBM baseline (current):     {[f'{m:.2f}%' for m in gbm_mapes]} -> avg {np.mean(gbm_mapes):.2f}%")

    holt_mapes = eval_holt_damped(df)
    print(f"2. Holt's Damped Trend:         {[f'{m:.2f}%' for m in holt_mapes]} -> avg {np.mean(holt_mapes):.2f}%")

    prophet_mapes = eval_prophet(df)
    print(f"3. Prophet:                     {[f'{m:.2f}%' for m in prophet_mapes]} -> avg {np.mean(prophet_mapes):.2f}%")

    print("\n=== Summary ===")
    results = {
        "GBM baseline": np.mean(gbm_mapes),
        "Holt's Damped Trend": np.mean(holt_mapes),
        "Prophet": np.mean(prophet_mapes)
    }
    winner = min(results, key=results.get)
    print(f"Best method: {winner} ({results[winner]:.2f}% avg MAPE)")
