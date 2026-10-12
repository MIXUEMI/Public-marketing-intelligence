"""Agent 运行监控 —— 读取 GET /executions 展示执行记录。"""
import pandas as pd
import streamlit as st

from api.client import get_executions

st.set_page_config(page_title="Agent 运行监控", page_icon="📊", layout="wide")

st.title("📊 Agent 运行监控")
st.caption("每个 Agent 的执行状态、耗时、执行时间（企业级可观测性）")

try:
    with st.spinner("加载执行记录…"):
        executions = get_executions()
except Exception as exc:
    st.error(f"调用后端失败：{exc}")
    st.stop()

if not executions:
    st.info("暂无执行记录。请先在「💬 智能营销对话」中发起一次分析，并确保已开启数据库。")
    st.stop()

# 汇总表格：Agent 名称 / 状态 / 耗时 / 执行时间
rows = [
    {
        "Agent 名称": e.get("agent_name", ""),
        "状态": e.get("status", ""),
        "耗时(ms)": e.get("duration_ms", ""),
        "会话 ID": e.get("session_id", ""),
        "执行时间": e.get("created_at", ""),
    }
    for e in executions
]
st.dataframe(pd.DataFrame(rows))

# 明细：输入/输出 JSON
st.markdown("#### 执行明细")
for e in executions:
    with st.expander(
        f"{e.get('agent_name', '?')} · {e.get('status', '?')} · {e.get('duration_ms', '')} ms",
        expanded=False,
    ):
        st.markdown(f"**会话 ID**：`{e.get('session_id', '')}`")
        st.markdown(f"**执行时间**：{e.get('created_at', '')}")
        col_in, col_out = st.columns(2)
        with col_in:
            st.markdown("**输入 input_data**")
            st.json(e.get("input_data") or {})
        with col_out:
            st.markdown("**输出 output_data**")
            st.json(e.get("output_data") or {})
