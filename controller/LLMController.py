from typing import List, Any

from fastapi import APIRouter
from langchain_core.messages import BaseMessage

from service.impl.LLMServiceImpl import LLMService, LLMServiceImpl
from vo.ChatAgentRequest import ChatAgentRequest
from vo.EditMessageRequest import EditMessageRequest
from vo.HouseInfoRequest import HouseInfoRequest


class LLMController:
    def __init__(self):
        self.llm_service = LLMServiceImpl()
        self.router = APIRouter()
        self._setup_router()

    def _setup_router(self):
        self.router.post("/house/")(self.get_house_info)
        self.router.post("/chat/tools")(self.chat_with_tools)
        self.router.get("/chat/history/{thread_id}")(self.get_history)
        self.router.delete("/chat/history/{thread_id}")(self.delete_thread)
        self.router.post("/chat/history/edit")(self.edit_message)

    async def get_house_info(self, request: HouseInfoRequest):
        return await self.llm_service.get_house_info_service(request.query)

    async def chat_with_tools(self, request: ChatAgentRequest):
        """
        添加工具的对话
        :param request: 对话请求
        :return: sse返回回复内容
        """
        return await self.llm_service.chat_with_tools(
            query=request.query, thread_id=request.thread_id, model=request.model
        )

    async def get_history(self, thread_id: str) -> List[BaseMessage]:
        """
        获取聊天历史记录
        :param thread_id: 线程ID
        :return: 历史记录
        """
        return await self.llm_service.get_history(thread_id=thread_id)

    async def delete_thread(self, thread_id: str) -> dict[str, Any]:
        """
        删除线程
        :param thread_id: 线程ID
        :return: 删除状态
        """
        return await self.llm_service.delete_thread(thread_id=thread_id)

    async def edit_message(self, request: EditMessageRequest) -> dict[str, Any]:
        """
        编辑消息
        :param request: 请求体
        :return: 请求状态
        """
        return await self.llm_service.edit_message(
            request.thread_id, request.message_idx, request.new_content
        )
