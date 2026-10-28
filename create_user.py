"""Create a SmartStock account without storing or printing the password.

Run from the project folder with the virtual environment active:
    python create_user.py
"""
from getpass import getpass

from sqlalchemy import func, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from app import create_app
from models.database_models import db, User


def prepare_user_table():
    """Create missing app tables and add login fields to older users tables."""
    db.create_all()
    columns = {column["name"] for column in inspect(db.engine).get_columns(User.__tablename__)}
    missing = {
        "is_active": "BOOLEAN NOT NULL DEFAULT TRUE",
        "created_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "last_login_at": "DATETIME NULL",
    }
    for name, definition in missing.items():
        if name not in columns:
            with db.engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))


def main():
    app = create_app()
    with app.app_context():
        try:
            prepare_user_table()
        except SQLAlchemyError as exc:
            db.session.rollback()
            original = str(getattr(exc, "orig", exc)).lower()
            if "unknown database" in original:
                message = "Database smartstock_db was not found. Run schema.sql in MySQL Workbench first."
            elif "access denied" in original or "authentication" in original:
                message = "MySQL rejected the DATABASE_URL credentials. Use the same account that connects in MySQL Workbench."
            else:
                message = "Could not prepare the MySQL users table. Check DATABASE_URL, MySQL service status, and the application database permissions."
            raise SystemExit(message) from None

        username = input("Username: ").strip()
        if not username or len(username) > 80:
            raise SystemExit("Username must contain 1 to 80 characters.")
        if User.query.filter(func.lower(User.username) == username.lower()).first():
            raise SystemExit("That username already exists.")

        password = getpass("Password (at least 12 characters): ")
        confirmation = getpass("Confirm password: ")
        if len(password) < 12:
            raise SystemExit("Password must contain at least 12 characters.")
        if password != confirmation:
            raise SystemExit("The passwords did not match.")

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role="admin",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        print(f"Account {username!r} created. Open http://127.0.0.1:5000/login to sign in.")


if __name__ == "__main__":
    main()
