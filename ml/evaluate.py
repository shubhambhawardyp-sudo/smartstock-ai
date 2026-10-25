"""Evaluation is performed chronologically by ml.train; inspect persisted metrics here."""
from app import create_app
from models.database_models import ModelMetric

if __name__=="__main__":
    app=create_app()
    with app.app_context():
        for row in ModelMetric.query.order_by(ModelMetric.evaluated_at.desc()).limit(30):print(row.evaluated_at,row.model_version,row.metric_name,row.metric_value)
