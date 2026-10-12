"""
Step 2 API 层测试。

覆盖：/health 健康检查、/chat 正常请求、/chat 参数校验失败。
使用 FastAPI TestClient 直接驱动 ASGI 应用，无需真实网络端口。
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "corporate-agent"
    assert data["version"] == "0.1.0"


def test_chat_success():
    resp = client.post(
        "/chat",
        json={"message": "帮我分析一下某制造企业客户", "session_id": "sess-001"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess-001"
    assert data["agent"] == "supervisor"
    assert data["status"] == "success"
    assert data["message"]  # 有回复内容


def test_chat_empty_message():
    """空消息应由 Pydantic 校验拦截，返回 422。"""
    resp = client.post("/chat", json={"message": "", "session_id": "sess-002"})
    assert resp.status_code == 422
