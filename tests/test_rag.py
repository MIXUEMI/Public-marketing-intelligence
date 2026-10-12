"""
Step 6 RAG 知识库测试。

覆盖：文档加载、切块、向量库写入/检索、语义查询、Agent 无需修改仍可调用。
"""
import pytest

from app.agents.product_recommend.agent import ProductRecommendAgent
from app.agents.registry import get_agent
from app.llm.mock import MockProvider
from app.rag.chunker import chunk_documents
from app.rag.document_loader import load_documents
from app.rag.embedding import get_embedding
from app.rag.retriever import ProductRetriever
from app.rag.vector_store import ChromaVectorStore


@pytest.fixture
def embedding():
    """无本地模型时自动降级 Mock（保证测试确定性）。"""
    return get_embedding()


@pytest.fixture
def retriever(tmp_path, embedding):
    """隔离的临时向量库，避免污染 data/chroma。"""
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"))
    return ProductRetriever(store=store, embedding=embedding)


# 1. 文档加载成功
def test_document_loading():
    docs = load_documents()
    assert docs
    names = {d["metadata"]["product_name"] for d in docs}
    assert "流动资金贷款" in names
    assert "固定资产贷款" in names
    # metadata 含 product_name 与 category
    assert all(d["metadata"].get("product_name") for d in docs)
    assert all(d["metadata"].get("category") for d in docs)


# 2. chunk 成功，产品信息不被切断
def test_chunking():
    docs = load_documents()
    chunks = chunk_documents(docs, chunk_size=500, chunk_overlap=100)
    assert chunks
    # 每个产品短于 chunk_size，应保持完整（一个产品一个 chunk）
    names = {c["metadata"]["product_name"] for c in chunks}
    assert "流动资金贷款" in names
    # chunk 元数据保留结构化字段
    assert all(c["metadata"].get("marketing_point") for c in chunks)


# 3. 向量库创建 + 写入 + 检索
def test_vector_store(tmp_path, embedding):
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"))
    docs = load_documents()
    chunks = chunk_documents(docs)
    texts = [c["text"] for c in chunks]
    vectors = embedding.embed_documents(texts)
    ids = [f"p-{i}" for i in range(len(chunks))]
    metadatas = [c["metadata"] for c in chunks]

    store.add_documents(ids=ids, texts=texts, embeddings=vectors, metadatas=metadatas)
    assert store.count() == len(chunks)

    hits = store.similarity_search(embedding.embed_query("制造企业扩大生产需要资金"), top_k=3)
    assert hits


# 4. 语义查询：返回 流动资金贷款 + 固定资产贷款
def test_retrieve_products(retriever):
    products = retriever.retrieve_products("制造企业扩大生产需要资金", top_k=5)
    names = [p["name"] for p in products]
    assert "流动资金贷款" in names
    assert "固定资产贷款" in names
    # 返回结构与旧 search_products 一致
    for p in products:
        assert set(p.keys()) == {"name", "description", "condition", "marketing_point"}


# 5. ProductRecommendAgent 无需修改仍能调用（search_products 已切换为 RAG）
@pytest.mark.asyncio
async def test_agent_unchanged():
    assert get_agent("product_recommend") is ProductRecommendAgent
    agent = ProductRecommendAgent(llm=MockProvider(model="test"))
    out = await agent.execute({
        "customer_insight": {
            "customer_profile": {"name": "某制造企业", "industry": "制造业",
                                 "scale": "中型企业", "description": ""},
            "potential_needs": [
                {"need": "流动资金贷款", "reason": ""},
                {"need": "设备融资", "reason": ""},
            ],
            "business_opportunities": [{"opportunity": "产能扩张", "recommendation": ""}],
        }
    })
    assert out["status"] == "success"
    assert out["result"]["recommended_products"]
