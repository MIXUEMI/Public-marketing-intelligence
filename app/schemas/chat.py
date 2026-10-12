"""
聊天相关请求/响应模型（Pydantic DTO）。

API 层与 Service 层之间的数据契约，与数据库模型（app/database/schemas/）解耦。
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /chat 请求体。"""

    message: str = Field(..., min_length=1, description="用户输入的自然语言消息")
    session_id: str = Field(..., description="会话 ID，用于多轮对话上下文管理")


class ChatResponse(BaseModel):
    """POST /chat 响应体。"""

    session_id: str = Field(..., description="会话 ID（回显）")
    message: str = Field(..., description="助手回复内容（汇总文本）")
    agent: str = Field(default="supervisor", description="处理该请求的 Agent 名称")
    status: str = Field(default="success", description="处理状态：success / error")
    intent: str | None = Field(default=None, description="识别出的意图")
    results: list[dict] = Field(default_factory=list, description="各 Agent 的完整执行结果")


class HealthResponse(BaseModel):
    """GET /health 响应体。"""

    status: str = "ok"
    service: str = "corporate-agent"
    version: str


class ErrorResponse(BaseModel):
    """统一错误响应体。"""

    detail: str = Field(..., description="错误信息")
