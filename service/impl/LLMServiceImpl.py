from typing import Any, override

from overrides import overrides

from llm.llm_chat.chat_graph import AgentClass
from llm.llm_praser.llm_out import LLMOut
from llm.llm_praser.llm_schema import Houses
from service.LLMService import LLMService
from fastapi.responses import StreamingResponse


class LLMServiceImpl(LLMService):
    def __init__(self):
        super().__init__()
        self.llm_out = LLMOut()

    @override
    async def test_service(self):
        return {"message": "test service"}

    @override
    async def get_house_info_service(self, query: str) -> Any:
        try:
            return await self.llm_out.llm_out(query)
        except Exception as e:
            return {"error": str(e)}

    @override
    async def chat_agent(self, query: str, thread_id: str) -> Any:
        config = {"configurable": {"thread_id": thread_id}}
        chat_agent = AgentClass(config)

        return StreamingResponse(
            chat_agent.agent_response(query),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @override
    async def get_thread_messages(self, thread_id: str) -> Any:
        config = {"configurable": {"thread_id": thread_id}}
        chat_agent = AgentClass(config)

        return await chat_agent.get_messages(config)

    @override
    async def clean_thread_messages(self, thread_id: str) -> Any:
        config = {"configurable": {"thread_id": thread_id}}
        chat_agent = AgentClass(config)

        result = await chat_agent.clean_messages(config)
        if result == "Success":
            return {"message": "success"}
        else:
            return {"message": "error", "error": result}
