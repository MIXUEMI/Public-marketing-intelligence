"""推荐记录中心 —— 读取 GET /recommendations 展示推荐记录。"""
import streamlit as st

from api.client import get_recommendations

st.set_page_config(page_title="推荐记录中心", page_icon="🎯", layout="wide")

st.title("🎯 推荐记录中心")
st.caption("推荐产品、推荐理由、生成时间（来自产品推荐 Agent + RAG 知识库）")

try:
    with st.spinner("加载推荐记录…"):
        recs = get_recommendations()
except Exception as exc:
    st.error(f"调用后端失败：{exc}")
    st.stop()

if not recs:
    st.info("暂无推荐记录。请先在「💬 智能营销对话」中发起一次产品推荐，并确保已开启数据库。")
    st.stop()


def _product_names(products) -> str:
    if isinstance(products, list):
        return "、".join(p.get("name", "") for p in products if isinstance(p, dict) and p.get("name"))
    if isinstance(products, dict):
        return products.get("name", "")
    return ""


for rec in recs:
    customer = rec.get("customer_name") or "未知客户"
    names = _product_names(rec.get("products")) or "—"
    with st.expander(f"🎯 {customer} · {names}", expanded=False):
        st.markdown(f"**客户**：{customer}")
        st.markdown(f"**推荐产品**：{names}")
        st.markdown(f"**推荐理由**：{rec.get('reason') or '—'}")
        st.markdown(f"**生成时间**：{rec.get('created_at') or '—'}")
        with st.expander("🔎 原始 JSON", expanded=False):
            st.json(rec)
