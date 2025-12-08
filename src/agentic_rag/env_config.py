"""
Canvas Learning System - 环境变量配置加载器

自动加载 .env 文件并提供配置访问接口。

使用方法:
    from src.agentic_rag.env_config import get_config, get_openai_embedder

    # 获取配置
    config = get_config()
    print(config.openai_api_key)

    # 获取 OpenAI 嵌入器 (用于 LanceDB)
    embedder = get_openai_embedder()
    lancedb_client.set_embedder(embedder)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

# 尝试导入 dotenv
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# 尝试导入 openai
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class CanvasEnvConfig:
    """
    Canvas Learning System 环境配置

    从 .env 文件加载所有配置项
    """
    # API Keys
    openai_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    langchain_api_key: Optional[str] = None

    # Neo4j 配置
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: Optional[str] = None

    # Graphiti MCP 配置
    # ✅ Verified from Graphiti Skill (SKILL.md - MCP Server Configuration)
    graphiti_mcp_enabled: bool = False
    graphiti_mcp_url: str = "http://localhost:8000/sse"
    graphiti_model_name: str = "gpt-4o-mini"
    graphiti_group_id: str = "canvas-learning-system"

    # 应用配置
    project_name: str = "Canvas Learning System API"
    version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"

    # CORS 配置
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "app://obsidian.md"
    ])

    # Canvas 配置
    canvas_base_path: str = "../笔记库"

    # API 配置
    api_v1_prefix: str = "/api/v1"
    max_concurrent_requests: int = 100

    # Agentic RAG 配置
    retrieval_batch_size: int = 10
    fusion_strategy: str = "rrf"
    reranking_strategy: str = "hybrid_auto"
    quality_threshold: float = 0.7
    max_rewrite_iterations: int = 2
    cohere_monthly_limit: int = 50
    retrieval_timeout: float = 10.0
    enable_caching: bool = True
    enable_cost_monitoring: bool = True

    # LangSmith 配置
    langsmith_tracing: bool = False
    langsmith_project: str = "canvas-learning-system"

    def is_openai_configured(self) -> bool:
        """检查 OpenAI API Key 是否已配置"""
        return bool(self.openai_api_key and not self.openai_api_key.startswith("在此填入"))

    def is_neo4j_configured(self) -> bool:
        """检查 Neo4j 是否已配置"""
        return bool(self.neo4j_password and not self.neo4j_password.startswith("在此填入"))

    def is_cohere_configured(self) -> bool:
        """检查 Cohere API Key 是否已配置"""
        return bool(self.cohere_api_key and not self.cohere_api_key.startswith("在此填入"))

    def is_graphiti_mcp_configured(self) -> bool:
        """检查 Graphiti MCP 是否已配置并可用"""
        # ✅ Verified from Graphiti Skill (SKILL.md - MCP Server Configuration)
        return self.graphiti_mcp_enabled and self.is_neo4j_configured()


# 全局配置实例
_config: Optional[CanvasEnvConfig] = None


def _find_env_file() -> Optional[Path]:
    """查找 .env 文件"""
    # 从当前目录向上查找
    current = Path.cwd()

    for _ in range(5):  # 最多向上查找5层
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        current = current.parent

    # 尝试项目根目录
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        return env_file

    return None


def load_config(force_reload: bool = False) -> CanvasEnvConfig:
    """
    加载环境变量配置

    Args:
        force_reload: 强制重新加载

    Returns:
        CanvasEnvConfig: 配置对象
    """
    global _config

    if _config is not None and not force_reload:
        return _config

    # 加载 .env 文件
    if DOTENV_AVAILABLE:
        env_file = _find_env_file()
        if env_file:
            load_dotenv(env_file)

    # 解析配置
    _config = CanvasEnvConfig(
        # API Keys
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        cohere_api_key=os.environ.get("COHERE_API_KEY"),
        langchain_api_key=os.environ.get("LANGCHAIN_API_KEY"),

        # Neo4j
        neo4j_uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
        neo4j_password=os.environ.get("NEO4J_PASSWORD"),

        # 应用
        project_name=os.environ.get("PROJECT_NAME", "Canvas Learning System API"),
        version=os.environ.get("VERSION", "1.0.0"),
        debug=os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes"),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),

        # CORS
        cors_origins=os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,app://obsidian.md"
        ).split(","),

        # Canvas
        canvas_base_path=os.environ.get("CANVAS_BASE_PATH", "../笔记库"),

        # API
        api_v1_prefix=os.environ.get("API_V1_PREFIX", "/api/v1"),
        max_concurrent_requests=int(os.environ.get("MAX_CONCURRENT_REQUESTS", "100")),

        # Agentic RAG
        retrieval_batch_size=int(os.environ.get("RETRIEVAL_BATCH_SIZE", "10")),
        fusion_strategy=os.environ.get("FUSION_STRATEGY", "rrf"),
        reranking_strategy=os.environ.get("RERANKING_STRATEGY", "hybrid_auto"),
        quality_threshold=float(os.environ.get("QUALITY_THRESHOLD", "0.7")),
        max_rewrite_iterations=int(os.environ.get("MAX_REWRITE_ITERATIONS", "2")),
        cohere_monthly_limit=int(os.environ.get("COHERE_MONTHLY_LIMIT", "50")),
        retrieval_timeout=float(os.environ.get("RETRIEVAL_TIMEOUT", "10.0")),
        enable_caching=os.environ.get("ENABLE_CACHING", "True").lower() in ("true", "1", "yes"),
        enable_cost_monitoring=os.environ.get("ENABLE_COST_MONITORING", "True").lower() in ("true", "1", "yes"),

        # LangSmith
        langsmith_tracing=os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() in ("true", "1", "yes"),
        langsmith_project=os.environ.get("LANGCHAIN_PROJECT", "canvas-learning-system"),

        # Graphiti MCP
        # ✅ Verified from Graphiti Skill (SKILL.md - MCP Server Configuration)
        graphiti_mcp_enabled=os.environ.get("GRAPHITI_MCP_ENABLED", "false").lower() in ("true", "1", "yes"),
        graphiti_mcp_url=os.environ.get("GRAPHITI_MCP_URL", "http://localhost:8000/sse"),
        graphiti_model_name=os.environ.get("GRAPHITI_MODEL_NAME", "gpt-4o-mini"),
        graphiti_group_id=os.environ.get("GRAPHITI_GROUP_ID", "canvas-learning-system"),
    )

    return _config


def get_config() -> CanvasEnvConfig:
    """获取配置 (单例)"""
    if _config is None:
        return load_config()
    return _config


def get_openai_embedder() -> Optional[Callable]:
    """
    获取 OpenAI 嵌入器函数

    用于 LanceDB 向量搜索

    Returns:
        async def embed(text: str) -> List[float]
        或 None (如果未配置 OpenAI API Key)
    """
    config = get_config()

    if not config.is_openai_configured():
        return None

    if not OPENAI_AVAILABLE:
        return None

    client = AsyncOpenAI(api_key=config.openai_api_key)

    async def embed(text: str) -> List[float]:
        """生成文本嵌入向量"""
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    return embed


def print_config_status():
    """打印配置状态"""
    config = get_config()

    print("=" * 60)
    print("Canvas Learning System - 配置状态")
    print("=" * 60)
    print()
    print("API Keys:")
    print(f"  OpenAI:    {'✅ 已配置' if config.is_openai_configured() else '❌ 未配置'}")
    print(f"  Cohere:    {'✅ 已配置' if config.is_cohere_configured() else '⚠️ 未配置 (可选)'}")
    print(f"  Neo4j:     {'✅ 已配置' if config.is_neo4j_configured() else '⚠️ 未配置 (可选)'}")
    print(f"  Graphiti:  {'✅ 已配置' if config.is_graphiti_mcp_configured() else '⚠️ 未配置 (可选)'}")
    print()
    print("Agentic RAG:")
    print(f"  融合策略:    {config.fusion_strategy}")
    print(f"  重排序策略:  {config.reranking_strategy}")
    print(f"  质量阈值:    {config.quality_threshold}")
    print()
    print("=" * 60)


# 模块加载时自动加载配置
if __name__ == "__main__":
    print_config_status()
