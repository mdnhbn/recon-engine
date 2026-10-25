import os


def _fix_postgres_url(url: str) -> str:
    # Render/Heroku কখনো postgres:// দেয়, SQLAlchemy চায় postgresql://
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-this-in-production")
    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(
        os.environ.get("DATABASE_URL", "sqlite:///recon.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_DAILY_SCAN_LIMIT = int(os.environ.get("DEFAULT_DAILY_SCAN_LIMIT", "10"))

