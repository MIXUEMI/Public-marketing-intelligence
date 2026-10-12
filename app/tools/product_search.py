"""
金融产品库查询工具（RAG 实现）。

内部调用 RAG Retriever（Chroma 向量检索），签名与返回结构保持不变：
    async def search_products(query: str, top_k: int = 3) -> list[dict]

因此 ProductRecommendAgent 无需任何改动。
"""
import logging

from app.rag.retriever import get_retriever

logger = logging.getLogger(__name__)


async def search_products(query: str, top_k: int = 3) -> list[dict]:
    """按查询检索金融产品（RAG 向量检索）。

    Args:
        query: 检索关键词（来自客户洞察的潜在需求/行业/商机）
        top_k: 返回数量

    Returns:
        list[dict]: 每个产品含 name/description/condition/marketing_point
    """
    retriever = get_retriever()
    products = retriever.retrieve_products(query, top_k=top_k)
    logger.info("产品检索（RAG）| query=%.50s | 命中=%d", query, len(products))
    return products
