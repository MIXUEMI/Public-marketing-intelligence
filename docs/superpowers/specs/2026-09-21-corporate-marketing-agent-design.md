# 对公营销智能体（Corporate Marketing Agent）设计规格

- 日期：2026-09-21
- 状态：待评审（Architectural）
- 目标用户：银行对公客户经理

## 1. 目标

建设一个面向银行对公客户经理的智能营销助手，基于「大模型 + Multi-Agent + RAG + 企业数据接口」，完成：

1. 客户洞察分析
2. 金融产品智能推荐
3. 营销方案与沟通话术生成

## 2. 技术选型（已确认）

| 层次 | 选型 |
|------|------|
| 后端 | Python 3.11 + FastAPI |
| Agent 编排 | **LangGraph**（LangChain 作为底层 LLM 封装） |
| LLM 抽象 | 自研 `llm/` 包，默认 **DeepSeek**，支持 Qwen/GLM/OpenAI 切换，内置 MockProvider 兜底 |
| 向量数据库 | **Chroma**（默认），统一 `VectorStore` 接口预留 **Milvus** 适配 |
| Embedding | 可插拔（OpenAI / sentence-transformers / Mock 哈希） |
| 关系数据库 | **PostgreSQL**（SQLAlchemy 2.0 ORM，可切 MySQL） |
| 前端 Demo | **Streamlit** |
| 配置 | Pydantic Settings + `.env` |
| 测试 | pytest |

## 3. 架构

### 3.1 总体模式

Supervisor Agent（主控）+ 三个专业 Agent（CustomerInsight / ProductRecommend / Marketing）。

```
用户输入 → Supervisor(意图识别/拆解/路由/融合)
                ├─→ CustomerInsightAgent   → 客户洞察 JSON
                ├─→ ProductRecommendAgent  → 产品推荐 JSON（基于 RAG）
                └─→ MarketingAgent         → 营销方案 Markdown
```

### 3.2 Supervisor 职责边界

- 只做：Planning / Routing / Aggregation / 上下文管理
- 不做：任何业务逻辑

### 3.3 Agent 扩展机制（Agent Registry）

新增 Agent 只需「新增 agent 文件 + 注册」，不改 Supervisor 核心。Registry 为映射表：

```python
AGENT_REGISTRY = {
    "customer_insight": CustomerInsightAgent,
    "product_recommend": ProductRecommendAgent,
    "marketing": MarketingAgent,
}
```

### 3.4 数据流（一次复合对话）

```
用户输入
 → Supervisor.plan() 拆解任务
 → Router 按 registry 路由（支持链式依赖：洞察 → 推荐 → 话术）
 → 各 Agent 产出结构化结果
 → Supervisor.aggregate() 融合返回
```

## 4. 各 Agent 接口契约

### 4.1 CustomerInsightAgent

- 输入：企业名称 + 基本信息（工商/行业/交易/历史，来自 tools 层）
- 输出 JSON：`{customer_profile, industry_analysis, potential_needs, business_opportunities}`

### 4.2 ProductRecommendAgent

- 输入：客户洞察结果 + 产品知识库（RAG 检索）
- 输出 JSON：`{recommended_products: [{name, reason, condition, marketing_point}]}`
- 约束：**必须基于知识库检索，不得凭空生成产品**

### 4.3 MarketingAgent

- 输入：洞察结果 + 推荐结果
- 输出：Markdown（拜访方案 / 沟通话术 / 产品介绍）

## 5. RAG 知识库

- 目录 `knowledge_base/`：`products/`（贷款、供应链）、`policies/`（监管规则）、`industry/`（制造等）
- 流程：文档 → 解析 → Chunk 切分 → Embedding → 向量库
- 检索接口：`retriever.py`

## 6. 数据库

- ORM：SQLAlchemy 2.0
- 表：`users` / `customers` / `conversations` / `agent_calls` / `recommendations`
- 记录 Agent 调用过程（供前端展示调用链）

## 7. 目录结构

见 README 与代码实际落位（`app/` 为根包，`knowledge_base/`、`frontend/`、`tests/` 平级）。

## 8. 错误处理与可运行性

- LLM / Embedding 均有无 Key 的 Mock 兜底，保证离线可跑通全链路
- 每个 Agent 输出走 Pydantic 校验，失败有明确错误信息返回前端
- 数据库不可用时降级为内存态（`USE_DB=false` 可关）

## 9. 测试策略

- 单测：Supervisor 拆解/路由、各 Agent 输出契约、RAG 检索
- 端到端：一条复合请求走通三 Agent 并返回结构化结果

## 10. 交付里程碑（Step1→Step8）

1. 项目初始化（目录/依赖/config/Mock LLM）
2. FastAPI 基础服务（`/health` `/chat` 骨架）
3. Supervisor Agent + Registry
4. 三个专业 Agent（先 Mock 数据源）
5. Agent Router 串联全流程
6. RAG 接入（Chroma 建库 + 检索）
7. 数据库落地（Postgres ORM + 落库）
8. Streamlit 前端 Demo + README

> 注：当前目录非 git 仓库，spec 未走 git 提交；如需纳入版本管理，可在 Step 1 一并 `git init`。
