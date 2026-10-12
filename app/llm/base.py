"""
LLM Provider 抽象层 —— 基类。

所有具体 Provider（OpenAI / DeepSeek / Qwen / GLM / Mock）都实现本接口。
上层（Agent、RAG）只依赖 BaseLLMProvider，从而做到「切换模型不改业务代码」。

消息统一使用 OpenAI 风格：
    messages = [{"role": "system" | "user" | "assistant", "content": str}, ...]
"""
from abc import ABC, abstractmethod
from typing import Any

# 标准消息格式（OpenAI 风格）
Message = dict[str, str]


class BaseLLMProvider(ABC):
    """LLM Provider 统一接口。"""

    name: str = "base"

    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.kwargs = kwargs

    @abstractmethod
    def generate(
        self, messages: list[Message], temperature: float = 0.7, **kwargs: Any
    ) -> str:
        """同步生成，返回纯文本结果。"""

    @abstractmethod
    async def agenerate(
        self, messages: list[Message], temperature: float = 0.7, **kwargs: Any
    ) -> str:
        """异步生成，返回纯文本结果。"""

    def __repr__(self) -> str:
        return f"<{self.name} model={self.model}>"
