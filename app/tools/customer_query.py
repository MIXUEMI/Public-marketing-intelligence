"""
企业客户数据查询工具（Mock 实现）。

未来替换为：工商信息接口 / CRM 系统 / 银行核心数据接口。
当前返回内置样例数据，保证系统无外部依赖也能运行。
"""
import logging

logger = logging.getLogger(__name__)


def get_customer_profile(customer_name: str | None = None) -> dict:
    """查询企业客户基本信息（Mock）。

    Args:
        customer_name: 企业名称；为空时返回默认样例。

    Returns:
        企业信息 dict：customer_name / industry / basic_info / business
    """
    name = (customer_name or "杭州某制造企业").strip()

    # 简单样例匹配：按名称关键词区分行业，否则默认制造企业
    if "科技" in name:
        industry = "新能源科技"
        business = "主营新能源电池系统研发与集成，处于快速成长期"
    else:
        industry = "新能源制造"
        business = "主营锂电池模组生产，处于产能扩张期"

    logger.info("查询企业信息（Mock）| 企业=%s | 行业=%s", name, industry)
    return {
        "customer_name": name,
        "industry": industry,
        "basic_info": {"scale": "中型企业", "location": "杭州", "employees": "500-2000人"},
        "business": business,
    }
