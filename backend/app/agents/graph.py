"""The LangGraph chat workflow and its runner.

Flow: planner -> sql -> prediction -> rag -> evaluation -> summary.
The evaluation agent may loop back to rag once if the answer is not yet grounded.
Each tool node no-ops unless the planner included it, so the plan controls which
agents actually do work while the graph shape stays fixed.
"""

from __future__ import annotations

import uuid

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents import planner
from app.agents.state import ChatState
from app.agents.summary import compose_answer
from app.agents.tools import Tools
from app.core.logging import get_logger
from app.models.chat import ChatHistory

logger = get_logger(__name__)

_MAX_RETRIES = 1


def _planner_node(state: ChatState) -> dict:
    steps = planner.plan(state["query"])
    return {"plan": steps, "retries": 0, "trace": [{"agent": "planner", "detail": {"plan": steps}}]}


def _sql_node(state: ChatState) -> dict:
    if "sql" not in state.get("plan", []):
        return {"trace": [{"agent": "sql", "detail": {"skipped": True}}]}
    result = state["tools"].sql(state["query"])
    return {
        "sql_result": result,
        "trace": [{"agent": "sql", "detail": {"intent": result.get("intent"), "rows": len(result.get("rows", []))}}],
    }


def _prediction_node(state: ChatState) -> dict:
    if "prediction" not in state.get("plan", []):
        return {"trace": [{"agent": "prediction", "detail": {"skipped": True}}]}
    result = state["tools"].prediction(state["query"])
    return {
        "prediction_result": result,
        "trace": [{"agent": "prediction", "detail": {"mode": result.get("mode")}}],
    }


def _rag_node(state: ChatState) -> dict:
    if "rag" not in state.get("plan", []):
        return {"trace": [{"agent": "rag", "detail": {"skipped": True}}]}
    result = state["tools"].rag(state["query"])
    return {
        "rag_result": result,
        "trace": [{"agent": "rag", "detail": {"chunks": len(result)}}],
    }


def _is_grounded(state: ChatState) -> bool:
    sql_ok = bool(state.get("sql_result") and state["sql_result"].get("rows"))
    pred = state.get("prediction_result")
    pred_ok = bool(pred and pred.get("mode") in ("single", "fleet"))
    rag_ok = bool(state.get("rag_result"))
    return sql_ok or pred_ok or rag_ok


def _evaluation_node(state: ChatState) -> dict:
    grounded = _is_grounded(state)
    retries = state.get("retries", 0)
    plan = list(state.get("plan", []))

    # If ungrounded and we haven't tried docs yet, retry once via RAG.
    if not grounded and "rag" not in plan and retries < _MAX_RETRIES:
        plan.append("rag")
        return {
            "evaluation": {"grounded": False, "action": "retry_rag"},
            "plan": plan,
            "retries": retries + 1,
            "route": "rag",
            "trace": [{"agent": "evaluation", "detail": {"grounded": False, "retry": "rag"}}],
        }

    return {
        "evaluation": {"grounded": grounded, "action": "finalize"},
        "route": "summary",
        "trace": [{"agent": "evaluation", "detail": {"grounded": grounded}}],
    }


def _summary_node(state: ChatState) -> dict:
    answer = compose_answer(state)
    return {"answer": answer, "trace": [{"agent": "summary", "detail": {"chars": len(answer)}}]}


def _route_after_eval(state: ChatState) -> str:
    return state.get("route", "summary")


def build_graph():
    graph = StateGraph(ChatState)
    graph.add_node("planner", _planner_node)
    graph.add_node("sql", _sql_node)
    graph.add_node("prediction", _prediction_node)
    graph.add_node("rag", _rag_node)
    graph.add_node("evaluation", _evaluation_node)
    graph.add_node("summary", _summary_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "sql")
    graph.add_edge("sql", "prediction")
    graph.add_edge("prediction", "rag")
    graph.add_edge("rag", "evaluation")
    graph.add_conditional_edges(
        "evaluation", _route_after_eval, {"rag": "rag", "summary": "summary"}
    )
    graph.add_edge("summary", END)
    return graph.compile()


_COMPILED = build_graph()


def run_chat(session: Session, query: str, session_id: str | None = None) -> dict:
    session_id = session_id or uuid.uuid4().hex
    tools = Tools(session)

    final: ChatState = _COMPILED.invoke({"query": query, "tools": tools, "trace": []})

    answer = final.get("answer", "")
    trace = final.get("trace", [])
    agents = [step["agent"] for step in trace]

    session.add(ChatHistory(session_id=session_id, role="user", content=query))
    session.add(
        ChatHistory(
            session_id=session_id,
            role="assistant",
            content=answer,
            agent_trace={
                "plan": final.get("plan", []),
                "evaluation": final.get("evaluation"),
                "trace": trace,
            },
        )
    )
    session.commit()

    logger.info("chat handled", extra={"session_id": session_id, "agents": agents})
    return {"session_id": session_id, "answer": answer, "agents": agents, "trace": trace}
