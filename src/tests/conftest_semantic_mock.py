"""
Story 10.11.3 - Semantic Memory Manager Mock Helper
帮助测试正确mock SemanticMemoryManager的get_status()方法
"""

from unittest.mock import Mock


def create_semantic_manager_mock(mode='mcp', initialized=True):
    """
    创建正确配置的SemanticMemoryManager mock对象

    Args:
        mode: 'mcp' | 'fallback' | 'unavailable'
        initialized: 是否初始化成功

    Returns:
        Mock: 配置好的mock对象
    """
    mock_manager = Mock()

    # 根据mode设置相应的属性
    if mode == 'mcp':
        mock_manager.mcp_client = Mock()  # MCP可用
        mock_manager.fallback_cache = None
        features = {
            'add_memory': True,
            'search_memories': True,
            'advanced_semantic_search': True,
            'vector_similarity': True,
            'cross_domain_connections': True,
            'intelligent_tags': True
        }
    elif mode == 'fallback':
        mock_manager.mcp_client = None
        mock_manager.fallback_cache = Mock()  # 降级缓存可用
        features = {
            'add_memory': True,
            'search_memories': True,
            'advanced_semantic_search': False,
            'vector_similarity': False,
            'cross_domain_connections': False,
            'intelligent_tags': False
        }
    else:  # unavailable
        mock_manager.mcp_client = None
        mock_manager.fallback_cache = None
        features = {}

    # Story 10.11.3 AC4: 配置get_status()
    mock_manager.get_status.return_value = {
        'initialized': initialized,
        'mode': mode,
        'features': features
    }

    # 配置默认的返回值
    mock_manager.is_initialized = initialized
    mock_manager.mode = mode
    mock_manager.store_semantic_memory.return_value = f"{mode}_memory_id_123"

    return mock_manager
