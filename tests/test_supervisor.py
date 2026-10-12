"""
Step 3 Supervisor Agent 与 Agent Registry 测试。

覆盖：注册中心增删查、Supervisor 初始化、意图识别（规则兜底）、端到端流程。
"""
import pytest

from app.agents.base import BaseAgent
from app.agents.registry import AGENT_REGISTRY, get_agent, list_agents, register_agent
from app.agents.schemas import IntentType
from app.agents.supervisor.agent import SupervisorAgent
from app.llm.mock import MockProvider


# ---- 测试用 Dummy Agent ----
class _DummyAgent(BaseAgent):
    name = "dummy_test"
    description = "测试用 Agent"

    async def execute(self, input_data: dict) -> dict:
        return {"agent": self.name, "status": "success", "result": {"echo": input_data}}


@pytest.fixture
def supervisor():
    """注入 MockProvider，强制走规则兜底，保证测试确定性（不依赖外部 Key）。"""
    return SupervisorAgent(llm=MockProvider(model="test"))


# 1. Agent Registry 注册 / 获取 / 列表
def test_registry_register_get_list():
    register_agent(_DummyAgent)
    try:
        assert get_agent("dummy_test") is _DummyAgent
        assert "dummy_test" in list_agents()
    finally:
        # 清理，避免污染其它测试
        AGENT_REGISTRY.pop("dummy_test", None)


def test_registry_get_missing():
    assert get_agent("no_such_agent") is None


# 2. Supervisor 初始化
def test_supervisor_init(supervisor):
    assert supervisor.name == "supervisor"
    assert supervisor.llm is not None


# 3. 意图识别（规则兜底，确定性）
@pytest.mark.asyncio
async def test_intent_customer_insight(supervisor):
    assert await supervisor.detect_intent("帮我分析一下某制造企业客户") == IntentType.CUSTOMER_INSIGHT


@pytest.mark.asyncio
async def test_intent_product_recommend(supervisor):
    assert await supervisor.detect_intent("推荐适合这个企业的贷款产品") == IntentType.PRODUCT_RECOMMEND


@pytest.mark.asyncio
async def test_intent_multi_task(supervisor):
    assert await supervisor.detect_intent("分析客户并生成拜访方案") == IntentType.MULTI_TASK


# 4. 端到端流程：customer_insight 已注册，应返回 success
@pytest.mark.asyncio
async def test_process_end_to_end(supervisor):
    result = await supervisor.process("帮我分析一下某制造企业客户", "sess-1")
    assert result["intent"] == "customer_insight"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    assert result["results"][0]["agent"] == "customer_insight"


# 5. 未注册 Agent 的优雅降级（executor 层）
@pytest.mark.asyncio
async def test_executor_not_registered():
    from app.agents.schemas import IntentType, Task, TaskPlan
    from app.workflow.executor import WorkflowExecutor
    from app.workflow.state import AgentState

    plan = TaskPlan(intent=IntentType.CUSTOMER_INSIGHT, tasks=[
        Task(agent_name="no_such_agent", purpose="x", input={})
    ])
    state = AgentState(message="x", intent="customer_insight")
    state = await WorkflowExecutor().execute(plan, state)
    assert state.history[0]["status"] == "not_registered"
