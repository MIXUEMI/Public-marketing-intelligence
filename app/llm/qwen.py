"""Qwen（通义千问）Provider（DashScope OpenAI 兼容协议）。"""
from app.llm._openai_compat import OpenAICompatibleProvider


class QwenProvider(OpenAICompatibleProvider):
    name = "qwen"
