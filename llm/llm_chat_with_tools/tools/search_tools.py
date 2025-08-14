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
from .result_processor import process_mcp_result

search_url = "https://api.search1api.com/search"
crawl_url = "https://api.search1api.com/crawl"
search_api_key = "F016AD79-D8F4-4A2E-B53F-8578A4D43DDB"

client = Client("http://localhost:8080/mcp")


@tool
async def search_tool(query: str) -> str:
    """
    智能网络搜索引擎 - 实时获取最新、最相关的网络信息

    功能特点：
    - 基于Google搜索引擎，提供高质量、实时的搜索结果
    - 智能匹配用户查询意图，返回最相关的网页信息
    - 结构化展示搜索结果，包含标题、摘要和链接
    - 支持中文和英文查询，自动优化搜索策略
    - 获取最多10个高质量搜索结果

    适用场景：
    - 获取最新新闻、资讯和事件信息
    - 查找产品信息、价格对比和用户评价
    - 搜索技术文档、教程和解决方案
    - 获取实时天气、股价、汇率等动态信息
    - 查找学术资料、统计数据和研究报告

    :param query: 搜索关键词或问题描述，支持自然语言查询
    :return: 格式化的搜索结果列表，包含排名、标题、内容摘要和源网页链接

    使用建议：
    - 使用具体、明确的关键词以获得更精准的结果
    - 可以组合多个关键词提高搜索精度
    - 搜索后可配合web_crawler工具获取详细内容
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

    # 格式化搜索结果
    formatted_result = format_search_results(response, query)

    print(f"\n网页搜索内容：\n{formatted_result}")
    # writer(f"web search result: {formatted_result}")
    return formatted_result


def format_search_results(response, query: str) -> str:
    """
    格式化搜索结果，提供结构化和易读的输出
    :param response: API响应结果
    :param query: 搜索查询
    :return: 格式化的搜索结果字符串
    """
    if not response or "results" not in response:
        return "❌ 搜索失败，未能获取到结果"

    results = response.get("results", [])
    if not results:
        return f"🔍 未找到与 '{query}' 相关的搜索结果"

    # 构建格式化的搜索结果
    formatted_output = f"""
🔍 **搜索查询**: {query}
📊 **找到 {len(results)} 个相关结果**

"""

    for i, res in enumerate(results, 1):
        title = res.get("title", "无标题").strip()
        snippet = res.get("snippet", "无摘要信息").strip()
        link = res.get("link", "")

        # 清理和优化摘要内容
        snippet = clean_snippet(snippet)

        formatted_output += f"""📄 **结果 {i}**: {title}
🔗 **链接**: {link}
📝 **摘要**: {snippet}

---

"""

    # 添加使用建议
    formatted_output += f"""
💡 **提示**: 
- 以上是最相关的 {len(results)} 个搜索结果
- 点击链接可访问原始网页获取完整信息
- 如需获取网页详细内容，可使用 web_crawler 工具
- 搜索结果按相关性排序，排名越靠前越相关
"""

    return formatted_output.strip()


def clean_snippet(snippet: str) -> str:
    """
    清理搜索结果摘要，移除多余字符和格式化文本
    :param snippet: 原始摘要文本
    :return: 清理后的摘要
    """
    import re

    if not snippet:
        return "暂无摘要信息"

    # 移除多余的空白字符
    snippet = re.sub(r"\s+", " ", snippet)

    # 移除特殊控制字符
    snippet = re.sub(r"[^\x00-\x7F\u4e00-\u9fff\u3400-\u4dbf]", "", snippet)

    # 限制长度，避免摘要过长
    if len(snippet) > 200:
        snippet = snippet[:197] + "..."

    return snippet.strip()


@tool
def web_crawler(links: List[str]) -> str:
    """
    高效批量网页内容抓取工具 - 深度解析网页信息并智能提取关键内容

    功能特点：
    - 支持同时抓取多个网页链接的完整内容
    - 自动提取网页标题、正文内容和关键信息段落
    - 智能清理无关内容（广告、导航等），专注核心信息
    - 结构化输出，便于阅读和进一步处理
    - 自动处理缺失标题，从URL推断页面主题

    使用场景：
    - 获取搜索结果页面的详细内容
    - 收集多个相关网页的完整信息
    - 提取文章、新闻、产品页面的核心内容
    - 对比分析不同网站的信息

    :param links: 需要抓取的网页URL列表，支持HTTP/HTTPS协议
    :return: 结构化的网页内容字符串，包含每个页面的标题、链接、内容摘要和信息来源标注

    注意：建议一次抓取不超过5个链接，确保响应速度和内容质量
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
    :param raw_response: 原始API响应 (批量爬取格式)
    :return: 结构化的网页内容字符串
    """
    if not raw_response:
        return "❌ 无法获取网页内容"

    # 处理批量爬取响应格式: [{"crawlParameters": {...}, "results": {...}}, ...]
    if isinstance(raw_response, list):
        crawl_results = raw_response
    else:
        # 兼容旧格式
        crawl_results = raw_response.get("results", []) if "results" in raw_response else []

    if not crawl_results:
        return "❌ 网页内容为空"

    formatted_pages = []

    for i, crawl_item in enumerate(crawl_results, 1):
        # 新格式：从 crawl_item 中提取 results
        if "results" in crawl_item:
            page_data = crawl_item["results"]
            crawl_params = crawl_item.get("crawlParameters", {})
            original_url = crawl_params.get("url", "未知URL")
        else:
            # 兼容旧格式
            page_data = crawl_item
            original_url = page_data.get("url", "未知URL")

        url = page_data.get("link", original_url)
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
🌐 **网页爬取结果** (共 {len(crawl_results)} 个页面)

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
async def query_student_avg_grade(
    class_name: str, process_result: bool = True, processing_mode: str = "formatted"
) -> str:
    """
    查询指定班级的平均成绩统计信息。

    此工具用于获取特定班级所有学生在语文、数学、英语三门科目的平均分数，
    以及该班级的学生总数。适用于教师查看班级整体学习情况、进行成绩分析等场景。

    Args:
        class_name (str): 要查询的班级名称，例如 "class_1"、"三年级一班" 等。
                         班级名称需要与数据库中存储的完全匹配。
        process_result (bool): 是否对结果进行处理，默认True
        processing_mode (str): 处理模式 (raw/summary/formatted/filtered/structured)，默认formatted

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

        # 如果启用结果处理，对原始结果进行处理
        if process_result:
            try:
                processed_result = await process_mcp_result(
                    tool_name="query_student_avg_grade",
                    result=json_str,
                    mode=processing_mode,
                )
                return processed_result
            except Exception as e:
                print(f"结果处理失败: {e}")
                return json_str

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


# async def test():
#     links = ["https://www.langchain.com/langgraph", "https://fastapi.tiangolo.com/"]
#     web_crawler(links)
#     # await label_extra("杭州天气")
#
#
# if __name__ == "__main__":
#     asyncio.run(test())
