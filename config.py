import os
from dotenv import load_dotenv
from pathlib import Path

# Force load .env from multiple possible locations
BASE_DIR = Path(__file__).resolve().parent.parent  # Go up to project root

load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
load_dotenv(override=True)  # fallback

print("DEBUG: .env loaded from:", BASE_DIR / ".env")  # For debugging


class Config:
    SECRET_KEY = (
        os.getenv("SECRET_KEY")
        or "supersecretkey2026restaurantSystemChangeThisInProduction"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = (
            "postgresql://postgres:mayee@localhost:5432/restaurant_db"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email (optional for now)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")
