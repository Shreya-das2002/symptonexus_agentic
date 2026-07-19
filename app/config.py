from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SymptoNexus AI Backend"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = ""

    qwen_api_url: str = "http://qwen.msqube.in/api/chat"
    qwen_api_key: str = ""
    qwen_model: str = "qwen3.6:27b"
    qwen_timeout: int = 90

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        if not self.database_url:
            raise ValueError("DATABASE_URL is not configured")

        # The PostgreSQL URL commonly supplied by hosting providers omits the
        # SQLAlchemy driver name. Use psycopg (v3) explicitly for this app.
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)

        return self.database_url


settings = Settings()
