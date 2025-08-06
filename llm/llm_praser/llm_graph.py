from langgraph.constants import START, END
from langgraph.graph import StateGraph

from llm.llm_praser.llm_func import init_prompt, llm_call, result_parse, should_end_after_llm, shout_end_after_parse
from llm.llm_praser.llm_schema import GraphState


def create_graph():
    graph_builder = StateGraph(GraphState)
    graph_builder.add_node("init_prompt", init_prompt)
    graph_builder.add_node("llm_call", llm_call)
    graph_builder.add_node("result_parse", result_parse)
    # graph_builder.add_node("tool_node", tool_node)

    graph_builder.add_edge(START, "init_prompt")
    graph_builder.add_edge("init_prompt", "llm_call")
    # graph_builder.add_conditional_edges("llm_call", tools_condition)
    # graph_builder.add_edge("tool_node", "llm_call")
    graph_builder.add_conditional_edges(
        "llm_call", should_end_after_llm, {"end": END, "continue": "result_parse"}
    )
    graph_builder.add_conditional_edges(
        "result_parse", shout_end_after_parse, {"end": END, "continue": END}
    )

    return graph_builder.compile()
