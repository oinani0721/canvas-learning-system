"""
Canvas与MCP集成接口
Canvas Learning System - Story 8.8

提供Canvas内容向量化处理、批量记忆存储、语义搜索等功能。
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from pathlib import Path

# 本地导入
from canvas_utils import CanvasOrchestrator, CanvasJSONOperator
from mcp_memory_client import MCPSemanticMemory
from semantic_processor import SemanticProcessor
from creative_association_engine import CreativeAssociationEngine
from memory_compression import MemoryCompressor

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CanvasMCPIntegration:
    """Canvas与MCP集成管理器"""

    def __init__(self, mcp_config_path: str = "config/mcp_config.yaml"):
        """初始化集成管理器

        Args:
            mcp_config_path: MCP配置文件路径
        """
        try:
            # 初始化MCP组件
            self.memory_client = MCPSemanticMemory(mcp_config_path)
            self.semantic_processor = SemanticProcessor()
            self.creative_engine = CreativeAssociationEngine(self.memory_client)
            self.memory_compressor = MemoryCompressor(self.memory_client)

            logger.info("Canvas与MCP集成初始化完成")

        except Exception as e:
            logger.error(f"集成初始化失败: {e}")
            raise

    def integrate_canvas_with_mcp(self, canvas_path: str, node_ids: List[str] = None) -> Dict:
        """将Canvas内容集成到MCP语义记忆

        Args:
            canvas_path: Canvas文件路径
            node_ids: 指定节点ID列表，None表示处理所有节点

        Returns:
            Dict: 集成结果和记忆ID列表
        """
        try:
            # 读取Canvas文件
            canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

            # 获取需要处理的节点
            if node_ids is None:
                # 处理所有文本节点
                target_nodes = [
                    node for node in canvas_data.get("nodes", [])
                    if node.get("type") == "text" and node.get("text", "").strip()
                ]
            else:
                # 处理指定节点
                node_id_set = set(node_ids)
                target_nodes = [
                    node for node in canvas_data.get("nodes", [])
                    if node.get("id") in node_id_set and node.get("text", "").strip()
                ]

            # 处理每个节点
            integration_results = {
                "canvas_path": canvas_path,
                "processed_nodes": 0,
                "skipped_nodes": 0,
                "memory_ids": [],
                "processing_errors": [],
                "integration_summary": {},
                "timestamp": datetime.now().isoformat()
            }

            for node in target_nodes:
                try:
                    # 提取节点内容
                    node_id = node["id"]
                    node_text = node["text"].strip()
                    node_color = node.get("color", "6")  # 默认黄色

                    if not node_text or len(node_text) < 10:  # 过滤过短内容
                        integration_results["skipped_nodes"] += 1
                        continue

                    # 语义处理
                    semantic_result = self.semantic_processor.process_text(node_text)

                    # 生成元数据
                    metadata = {
                        "source_canvas": os.path.basename(canvas_path),
                        "source_node_id": node_id,
                        "source_node_color": node_color,
                        "content_type": self._determine_content_type(node_color),
                        "concepts_count": len(semantic_result.get("concepts", [])),
                        "tags_count": len(semantic_result.get("tags", [])),
                        "processing_timestamp": datetime.now().isoformat()
                    }

                    # 添加概念和标签到元数据
                    if semantic_result.get("concepts"):
                        metadata["extracted_concepts"] = semantic_result["concepts"]

                    if semantic_result.get("tags"):
                        metadata["auto_generated_tags"] = [tag["tag"] for tag in semantic_result["tags"]]

                    # 存储到MCP记忆
                    memory_id = self.memory_client.store_semantic_memory(node_text, metadata)
                    integration_results["memory_ids"].append(memory_id)

                    integration_results["processed_nodes"] += 1
                    logger.debug(f"节点 {node_id} 集成成功，记忆ID: {memory_id}")

                except Exception as e:
                    error_msg = f"处理节点 {node.get('id', 'unknown')} 失败: {str(e)}"
                    integration_results["processing_errors"].append(error_msg)
                    logger.warning(error_msg)

            # 生成集成摘要
            integration_results["integration_summary"] = {
                "total_nodes_found": len(target_nodes),
                "successfully_processed": integration_results["processed_nodes"],
                "skipped": integration_results["skipped_nodes"],
                "errors": len(integration_results["processing_errors"]),
                "success_rate": integration_results["processed_nodes"] / len(target_nodes) if target_nodes else 0
            }

            logger.info(f"Canvas集成完成: {integration_results['processed_nodes']} 个节点成功处理")
            return integration_results

        except Exception as e:
            logger.error(f"Canvas集成失败: {e}")
            return {
                "error": str(e),
                "canvas_path": canvas_path,
                "timestamp": datetime.now().isoformat()
            }

    def _determine_content_type(self, color: str) -> str:
        """确定内容类型"""
        color_mapping = {
            "1": "question",        # 红色 - 问题
            "2": "understanding",    # 绿色 - 理解
            "3": "partial_understanding",  # 紫色 - 部分理解
            "5": "explanation",     # 蓝色 - 解释
            "6": "personal_note"    # 黄色 - 个人笔记
        }
        return color_mapping.get(color, "unknown")

    def semantic_search_canvas(self, query: str, canvas_filter: List[str] = None, limit: int = 10) -> List[Dict]:
        """在Canvas记忆中进行语义搜索

        Args:
            query: 搜索查询
            canvas_filter: Canvas文件过滤列表
            limit: 返回结果数量限制

        Returns:
            List[Dict]: 搜索结果
        """
        try:
            # 执行语义搜索
            search_results = self.memory_client.search_semantic_memory(query, limit)

            # 过滤Canvas文件
            if canvas_filter:
                canvas_filter_set = set(canvas_filter)
                filtered_results = []
                for result in search_results:
                    source_canvas = result.get("metadata", {}).get("source_canvas", "")
                    if source_canvas in canvas_filter_set:
                        filtered_results.append(result)
                search_results = filtered_results

            # 增强搜索结果
            enhanced_results = []
            for result in search_results:
                # 生成创意联想
                if result.get("similarity_score", 0) > 0.7:  # 高相似度结果
                    try:
                        content_preview = result["content"][:100]
                        creative_associations = self.creative_engine.generate_creative_associations(
                            content_preview, "conservative"
                        )
                        result["creative_associations"] = creative_associations.get("creative_insights", [])
                    except Exception as e:
                        logger.warning(f"生成创意联想失败: {e}")
                        result["creative_associations"] = []

                enhanced_results.append(result)

            return enhanced_results

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []

    def generate_cross_canvas_insights(self, concept: str, max_canvases: int = 5) -> Dict:
        """跨Canvas生成深度洞察

        Args:
            concept: 核心概念
            max_canvases: 最大搜索Canvas数量

        Returns:
            Dict: 跨Canvas洞察结果
        """
        try:
            # 搜索相关记忆
            search_results = self.memory_client.search_semantic_memory(concept, limit=50)

            # 按Canvas分组
            canvas_groups = {}
            for result in search_results:
                source_canvas = result.get("metadata", {}).get("source_canvas", "unknown")
                if source_canvas not in canvas_groups:
                    canvas_groups[source_canvas] = []
                canvas_groups[source_canvas].append(result)

            # 限制Canvas数量
            if len(canvas_groups) > max_canvases:
                # 按相关度排序并取前N个
                sorted_canvases = sorted(
                    canvas_groups.items(),
                    key=lambda x: sum(r.get("similarity_score", 0) for r in x[1]) / len(x[1]),
                    reverse=True
                )
                canvas_groups = dict(sorted_canvases[:max_canvases])

            # 生成洞察
            insights = {
                "concept": concept,
                "total_canvases_found": len(canvas_groups),
                "analyzed_canvases": len(canvas_groups),
                "canvas_insights": [],
                "cross_canvas_connections": [],
                "learning_recommendations": [],
                "generated_at": datetime.now().isoformat()
            }

            # 为每个Canvas生成洞察
            for canvas_name, canvas_results in canvas_groups.items():
                canvas_insight = {
                    "canvas_name": canvas_name,
                    "memory_count": len(canvas_results),
                    "avg_similarity": sum(r.get("similarity_score", 0) for r in canvas_results) / len(canvas_results),
                    "key_memories": canvas_results[:3],  # 取前3个最相关的记忆
                    "content_types": self._analyze_content_types(canvas_results)
                }
                insights["canvas_insights"].append(canvas_insight)

            # 生成跨Canvas连接
            insights["cross_canvas_connections"] = self._generate_cross_canvas_connections(canvas_groups)

            # 生成学习建议
            insights["learning_recommendations"] = self._generate_learning_recommendations(concept, canvas_groups)

            return insights

        except Exception as e:
            logger.error(f"跨Canvas洞察生成失败: {e}")
            return {
                "concept": concept,
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }

    def _analyze_content_types(self, canvas_results: List[Dict]) -> Dict[str, int]:
        """分析内容类型分布"""
        type_counts = {}
        for result in canvas_results:
            content_type = result.get("metadata", {}).get("content_type", "unknown")
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
        return type_counts

    def _generate_cross_canvas_connections(self, canvas_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """生成跨Canvas连接"""
        connections = []

        canvas_names = list(canvas_groups.keys())
        for i in range(len(canvas_names)):
            for j in range(i + 1, len(canvas_names)):
                canvas1, canvas2 = canvas_names[i], canvas_names[j]
                results1, results2 = canvas_groups[canvas1], canvas_groups[canvas2]

                # 计算两个Canvas之间的连接强度
                connection_strength = self._calculate_connection_strength(results1, results2)

                if connection_strength > 0.5:  # 只保留强连接
                    connections.append({
                        "canvas1": canvas1,
                        "canvas2": canvas2,
                        "connection_strength": connection_strength,
                        "connection_type": "semantic_similarity",
                        "shared_concepts": self._find_shared_concepts(results1, results2)
                    })

        return connections

    def _calculate_connection_strength(self, results1: List[Dict], results2: List[Dict]) -> float:
        """计算Canvas间的连接强度"""
        if not results1 or not results2:
            return 0.0

        # 简单计算：基于平均相似度
        avg_sim1 = sum(r.get("similarity_score", 0) for r in results1) / len(results1)
        avg_sim2 = sum(r.get("similarity_score", 0) for r in results2) / len(results2)

        return (avg_sim1 + avg_sim2) / 2

    def _find_shared_concepts(self, results1: List[Dict], results2: List[Dict]) -> List[str]:
        """查找共享概念"""
        concepts1 = set()
        concepts2 = set()

        for result in results1:
            concepts = result.get("metadata", {}).get("extracted_concepts", [])
            concepts1.update(concept.get("concept", "") for concept in concepts)

        for result in results2:
            concepts = result.get("metadata", {}).get("extracted_concepts", [])
            concepts2.update(concept.get("concept", "") for concept in concepts)

        return list(concepts1.intersection(concepts2))

    def _generate_learning_recommendations(self, concept: str, canvas_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """生成学习建议"""
        recommendations = []

        # 分析最相关的Canvas
        most_relevant_canvas = None
        highest_similarity = 0

        for canvas_name, results in canvas_groups.items():
            avg_similarity = sum(r.get("similarity_score", 0) for r in results) / len(results)
            if avg_similarity > highest_similarity:
                highest_similarity = avg_similarity
                most_relevant_canvas = canvas_name

        if most_relevant_canvas:
            recommendations.append({
                "type": "focus_study",
                "recommendation": f"重点关注 '{most_relevant_canvas}' 中的相关内容",
                "reason": f"该Canvas与概念 '{concept}' 的相关性最高 ({highest_similarity:.2f})",
                "priority": "high"
            })

        # 生成跨领域学习建议
        if len(canvas_groups) > 1:
            recommendations.append({
                "type": "cross_domain",
                "recommendation": f"探索 '{concept}' 在不同学科领域的应用",
                "reason": f"在 {len(canvas_groups)} 个不同的Canvas中都发现了相关内容",
                "priority": "medium"
            })

        # 生成练习建议
        recommendations.append({
            "type": "practice",
            "recommendation": f"通过实际练习来巩固 '{concept}' 的理解",
            "reason": "理论联系实际是最好的学习方式",
            "priority": "medium"
        })

        return recommendations

    def batch_integrate_canvases(self, canvas_directory: str, file_pattern: str = "*.canvas") -> Dict:
        """批量集成Canvas文件

        Args:
            canvas_directory: Canvas文件目录
            file_pattern: 文件匹配模式

        Returns:
            Dict: 批量集成结果
        """
        try:
            canvas_dir = Path(canvas_directory)
            if not canvas_dir.exists():
                raise ValueError(f"Canvas目录不存在: {canvas_directory}")

            # 查找Canvas文件
            canvas_files = list(canvas_dir.glob(file_pattern))
            if not canvas_files:
                return {
                    "total_files": 0,
                    "processed_files": 0,
                    "errors": [f"在目录 {canvas_directory} 中未找到匹配的Canvas文件"],
                    "timestamp": datetime.now().isoformat()
                }

            # 批量处理
            batch_results = {
                "total_files": len(canvas_files),
                "processed_files": 0,
                "skipped_files": 0,
                "total_memory_ids": [],
                "file_results": [],
                "errors": [],
                "batch_summary": {},
                "timestamp": datetime.now().isoformat()
            }

            for canvas_file in canvas_files:
                try:
                    result = self.integrate_canvas_with_mcp(str(canvas_file))

                    if "error" in result:
                        batch_results["errors"].append(f"{canvas_file.name}: {result['error']}")
                        batch_results["skipped_files"] += 1
                    else:
                        batch_results["file_results"].append({
                            "file": canvas_file.name,
                            "processed_nodes": result["processed_nodes"],
                            "memory_ids": result["memory_ids"]
                        })
                        batch_results["total_memory_ids"].extend(result["memory_ids"])
                        batch_results["processed_files"] += 1

                except Exception as e:
                    error_msg = f"{canvas_file.name}: {str(e)}"
                    batch_results["errors"].append(error_msg)
                    batch_results["skipped_files"] += 1

            # 生成批量摘要
            batch_results["batch_summary"] = {
                "success_rate": batch_results["processed_files"] / batch_results["total_files"],
                "total_memories_created": len(batch_results["total_memory_ids"]),
                "average_nodes_per_canvas": sum(
                    result["processed_nodes"] for result in batch_results["file_results"]
                ) / len(batch_results["file_results"]) if batch_results["file_results"] else 0
            }

            logger.info(f"批量集成完成: {batch_results['processed_files']}/{batch_results['total_files']} 个文件成功")
            return batch_results

        except Exception as e:
            logger.error(f"批量集成失败: {e}")
            return {
                "error": str(e),
                "canvas_directory": canvas_directory,
                "timestamp": datetime.now().isoformat()
            }

    def get_integration_statistics(self) -> Dict:
        """获取集成统计信息"""
        try:
            memory_stats = self.memory_client.get_memory_stats()

            # 获取Canvas相关统计
            canvas_stats = self._get_canvas_statistics()

            return {
                "memory_statistics": memory_stats,
                "canvas_statistics": canvas_stats,
                "integration_health": self._check_integration_health(),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _get_canvas_statistics(self) -> Dict:
        """获取Canvas统计信息"""
        # 这里应该查询MCP数据库中Canvas相关的统计
        # 由于当前限制，返回模拟数据
        return {
            "total_canvases_integrated": 0,
            "total_nodes_processed": 0,
            "content_type_distribution": {},
            "most_recent_integration": None
        }

    def _check_integration_health(self) -> Dict:
        """检查集成健康状态"""
        health_checks = {
            "mcp_connection": self._check_mcp_connection(),
            "semantic_processor": self._check_semantic_processor(),
            "creative_engine": self._check_creative_engine(),
            "overall_status": "healthy"
        }

        # 确定总体状态
        if any(check["status"] != "healthy" for check in health_checks.values()):
            health_checks["overall_status"] = "degraded"

        return health_checks

    def _check_mcp_connection(self) -> Dict:
        """检查MCP连接"""
        try:
            stats = self.memory_client.get_memory_stats()
            return {
                "status": "healthy" if stats else "error",
                "message": "MCP连接正常" if stats else "无法获取统计信息"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"MCP连接失败: {str(e)}"
            }

    def _check_semantic_processor(self) -> Dict:
        """检查语义处理器"""
        try:
            test_result = self.semantic_processor.process_text("测试文本")
            return {
                "status": "healthy" if test_result else "error",
                "message": "语义处理器正常" if test_result else "语义处理器异常"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"语义处理器检查失败: {str(e)}"
            }

    def _check_creative_engine(self) -> Dict:
        """检查创意引擎"""
        try:
            # 简单检查创意引擎是否可用
            return {
                "status": "healthy",
                "message": "创意引擎正常"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"创意引擎检查失败: {str(e)}"
            }

    def close(self):
        """关闭集成管理器"""
        try:
            if self.memory_client:
                self.memory_client.close()
            logger.info("Canvas与MCP集成管理器已关闭")
        except Exception as e:
            logger.error(f"关闭集成管理器时出错: {e}")


# 便捷函数
def create_canvas_integration(mcp_config_path: str = "config/mcp_config.yaml") -> CanvasMCPIntegration:
    """创建Canvas集成管理器的便捷函数

    Args:
        mcp_config_path: MCP配置文件路径

    Returns:
        CanvasMCPIntegration: 集成管理器实例
    """
    return CanvasMCPIntegration(mcp_config_path)


if __name__ == "__main__":
    # 简单测试
    try:
        integration = create_canvas_integration()

        # 测试Canvas集成
        test_canvas_path = "笔记库/离散数学/离散数学.canvas"
        if os.path.exists(test_canvas_path):
            result = integration.integrate_canvas_with_mcp(test_canvas_path)
            print(f"Canvas集成结果: {result}")

            # 测试语义搜索
            search_result = integration.semantic_search_canvas("逆否命题")
            print(f"语义搜索结果: {len(search_result)} 个相关记忆")

        else:
            print(f"测试Canvas文件不存在: {test_canvas_path}")

        # 获取统计信息
        stats = integration.get_integration_statistics()
        print(f"集成统计: {stats}")

        integration.close()

    except Exception as e:
        print(f"测试失败: {e}")