"""Execute: python -m pipelines.run_pipeline"""
from datetime import datetime
from app import create_app
from models.database_models import db, PipelineLog
from pipelines.extract import extract_sales
from pipelines.transform import transform_sales
from pipelines.load import load_daily

def run():
    app=create_app()
    with app.app_context():
        log=PipelineLog(status="RUNNING");db.session.add(log);db.session.commit()
        try:
            source=extract_sales();aggregate=transform_sales(source);count=load_daily(aggregate)
            log.status="SUCCESS";log.records_processed=count;log.finished_at=datetime.utcnow();db.session.commit()
            print(f"Pipeline succeeded: loaded {count} product-day aggregates")
        except Exception as exc:
            db.session.rollback();log=db.session.get(PipelineLog,log.id);log.status="FAILED";log.finished_at=datetime.utcnow();log.error_message=str(exc)[:4000];db.session.commit();raise

if __name__=="__main__":run()
