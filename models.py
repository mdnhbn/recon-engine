import json
from datetime import datetime, timedelta

from flask_login import UserMixin
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scans = db.relationship("ScanHistory", backref="user", lazy="dynamic")

    def set_password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        return self.is_active_user

    def scans_today_count(self) -> int:
        since = datetime.utcnow() - timedelta(hours=24)
        return self.scans.filter(ScanHistory.created_at >= since).count()


class ScanHistory(db.Model):
    __tablename__ = "scan_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target = db.Column(db.String(255), nullable=False)
    subdomain_count = db.Column(db.Integer, default=0)
    live_host_count = db.Column(db.Integer, default=0)
    result_json = db.Column(db.Text)  # পুরো রেজাল্ট JSON আকারে
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def result(self):
        try:
            return json.loads(self.result_json)
        except Exception:
            return {}


class Settings(db.Model):
    """একটামাত্র সিঙ্গেলটন row — সাইটের গ্লোবাল সেটিংস রাখে।"""
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    shodan_api_key = db.Column(db.String(255))
    censys_api_id = db.Column(db.String(255))
    censys_api_secret = db.Column(db.String(255))
    daily_scan_limit = db.Column(db.Integer, default=10)
    ad_snippet = db.Column(db.Text)  # AdSense বা যেকোনো অ্যাড HTML/JS কোড

    @staticmethod
    def get():
        settings = Settings.query.first()
        if not settings:
            settings = Settings(daily_scan_limit=current_app.config["DEFAULT_DAILY_SCAN_LIMIT"])
            db.session.add(settings)
            db.session.commit()
        return settings

