import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from sqlalchemy import text

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=PROJECT_DIR / ".env", override=False)

from config import Config
from models.database_models import db
from routes.products import bp as products_bp
from routes.sales import bp as sales_bp
from routes.analytics import bp as analytics_bp
from routes.predictions import bp as predictions_bp


def create_app(test_config=None):
    app=Flask(__name__)
    app.config.from_object(Config)
    if test_config: app.config.update(test_config)
    db.init_app(app)
    app.register_blueprint(products_bp);app.register_blueprint(sales_bp);app.register_blueprint(analytics_bp);app.register_blueprint(predictions_bp)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    @app.get("/")
    def index(): return render_template("index.html")
    @app.get("/health/db")
    def database_health():
        try:db.session.execute(text("SELECT 1"));return jsonify({"ok":True,"database":"connected"})
        except Exception as exc:
            db.session.rollback()
            app.logger.exception("Database health check failed")
            original = str(getattr(exc, "orig", exc)).lower()
            if "access denied" in original or "authentication" in original:
                hint = "MySQL rejected the login. Use the same username and password that work in MySQL Workbench."
            elif "can't connect" in original or "connection refused" in original or "timed out" in original:
                hint = "Could not reach MySQL. Make sure the MySQL80 service is running and the host/port are correct."
            elif "unknown database" in original:
                hint = "Database smartstock_db was not found. Run schema.sql once in MySQL Workbench."
            else:
                hint = "Check the application terminal for the database error; never share the password."
            return jsonify({"ok":False,"database":"unavailable","error":hint}),503
    @app.get("/api/pipeline/status")
    def pipeline_status():
        from models.database_models import PipelineLog
        last=PipelineLog.query.order_by(PipelineLog.started_at.desc()).first()
        return jsonify({"ok":True,"last_run":None if not last else {"status":last.status,"started_at":last.started_at.isoformat(),"finished_at":last.finished_at.isoformat() if last.finished_at else None,"records_processed":last.records_processed,"error":last.error_message}})
    @app.errorhandler(404)
    def not_found(_):return jsonify({"ok":False,"error":"Resource not found"}),404
    @app.errorhandler(500)
    def server_error(_):db.session.rollback();return jsonify({"ok":False,"error":"Unexpected server error. Check application logs."}),500
    return app

app=create_app()
if __name__=="__main__":
    with app.app_context():
        try:db.create_all()
        except Exception:app.logger.exception("Database initialization failed")
    app.run(host="127.0.0.1",port=5000,debug=app.config.get("DEBUG",False))
