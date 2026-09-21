from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Migraine Detector API"
    API_PREFIX: str = "/api"
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    DATABASE_URL: str = "sqlite:///./migraine.db"
    CORS_ORIGINS: str = "http://localhost:5174,http://127.0.0.1:5174,http://localhost:5173,http://127.0.0.1:5173"

    # --- Supabase (optional; used when DATABASE_URL points at a Supabase Postgres) ---
    SUPABASE_URL: str = ""
    SUPABASE_PROJECT_REF: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "datasets"

    DEMO_INTERVAL_SECONDS: float = 2.5
    DEFAULT_PREDICTION_WINDOW_MINUTES: int = 60

    # --- Notifications (SMS) ---
    SMS_ENABLED: bool = False
    SMS_PROVIDER: str = "mock"  # "mock" | "twilio"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    ALERT_SMS_TO: str = ""
    ALERT_SMS_LEVEL: str = "high"  # "high" | "moderate" | "all"
    SMS_MAX_SENDS: int = 5  # hard cap on real SMS sends (free-tier safety)

    # --- Dataset / exports ---
    EXPORT_MAX_ROWS: int = 10000
    DATASET_DIR: str = str(Path(__file__).resolve().parents[3] / "ml" / "datasets")
    THRESHOLDS_PATH: str = str(Path(__file__).resolve().parents[1] / "ml" / "thresholds.json")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()