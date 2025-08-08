import asyncio
import json
import time
from typing import TypedDict, Annotated, Sequence, List

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek
import os

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer, get_store
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import add_messages, StateGraph, START

from llm.llm_chat_with_tools.tools.calculate_tools import calculate_tools
from llm.llm_chat_with_tools.tools.search_tools import search_tool, web_crawler

os.environ["OPENAI_API_KEY"] = "sk-klxcwiidfejlwzupobhtdvwkzdvwtsxqekqucykewmyfryis"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1/chat/completions"
os.environ["DEEPSEEK_API_KEY"] = "sk-klxcwiidfejlwzupobhtdvwkzdvwtsxqekqucykewmyfryis"
os.environ["DEEPSEEK_API_BASE"] = "https://api.siliconflow.cn/v1"

api_key = os.environ["OPENAI_API_KEY"]
api_base = os.environ["OPENAI_API_BASE"]


class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


memory = MemorySaver()
SimplePrompt = "你是一个有用的ai助手。在调用网路搜索工具后如需获取详细信息，请调用网页访问工具获取网页详细信息。注意标出信息来源。"


class ChatBot:
    def __init__(self, model: str = "Qwen/Qwen2.5-7B-Instruct"):
        """
        ChatBot初始化
        :param model: 模型名称
        """
        self.llm = ChatDeepSeek(
            model=model,
            verbose=True,
            temperature=0.8,
        )
        self.tools = [search_tool, calculate_tools, web_crawler]
        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
        self.tool_node = ToolNode(tools=self.tools)

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", SimplePrompt), ("placeholder", "{messages}")]
        )

        self.chain = self.prompt | self.llm_with_tools

        self.graph = self.create_graph()

    async def chatbot(self, state: ChatState):
        """
        chatbot节点
        :param state: langgraph状态
        :return: 新langgraph状态，包含llm_out
        """
        # writer = get_stream_writer()
        messages = state["messages"]
        print(f"messages: {messages}")
        response = await self.chain.ainvoke({"messages": messages})
        # writer(response)
        # print(f"response: {response}")
        # print(f"response type: {type(response)}")
        return {"messages": response}
        # writer = get_stream_writer()
        # full_message = ""
        # async for chunk in self.chain.astream({"messages": messages}):
        #     # print(type(chunk))
        #     writer(chunk)
        #     full_message += chunk.content
        # return {"messages": AIMessage(content=full_message)}

    def create_graph(self):
        graph_builder = StateGraph(ChatState)
        graph_builder.add_node("chatbot", self.chatbot, metadata={"name": "chatbot"})
        graph_builder.add_node("tools", self.tool_node, metadata={"name": "search"})

        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_conditional_edges("chatbot", tools_condition)
        graph_builder.add_edge("tools", "chatbot")

        return graph_builder.compile(checkpointer=memory)

    async def generate(self, query: str, thread_id: str):
        """
        对话内容生成
        :param query: 问题内容
        :param thread_id: 线程id
        :return: stream返回llm内容
        """
        config: RunnableConfig = RunnableConfig(configurable={"thread_id": thread_id})
        full_messages = ""

        print("Start Chat:")
        async for chunk in self.graph.astream(
            {"messages": HumanMessage(content=query)},
            config=config,
            stream_mode="messages",
        ):
            # print(chunk)
            event = chunk[0]
            event_config = chunk[1]
            if isinstance(event, AIMessageChunk):
                print(event.content, end="")
                data = {
                    "id": event.id,
                    "messages": event.content,
                    "timestamp": time.time(),
                    "type": "ai",
                    "thread_id": event_config["thread_id"],
                }
                if event.additional_kwargs:
                    if event.additional_kwargs.get("tool_calls"):
                        data.update({"type": "ai_tool_calls"})
                    if event.additional_kwargs.get("reasoning_content"):
                        reasoning_content = event.additional_kwargs.get(
                            "reasoning_content"
                        )
                        print(reasoning_content, end="")
                        data.update(
                            {
                                "type": "ai_reasoning_content",
                                "messages": reasoning_content,
                            }
                        )

                full_messages += event.content
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            elif isinstance(event, ToolMessage):
                data = {
                    "id": event.id,
                    "messages": event.content,
                    "timestamp": time.time(),
                    "type": "tool",
                    "tool_name": event.name,
                    "thread_id": event_config["thread_id"],
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        print(f"\nfull_messages:\n {full_messages}")
        yield "data: [DONE]\n"

    async def get_history(self, thread_id: str) -> List[BaseMessage]:
        """
        获取历史记录
        :param thread_id: 对话线程ID
        :return: 历史记录
        """
        config: RunnableConfig = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            state = await self.graph.aget_state(config)
            print(f"messages: {state.values['messages']}")
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
        try:
            await memory.adelete_thread(thread_id)
            return True
        except Exception as e:
            print(f"Error deleting history: {str(e)}")
            return False

    async def generate_test(self, query: str):
        """
        测试方法（测试用）
        :param query: 问题
        :return: None
        """
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
