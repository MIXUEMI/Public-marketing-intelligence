"""
Supervisor Agent —— 系统主控。

职责：意图识别 → 动态任务规划 → 交给 WorkflowExecutor 执行 → 结果汇总。
不直接执行 Agent（执行与上下文传递由 app/workflow/executor.py 负责）。

采用 Supervisor Pattern + Agent Registry + Workflow Executor：
    - 通过 registry 动态查找 Agent
    - 动态检测用户需求，按依赖（depends_on）展开生成任务
    - 未来迁移 LangGraph 时，替换 WorkflowExecutor 即可，Supervisor 不变
"""
import logging

from app.agents.schemas import IntentType, Task, TaskPlan
from app.agents.supervisor.prompts import SUPERVISOR_SYSTEM_PROMPT
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm
from app.workflow.executor import WorkflowExecutor
from app.workflow.graph import AGENT_DEPENDENCIES
from app.workflow.state import AgentState

logger = logging.getLogger(__name__)

# 意图 -> agent 名称
_INTENT_TO_AGENT = {
    IntentType.CUSTOMER_INSIGHT: "customer_insight",
    IntentType.PRODUCT_RECOMMEND: "product_recommend",
    IntentType.MARKETING_GENERATION: "marketing",
}

# agent 名称 -> 任务目的
_AGENT_PURPOSES = {
    "customer_insight": "分析客户画像与潜在金融需求",
    "product_recommend": "匹配并推荐合适的金融产品",
    "marketing": "生成营销方案与沟通话术",
}

# 规则兜底关键词（LLM 不可用/解析失败时使用）
_RULE_KEYWORDS: dict[IntentType, list[str]] = {
    IntentType.CUSTOMER_INSIGHT: ["分析", "洞察", "画像", "了解", "客户", "经营", "需求"],
    IntentType.PRODUCT_RECOMMEND: ["推荐", "产品", "贷款", "融资", "信贷", "匹配", "额度"],
    IntentType.MARKETING_GENERATION: ["营销", "话术", "拜访", "方案", "沟通", "开场"],
}


class SupervisorAgent:
    """主控 Agent：Planning / Routing / Aggregation。"""

    name = "supervisor"

    def __init__(self, llm: BaseLLMProvider | None = None) -> None:
        self.llm = llm or get_llm()
        self.executor = WorkflowExecutor()
        logger.info("SupervisorAgent 初始化 | llm=%s", self.llm)

    # ---------- 对外主流程 ----------

    async def process(self, message: str, session_id: str | None = None) -> dict:
        """完整编排流程：意图 → 规划 → 交给 executor 执行 → 汇总。"""
        logger.info("Supervisor.process | session_id=%s | message=%.50s", session_id, message)
        intent = await self.detect_intent(message)
        plan = self.create_plan(message, intent)
        state = AgentState(message=message, intent=intent.value, session_id=session_id or "")
        state = await self.executor.execute(plan, state)
        return self.aggregate_results(plan, state)

    # ---------- Step 1: 意图识别 ----------

    async def detect_intent(self, message: str) -> IntentType:
        """识别用户意图：优先 LLM，失败回退规则。"""
        try:
            return await self._llm_detect_intent(message)
        except Exception as exc:
            logger.warning("LLM 意图识别失败，使用规则兜底: %s", exc)
            return self._rule_detect_intent(message)

    async def _llm_detect_intent(self, message: str) -> IntentType:
        """调用 LLM 识别意图，要求只返回意图名称。"""
        raw = await self.llm.agenerate(
            [
                {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0,
        )
        text = raw.strip().lower()
        for intent in IntentType:
            if intent.value in text:
                return intent
        raise ValueError(f"无法从 LLM 输出解析意图: {raw[:100]}")

    def _rule_detect_intent(self, message: str) -> IntentType:
        """关键词规则兜底分类。"""
        hit: dict[IntentType, int] = {}
        for intent, kws in _RULE_KEYWORDS.items():
            hit[intent] = sum(1 for kw in kws if kw in message)
        matched = [i for i, c in hit.items() if c > 0]
        if len(matched) >= 2:
            return IntentType.MULTI_TASK
        if len(matched) == 1:
            return matched[0]
        return IntentType.CUSTOMER_INSIGHT

    # ---------- Step 2: 动态任务规划 ----------

    def create_plan(self, message: str, intent: IntentType) -> TaskPlan:
        """动态生成任务计划：检测需求 → 依赖展开 → 生成带 depends_on 的任务。"""
        requested = self._detect_requested_agents(message)
        agent_names = self._expand_with_deps(requested)
        tasks = [
            Task(
                agent_name=name,
                purpose=_AGENT_PURPOSES[name],
                depends_on=AGENT_DEPENDENCIES[name],
            )
            for name in agent_names
        ]
        plan = TaskPlan(intent=intent, tasks=tasks)
        logger.info("生成任务计划 | intent=%s | agents=%s", intent.value, agent_names)
        return plan

    def _detect_requested_agents(self, message: str) -> set[str]:
        """检测用户直接请求的 agent（叶子需求）。"""
        requested: set[str] = set()
        for intent, kws in _RULE_KEYWORDS.items():
            if any(kw in message for kw in kws):
                requested.add(_INTENT_TO_AGENT[intent])
        if not requested:
            requested.add("customer_insight")
        return requested

    @staticmethod
    def _expand_with_deps(requested: set[str]) -> list[str]:
        """按依赖展开，返回拓扑序的 agent 列表。"""
        result: list[str] = []

        def add(agent: str) -> None:
            for dep in AGENT_DEPENDENCIES[agent]:
                add(dep)
            if agent not in result:
                result.append(agent)

        for agent in requested:
            add(agent)
        return result

    # ---------- Step 4: 结果汇总 ----------

    def aggregate_results(self, plan: TaskPlan, state: AgentState) -> dict:
        """汇总执行结果，返回统一结构。"""
        return {
            "intent": state.intent,
            "plan": plan.model_dump(),
            "results": state.history,
        }
