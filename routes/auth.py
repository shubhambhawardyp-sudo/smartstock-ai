from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash

from models.database_models import db, User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(func.lower(User.username) == username.lower()).first() if username else None

        if user and user.is_active and check_password_hash(user.password_hash, password):
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            session.clear()
            login_user(user, remember=False, fresh=True)
            return redirect(url_for("index"))

        error = "The username or password is incorrect."

    return render_template("login.html", error=error)


@bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
