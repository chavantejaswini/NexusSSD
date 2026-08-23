"""Summary agent — composes the final natural-language answer.

Uses an LLM when one is configured (fluent prose grounded in the gathered
context); otherwise falls back to a deterministic template so the assistant works
fully offline.
"""

from __future__ import annotations

import json

from app.agents.state import ChatState
from app.services.llm import get_llm

_SYSTEM = (
    "You are NexusSSD, a fleet health copilot for storage engineers. Answer the "
    "user's question using ONLY the provided context (SQL results, predictions, and "
    "documentation excerpts). Be concise and specific, cite drive serials and "
    "numbers, and when documentation is provided, ground recommendations in it. If "
    "the context is insufficient, say so."
)


def _format_sql(result: dict) -> str:
    intent = result.get("intent", "query")
    rows = result.get("rows", [])
    if not rows:
        return "No matching records were found."
    preview = rows[:8]
    return f"{intent.replace('_', ' ').title()}: " + "; ".join(
        ", ".join(f"{k}={v}" for k, v in row.items()) for row in preview
    )


def _format_prediction(result: dict) -> str:
    mode = result.get("mode")
    if mode == "single":
        r = result["result"]
        return (
            f"Drive {result['drive']} failure probability "
            f"{r['failure_probability']:.0%} ({r['band']} risk) within "
            f"{r['horizon_days']} days."
        )
    if mode == "fleet":
        rows = result.get("rows", [])[:5]
        if not rows:
            return "No predictions are available yet."
        return "Highest-risk drives: " + "; ".join(
            f"{row['serial_number']} {row['failure_probability']:.0%}" for row in rows
        )
    return result.get("note", "Prediction unavailable.")


def _format_rag(chunks: list[dict]) -> tuple[str, list[str]]:
    if not chunks:
        return "", []
    top = chunks[0]
    sources = list(dict.fromkeys(c["source"] for c in chunks))
    snippet = top["chunk_text"].strip().replace("\n", " ")
    if len(snippet) > 300:
        snippet = snippet[:300] + "…"
    return snippet, sources


def _build_context(state: ChatState) -> str:
    parts: dict[str, object] = {}
    if state.get("sql_result"):
        parts["sql"] = state["sql_result"]
    if state.get("prediction_result"):
        parts["prediction"] = state["prediction_result"]
    if state.get("rag_result"):
        parts["documentation"] = state["rag_result"]
    return json.dumps(parts, indent=2, default=str)


def compose_answer(state: ChatState) -> str:
    llm = get_llm()
    if llm is not None:
        context = _build_context(state)
        return llm.complete(_SYSTEM, f"Question: {state['query']}\n\nContext:\n{context}").strip()

    # Template fallback.
    lines: list[str] = []
    if state.get("sql_result"):
        lines.append(_format_sql(state["sql_result"]))
    if state.get("prediction_result"):
        lines.append(_format_prediction(state["prediction_result"]))
    if state.get("rag_result"):
        snippet, sources = _format_rag(state["rag_result"])
        if snippet:
            lines.append(f"Guidance: {snippet}")
            if sources:
                lines.append(f"Sources: {', '.join(sources)}")
    if not lines:
        return "I couldn't find relevant fleet data or documentation for that question."
    return "\n".join(lines)
