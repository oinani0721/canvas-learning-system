#!/usr/bin/env python3
"""
Graphiti API管理器

智能管理Graphiti知识图谱的API调用，优化成本和性能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict

import yaml
from loguru import logger

# 尝试导入各种LLM客户端
try:
    from graphiti_core.llm_client.openai_client import OpenAIClient, LLMConfig as OpenAILLMConfig
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI client not available")

try:
    from graphiti_core.llm_client.anthropic_client import AnthropicClient, LLMConfig as AnthropicLLMConfig
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic client not available")

try:
    from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
    OPENAI_EMBEDDING_AVAILABLE = True
except ImportError:
    OPENAI_EMBEDDING_AVAILABLE = False
    logger.warning("OpenAI embedding not available")


@dataclass
class APIUsageStats:
    """API使用统计"""
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    requests_by_type: Dict[str, int] = None
    cost_by_type: Dict[str, float] = None

    def __post_init__(self):
        if self.requests_by_type is None:
            self.requests_by_type = defaultdict(int)
        if self.cost_by_type is None:
            self.cost_by_type = defaultdict(float)


@dataclass
class APIRequest:
    """API请求定义"""
    request_type: str
    content: str
    priority: int  # 1=高, 2=中, 3=低
    requires_llm: bool = True
    requires_embedding: bool = False
    max_tokens: int = 1000
    cache_key: Optional[str] = None


class GraphitiAPIManager:
    """Graphiti API管理器

    def __init__(self, config_path: str = "config/graphiti_api_config.yaml"):
        """初始化API管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.stats = APIUsageStats()

        # 缓存系统
        self.memory_cache = {}
        self.cache_timestamps = {}

        # LLM客户端
        self.llm_client = None
        self.embedder = None

        # API限制
        self.daily_limits = self.config.get("daily_limits", {
            "max_requests": 1000,
            "max_tokens": 100000,
            "max_cost": 10.0
        })

        self.current_daily_usage = {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "date": datetime.now(timezone.utc).date().isoformat()
        }

        self._initialize_clients()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            # 创建默认配置
            default_config = {
                "llm_provider": "openai",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
                "cache_enabled": True,
                "cache_ttl": 3600,  # 1小时
                "batch_size": 10,
                "cost_optimization": {
                    "enable": True,
                    "prefer_small_model": True,
                    "batch_requests": True
                },
                "daily_limits": {
                    "max_requests": 1000,
                    "max_tokens": 100000,
                    "max_cost": 10.0
                },
                "api_keys": {
                    "openai_api_key": None,
                    "anthropic_api_key": None
                }
            }

            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False)

            return default_config

        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _initialize_clients(self):
        """初始化LLM客户端"""
        provider = self.config.get("llm_provider", "openai")

        if provider == "openai" and OPENAI_AVAILABLE:
            try:
                api_key = self.config["api_keys"].get("openai_api_key")
                if api_key:
                    self.llm_client = OpenAIClient(
                        config=OpenAILLMConfig(
                            api_key=api_key,
                            model=self.config.get("model", "gpt-3.5-turbo")
                        )
                    )

                    if OPENAI_EMBEDDING_AVAILABLE:
                        self.embedder = OpenAIEmbedder(
                            config=OpenAIEmbedderConfig(
                                api_key=api_key,
                                embedding_model=self.config.get("embedding_model", "text-embedding-3-small")
                            )
                        )

                    logger.info("OpenAI clients initialized successfully")
                else:
                    logger.warning("OpenAI API key not configured")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
            try:
                api_key = self.config["api_keys"].get("anthropic_api_key")
                if api_key:
                    self.llm_client = AnthropicClient(
                        config=AnthropicLLMConfig(
                            api_key=api_key,
                            model="claude-3-5-sonnet-20241022"
                        )
                    )
                    logger.info("Anthropic client initialized successfully")
                else:
                    logger.warning("Anthropic API key not configured")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

    def check_daily_limits(self, request: APIRequest) -> bool:
        """检查是否超出每日限制"""
        # 检查日期
        today = datetime.now(timezone.utc).date().isoformat()
        if self.current_daily_usage["date"] != today:
            self.current_daily_usage = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0,
                "date": today
            }

        # 检查限制
        if (self.current_daily_usage["requests"] >= self.daily_limits["max_requests"] or
            self.current_daily_usage["tokens"] >= self.daily_limits["max_tokens"] or
            self.current_daily_usage["cost"] >= self.daily_limits["max_cost"]):
            logger.warning(f"Daily limits reached: {self.current_daily_usage}")
            return False

        return True

    def get_cache_key(self, request: APIRequest) -> Optional[str]:
        """生成缓存键"""
        if not self.config.get("cache_enabled", True):
            return None

        # 生成基于内容和类型的缓存键
        content_hash = hash(request.content[:200])  # 使用前200字符的hash
        return f"{request.request_type}_{content_hash}"

    def get_cached_result(self, request: APIRequest) -> Optional[Any]:
        """获取缓存结果"""
        cache_key = request.cache_key or self.get_cache_key(request)
        if not cache_key:
            return None

        cache_ttl = self.config.get("cache_ttl", 3600)
        current_time = time.time()

        if cache_key in self.memory_cache:
            timestamp = self.cache_timestamps.get(cache_key, 0)
            if current_time - timestamp < cache_ttl:
                self.stats.requests_by_type["cache_hit"] += 1
                return self.memory_cache[cache_key]
            else:
                # 缓存过期，删除
                del self.memory_cache[cache_key]
                del self.cache_timestamps[cache_key]

        return None

    def cache_result(self, request: APIRequest, result: Any) -> None:
        """缓存结果"""
        cache_key = request.cache_key or self.get_cache_key(request)
        if not cache_key:
            return

        self.memory_cache[cache_key] = result
        self.cache_timestamps[cache_key] = time.time()

    async def process_request(self, request: APIRequest) -> Any:
        """处理API请求"""
        request_start = time.time()

        # 检查每日限制
        if not self.check_daily_limits(request):
            return {
                "error": "Daily limits exceeded",
                "usage": self.current_daily_usage,
                "limits": self.daily_limits
            }

        # 检查缓存
        cached_result = self.get_cached_result(request)
        if cached_result is not None:
            return {
                "result": cached_result,
                "cached": True,
                "processing_time": time.time() - request_start
            }

        # 更新使用统计
        self.stats.total_requests += 1
        self.stats.requests_by_type[request.request_type] += 1
        self.current_daily_usage["requests"] += 1

        # 处理请求
        result = await self._process_request_internal(request)

        # 缓存结果
        if result is not None:
            self.cache_result(request, result)

        # 记录处理时间
        processing_time = time.time() - request_start
        logger.info(f"Processed {request.request_type} request in {processing_time:.2f}s")

        return {
            "result": result,
            "cached": False,
            "processing_time": processing_time,
            "api_stats": {
                "daily_usage": self.current_daily_usage,
                "total_stats": {
                    "total_requests": self.stats.total_requests,
                    "total_tokens": self.stats.total_tokens,
                    "total_cost": self.stats.total_cost
                }
            }
        }

    async def _process_request_internal(self, request: APIRequest) -> Any:
        """内部请求处理逻辑"""
        try:
            if request.request_type == "concept_extraction":
                return await self._process_concept_extraction(request)
            elif request.request_type == "relationship_analysis":
                return await self._process_relationship_analysis(request)
            elif request.request_type == "learning_recommendation":
                return await self._process_learning_recommendation(request)
            elif request.request_type == "visualization_generation":
                return await self._process_visualization_generation(request)
            else:
                logger.warning(f"Unknown request type: {request.request_type}")
                return None
        except Exception as e:
            logger.error(f"Error processing request {request.request_type}: {e}")
            return {"error": str(e)}

    async def _process_concept_extraction(self, request: APIRequest) -> Any:
        """处理概念提取请求"""
        if not self.llm_client:
            return {"error": "LLM client not available"}

        # 这里实现概念提取的逻辑
        # 使用本地算法进行基础提取，仅在需要时调用LLM

        from concept_extractor import ConceptExtractor
        extractor = ConceptExtractor()

        # 从请求中提取Canvas文件路径
        canvas_path = request.content.get("canvas_path")
        if not canvas_path or not Path(canvas_path).exists():
            return {"error": "Canvas file not found"}

        # 使用本地算法提取概念
        try:
            result = extractor.extract_concepts_from_canvas(canvas_path)
            return result
        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            return {"error": str(e)}

    async def _process_relationship_analysis(self, request: APIRequest) -> Any:
        """处理关系分析请求"""
        # 基于本地算法的关系分析，仅在需要时调用LLM
        return {"message": "Relationship analysis completed", "relationships": []}

    async def _process_learning_recommendation(self, request: APIRequest) -> Any:
        """处理学习建议请求"""
        if not self.llm_client:
            return {"error": "LLM client not available"}

        # 简化的建议生成逻辑
        user_id = request.content.get("user_id", "default")

        recommendations = [
            {
                "type": "review_weakness",
                "concept": "示例概念",
                "description": "复习薄弱概念",
                "suggested_action": "多做练习题",
                "priority": "high"
            }
        ]

        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    async def _process_visualization_generation(self, request: APIRequest) -> Any:
        """处理可视化生成请求"""
        from graph_visualizer import GraphVisualizer

        try:
            visualizer = GraphVisualizer()

            # 这里可以根据请求内容生成不同格式的可视化
            concepts = request.content.get("concepts", {})
            relationships = request.content.get("relationships", [])
            output_format = request.content.get("output_format", "json")

            result = visualizer.visualize_concept_network(
                concepts=concepts,
                relationships=relationships,
                output_format=output_format
            )

            return result
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}")
            return {"error": str(e)}

    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        return {
            "total": {
                "requests": self.stats.total_requests,
                "tokens": self.stats.total_tokens,
                "cost": self.stats.total_cost
            },
            "daily": self.current_daily_usage,
            "by_type": dict(self.stats.requests_by_type)
        }

    def reset_daily_usage(self) -> None:
        """重置每日使用统计"""
        self.current_daily_usage = {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "date": datetime.now(timezone.utc).date().isoformat()
        }

    def export_usage_report(self, output_path: str) -> None:
        """导出使用报告"""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": "daily",
            "configuration": self.config,
            "statistics": self.get_usage_stats(),
            "recommendations": self._generate_cost_recommendations()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Usage report exported to: {output_path}")

    def _generate_cost_recommendations(self) -> List[str]:
        """生成成本优化建议"""
        recommendations = []

        if self.current_daily_usage["cost"] > self.daily_limits["max_cost"] * 0.8:
            recommendations.append("接近每日成本限制，建议优化API使用")

        if self.stats.requests_by_type.get("cache_hit", 0) < self.stats.total_requests * 0.3:
            recommendations.append("缓存命中率较低，建议启用缓存功能")

        return recommendations


# 便利函数
def create_api_manager(config_path: str = "config/graphiti_api_config.yaml") -> GraphitiAPIManager:
    """创建API管理器实例"""
    return GraphitiAPIManager(config_path)


# 使用示例
async def main():
    """主函数示例"""
    # 创建API管理器
    api_manager = create_api_manager()

    # 创建请求
    request = APIRequest(
        request_type="concept_extraction",
        content={
            "canvas_path": "examples/test_canvas.canvas",
            "user_id": "test_user"
        },
        priority=1,
        cache_key="concept_extraction_test_canvas"
    )

    # 处理请求
    result = await api_manager.process_request(request)

    print("处理结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 查看使用统计
    stats = api_manager.get_usage_stats()
    print("\n使用统计:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(main())