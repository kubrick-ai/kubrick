import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # TwelveLabs API
    TWELVELABS_API_KEY = os.getenv("TWELVELABS_API_KEY", "")

    # Database configuration
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DATABASE_URL = os.getenv(
        "DATABASE_URL", f"postgresql://postgres@localhost/{DATABASE_NAME}"
    )

    # Default embedding parameters
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "Marengo-retrieval-2.7")
    DEFAULT_CLIP_LENGTH = int(os.getenv("DEFAULT_CLIP_LENGTH", 6))

    # Default search parameters
    DEFAULT_PAGE_LIMIT = int(os.getenv("DEFAULT_PAGE_LIMIT", 5))
    DEFAULT_MIN_SIMILARITY = float(os.getenv("DEFAULT_MIN_SIMILARITY", 0.2))

    # Legacy database connection parameters (for backward compatibility)
    DB_PARAMS = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "postgres"),
        "database": DATABASE_NAME,
    }

    # Server configuration
    PORT = int(os.getenv("PORT", 5003))
    HOST = os.getenv("HOST", "127.0.0.1")

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DATABASE_NAME = "kubrick_test"
    DB_PARAMS = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "database": "kubrick_test",
    }


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
