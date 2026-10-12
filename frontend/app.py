"""
对公营销智能助手工作台 —— 入口页。

Streamlit 多页应用：本文件为首页，pages/ 下的页面自动出现在左侧边栏。
"""
import streamlit as st

st.set_page_config(page_title="对公营销智能助手", page_icon="🏦", layout="wide")

st.title("🏦 对公营销智能助手工作台")
st.caption("大模型 + Multi-Agent + RAG 知识库 —— 面向银行对公客户经理的企业级 Demo")

st.markdown(
    """
### 功能导航（见左侧边栏）

| 页面 | 功能 |
|---|---|
| 💬 智能营销对话 | 输入客户经理需求，Supervisor 编排 Agent 生成客户洞察、产品推荐、营销方案 |
| 👥 客户洞察中心 | 查看客户画像、行业分析、潜在需求、业务机会 |
| 🎯 推荐记录中心 | 查看推荐产品、推荐理由、生成时间 |
| 📊 Agent 运行监控 | 查看每个 Agent 的执行状态与耗时 |

### 快速开始

1. **启动后端**（另开一个终端）：
   ```bash
   uvicorn app.main:app --reload
   ```
   默认地址 `http://127.0.0.1:8000`（如需改，前端用环境变量 `AGENT_API_BASE` 覆盖）。

2. **启动前端**：
   ```bash
   streamlit run frontend/app.py
   ```

3. 进入左侧「💬 智能营销对话」，输入例如：
   > 分析制造企业并推荐金融产品，生成拜访方案

> 提示：演示模式下数据库默认关闭（`USE_DATABASE=false`），对话仍可完整运行；
> 客户洞察/推荐记录/运行监控三个页面需开启数据库（`USE_DATABASE=true`）才能读到历史数据。
"""
)
