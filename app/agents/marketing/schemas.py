"""
MarketingAgent 输出结构定义。

营销输出不是 JSON 列表，而是 Markdown 方案：
- content: 完整 Markdown 营销方案
- sections: 分节内容（拜访目标/开场/需求挖掘/产品介绍/跟进）
"""
from pydantic import BaseModel, Field


class MarketingSections(BaseModel):
    """营销方案分节内容。"""

    visit_plan: str = Field(..., description="拜访目标与计划")
    opening_script: str = Field(..., description="客户沟通开场话术")
    need_questions: str = Field(..., description="需求挖掘问题")
    product_intro: str = Field(..., description="产品价值介绍")
    follow_up: str = Field(..., description="后续跟进计划")


class MarketingResult(BaseModel):
    """营销方案生成结果。"""

    content: str = Field(..., description="完整 Markdown 营销方案")
    sections: MarketingSections = Field(..., description="分节内容")
