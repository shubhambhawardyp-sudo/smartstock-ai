"""Train/evaluate model: python -m ml.train"""
import os, joblib
from datetime import datetime
from app import create_app
from config import Config
from models.database_models import db, DailyProductSale, ModelMetric
from models.demand_model import train_and_evaluate
from services.forecasting_service import historical_frame, MODEL_VERSION

def run():
    app=create_app()
    with app.app_context():
        frame=historical_frame()
        if frame.empty or frame.groupby("product_id").size().max()<14:
            raise SystemExit("Insufficient real sales history. Use the explicitly labeled demo generator: python -m ml.generate_demo_data --days 120")
        model,metrics=train_and_evaluate(frame)
        os.makedirs(os.path.dirname(Config.MODEL_PATH),exist_ok=True);joblib.dump(model,Config.MODEL_PATH)
        for name,value in metrics.items():
            db.session.add(ModelMetric(model_version=MODEL_VERSION,model_name="RandomForestRegressor",metric_name=name,metric_value=value,evaluated_at=datetime.utcnow()))
        db.session.commit();print(f"Saved model to {Config.MODEL_PATH}; chronological holdout metrics: {metrics}")

if __name__=="__main__":run()
