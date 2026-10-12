"""
ProductRecommendAgent 输出结构定义。

对应业务结果：推荐产品列表（名称/理由/条件/营销切入点）。
"""
from pydantic import BaseModel, Field


class RecommendedProduct(BaseModel):
    """单个推荐产品。"""

    name: str = Field(..., description="产品名称")
    reason: str = Field(..., description="推荐理由")
    condition: str = Field(..., description="适用条件")
    marketing_point: str = Field(..., description="营销切入点")


class ProductRecommendResult(BaseModel):
    """产品推荐结果。"""

    recommended_products: list[RecommendedProduct] = Field(..., description="推荐产品列表")
