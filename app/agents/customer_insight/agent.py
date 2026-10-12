"""
CustomerInsightAgent —— 客户洞察智能体。

根据企业客户信息生成：客户画像、行业分析、潜在金融需求、营销机会。

- LLM 调用复用 app/llm/ 抽象层（get_llm()），不直接初始化模型
- LLM 不可用/解析失败时，自动降级为固定 Mock 结果，保证可运行
- 通过 @register_agent 注册到注册中心，Supervisor 无需改动
"""
import json
import logging

from app.agents.base import BaseAgent
from app.agents.customer_insight.prompts import CUSTOMER_INSIGHT_SYSTEM_PROMPT
from app.agents.customer_insight.schemas import (
    BusinessOpportunity,
    CustomerInsightResult,
    CustomerProfile,
    PotentialNeed,
)
from app.agents.registry import register_agent
from app.agents.utils import extract_json
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm
from app.tools.customer_query import get_customer_profile

logger = logging.getLogger(__name__)


@register_agent
class CustomerInsightAgent(BaseAgent):
    """客户洞察智能体。"""

    name = "customer_insight"
    description = "客户洞察智能体"

    def __init__(self, llm: BaseLLMProvider | None = None) -> None:
        self.llm = llm or get_llm()

    async def execute(self, input_data: dict) -> dict:
        """执行客户洞察分析。

        输入支持两种形式（见 _normalize_input）：
            1) BaseAgent 协议: {"task": ..., "context": {...}}
            2) 直接企业信息:   {"customer_name": ..., "industry": ..., "basic_info": {...}}
        """
        context = self._normalize_input(input_data)
        customer_info = self._resolve_customer(context)
        result = await self._analyze(customer_info)
        logger.info("CustomerInsightAgent 完成分析 | 企业=%s", customer_info.get("customer_name"))
        return {"agent": self.name, "status": "success", "result": result.model_dump()}

    # ---------- 输入归一化与数据获取 ----------

    @staticmethod
    def _normalize_input(input_data: dict) -> dict:
        """归一化输入，兼容 BaseAgent 协议与扁平企业信息两种形式。"""
        if "context" in input_data and isinstance(input_data["context"], dict):
            return input_data["context"]
        return input_data

    def _resolve_customer(self, context: dict) -> dict:
        """确定企业数据：优先用 context 中提供的，否则查 Mock 数据源。"""
        if context.get("customer_name") or context.get("basic_info"):
            return {
                "customer_name": context.get("customer_name", "未知企业"),
                "industry": context.get("industry", "制造业"),
                "basic_info": context.get("basic_info", {}),
                "business": context.get("business", ""),
            }
        # 未提供具体企业信息：从 Mock 数据源取默认样例（未来替换为工商/CRM 接口）
        return get_customer_profile(context.get("customer_name"))

    # ---------- LLM 分析 ----------

    def _build_messages(self, customer_info: dict) -> list[dict]:
        user_prompt = "请分析以下企业客户：\n" + json.dumps(customer_info, ensure_ascii=False, indent=2)
        return [
            {"role": "system", "content": CUSTOMER_INSIGHT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    async def _analyze(self, customer_info: dict) -> CustomerInsightResult:
        """优先 LLM 分析，失败降级为 Mock 结果。"""
        try:
            raw = await self.llm.agenerate(self._build_messages(customer_info), temperature=0.3)
            data = extract_json(raw)
            return CustomerInsightResult.model_validate(data)
        except Exception as exc:
            logger.warning("LLM 洞察分析失败，返回 Mock 结果: %s", exc)
            return self._mock_result(customer_info)

    # ---------- Mock 兜底 ----------

    @staticmethod
    def _mock_result(customer_info: dict) -> CustomerInsightResult:
        """固定 Mock 结果（LLM 不可用时的确定性兜底）。"""
        name = customer_info.get("customer_name", "某企业")
        industry = customer_info.get("industry", "制造业")
        scale = (customer_info.get("basic_info") or {}).get("scale", "中型企业")
        business = customer_info.get("business") or f"{industry}企业，处于经营发展期"
        return CustomerInsightResult(
            customer_profile=CustomerProfile(
                name=name,
                industry=industry,
                scale=scale,
                description=f"{scale}·{industry}企业，{business}",
            ),
            industry_analysis=f"{industry}行业整体处于景气区间，需关注政策导向与周期波动",
            potential_needs=[
                PotentialNeed(need="流动资金贷款", reason="日常经营周转与原材料采购需要流动资金支持"),
                PotentialNeed(need="设备融资", reason="产能扩张需购置新设备，可用设备抵押或融资租赁"),
            ],
            business_opportunities=[
                BusinessOpportunity(opportunity="供应链金融", recommendation="可切入上下游结算与应收账款融资"),
                BusinessOpportunity(opportunity="绿色金融", recommendation="新能源方向符合绿色信贷政策，可争取优惠利率"),
            ],
        )
