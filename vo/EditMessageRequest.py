from pydantic import BaseModel, Field


class BaseEditMessageRequest(BaseModel):
    thread_id: str = Field(description="线程ID")
    new_content: str = Field(description="新消息")


class EditMessageRequest(BaseEditMessageRequest):
    message_idx: int = Field(description="消息位置")


class EditWithIDRequest(BaseEditMessageRequest):
    message_id: str = Field(description="消息ID")
