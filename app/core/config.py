"""
全局配置模块。

使用 pydantic-settings 从 .env 文件与环境变量读取配置，
字段名与 .env 中的大写环境变量一一对应（大小写不敏感）。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置。所有可调参数集中于此，便于统一管理。"""

    # ---- 应用 ----
    app_name: str = "Corporate Marketing Agent"
    app_version: str = "0.1.0"

    # ---- LLM Provider ----
    # 可选: openai / deepseek / qwen / glm / mock
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.7

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    glm_api_key: str = ""
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"

    # ---- Embedding ----
    # 可选: sentence_transformers / openai / mock（模型缺失时自动降级 mock）
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "all-MiniLM-L6-v2"

    # ---- 向量数据库 ----
    # 可选: chroma / faiss / milvus(预留)
    vector_store: str = "chroma"
    chroma_persist_dir: str = "./data/chroma"

    # ---- 关系数据库 ----
    # use_database=false（开发）不连库也能运行；生产置 true
    use_database: bool = False
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/corporate_agent"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略 .env 中未定义的字段，避免干扰
    )


@lru_cache
def get_settings() -> Settings:
    """获取全局唯一配置实例（带缓存，避免重复读取 .env）。"""
    return Settings()


# 模块级单例，方便直接 `from app.core.config import settings`
settings = get_settings()
