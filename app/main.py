"""
应用入口。

职责（仅此而已）：
  1. 创建 FastAPI 实例
  2. 注册路由
  3. 初始化配置与日志
不承载任何业务逻辑。
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import chat, data
from app.core.config import settings
from app.core.logging import setup_logging
from app.schemas.chat import HealthResponse

# 初始化日志（在任何请求处理前完成）
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="对公营销智能体 —— 面向银行对公客户经理的 Multi-Agent 助手",
)

# 注册路由：聊天（Agent 统一入口）+ 数据查询（前端工作台）
app.include_router(chat.router)
app.include_router(data.router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """服务健康检查。"""
    return HealthResponse(status="ok", service="corporate-agent", version=settings.app_version)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底异常处理：统一返回 500 JSON，避免向客户端泄露堆栈细节。"""
    logger.exception("未处理异常 | path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})
