from typing import Optional

from pydantic import BaseModel, Field


class BaseEditMessageRequest(BaseModel):
    thread_id: str = Field(description="线程ID")
    new_content: Optional[str] = Field(description="新消息", default="")


class EditMessageRequest(BaseEditMessageRequest):
    message_idx: int = Field(description="消息位置")


class EditWithIDRequest(BaseEditMessageRequest):
    message_id: str = Field(description="消息ID")
