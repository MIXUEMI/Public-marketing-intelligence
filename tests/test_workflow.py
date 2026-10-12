"""
Step 5 Workflow 链式调用测试。

覆盖：build_agent_input 输入适配、单 Agent、依赖展开、完整链路上下文传递。
"""
import pytest

from app.agents.supervisor.agent import SupervisorAgent
from app.llm.mock import MockProvider
from app.workflow.executor import build_agent_input
from app.workflow.state import AgentState


@pytest.fixture
def supervisor():
    return SupervisorAgent(llm=MockProvider(model="test"))


# 1. build_agent_input 输入适配规则（链式传参核心）
def test_build_agent_input():
    state = AgentState(
        message="分析客户并推荐产品",
        intent="multi_task",
        customer_insight={"customer_profile": {"name": "A公司", "industry": "制造"}},
    )
    # customer_insight 只拿原始消息
    assert build_agent_input("customer_insight", state) == {"message": "分析客户并推荐产品"}

    # product_recommend 拿到 customer_insight 结果
    pin = build_agent_input("product_recommend", state)
    assert pin["customer_insight"]["customer_profile"]["name"] == "A公司"

    # marketing 拿到前两个结果
    state.product_recommend = {"recommended_products": [{"name": "流动资金贷款"}]}
    minp = build_agent_input("marketing", state)
    assert minp["customer_insight"]["customer_profile"]["name"] == "A公司"
    assert minp["product_recommend"]["recommended_products"][0]["name"] == "流动资金贷款"


# 2. 客户分析 → 只执行 customer_insight
@pytest.mark.asyncio
async def test_workflow_insight_only(supervisor):
    res = await supervisor.process("分析制造企业", "sess-1")
    agents = [r["agent"] for r in res["results"]]
    assert agents == ["customer_insight"]


# 3. 产品推荐 → customer_insight + product_recommend（依赖自动展开）
@pytest.mark.asyncio
async def test_workflow_product_recommend(supervisor):
    res = await supervisor.process("分析客户并推荐产品", "sess-2")
    agents = [r["agent"] for r in res["results"]]
    assert agents == ["customer_insight", "product_recommend"]
    assert res["results"][1]["result"].get("recommended_products")


# 4. 完整链路 → 三 Agent 全 success，marketing 引用推荐产品（验证上下文传递）
@pytest.mark.asyncio
async def test_workflow_full_pipeline(supervisor):
    res = await supervisor.process("分析客户，推荐产品，生成拜访方案", "sess-3")
    agents = [r["agent"] for r in res["results"]]
    assert agents == ["customer_insight", "product_recommend", "marketing"]

    by_agent = {r["agent"]: r["status"] for r in res["results"]}
    assert by_agent == {
        "customer_insight": "success",
        "product_recommend": "success",
        "marketing": "success",
    }

    # marketing 内容引用了 product_recommend 推荐的产品名（证明上下文已传递）
    product_names = [p["name"] for p in res["results"][1]["result"]["recommended_products"]]
    marketing_content = res["results"][2]["result"]["content"]
    assert any(name in marketing_content for name in product_names)
