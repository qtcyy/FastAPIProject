import os

import requests
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.prebuilt import ToolNode

from llm.llm_chat.chat_schema import AgentState

os.environ["OPENAI_API_KEY"] = "sk-klxcwiidfejlwzupobhtdvwkzdvwtsxqekqucykewmyfryis"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"


@tool
async def search_tool(query: str) -> str:
    """
    从网上搜索内容
    :param query: 要搜索的内容
    :return: 搜索引擎给出的结果
    """
    search_url = "https://api.search1api.com/search"
    search_api_key = "F016AD79-D8F4-4A2E-B53F-8578A4D43DDB"
    response = requests.post(
        url=search_url,
        headers={
            "Authorization": f"Bearer {search_api_key}",
        },
        json={"query": query, "search_service": "google"},
    )
    response.raise_for_status()
    response = response.json()

    result = ""
    for res in response["results"]:
        result += res["title"]
        result += res["snippet"]
        result += "\n"
    return result


tools = [search_tool]
llm = ChatOpenAI(model="Qwen/Qwen2.5-7B-Instruct", verbose=True, temperature=0.8)
tool_node = ToolNode(tools=tools)
llm_with_tools = llm.bind_tools(tools=tools)


async def chatbot(state: AgentState) -> dict[str, BaseMessage]:
    messages = state["messages"]
    # full_message = ""
    return {"messages": await llm_with_tools.ainvoke(messages)}
    # async for chunk in llm.astream(messages):
    #     full_message += chunk.content
    #     yield {"messages": [chunk]}
    # print(f"state: {state}")
    # print(f"full_message: {full_message}")
    # yield {"messages": full_message}
    # return {"messages": [full_message]}
