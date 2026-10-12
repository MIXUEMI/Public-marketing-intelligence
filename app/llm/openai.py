"""OpenAI Provider（标准 OpenAI API）。"""
from app.llm._openai_compat import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
