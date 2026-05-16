"""Configuration for LLMAgent, read from environment variables."""

import os


def get_llm_config():
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is required")

    return {
        "api_key": api_key,
        "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "model": os.environ.get("LLM_MODEL", "deepseek-v4-flash"),
        "timeout": int(os.environ.get("LLM_TIMEOUT", "120")),
        "max_retries": int(os.environ.get("LLM_MAX_RETRIES", "3")),
    }
