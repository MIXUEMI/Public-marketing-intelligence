"""Agent 层：Supervisor 与各专业 Agent。

导入各专业 Agent 模块以触发 @register_agent 注册（注册中心自动收集）。
新增 Agent 时在此追加一行导入即可，无需改动 Supervisor。
"""
from app.agents.customer_insight.agent import CustomerInsightAgent  # noqa: F401
from app.agents.product_recommend.agent import ProductRecommendAgent  # noqa: F401
from app.agents.marketing.agent import MarketingAgent  # noqa: F401
