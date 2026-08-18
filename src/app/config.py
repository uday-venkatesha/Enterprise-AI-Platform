from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Enterprise AI Platform"
    environment: str = "development"
    debug: bool = True

    # NEW. The "+asyncpg" part tells SQLAlchemy to use the async driver.
    # This default points at the Postgres CONTAINER via the host port you
    # remapped (5433). It's the URL used when you run the app locally with
    # uvicorn. When the app runs INSIDE docker-compose we override this with
    # an env var pointing at "db:5432" (see the compose change below) —
    # that host-vs-container distinction from Phase 1, made concrete.
    database_url: str = "postgresql+asyncpg://appuser:devpassword@localhost:5433/enterprise_ai"
    # NEW. The secret used to SIGN tokens. Anyone who has it can forge valid
    # tokens, so it must be long, random, and secret. This default is a
    # placeholder for local dev ONLY — real value comes from the environment.
    secret_key: str = "dev-only-change-me"
    # The signing algorithm. HS256 = symmetric (same secret signs and verifies).
    algorithm: str = "HS256"
    # How long a token stays valid. Short-lived tokens limit the damage if one
    # ever leaks.
    access_token_expire_minutes: int = 30

    # --- MinIO / object storage (NEW) ---
    # boto3 talks to THIS address. Locally it's MinIO on 9000. In docker-compose
    # the app reaches it by service name (see the compose env override below).
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "documents"          # the one bucket we store docs in
    # Reject uploads larger than this (bytes). 25 MB is a sane starting cap.
    max_upload_size: int = 25 * 1024 * 1024

    # --- Celery / Redis (NEW) ---
    # Where Celery finds the broker (the job queue). localhost when running the
    # worker on your Mac; overridden to redis://redis:6379 inside docker-compose.
    celery_broker_url: str = "redis://localhost:6379/0"
    # Where task results are stored (Celery can save return values). Same Redis,
    # a different logical database (/1 vs /0) to keep them tidy.
    celery_result_backend: str = "redis://localhost:6379/1"

    # --- OpenAI (NEW) ---
    # API key for OpenAI — read from OPENAI_API_KEY env var / .env file.
    # No default: if this is missing the app should fail loudly at startup.
    openai_api_key: str
    # Which embedding model to use. text-embedding-3-small is fast and cheap;
    # its output dimension is 1536, matching the Vector(1536) column on chunks.
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-5-mini"

settings = Settings()