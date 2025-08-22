import uuid
from typing import Optional

from pydantic import Field, BaseModel


class UpdateChatRequest(BaseModel):
    """更新对话请求模型"""
    
    thread_id: uuid.UUID = Field(description="对话线程ID")
    title: Optional[str] = Field(
        description="对话标题", 
        default=None,
        max_length=200
    )
    stared: Optional[bool] = Field(description="收藏状态", default=None)