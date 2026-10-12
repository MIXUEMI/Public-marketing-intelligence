"""
MarketingAgent —— 营销方案生成智能体。

根据客户洞察结果 + 产品推荐结果，生成：拜访方案、开场话术、需求挖掘、产品介绍、跟进计划。

- 只负责营销内容生成，不重新分析客户、不重新推荐产品
- LLM 调用复用 get_llm()；不可用时降级为固定 Mock 营销方案
- 输出为 Markdown（content）+ 分节（sections）
"""
import json
import logging

from app.agents.base import BaseAgent
from app.agents.marketing.prompts import MARKETING_SYSTEM_PROMPT
from app.agents.marketing.schemas import MarketingResult, MarketingSections
from app.agents.registry import register_agent
from app.agents.utils import extract_json
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm

logger = logging.getLogger(__name__)


@register_agent
class MarketingAgent(BaseAgent):
    """营销方案生成智能体。"""

    name = "marketing"
    description = "营销方案生成智能体"

    def __init__(self, llm: BaseLLMProvider | None = None) -> None:
        self.llm = llm or get_llm()

    async def execute(self, input_data: dict) -> dict:
        """生成营销方案。输入为前序两个 Agent 的结果。"""
        context = self._extract_context(input_data)
        insight = context.get("customer_insight") or {}
        recommend = context.get("product_recommend") or {}

        result = await self._generate(insight, recommend)
        logger.info("MarketingAgent 生成方案 | 长度=%d", len(result.content))
        return {"agent": self.name, "status": "success", "result": result.model_dump()}

    # ---------- 输入处理 ----------

    @staticmethod
    def _extract_context(input_data: dict) -> dict:
        """兼容 BaseAgent 协议 {"context": ...} 与直接输入。"""
        if "context" in input_data and isinstance(input_data["context"], dict):
            return input_data["context"]
        return input_data

    # ---------- LLM 生成 ----------

    def _build_messages(self, insight: dict, recommend: dict) -> list[dict]:
        user_prompt = (
            "请根据以下客户分析与产品推荐，生成营销方案。\n"
            "【客户洞察】\n" + json.dumps(insight, ensure_ascii=False, indent=2) +
            "\n【产品推荐】\n" + json.dumps(recommend, ensure_ascii=False, indent=2)
        )
        return [
            {"role": "system", "content": MARKETING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    async def _generate(self, insight: dict, recommend: dict) -> MarketingResult:
        """优先 LLM 生成分节内容，失败降级为 Mock。"""
        try:
            raw = await self.llm.agenerate(self._build_messages(insight, recommend), temperature=0.4)
            data = extract_json(raw)
            sections = MarketingSections.model_validate(data)
        except Exception as exc:
            logger.warning("LLM 营销生成失败，返回 Mock 方案: %s", exc)
            sections = self._mock_sections(insight, recommend)
        content = self._assemble_content(sections)
        return MarketingResult(content=content, sections=sections)

    # ---------- 组装 Markdown ----------

    @staticmethod
    def _assemble_content(sections: MarketingSections) -> str:
        """将分节内容组装为完整 Markdown 方案。"""
        return "\n\n".join([
            "# 客户拜访方案",
            "## 一、拜访目标", sections.visit_plan,
            "## 二、沟通开场", sections.opening_script,
            "## 三、需求挖掘", sections.need_questions,
            "## 四、产品介绍", sections.product_intro,
            "## 五、后续跟进", sections.follow_up,
        ])

    # ---------- Mock 兜底 ----------

    @staticmethod
    def _mock_sections(insight: dict, recommend: dict) -> MarketingSections:
        """固定 Mock 营销方案（LLM 不可用时确定性兜底）。"""
        profile = (insight or {}).get("customer_profile") or {}
        name = profile.get("name") or "某制造企业"
        products = (recommend or {}).get("recommended_products") or []
        product_name = products[0].get("name") if products else "流动资金贷款"

        return MarketingSections(
            visit_plan=f"拜访目标：了解{name}的经营状况与扩产资金需求，建立信任关系",
            opening_script="开场：\"了解到贵公司近期扩大生产规模，业务发展势头良好，今天想就资金安排做一次交流。\"",
            need_questions="需求挖掘：\"目前企业在原材料采购、生产周转方面是否存在资金压力？扩产设备投入方面是否有融资需求？\"",
            product_intro=f"产品介绍：可优先推荐「{product_name}」，满足企业阶段性资金需求，期限灵活、审批高效。",
            follow_up="跟进：梳理本次沟通要点，3 个工作日内回访，持续维护客户关系",
        )
