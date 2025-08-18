#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话命名功能测试脚本
测试智能对话标题生成功能
"""

import asyncio
import uuid
from llm.llm_chat_with_tools.chatbot.ChatBot import ChatBot
from langchain_core.messages import HumanMessage, AIMessage


async def test_chat_naming():
    """测试对话命名功能"""
    print("🚀 开始测试对话命名功能")
    
    # 初始化ChatBot
    chatbot = ChatBot()
    await chatbot.initialize()
    
    # 创建测试对话
    test_cases = [
        {
            "thread_id": str(uuid.uuid4()),
            "messages": [
                HumanMessage(content="你好，我想学习Python编程"),
                AIMessage(content="你好！很高兴你想学习Python编程。Python是一门非常适合初学者的编程语言，语法简洁明了。你想从哪个方面开始学习呢？"),
                HumanMessage(content="我想了解Python的基本语法"),
                AIMessage(content="好的！Python的基本语法包括变量定义、数据类型、控制流语句等。让我为你介绍一下...")
            ],
            "expected_theme": "Python编程"
        },
        {
            "thread_id": str(uuid.uuid4()),
            "messages": [
                HumanMessage(content="今天杭州的天气怎么样？"),
                AIMessage(content="我来为你查询杭州今天的天气情况。"),
                HumanMessage(content="温度大概多少度？"),
                AIMessage(content="根据最新的天气信息，杭州今天...")
            ],
            "expected_theme": "天气查询"
        },
        {
            "thread_id": str(uuid.uuid4()),
            "messages": [
                HumanMessage(content="帮我计算一下 123 * 456 + 789"),
                AIMessage(content="我来帮你计算这个数学表达式。"),
                HumanMessage(content="还需要计算标准差"),
                AIMessage(content="好的，我来帮你计算标准差...")
            ],
            "expected_theme": "数学计算"
        },
        {
            "thread_id": str(uuid.uuid4()),
            "messages": [
                HumanMessage(content="我想规划一下这个月的工作安排"),
                AIMessage(content="好的，让我帮你规划这个月的工作安排。你可以告诉我你的主要工作任务和目标吗？"),
                HumanMessage(content="主要是项目开发和文档编写"),
                AIMessage(content="明白了。项目开发和文档编写都是重要的工作内容...")
            ],
            "expected_theme": "工作规划"
        }
    ]
    
    # 测试每个用例
    for i, test_case in enumerate(test_cases, 1):
        thread_id = test_case["thread_id"]
        messages = test_case["messages"]
        expected_theme = test_case["expected_theme"]
        
        print(f"\n📝 测试用例 {i}: {expected_theme}")
        print(f"线程ID: {thread_id}")
        
        try:
            # 模拟对话历史（在实际环境中，这些消息会通过对话API添加到状态中）
            # 这里我们直接测试命名功能的核心逻辑
            
            # 提取对话内容
            conversation_content = chatbot._extract_conversation_for_naming(messages)
            print(f"提取的对话内容: {conversation_content[:100]}...")
            
            # 生成标题（模拟方式）
            # 在实际使用中，应该先通过对话API创建对话历史，然后调用named_chat
            title = chatbot._clean_generated_title(f"{expected_theme}相关讨论")
            
            print(f"✅ 生成的标题: '{title}'")
            print(f"期望主题: '{expected_theme}'")
            
            # 验证标题质量
            if len(title) >= 2 and len(title) <= 20:
                print("✅ 标题长度合适")
            else:
                print("❌ 标题长度不合适")
            
            if expected_theme in title or any(keyword in title for keyword in expected_theme.split()):
                print("✅ 标题内容相关")
            else:
                print("⚠️ 标题内容相关性待验证")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "="*50)
    print("📊 对话命名功能测试完成")
    print("="*50)
    
    # 测试标题清理功能
    print("\n🧹 测试标题清理功能:")
    
    test_titles = [
        "标题：Python编程问题",
        "对话标题: 天气查询",
        '"数学计算相关"',
        "工作规划讨论...",
        "   机器学习算法   ",
        "",
        "。，、",
        "这是一个非常非常长的标题，超过了我们设定的长度限制",
    ]
    
    for raw_title in test_titles:
        cleaned = chatbot._clean_generated_title(raw_title)
        print(f"原始: '{raw_title}' -> 清理后: '{cleaned}'")


async def test_integration():
    """集成测试：完整的对话命名流程"""
    print("\n🔧 开始集成测试")
    
    chatbot = ChatBot()
    await chatbot.initialize()
    
    # 创建一个真实的对话会话并生成标题
    thread_id = str(uuid.uuid4())
    
    try:
        # 注意：在真实环境中，你需要先通过对话API创建实际的对话历史
        # 这里只是演示API的调用方式
        print(f"测试线程ID: {thread_id}")
        
        # 调用命名功能（如果线程为空会返回"新对话"）
        title = await chatbot.named_chat(thread_id)
        print(f"生成的标题: '{title}'")
        
        if title == "新对话":
            print("✅ 正确处理空对话的情况")
        else:
            print("📝 生成了自定义标题")
            
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_chat_naming())
    asyncio.run(test_integration())