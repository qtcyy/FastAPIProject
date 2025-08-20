# 数据库层使用指南

本文档介绍如何使用项目中的数据库层，特别是自动时间戳更新功能。

## 功能概述

### 自动时间戳管理

所有继承 `BaseModal` 的模型都自动具备以下功能：

- **create_time**: 创建时自动设置为当前时间
- **update_time**: 创建时设置为当前时间，每次更新时自动更新为当前时间

### 核心组件

1. **TimestampMixin**: 时间戳混入类，提供自动时间戳管理
2. **BaseModal**: 基础模型类，继承 TimestampMixin
3. **DatabaseOperations**: 数据库操作工具类
4. **get_session()**: 数据库会话上下文管理器

## 快速开始

### 1. 创建模型

```python
from dao.entity.base_modal import BaseModal
from sqlmodel import Field

class User(BaseModal, table=True):
    __tablename__ = "users"
    
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    age: int | None = Field(default=None, description="年龄")
```

### 2. 基本CRUD操作

```python
from dao.database import db, get_session

# 创建用户
user = User(name="张三", email="zhangsan@example.com", age=25)
created_user = db.create(user)
print(f"创建时间: {created_user.create_time}")
print(f"更新时间: {created_user.update_time}")

# 更新用户（update_time会自动更新）
user = db.get_by_id(User, created_user.id)
user.name = "李四"
updated_user = db.update(user)
print(f"更新后时间: {updated_user.update_time}")

# 删除用户
db.delete_by_id(User, user.id)
```

### 3. 使用会话管理器

```python
from dao.database import get_session

with get_session() as session:
    # 创建
    user = User(name="王五", email="wangwu@example.com")
    session.add(user)
    session.flush()  # 获取ID但不提交
    
    # 更新（update_time会自动更新）
    user.age = 30
    session.add(user)  # 触发before_update事件
    
    # 事务会在with块结束时自动提交
```

## 高级用法

### 自定义模型

如果需要更多控制，可以直接继承 `TimestampMixin`：

```python
from dao.entity.timestamp_mixin import TimestampMixin
from sqlmodel import Field

class CustomModel(TimestampMixin, table=True):
    __tablename__ = "custom_models"
    
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(description="名称")
    
    # 可以添加额外的时间戳字段
    last_login: datetime | None = Field(default=None, description="最后登录时间")
    
    def update_last_login(self):
        self.last_login = datetime.now()
```

### 批量操作

```python
from dao.database import get_session

with get_session() as session:
    # 批量创建
    users = [
        User(name=f"用户{i}", email=f"user{i}@example.com")
        for i in range(10)
    ]
    session.add_all(users)
    session.flush()
    
    # 批量更新
    for user in users:
        user.age = 25  # update_time会自动更新
    
    session.add_all(users)
    # 提交时所有update_time都会更新
```

## 配置说明

### 数据库连接

在 `config.py` 中配置数据库URL：

```python
# 环境变量 DATABASE_URL 或默认值
DATABASE_URL = "postgresql://username:password@localhost:5432/database_name"
```

### 引擎配置

数据库引擎在 `dao/database.py` 中配置：

```python
engine = create_engine(
    config.database_url,
    echo=False,           # 生产环境建议False
    pool_pre_ping=True,   # 连接预检测
    pool_recycle=3600,    # 连接回收时间(秒)
)
```

## 测试

运行测试示例：

```bash
# 测试自动更新时间戳功能
python dao/test/auto_update_time_test.py
```

## 最佳实践

### 1. 使用会话管理器
```python
# 推荐：使用会话管理器
with get_session() as session:
    user = db.create(user, session)
    # 自动处理提交和回滚

# 避免：手动管理会话
session = Session(engine)  # 需要手动关闭和处理异常
```

### 2. 充分利用自动时间戳

```python
# 不需要手动设置update_time
user.name = "新名称"
db.update(user)  # update_time自动更新

# 避免手动设置
user.update_time = datetime.now()  # 不必要
```

### 3. 批量操作优化

```python
with get_session() as session:
    # 批量操作在同一个事务中
    for item in large_list:
        # 处理每个项目
        db.update(item, session)
    # 一次性提交所有更改
```

## 星标功能使用示例

### 创建星标对话模型

```python
from dao.entity.stared_chat import StaredChat
from dao.database import db
import uuid

# 创建星标记录
thread_id = uuid.uuid4()
starred_chat = StaredChat(thread_id=thread_id)
created_record = db.create(starred_chat)

print(f"星标记录创建时间: {created_record.create_at}")
print(f"线程ID: {created_record.thread_id}")
```

### 查询星标对话列表

```python
from dao.entity.stared_chat import StaredChat
from dao.database import get_session

# 获取所有星标对话
with get_session() as session:
    statement = session.query(StaredChat).order_by(StaredChat.create_at)
    starred_chats = session.exec(statement).all()
    
    for chat in starred_chats:
        print(f"线程ID: {chat.thread_id}, 创建时间: {chat.create_at}")
```

### 检查对话是否已收藏

```python
from dao.entity.stared_chat import StaredChat
from dao.database import get_session

def is_chat_starred(thread_id: uuid.UUID) -> bool:
    """检查对话是否已被收藏"""
    with get_session() as session:
        existing = session.query(StaredChat).filter(
            StaredChat.thread_id == thread_id
        ).first()
        return existing is not None
```

## 错误处理模式和最佳实践

### 1. 事务安全模式

```python
from dao.database import get_session
import logging

def safe_database_operation():
    """演示安全的数据库操作模式"""
    try:
        with get_session() as session:
            # 数据库操作
            user = User(name="测试用户")
            session.add(user)
            session.flush()  # 获取ID但不提交
            
            # 更多操作...
            user.name = "更新后的用户"
            session.add(user)
            
            # with块结束时自动提交
            return user
    except Exception as e:
        # 会话自动回滚，记录错误
        logging.error(f"数据库操作失败: {str(e)}")
        raise  # 重新抛出异常供上层处理
```

### 2. 重复操作检查

```python
def star_chat_safely(thread_id: uuid.UUID) -> dict:
    """安全地收藏对话，避免重复收藏"""
    try:
        with get_session() as session:
            # 检查是否已存在
            existing = session.query(StaredChat).filter(
                StaredChat.thread_id == thread_id
            ).first()
            
            if existing:
                return {
                    "message": "already_starred",
                    "status": True,
                    "thread_id": thread_id
                }
            
            # 创建新的收藏记录
            new_starred = StaredChat(thread_id=thread_id)
            session.add(new_starred)
            session.flush()
            
            return {
                "message": "success",
                "status": True,
                "thread_id": thread_id,
                "created_at": new_starred.create_at
            }
            
    except Exception as e:
        logging.error(f"收藏对话失败 {thread_id}: {str(e)}")
        return {
            "message": "error",
            "status": False,
            "error": str(e)
        }
```

### 3. 批量操作错误处理

```python
def batch_operations_with_error_handling(operations: List[dict]) -> dict:
    """批量操作的错误处理示例"""
    success_count = 0
    failed_operations = []
    
    try:
        with get_session() as session:
            for i, operation in enumerate(operations):
                try:
                    # 执行单个操作
                    model = operation['model']
                    session.add(model)
                    session.flush()  # 检查单个操作是否成功
                    success_count += 1
                    
                except Exception as op_error:
                    failed_operations.append({
                        'index': i,
                        'error': str(op_error),
                        'operation': operation
                    })
                    logging.warning(f"操作 {i} 失败: {str(op_error)}")
                    # 继续处理其他操作，不中断整个事务
            
            # 如果有太多失败，可以选择回滚
            if len(failed_operations) > len(operations) // 2:
                raise Exception("失败操作过多，回滚事务")
                
            # 否则提交成功的操作
            return {
                "success_count": success_count,
                "failed_count": len(failed_operations),
                "failed_operations": failed_operations,
                "status": "partial_success" if failed_operations else "success"
            }
            
    except Exception as e:
        logging.error(f"批量操作失败: {str(e)}")
        return {
            "success_count": 0,
            "failed_count": len(operations),
            "error": str(e),
            "status": "failed"
        }
```

### 4. 连接池和性能优化

```python
# 优化大量查询操作
def optimized_query_pattern():
    """演示优化的查询模式"""
    # 推荐：使用单个会话处理多个相关查询
    with get_session() as session:
        # 预加载相关数据
        users = session.query(User).options(
            # 如果有关联关系，可以使用预加载
            # selectinload(User.profile)
        ).all()
        
        # 在同一会话中处理结果
        for user in users:
            # 处理用户数据
            pass
    
    # 避免：为每个操作创建新会话
    # for user_id in user_ids:  # 性能较差的模式
    #     with get_session() as session:
    #         user = session.get(User, user_id)
```

### 5. 数据验证和约束处理

```python
from sqlalchemy.exc import IntegrityError

def handle_constraint_violations():
    """处理数据库约束违反的示例"""
    try:
        with get_session() as session:
            # 可能违反唯一约束的操作
            user = User(email="existing@example.com")  # 假设email有唯一约束
            session.add(user)
            session.flush()
            
    except IntegrityError as e:
        if "unique constraint" in str(e).lower():
            return {"error": "邮箱已存在", "code": "DUPLICATE_EMAIL"}
        elif "foreign key constraint" in str(e).lower():
            return {"error": "关联的记录不存在", "code": "INVALID_REFERENCE"}
        else:
            return {"error": "数据约束违反", "code": "CONSTRAINT_VIOLATION"}
    except Exception as e:
        return {"error": f"未知数据库错误: {str(e)}", "code": "DATABASE_ERROR"}
```

### 性能优化建议

1. **连接池管理**: 引擎配置了连接池，适合高并发场景
2. **批量操作**: 对于大量数据操作，使用批量方法和单个事务
3. **索引策略**: 时间戳字段自动添加索引，对常用查询字段也应添加索引
4. **查询优化**: 使用适当的查询条件、限制结果集大小，避免 N+1 查询问题
5. **会话复用**: 对相关操作使用同一个会话，减少连接开销

### 监控和日志记录

```python
import logging
from time import time

def monitor_database_operations():
    """监控数据库操作性能"""
    start_time = time()
    try:
        with get_session() as session:
            # 数据库操作
            result = db.create(model)
            
        operation_time = time() - start_time
        if operation_time > 1.0:  # 超过1秒记录警告
            logging.warning(f"数据库操作耗时过长: {operation_time:.2f}s")
            
        return result
    except Exception as e:
        logging.error(f"数据库操作失败: {str(e)}", exc_info=True)
        raise
```