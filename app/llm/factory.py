"""
LLM Provider 工厂：根据配置实例化对应的 Provider。

核心逻辑：若目标 provider 未配置 api_key，自动降级为 MockProvider，
从而保证系统「必须可运行」——即使没有真实模型 Key 也能跑通。
"""
import logging

from app.core.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.deepseek import DeepSeekProvider
from app.llm.glm import GLMProvider
from app.llm.mock import MockProvider
from app.llm.openai import OpenAIProvider
from app.llm.qwen import QwenProvider

logger = logging.getLogger(__name__)

# provider 名称 -> (实现类, settings 中的 api_key 字段名, base_url 字段名)
_PROVIDER_MAP: dict[str, tuple[type[BaseLLMProvider], str | None, str | None]] = {
    "openai": (OpenAIProvider, "openai_api_key", "openai_base_url"),
    "deepseek": (DeepSeekProvider, "deepseek_api_key", "deepseek_base_url"),
    "qwen": (QwenProvider, "qwen_api_key", "qwen_base_url"),
    "glm": (GLMProvider, "glm_api_key", "glm_base_url"),
    "mock": (MockProvider, None, None),
}


def get_llm(provider: str | None = None, model: str | None = None) -> BaseLLMProvider:
    """按名称实例化 LLM Provider；未知名称或缺 Key 时降级为 Mock。"""
    name = (provider or settings.llm_provider).lower()
    model = model or settings.llm_model

    if name not in _PROVIDER_MAP:
        logger.warning("未知 provider=%s，回退 MockProvider", name)
        return MockProvider(model=model)

    cls, key_field, url_field = _PROVIDER_MAP[name]

    if key_field is None:  # mock
        return cls(model=model)

    api_key = getattr(settings, key_field)
    base_url = getattr(settings, url_field)

    if not api_key:
        logger.warning("provider=%s 未配置 api_key，降级为 MockProvider", name)
        return MockProvider(model=model)

    return cls(model=model, base_url=base_url, api_key=api_key)
