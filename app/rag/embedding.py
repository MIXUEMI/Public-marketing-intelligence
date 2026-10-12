"""
Embedding 接口与实现。

- BaseEmbedding：统一接口（embed_documents / embed_query）
- SentenceTransformerEmbedding：本地模型（默认 all-MiniLM-L6-v2，私有化部署首选）
- OpenAIEmbedding：调用 OpenAI 兼容 embedding 接口
- MockEmbedding：确定性哈希向量（无模型/无 Key 时降级，保证系统可运行）

get_embedding() 工厂：优先本地模型，模型缺失自动降级 Mock。
"""
import hashlib
import logging
import math
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseEmbedding(ABC):
    """Embedding 抽象接口。"""

    name: str = "base"

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化。"""
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        """单条查询向量化（默认复用批量接口）。"""
        return self.embed_documents([text])[0]


class MockEmbedding(BaseEmbedding):
    """确定性 Mock 向量：字符 unigram + bigram 哈希（跨进程稳定，私有化无外网可跑）。"""

    name = "mock"

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def _embed(self, text: str) -> list[float]:
        text = (text or "").lower()
        vec = [0.0] * self.dim

        # 中文以字为单位：unigram + bigram 捕获词级信息
        tokens = list(text)
        tokens += [text[i:i + 2] for i in range(len(text) - 1)]

        for tok in tokens:
            # MD5 保证跨进程确定性（Python 内建 hash 对 str 有随机种子）
            digest = hashlib.md5(tok.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:8], "big") % self.dim
            vec[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class SentenceTransformerEmbedding(BaseEmbedding):
    """本地 sentence-transformers 模型（私有化部署首选）。"""

    name = "sentence_transformers"

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()


class OpenAIEmbedding(BaseEmbedding):
    """OpenAI 兼容 embedding 接口。"""

    name = "openai"

    def __init__(self, api_key: str, base_url: str, model: str = "text-embedding-3-small") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import httpx
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=60,
        )
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda x: x["index"])
        return [d["embedding"] for d in data]


def get_embedding(provider: str | None = None, model: str | None = None) -> BaseEmbedding:
    """按配置实例化 Embedding；模型缺失/无 Key 时自动降级 Mock。"""
    name = (provider or settings.embedding_provider).lower()
    model = model or settings.embedding_model

    if name == "openai":
        if settings.openai_api_key:
            return OpenAIEmbedding(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=model or "text-embedding-3-small",
            )
        logger.warning("openai embedding 未配置 api_key，降级 MockEmbedding")
        return MockEmbedding()

    if name in ("sentence_transformers", "sentence-transformer", "local"):
        try:
            return SentenceTransformerEmbedding(model)
        except Exception as exc:
            logger.warning("本地 embedding 不可用(%s)，降级 MockEmbedding", exc)
            return MockEmbedding()

    if name == "mock":
        return MockEmbedding()

    logger.warning("未知 embedding provider=%s，降级 MockEmbedding", name)
    return MockEmbedding()
