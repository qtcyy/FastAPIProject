import uuid
from typing import Optional

from pydantic import Field, BaseModel


class CreateChatRequest(BaseModel):
    """创建对话请求模型"""
    
    user_id: uuid.UUID = Field(description="用户ID")
    title: Optional[str] = Field(
        description="对话标题", 
        default="Untitled",
        max_length=200
    )