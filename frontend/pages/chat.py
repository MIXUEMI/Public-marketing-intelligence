"""智能营销对话页 —— 调用 POST /chat 编排 Agent 并展示结构化结果。"""
import uuid

import streamlit as st

from api.client import chat

st.set_page_config(page_title="智能营销对话", page_icon="💬", layout="wide")

st.title("💬 智能营销对话")
st.caption("输入客户经理需求，Supervisor 编排各 Agent 完成「客户洞察 → 产品推荐 → 营销方案」")

# 会话 ID（每次浏览器会话保持稳定，供多轮对话与记录关联）
if "session_id" not in st.session_state:
    st.session_state.session_id = f"web-{uuid.uuid4().hex[:8]}"


def find_result(resp: dict, agent: str) -> dict | None:
    """从编排结果中提取某个 Agent 的产出（纯展示辅助，非业务逻辑）。"""
    for r in resp.get("results", []):
        if r.get("agent") == agent:
            return r.get("result") or {}
    return None


with st.form("chat_form", clear_on_submit=True):
    message = st.text_area(
        "客户经理需求",
        placeholder="例：分析制造企业并推荐金融产品，生成拜访方案",
        height=120,
    )
    submitted = st.form_submit_button("🚀 开始分析", type="primary")

if submitted:
    if not message.strip():
        st.warning("请输入需求内容")
    else:
        # 加载状态
        try:
            with st.spinner("Supervisor 正在编排 Agent 执行中…"):
                resp = chat(message, st.session_state.session_id)
        except Exception as exc:  # 后端未启动/不可达
            st.error(f"调用后端失败：{exc}")
            st.stop()

        # 1. 用户问题
        st.chat_message("user").markdown(message)

        # 2. Agent 执行过程
        st.markdown("### ⚙️ Agent 执行过程")
        steps = resp.get("results", [])
        if steps:
            for i, r in enumerate(steps, 1):
                icon = "✅" if r.get("status") == "success" else "❌"
                st.markdown(f"{i}. {icon} **{r.get('agent')}** — `{r.get('status')}`")
        else:
            st.info("无执行记录")

        # 3. 客户洞察结果
        insight = find_result(resp, "customer_insight")
        if insight:
            st.markdown("### 👤 客户洞察结果")
            profile = insight.get("customer_profile") or {}
            head = " · ".join(filter(None, [profile.get("name"), profile.get("industry"), profile.get("scale")]))
            if head:
                st.markdown(f"**{head}**")
            if profile.get("description"):
                st.markdown(profile["description"])
            if insight.get("industry_analysis"):
                st.markdown(f"**行业分析**：{insight['industry_analysis']}")
            for title, items, k1, k2 in [
                ("**潜在需求**", insight.get("potential_needs") or [], "need", "reason"),
                ("**业务机会**", insight.get("business_opportunities") or [], "opportunity", "recommendation"),
            ]:
                if items:
                    st.markdown(title)
                    for it in items:
                        st.markdown(f"- {it.get(k1, '')}：{it.get(k2, '')}")

        # 4. 产品推荐结果
        recommend = find_result(resp, "product_recommend")
        if recommend:
            st.markdown("### 🎯 产品推荐结果")
            products = recommend.get("recommended_products") or []
            for p in products:
                with st.expander(f"📦 {p.get('name', '产品')}", expanded=True):
                    st.markdown(f"**推荐理由**：{p.get('reason', '')}")
                    st.markdown(f"**适用条件**：{p.get('condition', '')}")
                    st.markdown(f"**营销切入点**：{p.get('marketing_point', '')}")

        # 5. 营销方案（Markdown 渲染）
        marketing = find_result(resp, "marketing")
        if marketing:
            st.markdown("### 📝 营销方案")
            if marketing.get("content"):
                st.markdown(marketing["content"])
            sections = marketing.get("sections") or {}
            if sections:
                with st.expander("📋 分节话术", expanded=False):
                    for key, label in [
                        ("visit_plan", "拜访目标与计划"),
                        ("opening_script", "开场话术"),
                        ("need_questions", "需求挖掘问题"),
                        ("product_intro", "产品价值介绍"),
                        ("follow_up", "后续跟进计划"),
                    ]:
                        if sections.get(key):
                            st.markdown(f"**{label}**")
                            st.markdown(sections[key])

        # 原始 JSON（调试/审计）
        with st.expander("🔎 原始编排结果 JSON", expanded=False):
            st.json(resp)
