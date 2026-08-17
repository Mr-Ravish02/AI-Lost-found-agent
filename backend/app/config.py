import os
import pathlib

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        pass


try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        class BaseSettings:
            pass


# Determine base directories
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)

# Load .env file from root or backend directory if it exists
for env_path in [os.path.join(ROOT_DIR, '.env'), os.path.join(BACKEND_DIR, '.env')]:
    if os.path.exists(env_path):
        load_dotenv(env_path)


def resolve_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        default_db_path = os.path.join(BACKEND_DIR, "smart_lost_found.db")
        return f"sqlite:///{pathlib.Path(default_db_path).as_posix()}"

    # If SQLite relative URL is provided (e.g. sqlite:///./smart_lost_found.db or sqlite:///smart_lost_found.db)
    if raw_url.startswith("sqlite:///"):
        sqlite_path = raw_url[len("sqlite:///"):]
        if sqlite_path.startswith("./"):
            sqlite_path = sqlite_path[2:]
        # If it's a relative path (not Windows drive like C: and not Unix /)
        if not (os.path.isabs(sqlite_path) or (len(sqlite_path) > 1 and sqlite_path[1] == ":")):
            abs_db_path = os.path.join(BACKEND_DIR, sqlite_path)
            return f"sqlite:///{pathlib.Path(abs_db_path).as_posix()}"
    return raw_url


def resolve_upload_dir() -> str:
    raw_upload = os.getenv("UPLOAD_DIR", "uploads")
    if not os.path.isabs(raw_upload):
        return os.path.join(BACKEND_DIR, raw_upload)
    return raw_upload


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Smart Lost & Found Management System"
    BACKEND_DIR: str = BACKEND_DIR
    ROOT_DIR: str = ROOT_DIR
    DATABASE_URL: str = resolve_database_url()
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production-lost-and-found-2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    WATSONX_API_KEY: str = os.getenv("WATSONX_API_KEY", "")
    WATSONX_PROJECT_ID: str = os.getenv("WATSONX_PROJECT_ID", "")
    WATSONX_URL: str = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    # Uploads
    UPLOAD_DIR: str = resolve_upload_dir()

    class Config:
        case_sensitive = True


settings = Settings()

