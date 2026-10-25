"""Leakage-safe demand feature engineering and training helpers."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

FEATURES = ["product_id", "dow", "lag_1", "lag_7", "mean_7", "mean_28", "trend_7"]


def make_features(frame):
    data = frame.copy()
    data["sale_date"] = pd.to_datetime(data["sale_date"])
    data = data.sort_values(["product_id", "sale_date"])
    groups = data.groupby("product_id")["units_sold"]
    data["dow"] = data["sale_date"].dt.dayofweek
    data["lag_1"] = groups.shift(1)
    data["lag_7"] = groups.shift(7)
    data["mean_7"] = groups.transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean())
    data["mean_28"] = groups.transform(lambda s: s.shift(1).rolling(28, min_periods=1).mean())
    data["trend_7"] = data["mean_7"] - data["mean_28"]
    return data.dropna(subset=["lag_1", "lag_7"])


def train_and_evaluate(frame, random_state=42):
    features = make_features(frame)
    if len(features) < 14:
        raise ValueError("At least 14 feature-ready daily observations are required")
    features = features.sort_values("sale_date")
    split = max(1, int(len(features) * .8))
    train, test = features.iloc[:split], features.iloc[split:]
    if test.empty:
        train, test = features.iloc[:-1], features.iloc[-1:]
    model = RandomForestRegressor(n_estimators=160, min_samples_leaf=2, random_state=random_state, n_jobs=-1)
    model.fit(train[FEATURES], train["units_sold"])
    pred = np.maximum(0, model.predict(test[FEATURES]))
    baseline = np.maximum(0, test["mean_7"].to_numpy())
    metrics = {"mae": float(mean_absolute_error(test["units_sold"], pred)), "rmse": float(np.sqrt(mean_squared_error(test["units_sold"], pred))), "baseline_mae": float(mean_absolute_error(test["units_sold"], baseline)), "test_rows": int(len(test))}
    model.fit(features[FEATURES], features["units_sold"])
    return model, metrics
