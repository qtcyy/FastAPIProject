from typing import List, Any, Union

from fastapi import APIRouter, HTTPException
from langchain_core.messages import BaseMessage

from service.impl.LLMServiceImpl import LLMService, LLMServiceImpl
from vo.ChatAgentRequest import ChatAgentRequest
from vo.EditMessageRequest import EditMessageRequest, EditWithIDRequest
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
        self.router.get("/chat/message/{thread_id}/{message_id}")(
            self.get_message_by_id
        )
        self.router.delete("/chat/history/{thread_id}")(self.delete_thread)
        self.router.post("/chat/history/edit")(self.edit_message)
        self.router.post("/chat/history/edit/id")(self.edit_message_with_id)
        self.router.post("/chat/history/delete")(self.delete_message)
        self.router.post("/chat/history/delete/id")(self.delete_message_with_id)
        self.router.post("/chat/history/delete/after")(
            self.delete_messages_after_with_id
        )

    async def get_house_info(self, request: HouseInfoRequest):
        return await self.llm_service.get_house_info_service(request.query)

    async def chat_with_tools(self, request: ChatAgentRequest):
        """
        添加工具的对话
        :param request: 对话请求
        :return: sse返回回复内容
        """
        return await self.llm_service.chat_with_tools(
            query=request.query,
            thread_id=request.thread_id,
            model=request.model,
            summary_with_llm=request.summary_with_llm,
        )

    async def get_history(self, thread_id: str) -> List[BaseMessage]:
        """
        获取聊天历史记录
        :param thread_id: 线程ID
        :return: 历史记录
        """
        return await self.llm_service.get_history(thread_id=thread_id)

    async def get_message_by_id(self, thread_id: str, message_id: str) -> BaseMessage:
        """
        根据消息ID获取指定消息
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :return: 消息对象
        """
        message = await self.llm_service.get_message_by_id(
            thread_id=thread_id, message_id=message_id
        )
        if message is None:
            raise HTTPException(
                status_code=404,
                detail=f"Message with ID {message_id} not found in thread {thread_id}",
            )
        return message

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

    async def edit_message_with_id(self, request: EditWithIDRequest) -> dict[str, Any]:
        """
        根据消息ID编辑消息
        :param request: 请求体
        :return: 请求状态
        """
        return await self.llm_service.edit_message_with_id(
            request.thread_id, request.message_id, request.new_content
        )

    async def delete_message(self, request: EditMessageRequest) -> dict[str, Any]:
        """
        删除消息
        :param request: 请求体
        :return: 请求状态
        """
        return await self.llm_service.delete_message(
            request.thread_id, request.message_idx
        )

    async def delete_message_with_id(
        self, request: EditWithIDRequest
    ) -> dict[str, Any]:
        """
        根据消息ID删除消息
        :param request: 请求体
        :return: 请求状态
        """
        return await self.llm_service.delete_message_with_id(
            request.thread_id, request.message_id
        )

    async def delete_messages_after_with_id(
        self, request: EditWithIDRequest
    ) -> dict[str, Any]:
        """
        删除指定消息后面的所有消息，包括该消息
        :param request: 请求体
        :return: 请求状态
        """
        return await self.llm_service.delete_messages_after_with_id(
            request.thread_id, request.message_id
        )
