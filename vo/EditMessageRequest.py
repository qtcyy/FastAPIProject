from pydantic import BaseModel, Field


class EditMessageRequest(BaseModel):
    thread_id: str = Field(description="线程ID")
    message_idx: int = Field(description="消息位置")
    new_content: str = Field(description="新消息")
