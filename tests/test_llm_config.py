"""Tests for llm_config.py."""

import pytest
from llm_config import ConfigError, get_llm_config


class TestGetLLMConfig:
    def test_missing_api_key_raises(self):
        with pytest.raises(ConfigError, match="DEEPSEEK_API_KEY"):
            get_llm_config()

    def test_defaults(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        config = get_llm_config()
        assert config["api_key"] == "sk-test"
        assert config["base_url"] == "https://api.deepseek.com"
        assert config["model"] == "deepseek-v4-flash"
        assert config["timeout"] == 120
        assert config["max_retries"] == 3

    def test_custom_model_and_timeout(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        monkeypatch.setenv("LLM_MODEL", "deepseek-v4-pro")
        monkeypatch.setenv("LLM_TIMEOUT", "60")
        config = get_llm_config()
        assert config["model"] == "deepseek-v4-pro"
        assert config["timeout"] == 60
