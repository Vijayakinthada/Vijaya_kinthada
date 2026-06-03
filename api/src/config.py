from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg2://gentle:gentle@localhost:5432/gentle_activity"
    )
    api_prefix: str = "/api/v1"

    vitals_pulse_min: int = 50
    vitals_pulse_max: int = 120
    vitals_bp_systolic_max: int = 140
    vitals_bp_diastolic_max: int = 90

    points_per_100_steps: int = 5
    points_per_session: int = 10
    points_per_active_minutes_bucket: int = 5
    active_minutes_bucket_size: int = 15
    points_goal_met: int = 25


settings = Settings()
