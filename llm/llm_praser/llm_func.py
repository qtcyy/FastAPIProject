from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from llm.llm_praser.llm_schema import GraphState, Houses

import os

os.environ["OPENAI_API_KEY"] = "sk-klxcwiidfejlwzupobhtdvwkzdvwtsxqekqucykewmyfryis"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"

llm = ChatOpenAI(model="Qwen/Qwen2.5-7B-Instruct", verbose=True, temperature=0.8)
parser = PydanticOutputParser(pydantic_object=Houses)

prompt_template = PromptTemplate(
    template="根据给出的文本列出所需的信息.\n{format_instructions}\n{query}\n",
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


def init_prompt(state: GraphState) -> GraphState:
    """准备节点"""
    format_instruction = parser.get_format_instructions()
    prompt = prompt_template.format(
        query=state["query"], format_instruction=format_instruction
    )
    return {**state, "format_instructions": format_instruction, "prompt": prompt}


def llm_call(state: GraphState) -> GraphState:
    """llm调用"""
    try:
        llm_output = llm.invoke(state["prompt"]).content
        return {**state, "llm_output": llm_output}
    except Exception as e:
        return {**state, "error": str(e)}


def result_parse(state: GraphState) -> GraphState:
    """结果格式化"""
    try:
        parsed_result = parser.parse(state["llm_output"])
        return {**state, "parsed_result": parsed_result}
    except Exception as e:
        return {**state, "error": str(e)}


def should_end_after_llm(state: GraphState) -> str:
    if state.get("error"):
        return "end"
    return "continue"


def shout_end_after_parse(state: GraphState) -> str:
    if state.get("error"):
        return "end"
    return "continue"
