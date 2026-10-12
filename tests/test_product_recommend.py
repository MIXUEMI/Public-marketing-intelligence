"""
Step 4.2 ProductRecommendAgent 测试。

覆盖：注册、Mock 产品搜索、execute Schema、Supervisor 多 Agent 调用。
"""
import pytest

from app.agents.product_recommend.agent import ProductRecommendAgent
from app.agents.product_recommend.schemas import ProductRecommendResult
from app.agents.registry import get_agent
from app.agents.supervisor.agent import SupervisorAgent
from app.llm.mock import MockProvider
from app.tools.product_search import search_products


@pytest.fixture
def agent():
    return ProductRecommendAgent(llm=MockProvider(model="test"))


# 1. Agent 注册成功
def test_agent_registered():
    assert get_agent("product_recommend") is ProductRecommendAgent


# 2. Mock 产品搜索正常
@pytest.mark.asyncio
async def test_search_products():
    products = await search_products("流动资金")
    assert products
    assert products[0]["name"] == "流动资金贷款"

    products2 = await search_products("供应链")
    assert any(p["name"] == "供应链金融" for p in products2)


# 3. execute 返回正确 Schema
@pytest.mark.asyncio
async def test_execute_schema(agent):
    out = await agent.execute({
        "customer_insight": {
            "customer_profile": {"name": "杭州某制造企业", "industry": "新能源制造",
                                 "scale": "中型企业", "description": "..."},
            "potential_needs": [
                {"need": "流动资金贷款", "reason": "..."},
                {"need": "设备融资", "reason": "..."},
            ],
            "business_opportunities": [{"opportunity": "绿色金融", "recommendation": "..."}],
        }
    })
    assert out["status"] == "success"
    result = ProductRecommendResult.model_validate(out["result"])
    assert result.recommended_products


# 4. Supervisor 多 Agent 调用成功（multi_task → 洞察 + 推荐）
@pytest.mark.asyncio
async def test_supervisor_multi_agent():
    sup = SupervisorAgent(llm=MockProvider(model="test"))
    res = await sup.process("分析某制造企业并推荐适合产品", "sess-1")
    assert res["intent"] == "multi_task"
    by_agent = {r["agent"]: r["status"] for r in res["results"]}
    assert by_agent["customer_insight"] == "success"
    assert by_agent["product_recommend"] == "success"
