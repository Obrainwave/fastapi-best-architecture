from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "BookRoma"
    APP_ENV: str = "local"
    APP_DEBUG: bool = True
    APP_TIMEZONE: str = "Africa/Lagos"
    APP_LOCALE: str = "en"

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    APP_ENCRYPTION_KEY: str
    
    PAYMENT_CALLBACK_URL: str
    
    
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    LOCAL_STORAGE_ROOT: str = "./media"
    LOCAL_STORAGE_BASE_URL: str = "http://localhost:8000/media"

    S3_BUCKET: str | None = None
    S3_REGION: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_ENDPOINT_URL: str | None = None  # set this for R2, Backblaze, or MinIO

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    STREAM_TOKEN_SECRET: str
    STREAM_TOKEN_TTL_SECONDS: int = 6 * 60 * 60   # 6 hours, covers a full viewing session including pauses
    SEGMENT_URL_TTL_SECONDS: int = 600             # 10 minutes, reissued on every playlist fetch

    DEFAULT_RENTAL_DAYS: int = 3
    DEFAULT_EXTENSION_DAYS: int = 2

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Settings()