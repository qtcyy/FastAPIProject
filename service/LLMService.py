from abc import abstractmethod, ABC
from typing import Any


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
