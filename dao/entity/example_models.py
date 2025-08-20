"""
示例模型
演示如何使用BaseModal和自动时间戳功能
"""
from typing import Optional
from sqlmodel import Field, Relationship
from dao.entity.base_modal import BaseModal


class ChatThread(BaseModal, table=True):
    """
    对话线程模型
    自动管理创建时间和更新时间
    """
    __tablename__ = "chat_threads"
    
    id: int | None = Field(default=None, primary_key=True)
    thread_id: str = Field(unique=True, index=True, description="线程ID")
    title: str = Field(description="对话标题")
    user_id: str = Field(index=True, description="用户ID")
    status: str = Field(default="active", description="状态")
    
    # 关联消息
    messages: list["ChatMessage"] = Relationship(back_populates="thread")


class ChatMessage(BaseModal, table=True):
    """
    对话消息模型
    每次编辑消息时，update_time会自动更新
    """
    __tablename__ = "chat_messages"
    
    id: int | None = Field(default=None, primary_key=True)
    thread_id: str = Field(foreign_key="chat_threads.thread_id", index=True, description="线程ID")
    message_id: str = Field(unique=True, index=True, description="消息ID")
    content: str = Field(description="消息内容")
    role: str = Field(description="角色 (user/assistant)")
    message_type: str = Field(default="text", description="消息类型")
    
    # 关联线程
    thread: Optional[ChatThread] = Relationship(back_populates="messages")


class UserPreference(BaseModal, table=True):
    """
    用户偏好设置模型
    每次修改设置时自动更新时间戳
    """
    __tablename__ = "user_preferences"
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(unique=True, index=True, description="用户ID")
    theme: str = Field(default="light", description="主题")
    language: str = Field(default="zh", description="语言")
    notifications_enabled: bool = Field(default=True, description="通知开关")
    model_preference: str = Field(default="Qwen/Qwen2.5-7B-Instruct", description="偏好模型")


# 实用工具函数示例
def create_chat_thread(thread_id: str, title: str, user_id: str) -> ChatThread:
    """
    创建新的对话线程
    创建时间和更新时间会自动设置
    """
    from dao.database import db
    
    thread = ChatThread(
        thread_id=thread_id,
        title=title,
        user_id=user_id
    )
    
    return db.create(thread)


def update_chat_thread_title(thread_id: str, new_title: str) -> Optional[ChatThread]:
    """
    更新对话线程标题
    更新时间会自动更新
    """
    from dao.database import db, get_session
    from sqlmodel import select
    
    with get_session() as session:
        statement = select(ChatThread).where(ChatThread.thread_id == thread_id)
        thread = session.exec(statement).first()
        
        if thread:
            thread.title = new_title
            return db.update(thread, session)
        
        return None


def add_message_to_thread(thread_id: str, message_id: str, content: str, role: str) -> ChatMessage:
    """
    向对话线程添加消息
    创建时间和更新时间会自动设置
    """
    from dao.database import db
    
    message = ChatMessage(
        thread_id=thread_id,
        message_id=message_id,
        content=content,
        role=role
    )
    
    return db.create(message)


def edit_message(message_id: str, new_content: str) -> Optional[ChatMessage]:
    """
    编辑消息内容
    更新时间会自动更新
    """
    from dao.database import db, get_session
    from sqlmodel import select
    
    with get_session() as session:
        statement = select(ChatMessage).where(ChatMessage.message_id == message_id)
        message = session.exec(statement).first()
        
        if message:
            message.content = new_content
            return db.update(message, session)
        
        return None


def update_user_preferences(user_id: str, **preferences) -> Optional[UserPreference]:
    """
    更新用户偏好设置
    更新时间会自动更新
    """
    from dao.database import db, get_session
    from sqlmodel import select
    
    with get_session() as session:
        statement = select(UserPreference).where(UserPreference.user_id == user_id)
        user_pref = session.exec(statement).first()
        
        if not user_pref:
            # 创建新的用户偏好
            user_pref = UserPreference(user_id=user_id, **preferences)
            return db.create(user_pref, session)
        else:
            # 更新现有偏好
            for key, value in preferences.items():
                if hasattr(user_pref, key):
                    setattr(user_pref, key, value)
            return db.update(user_pref, session)