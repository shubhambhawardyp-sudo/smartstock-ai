from datetime import date, timedelta
import os
import joblib
import numpy as np
import pandas as pd
from models.database_models import db, Product, DailyProductSale, DemandPrediction
from models.demand_model import FEATURES

MODEL_VERSION = "rf-v1"


def historical_frame():
    rows = DailyProductSale.query.order_by(DailyProductSale.product_id, DailyProductSale.sale_date).all()
    return pd.DataFrame([{"product_id": r.product_id, "sale_date": r.sale_date, "units_sold": r.units_sold} for r in rows])


def forecast_next_week(model_path):
    model = joblib.load(model_path)
    out = []
    start = date.today() + timedelta(days=1)
    end = date.today() + timedelta(days=7)
    DemandPrediction.query.filter(
        DemandPrediction.model_version == MODEL_VERSION,
        DemandPrediction.forecast_date.between(start, end),
    ).delete(synchronize_session=False)
    for product in Product.query.all():
        hist = DailyProductSale.query.filter_by(product_id=product.id).order_by(DailyProductSale.sale_date).all()
        units = [r.units_sold for r in hist]
        avg7 = float(np.mean(units[-7:])) if units else 0.0
        avg28 = float(np.mean(units[-28:])) if units else avg7
        l1 = units[-1] if units else avg7
        l7 = units[-7] if len(units) >= 7 else avg7
        for offset in range(1, 8):
            target = date.today() + timedelta(days=offset)
            row = pd.DataFrame([{"product_id": product.id, "dow": target.weekday(), "lag_1": l1, "lag_7": l7, "mean_7": avg7, "mean_28": avg28, "trend_7": avg7-avg28}])[FEATURES]
            value = max(0.0, float(model.predict(row)[0]))
            db.session.add(DemandPrediction(product_id=product.id, forecast_date=target, predicted_units=value, model_version=MODEL_VERSION))
            out.append({"product_id": product.id, "product": product.name, "forecast_date": target.isoformat(), "predicted_units": round(value, 2), "model_version": MODEL_VERSION})
    db.session.commit()
    return out


def risk_and_reorder(product, forecast_daily):
    lead_demand = max(0, forecast_daily) * product.lead_time_days
    safety = max(product.reorder_threshold, int(round(forecast_daily * 2)))
    point = int(np.ceil(lead_demand + safety))
    target = int(np.ceil(point + forecast_daily * 7))
    risk = "high" if product.stock_quantity <= lead_demand else "medium" if product.stock_quantity <= point else "low"
    return {"risk": risk, "explanation": f"Stock {product.stock_quantity}; expected lead-time demand {lead_demand:.1f}; lead time {product.lead_time_days} days.", "reorder_point": point, "suggested_quantity": max(0, target-product.stock_quantity), "safety_stock": safety}
