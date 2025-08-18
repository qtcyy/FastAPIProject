import json
from typing import List

import requests
from langchain.tools import tool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
import os
from fastmcp import Client
from .result_processor import process_mcp_result

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config import config as app_config

client = Client(app_config.mcp_server_url)


@tool
async def search_tool(query: str, config: RunnableConfig = None) -> str:
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
        url=app_config.search_api_url,
        headers={
            "Authorization": f"Bearer {app_config.search_api_key}",
        },
        json={"query": query, "search_service": "google", "max_results": 10},
    )
    response.raise_for_status()
    response = response.json()

    # 格式化搜索结果
    formatted_result = format_search_results(response, query)

    print(f"\n网页搜索内容：\n{formatted_result}")
    # writer(f"web search result: {formatted_result}")

    # 检查是否启用LLM总结功能
    summary_enabled = False
    if config and config.get("configurable"):
        summary_enabled = config["configurable"].get("summary_with_llm", False)

    print(f"🤖 LLM智能总结功能状态: {'启用' if summary_enabled else '关闭'}")

    if summary_enabled:
        # llm再提炼
        print("🔄 正在使用LLM进行智能总结...")
        answer = await summary_with_llm(formatted_result)
        return answer
    else:
        # 直接返回格式化结果
        print("📄 返回原始格式化搜索结果")
        return formatted_result


async def summary_with_llm(response: str) -> str:
    """
    使用LLM对搜索结果进行智能总结和提炼

    :param response: 格式化的搜索结果文本
    :return: LLM总结后的精炼内容
    """
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """你是一个专业的信息总结助手。请对提供的搜索结果进行智能总结和提炼：

1. 提取最核心、最有价值的信息
2. 去除重复和冗余内容
3. 按重要性排序组织信息
4. 保持客观中性，不添加个人观点
5. 使用清晰简洁的中文表达
6. 如果信息来源多样，请注明关键信息的来源

输出格式要求：
- 使用结构化的markdown格式
- 重要信息用粗体标记
- 适当使用列表和分段
- 控制在500字以内""",
                ),
                ("human", "请总结以下搜索结果：\n\n{search_content}"),
            ]
        )

        llm = ChatOpenAI(
            model="deepseek-ai/DeepSeek-V3",
            base_url=app_config.deepseek_api_base,
            api_key=app_config.deepseek_api_key,
            temperature=0.3,  # 降低温度以获得更一致的输出
            max_tokens=1000,
        )

        chain = prompt | llm | StrOutputParser()
        print("summary_with_llm")
        summary_result = await chain.ainvoke({"search_content": response})

        # 组合总结和原始链接信息
        combined_result = f"""## 🤖 智能总结

{summary_result.strip()}

---

## 📚 详细搜索结果

{response}"""

        print(f"\n=== LLM总结结果 ===")
        print(f"原始搜索结果长度: {len(response)} 字符")
        print(f"总结后内容长度: {len(summary_result)} 字符")
        print(f"总结内容:\n{summary_result}")
        print(f"=== 总结结束 ===\n")

        return combined_result

    except Exception as e:
        print(f"LLM总结失败: {e}")
        # 如果LLM总结失败，返回原始格式化结果
        return response


async def summary_crawled_content(content: str) -> str:
    """
    使用LLM对网页爬取内容进行智能总结和提炼

    :param content: 格式化的网页爬取内容
    :return: LLM总结后的精炼内容
    """
    try:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """你是一个专业的网页内容总结助手。请对提供的网页爬取内容进行智能总结和分析：

1. 提取每个网页的核心信息和关键要点
2. 去除重复、冗余和无关内容
3. 识别网页间的关联性和互补性
4. 按重要性和逻辑顺序组织信息
5. 保持客观中性，准确传达原文意思
6. 使用清晰简洁的中文表达
7. 如果多个网页涉及同一主题，请进行综合分析

输出格式要求：
- 使用结构化的markdown格式
- 重要信息用粗体标记
- 适当使用列表和分段
- 为每个关键信息标注来源网页
- 控制总结内容在800字以内""",
                ),
                ("human", "请总结分析以下网页爬取内容：\n\n{crawled_content}"),
            ]
        )

        llm = ChatOpenAI(
            model="deepseek-ai/DeepSeek-V3",
            base_url=app_config.deepseek_api_base,
            api_key=app_config.deepseek_api_key,
            temperature=0.3,  # 降低温度以获得更一致的输出
            max_tokens=1500,
        )

        chain = prompt | llm | StrOutputParser()
        summary_result = await chain.ainvoke({"crawled_content": content})

        # 组合总结和原始内容信息
        combined_result = f"""## 🤖 智能总结分析

{summary_result.strip()}

---

## 📚 详细网页内容

{content}"""

        print(f"\n=== 网页内容LLM总结结果 ===")
        print(f"原始网页内容长度: {len(content)} 字符")
        print(f"总结后内容长度: {len(summary_result)} 字符")
        print(f"总结内容:\n{summary_result}")
        print(f"=== 网页总结结束 ===\n")

        return combined_result

    except Exception as e:
        print(f"网页内容LLM总结失败: {e}")
        # 如果LLM总结失败，返回原始格式化结果
        return content


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
async def web_crawler(links: List[str], config: RunnableConfig = None) -> str:
    """
    高效批量网页内容抓取工具 - 深度解析网页信息并智能提取关键内容

    功能特点：
    - 支持同时抓取多个网页链接的完整内容
    - 自动提取网页标题、正文内容和关键信息段落
    - 智能清理无关内容（广告、导航等），专注核心信息
    - 结构化输出，便于阅读和进一步处理
    - 自动处理缺失标题，从URL推断页面主题
    - 🤖 支持LLM智能总结：根据配置可开启智能总结功能，提取关键信息并去除冗余内容

    使用场景：
    - 获取搜索结果页面的详细内容
    - 收集多个相关网页的完整信息
    - 提取文章、新闻、产品页面的核心内容
    - 对比分析不同网站的信息
    - 通过LLM总结快速理解多个网页的核心内容

    :param links: 需要抓取的网页URL列表，支持HTTP/HTTPS协议
    :param config: 运行配置，包含summary_with_llm参数控制是否启用LLM总结
    :return: 结构化的网页内容字符串，包含每个页面的标题、链接、内容摘要和信息来源标注。
            如启用LLM总结，将返回智能总结分析 + 原始详细内容

    注意：建议一次抓取不超过5个链接，确保响应速度和内容质量
    """
    crawl_request = [{"url": link} for link in links]
    response = requests.post(
        url=app_config.crawl_api_url,
        headers={
            "Authorization": f"Bearer {app_config.search_api_key}",
        },
        json=crawl_request,
    )
    response.raise_for_status()
    response = response.json()
    print(f"\n网页爬取原始内容:\n{response}")

    # 处理和格式化网页内容
    formatted_content = format_crawled_content(response)
    print(f"\n格式化后的网页内容:\n{formatted_content}")

    # 检查是否启用LLM总结功能
    summary_enabled = False
    if config and config.get("configurable"):
        summary_enabled = config["configurable"].get("summary_with_llm", False)

    print(f"🤖 LLM智能总结功能状态: {'启用' if summary_enabled else '关闭'}")

    if summary_enabled:
        # 使用LLM进行智能总结
        print("🔄 正在使用LLM对网页内容进行智能总结...")
        summarized_content = await summary_crawled_content(formatted_content)
        return summarized_content
    else:
        # 直接返回格式化结果
        print("📄 返回原始格式化网页内容")
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
        crawl_results = (
            raw_response.get("results", []) if "results" in raw_response else []
        )

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
