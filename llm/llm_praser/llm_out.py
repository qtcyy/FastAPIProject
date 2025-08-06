from llm.llm_praser.llm_graph import create_graph
from llm.llm_praser.llm_schema import Houses, GraphState


class LLMOut:
    def __init__(self):
        pass

    async def llm_out(self, query: str) -> Houses:
        """
        返回llm数据
        :param query: 输入llm的查询信息
        :return: 房屋信息类
        """
        graph = create_graph()
        initial_state: GraphState = {
            "query": query,
            "format_instructions": "",
            "llm_output": "",
            "prompt": "",
            "parsed_result": None,
            "error": None,
        }
        result: GraphState = await graph.ainvoke(initial_state)
        if result.get("error"):
            raise Exception(f"处理失败: {result.get('error')}")
        else:
            parsed = result["parsed_result"]
            return parsed
