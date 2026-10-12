"""
Mock LLM Provider —— 无 Key 时的兜底实现。

返回确定性的占位输出，保证系统在离线 / 未配置 Key 的情况下仍能跑通全链路，
便于开发调试与单元测试（不产生任何外部网络请求）。
"""
from typing import Any

from app.llm.base import BaseLLMProvider, Message


class MockProvider(BaseLLMProvider):
    name = "mock"

    def generate(
        self, messages: list[Message], temperature: float = 0.7, **kwargs: Any
    ) -> str:
        # 取最后一条用户消息，方便直观看到「模型收到了什么」
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        return (
            "[Mock LLM] 未配置真实模型 Key，此为模拟输出。\n"
            f"共收到 {len(messages)} 条消息，最后一条用户输入：{last_user[:200]}"
        )

    async def agenerate(
        self, messages: list[Message], temperature: float = 0.7, **kwargs: Any
    ) -> str:
        return self.generate(messages, temperature, **kwargs)
