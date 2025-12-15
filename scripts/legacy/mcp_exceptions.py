"""
MCP语义记忆服务统一异常类
Canvas Learning System - Story 8.8

提供统一的异常处理机制，改善错误诊断和用户体验。
"""

from enum import Enum
from typing import Optional, Any, Dict


class MCPErrorCode(Enum):
    """MCP错误代码枚举"""

    # 依赖相关错误 (1000-1099)
    DEP_MISSING_CHROMADB = 1001
    DEP_MISSING_SENTENCE_TRANSFORMERS = 1002
    DEP_MISSING_NUMPY = 1003
    DEP_MISSING_JIEBA = 1004
    DEP_MISSING_SKLEARN = 1005
    DEP_MISSING_PSUTIL = 1006
    DEP_MISSING_TORCH = 1007

    # 配置相关错误 (1100-1199)
    CONFIG_FILE_NOT_FOUND = 1101
    CONFIG_PARSE_ERROR = 1102
    CONFIG_INVALID_FORMAT = 1103
    CONFIG_MISSING_REQUIRED_FIELD = 1104
    CONFIG_INVALID_VALUE = 1105

    # 模型相关错误 (1200-1299)
    MODEL_LOAD_FAILED = 1201
    MODEL_NOT_FOUND = 1202
    MODEL_EMBEDDING_FAILED = 1203
    MODEL_INFERENCE_FAILED = 1204

    # 数据库相关错误 (1300-1399)
    DB_CONNECTION_FAILED = 1301
    DB_COLLECTION_ERROR = 1302
    DB_STORAGE_ERROR = 1303
    DB_QUERY_ERROR = 1304
    DB_DELETE_ERROR = 1305

    # 记忆操作错误 (1400-1499)
    MEMORY_STORAGE_FAILED = 1401
    MEMORY_RETRIEVAL_FAILED = 1402
    MEMORY_COMPRESSION_FAILED = 1403
    MEMORY_VALIDATION_FAILED = 1404
    MEMORY_NOT_FOUND = 1405

    # 搜索相关错误 (1500-1599)
    SEARCH_INVALID_QUERY = 1501
    SEARCH_RESULTS_EMPTY = 1502
    SEARCH_TIMEOUT = 1503
    SEARCH_INDEX_ERROR = 1504

    # 语义处理错误 (1600-1699)
    SEMANTIC_PROCESSING_FAILED = 1601
    CONCEPT_EXTRACTION_FAILED = 1602
    TAG_GENERATION_FAILED = 1603
    TEXT_TOO_LONG = 1604
    TEXT_ENCODING_ERROR = 1605

    # 创意联想错误 (1700-1799)
    CREATIVE_ASSOCIATION_FAILED = 1701
    ANALOGY_GENERATION_FAILED = 1702
    LEARNING_PATH_GENERATION_FAILED = 1703
    CROSS_DOMAIN_CONNECTION_FAILED = 1704

    # Canvas集成错误 (1800-1899)
    CANVAS_FILE_NOT_FOUND = 1801
    CANVAS_PARSE_ERROR = 1802
    CANVAS_INVALID_FORMAT = 1803
    CANVAS_NODE_PROCESSING_FAILED = 1804

    # 硬件检测错误 (1900-1999)
    HARDWARE_DETECTION_FAILED = 1901
    GPU_NOT_AVAILABLE = 1902
    INSUFFICIENT_MEMORY = 1903
    DEVICE_INITIALIZATION_FAILED = 1904

    # 通用错误 (2000-2999)
    UNKNOWN_ERROR = 2001
    INITIALIZATION_FAILED = 2002
    OPERATION_TIMEOUT = 2003
    RESOURCE_EXHAUSTED = 2004
    PERMISSION_DENIED = 2005


class MCPException(Exception):
    """MCP服务基础异常类"""

    def __init__(
        self,
        error_code: MCPErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.cause = cause
        self.timestamp = __import__('datetime').datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "cause": str(self.cause) if self.cause else None
        }

    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"


class MCPDependencyError(MCPException):
    """MCP依赖错误"""

    def __init__(self, dependency_name: str, install_command: str, cause: Exception = None):
        message = f"缺少必要依赖: {dependency_name}"
        details = {
            "dependency_name": dependency_name,
            "install_command": install_command,
            "installation_guide": f"请运行: pip install {install_command}"
        }
        super().__init__(
            error_code=getattr(MCPErrorCode, f"DEP_MISSING_{dependency_name.upper()}"),
            message=message,
            details=details,
            cause=cause
        )


class MCPConfigurationError(MCPException):
    """MCP配置错误"""

    def __init__(self, config_path: str, error_type: str, details: str, cause: Exception = None):
        message = f"配置文件错误 ({error_type}): {details}"
        error_code_map = {
            "not_found": MCPErrorCode.CONFIG_FILE_NOT_FOUND,
            "parse_error": MCPErrorCode.CONFIG_PARSE_ERROR,
            "invalid_format": MCPErrorCode.CONFIG_INVALID_FORMAT,
            "missing_field": MCPErrorCode.CONFIG_MISSING_REQUIRED_FIELD,
            "invalid_value": MCPErrorCode.CONFIG_INVALID_VALUE
        }

        super().__init__(
            error_code=error_code_map.get(error_type, MCPErrorCode.CONFIG_INVALID_FORMAT),
            message=message,
            details={
                "config_path": config_path,
                "error_type": error_type,
                "error_details": details
            },
            cause=cause
        )


class MCPModelLoadError(MCPException):
    """MCP模型加载错误"""

    def __init__(self, model_name: str, error_type: str, details: str, cause: Exception = None):
        message = f"模型加载错误 ({error_type}): {details}"
        error_code_map = {
            "load_failed": MCPErrorCode.MODEL_LOAD_FAILED,
            "not_found": MCPErrorCode.MODEL_NOT_FOUND,
            "embedding_failed": MCPErrorCode.MODEL_EMBEDDING_FAILED,
            "inference_failed": MCPErrorCode.MODEL_INFERENCE_FAILED
        }

        super().__init__(
            error_code=error_code_map.get(error_type, MCPErrorCode.MODEL_LOAD_FAILED),
            message=message,
            details={
                "model_name": model_name,
                "error_type": error_type,
                "error_details": details
            },
            cause=cause
        )


class MCPDatabaseError(MCPException):
    """MCP数据库错误"""

    def __init__(self, operation: str, details: str, cause: Exception = None):
        message = f"数据库操作错误 ({operation}): {details}"
        error_code_map = {
            "connection": MCPErrorCode.DB_CONNECTION_FAILED,
            "collection": MCPErrorCode.DB_COLLECTION_ERROR,
            "storage": MCPErrorCode.DB_STORAGE_ERROR,
            "query": MCPErrorCode.DB_QUERY_ERROR,
            "delete": MCPErrorCode.DB_DELETE_ERROR
        }

        super().__init__(
            error_code=error_code_map.get(operation, MCPErrorCode.DB_QUERY_ERROR),
            message=message,
            details={
                "operation": operation,
                "error_details": details
            },
            cause=cause
        )


class MCPMemoryError(MCPException):
    """MCP记忆操作错误"""

    def __init__(self, operation: str, memory_id: str = None, details: str = "", cause: Exception = None):
        message = f"记忆操作错误 ({operation}): {details}"
        error_code_map = {
            "storage": MCPErrorCode.MEMORY_STORAGE_FAILED,
            "retrieval": MCPErrorCode.MEMORY_RETRIEVAL_FAILED,
            "compression": MCPErrorCode.MEMORY_COMPRESSION_FAILED,
            "validation": MCPErrorCode.MEMORY_VALIDATION_FAILED,
            "not_found": MCPErrorCode.MEMORY_NOT_FOUND
        }

        super().__init__(
            error_code=error_code_map.get(operation, MCPErrorCode.MEMORY_STORAGE_FAILED),
            message=message,
            details={
                "operation": operation,
                "memory_id": memory_id,
                "error_details": details
            },
            cause=cause
        )


class MCPSearchError(MCPException):
    """MCP搜索错误"""

    def __init__(self, error_type: str, query: str = None, details: str = "", cause: Exception = None):
        message = f"搜索错误 ({error_type}): {details}"
        error_code_map = {
            "invalid_query": MCPErrorCode.SEARCH_INVALID_QUERY,
            "results_empty": MCPErrorCode.SEARCH_RESULTS_EMPTY,
            "timeout": MCPErrorCode.SEARCH_TIMEOUT,
            "index_error": MCPErrorCode.SEARCH_INDEX_ERROR
        }

        super().__init__(
            error_code=error_code_map.get(error_type, MCPErrorCode.SEARCH_INVALID_QUERY),
            message=message,
            details={
                "error_type": error_type,
                "query": query,
                "error_details": details
            },
            cause=cause
        )


class MCPSemanticError(MCPException):
    """MCP语义处理错误"""

    def __init__(self, operation: str, text_preview: str = None, details: str = "", cause: Exception = None):
        message = f"语义处理错误 ({operation}): {details}"
        error_code_map = {
            "processing_failed": MCPErrorCode.SEMANTIC_PROCESSING_FAILED,
            "concept_extraction": MCPErrorCode.CONCEPT_EXTRACTION_FAILED,
            "tag_generation": MCPErrorCode.TAG_GENERATION_FAILED,
            "text_too_long": MCPErrorCode.TEXT_TOO_LONG,
            "encoding_error": MCPErrorCode.TEXT_ENCODING_ERROR
        }

        super().__init__(
            error_code=error_code_map.get(operation, MCPErrorCode.SEMANTIC_PROCESSING_FAILED),
            message=message,
            details={
                "operation": operation,
                "text_preview": text_preview[:100] if text_preview else None,
                "error_details": details
            },
            cause=cause
        )


class MCPCreativeError(MCPException):
    """MCP创意联想错误"""

    def __init__(self, operation: str, concept: str = None, details: str = "", cause: Exception = None):
        message = f"创意联想错误 ({operation}): {details}"
        error_code_map = {
            "association_failed": MCPErrorCode.CREATIVE_ASSOCIATION_FAILED,
            "analogy_failed": MCPErrorCode.ANALOGY_GENERATION_FAILED,
            "learning_path_failed": MCPErrorCode.LEARNING_PATH_GENERATION_FAILED,
            "cross_domain_failed": MCPErrorCode.CROSS_DOMAIN_CONNECTION_FAILED
        }

        super().__init__(
            error_code=error_code_map.get(operation, MCPErrorCode.CREATIVE_ASSOCIATION_FAILED),
            message=message,
            details={
                "operation": operation,
                "concept": concept,
                "error_details": details
            },
            cause=cause
        )


class MCPCanvasError(MCPException):
    """MCP Canvas集成错误"""

    def __init__(self, operation: str, canvas_path: str = None, details: str = "", cause: Exception = None):
        message = f"Canvas集成错误 ({operation}): {details}"
        error_code_map = {
            "file_not_found": MCPErrorCode.CANVAS_FILE_NOT_FOUND,
            "parse_error": MCPErrorCode.CANVAS_PARSE_ERROR,
            "invalid_format": MCPErrorCode.CANVAS_INVALID_FORMAT,
            "node_processing": MCPErrorCode.CANVAS_NODE_PROCESSING_FAILED
        }

        super().__init__(
            error_code=error_code_map.get(operation, MCPErrorCode.CANVAS_PARSE_ERROR),
            message=message,
            details={
                "operation": operation,
                "canvas_path": canvas_path,
                "error_details": details
            },
            cause=cause
        )


class MCPHardwareError(MCPException):
    """MCP硬件检测错误"""

    def __init__(self, operation: str, component: str = None, details: str = "", cause: Exception = None):
        message = f"硬件检测错误 ({operation}): {details}"
        error_code_map = {
            "detection_failed": MCPErrorCode.HARDWARE_DETECTION_FAILED,
            "gpu_not_available": MCPErrorCode.GPU_NOT_AVAILABLE,
            "insufficient_memory": MCPErrorCode.INSUFFICIENT_MEMORY,
            "device_init_failed": MCPErrorCode.DEVICE_INITIALIZATION_FAILED
        }

        super().__init__(
            error_code=error_code_map.get(operation, MCPErrorCode.HARDWARE_DETECTION_FAILED),
            message=message,
            details={
                "operation": operation,
                "component": component,
                "error_details": details
            },
            cause=cause
        )


# 便捷函数
def handle_exception(func):
    """异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MCPException as e:
            # 记录MCP异常
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"MCP异常: {e.to_dict()}")
            raise
        except Exception as e:
            # 包装为通用异常
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"未知异常: {str(e)}")
            raise MCPException(
                error_code=MCPErrorCode.UNKNOWN_ERROR,
                message=f"未知错误: {str(e)}",
                cause=e
            ) from e
    return wrapper


def create_dependency_error(dependency_name: str, install_command: str) -> MCPDependencyError:
    """创建依赖错误的便捷函数"""
    return MCPDependencyError(dependency_name, install_command)


def create_config_error(config_path: str, error_type: str, details: str) -> MCPConfigurationError:
    """创建配置错误的便捷函数"""
    return MCPConfigurationError(config_path, error_type, details)


def create_model_error(model_name: str, error_type: str, details: str) -> MCPModelLoadError:
    """创建模型错误的便捷函数"""
    return MCPModelLoadError(model_name, error_type, details)


def create_database_error(operation: str, details: str) -> MCPDatabaseError:
    """创建数据库错误的便捷函数"""
    return MCPDatabaseError(operation, details)


def create_memory_error(operation: str, memory_id: str = None, details: str = "") -> MCPMemoryError:
    """创建记忆错误的便捷函数"""
    return MCPMemoryError(operation, memory_id, details)


def create_search_error(error_type: str, query: str = None, details: str = "") -> MCPSearchError:
    """创建搜索错误的便捷函数"""
    return MCPSearchError(error_type, query, details)


def create_semantic_error(operation: str, text_preview: str = None, details: str = "") -> MCPSemanticError:
    """创建语义处理错误的便捷函数"""
    return MCPSemanticError(operation, text_preview, details)


def create_canvas_error(operation: str, canvas_path: str = None, details: str = "") -> MCPCanvasError:
    """创建Canvas错误的便捷函数"""
    return MCPCanvasError(operation, canvas_path, details)


def create_hardware_error(operation: str, component: str = None, details: str = "") -> MCPHardwareError:
    """创建硬件错误的便捷函数"""
    return MCPHardwareError(operation, component, details)


# 测试用例
if __name__ == "__main__":
    # 测试异常创建
    try:
        raise create_dependency_error("chromadb", "pip install chromadb")
    except MCPException as e:
        print(f"异常信息: {e.to_dict()}")

    try:
        raise create_config_error("config.yaml", "not_found", "文件不存在")
    except MCPException as e:
        print(f"异常信息: {e.to_dict()}")