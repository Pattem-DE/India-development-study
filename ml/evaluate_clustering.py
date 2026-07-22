import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from itertools import combinations
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from features import get_yearly_development_features

ALL_FEATURES = [
    'gdp_trillion_usd', 'internet_users_pct', 'mobile_per_100',
    'electricity_access_pct', 'emissions_intensity'
]

def evaluate_k(X_scaled, k_range=range(2, 6)):
    best = None
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        if best is None or score > best[1]:
            best = (k, score)
    return best

def evaluate():
    df = get_yearly_development_features()
    df['upi_volume_mn'] = df['upi_volume_mn'].fillna(0)

    print("=== Checking variance of each feature (higher = more differentiating) ===")
    for f in ALL_FEATURES:
        print(f"  {f}: std={df[f].std():.3f}, range={df[f].max()-df[f].min():.3f}")

    print("\n=== Testing feature subsets to find best-separated clustering ===")
    best_overall = None

    # Try all subsets of features with at least 2 features
    for r in range(2, len(ALL_FEATURES) + 1):
        for subset in combinations(ALL_FEATURES, r):
            X = df[list(subset)].copy()
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            k, score = evaluate_k(X_scaled)

            if best_overall is None or score > best_overall[2]:
                best_overall = (subset, k, score)

    print(f"\nBest feature subset: {best_overall[0]}")
    print(f"Best k: {best_overall[1]}, Silhouette score: {best_overall[2]:.3f}")
    print(f"(Previous full-feature score was 0.424 at k=3)")

if __name__ == "__main__":
    evaluate()
