"""客户洞察中心 —— 读取 GET /customers 展示客户画像与洞察结果。"""
import streamlit as st

from api.client import get_customers

st.set_page_config(page_title="客户洞察中心", page_icon="👥", layout="wide")

st.title("👥 客户洞察中心")
st.caption("客户画像、行业分析、潜在需求、业务机会（来自客户洞察 Agent）")

try:
    with st.spinner("加载客户数据…"):
        customers = get_customers()
except Exception as exc:
    st.error(f"调用后端失败：{exc}")
    st.stop()

if not customers:
    st.info("暂无客户数据。请先在「💬 智能营销对话」中发起一次分析，并确保已开启数据库。")
    st.stop()

# 客户列表（下拉选择）
labels = [c.get("name") or f"客户 #{c.get('id')}" for c in customers]
selected = st.selectbox("选择客户", labels)

customer = next(c for c in customers if (c.get("name") or f"客户 #{c.get('id')}") == selected)
basic = customer.get("basic_info") or {}

# customer_profile
profile = basic.get("customer_profile") or {}
st.subheader(f"👤 {profile.get('name') or customer.get('name') or '客户'}")
meta = "　".join(
    filter(
        None,
        [
            f"**行业**：{profile.get('industry') or customer.get('industry') or '—'}",
            f"**规模**：{profile.get('scale') or customer.get('scale') or '—'}",
            f"**地区**：{customer.get('location') or '—'}",
        ],
    )
)
if meta:
    st.markdown(meta)
if profile.get("description"):
    st.markdown(profile["description"])

# industry_analysis
if basic.get("industry_analysis"):
    st.markdown("#### 行业分析")
    st.markdown(basic["industry_analysis"])

# potential_needs
needs = basic.get("potential_needs") or []
if needs:
    st.markdown("#### 潜在需求")
    for n in needs:
        st.markdown(f"- **{n.get('need', '')}**：{n.get('reason', '')}")

# business_opportunities
opps = basic.get("business_opportunities") or []
if opps:
    st.markdown("#### 业务机会")
    for o in opps:
        st.markdown(f"- **{o.get('opportunity', '')}**：{o.get('recommendation', '')}")

with st.expander("🔎 原始 JSON", expanded=False):
    st.json(customer)
