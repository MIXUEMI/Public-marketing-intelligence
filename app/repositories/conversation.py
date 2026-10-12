"""
ConversationRepository：会话与消息持久化。
"""
import logging

from sqlalchemy import select

from app.database.models import Message, Session
from app.database.session import get_session

logger = logging.getLogger(__name__)


class ConversationRepository:
    """会话与消息数据访问层。"""

    async def create_session(self, session_id: str, user_id: str | None = None) -> int | None:
        """创建会话（幂等：已存在则直接返回其 id）。"""
        async with get_session() as session:
            if session is None:
                return None
            result = await session.execute(select(Session).where(Session.session_id == session_id))
            existing = result.scalar_one_or_none()
            if existing:
                return existing.id

            s = Session(session_id=session_id, user_id=user_id)
            session.add(s)
            await session.commit()
            await session.refresh(s)
            return s.id

    async def save_message(
        self, session_id: str, role: str, content: str, intent: str | None = None
    ) -> int | None:
        """保存一条对话消息，返回 message.id。"""
        async with get_session() as session:
            if session is None:
                return None
            m = Message(session_id=session_id, role=role, content=content, intent=intent)
            session.add(m)
            await session.commit()
            await session.refresh(m)
            return m.id

    async def get_history(self, session_id: str, limit: int = 100) -> list[dict]:
        """查询某个会话的消息历史（按时间正序）。数据库关闭时返回空列表。"""
        async with get_session() as session:
            if session is None:
                return []
            result = await session.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.id.asc())
                .limit(limit)
            )
            return [
                {
                    "id": m.id,
                    "session_id": m.session_id,
                    "role": m.role,
                    "content": m.content,
                    "intent": m.intent,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in result.scalars().all()
            ]
