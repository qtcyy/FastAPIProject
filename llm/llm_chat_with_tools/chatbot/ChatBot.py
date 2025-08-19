import json
import uuid
from typing import TypedDict, Annotated, Sequence, List, Coroutine, Any, Optional
from datetime import datetime
import pytz

import psycopg
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import add_messages, StateGraph, START
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.typing import StateT

from config import config as app_config

from llm.llm_chat_with_tools.tools.calculate_tools import calculate_tools, advanced_math
from llm.llm_chat_with_tools.tools.search_tools import (
    search_tool,
    web_crawler,
)
from llm.llm_chat_with_tools.tools.result_processor import (
    result_processor,
    ProcessingMode,
)


# 配置验证
app_config.validate()


class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def get_current_time_prompt() -> str:
    """获取包含当前时间信息的系统提示词"""
    # 获取中国时间（东八区）
    china_tz = pytz.timezone("Asia/Shanghai")
    current_time = datetime.now(china_tz)

    # 格式化时间信息
    time_str = current_time.strftime("%Y年%m月%d日 %H:%M:%S")
    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日",
    }
    weekday = weekday_map[current_time.weekday()]

    return f"""你是一个专业的AI智能助手，拥有多种工具能力，致力于为用户提供准确、及时、有用的信息和解决方案。

⏰ **当前时间**: {time_str} ({weekday}) - 中国标准时间 (GMT+8)

核心能力与工具：
🔍 智能搜索：实时获取最新网络信息，包括新闻、资讯、技术文档等
🌐 网页爬取：深度解析网页内容，提取关键信息和详细数据  
🧮 数学计算：处理各种数学运算、统计分析和计算问题
📊 数据查询：查询数据库信息，如学生成绩统计等

工作原则：
1. 信息准确性：优先使用搜索工具获取最新、真实的数据，避免过时信息
2. 来源标注：明确标出信息来源，提供可验证的参考链接
3. 深度分析：搜索后根据需要使用网页爬取工具获取详细内容
4. 结构化回答：以清晰、有条理的方式组织和呈现信息
5. 主动思考：理解用户真实意图，提供超出预期的有价值建议
6. 时间感知：充分利用当前时间信息，为用户提供时效性准确的回答

响应策略：
- 对于时效性强的问题（天气、新闻、股价等），必须使用搜索工具
- 对于需要详细信息的查询，先搜索概况，再爬取具体内容
- 对于计算类问题，使用计算工具确保准确性
- 对于数据查询需求，使用相应的查询工具
- 对于时间相关的查询，参考当前时间提供准确信息
- 始终以用户需求为导向，灵活运用各种工具组合

请根据用户问题的性质，智能选择最合适的工具组合来提供最佳解决方案。"""


client = MultiServerMCPClient(
    {
        "Student_Grade_System": {
            "url": app_config.mcp_server_url,
            "transport": "streamable_http",
        }
    }
)

mcp_tools = []


async def get_tools():
    global mcp_tools
    mcp_tools = await client.get_tools()


class ChatBot:
    def __init__(
        self,
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        enable_result_processing: bool = True,
    ):
        """
        ChatBot初始化
        :param model: 模型名称
        :param enable_result_processing: 是否启用结果处理
        """
        self.llm = ChatDeepSeek(
            model=model,
            verbose=False,
            temperature=0.6,
            # extra_body={"thinking_budget": 1024},
        )
        self.tools = [
            search_tool,
            calculate_tools,
            advanced_math,
            web_crawler,
        ]
        self.llm_with_tools = None
        self.tool_node = None
        self.enable_result_processing = enable_result_processing
        self.result_processor = result_processor

        # 初始化时不创建prompt，在chatbot方法中动态生成

        self.chain = None

        # 类型注解：明确graph的类型，帮助IDE提供代码补全
        # 初始化时为None，调用initialize()后会被正确初始化
        self.memory: Optional[AsyncPostgresSaver] = None
        self.graph: Optional[CompiledStateGraph[ChatState]] = None

    async def initialize(self):
        conn = await psycopg.AsyncConnection.connect(
            app_config.database_url,
            autocommit=True,
        )
        self.memory = AsyncPostgresSaver(conn)

        await self.memory.setup()
        if not self.llm_with_tools:
            await get_tools()
            self.tools.extend(mcp_tools)
            print(self.tools)
            self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
            self.tool_node = ToolNode(tools=self.tools)
        self.graph = await self.create_graph()

    async def chatbot(self, state: ChatState):
        """
        chatbot节点
        :param state: langgraph状态
        :return: 新langgraph状态，包含llm_out
        """
        messages = state["messages"]
        print(f"messages: {messages}")
        print("chatbot")

        # 动态创建包含当前时间的prompt
        current_prompt = ChatPromptTemplate.from_messages(
            [("system", get_current_time_prompt()), ("placeholder", "{messages}")]
        )

        # 创建包含当前时间信息的chain
        chain = current_prompt | self.llm_with_tools

        response = await chain.ainvoke({"messages": messages})
        return {"messages": response}

    async def process_tool_results(self, state: ChatState):
        """
        处理工具执行结果的节点
        """
        messages = state["messages"]
        processed_messages = []

        length = len(messages)
        for i in range(length - 1, -1, -1):
            message = messages[i]
            if isinstance(message, HumanMessage):
                break
            if isinstance(message, ToolMessage) and self.enable_result_processing:
                # 获取工具名称
                tool_name = getattr(message, "name", "unknown_tool")
                original_content = message.content

                try:
                    # 如果是MCP工具结果，进行处理
                    if any(
                        tool_name.startswith(prefix)
                        for prefix in ["get_", "query_", "fetch_"]
                    ):
                        processed_content = await self.result_processor.process_result(
                            tool_name=tool_name,
                            result=original_content,
                            mode=ProcessingMode.FORMATTED,
                        )
                        message.content = processed_content
                except Exception as e:
                    print(f"处理工具结果时出错: {e}")
                    # 保持原始内容

            processed_messages.append(message)

        return {"messages": processed_messages}

    async def create_graph(self):
        if self.memory is None:
            raise ValueError("Memory not initialized. Call initialize() first.")

        graph_builder = StateGraph(ChatState)
        graph_builder.add_node("chatbot", self.chatbot, metadata={"name": "chatbot"})
        graph_builder.add_node("tools", self.tool_node, metadata={"name": "search"})

        if self.enable_result_processing:
            graph_builder.add_node(
                "process_results",
                self.process_tool_results,
                metadata={"name": "process_results"},
            )

        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_conditional_edges("chatbot", tools_condition)

        if self.enable_result_processing:
            graph_builder.add_edge("tools", "process_results")
            graph_builder.add_edge("process_results", "chatbot")
        else:
            graph_builder.add_edge("tools", "chatbot")

        return graph_builder.compile(checkpointer=self.memory)

    async def generate(
        self, query: str, thread_id: str, summary_with_llm: bool = False
    ):
        """
        对话内容生成
        :param query: 问题内容
        :param thread_id: 线程id
        :param summary_with_llm: 是否启用LLM智能总结功能
        :return: stream返回llm内容
        """
        if self.graph is None:
            await self.initialize()

        # 类型断言：告诉IDE此时graph不为None，提供完整的代码补全
        assert self.graph is not None, "Graph should be initialized"

        config: RunnableConfig = RunnableConfig(
            configurable={"thread_id": thread_id, "summary_with_llm": summary_with_llm}
        )
        full_messages = ""

        print("Start Chat:")
        async for chunk in self.graph.astream(
            {"messages": HumanMessage(content=query)},
            config=config,
            stream_mode="messages",
        ):
            # print(chunk)
            event = chunk[0]
            config = chunk[1]
            if isinstance(event, AIMessageChunk):
                if config.get("name") and (
                    config["name"] == "search" or config["name"] == "process_results"
                ):
                    continue
                full_messages += event.content
                print(event.content, end="")
            yield f"data: {json.dumps(dict(chunk[0]), ensure_ascii=False)}\n\n"
        # print(f"\nfull_messages:\n {full_messages}")
        yield "data: [DONE]\n"

    async def named_chat(self, thread_id: str) -> str:
        """
        根据对话内容给对话命名，生成简洁有意义的对话标题
        :param thread_id: 线程ID
        :return: 对话标题，如果失败返回默认标题
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"

        config: RunnableConfig = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            # 获取对话历史
            state = await self.graph.aget_state(config)
            if not (state and state.values and "messages" in state.values):
                return "新对话"

            messages: List[BaseMessage] = state.values["messages"]
            if not messages:
                return "新对话"

            # 提取对话内容用于生成标题
            conversation_content = self._extract_conversation_for_naming(messages)
            if not conversation_content.strip():
                return "新对话"

            # 创建专门的命名提示词
            naming_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """你是一个专业的对话标题生成助手。请根据提供的对话内容，生成一个简洁、准确、有意义的对话标题。

要求：
1. 标题长度控制在8-15个字符
2. 准确概括对话的主要话题或内容
3. 使用简洁明了的中文表达
4. 避免使用"关于"、"讨论"等冗余词汇
5. 突出对话的核心主题或关键词
6. 如果是技术问题，可以包含技术关键词
7. 如果是日常对话，突出主要话题

示例：
- 对话涉及Python编程 → "Python编程问题"
- 讨论机器学习算法 → "机器学习算法"
- 询问天气情况 → "天气查询"
- 数学计算问题 → "数学计算"
- 工作规划讨论 → "工作规划"

请直接输出标题，不要包含任何解释或额外文字。""",
                    ),
                    ("human", "请为以下对话生成标题：\n\n{conversation}"),
                ]
            )

            # 创建命名链
            naming_chain = naming_prompt | self.llm

            # 生成标题
            response = await naming_chain.ainvoke(
                {"conversation": conversation_content}
            )

            # 提取并清理标题
            title = self._clean_generated_title(
                response.content if hasattr(response, "content") else str(response)
            )

            print(f"为对话 {thread_id} 生成标题: {title}")
            return title

        except Exception as e:
            print(f"Error generating chat name: {e}")
            return "新对话"

    def _extract_conversation_for_naming(self, messages: List[BaseMessage]) -> str:
        """
        从消息列表中提取用于命名的关键对话内容
        :param messages: 消息列表
        :return: 提取的对话内容
        """
        conversation_parts = []
        human_messages = []
        ai_messages = []

        # 提取前几轮对话，重点关注用户问题和AI回答
        for message in messages:
            if isinstance(message, HumanMessage):
                human_messages.append(message.content)
            elif isinstance(message, AIMessage):
                ai_messages.append(message.content)

        # 优先使用前3个用户消息，这通常能反映对话主题
        for i, human_msg in enumerate(human_messages[:3]):
            conversation_parts.append(f"用户: {human_msg}")
            # 如果有对应的AI回答，也包含（但限制长度）
            if i < len(ai_messages):
                ai_response = ai_messages[i][:200]  # 限制AI回答长度
                conversation_parts.append(f"助手: {ai_response}")

        # 组合对话内容，控制总长度
        conversation_text = "\n".join(conversation_parts)

        # 限制总长度，避免token过多
        if len(conversation_text) > 1000:
            conversation_text = conversation_text[:1000] + "..."

        return conversation_text

    def _clean_generated_title(self, raw_title: str) -> str:
        """
        清理和优化生成的标题
        :param raw_title: 原始生成的标题
        :return: 清理后的标题
        """
        if not raw_title:
            return "新对话"

        # 移除可能的引号、换行符等
        title = raw_title.strip().strip('"\'""' "").strip()

        # 移除可能的前缀
        prefixes_to_remove = [
            "标题：",
            "标题:",
            "对话标题：",
            "对话标题:",
            "题目：",
            "题目:",
        ]
        for prefix in prefixes_to_remove:
            if title.startswith(prefix):
                title = title[len(prefix) :].strip()

        # 长度控制
        if len(title) > 20:
            title = title[:17] + "..."
        elif len(title) < 2:
            title = "新对话"

        # 如果标题为空或只包含标点符号，返回默认值
        if not title or title.isspace() or all(c in "。，、；：！？" for c in title):
            return "新对话"

        return title

    async def get_history(self, thread_id: str) -> List[BaseMessage]:
        """
        获取历史记录
        :param thread_id: 对话线程ID
        :return: 历史记录
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"

        config: RunnableConfig = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            state = await self.graph.aget_state(config)
            if state and state.values and "messages" in state.values:
                return state.values["messages"]
            return []
        except Exception as e:
            print(f"Error getting history: {str(e)}")
            return []

    async def delete_history(self, thread_id: str) -> bool:
        """
        删除历史记录
        :param thread_id: 线程ID
        :return: 删除状态
        """
        if self.graph is None:
            await self.initialize()

        assert self.memory is not None, "Memory should be initialized"

        try:
            await self.memory.adelete_thread(thread_id)
            return True
        except Exception as e:
            print(f"Error deleting history: {str(e)}")
            return False

    async def delete_history_batch(self, thread_ids: List[str]) -> bool:
        """
        批量删除多个对话历史记录
        :param thread_ids: 线程ID列表
        :return: bool 删除状态
        """
        if not thread_ids:
            return False

        if self.graph is None:
            await self.initialize()

        assert self.memory is not None, "Memory should be initialized"

        success_count = 0
        for thread_id in thread_ids:
            try:
                await self.memory.adelete_thread(thread_id)
                success_count += 1
                print(f"Successfully deleted thread: {thread_id}")
            except Exception as e:
                print(f"Error deleting thread {thread_id}: {str(e)}")

        # 如果至少有一个删除成功，返回True
        return success_count > 0

    async def edit_message(
        self, thread_id: str, message_idx: int, new_content: str
    ) -> bool:
        """
        编辑消息
        :param thread_id: 线程ID
        :param message_idx: 消息位置
        :param new_content: 新内容
        :return: bool 编辑状态
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"
        assert self.memory is not None, "Memory should be initialized"

        config = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            state = await self.graph.aget_state(config)
            messages = state.values.get("messages", [])
            if 0 <= message_idx < len(messages):
                if isinstance(messages[message_idx], HumanMessage):
                    messages[message_idx] = HumanMessage(content=new_content)
                elif isinstance(messages[message_idx], AIMessage):
                    messages[message_idx] = AIMessage(content=new_content)
                else:
                    raise "Unsupported message type"
                await self.memory.adelete_thread(thread_id)
                await self.graph.aupdate_state(config, {"messages": messages})
                return True
            else:
                raise f"Message index {message_idx} out of range"
        except Exception as e:
            print(f"Error on edit message: {str(e)}")
            return False

    async def edit_message_with_id(
        self, thread_id: str, message_id: str, new_content: str
    ) -> bool:
        """
        根据消息ID修改消息内容
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :param new_content: 新消息内容
        :return: 修改状态
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"
        assert self.memory is not None, "Memory should be initialized"

        config = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            state = await self.graph.aget_state(config)
            messages = state.values.get("messages", [])
            idx = -1
            for i, message in enumerate(messages):
                if message.id == message_id:
                    idx = i
                    break
            if idx != -1:
                if isinstance(messages[idx], AIMessage):
                    messages[idx] = AIMessage(new_content)
                elif isinstance(messages[idx], HumanMessage):
                    messages[idx] = HumanMessage(new_content)
                else:
                    raise "Unsupported message type"

                await self.memory.adelete_thread(thread_id)
                await self.graph.aupdate_state(config, {"messages": messages})
                return True
            else:
                raise f"Unable to find messages index {message_id}"
        except Exception as e:
            print(f"Error on edit message with id: {str(e)}")
            return False

    async def delete_message(self, thread_id: str, message_idx: int) -> bool:
        """
        删除指定消息
        :param thread_id: 线程ID
        :param message_idx: 消息位置
        :return: 删除状态
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"
        assert self.memory is not None, "Memory should be initialized"

        config = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            state = await self.graph.aget_state(config)
            messages = state.values.get("messages", [])
            if 0 <= message_idx < len(messages):
                messages.pop(message_idx)
                await self.memory.adelete_thread(thread_id)
                await self.graph.aupdate_state(config, {"messages": messages})
                return True
            else:
                raise f"Message index out of range"
        except Exception as e:
            print(f"Error on delete message: {str(e)}")
            return False

    async def delete_message_with_id(self, thread_id: str, message_id: str) -> bool:
        """
        根据消息ID删除消息
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :return: 删除状态
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"
        assert self.memory is not None, "Memory should be initialized"

        config = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            state = await self.graph.aget_state(config)
            messages = state.values.get("messages", [])
            idx = -1
            for i, message in enumerate(messages):
                if message.id == message_id:
                    idx = i
                    break
            if idx != -1:
                messages.pop(idx)
            else:
                raise f"Message index {message_id} out of range"
            await self.memory.adelete_thread(thread_id)
            await self.graph.aupdate_state(config, {"messages": messages})
            return True
        except Exception as e:
            print(f"Error on delete message with id: {str(e)}")
            return False

    async def delete_messages_after_with_id(
        self, thread_id: str, message_id: str
    ) -> bool:
        """
        删除指定消息后面的所有消息，包括该消息
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :return: 删除情况
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"
        assert self.memory is not None, "Memory should be initialized"

        config = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            state = await self.graph.aget_state(config)
            messages = state.values.get("messages", [])
            idx = -1
            for i, message in enumerate(messages):
                if message.id == message_id:
                    idx = i
                    break
            if idx != -1:
                if not (
                    isinstance(messages[idx], AIMessage)
                    or isinstance(messages[idx], HumanMessage)
                ):
                    raise "Unsupported message type"
                messages = messages[:idx]
                await self.memory.adelete_thread(thread_id)
                await self.graph.aupdate_state(config, {"messages": messages})
                return True
            else:
                raise f"Message index {message_id} out of range"
        except Exception as e:
            print(f"Error on delete message with id: {str(e)}")
            return False

    async def get_message_by_id(self, thread_id: str, message_id: str) -> BaseMessage:
        """
        根据消息ID获取指定消息
        :param thread_id: 线程ID
        :param message_id: 消息ID
        :return: 消息对象，如果未找到返回None
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"

        config = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            state = await self.graph.aget_state(config)
            messages = state.values.get("messages", [])
            for message in messages:
                if message.id == message_id:
                    return message
            return None
        except Exception as e:
            print(f"Error getting message by id: {str(e)}")
            return None

    async def generate_test(self, query: str):
        """
        测试方法（测试用）
        :param query: 问题
        :return: None
        """
        if self.graph is None:
            await self.initialize()

        assert self.graph is not None, "Graph should be initialized"

        config: RunnableConfig = RunnableConfig(configurable={"thread_id": "1"})
        full_messages = ""

        print("Start Chat: ")
        async for chunk in self.graph.astream(
            {"messages": HumanMessage(content=query)},
            config=config,
            stream_mode="messages",
        ):
            # print(chunk[0].content, end="")
            # print(chunk)
            data = chunk[1]
            print(data["name"])
            if isinstance(chunk[0], AIMessageChunk):
                full_messages += chunk[0].content

        print(f"full_messages: {full_messages}")


# async def main():
#     bot = ChatBot()
#     await bot.generate_test("查询杭州的天气")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
