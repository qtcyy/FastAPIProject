import uuid

from pydantic import Field, BaseModel


class StarChatRequest(BaseModel):
    thread_id: uuid.UUID = Field(description="线程ID")
