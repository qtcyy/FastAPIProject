from langchain.tools import tool


@tool
async def calculate_tools(formula: str):
    """
    数学表达式计算工具，使用python中的eval(formula)进行计算
    :param formula: 数学表达式
    :return: 计算结果
    """
    return eval(formula)
