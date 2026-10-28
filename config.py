"""Application configuration. Credentials are supplied via environment/.env."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY or SECRET_KEY.startswith("replace-"):
        SECRET_KEY = secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://smartstock:change_me@localhost:3306/smartstock_db?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "ml" / "artifacts" / "demand_model.joblib"))
    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "12"))
