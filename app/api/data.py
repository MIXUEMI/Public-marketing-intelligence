"""
数据查询 API 路由层（供前端工作台读取业务数据与运行记录）。

职责：接收 HTTP 请求 → 调用 Repository 读取 → 返回结构化结果。
本层不写业务逻辑，只做数据透传与参数限制。
"""
import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_conversation_repo,
    get_customer_repo,
    get_execution_repo,
    get_recommendation_repo,
)
from app.repositories.conversation import ConversationRepository
from app.repositories.customer import CustomerRepository
from app.repositories.execution import ExecutionRepository
from app.repositories.recommendation import RecommendationRepository
from app.schemas.data import CustomerOut, ExecutionOut, MessageOut, RecommendationOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["data"])


@router.get("/customers", response_model=list[CustomerOut])
async def list_customers(
    limit: int = Query(100, ge=1, le=500),
    repo: CustomerRepository = Depends(get_customer_repo),
) -> list[CustomerOut]:
    """客户洞察中心：列出客户及其洞察结果。"""
    return await repo.list_customers(limit=limit)


@router.get("/recommendations", response_model=list[RecommendationOut])
async def list_recommendations(
    limit: int = Query(100, ge=1, le=500),
    repo: RecommendationRepository = Depends(get_recommendation_repo),
) -> list[RecommendationOut]:
    """推荐记录中心：列出推荐记录（关联客户名称）。"""
    return await repo.list_recommendations(limit=limit)


@router.get("/executions", response_model=list[ExecutionOut])
async def list_executions(
    limit: int = Query(100, ge=1, le=500),
    repo: ExecutionRepository = Depends(get_execution_repo),
) -> list[ExecutionOut]:
    """运行监控：列出最近 Agent 执行记录（全量）。"""
    return await repo.list_executions(limit=limit)


@router.get("/executions/{session_id}", response_model=list[ExecutionOut])
async def list_executions_by_session(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    repo: ExecutionRepository = Depends(get_execution_repo),
) -> list[ExecutionOut]:
    """运行监控：按会话查询 Agent 执行记录。"""
    return await repo.list_executions(session_id=session_id, limit=limit)


@router.get("/history/{session_id}", response_model=list[MessageOut])
async def get_history(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    repo: ConversationRepository = Depends(get_conversation_repo),
) -> list[MessageOut]:
    """对话历史：查询某个会话的消息记录。"""
    return await repo.get_history(session_id, limit=limit)
