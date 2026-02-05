"""
记忆系统专用日志模块
输出到: backend/logs/memory-system-{date}.log

用于记录 Neo4j/LanceDB/Graphiti 连接状态和错误，
方便通过前端 UI 查看和调试。
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime


def setup_memory_system_logger() -> logging.Logger:
    """
    配置记忆系统专用日志

    Features:
    - 按日期命名的日志文件
    - 按大小轮转 (最大 10MB)
    - 保留最近 14 个文件
    - UTF-8 编码支持中文
    """
    logger = logging.getLogger("memory_system")

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # 创建日志目录
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # 日志文件 (按日期命名)
    log_file = log_dir / f"memory-system-{datetime.now().strftime('%Y-%m-%d')}.log"

    # 文件处理器 (按大小轮转, 最大 10MB, 保留 14 个文件)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=14,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # 日志格式
    formatter = logging.Formatter(
        "[%(asctime)s] | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # 同时输出到控制台 (INFO 级别以上)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# 全局日志实例
memory_logger = setup_memory_system_logger()


# 便捷函数
def log_neo4j_init(uri: str, pool_size: int, timeout: float):
    """记录 Neo4j 初始化"""
    memory_logger.info(f"NEO4J_INIT | uri={uri} | pool_size={pool_size} | timeout={timeout}s")


def log_neo4j_auth_failed(uri: str, error: str):
    """记录 Neo4j 认证失败"""
    memory_logger.error(f"NEO4J_AUTH_FAILED | uri={uri} | error={error}")


def log_neo4j_connection_failed(uri: str, error: str):
    """记录 Neo4j 连接失败"""
    memory_logger.error(f"NEO4J_CONNECTION_FAILED | uri={uri} | error={error}")


def log_neo4j_health_check(status: str, latency_ms: float = None, error: str = None):
    """记录 Neo4j 健康检查结果"""
    if status == "success":
        memory_logger.info(f"NEO4J_HEALTH_CHECK | status=SUCCESS | latency={latency_ms:.2f}ms")
    else:
        memory_logger.warning(f"NEO4J_HEALTH_CHECK | status=FAILED | error={error}")


def log_neo4j_fallback(reason: str):
    """记录 Neo4j 降级到 JSON 存储"""
    memory_logger.warning(f"NEO4J_FALLBACK_TO_JSON | reason={reason}")


def log_neo4j_query_failed(query: str, error: str):
    """记录 Neo4j 查询失败"""
    # 截断长查询
    query_preview = query[:100] + "..." if len(query) > 100 else query
    memory_logger.error(f"NEO4J_QUERY_FAILED | query={query_preview} | error={error}")


def log_graphiti_status(status: str, error: str = None):
    """记录 Graphiti 状态"""
    if error:
        memory_logger.warning(f"GRAPHITI_STATUS | status={status} | error={error}")
    else:
        memory_logger.info(f"GRAPHITI_STATUS | status={status}")


def log_lancedb_status(status: str, path: str = None, error: str = None):
    """记录 LanceDB 状态"""
    if error:
        memory_logger.warning(f"LANCEDB_STATUS | status={status} | error={error}")
    else:
        memory_logger.info(f"LANCEDB_STATUS | status={status} | path={path}")
