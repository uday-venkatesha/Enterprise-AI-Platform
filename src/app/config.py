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


settings = Settings()