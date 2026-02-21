import os
from dotenv import load_dotenv


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


load_dotenv(dotenv_path=os.getenv("ENV_FILE", ".env"), override=False)


class Config:
    ENVIRONMENT = (os.getenv("FLASK_ENV") or "development").strip().lower()
    DEBUG = _env_bool("FLASK_DEBUG", default=ENVIRONMENT == "development")
    TESTING = _env_bool("TESTING", default=False)

    SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = (os.getenv("DATABASE_URL") or "").strip()
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("DATABASE_URL belum diset.")

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "connect_args": {"client_encoding": "utf8"},
    }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENVIRONMENT == "production"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = ENVIRONMENT == "production"
    PREFERRED_URL_SCHEME = "https" if ENVIRONMENT == "production" else "http"
    TRUSTED_HOSTS = _env_list("TRUSTED_HOSTS") or None

    DB_CREATE_ALL_ON_STARTUP = _env_bool("DB_CREATE_ALL_ON_STARTUP", default=ENVIRONMENT != "production")
    SEED_ON_STARTUP = _env_bool("SEED_ON_STARTUP", default=ENVIRONMENT != "production")
    FAIL_FAST_ON_DB_ERROR = _env_bool("FAIL_FAST_ON_DB_ERROR", default=ENVIRONMENT == "production")

    SCHOOL_SYSTEM_URL = os.getenv("SCHOOL_SYSTEM_URL", "#")
    PPDB_SYSTEM_URL = os.getenv("PPDB_SYSTEM_URL", "https://ppdb.rqdf.co.id")
    MEDIA_UPLOAD_DIR = os.getenv("MEDIA_UPLOAD_DIR", "uploads/media")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    MEDIA_ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

    SCHOOL_NAME = os.getenv("SCHOOL_NAME", "Sekolah")
    SCHOOL_PHONE = os.getenv("SCHOOL_PHONE", "")
    SCHOOL_WHATSAPP = os.getenv("SCHOOL_WHATSAPP", "")
    SCHOOL_EMAIL = os.getenv("SCHOOL_EMAIL", "")
    SCHOOL_ADDRESS = os.getenv("SCHOOL_ADDRESS", "")
    SCHOOL_MAP_EMBED_URL = os.getenv("SCHOOL_MAP_EMBED_URL", "")

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    @classmethod
    def validate(cls) -> None:
        if cls.ENVIRONMENT != "production":
            return

        if not cls.SECRET_KEY or cls.SECRET_KEY == "replace-with-strong-secret":
            raise RuntimeError("SECRET_KEY wajib diisi dengan nilai kuat untuk production.")

        if cls.DEBUG:
            raise RuntimeError("FLASK_DEBUG harus false di production.")
