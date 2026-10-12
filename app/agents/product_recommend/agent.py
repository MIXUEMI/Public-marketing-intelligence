"""
ProductRecommendAgent —— 金融产品智能推荐智能体。

根据客户洞察结果 + 银行产品库，生成：推荐产品、推荐理由、适配条件、营销切入点。

- 产品查询走 app/tools/product_search.py（当前 Mock，Step 6 换 RAG，本 Agent 不改）
- LLM 调用复用 get_llm()；不可用时降级为确定性 Mock 结果
- 通过 @register_agent 注册，Supervisor 自动发现
"""
import json
import logging

from app.agents.base import BaseAgent
from app.agents.product_recommend.prompts import PRODUCT_RECOMMEND_SYSTEM_PROMPT
from app.agents.product_recommend.schemas import ProductRecommendResult, RecommendedProduct
from app.agents.registry import register_agent
from app.agents.utils import extract_json
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm
from app.tools.product_search import search_products

logger = logging.getLogger(__name__)


@register_agent
class ProductRecommendAgent(BaseAgent):
    """金融产品智能推荐智能体。"""

    name = "product_recommend"
    description = "金融产品智能推荐智能体"

    def __init__(self, llm: BaseLLMProvider | None = None) -> None:
        self.llm = llm or get_llm()

    async def execute(self, input_data: dict) -> dict:
        """执行产品推荐。

        输入可来自：
            1) CustomerInsightAgent 输出: {"customer_insight": {...}}
            2) Supervisor 原始消息: {"context": {"message": ...}}
        """
        context = self._extract_context(input_data)
        insight = context.get("customer_insight")
        message = context.get("message", "")

        query = self._build_query(insight, message)
        products = await search_products(query)
        result = await self._recommend(insight, message, products)

        logger.info("ProductRecommendAgent 完成推荐 | 产品数=%d", len(result.recommended_products))
        return {"agent": self.name, "status": "success", "result": result.model_dump()}

    # ---------- 输入处理 ----------

    @staticmethod
    def _extract_context(input_data: dict) -> dict:
        """兼容 BaseAgent 协议 {"context": ...} 与直接输入。"""
        if "context" in input_data and isinstance(input_data["context"], dict):
            return input_data["context"]
        return input_data

    @staticmethod
    def _build_query(insight: dict | None, message: str) -> str:
        """从客户洞察或原始消息中提取检索关键词。"""
        if insight:
            parts: list[str] = []
            profile = insight.get("customer_profile", {})
            if profile.get("industry"):
                parts.append(profile["industry"])
            for n in insight.get("potential_needs", []):
                if n.get("need"):
                    parts.append(n["need"])
            for o in insight.get("business_opportunities", []):
                if o.get("opportunity"):
                    parts.append(o["opportunity"])
            return " ".join(parts)
        return message

    # ---------- LLM 推荐 ----------

    def _build_messages(self, insight: dict | None, message: str, products: list[dict]) -> list[dict]:
        customer_desc = json.dumps(insight, ensure_ascii=False, indent=2) if insight else message
        user_prompt = (
            "请根据以下信息推荐金融产品。\n"
            "【客户情况】\n" + customer_desc +
            "\n【产品库】\n" + json.dumps(products, ensure_ascii=False, indent=2)
        )
        return [
            {"role": "system", "content": PRODUCT_RECOMMEND_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    async def _recommend(self, insight, message, products) -> ProductRecommendResult:
        """优先 LLM 推荐，失败降级为 Mock 结果。"""
        try:
            raw = await self.llm.agenerate(self._build_messages(insight, message, products), temperature=0.3)
            data = extract_json(raw)
            return ProductRecommendResult.model_validate(data)
        except Exception as exc:
            logger.warning("LLM 产品推荐失败，返回 Mock 结果: %s", exc)
            return self._mock_result(products)

    # ---------- Mock 兜底 ----------

    @staticmethod
    def _mock_result(products: list[dict]) -> ProductRecommendResult:
        """固定 Mock 结果（基于检索到的产品，LLM 不可用时确定性兜底）。"""
        recs = [
            RecommendedProduct(
                name=p.get("name", ""),
                reason=f"匹配客户需求：{p.get('description', '')}",
                condition=p.get("condition", "需符合我行授信条件"),
                marketing_point=p.get("marketing_point", f"以{p.get('name', '')}切入客户融资需求"),
            )
            for p in products[:3]
        ]
        if not recs:
            recs = [
                RecommendedProduct(
                    name="流动资金贷款",
                    reason="满足企业日常经营周转需求",
                    condition="经营稳定，有还款能力",
                    marketing_point="以流动资金贷款建立合作关系",
                )
            ]
        return ProductRecommendResult(recommended_products=recs)
