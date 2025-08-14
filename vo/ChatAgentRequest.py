from typing import Optional

from pydantic import BaseModel, Field


class ChatAgentRequest(BaseModel):
    thread_id: str = Field(description="线程id")
    query: str = Field(description="问题")
    model: Optional[str] = Field(
        description="模型名称", default="Qwen/Qwen2.5-7B-Instruct"
    )
    summary_with_llm: bool = Field(
        description="是否启用LLM智能总结功能", default=False
    )
