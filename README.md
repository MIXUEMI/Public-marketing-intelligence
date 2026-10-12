# 对公营销智能体（Corporate Marketing Agent）

面向银行对公客户经理的企业级智能营销助手，基于「**大模型 + Multi-Agent 架构 + RAG 知识库 + 企业数据接口**」，
覆盖三大核心场景：

1. **客户洞察分析** —— 客户画像、行业分析、潜在需求、业务机会
2. **金融产品智能推荐** —— 基于 RAG 知识库匹配最合适的金融产品
3. **营销方案与沟通话术生成** —— 拜访计划、开场话术、需求挖掘、产品介绍、跟进

> 本项目按真实企业开发流程分 8 个 Step 渐进式构建，现已全部完成（Step 1–8）。

---

## 系统架构图

```
┌───────────────────────────────────────────────────────────────┐
│                    前端工作台（Streamlit）                       │
│   app.py + pages/{chat, customer, recommendation, monitor}     │
│   frontend/api/client.py（统一 HTTP 封装，无业务逻辑）            │
└───────────────────────────┬───────────────────────────────────┘
                            │ HTTP / JSON
┌───────────────────────────▼───────────────────────────────────┐
│                        FastAPI 后端                            │
│   POST /chat  │  GET /customers · /recommendations            │
│               │  GET /executions · /history                    │
└──────────┬────────────────────────────────┬───────────────────┘
           │                                │
┌──────────▼──────────────┐   ┌─────────────▼────────────────┐
│   ChatService           │   │   Repository 层               │
│   编排 + 持久化链路      │   │   customer / conversation /    │
└──────────┬──────────────┘   │   recommendation / execution  │
           │                  └─────────────┬────────────────┘
┌──────────▼──────────────┐   ┌─────────────▼────────────────┐
│   SupervisorAgent       │   │   SQLAlchemy 2.0（async）     │
│   意图→规划→汇总        │   │   PostgreSQL / SQLite          │
└──────────┬──────────────┘   └──────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────┐
│   WorkflowExecutor（依赖编排 + 执行 Hook 记录 agent_executions）│
└──────────┬──────────────────────────────────────────────┘
           │
┌──────────▼─────────────────────────────────────────────────────┐
│   三个专业 Agent                                                │
│   CustomerInsightAgent · ProductRecommendAgent · MarketingAgent │
└──────────┬───────────────────────────────┬─────────────────────┘
           │                               │
           │                     ┌─────────▼──────────────────┐
           │                     │   RAG 知识库               │
           │                     │   product_search 工具      │
           │                     │   → Retriever → Chroma     │
           │                     │   ← knowledge_base/products│
           │                     └────────────────────────────┘
           │
┌──────────▼───────────────────────────────┐
│   LLM 抽象层                              │
│   DeepSeek / Qwen / GLM / OpenAI / Mock   │
└──────────────────────────────────────────┘
```

---

## Agent 说明

| Agent | 职责 | 输入依赖 | 输出 |
|---|---|---|---|
| **SupervisorAgent** | 意图识别 → 动态任务规划 → 结果汇总（Planning/Routing/Aggregation，不执行） | 用户消息 | 统一编排结果 |
| **CustomerInsightAgent** | 客户画像、行业分析、潜在需求、业务机会 | 用户消息 | `customer_profile` / `industry_analysis` / `potential_needs` / `business_opportunities` |
| **ProductRecommendAgent** | 金融产品智能推荐 | 客户洞察结果 | `recommended_products` |
| **MarketingAgent** | 营销方案与沟通话术（Markdown） | 客户洞察 + 产品推荐 | `content`（完整方案）/ `sections`（分节话术） |

**编排机制**：`SupervisorAgent` 通过 Agent Registry 动态查找 Agent，按 `depends_on` 展开任务；
`WorkflowExecutor` 拓扑排序并链式传参（洞察 → 推荐 → 营销）。核心逻辑与数据层完全解耦，未来可平滑迁移 LangGraph。

---

## RAG 流程

```
knowledge_base/products/*.md（流动资金贷款/固定资产贷款/供应链金融/绿色金融…）
        │
        ▼  document_loader（按 # 标题解析）
   [{text, metadata(product_name, category, target_customer, ...)}]
        │
        ▼  chunker（chunk_size=500, overlap=100，保证产品信息不被切断）
   chunk 列表
        │
        ▼  embedding（sentence-transformers / OpenAI / Mock，缺失自动降级 Mock）
   向量
        │
        ▼  ChromaVectorStore（PersistentClient，data/chroma/）
   向量库
        │
        ▼  ProductRetriever.retrieve_products(query, top_k=3)
   [{name, description, condition, marketing_point}]
        │
        ▼  product_search 工具（async def search_products(query, top_k=3)）
   ProductRecommendAgent 调用
```

- **知识库构建**：`python scripts/build_knowledge_base.py`（首次调用检索时也会自愈式自动建索引）
- **可替换性**：`BaseEmbedding` + `ChromaVectorStore` 统一接口，未来可无痛替换为 Milvus / OpenAI Embedding

---

## 项目结构

```
app/
├── api/                 # 路由层（chat.py / data.py / deps.py）
├── agents/              # Supervisor + 三个专业 Agent（registry 注册中心）
├── workflow/            # WorkflowExecutor + AgentState + 依赖图
├── services/            # ChatService（编排 + 持久化）
├── llm/                 # LLM 抽象层（DeepSeek/Qwen/GLM/OpenAI/Mock）
├── rag/                 # document_loader/chunker/embedding/vector_store/retriever
├── tools/               # product_search / customer_query
├── database/            # connection/models/session + migrations(Alembic)
├── repositories/        # customer/conversation/recommendation/execution
├── schemas/             # Pydantic 请求/响应模型
└── core/                # config + logging
frontend/
├── app.py               # 工作台首页
├── pages/               # chat/customer/recommendation/monitor
└── api/client.py        # HTTP 封装
knowledge_base/products/ # RAG 金融产品知识库（Markdown）
scripts/                 # build_knowledge_base.py
tests/                   # pytest 测试
```

---

## 启动方式

### 1. 环境准备

```bash
# 建议 Python 3.11
python -m venv .venv
.venv\Scripts\activate              # Windows（Linux/Mac: source .venv/bin/activate）
pip install -r requirements.txt
```

配置（可选）：复制 `.env.example` 为 `.env`，填入 LLM API Key。不填则自动降级 Mock，保证无外网可跑。

### 2. 启动后端（FastAPI）

```bash
uvicorn app.main:app --reload --port 8000
```

- 接口文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

### 3. 启动前端（Streamlit）

```bash
streamlit run frontend/app.py
```

- 前端默认连 `http://127.0.0.1:8000`，如需改后端地址：
  ```bash
  # PowerShell
  $env:AGENT_API_BASE="http://127.0.0.1:8000"; streamlit run frontend/app.py
  ```

### 4.（可选）开启数据库持久化

默认 `USE_DATABASE=false`（不连库也能完整运行，用于演示）。

```bash
# .env 中开启
USE_DATABASE=true
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/corporate_agent
```

> 开发建表：`python -c "import asyncio; from app.database.connection import init_db; asyncio.run(init_db())"`
> 生产迁移：`alembic upgrade head`

---

## API 说明

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/chat` | Agent 统一入口，返回意图 + 各 Agent 完整结果 |
| GET | `/health` | 健康检查 |
| GET | `/customers` | 客户洞察中心（客户列表 + 洞察结果） |
| GET | `/recommendations` | 推荐记录中心（客户/产品/理由/时间） |
| GET | `/executions` | Agent 运行监控（全部执行记录） |
| GET | `/executions/{session_id}` | 按会话查询执行记录 |
| GET | `/history/{session_id}` | 会话消息历史 |

**POST /chat 请求示例**

```json
{
  "message": "分析制造企业并推荐金融产品，生成拜访方案",
  "session_id": "demo-001"
}
```

---

## 测试

```bash
python -m pytest -q
# 41 passed（含 API / Supervisor / Workflow / 三个 Agent / RAG / 数据库 / 数据查询接口）
```

---

## 演示截图位置

将前端演示截图放入 `docs/screenshots/`：

- `docs/screenshots/chat.png` —— 智能营销对话
- `docs/screenshots/customer.png` —— 客户洞察中心
- `docs/screenshots/recommendation.png` —— 推荐记录中心
- `docs/screenshots/monitor.png` —— Agent 运行监控

---

## 技术栈

Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL · Chroma · sentence-transformers · Streamlit · DeepSeek（可切 Qwen/GLM/OpenAI/Mock）
