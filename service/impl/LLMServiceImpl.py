from typing import Any, override, List

from langchain_core.messages import BaseMessage

from llm.llm_chat.chat_graph import AgentClass
from llm.llm_chat_with_tools.chatbot.ChatBot import ChatBot
from llm.llm_praser.llm_out import LLMOut
from llm.llm_praser.llm_schema import Houses
from service.LLMService import LLMService
from fastapi.responses import StreamingResponse


class LLMServiceImpl(LLMService):
    def __init__(self):
        super().__init__()
        self.llm_out = LLMOut()
        self.chatbot = ChatBot()

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

    @override
    async def chat_with_tools(
        self, query: str, thread_id: str, model: str = "Qwen/Qwen2.5-7B-Instruct", summary_with_llm: bool = False
    ) -> Any:
        custom_chatbot = ChatBot(model=model)
        return StreamingResponse(
            custom_chatbot.generate(query=query, thread_id=thread_id, summary_with_llm=summary_with_llm),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @override
    async def get_history(self, thread_id: str) -> List[BaseMessage]:
        """
        获取历史记录
        :param thread_id: 线程ID
        :return: 历史记录
        :type: List[str]
        """
        return await self.chatbot.get_history(thread_id=thread_id)

    @override
    async def delete_thread(self, thread_id: str) -> dict[str, Any]:
        """
        删除线程
        :param thread_id: 线程ID
        :return: 删除状态
        """
        state = await self.chatbot.delete_history(thread_id=thread_id)
        if state:
            return {"message": "success"}
        else:
            return {"message": "error"}

    @override
    async def edit_message(
        self, thread_id: str, message_idx: int, new_content: str
    ) -> dict[str, Any]:
        """
        编辑消息服务
        :param thread_id: 线程ID
        :param message_idx: 消息位置
        :param new_content: 新内容
        :return: 更新状态
        """
        status = await self.chatbot.edit_message(thread_id, message_idx, new_content)
        if status:
            return {"message": "success", "status": True}
        else:
            return {"message": "failed", "status": False}

    @override
    async def edit_message_with_id(
        self, thread_id: str, message_id: str, new_content: str
    ) -> dict[str, Any]:
        """
        根据消息ID编辑消息
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :param new_content: 新消息内容
        :return: 修改状态
        """
        status = await self.chatbot.edit_message_with_id(
            thread_id, message_id, new_content
        )
        if status:
            return {"message": "success", "status": True}
        else:
            return {"message": "failed", "status": False}

    @override
    async def delete_message(self, thread_id: str, message_idx: int) -> dict[str, Any]:
        """
        删除消息
        :param thread_id: 线程ID
        :param message_idx:
        :return: 删除状态
        """
        status = await self.chatbot.delete_message(thread_id, message_idx)
        if status:
            return {"message": "success", "status": True}
        else:
            return {"message": "failed", "status": False}

    @override
    async def delete_message_with_id(
        self, thread_id: str, message_id: str
    ) -> dict[str, Any]:
        """
        根据消息ID删除消息
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :return: 删除状态
        """
        status = await self.chatbot.delete_message_with_id(thread_id, message_id)
        if status:
            return {"message": "success", "status": True}
        else:
            return {"message": "failed", "status": False}

    @override
    async def delete_messages_after_with_id(
        self, thread_id: str, message_id: str
    ) -> dict[str, Any]:
        """
        删除指定消息后面的所有消息，包括该消息
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :return: 删除状态
        """
        status = await self.chatbot.delete_messages_after_with_id(thread_id, message_id)
        if status:
            return {"message": "success", "status": True}
        else:
            return {"message": "failed", "status": False}
