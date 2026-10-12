"""
Agent 层数据结构定义。

- IntentType：用户意图枚举
- Task / TaskPlan：Supervisor 任务规划结构
"""
from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """用户意图类型。"""

    CUSTOMER_INSIGHT = "customer_insight"          # 客户分析
    PRODUCT_RECOMMEND = "product_recommend"        # 产品推荐
    MARKETING_GENERATION = "marketing_generation"  # 营销方案生成
    MULTI_TASK = "multi_task"                      # 多任务组合


class Task(BaseModel):
    """单个子任务。"""

    agent_name: str = Field(..., description="目标 Agent 名称（registry 键）")
    purpose: str = Field(..., description="任务目的描述")
    depends_on: list[str] = Field(default_factory=list, description="依赖的 agent 名称列表")
    input: dict = Field(default_factory=dict, description="静态输入模板（运行时由 executor 的 build_agent_input 动态构建）")


class TaskPlan(BaseModel):
    """任务计划：意图 + 拆解出的子任务列表。"""

    intent: IntentType = Field(..., description="识别出的用户意图")
    tasks: list[Task] = Field(default_factory=list, description="子任务列表")
