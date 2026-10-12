"""
向量数据库封装：Chroma。

抽象出统一接口（create_collection / add_documents / similarity_search），
未来替换 Milvus 时，只需实现相同接口，Retriever 与 Agent 无需改动。
"""
import logging

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Chroma 向量库封装。"""

    def __init__(self, persist_dir: str, collection_name: str = "products") -> None:
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client = self._init_client()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # 余弦相似度
        )

    def _init_client(self):
        import chromadb
        try:
            # 关闭匿名遥测，适配私有化部署（无外网）
            return chromadb.PersistentClient(
                path=self.persist_dir,
                settings=chromadb.config.Settings(anonymized_telemetry=False),
            )
        except Exception:
            return chromadb.PersistentClient(path=self.persist_dir)

    def create_collection(self, name: str | None = None, recreate: bool = False):
        """创建集合；recreate=True 时先删除旧集合（重建索引）。"""
        name = name or self.collection_name
        if recreate:
            try:
                self._client.delete_collection(name)
            except Exception:
                pass
        self.collection_name = name
        self._collection = self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("向量集合就绪 | collection=%s | recreate=%s", name, recreate)
        return self._collection

    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        """批量写入向量与文档。"""
        self._collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("向量写入完成 | count=%d", len(ids))

    def similarity_search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """按余弦相似度检索 top_k 个结果。"""
        res = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        hits: list[dict] = []
        for i in range(len(ids)):
            hits.append({
                "id": ids[i],
                "text": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
                "distance": dists[i] if i < len(dists) else None,
            })
        return hits

    def count(self) -> int:
        """当前集合的向量数量。"""
        return self._collection.count()
