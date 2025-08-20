"""
数据库工具模块
提供数据库连接、会话管理和基础操作功能
"""
from typing import Generator, Optional, TypeVar, Type, Union, List
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session, select
from config import config

T = TypeVar('T', bound=SQLModel)

# 创建数据库引擎
engine = create_engine(
    config.database_url,
    echo=False,  # 生产环境建议设为False
    pool_pre_ping=True,  # 连接预检测
    pool_recycle=3600,   # 连接回收时间
)


def create_db_and_tables() -> None:
    """
    创建数据库表
    """
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    获取数据库会话上下文管理器
    
    Yields:
        Session: 数据库会话对象
    
    Example:
        with get_session() as session:
            # 执行数据库操作
            user = session.get(User, 1)
            session.commit()
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseOperations:
    """
    数据库操作工具类
    提供常用的CRUD操作
    """
    
    @staticmethod
    def create(obj: T, session: Optional[Session] = None) -> T:
        """
        创建新记录
        
        Args:
            obj: 要创建的模型实例
            session: 数据库会话（可选）
            
        Returns:
            T: 创建的模型实例
        """
        if session:
            session.add(obj)
            session.flush()  # 获取生成的ID但不提交事务
            return obj
        else:
            with get_session() as session:
                session.add(obj)
                session.flush()
                session.refresh(obj)  # 刷新以获取最新数据
                return obj
    
    @staticmethod
    def get_by_id(model_class: Type[T], id_value: Union[int, str], session: Optional[Session] = None) -> Optional[T]:
        """
        根据ID获取记录
        
        Args:
            model_class: 模型类
            id_value: ID值
            session: 数据库会话（可选）
            
        Returns:
            Optional[T]: 模型实例或None
        """
        if session:
            return session.get(model_class, id_value)
        else:
            with get_session() as session:
                return session.get(model_class, id_value)
    
    @staticmethod
    def update(obj: T, session: Optional[Session] = None) -> T:
        """
        更新记录（update_time会自动更新）
        
        Args:
            obj: 要更新的模型实例
            session: 数据库会话（可选）
            
        Returns:
            T: 更新后的模型实例
        """
        if session:
            session.add(obj)
            session.flush()
            return obj
        else:
            with get_session() as session:
                session.add(obj)
                session.flush()
                session.refresh(obj)
                return obj
    
    @staticmethod
    def delete(obj: T, session: Optional[Session] = None) -> bool:
        """
        删除记录
        
        Args:
            obj: 要删除的模型实例
            session: 数据库会话（可选）
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if session:
                session.delete(obj)
                session.flush()
                return True
            else:
                with get_session() as session:
                    # 重新获取对象以确保在当前session中
                    obj_to_delete = session.get(type(obj), obj.id if hasattr(obj, 'id') else obj)
                    if obj_to_delete:
                        session.delete(obj_to_delete)
                        return True
                    return False
        except Exception:
            return False
    
    @staticmethod
    def delete_by_id(model_class: Type[T], id_value: Union[int, str], session: Optional[Session] = None) -> bool:
        """
        根据ID删除记录
        
        Args:
            model_class: 模型类
            id_value: ID值
            session: 数据库会话（可选）
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if session:
                obj = session.get(model_class, id_value)
                if obj:
                    session.delete(obj)
                    session.flush()
                    return True
                return False
            else:
                with get_session() as session:
                    obj = session.get(model_class, id_value)
                    if obj:
                        session.delete(obj)
                        return True
                    return False
        except Exception:
            return False
    
    @staticmethod
    def list_all(model_class: Type[T], session: Optional[Session] = None) -> List[T]:
        """
        获取所有记录
        
        Args:
            model_class: 模型类
            session: 数据库会话（可选）
            
        Returns:
            List[T]: 模型实例列表
        """
        if session:
            statement = select(model_class)
            return list(session.exec(statement))
        else:
            with get_session() as session:
                statement = select(model_class)
                return list(session.exec(statement))


# 创建全局数据库操作实例
db = DatabaseOperations()