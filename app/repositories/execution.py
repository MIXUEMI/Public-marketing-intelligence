"""
ExecutionRepository + Agent 执行记录 Hook。

WorkflowExecutor 通过 create_execution_record() / update_execution_record()
在 Agent 执行前后落库（Middleware 机制），不侵入 Agent 代码。
"""
import logging

from sqlalchemy import select

from app.database.models import AgentExecution
from app.database.session import get_session

logger = logging.getLogger(__name__)


class ExecutionRepository:
    """Agent 执行记录数据访问层。"""

    async def create(self, session_id: str, agent_name: str, input_data: dict) -> int | None:
        """执行前：写入一条 status=running 的记录，返回 execution.id。"""
        async with get_session() as session:
            if session is None:
                return None
            e = AgentExecution(
                session_id=session_id or "",
                agent_name=agent_name,
                input_data=input_data,
                status="running",
            )
            session.add(e)
            await session.commit()
            await session.refresh(e)
            return e.id

    async def update(
        self,
        execution_id: int | None,
        output_data: dict | None = None,
        status: str = "success",
        duration_ms: int | None = None,
    ) -> None:
        """执行后：更新 output/status/duration。"""
        async with get_session() as session:
            if session is None or execution_id is None:
                return
            e = await session.get(AgentExecution, execution_id)
            if e is not None:
                e.output_data = output_data
                e.status = status
                e.duration_ms = duration_ms
                await session.commit()

    async def list_executions(self, session_id: str | None = None, limit: int = 100) -> list[dict]:
        """列出 Agent 执行记录；可按 session 过滤，默认返回最近记录。数据库关闭时返回空列表。"""
        async with get_session() as session:
            if session is None:
                return []
            if session_id:
                stmt = (
                    select(AgentExecution)
                    .where(AgentExecution.session_id == session_id)
                    .order_by(AgentExecution.id.asc())
                    .limit(limit)
                )
            else:
                stmt = select(AgentExecution).order_by(AgentExecution.id.desc()).limit(limit)
            result = await session.execute(stmt)
            return [
                {
                    "id": e.id,
                    "session_id": e.session_id,
                    "agent_name": e.agent_name,
                    "input_data": e.input_data,
                    "output_data": e.output_data,
                    "status": e.status,
                    "duration_ms": e.duration_ms,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in result.scalars().all()
            ]


_execution_repo = ExecutionRepository()


async def create_execution_record(session_id: str, agent_name: str, input_data: dict) -> int | None:
    """Hook：Agent 执行前记录，返回 execution.id（数据库关闭时返回 None）。"""
    return await _execution_repo.create(session_id, agent_name, input_data)


async def update_execution_record(
    execution_id: int | None,
    output_data: dict | None = None,
    status: str = "success",
    duration_ms: int | None = None,
) -> None:
    """Hook：Agent 执行后更新记录。"""
    await _execution_repo.update(execution_id, output_data, status, duration_ms)
