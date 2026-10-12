"""
CustomerRepository：客户主数据增删改查。

Agent 不直接操作数据库，统一通过 Repository 访问。
"""
import logging

from sqlalchemy import select

from app.database.models import Customer
from app.database.session import get_session

logger = logging.getLogger(__name__)


class CustomerRepository:
    """客户数据访问层。"""

    async def get_or_create(
        self,
        name: str,
        industry: str | None = None,
        scale: str | None = None,
        location: str | None = None,
        basic_info: dict | None = None,
    ) -> int | None:
        """按名称查询客户，不存在则创建，返回 customer.id（数据库关闭时返回 None）。"""
        async with get_session() as session:
            if session is None:
                return None
            result = await session.execute(select(Customer).where(Customer.name == name))
            customer = result.scalar_one_or_none()

            if customer:
                customer.industry = industry or customer.industry
                customer.scale = scale or customer.scale
                customer.location = location or customer.location
                if basic_info is not None:
                    customer.basic_info = basic_info
            else:
                customer = Customer(
                    name=name, industry=industry, scale=scale, location=location, basic_info=basic_info
                )
                session.add(customer)

            await session.commit()
            await session.refresh(customer)
            return customer.id

    async def save_customer_insight(self, insight: dict) -> int | None:
        """保存客户分析结果（CustomerInsightResult），返回 customer.id。"""
        profile = insight.get("customer_profile", {}) if isinstance(insight, dict) else {}
        name = profile.get("name") or "未知客户"
        return await self.get_or_create(
            name=name,
            industry=profile.get("industry"),
            scale=profile.get("scale"),
            location=profile.get("location"),
            basic_info=insight,
        )

    async def list_customers(self, limit: int = 100) -> list[dict]:
        """列出最近客户（含 basic_info 洞察结果）。数据库关闭时返回空列表。"""
        async with get_session() as session:
            if session is None:
                return []
            result = await session.execute(
                select(Customer).order_by(Customer.id.desc()).limit(limit)
            )
            return [self._to_dict(c) for c in result.scalars().all()]

    @staticmethod
    def _to_dict(c: Customer) -> dict:
        return {
            "id": c.id,
            "name": c.name,
            "industry": c.industry,
            "scale": c.scale,
            "location": c.location,
            "basic_info": c.basic_info,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
