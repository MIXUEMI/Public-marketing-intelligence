"""
Workflow 依赖图定义（预留 LangGraph 迁移点）。

当前用静态字典描述 Agent 之间的依赖关系，供 Supervisor 动态规划与 Executor 使用。
未来迁移 LangGraph 时，可替换为 StateGraph 构建，保持 Agent 与 Executor 接口不变。
"""

# agent 名称 -> 依赖的 agent 列表（拓扑依赖关系）
AGENT_DEPENDENCIES: dict[str, list[str]] = {
    "customer_insight": [],
    "product_recommend": ["customer_insight"],
    "marketing": ["customer_insight", "product_recommend"],
}

# 全流程默认执行顺序（供参考）
DEFAULT_PIPELINE: list[str] = ["customer_insight", "product_recommend", "marketing"]
