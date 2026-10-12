"""
Agent 基础抽象层。

所有专业 Agent（CustomerInsight / ProductRecommend / Marketing）都必须继承 BaseAgent，
实现统一的 execute 接口，从而能被 Supervisor 以一致方式调度。

统一 I/O 协议：
    输入 dict: {"task": str, "context": dict}
    输出 dict: {"agent": str, "status": str, "result": dict}
"""
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Agent 抽象基类。"""

    name: str = "base"       # registry 中的唯一键
    description: str = ""    # 一句话描述，供日志/列表展示

    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """执行 Agent 任务。

        Args:
            input_data: {"task": 任务描述, "context": 上下文}

        Returns:
            {"agent": Agent 名, "status": success/error, "result": 业务结果}
        """
        raise NotImplementedError
