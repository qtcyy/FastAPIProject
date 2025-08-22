import uuid
from typing import List, Any, Union

from fastapi import APIRouter, HTTPException
from langchain_core.messages import BaseMessage

from service.impl.LLMServiceImpl import LLMService, LLMServiceImpl
from vo.ChatAgentRequest import ChatAgentRequest
from vo.EditMessageRequest import EditMessageRequest, EditWithIDRequest
from vo.HouseInfoRequest import HouseInfoRequest
from vo.BatchDeleteRequest import BatchDeleteRequest
from vo.StarChatRequest import StarChatRequest
from vo.CreateChatRequest import CreateChatRequest
from vo.UpdateChatRequest import UpdateChatRequest
from vo.ChatResponse import ChatResponse, ChatListResponse, StarredChatsResponse


class LLMController:
    def __init__(self):
        self.llm_service = LLMServiceImpl()
        self.router = APIRouter()
        self._setup_router()

    def _setup_router(self):
        # 房屋信息相关
        self.router.post("/house/")(self.get_house_info)
        
        # 对话工具相关
        self.router.post("/chat/tools")(self.chat_with_tools)
        
        # 对话历史记录相关
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
        self.router.post("/chat/history/batch/delete")(self.delete_threads_batch)
        self.router.post("/chat/name/{thread_id}")(self.generate_chat_name)
        
        # 对话CRUD相关
        self.router.post("/chat", status_code=201)(self.create_chat)
        self.router.get("/chat/user/{user_id}")(self.get_user_chats)
        self.router.put("/chat/{thread_id}")(self.update_chat)
        self.router.delete("/chat/{thread_id}")(self.delete_chat)
        
        # 收藏功能相关
        self.router.post("/chat/{thread_id}/star")(self.star_chat)
        self.router.get("/chat/starred")(self.get_starred_chats)
        self.router.post("/chat/toggle_star")(self.toggle_star_chat)

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

    async def delete_threads_batch(self, request: BatchDeleteRequest) -> dict[str, Any]:
        """
        批量删除多个对话线程
        :param request: 批量删除请求体
        :return: 删除状态
        """
        if not request.thread_ids:
            raise HTTPException(status_code=400, detail="线程ID列表不能为空")

        return await self.llm_service.delete_threads_batch(request.thread_ids)

    async def generate_chat_name(self, thread_id: str) -> dict[str, str]:
        """
        为对话生成智能标题
        :param thread_id: 对话线程ID
        :return: 包含生成标题的字典
        """
        try:
            title = await self.llm_service.generate_chat_name(thread_id)
            return {"thread_id": thread_id, "title": title, "status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成对话标题失败: {str(e)}")

    async def toggle_star_chat(self, request: StarChatRequest):
        return await self.llm_service.toggle_star_chat(request.thread_id)

    # ==================== 对话CRUD操作 ====================
    
    async def create_chat(self, request: CreateChatRequest) -> ChatResponse:
        """
        创建新对话
        
        Args:
            request: 创建对话请求，包含用户ID和可选标题
            
        Returns:
            ChatResponse: 包含操作状态和创建的对话信息
            
        Raises:
            HTTPException: 400 - 创建失败时抛出异常
        """
        try:
            result = await self.llm_service.create_chat(request.user_id)
            
            if not result["status"]:
                raise HTTPException(
                    status_code=400,
                    detail=result.get("error", "创建对话失败")
                )
                
            # 如果提供了自定义标题，更新对话标题
            if request.title and request.title != "Untitled":
                chat_obj = result["chat"]
                chat_obj.title = request.title
                update_result = await self.llm_service.update_chat(chat_obj)
                if not update_result["status"]:
                    # 标题更新失败，但对话已创建，记录警告但不抛出异常
                    print(f"警告: 对话创建成功但标题更新失败 - {update_result.get('error')}")
                    
            return ChatResponse(
                message="success",
                status=True,
                data={
                    "chat_id": str(result["chat"].id),
                    "title": request.title or "Untitled",
                    "user_id": str(request.user_id),
                    "created_at": result["chat"].create_time.isoformat() if hasattr(result["chat"], 'create_time') else None
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"创建对话时发生内部错误: {str(e)}"
            )

    async def get_user_chats(self, user_id: uuid.UUID) -> ChatListResponse:
        """
        获取用户所有对话
        
        Args:
            user_id: 用户UUID
            
        Returns:
            ChatListResponse: 包含用户对话列表和数量信息
            
        Raises:
            HTTPException: 500 - 查询失败时抛出异常
        """
        try:
            result = await self.llm_service.get_chat(user_id)
            
            if not result["status"]:
                raise HTTPException(
                    status_code=500,
                    detail=result.get("error", "获取对话列表失败")
                )
                
            # 转换Chat对象为字典格式，便于序列化
            chats_data = []
            for chat in result.get("chats", []):
                chat_dict = {
                    "id": str(chat.id),
                    "title": chat.title,
                    "user_id": str(chat.user_id),
                    "stared": chat.stared,
                    "create_time": chat.create_time.isoformat() if hasattr(chat, 'create_time') else None,
                    "update_time": chat.update_time.isoformat() if hasattr(chat, 'update_time') else None
                }
                chats_data.append(chat_dict)
                
            return ChatListResponse(
                message="success",
                status=True,
                chats=chats_data,
                count=result.get("count", 0)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取对话列表时发生内部错误: {str(e)}"
            )

    async def update_chat(self, thread_id: uuid.UUID, request: UpdateChatRequest) -> ChatResponse:
        """
        更新对话信息
        
        Args:
            thread_id: 对话线程ID
            request: 更新请求，包含要更新的字段
            
        Returns:
            ChatResponse: 包含更新操作状态
            
        Raises:
            HTTPException: 404 - 对话不存在; 400 - 更新失败
        """
        try:
            # 首先获取现有对话信息以验证存在性
            # 注意：这里需要根据实际service实现调整获取单个对话的方法
            
            # 创建更新对象 - 这里简化处理，实际可能需要先获取现有对话
            from dao.entity.chat_models import Chat
            chat_updates = Chat(id=thread_id)
            
            # 仅更新提供的字段
            if request.title is not None:
                chat_updates.title = request.title
            if request.stared is not None:
                chat_updates.stared = request.stared
                
            result = await self.llm_service.update_chat(chat_updates)
            
            if not result["status"]:
                if "does not exist" in result.get("message", ""):
                    raise HTTPException(
                        status_code=404,
                        detail=f"对话 {thread_id} 不存在"
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=result.get("error", "更新对话失败")
                    )
                    
            return ChatResponse(
                message="success",
                status=True,
                data={
                    "thread_id": str(thread_id),
                    "updated_fields": {
                        k: v for k, v in {
                            "title": request.title,
                            "stared": request.stared
                        }.items() if v is not None
                    }
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"更新对话时发生内部错误: {str(e)}"
            )

    async def delete_chat(self, thread_id: uuid.UUID) -> ChatResponse:
        """
        删除对话
        
        Args:
            thread_id: 对话线程ID
            
        Returns:
            ChatResponse: 包含删除操作状态
            
        Raises:
            HTTPException: 404 - 对话不存在; 500 - 删除失败
        """
        try:
            result = await self.llm_service.delete_chat(thread_id)
            
            if not result["status"]:
                if "does not exist" in result.get("message", ""):
                    raise HTTPException(
                        status_code=404,
                        detail=f"对话 {thread_id} 不存在"
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=result.get("error", "删除对话失败")
                    )
                    
            return ChatResponse(
                message="success",
                status=True,
                data={"deleted_thread_id": str(thread_id)}
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"删除对话时发生内部错误: {str(e)}"
            )

    # ==================== 收藏功能操作 ====================
    
    async def star_chat(self, thread_id: uuid.UUID) -> ChatResponse:
        """
        收藏对话
        
        Args:
            thread_id: 对话线程ID
            
        Returns:
            ChatResponse: 包含收藏操作状态
            
        Raises:
            HTTPException: 400 - 已收藏或收藏失败; 500 - 内部错误
        """
        try:
            result = await self.llm_service.star_chat(thread_id)
            
            if not result["status"]:
                if result.get("message") == "already_starred":
                    raise HTTPException(
                        status_code=400,
                        detail="该对话已经收藏过了"
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=result.get("error", "收藏对话失败")
                    )
                    
            return ChatResponse(
                message="success",
                status=True,
                data={"starred_thread_id": str(thread_id)}
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"收藏对话时发生内部错误: {str(e)}"
            )

    async def get_starred_chats(self) -> StarredChatsResponse:
        """
        获取所有收藏的对话
        
        Returns:
            StarredChatsResponse: 包含收藏对话ID列表和数量
            
        Raises:
            HTTPException: 500 - 获取失败
        """
        try:
            result = await self.llm_service.get_stared_chat()
            
            if not result["status"]:
                raise HTTPException(
                    status_code=500,
                    detail=result.get("error", "获取收藏列表失败")
                )
                
            return StarredChatsResponse(
                message="success",
                status=True,
                chat_ids=result.get("chat_ids", []),
                count=result.get("count", 0)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取收藏列表时发生内部错误: {str(e)}"
            )
