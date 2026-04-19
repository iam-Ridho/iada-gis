from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "IADA GIS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    GROQ_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()