"""Application configuration. Credentials are supplied via environment/.env."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-for-local-development")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://smartstock:change_me@localhost:3306/smartstock_db?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "ml" / "artifacts" / "demand_model.joblib"))
    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "12"))
