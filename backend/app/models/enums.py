# Canvas Learning System - Error Type Enums
# Story 12.G.2: 增强错误处理与友好提示
# Source: specs/api/agent-api.openapi.yml:617-627
# Source: docs/architecture/decisions/ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md
"""
Agent Error Type Enumeration aligned with ADR-009 ErrorCode.

This module defines error types for the Agent system with:
- ADR-009 aligned naming conventions
- User-friendly message mapping
- Retry classification (RETRYABLE vs NON_RETRYABLE)
"""

from enum import Enum
from typing import Dict


class AgentErrorType(str, Enum):
    """
    Agent错误类型枚举 (对齐ADR-009 ErrorCode)

    来源: specs/api/agent-api.openapi.yml:617-627
    参考: docs/architecture/decisions/ADR-009-ERROR-HANDLING-RETRY-STRATEGY.md

    ErrorCategory分类:
    - RETRYABLE: 可重试错误 (网络、超时、速率限制)
    - NON_RETRYABLE: 不可重试错误 (配置、格式)
    - FATAL: 致命错误 (文件缺失)
    """

    # 配置类错误 (NON_RETRYABLE)
    CONFIG_MISSING = "CONFIG_MISSING"           # 对应ADR-009: 2001
    FILE_NOT_FOUND = "FILE_NOT_FOUND"           # 对应ADR-009: 3001

    # LLM调用错误 (RETRYABLE)
    LLM_TIMEOUT = "LLM_TIMEOUT"                 # 对应ADR-009: 1002
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"           # 对应ADR-009: 1001

    # LLM响应错误 (NON_RETRYABLE)
    LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"  # 对应ADR-009: 1004

    # 网络错误 (RETRYABLE)
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"         # 对应ADR-009: 4001

    # 未知错误
    UNKNOWN = "UNKNOWN"                         # 9999

    @property
    def is_retryable(self) -> bool:
        """
        判断错误是否可重试 (来自ADR-009 ErrorCategory)

        RETRYABLE类型:
        - LLM_TIMEOUT: API调用超时，可重试
        - LLM_RATE_LIMIT: 速率限制，等待后重试
        - NETWORK_TIMEOUT: 网络超时，可重试

        Returns:
            bool: True if error is retryable
        """
        return self in {
            AgentErrorType.LLM_TIMEOUT,
            AgentErrorType.LLM_RATE_LIMIT,
            AgentErrorType.NETWORK_TIMEOUT,
        }

    @property
    def user_message(self) -> str:
        """
        返回用户友好消息 (Story 12.G.2 AC1)

        Returns:
            str: Chinese user-friendly error message
        """
        messages: Dict[AgentErrorType, str] = {
            AgentErrorType.CONFIG_MISSING: "请在插件设置中配置 API Key",
            AgentErrorType.FILE_NOT_FOUND: "Agent 模板文件缺失",
            AgentErrorType.LLM_TIMEOUT: "AI 响应超时，请重试",
            AgentErrorType.LLM_RATE_LIMIT: "请求过于频繁，请稍后重试",
            AgentErrorType.LLM_INVALID_RESPONSE: "AI 响应格式异常",
            AgentErrorType.NETWORK_TIMEOUT: "网络连接失败，请检查网络",
            AgentErrorType.UNKNOWN: "发生未知错误",
        }
        return messages.get(self, "发生未知错误")

    @property
    def adr_code(self) -> int:
        """
        返回ADR-009定义的错误码

        Returns:
            int: ADR-009 error code number
        """
        codes: Dict[AgentErrorType, int] = {
            AgentErrorType.CONFIG_MISSING: 2001,
            AgentErrorType.FILE_NOT_FOUND: 3001,
            AgentErrorType.LLM_TIMEOUT: 1002,
            AgentErrorType.LLM_RATE_LIMIT: 1001,
            AgentErrorType.LLM_INVALID_RESPONSE: 1004,
            AgentErrorType.NETWORK_TIMEOUT: 4001,
            AgentErrorType.UNKNOWN: 9999,
        }
        return codes.get(self, 9999)

    @property
    def error_category(self) -> str:
        """
        返回ADR-009定义的错误类别

        Returns:
            str: ErrorCategory (RETRYABLE, NON_RETRYABLE, FATAL)
        """
        if self == AgentErrorType.FILE_NOT_FOUND:
            return "FATAL"
        elif self.is_retryable:
            return "RETRYABLE"
        else:
            return "NON_RETRYABLE"
