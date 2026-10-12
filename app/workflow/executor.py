"""
Workflow Executor —— 根据 TaskPlan 依依赖顺序执行 Agent，并自动传递上下文。

核心职责：
    1. 拓扑排序任务（尊重 depends_on）
    2. 逐任务获取 Agent 并构造输入（注入历史结果）
    3. 执行 Agent，更新共享状态
"""
import logging
import time

from app.agents.base import BaseAgent
from app.agents.registry import get_agent
from app.agents.schemas import Task, TaskPlan
from app.repositories.execution import create_execution_record, update_execution_record
from app.workflow.state import AgentState

logger = logging.getLogger(__name__)


def build_agent_input(agent_name: str, state: AgentState) -> dict:
    """根据 agent 类型构造输入，注入依赖的历史结果（链式传参核心）。"""
    if agent_name == "customer_insight":
        # 客户洞察只需原始消息
        return {"message": state.message}
    if agent_name == "product_recommend":
        # 产品推荐依赖客户洞察结果
        return {"customer_insight": state.customer_insight}
    if agent_name == "marketing":
        # 营销话术依赖客户洞察 + 产品推荐结果
        return {
            "customer_insight": state.customer_insight,
            "product_recommend": state.product_recommend,
        }
    # 未来新增 agent 的默认适配：注入消息
    return {"message": state.message}


class WorkflowExecutor:
    """按任务依赖顺序执行 Agent 的执行器。"""

    async def execute(self, plan: TaskPlan, state: AgentState) -> AgentState:
        """执行整个任务计划，逐任务更新 state，最后返回 state。"""
        for task in self._topo_sort(plan.tasks):
            # 依赖校验
            if not self._deps_satisfied(task, state):
                logger.warning("依赖未满足，跳过: %s (依赖 %s)", task.agent_name, task.depends_on)
                state.history.append({
                    "agent": task.agent_name,
                    "status": "skipped",
                    "result": {"detail": f"依赖未满足: {task.depends_on}"},
                })
                continue

            agent_cls = get_agent(task.agent_name)
            if agent_cls is None:
                logger.warning("Agent 未注册: %s", task.agent_name)
                state.history.append({
                    "agent": task.agent_name,
                    "status": "not_registered",
                    "result": {"detail": f"Agent '{task.agent_name}' 尚未注册"},
                })
                continue

            # 构造输入（注入历史结果）并执行
            agent_input = build_agent_input(task.agent_name, state)
            result = await self._run_agent(agent_cls, task, agent_input, state.session_id)
            self._update_state(state, task.agent_name, result)
        return state

    async def _run_agent(
        self, agent_cls: type[BaseAgent], task: Task, agent_input: dict, session_id: str = ""
    ) -> dict:
        """实例化并执行单个 Agent，异常兜底；执行前后通过 Hook 落库（不侵入 Agent）。"""
        start = time.perf_counter()
        execution_id = await create_execution_record(session_id, task.agent_name, agent_input)
        try:
            agent = agent_cls()
            logger.info("执行 Agent: %s | purpose=%s", agent.name, task.purpose)
            result = await agent.execute(agent_input)
            duration_ms = int((time.perf_counter() - start) * 1000)
            await update_execution_record(
                execution_id, result, result.get("status", "success"), duration_ms
            )
            return result
        except Exception as exc:
            logger.exception("Agent 执行失败: %s", task.agent_name)
            result = {"agent": task.agent_name, "status": "error", "result": {"detail": str(exc)}}
            duration_ms = int((time.perf_counter() - start) * 1000)
            await update_execution_record(execution_id, result, "error", duration_ms)
            return result

    def _update_state(self, state: AgentState, agent_name: str, result: dict) -> None:
        """将 Agent 结果写入 state（history + 对应字段）。"""
        state.history.append(result)
        if result.get("status") == "success" and hasattr(state, agent_name):
            setattr(state, agent_name, result.get("result", {}))

    @staticmethod
    def _deps_satisfied(task: Task, state: AgentState) -> bool:
        """检查 task.depends_on 是否都已成功执行。"""
        done = {h["agent"] for h in state.history if h.get("status") == "success"}
        return all(dep in done for dep in task.depends_on)

    @staticmethod
    def _topo_sort(tasks: list[Task]) -> list[Task]:
        """按 depends_on 拓扑排序，保证依赖先执行。"""
        by_name = {t.agent_name: t for t in tasks}
        result: list[Task] = []
        placed: set[str] = set()
        remaining = list(tasks)

        while remaining:
            progressed = False
            for t in list(remaining):
                # 依赖不在本次任务中，或已被放置 → 可执行
                if all(dep not in by_name or dep in placed for dep in t.depends_on):
                    result.append(t)
                    placed.add(t.agent_name)
                    remaining.remove(t)
                    progressed = True
            if not progressed:
                # 存在环或缺失依赖，按原顺序追加剩余任务
                result.extend(remaining)
                break
        return result
