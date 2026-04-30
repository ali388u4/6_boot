from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    bot_token: str
    webhook_base_url: str = Field(validation_alias=AliasChoices("WEBHOOK_BASE_URL", "WEBHOOK_URL"))
    webhook_path: str = "/telegram/webhook"

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "bot"
    postgres_user: str = "bot"
    postgres_password: str = "bot"

    redis_url: str | None = Field(default=None, validation_alias=AliasChoices("REDIS_URL", "REDIS_PUBLIC_URL"))
    redis_host: str = Field(default="redis", validation_alias=AliasChoices("REDIS_HOST", "REDISHOST"))
    redis_port: int = Field(default=6379, validation_alias=AliasChoices("REDIS_PORT", "REDISPORT"))
    redis_db: int = 0
    redis_username: str | None = Field(default=None, validation_alias=AliasChoices("REDIS_USER", "REDISUSER"))
    redis_password: str | None = Field(default=None, validation_alias=AliasChoices("REDIS_PASSWORD", "REDISPASSWORD"))
    redis_ssl: bool = False

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    rate_limit_per_minute: int = 30

    admin_api_key: str | None = None

    @property
    def database_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_dsn(self) -> str:
        if self.redis_url:
            return self.redis_url.strip()
        scheme = "rediss" if self.redis_ssl else "redis"
        host = self.redis_host.strip()
        username = self.redis_username.strip() if self.redis_username else None
        password = self.redis_password.strip() if self.redis_password else None
        if username and password:
            auth = f"{username}:{password}@"
        elif password:
            auth = f":{password}@"
        else:
            auth = ""
        return f"{scheme}://{auth}{host}:{self.redis_port}/{self.redis_db}"

    @property
    def webhook_url(self) -> str:
        base = self.webhook_base_url.strip().rstrip("/")
        raw_path = self.webhook_path.strip()
        path = raw_path if raw_path.startswith("/") else f"/{raw_path}"
        return f"{base}{path}"
