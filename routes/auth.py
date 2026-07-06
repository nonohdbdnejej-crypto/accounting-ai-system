"""مسارات المصادقة (Login / Logout)"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, UserMixin
from models.users import verify_user, get_user

auth_bp = Blueprint("auth", __name__)


class User(UserMixin):
    def __init__(self, row):
        self.id = str(row["id"])
        self.email = row["email"]
        self.full_name = row.get("full_name")
        self.role = row.get("role")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user_row = verify_user(email, password)
        if user_row:
            login_user(User(user_row))
            return redirect(url_for("main.dashboard"))
        flash("البريد الإلكتروني أو كلمة المرور غير صحيحة", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
