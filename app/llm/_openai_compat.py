"""
OpenAI 兼容协议实现（通用）。

DeepSeek / Qwen / GLM / OpenAI 都遵循 OpenAI 的 /chat/completions 协议，
因此这里实现一份通用 HTTP 调用逻辑，各 Provider 只需覆写 name 与默认 base_url，
避免重复代码。

说明：文件名以 _ 开头表示「内部共享实现」，不直接对外暴露。
"""
import logging
from typing import Any

import httpx

from app.llm.base import BaseLLMProvider, Message

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """基于 OpenAI 兼容 chat/completions 协议的通用实现。"""

    name: str = "openai_compat"

    def _build_payload(
        self, messages: list[Message], temperature: float, **kwargs: Any
    ) -> dict:
        """构造请求体。"""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        payload.update(kwargs)
        return payload

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _endpoint(self) -> str:
        """拼接 chat/completions 端点。"""
        base = (self.base_url or "").rstrip("/")
        return f"{base}/chat/completions"

    @staticmethod
    def _extract_text(data: dict) -> str:
        """从响应中提取文本内容。"""
        return data["choices"][0]["message"]["content"]

    def generate(
        self, messages: list[Message], temperature: float = 0.7, **kwargs: Any
    ) -> str:
        if not self.api_key:
            raise ValueError(f"{self.name} provider 缺少 api_key，无法调用真实模型")
        resp = httpx.post(
            self._endpoint(),
            headers=self._headers(),
            json=self._build_payload(messages, temperature, **kwargs),
            timeout=60,
        )
        resp.raise_for_status()
        return self._extract_text(resp.json())

    async def agenerate(
        self, messages: list[Message], temperature: float = 0.7, **kwargs: Any
    ) -> str:
        if not self.api_key:
            raise ValueError(f"{self.name} provider 缺少 api_key，无法调用真实模型")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self._endpoint(),
                headers=self._headers(),
                json=self._build_payload(messages, temperature, **kwargs),
            )
            resp.raise_for_status()
            data = resp.json()
        return self._extract_text(data)
