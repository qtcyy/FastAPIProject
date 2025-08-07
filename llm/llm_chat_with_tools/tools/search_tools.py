import requests
from langchain.tools import tool

search_url = "https://api.search1api.com/search"
crawl_url = "https://api.search1api.com/crawl"
search_api_key = "F016AD79-D8F4-4A2E-B53F-8578A4D43DDB"


@tool
async def search_tool(query: str) -> str:
    """
    从网上搜索内容
    :param query: 要搜索的内容
    :return: 搜索引擎给出的结果
    """
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
    for i, res in enumerate(response["results"]):
        result += str(i + 1) + " "
        result += "title: " + res["title"] + " "
        result += "snippet: " + res["snippet"] + " "
        result += "link: " + res["link"] + "\n"
        result += "\n"

    print(f"网页搜索内容：{result}")
    return result


@tool
def web_crawler(link: str) -> str:
    """
    网页访问工具，可以使用该工具访问具体网页的内容
    :param link: 网页地址
    :return: 网页内容
    """
    response = requests.post(
        url=crawl_url,
        headers={
            "Authorization": f"Bearer {search_api_key}",
        },
        json={"url": link},
    )
    response.raise_for_status()
    response = response.json()
    # print(f"response: {response}")

    print(f"网页访问内容：{response['results']['content']}")
    return response["results"]["content"]
