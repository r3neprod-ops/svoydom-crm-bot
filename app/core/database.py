from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


_ASYNC_PG_URL_QUERY_KEYS = {"ssl", "sslmode", "target_session_attrs"}
_SSL_REQUIRED_VALUES = {"1", "true", "yes", "require", "verify-ca", "verify-full"}


def database_url_without_asyncpg_ssl_query(database_url: str) -> str:
    parts = urlsplit(database_url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _ASYNC_PG_URL_QUERY_KEYS
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def database_ssl_enabled(settings: Settings) -> bool:
    if settings.db_ssl:
        return True

    query = parse_qsl(urlsplit(settings.database_url).query, keep_blank_values=True)
    return any(
        key.lower() in {"ssl", "sslmode"} and value.lower() in _SSL_REQUIRED_VALUES
        for key, value in query
    )


def database_connect_args(settings: Settings) -> dict[str, bool]:
    if database_ssl_enabled(settings):
        return {"ssl": True}
    return {}


def create_database_engine(settings: Settings, **engine_kwargs: Any):
    return create_async_engine(
        database_url_without_asyncpg_ssl_query(settings.database_url),
        pool_pre_ping=True,
        connect_args=database_connect_args(settings),
        **engine_kwargs,
    )


settings = get_settings()
engine = create_database_engine(settings)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
