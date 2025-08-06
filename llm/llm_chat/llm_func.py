import os
from typing import Any, AsyncGenerator

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from llm.llm_chat.chat_schema import AgentState

os.environ["OPENAI_API_KEY"] = "sk-klxcwiidfejlwzupobhtdvwkzdvwtsxqekqucykewmyfryis"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"

llm = ChatOpenAI(model="Qwen/Qwen2.5-7B-Instruct", verbose=True, temperature=0.8)


async def chatbot(state: AgentState) -> AsyncGenerator[dict[str, list[AIMessage]], Any]:
    messages = state["messages"]
    print(f"messages: {messages}")
    full_message = ""

    async for chunk in llm.astream(messages):
        full_message += chunk.content
        yield {"messages": [chunk.content]}
    print(f"state: {state}")
    print(f"full_message: {full_message}")
    # yield {"messages": full_message}
