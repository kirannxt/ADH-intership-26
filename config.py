import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__)).replace("\\", "/")


def _env(key, fallback):
    """Return env var value or fallback — treats empty string as missing."""
    val = os.environ.get(key, "").strip()
    return val if val else fallback


class Config:
    """Base configuration."""
    SECRET_KEY = _env("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _env(
        "DEV_DATABASE_URL",
        f"sqlite:///{BASE_DIR}/dev.db"
    )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = _env("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _env(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR}/prod.db"
    )


config = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
