"""
MCP语义记忆服务用户接口命令
Canvas Learning System - Story 8.8

提供记忆存储、语义搜索、创意联想等用户命令接口。
"""

import json
import argparse
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# 本地导入
from canvas_mcp_integration import CanvasMCPIntegration
from semantic_processor import SemanticProcessor
from creative_association_engine import CreativeAssociationEngine
from memory_compression import MemoryCompressor
from mcp_memory_client import create_memory_client

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPCommandInterface:
    """MCP命令行接口"""

    def __init__(self, config_path: str = "config/mcp_config.yaml"):
        """初始化命令接口

        Args:
            config_path: MCP配置文件路径
        """
        self.config_path = config_path
        self.integration = None

    def _ensure_integration(self):
        """确保集成已初始化"""
        if self.integration is None:
            self.integration = CanvasMCPIntegration(self.config_path)

    def store_memory_command(self, content: str, metadata: Dict = None) -> Dict:
        """存储语义记忆命令

        Args:
            content: 记忆内容
            metadata: 元数据

        Returns:
            Dict: 存储结果
        """
        try:
            self._ensure_integration()

            # 使用语义处理器处理内容
            semantic_result = self.integration.semantic_processor.process_text(content)

            # 构建完整元数据
            full_metadata = {
                "source": "user_command",
                "content_type": "user_memory",
                "processing_timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            # 添加语义处理结果
            if semantic_result.get("concepts"):
                full_metadata["extracted_concepts"] = semantic_result["concepts"]
            if semantic_result.get("tags"):
                full_metadata["auto_generated_tags"] = [tag["tag"] for tag in semantic_result["tags"]]

            # 存储记忆
            memory_id = self.integration.memory_client.store_semantic_memory(content, full_metadata)

            return {
                "success": True,
                "memory_id": memory_id,
                "concepts_found": len(semantic_result.get("concepts", [])),
                "tags_generated": len(semantic_result.get("tags", [])),
                "message": f"记忆已成功存储，ID: {memory_id}"
            }

        except Exception as e:
            logger.error(f"存储记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "记忆存储失败"
            }

    def search_memory_command(self, query: str, limit: int = 10) -> Dict:
        """语义搜索记忆命令

        Args:
            query: 搜索查询
            limit: 结果数量限制

        Returns:
            Dict: 搜索结果
        """
        try:
            self._ensure_integration()

            # 执行搜索
            results = self.integration.memory_client.search_semantic_memory(query, limit)

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_result = {
                    "memory_id": result["memory_id"],
                    "content_preview": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                    "similarity_score": f"{result['similarity_score']:.3f}",
                    "source_canvas": result.get("metadata", {}).get("source_canvas", "unknown"),
                    "content_type": result.get("metadata", {}).get("content_type", "unknown")
                }
                formatted_results.append(formatted_result)

            return {
                "success": True,
                "query": query,
                "results_count": len(formatted_results),
                "results": formatted_results,
                "message": f"找到 {len(formatted_results)} 个相关记忆"
            }

        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "搜索失败"
            }

    def creative_insights_command(self, concept: str, creativity_level: str = "moderate") -> Dict:
        """创意洞察命令

        Args:
            concept: 核心概念
            creativity_level: 创意级别

        Returns:
            Dict: 创意洞察结果
        """
        try:
            self._ensure_integration()

            # 生成创意联想
            creative_result = self.integration.creative_engine.generate_creative_associations(
                concept, creativity_level
            )

            # 格式化结果
            formatted_result = {
                "concept": concept,
                "creativity_level": creativity_level,
                "overall_creativity_score": f"{creative_result.get('overall_creativity_score', 0):.3f}",
                "insights_count": len(creative_result.get("creative_insights", [])),
                "analogies_count": len(creative_result.get("analogies", [])),
                "learning_paths_count": len(creative_result.get("learning_paths", [])),
                "top_insights": creative_result.get("creative_insights", [])[:3],  # 显示前3个洞察
                "top_analogies": creative_result.get("analogies", [])[:2],  # 显示前2个类比
                "learning_paths": [
                    {
                        "title": path["title"],
                        "duration_hours": path["estimated_duration_hours"],
                        "steps": path["total_steps"]
                    }
                    for path in creative_result.get("learning_paths", [])
                ]
            }

            return {
                "success": True,
                "result": formatted_result,
                "message": f"为概念 '{concept}' 生成了创意洞察"
            }

        except Exception as e:
            logger.error(f"生成创意洞察失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "创意洞察生成失败"
            }

    def integrate_canvas_command(self, canvas_path: str, node_ids: List[str] = None) -> Dict:
        """集成Canvas命令

        Args:
            canvas_path: Canvas文件路径
            node_ids: 指定节点ID列表

        Returns:
            Dict: 集成结果
        """
        try:
            self._ensure_integration()

            # 执行集成
            result = self.integration.integrate_canvas_with_mcp(canvas_path, node_ids)

            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "message": "Canvas集成失败"
                }

            return {
                "success": True,
                "canvas_path": canvas_path,
                "processed_nodes": result["processed_nodes"],
                "memory_ids_created": len(result["memory_ids"]),
                "success_rate": f"{result['integration_summary']['success_rate']:.2%}",
                "message": f"成功集成 {result['processed_nodes']} 个节点"
            }

        except Exception as e:
            logger.error(f"Canvas集成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Canvas集成失败"
            }

    def compress_memories_command(self, threshold: int = 5000, strategy: str = "semantic_clustering") -> Dict:
        """压缩记忆命令

        Args:
            threshold: 压缩阈值
            strategy: 压缩策略

        Returns:
            Dict: 压缩结果
        """
        try:
            self._ensure_integration()

            # 执行自动压缩
            result = self.integration.memory_compressor.auto_compress_memories(threshold, strategy)

            if result.get("compressed", False):
                return {
                    "success": True,
                    "original_count": result["original_count"],
                    "compressed_count": result["compressed_count"],
                    "compression_ratio": f"{result['compression_ratio']:.2%}",
                    "information_retention": f"{result['information_retention']:.2%}",
                    "compression_time": f"{result['compression_time']:.2f}秒",
                    "message": f"记忆压缩完成，压缩比例: {result['compression_ratio']:.2%}"
                }
            else:
                return {
                    "success": True,
                    "compressed": False,
                    "reason": result.get("reason", "未知原因"),
                    "message": "未执行记忆压缩"
                }

        except Exception as e:
            logger.error(f"记忆压缩失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "记忆压缩失败"
            }

    def get_statistics_command(self) -> Dict:
        """获取统计信息命令

        Returns:
            Dict: 统计信息
        """
        try:
            self._ensure_integration()

            # 获取统计信息
            stats = self.integration.get_integration_statistics()

            if "error" in stats:
                return {
                    "success": False,
                    "error": stats["error"],
                    "message": "获取统计信息失败"
                }

            # 格式化统计信息
            memory_stats = stats.get("memory_statistics", {})
            health_stats = stats.get("integration_health", {})

            formatted_stats = {
                "memory_statistics": {
                    "total_memories": memory_stats.get("total_memories", 0),
                    "device": memory_stats.get("device", "unknown"),
                    "model_name": memory_stats.get("model_name", "unknown"),
                    "last_updated": memory_stats.get("last_updated", "unknown")
                },
                "health_status": {
                    "mcp_connection": health_stats.get("mcp_connection", {}).get("status", "unknown"),
                    "semantic_processor": health_stats.get("semantic_processor", {}).get("status", "unknown"),
                    "creative_engine": health_stats.get("creative_engine", {}).get("status", "unknown"),
                    "overall_status": health_stats.get("overall_status", "unknown")
                },
                "timestamp": stats.get("timestamp", datetime.now().isoformat())
            }

            return {
                "success": True,
                "statistics": formatted_stats,
                "message": "统计信息获取成功"
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "获取统计信息失败"
            }

    def batch_integrate_command(self, directory: str, pattern: str = "*.canvas") -> Dict:
        """批量集成命令

        Args:
            directory: Canvas文件目录
            pattern: 文件匹配模式

        Returns:
            Dict: 批量集成结果
        """
        try:
            self._ensure_integration()

            # 执行批量集成
            result = self.integration.batch_integrate_canvases(directory, pattern)

            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "message": "批量集成失败"
                }

            summary = result.get("batch_summary", {})

            return {
                "success": True,
                "directory": directory,
                "pattern": pattern,
                "total_files": result["total_files"],
                "processed_files": result["processed_files"],
                "skipped_files": result["skipped_files"],
                "total_memories_created": summary.get("total_memories_created", 0),
                "success_rate": f"{summary.get('success_rate', 0):.2%}",
                "message": f"批量集成完成: {result['processed_files']}/{result['total_files']} 个文件成功"
            }

        except Exception as e:
            logger.error(f"批量集成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "批量集成失败"
            }


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="MCP语义记忆服务命令行接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 存储记忆
  python mcp_commands.py memory-store "逆否命题是逻辑学中的重要概念"

  # 搜索记忆
  python mcp_commands.py memory-search "逆否命题"

  # 生成创意洞察
  python mcp_commands.py creative-insights "逆否命题" --level creative

  # 集成Canvas
  python mcp_commands.py canvas-integrate "笔记库/离散数学/离散数学.canvas"

  # 压缩记忆
  python mcp_commands.py memory-compress --threshold 3000

  # 获取统计信息
  python mcp_commands.py statistics

  # 批量集成
  python mcp_commands.py batch-integrate "笔记库/" --pattern "*.canvas"
        """
    )

    # 全局参数
    parser.add_argument("--config", default="config/mcp_config.yaml",
                       help="MCP配置文件路径 (默认: config/mcp_config.yaml)")
    parser.add_argument("--format", choices=["json", "table"], default="json",
                       help="输出格式 (默认: json)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出")

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # memory-store 命令
    store_parser = subparsers.add_parser("memory-store", help="存储语义记忆")
    store_parser.add_argument("content", help="记忆内容")
    store_parser.add_argument("--metadata", help="元数据 (JSON格式)")

    # memory-search 命令
    search_parser = subparsers.add_parser("memory-search", help="语义搜索记忆")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("--limit", type=int, default=10, help="结果数量限制 (默认: 10)")

    # creative-insights 命令
    insights_parser = subparsers.add_parser("creative-insights", help="生成创意洞察")
    insights_parser.add_argument("concept", help="核心概念")
    insights_parser.add_argument("--level", choices=["conservative", "moderate", "creative"],
                                default="moderate", help="创意级别 (默认: moderate)")

    # canvas-integrate 命令
    canvas_parser = subparsers.add_parser("canvas-integrate", help="集成Canvas")
    canvas_parser.add_argument("canvas_path", help="Canvas文件路径")
    canvas_parser.add_argument("--nodes", help="指定节点ID (逗号分隔)")

    # memory-compress 命令
    compress_parser = subparsers.add_parser("memory-compress", help="压缩记忆")
    compress_parser.add_argument("--threshold", type=int, default=5000, help="压缩阈值 (默认: 5000)")
    compress_parser.add_argument("--strategy", choices=["semantic_clustering", "frequency_based"],
                                default="semantic_clustering", help="压缩策略 (默认: semantic_clustering)")

    # statistics 命令
    subparsers.add_parser("statistics", help="获取统计信息")

    # batch-integrate 命令
    batch_parser = subparsers.add_parser("batch-integrate", help="批量集成Canvas")
    batch_parser.add_argument("directory", help="Canvas文件目录")
    batch_parser.add_argument("--pattern", default="*.canvas", help="文件匹配模式 (默认: *.canvas)")

    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 初始化命令接口
    try:
        cmd_interface = MCPCommandInterface(args.config)
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

    # 执行命令
    try:
        result = None

        if args.command == "memory-store":
            metadata = json.loads(args.metadata) if args.metadata else {}
            result = cmd_interface.store_memory_command(args.content, metadata)

        elif args.command == "memory-search":
            result = cmd_interface.search_memory_command(args.query, args.limit)

        elif args.command == "creative-insights":
            result = cmd_interface.creative_insights_command(args.concept, args.level)

        elif args.command == "canvas-integrate":
            node_ids = args.nodes.split(",") if args.nodes else None
            result = cmd_interface.integrate_canvas_command(args.canvas_path, node_ids)

        elif args.command == "memory-compress":
            result = cmd_interface.compress_memories_command(args.threshold, args.strategy)

        elif args.command == "statistics":
            result = cmd_interface.get_statistics_command()

        elif args.command == "batch-integrate":
            result = cmd_interface.batch_integrate_command(args.directory, args.pattern)

        # 输出结果
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:  # table format
            output_table_format(result)

    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"命令执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理资源
        if cmd_interface.integration:
            cmd_interface.integration.close()


def output_table_format(result: Dict):
    """表格格式输出"""
    if not result.get("success", False):
        print(f"❌ 错误: {result.get('message', '未知错误')}")
        if "error" in result:
            print(f"   详情: {result['error']}")
        return

    print(f"✅ {result.get('message', '操作成功')}")

    # 根据结果类型输出具体信息
    if "memory_id" in result:
        print(f"   记忆ID: {result['memory_id']}")
        print(f"   概念数: {result.get('concepts_found', 0)}")
        print(f"   标签数: {result.get('tags_generated', 0)}")

    elif "results_count" in result:
        print(f"   查询: {result.get('query', '')}")
        print(f"   结果数: {result['results_count']}")
        for i, res in enumerate(result.get("results", [])[:5], 1):
            print(f"   {i}. [{res['similarity_score']}] {res['content_preview'][:80]}...")

    elif "result" in result:
        res = result["result"]
        print(f"   概念: {res.get('concept', '')}")
        print(f"   创意分数: {res.get('overall_creativity_score', '')}")
        print(f"   洞察数: {res.get('insights_count', 0)}")
        print(f"   类比数: {res.get('analogies_count', 0)}")

    elif "processed_nodes" in result:
        print(f"   处理节点: {result.get('processed_nodes', 0)}")
        print(f"   创建记忆: {result.get('memory_ids_created', 0)}")
        print(f"   成功率: {result.get('success_rate', '')}")

    elif "compressed" in result and result["compressed"]:
        print(f"   原始数量: {result.get('original_count', 0)}")
        print(f"   压缩后: {result.get('compressed_count', 0)}")
        print(f"   压缩比例: {result.get('compression_ratio', '')}")
        print(f"   信息保留: {result.get('information_retention', '')}")

    elif "statistics" in result:
        stats = result["statistics"]
        mem_stats = stats.get("memory_statistics", {})
        print(f"   总记忆数: {mem_stats.get('total_memories', 0)}")
        print(f"   设备: {mem_stats.get('device', '')}")
        print(f"   模型: {mem_stats.get('model_name', '')}")

        health = stats.get("health_status", {})
        print(f"   整体状态: {health.get('overall_status', '')}")


if __name__ == "__main__":
    main()