# app/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

# Determine base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent
# load environment variables from .env at project root
load_dotenv(BASE_DIR / ".env")

# ensure instance folder exists
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    # Secret keys
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)

    # Database configuration
    # Allow DATABASE_URL override; default to SQLite in instance/app.db
    _db_url = os.getenv("DATABASE_URL") or f"sqlite:///{INSTANCE_DIR / 'app.db'}"
    if _db_url.startswith("sqlite:///"):
        # strip the prefix and make path absolute
        rel_path = _db_url.replace("sqlite:///", "")
        abs_path = (BASE_DIR / rel_path).resolve()
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{abs_path}"
    else:
        SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail settings
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.example.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")

    # External API keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ADMIN_SECRET_CODE = os.getenv("ADMIN_SECRET_CODE", "")