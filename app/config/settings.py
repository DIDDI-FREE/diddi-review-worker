from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    service_name: str = "diddi-review-runner"
    diddifreeid_base_url: str = "http://diddi-free-id:8000"
    diddigo_base_url: str = "http://diddi-go:8000"
    diddisend_base_url: str = "http://diddi-send:8000"
    diddifood_base_url: str = "https://diddifood-backend-staging.diddifree.com"
    redis_url: str = "redis://redis:6379/0"
    stream_name: str = "diddi-review-runs"
    database_url: str = "postgresql+asyncpg://runner:runner@postgres:5432/review_runner"
    diddifreeid_issuer: str = "https://identity.example.test"
    diddifreeid_audience: str = "diddi-services"
    diddifreeid_jwks_url: str = "http://diddi-free-id:8000/.well-known/jwks.json"
    jwt_algorithms: str = "RS256"
    http_timeout_seconds: float = 15.0
    review_accounts_json: str = "[]"
    diddigo_passenger_user_id: str = ""
    diddigo_passenger_email: str = ""
    diddigo_passenger_otp: str = ""
    diddigo_driver_user_id: str = ""
    diddigo_driver_email: str = ""
    diddigo_driver_otp: str = ""
    reactive_enabled: bool = False
    reactive_poll_interval_seconds: float = 3.0
    # Default pickup/dropoff used when the runner (as the review client) creates a
    # request after a professional goes online. Defaults sit in Abidjan.
    request_pickup_lat: float = 5.3599
    request_pickup_lng: float = -4.0083
    request_pickup_address: str = "Plateau, Abidjan"
    request_dropoff_lat: float = 5.3760
    request_dropoff_lng: float = -3.9876
    request_dropoff_address: str = "Cocody, Abidjan"

    @property
    def algorithms(self) -> list[str]:
        return [value.strip() for value in self.jwt_algorithms.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
