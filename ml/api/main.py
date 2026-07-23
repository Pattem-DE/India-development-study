import os
import sys
import warnings
warnings.filterwarnings('ignore')

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from features import get_upi_monthly_features, get_yearly_development_features

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

app = FastAPI(
    title="India Development Study - ML API",
    description="Serves 3 models: UPI forecasting (Prophet), GDP-emissions decoupling, development eras clustering",
    version="1.1.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Load all models once at startup ---
upi_model = joblib.load(os.path.join(MODEL_DIR, "upi_forecaster.joblib"))
upi_metrics = joblib.load(os.path.join(MODEL_DIR, "upi_forecaster_metrics.joblib"))

emissions_model = joblib.load(os.path.join(MODEL_DIR, "emissions_trend.joblib"))
emissions_metrics = joblib.load(os.path.join(MODEL_DIR, "emissions_trend_metrics.joblib"))

eras_model = joblib.load(os.path.join(MODEL_DIR, "eras_clustering.joblib"))
eras_scaler = joblib.load(os.path.join(MODEL_DIR, "eras_scaler.joblib"))
eras_labels = joblib.load(os.path.join(MODEL_DIR, "eras_labels.joblib"))
eras_features = joblib.load(os.path.join(MODEL_DIR, "eras_features.joblib"))
eras_metrics = joblib.load(os.path.join(MODEL_DIR, "eras_metrics.joblib"))


@app.get("/")
def root():
    return {
        "service": "India Development Study - ML API",
        "endpoints": [
            "/predict/upi-volume?months_ahead=12",
            "/predict/emissions-trend",
            "/predict/development-eras",
            "/health"
        ]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/predict/upi-volume")
def predict_upi_volume(months_ahead: int = 12):
    """Forecast UPI transaction volume for the next N months using Prophet"""
    if months_ahead < 1 or months_ahead > 24:
        raise HTTPException(400, "months_ahead must be between 1 and 24")

    df = get_upi_monthly_features()

    # Prophet forecasts natively - no manual recursive loop needed
    future = upi_model.make_future_dataframe(periods=months_ahead, freq='MS')
    forecast = upi_model.predict(future)

    future_only = forecast.tail(months_ahead)
    forecasts = [
        {
            "month": row['ds'].strftime("%Y-%m"),
            "predicted_volume_mn": round(max(row['yhat'], 0), 2),
            "confidence_low": round(max(row['yhat_lower'], 0), 2),
            "confidence_high": round(row['yhat_upper'], 2)
        }
        for _, row in future_only.iterrows()
    ]

    return {
        "forecast": forecasts,
        "model_accuracy": {
            "avg_mape_pct": round(upi_metrics["avg_mape"], 2),
            "method": upi_metrics["method"],
            "evaluation_method": upi_metrics["evaluation_method"]
        },
        "historical_data": [
            {"month": row['month_date'].strftime("%Y-%m"), "volume_mn": round(row['volume_mn'], 2)}
            for _, row in df.iterrows()
        ]
    }


@app.get("/predict/emissions-trend")
def predict_emissions_trend():
    df = get_yearly_development_features()
    return {
        "verdict": emissions_metrics["verdict"],
        "emissions_intensity_change_pct": round(emissions_metrics["pct_change"], 1),
        "gdp_total_growth_pct": round(emissions_metrics["gdp_total_growth"], 1),
        "emissions_total_growth_pct": round(emissions_metrics["emissions_total_growth"], 1),
        "trend_slope": round(emissions_metrics["slope"], 2),
        "r_squared": round(emissions_metrics["r2"], 3),
        "yearly_data": [
            {"year": int(row['year']), "gdp_trillion_usd": round(row['gdp_trillion_usd'], 3),
             "total_co2e_mt": round(row['total_co2e_mt'], 1), "emissions_intensity": round(row['emissions_intensity'], 1)}
            for _, row in df.iterrows()
        ]
    }


@app.get("/predict/development-eras")
def predict_development_eras():
    df = get_yearly_development_features()
    df['upi_volume_mn'] = df['upi_volume_mn'].fillna(0)

    X = df[eras_features]
    X_scaled = eras_scaler.transform(X)
    clusters = eras_model.predict(X_scaled)
    df['era_name'] = [eras_labels[c] for c in clusters]

    return {
        "silhouette_score": round(eras_metrics["silhouette_score"], 3),
        "features_used": eras_metrics["features_used"],
        "methodology_note": eras_metrics["note"],
        "years": [
            {"year": int(row['year']), "era": row['era_name'],
             "gdp_trillion_usd": round(row['gdp_trillion_usd'], 3),
             "internet_users_pct": round(row['internet_users_pct'], 1),
             "upi_volume_mn": round(row['upi_volume_mn'], 2)}
            for _, row in df.iterrows()
        ]
    }
