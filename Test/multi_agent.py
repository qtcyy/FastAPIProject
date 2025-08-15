# -*- coding: utf-8 -*-
"""
多智能体测试脚本
测试 FastAPI ChatBot 项目中的多智能体协作功能
"""

import asyncio
import uuid
from typing import List, Dict, Any
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from llm.llm_chat_with_tools.chatbot.ChatBot import ChatBot


class MultiAgentTester:
    """多智能体测试器"""
    
    def __init__(self):
        self.agents = {}
        self.test_results = []
    
    async def create_agent(self, agent_id: str, model_name: str = "Qwen/Qwen2.5-7B-Instruct") -> ChatBot:
        """创建一个智能体实例"""
        agent = ChatBot(model=model_name)
        await agent.initialize()
        self.agents[agent_id] = agent
        print(f"✅ 创建智能体: {agent_id} (模型: {model_name})")
        return agent
    
    async def single_agent_test(self, agent_id: str, query: str, thread_id: str = None) -> Dict[str, Any]:
        """单智能体测试"""
        if agent_id not in self.agents:
            raise ValueError(f"智能体 {agent_id} 不存在")
        
        agent = self.agents[agent_id]
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        print(f"\n🤖 [{agent_id}] 处理查询: {query}")
        
        try:
            response = ""
            async for chunk in agent.generate(
                query=query,
                thread_id=thread_id,
                summary_with_llm=True
            ):
                if chunk.strip() and not chunk.startswith("data: [DONE]"):
                    # 提取实际内容，跳过SSE格式
                    if chunk.startswith("data: "):
                        try:
                            data = json.loads(chunk[6:])
                            if isinstance(data, dict) and "content" in data:
                                response += data["content"]
                        except json.JSONDecodeError:
                            continue
            
            result = {
                "agent_id": agent_id,
                "query": query,
                "response": response.strip(),
                "thread_id": thread_id,
                "status": "success"
            }
            
            print(f"📝 [{agent_id}] 响应: {response[:100]}...")
            return result
            
        except Exception as e:
            result = {
                "agent_id": agent_id,
                "query": query,
                "response": f"错误: {str(e)}",
                "thread_id": thread_id,
                "status": "error"
            }
            print(f"❌ [{agent_id}] 错误: {str(e)}")
            return result
    
    async def multi_agent_collaboration_test(self, agents_queries: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """多智能体协作测试"""
        print(f"\n🔄 开始多智能体协作测试，共 {len(agents_queries)} 个任务")
        
        tasks = []
        for item in agents_queries:
            agent_id = item["agent_id"]
            query = item["query"]
            thread_id = item.get("thread_id", str(uuid.uuid4()))
            
            task = self.single_agent_test(agent_id, query, thread_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "agent_id": agents_queries[i]["agent_id"],
                    "query": agents_queries[i]["query"],
                    "response": f"异常: {str(result)}",
                    "status": "exception"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def sequential_agent_test(self, queries: List[str], agent_id: str) -> List[Dict[str, Any]]:
        """顺序智能体测试（同一智能体处理多个相关查询）"""
        print(f"\n🔗 开始顺序测试，智能体: {agent_id}")
        
        thread_id = str(uuid.uuid4())
        results = []
        
        for i, query in enumerate(queries):
            print(f"\n  步骤 {i+1}/{len(queries)}")
            result = await self.single_agent_test(agent_id, query, thread_id)
            results.append(result)
        
        return results
    
    async def run_comprehensive_tests(self):
        """运行综合测试套件"""
        print("🚀 开始多智能体综合测试\n")
        
        # 创建多个智能体
        await self.create_agent("agent_search", "Qwen/Qwen2.5-7B-Instruct")
        await self.create_agent("agent_calc", "Qwen/Qwen2.5-7B-Instruct")
        await self.create_agent("agent_web", "Qwen/Qwen2.5-7B-Instruct")
        
        # 测试1: 并行多智能体测试
        print("\n" + "="*50)
        print("测试1: 并行多智能体协作")
        print("="*50)
        
        parallel_tests = [
            {"agent_id": "agent_search", "query": "搜索今天的新闻头条"},
            {"agent_id": "agent_calc", "query": "计算 123 * 456 + 789"},
            {"agent_id": "agent_web", "query": "爬取 python.org 的首页内容"}
        ]
        
        parallel_results = await self.multi_agent_collaboration_test(parallel_tests)
        self.test_results.extend(parallel_results)
        
        # 测试2: 顺序智能体测试
        print("\n" + "="*50)
        print("测试2: 顺序智能体对话")
        print("="*50)
        
        sequential_queries = [
            "你好，我想了解Python编程",
            "Python有哪些主要特点？",
            "请帮我计算一下 2的10次方",
            "搜索一些Python学习资源"
        ]
        
        sequential_results = await self.sequential_agent_test(sequential_queries, "agent_search")
        self.test_results.extend(sequential_results)
        
        # 测试3: 工具特化测试
        print("\n" + "="*50)
        print("测试3: 工具特化测试")
        print("="*50)
        
        tool_tests = [
            {"agent_id": "agent_calc", "query": "计算正弦函数 sin(π/4) 的值"},
            {"agent_id": "agent_search", "query": "搜索机器学习的最新发展"},
            {"agent_id": "agent_web", "query": "爬取 github.com 的trending页面"}
        ]
        
        tool_results = await self.multi_agent_collaboration_test(tool_tests)
        self.test_results.extend(tool_results)
        
        # 生成测试报告
        await self.generate_test_report()
    
    async def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "="*50)
        print("📊 测试报告")
        print("="*50)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["status"] == "success"])
        error_tests = len([r for r in self.test_results if r["status"] == "error"])
        exception_tests = len([r for r in self.test_results if r["status"] == "exception"])
        
        print(f"总测试数: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"错误: {error_tests}")
        print(f"异常: {exception_tests}")
        print(f"成功率: {(successful_tests/total_tests)*100:.1f}%")
        
        print("\n📋 详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_emoji = "✅" if result["status"] == "success" else "❌"
            print(f"{i:2d}. {status_emoji} [{result['agent_id']}] {result['query'][:50]}...")
            if result["status"] != "success":
                print(f"     错误: {result['response'][:100]}...")
        
        # 保存测试结果到文件
        report_file = Path(__file__).parent / "multi_agent_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细测试报告已保存到: {report_file}")


async def main():
    """主测试函数"""
    tester = MultiAgentTester()
    
    try:
        await tester.run_comprehensive_tests()
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🏁 多智能体测试完成")


if __name__ == "__main__":
    asyncio.run(main())