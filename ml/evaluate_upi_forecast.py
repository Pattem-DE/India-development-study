import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_percentage_error
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from features import get_upi_monthly_features

FEATURE_COLS = [
    'time_index', 'month_num',
    'volume_lag_1', 'volume_lag_3', 'volume_lag_6', 'volume_lag_12',
    'volume_roll_3', 'volume_roll_6'
]

def rolling_evaluation():
    df = get_upi_monthly_features()
    df['log_volume'] = np.log(df['volume_mn'])

    # Test on the last 4 different 6-month windows (rolling backtest)
    n_windows = 4
    window_size = 6
    mapes = []

    for i in range(n_windows):
        end = len(df) - i * window_size
        start = end - window_size
        if start < 30:  # need enough training data
            break

        train_df = df.iloc[:start]
        test_df = df.iloc[start:end]

        X_train, y_train = train_df[FEATURE_COLS], train_df['log_volume']
        X_test = test_df[FEATURE_COLS]
        y_test_actual = test_df['volume_mn']

        model = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42)
        model.fit(X_train, y_train)
        preds = np.exp(model.predict(X_test))

        mape = mean_absolute_percentage_error(y_test_actual, preds) * 100
        mapes.append(mape)
        period = f"{test_df.iloc[0]['month_date'].strftime('%Y-%m')} to {test_df.iloc[-1]['month_date'].strftime('%Y-%m')}"
        print(f"Window {i+1} ({period}): MAPE = {mape:.2f}%")

    print(f"\nAverage MAPE across {len(mapes)} windows: {np.mean(mapes):.2f}%")
    print(f"This is a more reliable accuracy estimate than a single test period.")

if __name__ == "__main__":
    rolling_evaluation()
