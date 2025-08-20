"""
自动更新时间戳功能测试
演示BaseModal的自动update_time更新功能
"""
import time
from datetime import datetime
from sqlmodel import Field
from dao.entity.base_modal import BaseModal
from dao.database import get_session, create_db_and_tables, db


class User(BaseModal, table=True):
    """
    用户模型示例
    继承BaseModal，自动获得create_time和update_time字段
    """
    __tablename__ = "test_users"
    
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="用户名")
    email: str = Field(description="邮箱")
    age: int | None = Field(default=None, description="年龄")


def test_auto_update_time():
    """
    测试自动更新时间戳功能
    """
    print("=== 自动更新时间戳功能测试 ===")
    
    # 1. 创建表
    print("1. 创建数据库表...")
    create_db_and_tables()
    
    # 2. 创建用户
    print("2. 创建新用户...")
    user = User(
        name="张三",
        email="zhangsan@example.com",
        age=25
    )
    
    with get_session() as session:
        created_user = db.create(user, session)
        print(f"   用户创建时间: {created_user.create_time}")
        print(f"   用户更新时间: {created_user.update_time}")
        print(f"   创建时间和更新时间相等: {created_user.create_time == created_user.update_time}")
        user_id = created_user.id
    
    # 3. 等待一段时间，然后更新用户信息
    print("\n3. 等待2秒后更新用户信息...")
    time.sleep(2)
    
    with get_session() as session:
        # 获取用户
        user = db.get_by_id(User, user_id, session)
        if user:
            original_update_time = user.update_time
            print(f"   更新前的更新时间: {original_update_time}")
            
            # 更新用户信息
            user.name = "李四"
            user.age = 30
            
            # 保存更新（update_time会自动更新）
            updated_user = db.update(user, session)
            
            print(f"   更新后的创建时间: {updated_user.create_time}")
            print(f"   更新后的更新时间: {updated_user.update_time}")
            print(f"   更新时间是否改变: {updated_user.update_time != original_update_time}")
            print(f"   时间差: {updated_user.update_time - original_update_time}")
    
    # 4. 再次更新测试
    print("\n4. 等待2秒后再次更新...")
    time.sleep(2)
    
    with get_session() as session:
        user = db.get_by_id(User, user_id, session)
        if user:
            previous_update_time = user.update_time
            print(f"   第二次更新前的更新时间: {previous_update_time}")
            
            # 再次更新
            user.email = "lisi@example.com"
            updated_user = db.update(user, session)
            
            print(f"   第二次更新后的更新时间: {updated_user.update_time}")
            print(f"   第二次更新时间是否改变: {updated_user.update_time != previous_update_time}")
    
    # 5. 直接使用session操作测试
    print("\n5. 使用原生session操作测试...")
    time.sleep(2)
    
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            previous_update_time = user.update_time
            print(f"   使用session更新前的更新时间: {previous_update_time}")
            
            # 直接修改并保存
            user.name = "王五"
            session.add(user)  # 这会触发before_update事件
            session.commit()
            
            # 刷新获取最新数据
            session.refresh(user)
            print(f"   使用session更新后的更新时间: {user.update_time}")
            print(f"   使用session更新时间是否改变: {user.update_time != previous_update_time}")
    
    print("\n=== 测试完成 ===")
    print("结论: update_time字段在每次数据更新时都会自动更新为当前时间")


def test_without_auto_update():
    """
    测试不使用自动更新功能的对比
    """
    print("\n=== 对比测试：手动管理时间戳 ===")
    
    # 创建一个不使用自动更新的简单模型
    from sqlmodel import SQLModel
    
    class SimpleUser(SQLModel, table=True):
        __tablename__ = "simple_users"
        
        id: int | None = Field(default=None, primary_key=True)
        name: str = Field(description="用户名")
        create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
        update_time: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    create_db_and_tables()
    
    with get_session() as session:
        # 创建用户
        user = SimpleUser(name="测试用户")
        session.add(user)
        session.commit()
        session.refresh(user)
        
        original_update_time = user.update_time
        print(f"简单模型创建时的更新时间: {original_update_time}")
        
        time.sleep(2)
        
        # 更新用户（不会自动更新update_time）
        user.name = "更新后的用户"
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"简单模型更新后的更新时间: {user.update_time}")
        print(f"时间是否改变: {user.update_time != original_update_time}")
        print("结论: 不使用TimestampMixin的模型不会自动更新update_time")


if __name__ == "__main__":
    # 运行测试
    test_auto_update_time()
    test_without_auto_update()