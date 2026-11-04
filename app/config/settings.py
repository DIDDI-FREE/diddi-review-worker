from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    service_name: str = "diddi-review-runner"
    runner_service_token: str = "change-me"
    diddifreeid_base_url: str = "http://diddi-free-id:8000"
    diddigo_base_url: str = "http://diddi-go:8000"
    diddisend_base_url: str = "http://diddi-send:8000"
    diddifoood_base_url: str = "https://diddifood-backend-staging.diddifree.com"
    redis_url: str = "redis://redis:6379/0"
    stream_name: str = "diddi-review-runs"
    database_url: str = "postgresql+asyncpg://runner:runner@postgres:5432/review_runner"
    diddifreeid_issuer: str = "https://identity.example.test"
    diddifreeid_audience: str = "diddi-services"
    diddifreeid_jwks_url: str = "http://diddi-free-id:8000/.well-known/jwks.json"
    jwt_algorithms: str = "RS256"
    http_timeout_seconds: float = 15.0
    review_accounts_json: str = "[]"

    @property
    def algorithms(self) -> list[str]:
        return [value.strip() for value in self.jwt_algorithms.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
