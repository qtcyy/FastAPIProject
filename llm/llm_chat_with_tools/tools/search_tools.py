import asyncio
import json
from typing import List

import requests
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
import os
from fastmcp import Client

search_url = "https://api.search1api.com/search"
crawl_url = "https://api.search1api.com/crawl"
search_api_key = "F016AD79-D8F4-4A2E-B53F-8578A4D43DDB"

client = Client("http://localhost:8080/mcp")


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
    :param links: 链接字符串数组
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
    # tool_prompt = ChatPromptTemplate.from_messages(
    #     [
    #         (
    #             "system",
    #             "你是一个帮助我提取信息的助手，我给你的内容是网页的内容，请提取出有效信息并返回。注意保留原先的json格式。",
    #         ),
    #         ("human", "{input}"),
    #     ]
    # )
    # tool_llm = ChatOpenAI(
    #     model="Qwen/Qwen2.5-7B-Instruct",
    #     base_url="https://api.siliconflow.cn/v1",
    #     api_key="sk-klxcwiidfejlwzupobhtdvwkzdvwtsxqekqucykewmyfryis",
    # )
    # chain = tool_prompt | tool_llm
    # config = RunnableConfig(configurable={"thread_id": "tool_thread"})
    #
    # try:
    #     tool_response = chain.invoke(input={"input": response}, config=config)
    #     print(f"工具llm返回内容:\n{tool_response.content}")
    #     return f"response: {tool_response.content}"
    # except Exception as e:
    #     print(f"Error on tool llm: {str(e)}")
    #     return f"Error on tool llm: {str(e)}"
    return response


@tool
async def query_student_avg_grade(class_name: str) -> str:
    """
    查询指定班级的平均成绩统计信息。

    此工具用于获取特定班级所有学生在语文、数学、英语三门科目的平均分数，
    以及该班级的学生总数。适用于教师查看班级整体学习情况、进行成绩分析等场景。

    Args:
        class_name (str): 要查询的班级名称，例如 "class_1"、"三年级一班" 等。
                         班级名称需要与数据库中存储的完全匹配。

    Returns:
        str: 返回包含班级平均成绩信息的JSON字符串，包含以下字段：
            - class_name: 班级名称
            - chinese_avg: 语文平均分（保留2位小数）
            - math_avg: 数学平均分（保留2位小数）
            - english_avg: 英语平均分（保留2位小数）

    Example:
        输入: "class_1"
        输出: {
            "class_name": "class_1",
            "chinese_avg": 85.67,
            "math_avg": 78.92,
            "english_avg": 82.45,
        }

    Usage Scenarios:
        - 教师查看班级整体学习水平
        - 对比不同班级的成绩表现
        - 生成班级成绩报告
        - 分析各科目强弱项

    Note:
        - 如果班级不存在或没有成绩数据，将返回相应的错误信息
        - 平均分计算基于该班级所有有效的考试成绩记录
        - 确保输入的班级名称准确无误
    """
    async with client:
        result = await client.call_tool(
            "get_class_average_grade", {"class_name": class_name}
        )
        json_str = result.content[0].text
        return json_str


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


async def test():
    links = ["https://www.langchain.com/langgraph", "https://fastapi.tiangolo.com/"]
    web_crawler(links)
    # await label_extra("杭州天气")


if __name__ == "__main__":
    asyncio.run(test())
