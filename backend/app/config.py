from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./veriq.db"
    storage_dir: str = "./storage"
    max_upload_mb: int = 10
    demo_mode: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
