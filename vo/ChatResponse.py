import uuid
from typing import Optional, Any, List

from pydantic import Field, BaseModel

from dao.entity.chat_models import Chat


class ChatResponse(BaseModel):
    """标准化聊天操作响应模型"""
    
    message: str = Field(description="状态消息")
    status: bool = Field(description="操作状态")
    data: Optional[Any] = Field(description="返回数据", default=None)
    error: Optional[str] = Field(description="错误信息", default=None)


class ChatListResponse(BaseModel):
    """对话列表响应模型"""
    
    message: str = Field(description="状态消息")
    status: bool = Field(description="操作状态") 
    chats: Optional[List[dict]] = Field(description="对话列表", default=None)
    count: Optional[int] = Field(description="对话数量", default=0)
    error: Optional[str] = Field(description="错误信息", default=None)


class StarredChatsResponse(BaseModel):
    """收藏对话响应模型"""
    
    message: str = Field(description="状态消息")
    status: bool = Field(description="操作状态")
    chat_ids: Optional[List[uuid.UUID]] = Field(description="收藏的对话ID列表", default=None)
    count: Optional[int] = Field(description="收藏数量", default=0)
    error: Optional[str] = Field(description="错误信息", default=None)