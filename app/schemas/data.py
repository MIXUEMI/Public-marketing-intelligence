"""
数据查询响应模型（供前端读取业务数据与运行记录）。

与 ORM 模型（app/database/models.py）解耦，只暴露前端需要的字段。
"""
from pydantic import BaseModel


class CustomerOut(BaseModel):
    """客户列表项。"""

    id: int
    name: str
    industry: str | None = None
    scale: str | None = None
    location: str | None = None
    basic_info: dict | None = None
    created_at: str | None = None


class RecommendationOut(BaseModel):
    """推荐记录列表项。"""

    id: int
    session_id: str
    customer_id: int | None = None
    customer_name: str | None = None
    products: list | dict | None = None
    reason: str | None = None
    created_at: str | None = None


class ExecutionOut(BaseModel):
    """Agent 执行记录列表项。"""

    id: int
    session_id: str
    agent_name: str
    input_data: dict | None = None
    output_data: dict | None = None
    status: str
    duration_ms: int | None = None
    created_at: str | None = None


class MessageOut(BaseModel):
    """会话消息列表项。"""

    id: int
    session_id: str
    role: str
    content: str
    intent: str | None = None
    created_at: str | None = None
