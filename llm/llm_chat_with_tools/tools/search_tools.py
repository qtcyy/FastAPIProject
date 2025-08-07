import requests
from langchain.tools import tool


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
