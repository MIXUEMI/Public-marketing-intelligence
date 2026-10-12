"""
FastAPI 客户端封装。

前端所有页面统一通过本模块调用后端 HTTP 接口，不在页面里写请求逻辑。
后端地址通过环境变量 AGENT_API_BASE 覆盖，默认 http://127.0.0.1:8000。
"""
import os

import httpx

BASE_URL = os.environ.get("AGENT_API_BASE", "http://127.0.0.1:8000")
_TIMEOUT = 120.0


def _get(path: str, params: dict | None = None) -> list | dict:
    with httpx.Client(base_url=BASE_URL, timeout=_TIMEOUT) as client:
        resp = client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()


def _post(path: str, payload: dict) -> dict:
    with httpx.Client(base_url=BASE_URL, timeout=_TIMEOUT) as client:
        resp = client.post(path, json=payload)
        resp.raise_for_status()
        return resp.json()


def chat(message: str, session_id: str) -> dict:
    """POST /chat —— 提交客户经理需求，返回完整编排结果。"""
    return _post("/chat", {"message": message, "session_id": session_id})


def get_customers(limit: int = 100) -> list:
    """GET /customers —— 客户洞察中心列表。"""
    return _get("/customers", {"limit": limit})


def get_recommendations(limit: int = 100) -> list:
    """GET /recommendations —— 推荐记录中心列表。"""
    return _get("/recommendations", {"limit": limit})


def get_executions(session_id: str | None = None, limit: int = 100) -> list:
    """GET /executions 或 /executions/{session_id} —— Agent 运行监控。"""
    if session_id:
        return _get(f"/executions/{session_id}", {"limit": limit})
    return _get("/executions", {"limit": limit})


def get_history(session_id: str, limit: int = 100) -> list:
    """GET /history/{session_id} —— 会话消息历史。"""
    return _get(f"/history/{session_id}", {"limit": limit})
