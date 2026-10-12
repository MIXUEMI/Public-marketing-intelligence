"""
共享状态 AgentState：保存整个任务执行过程的上下文。

每执行一个 Agent，由 WorkflowExecutor 更新对应字段与 history。
"""
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Agent 执行过程中的共享状态。"""

    message: str = Field(default="", description="原始用户消息")
    intent: str = Field(default="", description="识别出的意图")
    session_id: str = Field(default="", description="会话 ID（用于执行记录关联）")

    # 各 Agent 的产出结果（agent 名称与字段名一致，便于 executor 通过 setattr 写入）
    customer_insight: dict = Field(default_factory=dict, description="客户洞察结果")
    product_recommend: dict = Field(default_factory=dict, description="产品推荐结果")
    marketing: dict = Field(default_factory=dict, description="营销方案结果")

    # 执行历史（每个 Agent 的完整返回，含 agent/status/result）
    history: list[dict] = Field(default_factory=list, description="执行历史")
