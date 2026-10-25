from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("সব ফিল্ড পূরণ করো।", "error")
            return render_template("signup.html")

        if len(username) > 80 or len(email) > 200 or "@" not in email or len(password) < 8:
            flash("সঠিক ইমেইল এবং অন্তত ৮ অক্ষরের পাসওয়ার্ড দিন।", "error")
            return render_template("signup.html"), 400

        if User.query.filter(
            (func.lower(User.username) == username.lower()) |
            (func.lower(User.email) == email.lower())
        ).first():
            flash("এই username বা email দিয়ে আগেই অ্যাকাউন্ট আছে।", "error")
            return render_template("signup.html")

        # প্রথম যে ইউজার সাইনআপ করবে, সে অটোমেটিক admin হয়ে যাবে
        is_first_user = User.query.count() == 0

        user = User(username=username, email=email, is_admin=is_first_user)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("এই username বা email দিয়ে আগেই অ্যাকাউন্ট আছে।", "error")
            return render_template("signup.html"), 409

        login_user(user)
        flash("অ্যাকাউন্ট তৈরি হয়েছে!" + (" তুমি এখন admin।" if is_first_user else ""), "success")
        return redirect(url_for("main.index"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        # Preserve existing mixed-case usernames. Never choose an arbitrary
        # account if legacy rows differ only by case.
        candidates = User.query.filter(
            (func.lower(User.username) == identifier.lower()) |
            (func.lower(User.email) == identifier.lower())
        ).all()
        if len(candidates) == 1:
            user = candidates[0]
        else:
            exact = [u for u in candidates if u.username == identifier or u.email == identifier]
            user = exact[0] if len(exact) == 1 else None

        if user and user.check_password(password) and user.is_active_user:
            login_user(user)
            return redirect(url_for("main.index"))

        flash("ভুল username/email অথবা পাসওয়ার্ড।", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

