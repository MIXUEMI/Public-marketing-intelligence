"""
Step 8 数据查询接口测试。

用 SQLite override + httpx ASGITransport 直测 FastAPI 端点，无需真实 PostgreSQL。
覆盖：GET /customers /recommendations /executions/{session_id} /history/{session_id}。
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.connection import override_session_factory, reset_session_factory
from app.database.models import Base
from app.main import app
from app.repositories.conversation import ConversationRepository
from app.repositories.customer import CustomerRepository
from app.repositories.execution import ExecutionRepository
from app.repositories.recommendation import RecommendationRepository


@pytest.fixture
async def client(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'api.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    override_session_factory(async_sessionmaker(engine, expire_on_commit=False))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    reset_session_factory()
    await engine.dispose()


async def _seed() -> None:
    """预置数据：会话 + 消息 + 客户 + 执行记录 + 推荐记录。"""
    conv = ConversationRepository()
    await conv.create_session("sess-api")
    await conv.save_message("sess-api", "user", "分析制造企业", intent="customer_insight")

    cust = CustomerRepository()
    cid = await cust.save_customer_insight(
        {"customer_profile": {"name": "A制造公司", "industry": "制造业", "scale": "中型"}}
    )

    exec_repo = ExecutionRepository()
    eid = await exec_repo.create("sess-api", "customer_insight", {"message": "x"})
    await exec_repo.update(eid, output_data={"result": "ok"}, status="success", duration_ms=5)

    rec = RecommendationRepository()
    await rec.save(
        "sess-api",
        customer_id=cid,
        products=[{"name": "流动资金贷款", "reason": "周转需求"}],
        reason="流动资金贷款: 周转需求",
    )


@pytest.mark.asyncio
async def test_customers_endpoint(client):
    await _seed()
    resp = await client.get("/customers")
    assert resp.status_code == 200
    data = resp.json()
    assert any(c["name"] == "A制造公司" for c in data)


@pytest.mark.asyncio
async def test_recommendations_endpoint(client):
    await _seed()
    resp = await client.get("/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert any(r["customer_name"] == "A制造公司" for r in data)


@pytest.mark.asyncio
async def test_executions_endpoint(client):
    await _seed()
    resp = await client.get("/executions/sess-api")
    assert resp.status_code == 200
    data = resp.json()
    assert any(e["agent_name"] == "customer_insight" for e in data)


@pytest.mark.asyncio
async def test_history_endpoint(client):
    await _seed()
    resp = await client.get("/history/sess-api")
    assert resp.status_code == 200
    data = resp.json()
    assert any(m["role"] == "user" for m in data)
