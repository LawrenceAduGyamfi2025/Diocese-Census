from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root directory resolution using pathlib
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Diocese Census GH"
    ENVIRONMENT: str = "dev"
    
    # Pathlib ensures these strings work across OS boundaries
    DB_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'census.db'}"
    SECRET_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
