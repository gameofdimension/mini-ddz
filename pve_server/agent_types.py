"""Agent type constants used across the codebase."""

from typing import Literal

AgentType = Literal["deep", "llm", "random"]

DEEP = "deep"
LLM = "llm"
RANDOM = "random"

ALL = (DEEP, LLM, RANDOM)


def is_valid(value: str) -> bool:
    return value in ALL


def validate(value: str) -> str:
    if not is_valid(value):
        raise ValueError(f"Invalid agent type '{value}', must be one of: {', '.join(ALL)}")
    return value
