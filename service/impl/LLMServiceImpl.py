import uuid
from typing import Any, override, List

from langchain_core.messages import BaseMessage
from sqlmodel import select

from dao.database import get_session, create_db_and_tables
from dao.entity.chat_models import Chat
from dao.entity.stared_chat import StaredChat
from llm.llm_chat.chat_graph import AgentClass
from llm.llm_chat_with_tools.chatbot.ChatBot import ChatBot
from llm.llm_praser.llm_out import LLMOut
from llm.llm_praser.llm_schema import Houses
from service.LLMService import LLMService
from fastapi.responses import StreamingResponse

from vo.StarChatRequest import StarChatRequest


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
        self,
        query: str,
        thread_id: str,
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        summary_with_llm: bool = False,
    ) -> Any:
        custom_chatbot = ChatBot(model=model)
        return StreamingResponse(
            custom_chatbot.generate(
                query=query, thread_id=thread_id, summary_with_llm=summary_with_llm
            ),
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

    @override
    async def get_message_by_id(self, thread_id: str, message_id: str) -> BaseMessage:
        """
        根据消息ID获取指定消息
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :return: 消息对象
        """
        return await self.chatbot.get_message_by_id(thread_id, message_id)

    @override
    async def generate_chat_name(self, thread_id: str) -> str:
        """
        为对话生成智能标题
        :param thread_id: 线程ID
        :return: 生成的对话标题
        """
        chatbot = ChatBot(model="qwen-turbo-latest")

        return await chatbot.named_chat(thread_id)

    @override
    async def delete_threads_batch(self, thread_ids: List[str]) -> dict[str, Any]:
        """
        批量删除多个对话线程
        :param thread_ids: 线程ID列表
        :return: 删除状态
        """
        if not thread_ids:
            return {"message": "error", "error": "No thread IDs provided"}

        state = await self.chatbot.delete_history_batch(thread_ids)
        if state:
            return {
                "message": "success",
                "deleted_count": len(thread_ids),
                "thread_ids": thread_ids,
            }
        else:
            return {
                "message": "error",
                "error": "Failed to delete threads",
                "thread_ids": thread_ids,
            }

    @override
    async def create_chat(self, user_id: uuid.UUID) -> dict[str, Any]:
        """
        创建新的对话记录

        此方法为指定用户创建一个新的对话线程记录在数据库中。
        对话记录包含用户ID、创建时间等基本信息，为后续的消息存储和管理提供基础。

        Args:
            user_id (uuid.UUID): 用户的唯一标识符，用于关联对话所有者

        Returns:
            dict[str, Any]: 操作结果字典，包含以下字段：
                - message (str): 操作状态消息 ("success" | "error")
                - status (bool): 操作是否成功 (True | False)
                - chat (Chat, 可选): 成功时返回创建的对话对象
                - error (str, 可选): 失败时返回错误信息

        Raises:
            Exception: 数据库操作异常时抛出，会被捕获并返回错误信息

        Example:
            >>> result = await service.create_chat(user_id=uuid4())
            >>> if result["status"]:
            >>>     print(f"创建成功，对话ID: {result['chat'].id}")
            >>> else:
            >>>     print(f"创建失败: {result['error']}")
        """
        try:
            with get_session() as session:
                chat = Chat(user_id=user_id)
                session.add(chat)

                session.commit()
            return {"message": "success", "status": True, "chat": chat}
        except Exception as e:
            error_info = f"Error on create chat:\n{e}"
            print(error_info)

            return {"message": "error", "status": False, "error": error_info}

    @override
    async def get_chat(self, user_id: uuid.UUID) -> dict[str, Any]:
        """
        获取指定用户的所有对话记录

        查询数据库中属于指定用户的所有对话记录，返回完整的对话列表。
        这个方法通常用于展示用户的对话历史或对话管理界面。

        Args:
            user_id (uuid.UUID): 用户的唯一标识符，用于筛选对话记录

        Returns:
            dict[str, Any]: 查询结果字典，包含以下字段：
                - message (str): 操作状态消息 ("success" | "error")
                - status (bool): 操作是否成功 (True | False)
                - chats (List[Chat], 可选): 成功时返回对话对象列表
                - count (int, 可选): 成功时返回对话数量
                - error (str, 可选): 失败时返回错误信息

        Raises:
            Exception: 数据库查询异常时抛出，会被捕获并返回错误信息

        Example:
            >>> result = await service.get_chat(user_id=uuid4())
            >>> if result["status"]:
            >>>     print(f"找到 {result['count']} 个对话")
            >>>     for chat in result["chats"]:
            >>>         print(f"对话ID: {chat.id}, 创建时间: {chat.create_time}")
        """
        try:
            with get_session() as session:
                statement = select(Chat).where(Chat.user_id == user_id)
                chats: List[Chat] = session.exec(statement)
            return {
                "message": "success",
                "status": True,
                "chats": chats,
                "count": len(chats),
            }
        except Exception as e:
            error_info = f"Error on delete chat:\n{e}"
            print(error_info)

            return {"message": "error", "status": False, "error": error_info}

    @override
    async def delete_chat(self, thread_id: uuid.UUID):
        """
        删除指定的对话记录

        此方法会从数据库中删除指定ID的对话记录，并同时清理相关的聊天历史。
        删除操作包括数据库记录删除和聊天机器人历史记录清理两个步骤。

        Args:
            thread_id (uuid.UUID): 要删除的对话线程ID

        Returns:
            dict[str, Any]: 删除结果字典，包含以下字段：
                - message (str): 操作状态消息 ("success" | "error" | "Chat does not exist")
                - status (bool): 操作是否成功 (True | False)
                - error (str, 可选): 失败时返回错误详情

        Raises:
            Exception: 数据库操作或历史记录清理异常时抛出，会被捕获并返回错误信息

        Note:
            删除操作是不可逆的，会同时清除数据库记录和聊天历史记录

        Example:
            >>> result = await service.delete_chat(thread_id=chat_uuid)
            >>> if result["status"]:
            >>>     print("对话删除成功")
            >>> else:
            >>>     print(f"删除失败: {result.get('message', '未知错误')}")
        """
        try:
            with get_session() as session:
                statement = select(Chat).where(Chat.id == thread_id).limit(1)
                chat = session.exec(statement)
                if not chat:
                    return {"message": "Chat does not exist", "status": False}

                session.delete(chat)
                session.commit()

            await self.chatbot.delete_history(thread_id)
            return {"message": "success", "status": True}
        except Exception as e:
            error_info = f"Error on delete chat:\n{e}"
            print(error_info)

            return {"message": "error", "status": False, "error": error_info}

    @override
    async def update_chat(self, chat: Chat) -> dict[str, Any]:
        """
        更新对话记录信息

        此方法用于更新已存在的对话记录信息。会先验证对话是否存在，
        然后使用传入的Chat对象更新数据库中的对应记录。

        Args:
            chat (Chat): 包含更新信息的对话对象，必须包含有效的ID

        Returns:
            dict[str, Any]: 更新结果字典，包含以下字段：
                - message (str): 操作状态消息 ("success" | "error" | "Chat does not exist")
                - status (bool): 操作是否成功 (True | False)
                - error (str, 可选): 失败时返回错误详情

        Raises:
            Exception: 数据库操作异常时抛出，会被捕获并返回错误信息

        Note:
            更新操作会自动触发timestamp_mixin的update_time字段更新

        Example:
            >>> chat.title = "新的对话标题"
            >>> result = await service.update_chat(chat)
            >>> if result["status"]:
            >>>     print("对话更新成功")
            >>> else:
            >>>     print(f"更新失败: {result.get('message', '未知错误')}")
        """
        try:
            with get_session() as session:
                statement = select(Chat).where(Chat.id == chat.id).exists()
                if not session.exec(statement):
                    return {
                        "message": "Chat does not exist",
                        "status": False,
                    }
                session.add(chat)
                session.commit()

            return {"message": "success", "status": True}
        except Exception as e:
            error_info = f"Error on create chat:\n{e}"
            print(error_info)

            return {"message": "error", "status": False, "error": error_info}

    @override
    async def star_chat(self, thread_id: uuid.UUID) -> dict[str, Any]:
        """
        收藏对话线程

        Args:
            thread_id: 要收藏的对话线程ID
            :type thread_id: uuid.UUID

        Returns:
            dict: 操作结果，包含状态信息
        """
        try:
            # 使用数据库会话管理器确保事务安全
            with get_session() as session:
                # 检查是否已经收藏过该线程
                existing = (
                    session.query(StaredChat)
                    .filter(StaredChat.thread_id == thread_id)
                    .first()
                )

                if existing:
                    return {
                        "message": "already_starred",
                        "status": False,
                        "error": "该对话已经收藏过了",
                    }

                # 创建新的收藏记录
                entity = StaredChat(thread_id=thread_id)
                session.add(entity)
                session.commit()

            return {"message": "success", "status": True}

        except Exception as e:
            # 记录错误日志
            print(f"收藏对话失败 - thread_id: {thread_id}, 错误: {str(e)}")
            return {
                "message": "error",
                "status": False,
                "error": f"收藏对话时发生错误: {str(e)}",
            }

    @override
    async def toggle_star_chat(self, thread_id: uuid.UUID) -> dict[str, Any]:
        """
        切换对话的收藏状态

        此方法用于切换指定对话的收藏状态（收藏/取消收藏）。
        如果当前是收藏状态则取消收藏，如果未收藏则添加收藏。

        Args:
            thread_id (uuid.UUID): 要操作的对话线程ID

        Returns:
            dict[str, Any]: 操作结果字典，包含以下字段：
                - message (str): 操作状态消息 ("success" | "error" | 对话不存在消息)
                - status (bool): 操作是否成功 (True | False)
                - current_state (bool, 可选): 成功时返回当前收藏状态 (True=已收藏, False=未收藏)
                - error (str, 可选): 失败时返回错误详情

        Raises:
            Exception: 数据库操作异常时抛出，会被捕获并返回错误信息

        Note:
            此方法直接修改Chat对象的stared字段，与star_chat方法使用不同的数据表

        Example:
            >>> result = await service.toggle_star_chat(thread_id=chat_uuid)
            >>> if result["status"]:
            >>>     state = "已收藏" if result["current_state"] else "已取消收藏"
            >>>     print(f"操作成功，当前状态: {state}")
        """
        try:
            with get_session() as session:
                statement = select(Chat).where(Chat.id == thread_id)
                chat: Chat = session.exec(statement)
                if not chat:
                    return {
                        "message": f"Chat {thread_id} is not exist",
                        "status": False,
                    }

                chat.stared = not chat.stared

                session.add(chat)
                session.commit()
            return {"message": "success", "status": False, "current_state": chat.stared}

        except Exception as e:
            print(f"Error on toggle star chat:\n{e}")
            return {
                "message": "error",
                "status": False,
                "error": f"Error on toggle star chat:\n{e}",
            }

    @override
    async def get_stared_chat(self) -> dict[str, Any]:
        """
        获取所有收藏的对话线程ID列表

        Returns:
            dict: 包含收藏的对话ID列表、数量和状态信息
        """
        try:
            stared_chat_list: List[StaredChat] = []

            # 使用数据库会话管理器进行查询
            with get_session() as session:
                # 按创建时间排序查询所有收藏记录
                statement = session.query(StaredChat).order_by(StaredChat.create_at)
                stared_chat_list = session.exec(statement).all()

            # 提取所有收藏的对话线程ID
            chat_ids: List[uuid.UUID] = [
                entity.thread_id for entity in stared_chat_list
            ]

            return {
                "message": "success",
                "status": True,
                "chat_ids": chat_ids,
                "count": len(chat_ids),
            }

        except Exception as e:
            # 记录错误日志并返回错误信息
            print(f"获取收藏对话列表失败，错误: {str(e)}")
            return {
                "message": "error",
                "status": False,
                "error": f"获取收藏列表时发生错误: {str(e)}",
                "chat_ids": [],
                "count": 0,
            }
