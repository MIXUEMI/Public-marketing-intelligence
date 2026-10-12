#!/usr/bin/env python
"""
构建金融产品知识库：读取 md → 切块 → Embedding → 写入 Chroma。

运行：python scripts/build_knowledge_base.py
产物：data/chroma/（向量库持久化目录，见 settings.chroma_persist_dir）
"""
import logging
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，保证脚本可从任意目录直接运行
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.rag.chunker import chunk_documents
from app.rag.document_loader import load_documents
from app.rag.embedding import get_embedding
from app.rag.vector_store import ChromaVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("开始构建知识库 ...")

    docs = load_documents()
    chunks = chunk_documents(docs)

    embedding = get_embedding()
    logger.info("使用 Embedding: %s", embedding.name)

    store = ChromaVectorStore(persist_dir=settings.chroma_persist_dir)
    store.create_collection(recreate=True)  # 重建，避免旧向量残留

    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    vectors = embedding.embed_documents(texts)
    ids = [f"{c['metadata']['product_name']}-{i}" for i, c in enumerate(chunks)]

    store.add_documents(ids=ids, texts=texts, embeddings=vectors, metadatas=metadatas)

    logger.info(
        "知识库构建完成 | 产品数=%d | 向量维度=%d | 目录=%s",
        len(chunks),
        len(vectors[0]),
        settings.chroma_persist_dir,
    )


if __name__ == "__main__":
    main()
