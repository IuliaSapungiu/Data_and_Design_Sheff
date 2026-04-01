import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from features.progression import compute_progression_features
from features.performance import compute_performance_features


FEATURE_COLS = ["Age", "percentile", "progression_slope", "rate_of_improvement", "years_competing"]


def build_feature_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combines progression + performance features into one table.
    Also pulls latest Age from raw df.
    """
    prog = compute_progression_features(df)
    perf = compute_performance_features(df)

    # Latest age per swimmer
    latest_age = (
        df.sort_values("Year")
        .groupby("Swimmer")["Age"]
        .last()
        .reset_index()
        .rename(columns={"Age": "Age"})
    )

    merged = prog.merge(perf, on=["Swimmer", "FullEvent"], how="inner")
    merged = merged.merge(latest_age, on="Swimmer", how="left")

    return merged.dropna(subset=FEATURE_COLS)


def find_similar_swimmers(
    feature_table: pd.DataFrame,
    swimmer: str,
    event: str,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Given a feature table, finds the top_n most similar swimmers
    to the target swimmer in the same event using Euclidean distance.
    """
    event_df = feature_table[feature_table["FullEvent"] == event].copy()

    if swimmer not in event_df["Swimmer"].values:
        return pd.DataFrame()

    target_row = event_df[event_df["Swimmer"] == swimmer][FEATURE_COLS].values
    others = event_df[FEATURE_COLS].values

    scaler = StandardScaler()
    scaled_all = scaler.fit_transform(others)
    scaled_target = scaler.transform(target_row)

    distances = np.linalg.norm(scaled_all - scaled_target, axis=1)
    event_df = event_df.copy()
    event_df["similarity_distance"] = distances

    # Exclude the swimmer themselves, sort by distance
    similar = (
        event_df[event_df["Swimmer"] != swimmer]
        .sort_values("similarity_distance")
        .head(top_n)
    )
    return similar


def predict_performance(
    df: pd.DataFrame,
    feature_table: pd.DataFrame,
    swimmer: str,
    event: str
):
    """
    Trains a GradientBoosting model on similar swimmers and predicts:
      - predicted_time_2yr      : expected time in 2 years
      - expected_improvement_pct: % improvement expected
      - prob_final               : probability of reaching final level (top 10%)

    Returns a dict of predictions or None if not enough data.
    """
    similar = find_similar_swimmers(feature_table, swimmer, event, top_n=20)

    if len(similar) < 5:
        return None

    # Target: average improvement per year (from progression)
    if "rate_of_improvement" not in similar.columns:
        return None

    X = similar[FEATURE_COLS]
    y = similar["rate_of_improvement"]

    if y.nunique() < 2:
        return None

    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    target_features = feature_table[
        (feature_table["Swimmer"] == swimmer) &
        (feature_table["FullEvent"] == event)
    ][FEATURE_COLS]

    if target_features.empty:
        return None

    pred_improvement_per_year = model.predict(target_features)[0]
    pred_improvement_2yr = pred_improvement_per_year * 2

    # Latest time
    swimmer_event_df = df[
        (df["Swimmer"] == swimmer) & (df["FullEvent"] == event)
    ].sort_values("Year")
    latest_time = float(swimmer_event_df["Time"].iloc[-1])

    pred_time_2yr = latest_time - pred_improvement_2yr  # subtract because lower = faster

    # Expected improvement %
    expected_improvement_pct = (pred_improvement_2yr / latest_time) * 100

    # Probability of reaching final level (top 10% of event times)
    all_event_times = df[df["FullEvent"] == event]["Time"].dropna().values
    top10_threshold = np.percentile(all_event_times, 10)  # lower = faster

    current_gap   = latest_time - top10_threshold
    predicted_gap = pred_time_2yr - top10_threshold

    if current_gap <= 0:
        prob_final = 1.0
    else:
        prob_final = max(0.0, min(1.0, 1 - (predicted_gap / current_gap)))

    return {
        "latest_time":             latest_time,
        "predicted_time_2yr":      pred_time_2yr,
        "expected_improvement_2yr": pred_improvement_2yr,
        "expected_improvement_pct": expected_improvement_pct,
        "prob_final":              prob_final,
        "similar_swimmers":        similar,
    }