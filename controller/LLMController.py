from fastapi import APIRouter

from service.impl.LLMServiceImpl import LLMService, LLMServiceImpl
from vo.ChatAgentRequest import ChatAgentRequest
from vo.HouseInfoRequest import HouseInfoRequest


class LLMController:
    def __init__(self):
        self.llm_service = LLMServiceImpl()
        self.router = APIRouter()
        self._setup_router()

    def _setup_router(self):
        self.router.get("/hello")(self.hello)
        self.router.get("/test")(self.test)
        self.router.post("/house/")(self.get_house_info)
        self.router.post("/chat_agent")(self.chat_agent)
        self.router.get("/chat/messages/{thread_id}")(self.get_chat_messages)
        self.router.delete("/chat/messages/{thread_id}")(self.clean_thread_messages)

    async def hello(self):
        return {"message": "Hello World!"}

    async def test(self):
        return await self.llm_service.test_service()

    async def get_house_info(self, request: HouseInfoRequest):
        return await self.llm_service.get_house_info_service(request.query)

    async def chat_agent(self, request: ChatAgentRequest):
        return await self.llm_service.chat_agent(
            query=request.query, thread_id=request.thread_id
        )

    async def get_chat_messages(self, thread_id: str):
        return await self.llm_service.get_thread_messages(thread_id=thread_id)

    async def clean_thread_messages(self, thread_id: str):
        return await self.llm_service.clean_thread_messages(thread_id=thread_id)
