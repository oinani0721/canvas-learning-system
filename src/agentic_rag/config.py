"""
CanvasRAGConfig Context Schema定义

定义Agentic RAG系统的Runtime配置，通过LangGraph context传递。

✅ Verified from LangGraph Skill:
- Pattern: context_schema=ContextSchema
- Runtime configuration不在state中，通过context传递
- 节点函数通过runtime参数访问: runtime.context["key"]

Story 12.5 AC 5.2:
- ✅ 配置字段: retrieval_batch_size, fusion_strategy, reranking_strategy
- ✅ quality_threshold, max_rewrite_iterations

Story 23.2: LanceDB Embedding Pipeline Configuration
- ✅ AC 4: 向量维度和模型可配置

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-11-29
Updated: 2025-12-12 (Story 23.2 - LanceDB Embedding Config)
"""

import os
from typing import Any, Dict, List, Literal, Optional

from typing_extensions import TypedDict

# ============================================================================
# Story 23.2: LanceDB Embedding Configuration
# ✅ Verified from specs/data/canvas-node.schema.json (Canvas node structure)
# ✅ Verified from sentence-transformers documentation (embedding dimensions)
# ============================================================================

# Supported embedding models with their dimensions
# Story 2.3: bge-m3 1024d Dense 为默认模型，旧模型保留兼容但标记 deprecated
EMBEDDING_MODELS: Dict[str, int] = {
    "BAAI/bge-m3": 1024,  # Default — 中英双语，MIRACL nDCG@10=63.9
    "sentence-transformers/all-MiniLM-L6-v2": 384,  # [deprecated] fast, English-only
    "sentence-transformers/all-mpnet-base-v2": 768,  # [deprecated] higher quality, English-only
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,  # [deprecated] multilingual
}

# ✅ Story 23.2 AC 4: 向量维度和模型可配置
LANCEDB_CONFIG: Dict[str, Any] = {
    "db_path": os.environ.get("LANCEDB_PATH", "data/lancedb"),
    "table_name": os.environ.get("LANCEDB_TABLE", "canvas_nodes"),
    "embedding_model": os.environ.get("LANCEDB_EMBEDDING_MODEL", "BAAI/bge-m3"),
    "embedding_dim": int(os.environ.get("LANCEDB_EMBEDDING_DIM", "1024")),
    "batch_size": int(os.environ.get("LANCEDB_BATCH_SIZE", "100")),
    "timeout_ms": int(os.environ.get("LANCEDB_TIMEOUT_MS", "400")),
}

# LanceDB Canvas Nodes Table Schema
# ✅ Story 23.2 AC 2: Canvas节点批量索引
# ✅ Verified from specs/data/canvas-node.schema.json#/properties
CANVAS_NODES_SCHEMA = {
    "doc_id": str,  # 文档唯一ID
    "content": str,  # 节点文本内容
    "vector": list,  # embedding向量 (1024维, bge-m3 Dense)
    "canvas_file": str,  # Canvas文件路径
    "node_id": str,  # 原始节点ID
    "node_type": str,  # 节点类型 (text/file/group/link)
    "color": str,  # 颜色代码 (1-6)
    "x": int,  # X坐标
    "y": int,  # Y坐标
    "timestamp": str,  # 索引时间
    "metadata_json": str,  # 其他元数据JSON
}


class CanvasRAGConfig(TypedDict, total=False):
    """
    Canvas Agentic RAG Runtime Configuration

    通过graph.invoke(state, context=config)传递，
    不存储在state中，节点通过runtime参数访问。

    Usage:
    ```python
    config = CanvasRAGConfig(
        retrieval_batch_size=10,
        fusion_strategy="weighted",
        quality_threshold=0.7,
    )
    result = canvas_agentic_rag.invoke(
        {"messages": [("user", "query")]},
        context=config
    )
    ```
    """

    # === 检索配置 ===
    retrieval_batch_size: int  # Top-K结果数 (默认10)
    graphiti_batch_size: Optional[int]  # Graphiti专用 (默认同retrieval_batch_size)
    lancedb_batch_size: Optional[int]  # LanceDB专用 (默认同retrieval_batch_size)
    search_type: Literal["vector", "hybrid"]  # 默认搜索模式

    # === 融合配置 ===
    fusion_strategy: Literal["rrf", "weighted", "cascade", "layered_rrf"]  # 融合算法
    fusion_groups: Dict[str, List[str]]  # 3 组分层映射
    rrf_k: int  # RRF k 值 (默认 60)
    source_weights: Dict[str, float]  # 数据源权重配置
    time_decay_factor: float  # 时间衰减因子 (默认0.05)

    # === 精排配置 ===
    reranking_strategy: Literal["local", "cohere", "hybrid_auto"]  # Reranking策略
    reranker_model_name: str  # 精排模型名称 (默认 gte-reranker-modernbert-base)
    reranker_torch_dtype: str  # 推理精度 (默认 float16)
    adaptive_k_buffer: int  # gap 后缓冲区 (默认 5)
    adaptive_k_min: int  # 最小返回数量 (默认 3)
    adaptive_k_max: int  # 最大返回数量 (默认 15)

    # === 质量门控配置 ===
    quality_threshold: float  # 质量阈值 (0.7=high, 0.5=medium)
    max_rewrite_iterations: int  # 最大重写次数 (默认2)
    quality_check_model: str  # CRAG 二元评分 LLM 模型
    rewrite_model: str  # 查询改写 LLM 模型

    # === 压缩配置 (Story 2.10) ===
    context_max_tokens: int  # 上下文压缩目标 token 数 (默认 3000)
    mastery_injection_enabled: bool  # 是否注入掌握度信息 (默认 True)
    learning_memory_max_tokens: int  # Graphiti 学习记忆 token 上限 (默认 1000)
    staleness_check_enabled: bool  # 是否启用回源验证 (默认 True)
    multi_query_enabled: bool  # 是否启用查询改写 (默认 True)
    multi_query_model: str  # 查询改写 LLM 模型

    # === 过滤与扩展配置 (Story 2.8) ===
    progressive_scope_enabled: bool  # 渐进范围搜索 (默认 True)
    min_results_threshold: int  # 渐进搜索最小结果阈值 (默认 5)
    neighbor_expansion_enabled: bool  # Wiki-links 邻居扩展 (默认 True)
    neighbor_max_count: int  # 最大邻居扩展文件数 (默认 5)
    neighbor_score_decay: float  # 邻居分数衰减系数 (默认 0.7)
    tag_jaccard_bridge_enabled: bool  # Tag Jaccard 桥接 (默认 False)
    tag_jaccard_threshold: float  # Jaccard 相似度阈值 (默认 0.3)

    # === 图片配置 (Story 2.9) ===
    ocr_model: str  # OCR LLM 模型名 (默认 gemini/gemini-2.0-flash)

    # === 成本控制 ===
    cohere_monthly_limit: int  # Cohere月度限额 (默认50)
    enable_cost_monitoring: bool  # 是否启用成本监控 (默认True)

    # === 性能配置 ===
    timeout_seconds: float  # 检索超时时间 (默认10s)
    enable_caching: bool  # 是否启用缓存 (默认True)


# Story 23.4: 默认数据源权重配置 (Feature 2.2: textbook removed per GDA-2)
# ✅ Verified from Story 23.4 Dev Notes: Data Sources Overview
DEFAULT_SOURCE_WEIGHTS = {
    "graphiti": 0.30,  # Graphiti知识图谱
    "lancedb": 0.30,  # LanceDB向量检索
    "vault_notes": 0.25,  # Vault笔記検索
    "multimodal": 0.15,  # 多模態検索
}

# Story 2.5: 默认分層 RRF 融合組映射 (Feature 2.2: textbook removed per GDA-2)
# Dense 組: 筆記内容の語義和関鍵詞匹配
# Graph 組: 知識図譜結構、鏈接関係
# Personal 組: 用戶個人筆記和多模態内容
DEFAULT_FUSION_GROUPS: Dict[str, List[str]] = {
    "dense": ["lancedb"],
    "graph": ["graphiti", "cross_canvas"],
    "personal": ["vault_notes", "multimodal"],
}

# 默认配置
DEFAULT_CONFIG = CanvasRAGConfig(
    # === 检索 ===
    retrieval_batch_size=10,
    search_type="hybrid",
    # === 融合 ===
    fusion_strategy="layered_rrf",
    fusion_groups=DEFAULT_FUSION_GROUPS,
    rrf_k=60,
    source_weights=DEFAULT_SOURCE_WEIGHTS,
    time_decay_factor=0.05,
    # === 精排 ===
    reranking_strategy="hybrid_auto",
    reranker_model_name="Alibaba-NLP/gte-reranker-modernbert-base",
    reranker_torch_dtype="float16",
    adaptive_k_buffer=5,
    adaptive_k_min=3,
    adaptive_k_max=15,
    # === 质量门控 ===
    quality_threshold=0.7,
    max_rewrite_iterations=2,
    quality_check_model="ollama/qwen3:8b",
    rewrite_model="ollama/qwen3:8b",
    # === 压缩 (Story 2.10) ===
    context_max_tokens=3000,
    mastery_injection_enabled=True,
    learning_memory_max_tokens=1000,
    staleness_check_enabled=True,
    multi_query_enabled=True,
    multi_query_model="gemini/gemini-2.0-flash",
    # === 过滤与扩展 (Story 2.8) ===
    progressive_scope_enabled=True,
    min_results_threshold=5,
    neighbor_expansion_enabled=True,
    neighbor_max_count=5,
    neighbor_score_decay=0.7,
    tag_jaccard_bridge_enabled=False,
    tag_jaccard_threshold=0.3,
    # === 图片 (Story 2.9) ===
    ocr_model="gemini/gemini-2.0-flash",
    # === 成本 ===
    cohere_monthly_limit=50,
    enable_cost_monitoring=True,
    # === 性能 ===
    timeout_seconds=10.0,
    enable_caching=True,
)


def validate_config(config: CanvasRAGConfig) -> CanvasRAGConfig:
    """
    Story 2.11 AC-3: Validate all config parameters, replace invalid with defaults + WARNING log.

    Args:
        config: Config dict to validate.

    Returns:
        Validated config dict (invalid values replaced with defaults).
    """
    import logging

    _cfg_logger = logging.getLogger(__name__)
    validated = dict(config)

    # --- Numeric range rules ---
    _VALIDATION_RULES: Dict[str, dict] = {
        "rrf_k": {"type": int, "min": 1},
        "max_rewrite_iterations": {"type": int, "min": 0, "max": 5},
        "quality_threshold": {"type": (int, float), "min": 0.0, "max": 1.0},
        "adaptive_k_min": {"type": int, "min": 1},
        "adaptive_k_max": {"type": int, "min": 1},
        "adaptive_k_buffer": {"type": int, "min": 0},
        "context_max_tokens": {"type": int, "min": 100},
        "neighbor_score_decay": {"type": (int, float), "min": 0.0, "max": 1.0},
        "tag_jaccard_threshold": {"type": (int, float), "min": 0.0, "max": 1.0},
        "timeout_seconds": {"type": (int, float), "min": 1},
        "min_results_threshold": {"type": int, "min": 1},
        "neighbor_max_count": {"type": int, "min": 1},
        "learning_memory_max_tokens": {"type": int, "min": 100},
        "retrieval_batch_size": {"type": int, "min": 1},
        "time_decay_factor": {"type": (int, float), "min": 0.0, "max": 1.0},
        "cohere_monthly_limit": {"type": int, "min": 0},
    }

    for param, rules in _VALIDATION_RULES.items():
        if param not in validated:
            continue
        value = validated[param]
        valid = True
        # YAML parses `true`/`false` as bool, which is a subclass of int in Python.
        # Reject bools when an int/float is expected to avoid silent misinterpretation
        # (e.g., YAML `true` -> Python True -> int 1).
        if isinstance(value, bool):
            valid = False
        elif not isinstance(value, rules["type"]):
            valid = False
        elif "min" in rules and value < rules["min"]:
            valid = False
        elif "max" in rules and value > rules["max"]:
            valid = False

        if not valid:
            default_val = DEFAULT_CONFIG.get(param)
            _cfg_logger.warning(
                f"[CONFIG-WARN] Invalid value for {param}: {value}, using default {default_val}"
            )
            validated[param] = default_val

    # --- Enum rules ---
    _ENUM_RULES: Dict[str, set] = {
        "fusion_strategy": {"rrf", "weighted", "cascade", "layered_rrf"},
        "reranking_strategy": {"local", "cohere", "hybrid_auto"},
        "search_type": {"vector", "hybrid"},
    }
    for param, allowed in _ENUM_RULES.items():
        if param not in validated:
            continue
        value = validated[param]
        if not isinstance(value, str) or value not in allowed:
            default_val = DEFAULT_CONFIG.get(param)
            _cfg_logger.warning(
                f"[CONFIG-WARN] Invalid value for {param}: {value}, using default {default_val}"
            )
            validated[param] = default_val

    # --- Boolean rules ---
    _BOOL_FIELDS = [
        "mastery_injection_enabled",
        "staleness_check_enabled",
        "multi_query_enabled",
        "progressive_scope_enabled",
        "neighbor_expansion_enabled",
        "tag_jaccard_bridge_enabled",
        "enable_cost_monitoring",
        "enable_caching",
    ]
    for param in _BOOL_FIELDS:
        if param not in validated:
            continue
        value = validated[param]
        if not isinstance(value, bool):
            default_val = DEFAULT_CONFIG.get(param)
            _cfg_logger.warning(
                f"[CONFIG-WARN] Invalid value for {param}: {value}, using default {default_val}"
            )
            validated[param] = default_val

    # --- String rules (model names must be non-empty strings) ---
    _STRING_FIELDS = [
        "reranker_model_name",
        "reranker_torch_dtype",
        "quality_check_model",
        "rewrite_model",
        "multi_query_model",
        "ocr_model",
    ]
    for param in _STRING_FIELDS:
        if param not in validated:
            continue
        value = validated[param]
        if not isinstance(value, str) or not value.strip():
            default_val = DEFAULT_CONFIG.get(param)
            _cfg_logger.warning(
                f"[CONFIG-WARN] Invalid value for {param}: {value}, using default {default_val}"
            )
            validated[param] = default_val

    # --- Dict rules: fusion_groups and source_weights ---
    if "fusion_groups" in validated:
        fg = validated["fusion_groups"]
        valid_fg = True
        if not isinstance(fg, dict):
            valid_fg = False
        else:
            for grp_name, grp_sources in fg.items():
                if not isinstance(grp_name, str) or not isinstance(grp_sources, list):
                    valid_fg = False
                    break
                if not all(isinstance(s, str) for s in grp_sources):
                    valid_fg = False
                    break
        if not valid_fg:
            _cfg_logger.warning(
                f"[CONFIG-WARN] Invalid fusion_groups: {fg}, using default"
            )
            validated["fusion_groups"] = DEFAULT_CONFIG.get("fusion_groups")

    if "source_weights" in validated:
        sw = validated["source_weights"]
        valid_sw = True
        if not isinstance(sw, dict):
            valid_sw = False
        else:
            for sw_key, sw_val in sw.items():
                if not isinstance(sw_key, str) or not isinstance(sw_val, (int, float)):
                    valid_sw = False
                    break
                if isinstance(sw_val, bool):
                    valid_sw = False
                    break
        if not valid_sw:
            _cfg_logger.warning(
                f"[CONFIG-WARN] Invalid source_weights: {sw}, using default"
            )
            validated["source_weights"] = DEFAULT_CONFIG.get("source_weights")

    # Cross-field: adaptive_k_max >= adaptive_k_min
    ak_min = validated.get("adaptive_k_min", 3)
    ak_max = validated.get("adaptive_k_max", 15)
    if isinstance(ak_min, int) and isinstance(ak_max, int) and ak_max < ak_min:
        _cfg_logger.warning(
            f"[CONFIG-WARN] adaptive_k_max ({ak_max}) < adaptive_k_min ({ak_min}), "
            f"using defaults {DEFAULT_CONFIG.get('adaptive_k_min')}/{DEFAULT_CONFIG.get('adaptive_k_max')}"
        )
        validated["adaptive_k_min"] = DEFAULT_CONFIG.get("adaptive_k_min", 3)
        validated["adaptive_k_max"] = DEFAULT_CONFIG.get("adaptive_k_max", 15)

    return CanvasRAGConfig(**validated)  # type: ignore[arg-type]


def load_config_from_file(file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Story 2.11 AC-5: Load config from YAML file.

    Args:
        file_path: Path to YAML config file. Defaults to config/rag_config.yaml.

    Returns:
        Dict of config values, or None if file not found.
    """
    import logging

    _cfg_logger = logging.getLogger(__name__)

    if file_path is None:
        # Try standard locations relative to __file__ (stable) and cwd (fallback).
        # __file__-relative is preferred because os.getcwd() changes depending on
        # how the process is launched (pytest, Docker, IDE, etc.).
        _this_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(_this_dir, "..", "..", "config", "rag_config.yaml"),
            os.path.join(os.getcwd(), "config", "rag_config.yaml"),
        ]
        for candidate in candidates:
            normalized = os.path.normpath(candidate)
            if os.path.isfile(normalized):
                file_path = normalized
                break

    if file_path is None or not os.path.isfile(file_path):
        _cfg_logger.info("[CONFIG] No config file found, using all defaults")
        return None

    try:
        import yaml

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        _cfg_logger.info(f"[CONFIG] Loaded config from {file_path} ({len(data)} keys)")
        return data
    except ImportError:
        _cfg_logger.warning(
            "[CONFIG] pyyaml not installed, cannot load YAML config file"
        )
        return None
    except Exception as e:
        _cfg_logger.warning(f"[CONFIG] Failed to load config file {file_path}: {e}")
        return None


def merge_config(user_config: Optional[CanvasRAGConfig] = None) -> CanvasRAGConfig:
    """
    Story 2.11: Merge config with priority: user_config > file config > defaults.

    Also runs validation on the merged result.

    Args:
        user_config: Runtime config overrides (optional).

    Returns:
        Validated, merged config.
    """
    merged = DEFAULT_CONFIG.copy()

    # Layer 1: File config (lowest priority above defaults)
    file_config = load_config_from_file()
    if file_config:
        merged.update(file_config)

    # Layer 2: User/API runtime config (highest priority)
    if user_config:
        merged.update(user_config)

    # Validate
    merged = validate_config(merged)
    return merged


def generate_default_config_file(output_path: str = "config/rag_config.yaml") -> str:
    """
    Story 2.11: Generate a default YAML config file from DEFAULT_CONFIG.

    Iterates over DEFAULT_CONFIG keys to produce the YAML file,
    ensuring the generated file always stays in sync with the code-level
    defaults instead of drifting via a static template literal.

    Args:
        output_path: Where to write the file.

    Returns:
        Absolute path of written file.
    """
    import yaml

    header = (
        "# Canvas Learning System — RAG Pipeline Configuration\n"
        "# Modify values below to tune the search pipeline without code changes.\n"
        "# Invalid values will be replaced with defaults + WARNING log.\n"
        "# Auto-generated from DEFAULT_CONFIG.\n\n"
    )

    # Serialize scalar values from DEFAULT_CONFIG to YAML.
    # Complex nested dicts (fusion_groups, source_weights) are excluded because
    # they require careful editing and should be modified in code.
    scalar_config = {k: v for k, v in DEFAULT_CONFIG.items() if not isinstance(v, dict)}
    yaml_body = yaml.dump(
        scalar_config,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    content = header + yaml_body
    dirpath = os.path.dirname(output_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(output_path)
