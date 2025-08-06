from pydantic import BaseModel, Field


class HouseInfoRequest(BaseModel):
    query: str = Field(alias="query", description="问题")
