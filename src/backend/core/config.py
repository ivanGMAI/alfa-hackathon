from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

env_files = (".env.app_config",)

BASE_DIR = Path(__file__).resolve().parent.parent

for file in env_files:
    load_dotenv(BASE_DIR / file)


class RunConfig(BaseModel):
    host: str
    port: int


class DbConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    max_overflow: int = 10
    pool_size: int = 50

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class LLMConfig(BaseModel):
    api_key: str
    api_base: str
    default_model: str
    temperature: float = 0.7
    max_tokens: int = 1024
    request_timeout: float = 30.0
    max_agent_steps: int = 6
    # RAG embeddings. mode="local" works offline (hashed); "api" calls an
    # OpenAI-compatible /embeddings endpoint with embedding_model.
    embedding_mode: str = "local"
    embedding_model: str = "text-embedding-3-small"


class CorsConfig(BaseModel):
    # Comma-separated list of allowed origins, e.g. "http://localhost,http://localhost:5173"
    allow_origins: str = "http://localhost"

    @property
    def origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.allow_origins.split(",") if origin.strip()
        ]


class SentryConfig(BaseModel):
    dsn: str = ""  # empty -> Sentry disabled


class JWTConfig(BaseModel):
    private_key_path: Path = BASE_DIR / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_lifetime_seconds: int = 1800
    refresh_token_lifetime_seconds: int = 2_592_000
    email_token_lifetime_seconds: int = 7200
    password_token_lifetime_seconds: int = 600


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    chats: str = "/chats"
    messages: str = "/messages"
    users: str = "/users"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_files,
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    environment: str = "dev"  # "dev" enables hot-reload and /docs; use "prod" otherwise
    run: RunConfig
    llm: LLMConfig
    db: DbConfig
    cors: CorsConfig = CorsConfig()
    sentry: SentryConfig = SentryConfig()
    jwt: JWTConfig = JWTConfig()
    api: ApiPrefix = ApiPrefix()


settings = Settings()
