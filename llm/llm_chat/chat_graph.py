import json
import time

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from llm.llm_chat.chat_schema import AgentState
from llm.llm_chat.llm_func import chatbot

memory = MemorySaver()


class ChatGraph:
    def __init__(self, config):
        self.config = config

    def create_graph(self):
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("chatbot", chatbot)

        graph_builder.add_edge(START, "chatbot")

        return graph_builder.compile(checkpointer=memory)


class AgentClass:
    def __init__(self, config):
        self.config = config
        self.chat_graph = ChatGraph(config)
        self.graph = self.chat_graph.create_graph()

    async def agent_response(self, query: str):
        async for chunk in self.graph.astream(
            {"messages": HumanMessage(content=query)},
            config=self.config,
            stream_mode="messages",
        ):
            data = {"message": chunk[0].content, "timestamp": time.time()}
            print(f"chunk: {chunk}")
            yield f"data: {json.dumps(data,ensure_ascii=False)}\n\n"

        yield f"data: [DONE]\n"

    async def get_messages(self, config: RunnableConfig):
        """
        获取聊天历史记录
        :param config: 配置信息，包含thread_id
        :return: 历史记录
        """
        try:
            state = await self.graph.aget_state(config)
            if state and state.values and "messages" in state.values:
                return state.values["messages"]
            return []
        except Exception as e:
            print(f"Error on get messages: {str(e)}")
            return []

    async def clean_messages(self, config: RunnableConfig) -> str:
        """
        清楚聊天历史记录
        :param config: 配置信息，包含thread_id
        :return: 清除状态
        """
        thread_id = config["configurable"]["thread_id"]
        try:
            await memory.adelete_thread(thread_id)
            return "Success"
        except Exception as e:
            print(f"Error on clean messages: {str(e)}")
            return f"Error on clean messages: {str(e)}"
