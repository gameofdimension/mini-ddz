"""Configuration for LLMAgent, read from environment variables."""

import os


def get_llm_config():
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is required")

    raw_positions = os.environ.get("LLM_AGENT_POSITIONS", "0,1,2")
    llm_positions = [int(p.strip()) for p in raw_positions.split(",")]

    return {
        "api_key": api_key,
        "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "model": os.environ.get("LLM_MODEL", "deepseek-v4-pro"),
        "timeout": int(os.environ.get("LLM_TIMEOUT", "30")),
        "max_retries": int(os.environ.get("LLM_MAX_RETRIES", "3")),
        "llm_agent_positions": llm_positions,
    }
