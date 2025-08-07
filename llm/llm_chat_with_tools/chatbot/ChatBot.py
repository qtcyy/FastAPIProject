import json
import time
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import add_messages, StateGraph, START

from llm.llm_chat_with_tools.tools.search_tools import search_tool

os.environ["OPENAI_API_KEY"] = "sk-klxcwiidfejlwzupobhtdvwkzdvwtsxqekqucykewmyfryis"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"


class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


memory = MemorySaver()


class ChatBot:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="Qwen/Qwen2.5-7B-Instruct", verbose=True, temperature=0.8
        )
        self.tools = [search_tool]
        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
        self.tool_node = ToolNode(tools=self.tools)

        self.graph = self.create_graph()

    async def chatbot(self, state: ChatState):
        messages = state["messages"]
        return {"messages": await self.llm_with_tools.ainvoke(messages)}

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

        async for chunk in self.graph.astream(
            {"messages": HumanMessage(content=query)},
            config=config,
            stream_mode="messages",
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
                if event.additional_kwargs and event.additional_kwargs["tool_calls"]:
                    data.update({"type": "ai_tool_calls"})
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
        yield "data: [DONE]\n"
