"""
对话服务层（ChatService）。

职责：承接 API 层请求，编排 SupervisorAgent，并落地持久化链路：
    用户请求 → 创建 Session → 保存 Message → 执行 Workflow → 保存结果。
数据库关闭时所有持久化自动降级为 no-op，服务仍可运行。
"""
import logging

from app.agents.supervisor.agent import SupervisorAgent
from app.repositories.conversation import ConversationRepository
from app.repositories.customer import CustomerRepository
from app.repositories.recommendation import RecommendationRepository
from app.schemas.chat import ChatResponse

logger = logging.getLogger(__name__)


class ChatService:
    """统一对话服务入口。"""

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.conversation_repo = ConversationRepository()
        self.customer_repo = CustomerRepository()
        self.recommendation_repo = RecommendationRepository()

    async def process_message(self, message: str, session_id: str) -> ChatResponse:
        """处理一条用户消息：创建会话 → 存消息 → 执行 → 存结果。"""
        logger.info("ChatService 处理消息 | session_id=%s", session_id)

        # 1. 创建（或复用）会话
        await self.conversation_repo.create_session(session_id)
        # 2. 保存用户消息
        await self.conversation_repo.save_message(session_id, "user", message)

        # 3. 执行 Workflow（Agent 执行记录由 executor Hook 自动落库）
        result = await self.supervisor.process(message, session_id)

        # 4. 保存结果（助手回复 / 客户洞察 / 推荐）
        reply = self._summarize(result)
        await self._persist_results(session_id, result, reply)

        return ChatResponse(
            session_id=session_id,
            message=reply,
            agent="supervisor",
            status="success",
            intent=result.get("intent", ""),
            results=result.get("results", []),
        )

    async def _persist_results(self, session_id: str, result: dict, reply: str) -> None:
        """持久化执行结果：助手消息 + 客户洞察 + 推荐记录。"""
        intent = result.get("intent", "")

        # 助手回复
        await self.conversation_repo.save_message(session_id, "assistant", reply, intent=intent)

        # 客户洞察 → 客户主数据
        customer_id = None
        insight = self._find_result(result, "customer_insight")
        if insight:
            customer_id = await self.customer_repo.save_customer_insight(insight)

        # 产品推荐 → 推荐记录
        recommend = self._find_result(result, "product_recommend")
        if recommend:
            products = recommend.get("recommended_products", [])
            reason = "；".join(
                f"{p.get('name', '')}: {p.get('reason', '')}"
                for p in products
                if isinstance(p, dict) and p.get("reason")
            )
            await self.recommendation_repo.save(
                session_id=session_id,
                customer_id=customer_id,
                products=products,
                reason=reason or f"intent={intent}",
                agent_trace={"intent": intent, "agents": [r["agent"] for r in result.get("results", [])]},
            )

    @staticmethod
    def _find_result(result: dict, agent_name: str) -> dict | None:
        """从执行结果中提取某个 Agent 的成功产出。"""
        for r in result.get("results", []):
            if r.get("agent") == agent_name and r.get("status") == "success":
                return r.get("result")
        return None

    @staticmethod
    def _summarize(result: dict) -> str:
        """将 Supervisor 结构化结果转为可读文本（供前端展示）。"""
        lines = [f"意图识别：{result['intent']}"]
        for r in result.get("results", []):
            agent = r["agent"]
            status = r["status"]
            detail = r.get("result", {}).get("detail", "")
            suffix = f"：{detail}" if detail else ""
            lines.append(f"  · [{status}] {agent}{suffix}")
        return "\n".join(lines)
