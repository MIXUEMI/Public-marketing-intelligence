"""Agent 层通用工具函数。"""
import json
import re


def extract_json(text: str) -> dict:
    """从 LLM 输出中提取 JSON 对象。

    支持三种情况：纯 JSON、```json 代码块包裹、JSON 前后有额外文字。
    提取失败抛出 ValueError。
    """
    text = text.strip()

    # 1. 去掉 markdown 代码块
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)

    # 2. 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. 兜底：提取第一个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从输出中解析 JSON: {text[:200]}")
