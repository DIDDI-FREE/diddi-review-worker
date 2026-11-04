from dataclasses import dataclass

from redis.asyncio import Redis

from app.config.settings import Settings
from app.orchestration.stream import RedisRunStream
from app.persistence.sql import SqlEventLedger, SqlRunRepository, session_factory


@dataclass(frozen=True)
class ProductionDependencies:
    redis: Redis
    stream: RedisRunStream
    sessions: object
    runs: SqlRunRepository
    events: SqlEventLedger


def build_production_dependencies(settings: Settings) -> ProductionDependencies:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    sessions = session_factory(settings.database_url)
    return ProductionDependencies(
        redis=redis,
        stream=RedisRunStream(redis, settings.stream_name),
        sessions=sessions,
        runs=SqlRunRepository(sessions),
        events=SqlEventLedger(sessions),
    )
