# MCP语义记忆服务API文档

**版本**: v1.0
**最后更新**: 2025-10-23

---

## 📚 目录

- [概述](#概述)
- [核心类和方法](#核心类和方法)
  - [MCPSemanticMemory](#mcsemanticmemory)
  - [SemanticProcessor](#semanticprocessor)
  - [CreativeAssociationEngine](#creativeassociationengine)
  - [MemoryCompressor](#memorycompressor)
  - [CanvasMCPIntegration](#canvasmcpintegration)
- [错误处理](#错误处理)
- [使用示例](#使用示例)
- [性能优化](#性能优化)

---

## 概述

MCP语义记忆服务提供完整的语义记忆、概念提取、创意联想和记忆压缩功能。本文档详细描述了所有公共API的使用方法、参数说明和返回值格式。

---

## 核心类和方法

### MCPSemanticMemory

MCP语义记忆服务的核心客户端，负责记忆的存储、搜索和管理。

#### 初始化

```python
def __init__(self, config_path: str = "config/mcp_config.yaml") -> None:
    """
    初始化MCP语义记忆服务

    Args:
        config_path: MCP配置文件路径

    Raises:
        ImportError: 当必要的依赖库未安装时
        yaml.YAMLError: 当配置文件格式错误时
        Exception: 其他初始化错误

    Example:
        >>> client = MCPSemanticMemory("config/mcp_config.yaml")
        >>> print(f"使用设备: {client.device}")
    """
```

#### 核心方法

##### store_semantic_memory

```python
def store_semantic_memory(self, content: str, metadata: Dict) -> str:
    """
    存储语义记忆

    Args:
        content: 需要记忆的内容文本，最大长度10KB
        metadata: 内容元数据字典，支持以下字段：
            - source_canvas: Canvas文件名
            - source_node_id: Canvas节点ID
            - content_type: 内容类型 ("question", "explanation", "understanding", "concept")
            - tags: 手动标签列表
            - priority: 优先级 (1-10)

    Returns:
        str: 记忆ID，格式为 "memory-{16位十六进制字符}"

    Raises:
        ValueError: 当内容为空或超过长度限制时
        Exception: 当存储失败时

    Example:
        >>> metadata = {
        ...     "source_canvas": "离散数学.canvas",
        ...     "content_type": "concept",
        ...     "tags": ["逻辑", "数学"]
        ... }
        >>> memory_id = client.store_semantic_memory("逆否命题是重要的逻辑概念", metadata)
        >>> print(f"记忆ID: {memory_id}")
        memory-id-abc123def4567890
    """
```

##### search_semantic_memory

```python
def search_semantic_memory(self, query: str, limit: int = 10) -> List[Dict]:
    """
    语义搜索记忆

    Args:
        query: 搜索查询文本，支持中英文自然语言
        limit: 返回结果数量限制，范围1-100

    Returns:
        List[Dict]: 相关记忆列表，每个记忆包含：
            - memory_id: 记忆ID
            - content: 记忆内容
            - metadata: 元数据字典
            - similarity_score: 相似度分数 (0-1)
            - distance: 语义距离 (0-1)

    Raises:
        ValueError: 当查询为空时
        Exception: 当搜索失败时

    Example:
        >>> results = client.search_semantic_memory("逆否命题", limit=5)
        >>> for result in results:
        ...     print(f"{result['memory_id']}: {result['similarity_score']:.3f}")
    """
```

##### auto_generate_tags

```python
def auto_generate_tags(self, content: str, max_tags: int = 10) -> List[str]:
    """
    自动生成内容标签

    Args:
        content: 需要分析的内容文本
        max_tags: 最大标签数量，范围1-50

    Returns:
        List[str]: 生成的标签列表，按相关性排序

    Raises:
        ValueError: 当内容为空或max_tags无效时

    Example:
        >>> tags = client.auto_generate_tags("逆否命题的逻辑结构和应用", 5)
        >>> print(tags)
        ['逆否命题', '逻辑结构', '命题逻辑', '数学概念', '逻辑推理']
    """
```

##### get_memory_stats

```python
def get_memory_stats(self) -> Dict:
    """
    获取记忆统计信息

    Returns:
        Dict: 统计信息字典，包含：
            - total_memories: 总记忆数量
            - device: 使用的设备类型
            - model_name: 嵌入模型名称
            - hardware_info: 硬件信息
            - last_updated: 最后更新时间

    Example:
        >>> stats = client.get_memory_stats()
        >>> print(f"总记忆数: {stats['total_memories']}")
        >>> print(f"使用设备: {stats['device']}")
        总记忆数: 42
        使用设备: cuda
    """
```

### SemanticProcessor

语义处理器，负责文本分析、概念提取和标签生成。

#### 初始化

```python
def __init__(self) -> None:
    """
    初始化语义处理器

    Example:
        >>> processor = SemanticProcessor()
        >>> result = processor.process_text("测试文本")
    """
```

#### 核心方法

##### process_text

```python
def process_text(self, text: str, options: Dict = None) -> Dict:
    """
    处理文本语义信息

    Args:
        text: 需要处理的文本内容
        options: 处理选项字典，支持：
            - extract_concepts: bool, 是否提取概念 (默认True)
            - generate_tags: bool, 是否生成标签 (默认True)
            - max_concepts: int, 最大概念数量 (默认20)
            - max_tags: int, 最大标签数量 (默认10)
            - concept_confidence_threshold: float, 概念置信度阈值 (默认0.5)
            - tag_relevance_threshold: float, 标签相关性阈值 (默认0.3)

    Returns:
        Dict: 处理结果，包含：
            - text_length: 文本长度
            - word_count: 词数量
            - processing_time: 处理时间(秒)
            - concepts: 提取的概念列表
            - tags: 生成的标签列表
            - language: 检测的语言

    Example:
        >>> processor = SemanticProcessor()
        >>> text = "逆否命题是逻辑学中的重要概念，它用于数学证明"
        >>> result = processor.process_text(text)
        >>> print(f"提取概念数: {len(result['concepts'])}")
        >>> print(f"生成标签数: {len(result['tags'])}")
        提取概念数: 2
        生成标签数: 5
    """
```

### CreativeAssociationEngine

创意联想引擎，负责生成创意洞察、类比推理和学习路径建议。

#### 初始化

```python
def __init__(self, memory_client: MCPSemanticMemory = None, config: Dict = None) -> None:
    """
    初始化创意联想引擎

    Args:
        memory_client: MCP记忆客户端实例，可选
        config: 配置字典，可选

    Example:
        >>> engine = CreativeAssociationEngine(memory_client)
        >>> result = engine.generate_creative_associations("逆否命题")
    """
```

#### 核心方法

##### generate_creative_associations

```python
def generate_creative_associations(self, concept: str, creativity_level: str = "moderate") -> Dict:
    """
    生成创意联想

    Args:
        concept: 核心概念文本
        creativity_level: 创意级别，支持：
            - "conservative": 保守级别，温度0.7，最多5个联想
            - "moderate": 中等级别，温度0.9，最多8个联想
            - "creative": 创意级别，温度1.2，最多12个联想

    Returns:
        Dict: 创意联想结果，包含：
            - association_id: 联想ID
            - query_concept: 查询概念
            - creativity_level: 使用的创意级别
            - creative_insights: 创意洞察列表
            - analogies: 类比推理列表
            - practical_applications: 实际应用列表
            - learning_paths: 学习路径列表
            - overall_creativity_score: 总体创意分数 (0-1)

    Example:
        >>> engine = CreativeAssociationEngine()
        >>> result = engine.generate_creative_associations("逆否命题", "creative")
        >>> print(f"创意分数: {result['overall_creativity_score']:.3f}")
        >>> print(f"洞察数量: {len(result['creative_insights'])}")
        创意分数: 0.856
        洞察数量: 8
    """
```

### MemoryCompressor

记忆数据压缩器，负责语义记忆的压缩和优化。

#### 初始化

```python
def __init__(self, memory_client: MCPSemanticMemory, config: Dict = None) -> None:
    """
    初始化记忆压缩器

    Args:
        memory_client: MCP记忆客户端实例
        config: 配置字典，可选

    Example:
        >>> compressor = MemoryCompressor(memory_client)
        >>> result = compressor.compress_memories(memory_ids, 0.3)
    """
```

#### 核心方法

##### compress_memories

```python
def compress_memories(self, memory_ids: List[str], compression_ratio: float = 0.3, strategy: str = None) -> CompressionResult:
    """
    压缩记忆数据

    Args:
        memory_ids: 需要压缩的记忆ID列表
        compression_ratio: 目标压缩比例 (0.0-1.0)
        strategy: 压缩策略，支持：
            - "semantic_clustering": 语义聚类 (默认)
            - "frequency_based": 基于频率
            - "temporal_grouping": 时间分组
            - "topic_merging": 主题合并

    Returns:
        CompressionResult: 压缩结果，包含：
            - original_memory_count: 原始记忆数量
            - compressed_memory_count: 压缩后数量
            - compression_ratio: 实际压缩比例
            - information_retention_score: 信息保留分数 (0-1)
            - compression_time_seconds: 压缩耗时
            - clusters: 压缩簇列表

    Example:
        >>> compressor = MemoryCompressor(memory_client)
        >>> result = compressor.compress_memories(memory_ids, 0.3, "semantic_clustering")
        >>> print(f"压缩比: {result.compression_ratio:.3f}")
        >>> print(f"信息保留: {result.information_retention_score:.3f}")
        压缩比: 0.285
        信息保留: 0.912
    """
```

##### auto_compress_memories

```python
def auto_compress_memories(self, threshold: int = 5000, strategy: str = None) -> Dict:
    """
    自动压缩记忆

    Args:
        threshold: 压缩阈值，当记忆数量超过此值时触发压缩
        strategy: 压缩策略，默认使用配置中的策略

    Returns:
        Dict: 自动压缩结果

    Example:
        >>> result = compressor.auto_compress_memories(3000)
        >>> if result['compressed']:
        ...     print(f"压缩完成: {result['compression_ratio']:.2%}")
        >>> else:
        ...     print(f"未压缩: {result['reason']}")
    """
```

### CanvasMCPIntegration

Canvas与MCP集成管理器，提供Canvas内容的语义化处理。

#### 初始化

```python
def __init__(self, mcp_config_path: str = "config/mcp_config.yaml") -> None:
    """
    初始化集成管理器

    Args:
        mcp_config_path: MCP配置文件路径

    Example:
        >>> integration = CanvasMCPIntegration()
        >>> result = integration.integrate_canvas_with_mcp("canvas.canvas")
    """
```

#### 核心方法

##### integrate_canvas_with_mcp

```python
def integrate_canvas_with_mcp(self, canvas_path: str, node_ids: List[str] = None) -> Dict:
    """
    将Canvas内容集成到MCP语义记忆

    Args:
        canvas_path: Canvas文件路径
        node_ids: 指定节点ID列表，None表示处理所有文本节点

    Returns:
        Dict: 集成结果，包含：
            - canvas_path: Canvas路径
            - processed_nodes: 处理的节点数量
            - skipped_nodes: 跳过的节点数量
            - memory_ids: 创建的记忆ID列表
            - processing_errors: 处理错误列表
            - integration_summary: 集成摘要

    Example:
        >>> integration = CanvasMCPIntegration()
        >>> result = integration.integrate_canvas_with_mcp("离散数学.canvas")
        >>> print(f"处理节点: {result['processed_nodes']}")
        >>> print(f"创建记忆: {len(result['memory_ids'])}")
        处理节点: 15
        创建记忆: 15
    """
```

##### semantic_search_canvas

```python
def semantic_search_canvas(self, query: str, canvas_filter: List[str] = None, limit: int = 10) -> List[Dict]:
    """
    在Canvas记忆中进行语义搜索

    Args:
        query: 搜索查询文本
        canvas_filter: Canvas文件过滤列表
        limit: 结果数量限制

    Returns:
        List[Dict]: 搜索结果列表

    Example:
        >>> results = integration.semantic_search_canvas("逆否命题", ["离散数学.canvas"])
        >>> for result in results:
        ...     print(f"{result['source_canvas']}: {result['similarity_score']:.3f}")
    """
```

##### generate_cross_canvas_insights

```python
def generate_cross_canvas_insights(self, concept: str, max_canvases: int = 5) -> Dict:
    """
    跨Canvas生成深度洞察

    Args:
        concept: 核心概念
        max_canvases: 最大搜索Canvas数量

    Returns:
        Dict: 跨Canvas洞察结果

    Example:
        >>> insights = integration.generate_cross_canvas_insights("逻辑")
        >>> print(f"涉及Canvas数: {insights['total_canvases_found']}")
        >>> print(f"跨域连接数: {len(insights['cross_canvas_connections'])}")
        涉及Canvas数: 3
        跨域连接数: 2
    """
```

---

## 错误处理

### 异常类型

系统使用分层异常处理机制，主要异常类型：

#### 依赖异常
```python
class MCPDependencyError(Exception):
    """MCP服务依赖错误"""
    pass

class ModelLoadError(Exception):
    """模型加载错误"""
    pass

class DatabaseConnectionError(Exception):
    """数据库连接错误"""
    pass
```

#### 配置异常
```python
class MCPConfigurationError(Exception):
    """MCP配置错误"""
    pass

class ValidationError(Exception):
    """参数验证错误"""
    pass
```

#### 运行时异常
```python
class MCPRuntimeError(Exception):
    """MCP运行时错误"""
    pass

class MemoryStorageError(Exception):
    """记忆存储错误"""
    pass

class SearchError(Exception):
    """搜索操作错误"""
    pass
```

### 错误处理最佳实践

```python
try:
    client = MCPSemanticMemory(config_path)
    memory_id = client.store_semantic_memory(content, metadata)
except MCPDependencyError as e:
    logger.error(f"依赖错误: {e}")
    # 依赖库安装提示
except MCPConfigurationError as e:
    logger.error(f"配置错误: {e}")
    # 配置文件修复提示
except MemoryStorageError as e:
    logger.error(f"存储错误: {e}")
    # 存储系统检查提示
except Exception as e:
    logger.error(f"未知错误: {e}")
    # 通用错误处理
```

---

## 使用示例

### 基础使用流程

```python
from mcp_memory_client import MCPSemanticMemory
from semantic_processor import SemanticProcessor
from creative_association_engine import CreativeAssociationEngine

# 1. 初始化组件
client = MCPSemanticMemory("config/mcp_config.yaml")
processor = SemanticProcessor()
engine = CreativeAssociationEngine(client)

# 2. 存储记忆
content = "逆否命题是逻辑学中的重要概念，用于数学证明"
metadata = {
    "source_canvas": "离散数学.canvas",
    "content_type": "concept",
    "tags": ["逻辑", "数学"]
}
memory_id = client.store_semantic_memory(content, metadata)

# 3. 语义处理
semantic_result = processor.process_text(content)
print(f"提取概念: {len(semantic_result['concepts'])}")
print(f"生成标签: {semantic_result['tags']}")

# 4. 创意联想
creative_result = engine.generate_creative_associations("逆否命题", "moderate")
print(f"创意分数: {creative_result['overall_creativity_score']:.3f}")

# 5. 搜索记忆
search_results = client.search_semantic_memory("逻辑概念")
for result in search_results:
    print(f"{result['memory_id']}: {result['similarity_score']:.3f}")

# 6. 清理资源
client.close()
```

### Canvas集成示例

```python
from canvas_mcp_integration import create_canvas_integration

# 1. 创建集成管理器
integration = create_canvas_integration()

# 2. 集成Canvas
result = integration.integrate_canvas_with_mcp("笔记库/离散数学/离散数学.canvas")
print(f"处理节点: {result['processed_nodes']}")
print(f"创建记忆: {len(result['memory_ids'])}")

# 3. 语义搜索
search_results = integration.semantic_search_canvas("逆否命题", limit=5)
for result in search_results:
    print(f"来源: {result['source_canvas']}")
    print(f"相似度: {result['similarity_score']:.3f}")

# 4. 跨Canvas洞察
insights = integration.generate_cross_canvas_insights("逻辑", max_canvases=3)
print(f"涉及Canvas: {insights['total_canvases_found']}")
print(f"学习建议数: {len(insights['learning_recommendations'])}")

# 5. 获取统计
stats = integration.get_integration_statistics()
print(f"总记忆数: {stats['memory_statistics']['total_memories']}")
print(f"系统状态: {stats['integration_health']['overall_status']}")

# 6. 清理资源
integration.close()
```

### 高级配置示例

```python
# 自定义配置
config = {
    "mcp_service": {
        "embedding_model": {
            "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "device": "cuda",
            "batch_size": 64
        },
        "semantic_processing": {
            "chunk_size": 1024,
            "extract_concepts": True,
            "generate_tags": True
        },
        "creative_association": {
            "enable": True,
            "creativity_levels": {
                "creative": {
                    "temperature": 1.5,
                    "max_associations": 15
                }
            }
        }
    }
}

# 使用自定义配置初始化
client = MCPSemanticMemory(config_path="custom_config.yaml")
engine = CreativeAssociationEngine(client, config)

# 高级压缩
memory_compressor = MemoryCompressor(client, config)
compression_result = memory_compressor.compress_memories(
    memory_ids=["memory-1", "memory-2", ...],
    compression_ratio=0.2,
    strategy="semantic_clustering"
)
```

---

## 性能优化

### 批处理优化

```python
# 批量存储记忆
batch_size = 32
contents = [f"记忆内容{i}" for i in range(100)]
metadata_list = [{"source": "batch"} for _ in contents]

# 分批处理
for i in range(0, len(contents), batch_size):
    batch_contents = contents[i:i+batch_size]
    batch_metadata = metadata_list[i:i+batch_size]

    # 批量存储
    memory_ids = []
    for content, metadata in zip(batch_contents, batch_metadata):
        memory_id = client.store_semantic_memory(content, metadata)
        memory_ids.append(memory_id)

    print(f"批次 {i//batch_size + 1}: 存储了 {len(memory_ids)} 个记忆")
```

### 搜索优化

```python
# 使用合适的查询策略
def smart_search(client, query, filters=None):
    # 1. 直接搜索
    results = client.search_semantic_memory(query, limit=20)

    # 2. 如果结果不足，扩展搜索
    if len(results) < 5:
        # 使用同义词扩展
        expanded_query = f"{query} 相关概念"
        additional_results = client.search_semantic_memory(expanded_query, limit=10)
        results.extend(additional_results)

    # 3. 应用过滤器
    if filters:
        results = [r for r in results if all(r['metadata'].get(k) == v
                                           for k, v in filters.items())]

    return results
```

### 内存管理

```python
# 定期压缩策略
def periodic_compression(client, threshold=5000):
    stats = client.get_memory_stats()

    if stats['total_memories'] > threshold:
        # 获取所有记忆ID
        all_memory_ids = []  # 实际实现中需要从数据库获取

        # 执行压缩
        compressor = MemoryCompressor(client)
        result = compressor.auto_compress_memories(threshold)

        if result['compressed']:
            print(f"压缩完成: {result['compression_ratio']:.2%}")
            return result

    return {"compressed": False, "reason": "未达到压缩阈值"}
```

---

## 更新日志

### v1.0 (2025-10-23)
- 初始版本发布
- 完整的MCP语义记忆服务API
- 支持语义存储、搜索、压缩和创意联想
- 提供Canvas集成接口
- 完整的错误处理和配置管理

---

**文档维护**: Canvas Learning System Development Team
**最后更新**: 2025-10-23
**联系方式**: 如有疑问，请参考项目文档或提交Issue
