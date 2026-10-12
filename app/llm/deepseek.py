"""DeepSeek Provider（OpenAI 兼容协议）。"""
from app.llm._openai_compat import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    name = "deepseek"
