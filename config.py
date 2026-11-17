from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Toute la configuration vient de l'environnement (ou d'un fichier .env en local)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Sur Scalingo, l'addon PostgreSQL fournit SCALINGO_POSTGRESQL_URL ; en local on utilise DATABASE_URL
    database_url: str | None = None
    scalingo_postgresql_url: str | None = None

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Origines autorisées pour CORS, séparées par des virgules
    cors_origins: str = ""

    @field_validator("database_url", "scalingo_postgresql_url")
    @classmethod
    def fix_postgres_scheme(cls, value: str | None) -> str | None:
        # SQLAlchemy n'accepte pas "postgres://" : on force le driver psycopg 3
        if value is None:
            return None
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @property
    def sqlalchemy_url(self) -> str:
        url = self.scalingo_postgresql_url or self.database_url
        if not url:
            raise RuntimeError("DATABASE_URL ou SCALINGO_POSTGRESQL_URL doit être défini")
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
