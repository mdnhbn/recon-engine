from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import User, ScanHistory, Settings

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "total_users": User.query.count(),
        "total_scans": ScanHistory.query.count(),
        "scans_today": ScanHistory.query.filter(
            ScanHistory.created_at >= __import__("datetime").datetime.utcnow()
            - __import__("datetime").timedelta(hours=24)
        ).count(),
    }
    recent_scans = ScanHistory.query.order_by(ScanHistory.created_at.desc()).limit(15).all()
    return render_template("admin/dashboard.html", stats=stats, recent_scans=recent_scans)


@admin_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("নিজের admin status বদলাতে পারবে না।", "error")
        return redirect(url_for("admin.users"))
    user.is_admin = not user.is_admin
    db.session.commit()
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("নিজেকে ব্লক করতে পারবে না।", "error")
        return redirect(url_for("admin.users"))
    user.is_active_user = not user.is_active_user
    db.session.commit()
    return redirect(url_for("admin.users"))


@admin_bp.route("/scans")
@admin_required
def scans():
    all_scans = ScanHistory.query.order_by(ScanHistory.created_at.desc()).limit(200).all()
    return render_template("admin/scans.html", scans=all_scans)


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    settings_obj = Settings.get()

    if request.method == "POST":
        settings_obj.shodan_api_key = request.form.get("shodan_api_key", "").strip() or None
        settings_obj.censys_api_id = request.form.get("censys_api_id", "").strip() or None
        settings_obj.censys_api_secret = request.form.get("censys_api_secret", "").strip() or None
        try:
            settings_obj.daily_scan_limit = int(request.form.get("daily_scan_limit", 10))
        except ValueError:
            settings_obj.daily_scan_limit = 10
        settings_obj.ad_snippet = request.form.get("ad_snippet", "").strip() or None

        db.session.commit()
        flash("সেটিংস সেভ হয়েছে।", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", settings=settings_obj)

