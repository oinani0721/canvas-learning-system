# Canvas Learning System - Configuration Management
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings pydantic-settings)
"""
Application configuration using Pydantic Settings.

This module provides centralized configuration management for the Canvas Learning System
backend API. Settings are loaded from environment variables and .env files.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#配置管理]
[Source: specs/api/fastapi-backend-api.openapi.yml]
"""

import json
import logging
import os
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator, model_validator

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings)
# Source: "from pydantic_settings import BaseSettings, SettingsConfigDict"
from pydantic_settings import BaseSettings, SettingsConfigDict

# Logger for config validation warnings
# [Source: docs/stories/21.5.2.story.md - AC-1]
logger = logging.getLogger(__name__)

# Calculate absolute project root path for reliable path resolution
# This ensures paths work regardless of where the backend is started from
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/app/
_BACKEND_DIR = os.path.dirname(_CONFIG_DIR)  # backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)  # Canvas/


#: ⛔⛔ 索引黑名单的**不可撤销硬底** (P1-02, Codex 对抗审查 2026-08-19)
#:
#: 问题: VAULT_INDEX_SKIP_DIRS 是 env 可**整体替换**的单一字符串 —— 设
#: `VAULT_INDEX_SKIP_DIRS=.git` 就能一次性撤掉全部黑名单。实测该 env 下
#: `检验白板/exam.md` 与 `验收单/uat.md` 双双变为 allowed。
#:
#: 这不是 A-9 引入的新缺陷: 检验白板/验收单 自 2026-07-10 检验白板 v1 审计起
#: 就与其它项同在一条逗号串里, 共享完全相同的可撤销性 —— 即**信息隔离铁律
#: (Karpicke d=1.50, 考题绝不能经 RAG 回流) 一直可被一行 env 撤销**。
#: 因此硬底的范围必须大于审查建议的「只锁 _待处理/_archive」。
#:
#: 防御层数实测 (决定了本集合的必要性排序):
#:   - 检验白板: 双层 —— 目录黑名单 + 读侧 exclude_doc_types=["whiteboard","exam_board"]
#:     (靠 `type: exam_board` frontmatter 或 exam_question_id 推断)
#:   - 验收单 / _待处理 / _archive: **单层** —— frontmatter 无 doc_type,
#:     读侧不挡, 目录黑名单是唯一防线, 撤掉即全裸
#:
#: 契约: env 只能**追加**黑名单, 不能移除本集合中的项。
#: 所有消费点必须走 Settings.effective_vault_skip_dirs(), 不要直接 split。
IMMUTABLE_VAULT_SKIP_DIRS: frozenset[str] = frozenset(
    {
        "检验白板",  # 信息隔离铁律 — 双层防御的第一层
        "验收单",  # 信息隔离铁律 — 单层防御, 撤掉即全裸
        "_待处理",  # A-9 收件箱暂存区 — 单层
        "_archive",  # A-9 下划线前缀归档 — 单层
        ".git",  # 仓库内部, 任何情况都不该进检索
        ".obsidian",  # Obsidian 配置与插件数据
    }
)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings)
    Pattern: Pydantic v2 BaseSettings with model_config for .env file loading.

    Attributes:
        PROJECT_NAME: Application name displayed in API responses
        PROJECT_DESCRIPTION: Application description for documentation
        VERSION: Application version (semver format)
        DEBUG: Enable debug mode (Swagger/ReDoc docs, detailed errors)
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        CORS_ORIGINS: Allowed CORS origins as comma-separated string
        CANVAS_BASE_PATH: Base path to Canvas files directory
        API_V1_PREFIX: API version prefix path
        MAX_CONCURRENT_REQUESTS: Maximum concurrent requests limit
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # Application Settings
    # ═══════════════════════════════════════════════════════════════════════════

    PROJECT_NAME: str = Field(
        default="Canvas Learning System API",
        description="Application name displayed in API responses and Swagger UI",
    )

    PROJECT_DESCRIPTION: str = Field(
        default="Multi-agent learning system backend using Feynman method",
        description="Application description for API documentation",
    )

    VERSION: str = Field(default="1.0.0", description="Application version (semver format)")

    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (Swagger/ReDoc docs, detailed errors)",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # FR-KG-04 Phase 2: Internal API key for sensitive endpoints
    # ═══════════════════════════════════════════════════════════════════════════

    INTERNAL_API_KEY: str = Field(
        default="",
        description=(
            "Device-scoped internal API key for backend sensitive endpoints "
            "(currently /api/v1/sync/batch). Sent by the frontend Tauri app "
            "via the X-CLS-Internal-Key header. Empty in production triggers "
            "fail-closed 503; empty in DEBUG mode logs a warning and allows "
            "the request through."
        ),
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Agent Debug Settings (Story 12.G.1)
    # [Source: docs/stories/story-12.G.1-api-response-logging.md]
    # ═══════════════════════════════════════════════════════════════════════════

    DEBUG_AGENT_RESPONSE: bool = Field(
        default=False,
        description="Enable detailed Agent API response logging for debugging (Story 12.G.1)",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Request Deduplication Settings (Story 12.H.5)
    # [Source: docs/stories/story-12.H.5-backend-dedup.md]
    # ═══════════════════════════════════════════════════════════════════════════

    ENABLE_REQUEST_DEDUP: bool = Field(
        default=True,
        description="Enable request deduplication for Agent endpoints (Story 12.H.5)",
    )

    REQUEST_CACHE_TTL: int = Field(
        default=60,
        description="Request cache TTL in seconds (Story 12.H.5, ADR-007 aligned)",
    )

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CORS Settings
    # ═══════════════════════════════════════════════════════════════════════════

    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://tauri.localhost,app://obsidian.md",
        description="Allowed CORS origins (comma-separated)",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Canvas Settings
    # ═══════════════════════════════════════════════════════════════════════════

    # Story 1.8: Multi-vault support — VAULTS_ROOT + ACTIVE_VAULT
    VAULTS_ROOT: str = Field(
        default=_PROJECT_ROOT,
        description="Parent directory containing all vault subdirectories",
    )
    ACTIVE_VAULT: str = Field(
        default="canvas-vault",
        description="Currently active vault subdirectory name",
    )

    # FIX-4.0: Use absolute path to avoid encoding issues with Chinese characters
    # The relative path "../笔记库" was causing 404 errors due to path resolution issues
    CANVAS_BASE_PATH: str = Field(
        default=os.path.join(_PROJECT_ROOT, "笔记库"),
        description="Absolute path to Canvas files directory",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # API Settings
    # ═══════════════════════════════════════════════════════════════════════════

    API_V1_PREFIX: str = Field(default="/api/v1", description="API version prefix path")

    # ═══════════════════════════════════════════════════════════════════════════
    # Field Validators
    # ═══════════════════════════════════════════════════════════════════════════

    @field_validator("API_V1_PREFIX")
    @classmethod
    def validate_api_prefix(cls, v: str) -> str:
        """
        Fix MSYS/Git Bash path conversion issue.

        On Windows with Git Bash, paths starting with '/' get converted to
        Windows paths (e.g., '/api/v1' becomes 'C:/Program Files/Git/api/v1').
        This validator detects and corrects such conversions.

        Args:
            v: The API prefix value (possibly converted by MSYS)

        Returns:
            Corrected API prefix starting with '/'
        """
        if v.startswith("/"):
            return v

        # Detect MSYS path conversion - look for /api/ in the converted path
        if "/api/" in v:
            # Extract the API path portion
            idx = v.find("/api/")
            return v[idx:]

        # Fallback: return default if path is completely invalid
        return "/api/v1"

    # ✅ Verified from Context7:/websites/pydantic_dev (topic: model_validator)
    # [Source: docs/stories/21.5.2.story.md - AC-1, AC-2]
    # [FIX] Changed from field_validator to model_validator to access AI_PROVIDER
    @model_validator(mode="after")
    def validate_model_name(self) -> "Settings":
        """
        检测并清理AI模型名称中的异常前缀（仅对非 custom provider）。

        某些终端或配置工具可能会在模型名称前添加前缀（如 [K1], [K2]），
        这会导致某些 API 调用失败。此验证器自动检测并清理这些前缀。

        **重要**: 对于 custom provider，保留前缀，因为自定义 AI 服务商
        可能使用这些前缀作为模型路由标识。

        异常前缀示例: [K1], [K2], [TEST]

        Returns:
            修改后的 Settings 实例

        [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-2]
        """
        v = self.AI_MODEL_NAME

        # [FIX] Skip prefix cleaning for custom providers - they may use prefixes
        # for model routing (e.g., [K1] routes to a specific model channel)
        if self.AI_PROVIDER == "custom":
            if v.startswith("[") and "]" in v:
                logger.info(f"AI_MODEL_NAME '{v}' contains prefix, preserved for custom provider")
            return self

        # 检测方括号前缀模式
        if v.startswith("[") and "]" in v:
            bracket_end = v.index("]") + 1
            prefix = v[:bracket_end]
            clean_name = v[bracket_end:]
            logger.warning(f"AI_MODEL_NAME contains abnormal prefix '{prefix}', auto-cleaned to '{clean_name}'")
            self.AI_MODEL_NAME = clean_name
        return self

    # ═══════════════════════════════════════════════════════════════════════════
    # Round-23 Story 7.1 · Patch 1 — fail-closed 安全默认值校验
    # [Source: _bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md]
    # ═══════════════════════════════════════════════════════════════════════════

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        """
        Round-23 Patch 1: fail-closed 安全默认值校验。

        生产环境（非 local dev）强制：
        - NEO4J_PASSWORD 在 NEO4J_ENABLED=True 时必须显式设置
        - INTERNAL_API_KEY 必须显式设置（敏感 endpoint 鉴权）

        本地 dev（DEBUG=True + CORS 含 localhost）允许 warning + 放行。
        防止容器开放端口意外暴露弱密码或无鉴权状态。
        """
        is_local = self.DEBUG and ("localhost" in self.CORS_ORIGINS or "127.0.0.1" in self.CORS_ORIGINS)

        if self.NEO4J_ENABLED and not self.NEO4J_PASSWORD:
            if not is_local:
                raise ValueError(
                    "NEO4J_PASSWORD must be set explicitly outside local dev. Set env var or disable NEO4J_ENABLED."
                )
            logger.warning("NEO4J_PASSWORD empty in DEBUG mode. Set before deploying.")

        if not is_local and not self.INTERNAL_API_KEY:
            raise ValueError(
                "INTERNAL_API_KEY required outside local dev. Set env var or enable DEBUG with localhost CORS."
            )

        if "*" in self.CORS_ORIGINS:
            logger.warning("CORS_ORIGINS contains wildcard '*'. Unsafe in production.")

        return self

    MAX_CONCURRENT_REQUESTS: int = Field(default=100, description="Maximum concurrent requests limit")

    # ═══════════════════════════════════════════════════════════════════════════
    # Rollback Settings (Story 18.5)
    # [Source: docs/architecture/rollback-recovery-architecture.md:100-150]
    # ═══════════════════════════════════════════════════════════════════════════

    ROLLBACK_HISTORY_LIMIT: int = Field(default=100, description="Maximum operation history records per Canvas")

    ROLLBACK_SNAPSHOT_INTERVAL: int = Field(
        default=300,
        description="Auto snapshot interval in seconds (default: 5 minutes)",
    )

    ROLLBACK_MAX_SNAPSHOTS: int = Field(default=50, description="Maximum snapshots per Canvas before auto-cleanup")

    ROLLBACK_GRAPH_SYNC_TIMEOUT_MS: int = Field(default=200, description="Graph sync timeout in milliseconds")

    ROLLBACK_ENABLE_GRAPH_SYNC: bool = Field(
        default=True, description="Enable Graphiti knowledge graph synchronization"
    )

    ROLLBACK_STORAGE_PATH: str = Field(
        default=".canvas-learning",
        description="Base path for rollback data storage (history/snapshots)",
    )

    ROLLBACK_ENABLE_AUTO_BACKUP: bool = Field(
        default=True, description="Create backup snapshot before rollback operations"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # AI Model Configuration (Multi-Provider Support)
    # Supports: google, openai, anthropic, openrouter, custom
    # [Source: Multi-Provider AI Architecture - flexible model configuration]
    # ═══════════════════════════════════════════════════════════════════════════

    AI_PROVIDER: str = Field(
        default="google",
        description="AI provider: google, openai, anthropic, openrouter, custom",
    )

    AI_MODEL_NAME: str = Field(
        default="gemini-3.1-flash-lite-preview",
        description="AI model name (e.g., gemini-3.1-flash-lite-preview, gpt-4o, claude-3-5-sonnet)",
    )

    AI_BASE_URL: str = Field(
        default="",
        description="AI API base URL (leave empty to use provider's default)",
    )

    AI_API_KEY: str = Field(default="", description="AI API key for the selected provider")

    AGENT_MAX_TOKENS: int = Field(default=4000, description="Maximum tokens per Agent response")

    AGENT_PROMPT_PATH: str = Field(
        default=os.path.join(_PROJECT_ROOT, ".claude", "agents"),
        description="Path to Agent prompt templates directory (absolute path)",
    )

    # 6-10 M1: Configurable scoring model (replaces hardcoded openai/gpt-4o-mini)
    SCORING_MODEL: str = Field(
        default="",
        description="LiteLLM model string for scoring/difficulty tasks. "
        "Empty = use AI_PROVIDER/AI_MODEL_NAME. Story 6.4, 6.10.",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Legacy Settings (Deprecated - kept for backward compatibility)
    # ═══════════════════════════════════════════════════════════════════════════

    GEMINI_MODEL: str = Field(
        default="gemini-3.1-flash-lite-preview",
        description="[DEPRECATED] Use AI_MODEL_NAME instead",
    )

    GOOGLE_API_KEY: str = Field(default="", description="[DEPRECATED] Use AI_API_KEY instead")

    AGENT_MODEL: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="[DEPRECATED] Use AI_MODEL_NAME instead",
    )

    ANTHROPIC_API_KEY: str = Field(default="", description="[DEPRECATED] Use AI_API_KEY instead")

    # ═══════════════════════════════════════════════════════════════════════════
    # Neo4j Configuration (Story 30.1)
    # [Source: docs/stories/30.1.story.md - AC 2]
    # ═══════════════════════════════════════════════════════════════════════════

    NEO4J_ENABLED: bool = Field(
        default=True,
        description="Enable Neo4j connection (set to False for JSON fallback)",
    )

    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j Bolt connection URI")

    NEO4J_USER: str = Field(default="neo4j", description="Neo4j username")

    NEO4J_PASSWORD: str = Field(default="", description="Neo4j password (REQUIRED in production)")

    NEO4J_DATABASE: str = Field(default="neo4j", description="Neo4j database name")

    # ═══════════════════════════════════════════════════════════════════════════
    # Neo4j Connection Pool Configuration (Story 30.2)
    # [Source: docs/stories/30.2.story.md - AC 2]
    # ═══════════════════════════════════════════════════════════════════════════

    NEO4J_MAX_CONNECTION_POOL_SIZE: int = Field(
        default=50,
        description="Maximum connections in Neo4j connection pool (Story 30.2)",
    )

    NEO4J_CONNECTION_TIMEOUT: int = Field(
        default=30,
        description="Neo4j connection acquisition timeout in seconds (Story 30.2)",
    )

    NEO4J_MAX_CONNECTION_LIFETIME: int = Field(
        default=3600, description="Maximum connection lifetime in seconds (Story 30.2)"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Neo4j Retry Configuration (Story 30.2)
    # [Source: docs/stories/30.2.story.md - AC 5]
    # ═══════════════════════════════════════════════════════════════════════════

    NEO4J_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="Number of retry attempts for Neo4j operations (Story 30.2)",
    )

    NEO4J_RETRY_DELAY_BASE: float = Field(
        default=1.0,
        description="Base delay for exponential backoff in seconds (1s, 2s, 4s) (Story 30.2)",
    )

    NEO4J_RETRY_MAX_DELAY: float = Field(default=10.0, description="Maximum retry delay in seconds (Story 30.2)")

    # ═══════════════════════════════════════════════════════════════════════════
    # Verification Service Settings (Story 31.1)
    # [Source: docs/stories/31.1.story.md - Task 6]
    # ═══════════════════════════════════════════════════════════════════════════

    USE_MOCK_VERIFICATION: bool = Field(
        default=False,
        description="Force mock mode for verification service (Story 31.1, used for testing/debugging)",
    )

    VERIFICATION_AI_TIMEOUT: float = Field(
        default=15.0,
        description="Timeout in seconds for AI calls in verification service (Story 31.1 AC-31.1.5)",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Batch Processing Settings (Story 30.11)
    # [Source: docs/stories/30.11.batch-true-parallel.story.md - AC-30.11.3]
    # ═══════════════════════════════════════════════════════════════════════════

    BATCH_NEO4J_CONCURRENCY: int = Field(
        default=10,
        description="Max concurrent Neo4j writes during batch processing. Story 30.11 AC-30.11.3",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Graphiti JSON Dual-Write Settings (Story 36.9)
    # [Source: docs/stories/36.9.story.md - AC-36.9.5]
    # DEPRECATED: Phase 2 replaced JSON dual-write with GraphitiEpisodeWorker.
    # ═══════════════════════════════════════════════════════════════════════════

    # DEPRECATED: Phase 2 replaced JSON dual-write with GraphitiEpisodeWorker.
    ENABLE_GRAPHITI_JSON_DUAL_WRITE: bool = Field(
        default=False,
        description="[DEPRECATED] Legacy JSON dual-write. Replaced by GraphitiEpisodeWorker.",
    )

    # Graphiti Episode Worker (Phase 2)
    GOOGLE_API_KEY: str = Field(default="", description="Google API key for graphiti-core Gemini LLM/Embedder")

    GRAPHITI_QUEUE_MAXSIZE: int = Field(
        default=100, description="Max episodes in graphiti worker queue before dropping"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # LanceDB Auto-Index Settings (Story 38.1)
    # ═══════════════════════════════════════════════════════════════════════════

    ENABLE_LANCEDB_AUTO_INDEX: bool = Field(
        default=True,
        description="Enable automatic LanceDB indexing after Canvas CRUD. Story 38.1 AC-1.",
    )

    LANCEDB_INDEX_DEBOUNCE_MS: int = Field(
        default=500,
        description="Debounce window in ms for LanceDB auto-index. Prevents rapid re-indexing. Story 38.1.",
    )

    LANCEDB_INDEX_TIMEOUT: float = Field(
        default=5.0,
        description="Timeout in seconds per LanceDB index attempt. Story 38.1 AC-1.",
    )

    LANCEDB_INDEX_TABLE_NAME: str = Field(
        default="canvas_nodes",
        description="LanceDB table name for canvas node index. Story 38.1.",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Subject / Group ID Configuration (Story 2.1)
    # ═══════════════════════════════════════════════════════════════════════════

    DEFAULT_GROUP_ID: str = Field(
        default="vault:default",
        description=(
            "Default Graphiti group_id for memory isolation. Story 2.1 AC-5. "
            "Round-23 Patch 2: 默认改 'vault:default' (语义对齐 LEGACY_TO_VAULT_MAPPING). "
            "deprecated 值 (cs188/canvas-dev/general/main) 经 canonical_group_id() 自动归一化 + WARNING."
        ),
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Ollama Settings (Story 1.1)
    # ═══════════════════════════════════════════════════════════════════════════

    OLLAMA_HOST: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL. Use http://ollama:11434 inside Docker.",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Vault-wide Note Indexing Settings
    # ═══════════════════════════════════════════════════════════════════════════

    VAULT_INDEX_ENABLED: bool = Field(default=True, description="Enable vault-wide .md note indexing to LanceDB.")

    VAULT_INDEX_SKIP_DIRS: str = Field(
        default=(
            # Phase A T1.1 (2026-05-09): GPT DR + 用户实测污染清单完整黑名单
            # - .obsidian/.git/.trash/node_modules: 标准非笔记目录
            # - .claude/.claudian: Skill / Claudian 工具文档（用户实测 3 SKILL.md 进库噪音）
            # - _bmad-output/archive/templates: 开发文档/归档/模板（非学习内容）
            # - outputs: 验收/导出物
            # - *-explanations: AI 生成解释（fnmatch glob，配合 lancedb_client.py:1251 fix）
            # - Excalidraw/_misc: 手绘图/杂项 junk
            # - 检验白板/验收单: 信息隔离铁律——考题绝不能经 RAG 回流进学习对话
            #   (检验白板 v1 审计 A5-7, 2026-07-10; 本字段是黑名单唯一权威源,
            #    与 lancedb_client.DEFAULT_VAULT_SKIP_DIRS 兜底常量保持一致)
            # - chunks: video-to-canvas 的 merged.md 与源笔记同内容双份入库 (RAG-S1)
            # - .quarantine: MCP 隔离区非学习内容 (RAG-S1)
            # - _待处理: A-9 (R11-BATCH2-2026-08-17) 收件箱暂存区 — 未分诊的碎片
            #   笔记不应参与检索; 是第 3 批清仓流程 (B-1) 的前置边界。加入时现网
            #   vault 尚无此目录 (容器内任意深度 find 零命中), 属预防性加固
            # - _archive: 同批 — 下划线前缀归档区, 与上方无前缀的 archive 并存
            ".obsidian,.git,.trash,node_modules,"
            ".claude,.claudian,_bmad-output,archive,templates,"
            "outputs,*-explanations,Excalidraw,_misc,"
            "检验白板,验收单,chunks,.quarantine,"
            "_待处理,_archive"
        ),
        description="Comma-separated list of directories to skip during vault indexing.",
    )

    def effective_vault_skip_dirs(self) -> List[str]:
        """索引目录黑名单 = 配置值 ∪ IMMUTABLE_VAULT_SKIP_DIRS。

        ⛔ P1-02 (Codex 对抗审查 2026-08-19): **所有消费点必须走这里**, 不要
        直接 `settings.VAULT_INDEX_SKIP_DIRS.split(",")` —— 直接 split 会让一行
        env 覆盖撤掉信息隔离铁律 (检验白板/验收单), 实测可复现。

        保序策略: 先配置串的原顺序 (保留用户可见的排列, 且 demote-first 之类的
        顺序语义不被打乱), 再追加硬底中缺失的项。
        """
        configured = [d.strip() for d in self.VAULT_INDEX_SKIP_DIRS.split(",") if d.strip()]
        merged = list(configured)
        for hard in sorted(IMMUTABLE_VAULT_SKIP_DIRS):  # sorted 保证追加顺序确定
            if hard not in merged:
                merged.append(hard)
        return merged

    # RAG-S1-2026-08-02 阶段 1: vault 索引 orchestrator (统一原语 + durable
    # pending + 双机制触发)。关掉 = 回阶段 0 现状 (仅手动全量端点)。
    ENABLE_VAULT_INDEX_ORCHESTRATOR: bool = Field(
        default=True,
        description="Enable the vault index orchestrator (watcher + periodic "
        "anti-entropy reconcile + durable per-path pending). Rollback switch.",
    )

    VAULT_INDEX_SCAN_INTERVAL_S: int = Field(
        default=60,
        description="Anti-entropy fingerprint scan interval in seconds. The "
        "save-to-searchable SLO is guaranteed by this pass even with all "
        "file events lost.",
    )

    VAULT_INDEX_STALE_AFTER_S: int = Field(
        default=300,
        description="Oldest-pending lag threshold in seconds after which the index status endpoint reports stale=true.",
    )

    VAULT_INDEX_CHUNK_SIZE: int = Field(
        default=500,
        description="Target chunk size in characters for .md note segmentation.",
    )

    VAULT_INDEX_OVERLAP: int = Field(
        default=50,
        description="Overlap characters between chunks for .md note segmentation.",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Board Manifest (RAG-S2.5-2026-08-10) — 结构读模型快照兜底
    # ═══════════════════════════════════════════════════════════════════════════

    MANIFEST_SNAPSHOT_STALE_AFTER_S: int = Field(
        default=86400,
        description="Board manifest 快照兜底 stale 阈值(秒): live 失败退快照时, "
        "lag_seconds 超过此值即标注 stale=true (只标注不删除, last known good 常驻)。",
        ge=0,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # FSRS Spaced Repetition Settings (Story 32.2)
    # ═══════════════════════════════════════════════════════════════════════════

    USE_FSRS: bool = Field(
        default=True,
        description="Enable FSRS algorithm. Set False to disable FSRS and use fallback scheduling. Story 32.8.",
    )

    FSRS_DESIRED_RETENTION: float = Field(
        default=0.9,
        description="FSRS target retention rate (0.0 to 1.0). Higher = more frequent reviews. Story 32.2.",
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Memory Retry Settings (Story 36.13 AC-2)
    # ═══════════════════════════════════════════════════════════════════════════

    MEMORY_RETRY_BASE_DELAY: float = Field(
        default=1.0,
        description="Base delay in seconds for Graphiti write retry backoff (1s, 2s, 4s). Story 36.13 AC-2.",
        ge=0.0,
    )

    MEMORY_RETRY_MAX_DELAY: float = Field(
        default=10.0,
        description="Maximum retry delay in seconds for Graphiti write operations. Story 36.13 AC-2.",
        ge=0.0,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # TTLCache Configuration (Story 36.13 AC-3,4,5)
    # ═══════════════════════════════════════════════════════════════════════════

    AGENT_MEMORY_CACHE_MAXSIZE: int = Field(
        default=1000,
        description="Max entries in AgentService memory cache. Story 36.13 AC-3.",
        ge=1,
    )

    AGENT_MEMORY_CACHE_TTL: int = Field(
        default=30,
        description="TTL in seconds for AgentService memory cache entries. Story 36.13 AC-3.",
        ge=0,
    )

    SCORE_HISTORY_CACHE_MAXSIZE: int = Field(
        default=1000,
        description="Max entries in MemoryService score history cache. Story 36.13 AC-4.",
        ge=1,
    )

    ENRICHMENT_CACHE_MAXSIZE: int = Field(
        default=1000,
        description="Max entries in ContextEnrichmentService association cache. Story 36.13 AC-5.",
        ge=1,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Faithfulness Check Settings (Story 7.1)
    # [Source: _bmad-output/implementation-artifacts/7-1-llm-faithfulness-prompt-injection.md]
    # ═══════════════════════════════════════════════════════════════════════════

    FAITHFULNESS_ENABLED: bool = Field(
        default=True,
        description="Enable RAGAS faithfulness check in RAG pipeline. Story 7.1 AC-1.",
    )

    FAITHFULNESS_THRESHOLD: float = Field(
        default=0.85,
        description="Faithfulness score threshold for acceptable answers. Story 7.1 AC-1.",
        ge=0.0,
        le=1.0,
    )

    FAITHFULNESS_THRESHOLD_LOW: float = Field(
        default=0.5,
        description="Faithfulness score below this triggers full degradation. Story 7.1 AC-4.",
        ge=0.0,
        le=1.0,
    )

    FAITHFULNESS_MODEL: str = Field(
        default="",
        description="Model for faithfulness checks via LiteLLM. Empty = use AI_MODEL_NAME. Story 7.1.",
    )

    INJECTION_GUARD_ENABLED: bool = Field(
        default=True,
        description="Enable prompt injection detection guard. Story 7.1 AC-2,5.",
    )

    INJECTION_THRESHOLD: float = Field(
        default=0.7,
        description="Risk score threshold for blocking suspected injection. Story 7.1 AC-5.",
        ge=0.0,
        le=1.0,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Computed Properties
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parse CORS_ORIGINS string into a list of origins.

        Supports two formats:
        1. Comma-separated: "http://localhost:3000,http://127.0.0.1:3000"
        2. JSON array: '["http://localhost:3000","http://127.0.0.1:3000"]'

        Returns:
            List of allowed CORS origin strings.
        """
        cors_value = self.CORS_ORIGINS.strip()

        # Try JSON array format first (handles system env variable override)
        if cors_value.startswith("["):
            try:
                origins = json.loads(cors_value)
                if isinstance(origins, list):
                    return [str(o).strip() for o in origins if o]
            except json.JSONDecodeError:
                pass  # Fall through to comma-separated parsing

        # Comma-separated format (from .env file)
        return [origin.strip() for origin in cors_value.split(",") if origin.strip()]

    # ═══════════════════════════════════════════════════════════════════════════
    # Lowercase Property Aliases (for convenience)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def canvas_base_path(self) -> str:
        """Alias for CANVAS_BASE_PATH (lowercase for convenience)."""
        return self.CANVAS_BASE_PATH

    @property
    def vault_id(self) -> str:
        """Story 1.9 + Phase B0.4 (Round-5 路径 A): Derive vault_id.

        Priority order (Round-5 A2):
        1. .canvas-config.yaml `vault_id` field (explicit, schema_version >= 2.0)
        2. sanitize_vault_id(ACTIVE_VAULT) (fallback, legacy schema 1.0)

        Reading yaml each access is OK because:
        - get_settings() is @lru_cache → Settings instance reused
        - vault_id property called frequently but yaml file rarely changes
        - hot-reload via reload_settings() invalidates cache
        """
        try:
            from pathlib import Path

            import yaml

            yaml_path = Path(self.CANVAS_BASE_PATH) / ".canvas-config.yaml"
            if yaml_path.exists():
                with open(yaml_path, encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                explicit_vault_id = config.get("vault_id")
                if explicit_vault_id and isinstance(explicit_vault_id, str):
                    # Validate explicit vault_id is well-formed
                    sanitized = sanitize_vault_id(explicit_vault_id)
                    if sanitized != "default":
                        return sanitized
        except Exception:
            # Yaml parse failure or path error → fallback silently to ACTIVE_VAULT
            pass
        return sanitize_vault_id(self.ACTIVE_VAULT)

    @property
    def api_v1_prefix(self) -> str:
        """Alias for API_V1_PREFIX (lowercase for convenience)."""
        return self.API_V1_PREFIX

    @property
    def max_concurrent_requests(self) -> int:
        """Alias for MAX_CONCURRENT_REQUESTS (lowercase for convenience)."""
        return self.MAX_CONCURRENT_REQUESTS

    @property
    def project_name(self) -> str:
        """Alias for PROJECT_NAME (lowercase for convenience)."""
        return self.PROJECT_NAME

    @property
    def debug(self) -> bool:
        """Alias for DEBUG (lowercase for convenience)."""
        return self.DEBUG

    @property
    def debug_agent_response(self) -> bool:
        """Alias for DEBUG_AGENT_RESPONSE (lowercase for convenience). Story 12.G.1."""
        return self.DEBUG_AGENT_RESPONSE

    @property
    def log_level(self) -> str:
        """Alias for LOG_LEVEL (lowercase for convenience)."""
        return self.LOG_LEVEL

    @property
    def rollback_history_limit(self) -> int:
        """Alias for ROLLBACK_HISTORY_LIMIT (lowercase for convenience)."""
        return self.ROLLBACK_HISTORY_LIMIT

    @property
    def rollback_snapshot_interval(self) -> int:
        """Alias for ROLLBACK_SNAPSHOT_INTERVAL (lowercase for convenience)."""
        return self.ROLLBACK_SNAPSHOT_INTERVAL

    @property
    def rollback_max_snapshots(self) -> int:
        """Alias for ROLLBACK_MAX_SNAPSHOTS (lowercase for convenience)."""
        return self.ROLLBACK_MAX_SNAPSHOTS

    @property
    def rollback_graph_sync_timeout_ms(self) -> int:
        """Alias for ROLLBACK_GRAPH_SYNC_TIMEOUT_MS (lowercase for convenience)."""
        return self.ROLLBACK_GRAPH_SYNC_TIMEOUT_MS

    @property
    def rollback_enable_graph_sync(self) -> bool:
        """Alias for ROLLBACK_ENABLE_GRAPH_SYNC (lowercase for convenience)."""
        return self.ROLLBACK_ENABLE_GRAPH_SYNC

    @property
    def rollback_storage_path(self) -> str:
        """Alias for ROLLBACK_STORAGE_PATH (lowercase for convenience)."""
        return self.ROLLBACK_STORAGE_PATH

    @property
    def rollback_enable_auto_backup(self) -> bool:
        """Alias for ROLLBACK_ENABLE_AUTO_BACKUP (lowercase for convenience)."""
        return self.ROLLBACK_ENABLE_AUTO_BACKUP

    @property
    def enable_request_dedup(self) -> bool:
        """Alias for ENABLE_REQUEST_DEDUP (lowercase for convenience). Story 12.H.5."""
        return self.ENABLE_REQUEST_DEDUP

    @property
    def request_cache_ttl(self) -> int:
        """Alias for REQUEST_CACHE_TTL (lowercase for convenience). Story 12.H.5."""
        return self.REQUEST_CACHE_TTL

    @property
    def neo4j_enabled(self) -> bool:
        """Alias for NEO4J_ENABLED (lowercase for convenience). Story 30.1."""
        return self.NEO4J_ENABLED

    @property
    def neo4j_uri(self) -> str:
        """Alias for NEO4J_URI (lowercase for convenience). Story 30.1."""
        return self.NEO4J_URI

    @property
    def neo4j_user(self) -> str:
        """Alias for NEO4J_USER (lowercase for convenience). Story 30.1."""
        return self.NEO4J_USER

    @property
    def neo4j_password(self) -> str:
        """Alias for NEO4J_PASSWORD (lowercase for convenience). Story 30.1."""
        return self.NEO4J_PASSWORD

    @property
    def neo4j_database(self) -> str:
        """Alias for NEO4J_DATABASE (lowercase for convenience). Story 30.1."""
        return self.NEO4J_DATABASE

    @property
    def neo4j_max_connection_pool_size(self) -> int:
        """Alias for NEO4J_MAX_CONNECTION_POOL_SIZE (lowercase). Story 30.2."""
        return self.NEO4J_MAX_CONNECTION_POOL_SIZE

    @property
    def neo4j_connection_timeout(self) -> int:
        """Alias for NEO4J_CONNECTION_TIMEOUT (lowercase). Story 30.2."""
        return self.NEO4J_CONNECTION_TIMEOUT

    @property
    def neo4j_max_connection_lifetime(self) -> int:
        """Alias for NEO4J_MAX_CONNECTION_LIFETIME (lowercase). Story 30.2."""
        return self.NEO4J_MAX_CONNECTION_LIFETIME

    @property
    def neo4j_retry_attempts(self) -> int:
        """Alias for NEO4J_RETRY_ATTEMPTS (lowercase). Story 30.2."""
        return self.NEO4J_RETRY_ATTEMPTS

    @property
    def neo4j_retry_delay_base(self) -> float:
        """Alias for NEO4J_RETRY_DELAY_BASE (lowercase). Story 30.2."""
        return self.NEO4J_RETRY_DELAY_BASE

    @property
    def neo4j_retry_max_delay(self) -> float:
        """Alias for NEO4J_RETRY_MAX_DELAY (lowercase). Story 30.2."""
        return self.NEO4J_RETRY_MAX_DELAY

    @property
    def enable_graphiti_json_dual_write(self) -> bool:
        """Alias for ENABLE_GRAPHITI_JSON_DUAL_WRITE (lowercase). Story 36.9."""
        return self.ENABLE_GRAPHITI_JSON_DUAL_WRITE

    @property
    def fsrs_desired_retention(self) -> float:
        """Alias for FSRS_DESIRED_RETENTION (lowercase). Story 32.2."""
        return self.FSRS_DESIRED_RETENTION

    # ═══════════════════════════════════════════════════════════════════════════
    # Configuration
    # ═══════════════════════════════════════════════════════════════════════════

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings .env file)
    # Pattern: model_config = SettingsConfigDict(env_file=".env")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: lru_cache Depends settings)
# Pattern: @lru_cache decorator ensures Settings is initialized only once
@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses @lru_cache to ensure the Settings object is instantiated only once,
    preventing repeated reads from the .env file.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: lru_cache settings)

    Returns:
        Settings: Cached application settings instance.
    """
    return Settings()


# Create default settings instance for direct import
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings module pattern)
settings = get_settings()


# B1 修复 (2026-07-12): AI_PROVIDER → litellm 路由前缀映射。
# litellm 的 Google AI Studio 路由前缀是 "gemini/" 而非 "google/" —— 旧拼接
# f"{AI_PROVIDER}/{AI_MODEL_NAME}" 产出 litellm 不识别的 "google/gemini-..."
# 使 /exam/grade 恒 502、/exam/quick 恒退化模板题（2026-07-12 对抗审查真机实证）。
_LITELLM_PROVIDER_PREFIX = {"google": "gemini"}


def resolve_litellm_model() -> str:
    """出题/评分统一的 litellm model 字符串解析（唯一入口, DRY 两处调用点）。

    优先级: SCORING_MODEL 显式配置 > AI_PROVIDER(映射后)/AI_MODEL_NAME。
    前缀判断用 startswith(f"{provider}/") 而非 startswith(provider) —— 后者
    会被 "gemini-2.5-flash" 这类以 provider 名开头的模型名误判为已带前缀。
    """
    s = get_settings()
    if s.SCORING_MODEL:
        return s.SCORING_MODEL
    provider = _LITELLM_PROVIDER_PREFIX.get(s.AI_PROVIDER, s.AI_PROVIDER)
    if provider and not s.AI_MODEL_NAME.startswith(f"{provider}/"):
        return f"{provider}/{s.AI_MODEL_NAME}"
    return s.AI_MODEL_NAME


# Convenience constant: default group_id for Graphiti memory isolation.
# All modules should import this instead of hardcoding "cs188".
# Story 2.1 AC-5: cs188 hardcode cleanup.
# Round-23 Story 7.2 · Patch 2: 经 canonical_group_id() 唯一入口归一化, deprecated 值会 WARNING.
# Lazy import 避免 Settings 加载时循环 (subject_config 不反向依赖 config).
from app.core.subject_config import canonical_group_id as _canonical_group_id

DEFAULT_GROUP_ID: str = _canonical_group_id(settings.DEFAULT_GROUP_ID)


# ═══════════════════════════════════════════════════════════════════════════════
# Story 1.8: Vault Switch — Runtime Settings Reload
# ═══════════════════════════════════════════════════════════════════════════════

import re
import unicodedata

# Phase B0.1 (Round-4 ChatGPT V3 + 4 agent confirmed P0):
# 旧 sanitize_vault_id 用 [^a-z0-9] 剥离所有非 ASCII → 中文 vault 全部坍缩 'default' → 跨 vault 数据泄漏
# 新实现采用与 sanitize_subject_name (subject_config.py:357) 一致的 unicode-aware 逻辑
# 关键升级:
#   - NFKC normalize (拆合字 ﬁ→fi, 兼容 macOS APFS NFD/NFC mismatch)
#   - casefold (Unicode-aware lower; ß→ss, Σ→σ)
#   - re.UNICODE \w (覆盖 CJK/西里尔/希腊/谚文等所有 Unicode 字母)
#   - truncate 200 字符 (APFS 单段名 255 byte 限制 + Neo4j 4039 byte 边界)
_VAULT_ID_MAX_LEN = 200


def sanitize_vault_id(vault_name: str) -> str:
    """Derive a safe vault_id from a vault directory name.

    Unicode-aware: keeps CJK/Cyrillic/Greek letters, normalizes ASCII to lowercase,
    replaces special chars with underscores. Safe across LanceDB table prefix,
    Neo4j group_id property, APFS file path, and shell command.

    Examples:
        "CS 61B"          -> "cs_61b"
        "笔记库"          -> "笔记库"  (Phase B0.1: 不再坍缩 default)
        "数学のノート"     -> "数学のノート"
        "수학 노트"        -> "수학_노트"
        "café"            -> "café"  (NFKC preserves)
        "📚 笔记本"       -> "笔记本"  (emoji stripped)
        "../etc/passwd"   -> "etc_passwd"  (path traversal defused)
        ""                -> "default"
    """
    if not vault_name:
        return "default"
    # NFKC: 兼容字符归一化 (ﬁ→fi 拆合字, 同时 NFC normalize 防 APFS 坑)
    normalized = unicodedata.normalize("NFKC", vault_name).casefold().strip()
    # \w + UNICODE 覆盖所有 Unicode 字母数字下划线 (CJK/西里尔/希腊/谚文等)
    sanitized = re.sub(r"[^\w]+", "_", normalized, flags=re.UNICODE)
    # Collapse runs of underscores + strip edges
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    # Truncate to APFS-safe length
    if len(sanitized) > _VAULT_ID_MAX_LEN:
        sanitized = sanitized[:_VAULT_ID_MAX_LEN].rstrip("_")
    return sanitized or "default"


def get_current_vault_id() -> str:
    """Return the vault_id for the currently active vault."""
    return get_settings().vault_id


def reload_settings(overrides: dict | None = None) -> Settings:
    """Hot-reload settings with optional overrides (Story 1.8 AC #4).

    Clears the lru_cache on get_settings(), injects overrides into
    os.environ so the next Settings() picks them up, then rebuilds.

    Returns the new Settings instance.
    """
    global settings, DEFAULT_GROUP_ID

    overrides = overrides or {}
    for key, value in overrides.items():
        os.environ[key] = str(value)

    get_settings.cache_clear()

    settings = get_settings()
    # Round-23 Patch 2: 经 canonical_group_id 归一化, 与 module-level DEFAULT_GROUP_ID 保持一致
    DEFAULT_GROUP_ID = _canonical_group_id(settings.DEFAULT_GROUP_ID)
    return settings
