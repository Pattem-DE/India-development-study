import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from features import get_upi_monthly_features

RESIDUAL_FEATURES = ['month_num', 'volume_lag_1', 'volume_lag_3', 'volume_lag_6', 'volume_lag_12', 'volume_roll_3', 'volume_roll_6']
GBM_FEATURES = ['time_index', 'month_num', 'volume_lag_1', 'volume_lag_3', 'volume_lag_6', 'volume_lag_12', 'volume_roll_3', 'volume_roll_6']

def recursive_forecast(model, history_volumes, start_time_index, months, month_start, use_trend=None, feature_cols=None):
    """Recursively forecast N months ahead, feeding predictions back in as lag inputs - exactly like the API does"""
    history = list(history_volumes)
    preds = []
    for i in range(months):
        month_num = ((month_start + i - 1) % 12) + 1
        feat = {
            'time_index': start_time_index + i,
            'month_num': month_num,
            'volume_lag_1': history[-1],
            'volume_lag_3': history[-3],
            'volume_lag_6': history[-6],
            'volume_lag_12': history[-12],
            'volume_roll_3': np.mean(history[-3:]),
            'volume_roll_6': np.mean(history[-6:]),
        }
        X = pd.DataFrame([feat])

        if use_trend is not None:
            time_idx_sq = (start_time_index + i) ** 2 if False else None
            trend_pred = use_trend.predict(X[['time_index']]) if hasattr(use_trend, 'coef_') and len(use_trend.coef_) == 1 else None
            residual_pred = model.predict(X[feature_cols])[0]
            pred_log = trend_pred[0] + residual_pred if trend_pred is not None else residual_pred
        else:
            pred_log = model.predict(X[feature_cols])[0]

        pred_volume = np.exp(pred_log)
        history.append(pred_volume)
        preds.append(pred_volume)
    return preds

def evaluate_original_gbm(df, test_months=6, n_windows=3):
    """Recursive evaluation of the ORIGINAL approach (GBM directly on log volume, no detrending)"""
    mapes = []
    for w in range(n_windows):
        end = len(df) - w * test_months
        start = end - test_months
        if start < 30:
            break
        train_df = df.iloc[:start].copy()
        test_df = df.iloc[start:end].copy()
        train_df['log_volume'] = np.log(train_df['volume_mn'])

        gbm = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)
        gbm.fit(train_df[GBM_FEATURES], train_df['log_volume'])

        history = train_df['volume_mn'].tolist()
        month_start = test_df.iloc[0]['month_date'].month
        preds = recursive_forecast(gbm, history, train_df['time_index'].iloc[-1] + 1, test_months, month_start, feature_cols=GBM_FEATURES)

        mape = mean_absolute_percentage_error(test_df['volume_mn'], preds) * 100
        mapes.append(mape)
        print(f"  Window {w+1}: recursive MAPE = {mape:.2f}%  (predicted: {[f'{p:.0f}' for p in preds]})")
        print(f"              actual:            {test_df['volume_mn'].round(0).tolist()}")
    return mapes

if __name__ == "__main__":
    df = get_upi_monthly_features()
    print("=== HONEST recursive evaluation: original GBM (no detrending) ===")
    mapes = evaluate_original_gbm(df)
    print(f"\nAverage recursive MAPE: {np.mean(mapes):.2f}%")
    print("(This is the REAL accuracy for 6-month-ahead recursive forecasting,")
    print(" as opposed to the misleading 10.42% from one-step backtesting)")

def evaluate_quadratic_detrend(df, test_months=6, n_windows=3):
    """Recursive evaluation of quadratic detrend - does it fix the widening gap?"""
    from sklearn.linear_model import LinearRegression
    mapes = []
    for w in range(n_windows):
        end = len(df) - w * test_months
        start = end - test_months
        if start < 30:
            break
        train_df = df.iloc[:start].copy()
        test_df = df.iloc[start:end].copy()
        train_df['log_volume'] = np.log(train_df['volume_mn'])
        train_df['time_index_sq'] = train_df['time_index'] ** 2

        trend_model = LinearRegression()
        trend_model.fit(train_df[['time_index', 'time_index_sq']], train_df['log_volume'])
        train_df['residual'] = train_df['log_volume'] - trend_model.predict(train_df[['time_index', 'time_index_sq']])

        gbm = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)
        gbm.fit(train_df[RESIDUAL_FEATURES], train_df['residual'])

        history = train_df['volume_mn'].tolist()
        month_start = test_df.iloc[0]['month_date'].month
        preds = []
        for i in range(test_months):
            t_idx = train_df['time_index'].iloc[-1] + 1 + i
            month_num = ((month_start + i - 1) % 12) + 1
            feat = {
                'month_num': month_num,
                'volume_lag_1': history[-1], 'volume_lag_3': history[-3],
                'volume_lag_6': history[-6], 'volume_lag_12': history[-12],
                'volume_roll_3': np.mean(history[-3:]), 'volume_roll_6': np.mean(history[-6:]),
            }
            X = pd.DataFrame([feat])
            trend_pred = trend_model.predict(pd.DataFrame([[t_idx, t_idx**2]], columns=['time_index', 'time_index_sq']))[0]
            resid_pred = gbm.predict(X[RESIDUAL_FEATURES])[0]
            pred_vol = np.exp(trend_pred + resid_pred)
            history.append(pred_vol)
            preds.append(pred_vol)

        mape = mean_absolute_percentage_error(test_df['volume_mn'], preds) * 100
        mapes.append(mape)
        print(f"  Window {w+1}: recursive MAPE = {mape:.2f}%  (predicted: {[f'{p:.0f}' for p in preds]})")
        print(f"              actual:            {test_df['volume_mn'].round(0).tolist()}")
    return mapes

print("\n=== HONEST recursive evaluation: quadratic detrend ===")
mapes2 = evaluate_quadratic_detrend(df)
print(f"\nAverage recursive MAPE: {np.mean(mapes2):.2f}%")
