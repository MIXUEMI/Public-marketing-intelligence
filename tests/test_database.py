"""
Step 7 数据库落地测试。

用 SQLite（aiosqlite）+ override_session_factory 注入，无需真实 PostgreSQL。
覆盖：模型创建 / Session 保存 / Message 保存 / Agent 执行记录保存 / Recommendation 保存。
"""
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.connection import override_session_factory, reset_session_factory
from app.database.models import Base
from app.repositories.conversation import ConversationRepository
from app.repositories.customer import CustomerRepository
from app.repositories.execution import ExecutionRepository
from app.repositories.recommendation import RecommendationRepository


@pytest.fixture
async def db(tmp_path):
    """注入 SQLite 异步 SessionFactory，测试结束释放。"""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    override_session_factory(factory)
    yield factory
    reset_session_factory()
    await engine.dispose()


@pytest.mark.asyncio
async def test_models_created(db):
    """1. 数据库模型创建：5 张表齐全。"""
    expected = {"customers", "sessions", "messages", "recommendations", "agent_executions"}
    assert expected <= set(Base.metadata.tables.keys())


@pytest.mark.asyncio
async def test_session_save(db):
    """2. Session 保存。"""
    repo = ConversationRepository()
    sid = await repo.create_session("sess-001", user_id="u1")
    assert sid is not None
    # 幂等：重复创建返回同一会话
    assert await repo.create_session("sess-001", user_id="u1") == sid


@pytest.mark.asyncio
async def test_message_save(db):
    """3. Message 保存。"""
    repo = ConversationRepository()
    await repo.create_session("sess-002")
    mid = await repo.save_message("sess-002", "user", "帮我分析某制造企业", intent="customer_insight")
    assert mid is not None


@pytest.mark.asyncio
async def test_agent_execution_save(db):
    """4. Agent 执行记录保存（create → update 落 output/status/duration）。"""
    repo = ExecutionRepository()
    eid = await repo.create("sess-003", "customer_insight", {"message": "hi"})
    assert eid is not None
    await repo.update(eid, output_data={"result": "ok"}, status="success", duration_ms=12)


@pytest.mark.asyncio
async def test_recommendation_save(db):
    """5. Recommendation 保存（关联客户与会话）。"""
    conv = ConversationRepository()
    await conv.create_session("sess-004")

    customer_repo = CustomerRepository()
    cid = await customer_repo.save_customer_insight(
        {"customer_profile": {"name": "A制造公司", "industry": "制造业", "scale": "中型"}}
    )
    assert cid is not None

    rec_repo = RecommendationRepository()
    rid = await rec_repo.save(
        session_id="sess-004",
        customer_id=cid,
        products=[{"name": "流动资金贷款"}],
        reason="intent=product_recommend",
    )
    assert rid is not None
