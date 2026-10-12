"""
Step 4.3 MarketingAgent 测试。

覆盖：注册、Mock 输出、Schema 验证、Supervisor 三 Agent 链路。
"""
import pytest

from app.agents.marketing.agent import MarketingAgent
from app.agents.marketing.schemas import MarketingResult
from app.agents.registry import get_agent
from app.agents.supervisor.agent import SupervisorAgent
from app.llm.mock import MockProvider


@pytest.fixture
def agent():
    return MarketingAgent(llm=MockProvider(model="test"))


# 1. Agent 注册
def test_agent_registered():
    assert get_agent("marketing") is MarketingAgent


# 2. Mock 输出（含客户名与产品名）
@pytest.mark.asyncio
async def test_mock_output(agent):
    out = await agent.execute({
        "customer_insight": {
            "customer_profile": {"name": "杭州某制造企业", "industry": "新能源制造",
                                 "scale": "中型企业", "description": "..."},
        },
        "product_recommend": {
            "recommended_products": [
                {"name": "流动资金贷款", "reason": "...", "condition": "...", "marketing_point": "..."},
            ],
        },
    })
    assert out["status"] == "success"
    assert "流动资金贷款" in out["result"]["content"]
    assert "杭州某制造企业" in out["result"]["content"]


# 3. Schema 验证
@pytest.mark.asyncio
async def test_schema(agent):
    out = await agent.execute({
        "customer_insight": {"customer_profile": {"name": "x", "industry": "制造业", "scale": "中", "description": ""}},
        "product_recommend": {"recommended_products": [{"name": "流动资金贷款", "reason": "", "condition": "", "marketing_point": ""}]},
    })
    result = MarketingResult.model_validate(out["result"])
    assert result.content
    assert result.sections.visit_plan
    assert result.sections.opening_script
    assert result.sections.need_questions
    assert result.sections.product_intro
    assert result.sections.follow_up


# 4. Supervisor 三 Agent 链路（洞察 → 推荐 → 话术 全部 success）
@pytest.mark.asyncio
async def test_supervisor_three_agents():
    sup = SupervisorAgent(llm=MockProvider(model="test"))
    res = await sup.process("分析某制造企业，并推荐产品，生成拜访方案", "sess-1")
    assert res["intent"] == "multi_task"
    by_agent = {r["agent"]: r["status"] for r in res["results"]}
    assert by_agent == {
        "customer_insight": "success",
        "product_recommend": "success",
        "marketing": "success",
    }
