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

from flask import Flask
from flask_login import LoginManager

from config import Config
from extensions import db, login_manager
from models import User
from auth import auth_bp
from admin import admin_bp
from main import main_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

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

