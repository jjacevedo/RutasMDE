import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.prompts import SYSTEM_PROMPT
from agent.tools import calcular_ruta, consultar_movilidad

load_dotenv()

TOOLS = [calcular_ruta, consultar_movilidad]
MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
RECURSION_LIMIT = 25
SOURCES_PER_SEARCH = 2
MAX_RETRIES = 6


@lru_cache(maxsize=1)
def build_graph():
    llm = ChatGroq(model=MODEL_NAME, temperature=0, max_retries=MAX_RETRIES).bind_tools(TOOLS)

    def call_model(state: MessagesState) -> dict:
        messages = [SystemMessage(SYSTEM_PROMPT), *state["messages"]]
        return {"messages": [llm.invoke(messages)]}

    graph = StateGraph(MessagesState)
    graph.add_node("modelo", call_model)
    graph.add_node("herramientas", ToolNode(TOOLS))
    graph.add_edge(START, "modelo")
    graph.add_conditional_edges("modelo", tools_condition, {"tools": "herramientas", END: END})
    graph.add_edge("herramientas", "modelo")
    return graph.compile()


def _to_messages(chat_history: list) -> list:
    messages = []
    for turn in chat_history:
        if turn["role"] == "user":
            messages.append(HumanMessage(turn["content"]))
        elif turn["role"] == "assistant":
            messages.append(AIMessage(turn["content"]))
    return messages


def run_agent(user_message: str, chat_history: list) -> dict:
    history = _to_messages(chat_history)
    try:
        result = build_graph().invoke(
            {"messages": [*history, HumanMessage(user_message)]},
            {"recursion_limit": RECURSION_LIMIT},
        )
    except GraphRecursionError:
        return {
            "response": "No pude completar la consulta. ¿Puedes reformularla con más detalle?",
            "route": None,
            "sources": [],
            "tools": [],
        }

    route = None
    sources = []
    tools_used = []
    for message in result["messages"][len(history) + 1:]:
        if not isinstance(message, ToolMessage):
            continue
        tools_used.append(message.name)
        if message.artifact is None:
            continue
        if message.name == "calcular_ruta":
            route = message.artifact
        elif message.name == "consultar_movilidad":
            for chunk in message.artifact[:SOURCES_PER_SEARCH]:
                label = f"{chunk['titulo']} - {chunk['seccion']}"
                if label not in sources:
                    sources.append(label)

    return {
        "response": result["messages"][-1].content,
        "route": route,
        "sources": sources,
        "tools": tools_used,
    }
