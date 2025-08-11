import asyncio
import json
from typing import List

import requests
from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer

search_url = "https://api.search1api.com/search"
crawl_url = "https://api.search1api.com/crawl"
search_api_key = "F016AD79-D8F4-4A2E-B53F-8578A4D43DDB"


@tool
async def search_tool(query: str) -> str:
    """
    搜索引擎工具，从网上搜索内容，返回内容包含（网页标题，网页简要内容，网页链接）
    :param query: 要搜索的内容
    :return: 搜索引擎给出的结果
    """
    # writer = get_stream_writer()
    # writer(f"web search: {query}")
    print(f"query: {query}")
    # await label_extra(query)
    response = requests.post(
        url=search_url,
        headers={
            "Authorization": f"Bearer {search_api_key}",
        },
        json={"query": query, "search_service": "google", "max_results": 10},
    )
    response.raise_for_status()
    response = response.json()

    result = ""
    for i, res in enumerate(response["results"]):
        result += str(i + 1) + " "
        result += "title: " + res["title"] + " "
        result += "snippet: " + res["snippet"] + " "
        result += "link: " + res["link"] + "\n"
        result += "\n"

    print(f"\n网页搜索内容：\n{result}")
    # writer(f"web search result: {result}")
    return result


@tool
def web_crawler(links: List[str]) -> str:
    """
    批量网页访问工具，可以使用该工具访问具体网页的内容
    :param links: 链接字符串序列
    :return: 序列中网页的内容
    """
    crawl_request = [{"url": link} for link in links]
    response = requests.post(
        url=crawl_url,
        headers={
            "Authorization": f"Bearer {search_api_key}",
        },
        json=crawl_request,
    )
    response.raise_for_status()
    response = response.json()
    print(f"\n网页爬取内容:\n{response}")

    # print(f"网页访问内容：{response['results']['content']}")
    return f"response: {response}"


async def label_extra(query):
    print(f"query2: {query}")
    llm = ChatOpenAI(
        model_name="Qwen/Qwen2.5-32B-Instruct",
        name="tool_llm",
        temperature=0.8,
        streaming=False,
        max_tokens=1024,
        base_url="https://api-inference.modelscope.cn/v1",
        api_key="a5a8fdf1-e914-4c1e-ac56-82888ec1be87",
    )
    config: RunnableConfig = {"configurable": {"thread_id": "tool_thread"}}
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"你是一个智能助手 专门用来对内容进行标签抽取 标签抽取方式有关键字抽取和语义抽取 特别是隐含语义抽取 然后返回标签列表\n"
                "要求：\n"
                "- 严格返回 JSON 数组格式"
                "- 禁止输出除 JSON 外的任何文字\n"
                "- 标签必须精炼准确",
            ),
            ("human", "{input}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    # res = await chain.ainvoke(input={"input": query})
    res = ""
    async for chunk in chain.astream(input={"input": query}, config=config):
        res += chunk
    print(f"label_extra: {type(res)}, {res}")
    res = json.loads(res)
    print(f"json res: {res}")
    return res


# async def test():
#     # links = ["https://www.langchain.com/langgraph", "https://fastapi.tiangolo.com/"]
#     # web_crawler(links)
#     await label_extra("杭州天气")
#
#
# if __name__ == "__main__":
#     asyncio.run(test())
