"""
聊天 API 路由层。

职责：接收 HTTP 请求 → 参数校验（Pydantic 自动完成）→ 调用 service。
本层不直接调用 LLM，也不写业务逻辑。
"""
import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    req: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """统一 Agent 入口（当前为 Mock，未来接入 SupervisorAgent）。"""
    logger.info("收到 chat 请求 | session_id=%s | message=%.50s", req.session_id, req.message)
    return await service.process_message(req.message, req.session_id)
