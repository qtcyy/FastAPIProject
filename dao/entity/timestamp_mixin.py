"""
时间戳混入类
提供自动更新时间戳的功能
"""
from datetime import datetime
from typing import Any
from sqlalchemy import event
from sqlmodel import SQLModel, Field


class TimestampMixin(SQLModel):
    """
    时间戳混入类
    为继承的模型自动管理创建时间和更新时间
    """
    create_time: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        index=True,
        description="创建时间"
    )
    update_time: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        index=True,
        description="更新时间"
    )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        在子类初始化时注册事件监听器
        """
        super().__init_subclass__(**kwargs)
        
        # 如果是表模型，注册更新事件监听器
        if hasattr(cls, '__tablename__'):
            event.listen(cls, 'before_update', cls._update_timestamp)
    
    @classmethod
    def _update_timestamp(cls, mapper: Any, connection: Any, target: Any) -> None:
        """
        在更新前自动设置更新时间
        
        Args:
            mapper: SQLAlchemy映射器
            connection: 数据库连接
            target: 被更新的模型实例
        """
        target.update_time = datetime.now()


# 为了兼容现有代码，创建一个别名
BaseModal = TimestampMixin