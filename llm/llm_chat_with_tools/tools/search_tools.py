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
    批量网页访问工具，获取网页详细内容并进行结构化处理
    :param links: 链接字符串数组
    :return: 格式化后的网页内容，包含标题、URL、主要内容和关键信息
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
    print(f"\n网页爬取原始内容:\n{response}")

    # 处理和格式化网页内容
    formatted_content = format_crawled_content(response)
    print(f"\n格式化后的网页内容:\n{formatted_content}")

    return formatted_content


def format_crawled_content(raw_response) -> str:
    """
    格式化爬取的网页内容，提取关键信息并结构化展示
    :param raw_response: 原始API响应
    :return: 结构化的网页内容字符串
    """
    if not raw_response or "results" not in raw_response:
        return "❌ 无法获取网页内容"

    results = raw_response.get("results", [])
    if not results:
        return "❌ 网页内容为空"

    formatted_pages = []

    for i, page_data in enumerate(results, 1):
        url = page_data.get("url", "未知URL")
        title = page_data.get("title", "无标题").strip()
        content = page_data.get("content", "").strip()

        # 处理标题
        if not title or title == "无标题":
            title = extract_title_from_url(url)

        # 处理内容
        if content:
            # 清理和截取内容
            cleaned_content = clean_content(content)
            # 提取关键段落
            key_paragraphs = extract_key_paragraphs(cleaned_content)
            content_summary = key_paragraphs[:2000]  # 限制长度
        else:
            content_summary = "无可用内容"

        # 格式化单个页面内容
        page_formatted = f"""
📄 **网页 {i}**: {title}
🔗 **链接**: {url}
📝 **内容摘要**:
{content_summary}
{'...' if len(content) > 2000 else ''}

---
"""
        formatted_pages.append(page_formatted)

    # 组合所有页面内容
    final_content = f"""
🌐 **网页爬取结果** (共 {len(results)} 个页面)

{''.join(formatted_pages)}

💡 **提示**: 以上内容来自指定网页的实时爬取，信息来源已标注。
"""

    return final_content.strip()


def extract_title_from_url(url: str) -> str:
    """从URL中提取可能的标题"""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            return f"{domain} - {path_parts[-1]}"
        return domain
    except:
        return "未知页面"


def clean_content(content: str) -> str:
    """清理网页内容，移除多余的空白和无用字符"""
    import re

    # 移除多余的空白字符
    content = re.sub(r"\s+", " ", content)
    # 移除特殊控制字符
    content = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", content)
    # 移除多余的换行
    content = re.sub(r"\n\s*\n", "\n\n", content)

    return content.strip()


def extract_key_paragraphs(content: str) -> str:
    """提取关键段落，优先显示较长的段落"""
    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

    # 过滤掉太短的段落（可能是导航、广告等）
    meaningful_paragraphs = [p for p in paragraphs if len(p) > 50]

    if not meaningful_paragraphs:
        meaningful_paragraphs = paragraphs[:5]  # 如果没有长段落，取前5个

    # 按长度排序，优先展示信息量大的段落
    meaningful_paragraphs.sort(key=len, reverse=True)

    # 取前几个最有意义的段落
    selected_paragraphs = meaningful_paragraphs[:3]

    return "\n\n".join(selected_paragraphs)


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
