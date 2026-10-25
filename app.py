#!/usr/bin/env python3
"""
ReconEngine — সার্চ ইঞ্জিন স্টাইলের Recon & OSINT ওয়েব অ্যাপ।
লোকাল এবং Render-এর মতো হোস্টিং, দুই জায়গাতেই চলার জন্য বানানো (app factory
pattern + env var দিয়ে কনফিগ)।

লোকালি চালানো:
    pip install -r requirements.txt
    python app.py
    -> http://127.0.0.1:5000

প্রোডাকশনে (Render/gunicorn):
    gunicorn app:app
"""

import os

from flask import Flask, jsonify, request, redirect, url_for
from werkzeug.exceptions import HTTPException
from flask_login import LoginManager

from config import Config
from extensions import db, login_manager
from models import User
from auth import auth_bp
from admin import admin_bp
from main import main_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None
        return user if user and user.is_active_user else None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(error="লগইনের মেয়াদ শেষ হয়েছে। আবার লগইন করুন।",
                           login_url=url_for("auth.login")), 401
        return redirect(url_for("auth.login", next=request.path))

    @app.errorhandler(Exception)
    def handle_error(error):
        if not request.path.startswith("/api/"):
            if isinstance(error, HTTPException):
                return error
            app.logger.exception("Page request failed")
            return "সার্ভারে সমস্যা হয়েছে। কিছুক্ষণ পরে আবার চেষ্টা করুন।", 500
        db.session.rollback()
        if isinstance(error, HTTPException):
            return jsonify(error=error.description), error.code
        app.logger.exception("API request failed")
        return jsonify(error="স্ক্যান সম্পন্ন হয়নি। কিছুক্ষণ পরে আবার চেষ্টা করুন।"), 500

    @app.get("/healthz")
    def health():
        return jsonify(status="ok", version=os.environ.get("RENDER_GIT_COMMIT", "local"))

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"ReconEngine চালু হচ্ছে... ব্রাউজারে খোলো: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

