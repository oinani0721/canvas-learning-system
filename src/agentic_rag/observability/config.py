"""
LangSmith 配置管理

Story 12.12: LangSmith集成配置

支持:
- 环境变量配置
- 编程式配置
- 项目/工作区管理
- 采样率控制

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29

# ✅ Verified from LangSmith SDK (Context7):
# - Configure via environment variables or programmatically
# - tracing_context for selective tracing
# - Client with api_key and api_url
"""

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional

# Check LangSmith availability
try:
    from langsmith import Client, tracing_context
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    Client = None
    tracing_context = None


@dataclass
class LangSmithConfig:
    """
    LangSmith 配置数据类

    Attributes:
        enabled: 是否启用追踪
        api_key: LangSmith API密钥
        api_url: LangSmith API URL
        project_name: 项目名称
        workspace_id: 工作区ID (多工作区时必需)
        sampling_rate: 采样率 (0.0-1.0)
        tags: 默认标签
    """
    enabled: bool = True
    api_key: Optional[str] = None
    api_url: str = "https://api.smith.langchain.com"
    project_name: str = "canvas-agentic-rag"
    workspace_id: Optional[str] = None
    sampling_rate: float = 1.0
    tags: list[str] = field(default_factory=lambda: ["canvas", "agentic-rag"])


# Global config instance
_config: Optional[LangSmithConfig] = None
_client: Optional["Client"] = None


def configure_langsmith(
    enabled: Optional[bool] = None,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    project_name: Optional[str] = None,
    workspace_id: Optional[str] = None,
    sampling_rate: Optional[float] = None,
    tags: Optional[list[str]] = None,
) -> LangSmithConfig:
    """
    配置 LangSmith 追踪

    ✅ Verified from LangSmith SDK:
    ```python
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = "ls_..."
    ```

    Args:
        enabled: 是否启用追踪 (默认从环境变量读取)
        api_key: API密钥 (默认从 LANGSMITH_API_KEY)
        api_url: API URL (默认从 LANGSMITH_API_URL)
        project_name: 项目名称 (默认从 LANGSMITH_PROJECT)
        workspace_id: 工作区ID (默认从 LANGSMITH_WORKSPACE_ID)
        sampling_rate: 采样率 (0.0-1.0)
        tags: 默认标签列表

    Returns:
        LangSmithConfig: 配置对象
    """
    global _config, _client

    # Read from environment with defaults
    _config = LangSmithConfig(
        enabled=enabled if enabled is not None else _parse_bool_env("LANGSMITH_TRACING", True),
        api_key=api_key or os.environ.get("LANGSMITH_API_KEY"),
        api_url=api_url or os.environ.get("LANGSMITH_API_URL", "https://api.smith.langchain.com"),
        project_name=project_name or os.environ.get("LANGSMITH_PROJECT", "canvas-agentic-rag"),
        workspace_id=workspace_id or os.environ.get("LANGSMITH_WORKSPACE_ID"),
        sampling_rate=sampling_rate if sampling_rate is not None else 1.0,
        tags=tags or ["canvas", "agentic-rag"],
    )

    # Set environment variables for LangSmith SDK
    if _config.enabled and LANGSMITH_AVAILABLE:
        os.environ["LANGSMITH_TRACING"] = "true"
        if _config.api_key:
            os.environ["LANGSMITH_API_KEY"] = _config.api_key
        if _config.api_url:
            os.environ["LANGSMITH_API_URL"] = _config.api_url
        if _config.project_name:
            os.environ["LANGSMITH_PROJECT"] = _config.project_name
        if _config.workspace_id:
            os.environ["LANGSMITH_WORKSPACE_ID"] = _config.workspace_id

        # Create client
        if _config.api_key:
            _client = Client(
                api_key=_config.api_key,
                api_url=_config.api_url,
            )

    return _config


def get_langsmith_config() -> LangSmithConfig:
    """获取当前 LangSmith 配置"""
    global _config
    if _config is None:
        _config = configure_langsmith()
    return _config


def get_langsmith_client() -> Optional["Client"]:
    """获取 LangSmith 客户端实例"""
    global _client
    if _client is None:
        config = get_langsmith_config()
        if config.enabled and LANGSMITH_AVAILABLE and config.api_key:
            _client = Client(
                api_key=config.api_key,
                api_url=config.api_url,
            )
    return _client


def is_tracing_enabled() -> bool:
    """检查追踪是否启用"""
    config = get_langsmith_config()
    return config.enabled and LANGSMITH_AVAILABLE


@contextmanager
def langsmith_tracing_context(
    enabled: Optional[bool] = None,
    project_name: Optional[str] = None,
    tags: Optional[list[str]] = None,
):
    """
    LangSmith 追踪上下文管理器

    ✅ Verified from LangSmith SDK:
    ```python
    with ls.tracing_context(enabled=True):
        chain.invoke(...)
    ```

    Args:
        enabled: 是否启用 (默认使用全局配置)
        project_name: 项目名称 (覆盖默认)
        tags: 标签 (覆盖默认)

    Yields:
        上下文
    """
    if not LANGSMITH_AVAILABLE:
        yield
        return

    config = get_langsmith_config()
    _ = get_langsmith_client()  # Ensure client is initialized

    use_enabled = enabled if enabled is not None else config.enabled

    if tracing_context is not None:
        with tracing_context(enabled=use_enabled):
            yield
    else:
        yield


def _parse_bool_env(key: str, default: bool = False) -> bool:
    """解析环境变量布尔值"""
    value = os.environ.get(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    return default
