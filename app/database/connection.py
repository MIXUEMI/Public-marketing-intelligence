"""
数据库连接管理：异步 Engine 与 SessionFactory。

设计要点：
    - use_database=false 时 get_engine() 返回 None，整个持久化层优雅降级（项目仍可运行）
    - 提供 override_session_factory() 供测试注入 SQLite，不依赖真实 PostgreSQL
"""
import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.database.models import Base

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_factory: async_sessionmaker[AsyncSession] | None = None
_override_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine | None:
    """返回全局异步 Engine；未启用数据库时返回 None。"""
    global _engine
    if _engine is None and settings.use_database:
        _engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
        logger.info("数据库 Engine 已创建 | url=%s", settings.database_url.split("@")[-1])
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    """返回异步 SessionFactory（优先测试注入的 override）。"""
    global _factory
    if _override_factory is not None:
        return _override_factory
    if _factory is None:
        engine = get_engine()
        if engine is not None:
            _factory = async_sessionmaker(engine, expire_on_commit=False)
    return _factory


def override_session_factory(factory: async_sessionmaker[AsyncSession]) -> None:
    """测试用：注入自定义 SessionFactory（如 SQLite）。"""
    global _override_factory
    _override_factory = factory


def reset_session_factory() -> None:
    """重置 override 与全局状态（测试收尾）。"""
    global _override_factory, _engine, _factory
    _override_factory = None
    _engine = None
    _factory = None


async def init_db() -> None:
    """建表（开发/演示用；生产用 Alembic 迁移）。"""
    engine = get_engine()
    if engine is not None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表已创建")


async def close_db() -> None:
    """释放连接。"""
    global _engine, _factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _factory = None
