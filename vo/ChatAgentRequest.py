from pydantic import BaseModel, Field


class ChatAgentRequest(BaseModel):
    thread_id: str = Field(description="线程id")
    query: str = Field(description="问题")
