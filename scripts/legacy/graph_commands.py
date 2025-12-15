#!/usr/bin/env python3
"""
Graphiti知识图谱命令系统

实现用户接口和命令系统，支持知识图谱记录、搜索和分析功能。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

import click
import yaml
from loguru import logger

from graphiti_integration import GraphitiKnowledgeGraph, GraphitiContextManager
from concept_extractor import extract_and_analyze_canvas


class GraphCommandHandler:
    """Graphiti命令处理器

    负责处理所有/graph相关的命令：
    - 激活知识图谱记录
    - 搜索概念网络
    - 显示图谱统计
    - 生成学习建议
    """

    def __init__(self, config_path: str = "config/graphiti_config.yaml"):
        """初始化命令处理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.current_session_id = None
        self.is_recording = False

    async def start_recording(self, canvas_path: str, user_id: str = "default") -> str:
        """开始记录学习会话

        Args:
            canvas_path: Canvas文件路径
            user_id: 用户ID

        Returns:
            str: 会话ID
        """
        try:
            canvas_file = Path(canvas_path)
            if not canvas_file.exists():
                raise FileNotFoundError(f"Canvas文件不存在: {canvas_path}")

            # 生成会话ID
            import uuid
            self.current_session_id = f"session-{uuid.uuid4().hex[:16]}"
            self.is_recording = True

            # 创建会话数据
            session_data = {
                "session_id": self.current_session_id,
                "canvas_file": canvas_path,
                "session_type": "recording",
                "duration_minutes": 0,
                "start_time": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "nodes_interacted": [],
                "learning_outcomes": {
                    "new_concepts_learned": 0,
                    "concepts_reviewed": 0,
                    "weaknesses_identified": 0,
                    "mastery_improvements": 0
                }
            }

            # 记录会话到知识图谱
            async with GraphitiContextManager(self.config_path) as graphiti:
                recorded_session_id = await graphiti.record_learning_session(session_data)

            logger.info(f"开始记录学习会话: {recorded_session_id}")
            return recorded_session_id

        except Exception as e:
            logger.error(f"开始记录失败: {e}")
            raise

    async def stop_recording(self) -> Dict[str, Any]:
        """停止记录学习会话

        Returns:
            Dict: 会话摘要
        """
        if not self.is_recording or not self.current_session_id:
            raise ValueError("当前没有活跃的录制会话")

        try:
            # 这里可以添加会话结束的逻辑
            session_summary = {
                "session_id": self.current_session_id,
                "status": "completed",
                "end_time": datetime.now(timezone.utc).isoformat(),
                "message": "学习会话录制已完成"
            }

            self.is_recording = False
            self.current_session_id = None

            logger.info("学习会话录制已停止")
            return session_summary

        except Exception as e:
            logger.error(f"停止录制失败: {e}")
            raise

    async def search_concepts(self, query: str, depth: int = 2, user_id: str = "default") -> Dict[str, Any]:
        """搜索概念网络

        Args:
            query: 搜索查询
            depth: 搜索深度
            user_id: 用户ID

        Returns:
            Dict: 搜索结果
        """
        try:
            async with GraphitiContextManager(self.config_path) as graphiti:
                result = await graphiti.search_concept_network(query, depth, user_id)

            # 格式化输出
            search_result = {
                "query": query,
                "center_concept": result["center_concept"],
                "total_concepts": len(result["concepts"]),
                "total_relationships": len(result["relationships"]),
                "concepts": result["concepts"][:10],  # 限制显示数量
                "relationships": result["relationships"][:15],  # 限制显示数量
                "network_stats": result["network_stats"],
                "search_time": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"搜索概念网络完成: {query}, 找到{len(result['concepts'])}个概念")
            return search_result

        except Exception as e:
            logger.error(f"搜索概念失败: {e}")
            raise

    async def get_graph_stats(self, user_id: str = "default") -> Dict[str, Any]:
        """获取知识图谱统计信息

        Args:
            user_id: 用户ID

        Returns:
            Dict: 统计信息
        """
        try:
            async with GraphitiContextManager(self.config_path) as graphiti:
                stats = await graphiti.get_graph_statistics()

            # 格式化统计信息
            formatted_stats = {
                "user_id": user_id,
                "statistics": stats,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_nodes": sum(stats.get("nodes", {}).values()),
                    "total_relationships": stats.get("total_relationships", 0),
                    "concepts_count": stats.get("nodes", {}).get("Concept", 0),
                    "sessions_count": stats.get("learning_sessions", {}).get("total_sessions", 0)
                }
            }

            logger.info("获取图谱统计信息完成")
            return formatted_stats

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise

    async def get_learning_recommendations(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """生成学习建议

        Args:
            user_id: 用户ID

        Returns:
            List[Dict]: 学习建议列表
        """
        try:
            async with GraphitiContextManager(self.config_path) as graphiti:
                recommendations = await graphiti.generate_learning_recommendations(user_id)

            # 格式化建议
            formatted_recommendations = {
                "user_id": user_id,
                "total_recommendations": len(recommendations),
                "recommendations": recommendations[:10],  # 限制显示数量
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "priority_summary": {
                    "high": len([r for r in recommendations if r.get("priority") == "high"]),
                    "medium": len([r for r in recommendations if r.get("priority") == "medium"]),
                    "low": len([r for r in recommendations if r.get("priority") == "low"])
                }
            }

            logger.info(f"生成学习建议完成: {len(recommendations)}条建议")
            return formatted_recommendations

        except Exception as e:
            logger.error(f"生成学习建议失败: {e}")
            raise

    async def analyze_canvas(self, canvas_path: str, user_id: str = "default") -> Dict[str, Any]:
        """分析Canvas文件

        Args:
            canvas_path: Canvas文件路径
            user_id: 用户ID

        Returns:
            Dict: 分析结果
        """
        try:
            # 提取概念和关系
            extraction_result = await extract_and_analyze_canvas(canvas_path)

            # 如果正在录制，则记录到知识图谱
            if self.is_recording and self.current_session_id:
                async with GraphitiContextManager(self.config_path) as graphiti:
                    await graphiti.extract_concept_relationships(canvas_path, self.current_session_id)

            # 格式化分析结果
            analysis_result = {
                "canvas_file": canvas_path,
                "user_id": user_id,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "extraction_summary": extraction_result["extraction_result"]["statistics"],
                "concept_clusters": extraction_result["concept_clusters"],
                "cluster_statistics": extraction_result["cluster_statistics"],
                "recommendations": extraction_result["recommendations"],
                "recording_status": "active" if self.is_recording else "inactive"
            }

            logger.info(f"Canvas分析完成: {canvas_path}")
            return analysis_result

        except Exception as e:
            logger.error(f"Canvas分析失败: {e}")
            raise

    async def identify_weaknesses(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """识别学习薄弱环节

        Args:
            user_id: 用户ID

        Returns:
            List[Dict]: 薄弱环节列表
        """
        try:
            async with GraphitiContextManager(self.config_path) as graphiti:
                weaknesses = await graphiti.identify_weaknesses(user_id)

            # 格式化薄弱环节
            formatted_weaknesses = {
                "user_id": user_id,
                "total_weaknesses": len(weaknesses),
                "weaknesses": weaknesses[:10],  # 限制显示数量
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "severity_summary": {
                    "critical": len([w for w in weaknesses if w.get("weakness_level") == "critical"]),
                    "high": len([w for w in weaknesses if w.get("weakness_level") == "high"]),
                    "medium": len([w for w in weaknesses if w.get("weakness_level") == "medium"]),
                    "low": len([w for w in weaknesses if w.get("weakness_level") == "low"])
                }
            }

            logger.info(f"识别薄弱环节完成: {len(weaknesses)}个薄弱环节")
            return formatted_weaknesses

        except Exception as e:
            logger.error(f"识别薄弱环节失败: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态

        Returns:
            Dict: 状态信息
        """
        return {
            "is_recording": self.is_recording,
            "current_session_id": self.current_session_id,
            "config_path": self.config_path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Click命令行接口
@click.group()
@click.option('--config', default='config/graphiti_config.yaml', help='配置文件路径')
@click.pass_context
def cli(ctx, config):
    """Graphiti知识图谱命令行工具"""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['handler'] = GraphCommandHandler(config)


@cli.command()
@click.argument('canvas_path', type=click.Path(exists=True))
@click.option('--user-id', default='default', help='用户ID')
@click.pass_context
def start(ctx, canvas_path, user_id):
    """开始录制Canvas学习会话"""
    async def _start():
        handler = ctx.obj['handler']
        try:
            session_id = await handler.start_recording(canvas_path, user_id)
            click.echo(f"✅ 开始录制学习会话")
            click.echo(f"   会话ID: {session_id}")
            click.echo(f"   Canvas文件: {canvas_path}")
            click.echo(f"   用户ID: {user_id}")
        except Exception as e:
            click.echo(f"❌ 开始录制失败: {e}", err=True)
            sys.exit(1)

    asyncio.run(_start())


@cli.command()
@click.pass_context
def stop(ctx):
    """停止录制学习会话"""
    async def _stop():
        handler = ctx.obj['handler']
        try:
            summary = await handler.stop_recording()
            click.echo(f"✅ 录制已停止")
            click.echo(f"   会话ID: {summary['session_id']}")
            click.echo(f"   状态: {summary['status']}")
        except Exception as e:
            click.echo(f"❌ 停止录制失败: {e}", err=True)
            sys.exit(1)

    asyncio.run(_stop())


@cli.command()
@click.argument('query')
@click.option('--depth', default=2, help='搜索深度')
@click.option('--user-id', default='default', help='用户ID')
@click.pass_context
def search(ctx, query, depth, user_id):
    """搜索概念网络"""
    async def _search():
        handler = ctx.obj['handler']
        try:
            result = await handler.search_concepts(query, depth, user_id)

            click.echo(f"🔍 搜索结果: '{query}'")
            click.echo(f"   找到概念: {result['total_concepts']} 个")
            click.echo(f"   找到关系: {result['total_relationships']} 个")
            click.echo(f"   中心概念: {result['center_concept']}")

            if result['concepts']:
                click.echo("\n📚 相关概念:")
                for i, concept in enumerate(result['concepts'][:10], 1):
                    click.echo(f"   {i}. {concept}")

            if result['relationships']:
                click.echo("\n🔗 关系:")
                for i, rel in enumerate(result['relationships'][:5], 1):
                    fact = rel.get('fact', str(rel))
                    click.echo(f"   {i}. {fact[:100]}...")

        except Exception as e:
            click.echo(f"❌ 搜索失败: {e}", err=True)
            sys.exit(1)

    asyncio.run(_search())


@cli.command()
@click.option('--user-id', default='default', help='用户ID')
@click.pass_context
def stats(ctx, user_id):
    """显示知识图谱统计信息"""
    async def _stats():
        handler = ctx.obj['handler']
        try:
            result = await handler.get_graph_stats(user_id)

            click.echo("📊 知识图谱统计信息")
            click.echo(f"   用户ID: {result['user_id']}")
            summary = result['summary']
            click.echo(f"   总节点数: {summary['total_nodes']}")
            click.echo(f"   总关系数: {summary['total_relationships']}")
            click.echo(f"   概念数: {summary['concepts_count']}")
            click.echo(f"   学习会话数: {summary['sessions_count']}")

            if result['statistics'].get('nodes'):
                click.echo("\n📋 节点详情:")
                for node_type, count in result['statistics']['nodes'].items():
                    click.echo(f"   {node_type}: {count}")

        except Exception as e:
            click.echo(f"❌ 获取统计信息失败: {e}", err=True)
            sys.exit(1)

    asyncio.run(_stats())


@cli.command()
@click.option('--user-id', default='default', help='用户ID')
@click.pass_context
def recommendations(ctx, user_id):
    """生成学习建议"""
    async def _recommendations():
        handler = ctx.obj['handler']
        try:
            result = await handler.get_learning_recommendations(user_id)

            click.echo("💡 学习建议")
            click.echo(f"   用户ID: {result['user_id']}")
            click.echo(f"   总建议数: {result['total_recommendations']}")

            priority_summary = result['priority_summary']
            click.echo(f"   高优先级: {priority_summary['high']} 条")
            click.echo(f"   中优先级: {priority_summary['medium']} 条")
            click.echo(f"   低优先级: {priority_summary['low']} 条")

            if result['recommendations']:
                click.echo("\n📝 建议:")
                for i, rec in enumerate(result['recommendations'][:5], 1):
                    priority_icon = "🔴" if rec.get('priority') == 'high' else "🟡" if rec.get('priority') == 'medium' else "🟢"
                    click.echo(f"   {i}. {priority_icon} {rec['description']}")
                    click.echo(f"      概念: {rec['concept']}")
                    click.echo(f"      建议: {rec['suggested_action']}")
                    click.echo()

        except Exception as e:
            click.echo(f"❌ 生成建议失败: {e}", err=True)
            sys.exit(1)

    asyncio.run(_recommendations())


@cli.command()
@click.argument('canvas_path', type=click.Path(exists=True))
@click.option('--user-id', default='default', help='用户ID')
@click.pass_context
def analyze(ctx, canvas_path, user_id):
    """分析Canvas文件"""
    async def _analyze():
        handler = ctx.obj['handler']
        try:
            result = await handler.analyze_canvas(canvas_path, user_id)

            click.echo("🔍 Canvas分析结果")
            click.echo(f"   Canvas文件: {result['canvas_file']}")
            click.echo(f"   用户ID: {result['user_id']}")
            click.echo(f"   录制状态: {'活跃' if result['recording_status'] == 'active' else '非活跃'}")

            summary = result['extraction_summary']
            click.echo(f"\n📈 提取统计:")
            click.echo(f"   总概念数: {summary['total_concepts']}")
            click.echo(f"   总关系数: {summary['total_relationships']}")
            click.echo(f"   显式关系: {summary['explicit_relationships']}")
            click.echo(f"   隐式关系: {summary['implicit_relationships']}")

            cluster_stats = result['cluster_statistics']
            click.echo(f"\n🎯 聚类统计:")
            click.echo(f"   聚类数: {cluster_stats['total_clusters']}")
            click.echo(f"   最大聚类: {cluster_stats['largest_cluster_size']} 个概念")
            click.echo(f"   平均聚类大小: {cluster_stats['average_cluster_size']:.1f} 个概念")

            if result['recommendations']:
                click.echo(f"\n💡 建议:")
                for rec in result['recommendations']:
                    click.echo(f"   • {rec}")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)
            sys.exit(1)

    asyncio.run(_analyze())


@cli.command()
@click.option('--user-id', default='default', help='用户ID')
@click.pass_context
def weaknesses(ctx, user_id):
    """识别学习薄弱环节"""
    async def _weaknesses():
        handler = ctx.obj['handler']
        try:
            result = await handler.identify_weaknesses(user_id)

            click.echo("⚠️  学习薄弱环节")
            click.echo(f"   用户ID: {result['user_id']}")
            click.echo(f"   总薄弱环节: {result['total_weaknesses']} 个")

            severity_summary = result['severity_summary']
            click.echo(f"\n📊 严重程度分布:")
            click.echo(f"   严重: {severity_summary['critical']} 个")
            click.echo(f"   高: {severity_summary['high']} 个")
            click.echo(f"   中等: {severity_summary['medium']} 个")
            click.echo(f"   低: {severity_summary['low']} 个")

            if result['weaknesses']:
                click.echo(f"\n🎯 薄弱环节:")
                for i, weakness in enumerate(result['weaknesses'][:5], 1):
                    severity_icon = "🔴" if weakness.get('weakness_level') == 'critical' else "🟠" if weakness.get('weakness_level') == 'high' else "🟡"
                    click.echo(f"   {i}. {severity_icon} {weakness['concept_name']}")
                    click.echo(f"      失败次数: {weakness['failure_count']}")
                    click.echo(f"      建议: {weakness['recommendation']}")
                    click.echo()

        except Exception as e:
            click.echo(f"❌ 识别薄弱环节失败: {e}", err=True)
            sys.exit(1)

    asyncio.run(_weaknesses())


@cli.command()
@click.pass_context
def status(ctx):
    """显示当前状态"""
    handler = ctx.obj['handler']
    try:
        result = handler.get_status()

        click.echo("📋 当前状态")
        click.echo(f"   录制状态: {'活跃' if result['is_recording'] else '非活跃'}")
        if result['current_session_id']:
            click.echo(f"   会话ID: {result['current_session_id']}")
        click.echo(f"   配置文件: {result['config_path']}")
        click.echo(f"   时间戳: {result['timestamp']}")

    except Exception as e:
        click.echo(f"❌ 获取状态失败: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    # 配置日志
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    cli()