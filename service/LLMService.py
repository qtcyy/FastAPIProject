from abc import abstractmethod, ABC
from typing import Any, List

from langchain_core.messages import BaseMessage


class LLMService(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def test_service(self): ...

    @abstractmethod
    async def get_house_info_service(self, query: str) -> Any: ...

    @abstractmethod
    async def chat_agent(self, query: str, thread_id: str) -> Any: ...

    @abstractmethod
    async def get_thread_messages(self, thread_id: str) -> Any: ...

    @abstractmethod
    async def clean_thread_messages(self, thread_id: str) -> Any: ...

    @abstractmethod
    async def chat_with_tools(self, query: str, thread_id: str, model: str, summary_with_llm: bool = False) -> Any: ...

    @abstractmethod
    async def get_history(self, thread_id: str) -> List[BaseMessage]: ...

    @abstractmethod
    async def delete_thread(self, thread_id: str) -> Any: ...

    @abstractmethod
    async def edit_message(
        self, thread_id: str, message_idx: int, new_content: str
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def edit_message_with_id(
        self, thread_id: str, message_id: str, new_content: str
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_message(
        self, thread_id: str, message_idx: int
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_message_with_id(
        self, thread_id: str, message_id: str
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_messages_after_with_id(
        self, thread_id: str, message_id: str
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_message_by_id(
        self, thread_id: str, message_id: str
    ) -> BaseMessage: ...
