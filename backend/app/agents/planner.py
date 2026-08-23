"""Planner agent — routes a query to the tools that should run.

Rule-based (deterministic, testable) intent detection. Returns an ordered list
drawn from {"sql", "prediction", "rag"}; the summary agent always runs.
"""

from __future__ import annotations

_RISK_WORDS = ("risk", "fail", "predict", "likely", "probability", "health", "at-risk")
_DOC_WORDS = (
    "why", "how", "recommend", "maintenance", "should", "explain", "cause",
    "what is", "what are", "documentation", "guidance", "replace", "wear", "smart",
)
_SQL_WORDS = (
    "how many", "list", "which", "count", "status", "hottest", "temperature",
    "alert", "failed", "top", "show", "fleet",
)


def plan(query: str) -> list[str]:
    q = query.lower()
    steps: list[str] = []

    if any(w in q for w in _SQL_WORDS) or any(w in q for w in _RISK_WORDS):
        steps.append("sql")
    if any(w in q for w in _RISK_WORDS):
        steps.append("prediction")
    if any(w in q for w in _DOC_WORDS):
        steps.append("rag")

    if not steps:
        # Sensible default: pull fleet facts and ground with docs.
        steps = ["sql", "rag"]
    return steps
