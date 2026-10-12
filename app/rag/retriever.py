"""
Retriever —— 产品检索入口。

对外提供 retrieve_products(query, top_k)，返回结构与旧 search_products 一致：
    [{"name", "description", "condition", "marketing_point"}]

首次调用时若向量库为空，自动从知识库构建索引（自愈，无需手动跑脚本也能用）。
"""
import logging

from app.core.config import settings
from app.rag.chunker import chunk_documents
from app.rag.document_loader import load_documents
from app.rag.embedding import BaseEmbedding, get_embedding
from app.rag.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class ProductRetriever:
    """金融产品向量检索器。"""

    def __init__(self, store: ChromaVectorStore, embedding: BaseEmbedding) -> None:
        self.store = store
        self.embedding = embedding

    def ensure_indexed(self) -> None:
        """向量库为空时，从知识库自动构建索引。"""
        if self.store.count() > 0:
            return
        logger.info("向量库为空，自动构建索引 ...")
        docs = load_documents()
        chunks = chunk_documents(docs)
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        embeddings = self.embedding.embed_documents(texts)
        ids = [f"{c['metadata']['product_name']}-{i}" for i, c in enumerate(chunks)]
        self.store.add_documents(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)
        logger.info("索引构建完成 | products=%d", len(chunks))

    def retrieve_products(self, query: str, top_k: int = 3) -> list[dict]:
        """检索金融产品，返回与旧 search_products 一致的结构。"""
        self.ensure_indexed()
        qvec = self.embedding.embed_query(query)
        hits = self.store.similarity_search(qvec, top_k=top_k)

        products: list[dict] = []
        seen: set[str] = set()
        for h in hits:
            meta = h.get("metadata", {})
            name = meta.get("product_name", "")
            if not name or name in seen:
                continue
            seen.add(name)
            products.append({
                "name": name,
                "description": meta.get("description", ""),
                "condition": meta.get("condition", ""),
                "marketing_point": meta.get("marketing_point", ""),
            })

        logger.info("产品检索 | query=%.50s | 命中=%d", query, len(products))
        return products


_retriever: ProductRetriever | None = None


def get_retriever() -> ProductRetriever:
    """全局单例 Retriever（向量库指向 settings.chroma_persist_dir）。"""
    global _retriever
    if _retriever is None:
        embedding = get_embedding()
        store = ChromaVectorStore(persist_dir=settings.chroma_persist_dir)
        _retriever = ProductRetriever(store=store, embedding=embedding)
        logger.info("Retriever 初始化 | embedding=%s | store=%s", embedding.name, settings.chroma_persist_dir)
    return _retriever
