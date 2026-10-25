from flask import Blueprint, current_app, jsonify
from models.database_models import DemandPrediction, Product
from services.forecasting_service import forecast_next_week, risk_and_reorder
import os

bp=Blueprint("predictions",__name__,url_prefix="/api")
@bp.get("/predictions")
def predictions():
    rows=DemandPrediction.query.order_by(DemandPrediction.forecast_date, DemandPrediction.product_id).all()
    return jsonify({"ok":True,"items":[{"product":r.product.name,"product_id":r.product_id,"forecast_date":r.forecast_date.isoformat(),"predicted_units":round(r.predicted_units,2),"model_version":r.model_version} for r in rows]})
@bp.post("/predictions/generate")
def generate():
    path=current_app.config["MODEL_PATH"]
    if not os.path.exists(path):return jsonify({"ok":False,"error":"Model artifact not found. Run python -m ml.train first."}),409
    try:return jsonify({"ok":True,"items":forecast_next_week(path)})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),500
@bp.get("/reorder")
def reorder():
    items=[]
    for p in Product.query.all():
        from sqlalchemy import func
        from models.database_models import DemandPrediction
        avg=DemandPrediction.query.with_entities(func.avg(DemandPrediction.predicted_units)).filter_by(product_id=p.id).scalar() or 0
        items.append({"product":p.name,"sku":p.sku,"stock":p.stock_quantity,"forecast_daily":round(float(avg),2),**risk_and_reorder(p,float(avg))})
    return jsonify({"ok":True,"items":items})
