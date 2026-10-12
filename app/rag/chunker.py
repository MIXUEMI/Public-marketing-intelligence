"""
文本切分器。

支持 chunk_size / chunk_overlap，默认 chunk_size=500、overlap=100。
关键约束：产品信息不被切断 —— document_loader 已按产品切分文档，
单个产品文本短于 chunk_size 时保持完整（一个产品 = 一个 chunk）。
"""
import logging

logger = logging.getLogger(__name__)


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[dict]:
    """把文档切分为 chunk，保留 metadata（product_name 始终可归属）。"""
    chunks: list[dict] = []
    for doc in documents:
        text = doc["text"]
        metadata = doc["metadata"]

        # 产品短文本：整体作为一个 chunk，保证信息完整
        if len(text) <= chunk_size:
            chunks.append({"text": text, "metadata": metadata})
            continue

        # 超长文本：按 chunk_size 滑窗切分，overlap 重叠，metadata 保留
        step = max(1, chunk_size - chunk_overlap)
        for start in range(0, len(text), step):
            seg = text[start:start + chunk_size]
            if not seg:
                break
            chunks.append({"text": seg, "metadata": metadata})
            if start + chunk_size >= len(text):
                break

    logger.info("切块完成 | documents=%d | chunks=%d", len(documents), len(chunks))
    return chunks
