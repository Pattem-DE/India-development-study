import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import joblib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from features import get_yearly_development_features

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Dropped electricity_access_pct only - it was redundant with BOTH gdp (0.91)
# AND internet_users_pct (0.90), essentially double-counting the same signal.
# Kept internet_users_pct since it's the core digital-adoption signal this
# whole study is about, even though it correlates with GDP at 0.92 - some
# correlation between genuinely meaningful features is expected and fine.
CLUSTER_FEATURES = ['gdp_trillion_usd', 'internet_users_pct', 'mobile_per_100', 'emissions_intensity']

def train():
    df = get_yearly_development_features()
    df['upi_volume_mn'] = df['upi_volume_mn'].fillna(0)

    X = df[CLUSTER_FEATURES].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("=== Validating k with refined feature set ===")
    best_k, best_score = None, -1
    for k in range(2, 6):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        print(f"  k={k}: silhouette={score:.3f}")
        if score > best_score:
            best_k, best_score = k, score
    print(f"\nBest k: {best_k} (score={best_score:.3f})")

    n_clusters = best_k
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['era_cluster'] = kmeans.fit_predict(X_scaled)

    cluster_order = df.groupby('era_cluster')['year'].mean().sort_values().index.tolist()
    era_names = ["Foundation Era", "Digital Transition", "Mature Digital Economy"] if n_clusters == 3 \
                else [f"Era {i+1}" for i in range(n_clusters)]
    cluster_to_era = {cluster: era_names[i] for i, cluster in enumerate(cluster_order)}
    df['era_name'] = df['era_cluster'].map(cluster_to_era)

    print("\n=== India's Development Eras ===")
    print(df[['year', 'era_name'] + CLUSTER_FEATURES].to_string(index=False))

    print("\n=== Era Profiles (average values) ===")
    profile = df.groupby('era_name')[CLUSTER_FEATURES + ['year']].mean()
    print(profile.round(2))

    joblib.dump(kmeans, os.path.join(MODEL_DIR, "eras_clustering.joblib"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "eras_scaler.joblib"))
    joblib.dump(cluster_to_era, os.path.join(MODEL_DIR, "eras_labels.joblib"))
    joblib.dump(CLUSTER_FEATURES, os.path.join(MODEL_DIR, "eras_features.joblib"))
    joblib.dump({
        "silhouette_score": best_score, "k": n_clusters, "features_used": CLUSTER_FEATURES,
        "note": "Dropped electricity_access_pct (redundant with gdp AND internet at 0.90-0.91 correlation). Kept internet_users_pct despite 0.92 correlation with gdp since it's the core digital-adoption signal for this study."
    }, os.path.join(MODEL_DIR, "eras_metrics.joblib"))

    print(f"\nModel saved to {MODEL_DIR}/eras_clustering.joblib")

if __name__ == "__main__":
    train()
