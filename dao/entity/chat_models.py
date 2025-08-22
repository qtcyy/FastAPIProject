import uuid

from dao.entity.base_modal import BaseModal
from sqlmodel import Field


class Chat(BaseModal, table=True):
    __tablename__ = "chat"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True, nullable=False)
    title: str = Field(index=True, nullable=False, default="Untitled")
    stared: bool = Field(default=False, nullable=False)
