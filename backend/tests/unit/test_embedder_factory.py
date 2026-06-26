"""可切换 embedder 工厂单测 (2026-06-26): 按 EMBEDDER_PROVIDER 构造正确后端。

纯构造验证, 不调网络 (OpenAIEmbedder/GeminiEmbedder 构造均不发请求)。
"""

from __future__ import annotations

import pytest

import app.graphiti.embedder_factory as ef


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in (
        "EMBEDDER_PROVIDER",
        "LOCAL_EMBEDDER_BASE_URL",
        "LOCAL_EMBEDDER_MODEL",
        "LOCAL_EMBEDDER_API_KEY",
        "OPENAI_API_KEY",
        "OPENAI_EMBEDDER_MODEL",
        "GEMINI_EMBEDDER_MODEL",
    ):
        monkeypatch.delenv(k, raising=False)


def test_get_provider_default_gemini(monkeypatch):
    assert ef.get_embedder_provider() == "gemini"


def test_get_provider_normalizes_case(monkeypatch):
    monkeypatch.setenv("EMBEDDER_PROVIDER", "  LOCAL  ")
    assert ef.get_embedder_provider() == "local"


def test_default_builds_gemini():
    from graphiti_core.embedder.gemini import GeminiEmbedder

    e = ef.build_embedder("dummy-key")
    assert isinstance(e, GeminiEmbedder)


def test_local_builds_openai_embedder_with_base_url(monkeypatch):
    from graphiti_core.embedder.openai import OpenAIEmbedder

    monkeypatch.setenv("EMBEDDER_PROVIDER", "local")
    monkeypatch.setenv(
        "LOCAL_EMBEDDER_BASE_URL", "http://host.docker.internal:11434/v1"
    )
    monkeypatch.setenv("LOCAL_EMBEDDER_MODEL", "bge-m3")
    e = ef.build_embedder()
    assert isinstance(e, OpenAIEmbedder)
    assert e.config.base_url == "http://host.docker.internal:11434/v1"
    assert e.config.embedding_model == "bge-m3"
    assert e.config.embedding_dim == 1024  # 与存量 1024 维一致


def test_local_defaults_to_bge_m3_and_ollama(monkeypatch):
    from graphiti_core.embedder.openai import OpenAIEmbedder

    monkeypatch.setenv("EMBEDDER_PROVIDER", "local")
    e = ef.build_embedder()
    assert isinstance(e, OpenAIEmbedder)
    assert e.config.embedding_model == "bge-m3"
    assert "11434" in (e.config.base_url or "")  # Ollama 默认端口


def test_openai_provider_uses_text_embedding_3_small(monkeypatch):
    from graphiti_core.embedder.openai import OpenAIEmbedder

    monkeypatch.setenv("EMBEDDER_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    e = ef.build_embedder()
    assert isinstance(e, OpenAIEmbedder)
    assert e.config.embedding_model == "text-embedding-3-small"
    assert e.config.embedding_dim == 1024


def test_custom_local_model_via_env(monkeypatch):
    monkeypatch.setenv("EMBEDDER_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_EMBEDDER_MODEL", "nomic-embed-text")
    e = ef.build_embedder()
    assert e.config.embedding_model == "nomic-embed-text"
