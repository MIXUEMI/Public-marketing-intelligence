"""
RecommendationRepository：推荐记录持久化。
"""
import logging

from sqlalchemy import select

from app.database.models import Customer, Recommendation
from app.database.session import get_session

logger = logging.getLogger(__name__)


class RecommendationRepository:
    """推荐记录数据访问层。"""

    async def save(
        self,
        session_id: str,
        customer_id: int | None = None,
        products: list | dict | None = None,
        reason: str | None = None,
        agent_trace: dict | None = None,
    ) -> int | None:
        """保存一次推荐记录，返回 recommendation.id。"""
        async with get_session() as session:
            if session is None:
                return None
            r = Recommendation(
                session_id=session_id,
                customer_id=customer_id,
                products=products,
                reason=reason,
                agent_trace=agent_trace,
            )
            session.add(r)
            await session.commit()
            await session.refresh(r)
            return r.id

    async def list_recommendations(self, limit: int = 100) -> list[dict]:
        """列出最近推荐记录（关联客户名称）。数据库关闭时返回空列表。"""
        async with get_session() as session:
            if session is None:
                return []
            result = await session.execute(
                select(Recommendation, Customer.name)
                .join(Customer, Recommendation.customer_id == Customer.id, isouter=True)
                .order_by(Recommendation.id.desc())
                .limit(limit)
            )
            return [
                {
                    "id": r.id,
                    "session_id": r.session_id,
                    "customer_id": r.customer_id,
                    "customer_name": customer_name,
                    "products": r.products,
                    "reason": r.reason,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r, customer_name in result.all()
            ]
