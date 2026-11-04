FROM python:3.12-slim
WORKDIR /app
# Make the `app` package importable by both alembic (run as a CLI) and uvicorn.
ENV PYTHONPATH=/app
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    fastapi httpx pydantic-settings 'PyJWT[crypto]' 'uvicorn[standard]' redis \
    'SQLAlchemy[asyncio]' asyncpg alembic
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh
EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
