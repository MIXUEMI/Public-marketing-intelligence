"""
Agent 注册中心（Agent Registry）。

扩展机制：未来新增 Agent（如 KnowledgeQA / DataInsight / MarketingMemory）只需：
    1. 新建 agent 文件并继承 BaseAgent
    2. 用 @register_agent 装饰 或 调用 register_agent() 注册
无需修改 Supervisor 核心代码。
"""
import logging
from typing import Callable

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# 全局注册表：name -> Agent 类
AGENT_REGISTRY: dict[str, type[BaseAgent]] = {}


def register_agent(agent_cls: type[BaseAgent] | None = None) -> Callable:
    """注册一个 Agent 类到注册中心。

    支持两种用法：
        @register_agent                  # 装饰器
        class MyAgent(BaseAgent): ...

        register_agent(MyAgent)          # 直接调用
    """
    def decorator(cls: type[BaseAgent]) -> type[BaseAgent]:
        if not getattr(cls, "name", None):
            raise ValueError(f"Agent 类 {cls.__name__} 缺少 name 属性")
        AGENT_REGISTRY[cls.name] = cls
        logger.info("注册 Agent: %s -> %s", cls.name, cls.__name__)
        return cls

    if agent_cls is not None:
        return decorator(agent_cls)
    return decorator


def get_agent(name: str) -> type[BaseAgent] | None:
    """按名称获取 Agent 类；不存在返回 None。"""
    return AGENT_REGISTRY.get(name)


def list_agents() -> list[str]:
    """列出所有已注册 Agent 名称。"""
    return list(AGENT_REGISTRY.keys())
