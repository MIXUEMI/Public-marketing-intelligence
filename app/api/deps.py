"""
依赖注入：提供各 Service / Repository 的单例实例。
"""
from app.repositories.conversation import ConversationRepository
from app.repositories.customer import CustomerRepository
from app.repositories.execution import ExecutionRepository
from app.repositories.recommendation import RecommendationRepository
from app.services.chat_service import ChatService

# 模块级单例，避免每次请求重建
_chat_service = ChatService()
_customer_repo = CustomerRepository()
_conversation_repo = ConversationRepository()
_recommendation_repo = RecommendationRepository()
_execution_repo = ExecutionRepository()


def get_chat_service() -> ChatService:
    """获取 ChatService 单例。"""
    return _chat_service


def get_customer_repo() -> CustomerRepository:
    """获取 CustomerRepository 单例。"""
    return _customer_repo


def get_conversation_repo() -> ConversationRepository:
    """获取 ConversationRepository 单例。"""
    return _conversation_repo


def get_recommendation_repo() -> RecommendationRepository:
    """获取 RecommendationRepository 单例。"""
    return _recommendation_repo


def get_execution_repo() -> ExecutionRepository:
    """获取 ExecutionRepository 单例。"""
    return _execution_repo
