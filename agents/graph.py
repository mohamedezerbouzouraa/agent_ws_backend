from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from agents.state import AgentState
from agents.tools import TOOLS
from config import get_settings
settings = get_settings()

def _build_llm():
    if settings.MODEL_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=settings.MODEL_NAME,
            api_key=settings.ANTHROPIC_API_KEY,
            streaming=True,
        )
    else:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            streaming=True,)
    return llm.bind_tools(TOOLS)


SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are a helpful assistant with access to tools. "
        "Use tools when they help answer the user accurately. "
        "Be concise."
    )
)
_llm = _build_llm()
async def agent_node(state: AgentState) -> dict:
    """Call the LLM with the full message history."""
    messages = state["messages"]
    response = await _llm.ainvoke([SYSTEM_PROMPT, *messages])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(TOOLS))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


compiled_graph = build_graph()
