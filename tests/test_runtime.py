from app.config.settings import Settings
from app.runtime import build_production_dependencies


def test_production_dependencies_use_runner_redis_and_database_urls():
    dependencies = build_production_dependencies(
        Settings(redis_url="redis://runner-redis:6379/2", database_url="postgresql+asyncpg://runner:runner@runner-db/review_runner", stream_name="review-events")
    )
    assert dependencies.stream.stream_name == "review-events"
    assert str(dependencies.redis.connection_pool.connection_kwargs["host"]) == "runner-redis"
    assert dependencies.sessions is not None
