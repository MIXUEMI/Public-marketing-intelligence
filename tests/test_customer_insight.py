"""
Step 4.1 CustomerInsightAgent 测试。

覆盖：注册、execute 正常返回、Mock 结果 Schema 校验、Supervisor 调用。
"""
import pytest

from app.agents.customer_insight.agent import CustomerInsightAgent
from app.agents.customer_insight.schemas import CustomerInsightResult
from app.agents.registry import get_agent
from app.agents.supervisor.agent import SupervisorAgent
from app.llm.mock import MockProvider


@pytest.fixture
def agent():
    """注入 MockProvider，强制走 Mock 兜底，保证测试确定性。"""
    return CustomerInsightAgent(llm=MockProvider(model="test"))


# 1. Agent 注册成功
def test_agent_registered():
    assert get_agent("customer_insight") is CustomerInsightAgent


# 2. execute 正常返回（扁平企业信息输入）
@pytest.mark.asyncio
async def test_execute_normal(agent):
    out = await agent.execute({
        "customer_name": "杭州XX科技有限公司",
        "industry": "新能源制造",
        "basic_info": {"scale": "中型企业", "location": "杭州"},
    })
    assert out["agent"] == "customer_insight"
    assert out["status"] == "success"


# 3. Mock 模式结果符合 Schema
@pytest.mark.asyncio
async def test_mock_result_schema(agent):
    out = await agent.execute({
        "customer_name": "杭州某制造企业",
        "industry": "制造业",
        "basic_info": {"scale": "中型企业"},
    })
    result = CustomerInsightResult.model_validate(out["result"])
    assert result.customer_profile.name
    assert result.potential_needs  # 非空
    assert result.business_opportunities  # 非空
    assert result.industry_analysis


# 4. Supervisor 调用 CustomerInsightAgent 成功
@pytest.mark.asyncio
async def test_supervisor_calls_insight():
    sup = SupervisorAgent(llm=MockProvider(model="test"))
    res = await sup.process("帮我分析一下某制造企业客户", "sess-1")
    assert res["intent"] == "customer_insight"
    assert res["results"][0]["agent"] == "customer_insight"
    assert res["results"][0]["status"] == "success"
    # 结果可被 CustomerInsightResult 校验
    CustomerInsightResult.model_validate(res["results"][0]["result"])
