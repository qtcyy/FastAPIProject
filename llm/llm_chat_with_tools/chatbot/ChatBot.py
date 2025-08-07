import asyncio
import json
import time
from typing import TypedDict, Annotated, Sequence

from langchain_anthropic import ChatAnthropic
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

from langgraph.checkpoint.memory import MemorySaver
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
    def __init__(self):
        self.llm = ChatDeepSeek(
            model="deepseek-ai/DeepSeek-R1",
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
        messages = state["messages"]
        print(f"messages: {messages}")
        response = await self.chain.ainvoke({"messages": messages})
        print(response)
        return {"messages": response}

    def create_graph(self):
        graph_builder = StateGraph(ChatState)
        graph_builder.add_node("chatbot", self.chatbot)
        graph_builder.add_node("tools", self.tool_node)

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

        async for chunk in self.graph.astream(
            {"messages": HumanMessage(content=query)},
            config=config,
            stream_mode="messages",
            print_mode=["messages"],
        ):
            event = chunk[0]
            event_config = chunk[1]
            if isinstance(event, AIMessageChunk):
                data = {
                    "id": event.id,
                    "messages": event.content,
                    "timestamp": time.time(),
                    "type": "ai",
                    "thread_id": event_config["thread_id"],
                }
                if event.additional_kwargs and hasattr(
                    event.additional_kwargs, "tool_calls"
                ):
                    data.update({"type": "ai_tool_calls"})
                else:
                    full_messages += event.content
                # full_messages += event.content
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
        print(f"full_messages: {full_messages}")
        yield "data: [DONE]\n"

    async def generate_test(self, query: str):
        response = await self.chain.ainvoke({"messages": [HumanMessage(content=query)]})
        print(response)


#
# async def main():
#     bot = ChatBot()
#     await bot.generate_test("你好")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
