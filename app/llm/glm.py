"""GLM（智谱 AI）Provider（OpenAI 兼容协议）。"""
from app.llm._openai_compat import OpenAICompatibleProvider


class GLMProvider(OpenAICompatibleProvider):
    name = "glm"
