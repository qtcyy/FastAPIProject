"""
基础模型类
提供通用的时间戳字段和自动更新功能
"""
from .timestamp_mixin import TimestampMixin


class BaseModal(TimestampMixin):
    """
    基础模型类
    继承TimestampMixin，提供自动时间戳管理功能
    """
    pass
