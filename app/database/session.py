"""
异步会话上下文管理器。

数据库关闭时 yield None，调用方据此跳过持久化 —— 保证「数据库关闭时项目仍可运行」。
"""
from contextlib import asynccontextmanager

from app.database.connection import get_session_factory


@asynccontextmanager
async def get_session():
    """获取一个异步会话；不可用时 yield None。"""
    factory = get_session_factory()
    if factory is None:
        yield None
        return
    async with factory() as session:
        yield session
