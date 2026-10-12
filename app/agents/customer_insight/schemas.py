"""
CustomerInsightAgent 输出结构定义。

对应业务结果：客户画像、行业分析、潜在金融需求、业务机会。
"""
from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    """企业基本画像。"""

    name: str = Field(..., description="企业名称")
    industry: str = Field(..., description="所属行业")
    scale: str = Field(..., description="企业规模")
    description: str = Field(..., description="画像描述")


class PotentialNeed(BaseModel):
    """潜在金融需求。"""

    need: str = Field(..., description="需求类型")
    reason: str = Field(..., description="需求原因")


class BusinessOpportunity(BaseModel):
    """业务/商机机会。"""

    opportunity: str = Field(..., description="机会点")
    recommendation: str = Field(..., description="营销建议")


class CustomerInsightResult(BaseModel):
    """客户洞察分析结果。"""

    customer_profile: CustomerProfile
    industry_analysis: str
    potential_needs: list[PotentialNeed]
    business_opportunities: list[BusinessOpportunity]
