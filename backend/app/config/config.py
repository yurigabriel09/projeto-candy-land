import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOW_DUPLICATE_PHONE = (
        os.getenv("ALLOW_DUPLICATE_PHONE", "false").strip().lower()
        in ("true", "1", "yes", "on")
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-troque-em-producao")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    GOOGLE_CLOCK_SKEW_SECONDS = int(os.getenv("GOOGLE_CLOCK_SKEW_SECONDS", "300"))

    UPLOAD_FOLDER = BASE_DIR / "uploads"
    UPLOAD_MAX_BYTES = 2 * 1024 * 1024
    # Limite duro da requisição (folga para o overhead do multipart)
    MAX_CONTENT_LENGTH = UPLOAD_MAX_BYTES + 512 * 1024
