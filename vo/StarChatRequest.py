import uuid

from pydantic import Field, BaseModel


class StartChatRequest(BaseModel):
    thread_id: uuid.UUID = Field(description="线程ID")
