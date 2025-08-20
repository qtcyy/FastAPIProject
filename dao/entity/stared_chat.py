import uuid
from typing import Optional

from dao.entity.base_modal import BaseModal
from sqlmodel import Field


class StaredChat(BaseModal, table=True):
    __tablename__ = "stared_chat"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    thread_id: uuid.UUID = Field(index=True, nullable=False)
    user_id: Optional[uuid.UUID] = Field(index=True, nullable=True)
