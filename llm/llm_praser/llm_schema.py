from typing import Optional, TypedDict, Sequence

from pydantic import BaseModel, Field


class House(BaseModel):
    location: str = Field(description="房屋的位置信息")
    area: str = Field(description="房屋的面积信息")
    price: float = Field(description="每平方米的价格（单位：万元）")
    star: Optional[str] = Field(description="房屋的热门程度（可选参数）")


class Houses(BaseModel):
    house: Sequence[House] = Field(description="房屋信息列表")
    count: int = Field(description="统计出的房屋数量")
    average_price: float = Field(description="每平方米的平均价格（单位：万元）")


class GraphState(TypedDict):
    query: str
    format_instructions: str
    llm_output: str
    prompt: str
    parsed_result: Optional[Houses]
    error: Optional[str]
