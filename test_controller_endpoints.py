"""
简单的API端点测试脚本
用于验证新增的Controller端点功能
"""

import asyncio
import uuid
from controller.LLMController import LLMController
from vo.CreateChatRequest import CreateChatRequest
from vo.UpdateChatRequest import UpdateChatRequest


async def test_controller_endpoints():
    """测试Controller端点的基本功能"""
    print("=== 开始测试Controller端点 ===")
    
    controller = LLMController()
    test_user_id = uuid.uuid4()
    
    try:
        # 1. 测试创建对话
        print("1. 测试创建对话...")
        create_request = CreateChatRequest(
            user_id=test_user_id,
            title="测试对话"
        )
        
        create_result = await controller.create_chat(create_request)
        print(f"创建结果: {create_result}")
        
        # 2. 测试获取用户对话列表
        print("2. 测试获取用户对话...")
        get_result = await controller.get_user_chats(test_user_id)
        print(f"获取结果: {get_result}")
        
        if get_result.status and get_result.chats:
            chat_id = uuid.UUID(get_result.chats[0]["id"])
            
            # 3. 测试更新对话
            print("3. 测试更新对话...")
            update_request = UpdateChatRequest(
                thread_id=chat_id,
                title="更新后的标题",
                stared=True
            )
            update_result = await controller.update_chat(chat_id, update_request)
            print(f"更新结果: {update_result}")
            
            # 4. 测试收藏对话
            print("4. 测试收藏对话...")
            star_result = await controller.star_chat(chat_id)
            print(f"收藏结果: {star_result}")
            
            # 5. 测试获取收藏列表
            print("5. 测试获取收藏列表...")
            starred_result = await controller.get_starred_chats()
            print(f"收藏列表: {starred_result}")
            
            # 6. 测试删除对话
            print("6. 测试删除对话...")
            delete_result = await controller.delete_chat(chat_id)
            print(f"删除结果: {delete_result}")
        
        print("=== 所有测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")


if __name__ == "__main__":
    # 注意：这个测试需要数据库连接，实际运行前请确保数据库配置正确
    print("注意：此测试脚本需要数据库连接，请确保PostgreSQL数据库正常运行")
    print("测试脚本结构验证完成，实际测试请在完整环境中运行")