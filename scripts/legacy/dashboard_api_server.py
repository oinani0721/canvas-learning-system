#!/usr/bin/env python3
"""
Canvas学习进度仪表板 API服务器

提供RESTful API接口，用于学习进度数据的查询和可视化。
对应Task 5-7实现的前端界面集成。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-19
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging

# 导入我们的Canvas工具
try:
    from canvas_utils import KnowledgeGraphLayer
    CANVAS_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入canvas_utils: {e}")
    CANVAS_UTILS_AVAILABLE = False

# 导入Canvas数据读取器
try:
    from canvas_data_reader import CanvasDataReader
    CANVAS_READER_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入canvas_data_reader: {e}")
    CANVAS_READER_AVAILABLE = False

# 导入Graphiti时间线读取器
try:
    from graphiti_timeline_reader import GraphitiTimelineReader, get_graphiti_reader
    GRAPHITI_READER_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入graphiti_timeline_reader: {e}")
    GRAPHITI_READER_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 全局变量
kg_layer = None
canvas_reader = None
graphiti_reader = None

async def initialize_knowledge_graph():
    """初始化知识图谱层、Canvas数据读取器和Graphiti时间线读取器"""
    global kg_layer, canvas_reader, graphiti_reader

    if CANVAS_UTILS_AVAILABLE:
        try:
            kg_layer = KnowledgeGraphLayer()
            logger.info("知识图谱层初始化成功")
        except Exception as e:
            logger.error(f"知识图谱层初始化失败: {e}")
            kg_layer = None
    else:
        logger.warning("Canvas工具不可用，将使用模拟数据")
        kg_layer = None

    if CANVAS_READER_AVAILABLE:
        try:
            canvas_reader = CanvasDataReader()
            logger.info("Canvas数据读取器初始化成功")
        except Exception as e:
            logger.error(f"Canvas数据读取器初始化失败: {e}")
            canvas_reader = None
    else:
        logger.warning("Canvas数据读取器不可用，将使用模拟数据")
        canvas_reader = None

    if GRAPHITI_READER_AVAILABLE:
        try:
            graphiti_reader = GraphitiTimelineReader()
            await graphiti_reader.initialize()
            logger.info("Graphiti时间线读取器初始化成功")
        except Exception as e:
            logger.error(f"Graphiti时间线读取器初始化失败: {e}")
            graphiti_reader = None
    else:
        logger.warning("Graphiti时间线读取器不可用，将使用模拟数据")
        graphiti_reader = None

async def get_graphiti_dashboard_data(user_id: str, canvas_id: str) -> Dict[str, Any]:
    """从Graphiti获取基于真实学习时间的仪表板数据"""

    if not graphiti_reader or not graphiti_reader.initialized:
        logger.warning("Graphiti时间线读取器未初始化，回退到Canvas文件数据")
        return get_real_canvas_dashboard_data(user_id, canvas_id)

    try:
        # 从Graphiti获取真实的时间线数据
        timeline_data = await graphiti_reader.get_real_timeline_data(user_id, canvas_id)

        if not timeline_data.get("success"):
            logger.warning(f"从Graphiti获取时间线失败: {timeline_data.get('error', '未知错误')}")
            return get_real_canvas_dashboard_data(user_id, canvas_id)

        # 基于真实时间线数据生成仪表板
        dashboard_data = graphiti_reader.generate_dashboard_data_from_graphiti(
            user_id, canvas_id, timeline_data
        )

        if "error" in dashboard_data:
            logger.error(f"从Graphiti生成仪表板失败: {dashboard_data['error']}")
            return get_real_canvas_dashboard_data(user_id, canvas_id)

        logger.info("✅ 成功从Graphiti获取真实学习时间数据")
        return dashboard_data

    except Exception as e:
        logger.error(f"获取Graphiti数据失败: {e}")
        return get_real_canvas_dashboard_data(user_id, canvas_id)

def get_real_canvas_dashboard_data(user_id: str, canvas_id: str) -> Dict[str, Any]:
    """获取基于真实Canvas文件的仪表板数据（回退方案）"""

    if not canvas_reader:
        logger.warning("Canvas数据读取器不可用，回退到模拟数据")
        return get_fallback_dashboard_data(user_id, canvas_id)

    try:
        # 尝试从真实的Canvas文件获取数据
        # 首先列出了可用的Canvas文件
        available_canvases = canvas_reader.list_available_canvases()

        if not available_canvases:
            logger.warning("未找到Canvas文件，使用模拟数据")
            return get_fallback_dashboard_data(user_id, canvas_id)

        # 使用第一个可用的Canvas文件，或者根据canvas_id匹配
        selected_canvas = None
        for canvas_file in available_canvases:
            if canvas_id in canvas_file or canvas_id == "default":
                selected_canvas = canvas_file
                break

        if not selected_canvas:
            selected_canvas = available_canvases[0]
            logger.info(f"未找到匹配的Canvas文件，使用: {selected_canvas}")

        # 读取和分析Canvas数据
        dashboard_data = canvas_reader.get_canvas_dashboard_data(selected_canvas)

        if "error" in dashboard_data:
            logger.error(f"读取Canvas数据失败: {dashboard_data['error']}")
            return get_fallback_dashboard_data(user_id, canvas_id)

        logger.info(f"成功从Canvas文件读取数据: {selected_canvas}")
        return dashboard_data

    except Exception as e:
        logger.error(f"获取真实Canvas数据失败: {e}")
        return get_fallback_dashboard_data(user_id, canvas_id)

def get_fallback_dashboard_data(user_id: str, canvas_id: str) -> Dict[str, Any]:
    """获取模拟的仪表板数据（作为回退方案）"""

    # 生成模拟的时间线数据
    today = datetime.now()
    daily_data = []

    for i in range(30):
        date = today - timedelta(days=i)
        # 模拟学习活动（周末活动较少）
        is_weekend = date.weekday() >= 5
        has_activity = not is_weekend or (i % 3 == 0)  # 周末偶尔有活动

        if has_activity:
            session_count = min(3, max(0, int((5 - date.weekday()) * 0.8 + 1)))
            total_duration = session_count * (20 + int(date.weekday() * 5))
            mastery_changes = max(0, session_count - 1) if i % 4 == 0 else 0
        else:
            session_count = 0
            total_duration = 0
            mastery_changes = 0

        daily_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "session_count": session_count,
            "total_duration": total_duration,
            "mastery_changes": mastery_changes
        })

    # 生成模拟的热力图数据
    heatmap_data = []
    for weekday in range(7):
        for hour in range(24):
            # 模拟活跃度：工作日9-18点较高
            base_activity = 0
            if weekday < 5:  # 工作日
                if 9 <= hour <= 18:
                    base_activity = 0.8
                elif 19 <= hour <= 22:
                    base_activity = 0.5
            else:  # 周末
                if 10 <= hour <= 16:
                    base_activity = 0.4

            activity = int(base_activity * (60 + (hour % 3) * 20))
            intensity = min(activity / 30, 10)

            heatmap_data.append({
                "weekday": weekday,
                "hour": hour,
                "activity": activity,
                "intensity": intensity
            })

    return {
        "overview": {
            "total_nodes": 42,
            "mastered_nodes": 28,
            "mastery_rate": 66.7,
            "color_distribution": {
                "1": 5,  # 不理解
                "2": 28, # 完全理解
                "3": 6,  # 似懂非懂
                "4": 1,  # 困难
                "5": 2,  # AI解释
                "6": 0   # 个人理解
            },
            "recent_sessions": 12,
            "total_study_time": 480,
            "last_activity": today.isoformat()
        },
        "timeline_chart": {
            "period": "30天",
            "daily_data": daily_data,
            "total_sessions": sum(d["session_count"] for d in daily_data),
            "total_mastery_changes": sum(d["mastery_changes"] for d in daily_data)
        },
        "mastery_distribution": {
            "colors": [
                {"code": "1", "name": "不理解", "color": "#ff4444", "count": 5, "percentage": 11.9},
                {"code": "2", "name": "完全理解", "color": "#44ff44", "count": 28, "percentage": 66.7},
                {"code": "3", "name": "似懂非懂", "color": "#ff44ff", "count": 6, "percentage": 14.3},
                {"code": "4", "name": "困难", "color": "#ff6666", "count": 1, "percentage": 2.4},
                {"code": "5", "name": "AI解释", "color": "#4444ff", "count": 2, "percentage": 4.7}
            ],
            "total_nodes": 42,
            "mastered_percentage": 66.7
        },
        "activity_heatmap": {
            "period": "90天",
            "heatmap_data": heatmap_data,
            "peak_hour": 14,
            "peak_weekday": 2
        },
        "efficiency_analysis": {
            "overall_efficiency": 78.5,
            "time_efficiency": 85.0,
            "frequency_efficiency": 72.0,
            "mastery_efficiency": 78.5,
            "recommendations": [
                "建议增加学习频率，每周至少学习5次",
                "学习效率很高，继续保持当前学习节奏",
                "可以尝试在上午时段学习，可能效果更好",
                "重点关注似懂非懂的知识点，加强练习"
            ]
        },
        "generated_at": today.isoformat(),
        "data_source": "simulated"
    }

@app.route('/')
def index():
    """返回主页"""
    return send_from_directory('.', 'learning_progress_dashboard.html')

@app.route('/api/dashboard/<user_id>/<canvas_id>')
async def get_dashboard(user_id: str, canvas_id: str):
    """获取学习进度仪表板数据"""

    try:
        logger.info(f"获取仪表板数据: user_id={user_id}, canvas_id={canvas_id}")

        # 新的数据源优先级：Graphiti > Canvas文件 > KnowledgeGraphLayer > 模拟数据
        if graphiti_reader and graphiti_reader.initialized:
            # 优先使用Graphiti真实学习时间数据
            dashboard_data = await get_graphiti_dashboard_data(user_id, canvas_id)
            logger.info("使用Graphiti真实学习时间数据返回仪表板")
        elif canvas_reader:
            # 使用真实Canvas文件数据
            dashboard_data = get_real_canvas_dashboard_data(user_id, canvas_id)
            logger.info("使用真实Canvas文件数据返回仪表板")
        elif kg_layer and kg_layer.enabled:
            # 使用知识图谱数据
            try:
                dashboard_data = await kg_layer.get_progress_dashboard(user_id, canvas_id)
                logger.info("使用知识图谱数据返回仪表板")
            except Exception as e:
                logger.error(f"知识图谱获取数据失败: {e}")
                dashboard_data = get_fallback_dashboard_data(user_id, canvas_id)
                logger.info("回退到模拟数据")
        else:
            # 使用模拟数据作为最后回退
            dashboard_data = get_fallback_dashboard_data(user_id, canvas_id)
            logger.info("使用模拟数据返回仪表板")

        return jsonify({
            "success": True,
            "data": dashboard_data
        })

    except Exception as e:
        logger.error(f"获取仪表板数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/viewer/<user_id>/<canvas_id>')
async def get_viewer(user_id: str, canvas_id: str):
    """获取交互式进度查看器数据"""

    try:
        logger.info(f"获取交互式查看器数据: user_id={user_id}, canvas_id={canvas_id}")

        if kg_layer and kg_layer.enabled:
            viewer_data = await kg_layer.get_interactive_progress_viewer(user_id, canvas_id)
        else:
            # 使用模拟数据构建查看器数据
            dashboard_data = get_fallback_dashboard_data(user_id, canvas_id)
            viewer_data = {
                "navigation": {
                    "current_view": "overview",
                    "available_views": ["overview", "timeline", "nodes", "patterns", "recommendations"]
                },
                "dashboard": dashboard_data,
                "filters": {
                    "time_range": {
                        "options": ["7天", "30天", "90天", "全部"],
                        "selected": "30天"
                    },
                    "node_types": {
                        "options": ["全部", "不理解", "似懂非懂", "完全理解"],
                        "selected": "全部"
                    },
                    "session_types": {
                        "options": ["全部", "学习", "复习", "探索"],
                        "selected": "全部"
                    }
                },
                "actions": [
                    {"id": "refresh_data", "label": "刷新数据", "action": "refresh"},
                    {"id": "export_data", "label": "导出数据", "action": "export"},
                    {"id": "generate_report", "label": "生成报告", "action": "report"}
                ]
            }
            logger.info("使用模拟数据返回查看器")

        return jsonify({
            "success": True,
            "data": viewer_data
        })

    except Exception as e:
        logger.error(f"获取查看器数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/query/progress/<user_id>/<canvas_id>')
async def query_progress(user_id: str, canvas_id: str):
    """学习进度查询API"""

    try:
        query_type = request.args.get('type', 'overview')
        time_range = request.args.get('time_range', '30days')

        logger.info(f"查询学习进度: user_id={user_id}, canvas_id={canvas_id}, type={query_type}")

        if kg_layer and kg_layer.enabled:
            result = await kg_layer.get_learning_progress_query(
                user_id, canvas_id, query_type, time_range
            )
        else:
            # 使用模拟数据
            dashboard_data = get_fallback_dashboard_data(user_id, canvas_id)

            if query_type == "overview":
                result = {"type": "overview", "data": dashboard_data}
            elif query_type == "timeline":
                result = {"type": "timeline", "data": dashboard_data["timeline_chart"]}
            elif query_type == "patterns":
                result = {"type": "patterns", "data": {"efficiency": dashboard_data["efficiency_analysis"]}}
            else:
                result = {"error": f"不支持的查询类型: {query_type}"}

            result["query_info"] = {
                "query_type": query_type,
                "time_range": time_range,
                "query_time_ms": 150,
                "cache_used": False
            }

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"查询学习进度失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/timeline/<user_id>/<canvas_id>')
async def get_timeline(user_id: str, canvas_id: str):
    """获取学习时间线数据"""

    try:
        granularity = request.args.get('granularity', 'daily')
        include_events = request.args.get('include_events', 'true').lower() == 'true'

        logger.info(f"获取时间线: user_id={user_id}, canvas_id={canvas_id}, granularity={granularity}")

        if kg_layer and kg_layer.enabled:
            result = await kg_layer.get_learning_timeline_query(
                user_id, canvas_id, granularity=granularity, include_events=include_events
            )
        else:
            # 使用模拟数据
            dashboard_data = get_fallback_dashboard_data(user_id, canvas_id)
            timeline_data = dashboard_data["timeline_chart"]

            # 根据粒度聚合数据
            if granularity == "daily":
                aggregated_data = {"aggregation": "daily", "data": timeline_data["daily_data"]}
            elif granularity == "weekly":
                # 简单的周聚合
                weekly_data = {}
                for day_data in timeline_data["daily_data"]:
                    date = datetime.strptime(day_data["date"], "%Y-%m-%d")
                    week_key = f"{date.year}-W{date.isocalendar()[1]:02d}"

                    if week_key not in weekly_data:
                        weekly_data[week_key] = {"sessions": 0, "duration": 0}

                    weekly_data[week_key]["sessions"] += day_data["session_count"]
                    weekly_data[week_key]["duration"] += day_data["total_duration"]

                aggregated_data = {"aggregation": "weekly", "data": weekly_data}
            else:
                aggregated_data = {"aggregation": granularity, "data": {}}

            result = {
                "timeline": aggregated_data,
                "granularity": granularity,
                "period": {
                    "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "total_days": 30
                },
                "summary": {
                    "total_sessions": timeline_data["total_sessions"],
                    "total_events": timeline_data["total_mastery_changes"] if include_events else 0,
                    "total_duration": sum(d["total_duration"] for d in timeline_data["daily_data"]),
                    "active_days": len([d for d in timeline_data["daily_data"] if d["session_count"] > 0])
                }
            }

            result["query_info"] = {
                "query_time_ms": 120,
                "cache_used": False
            }

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"获取时间线失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/recommendations/<user_id>/<canvas_id>')
async def get_recommendations(user_id: str, canvas_id: str):
    """获取学习建议"""

    try:
        recommendation_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 10))

        logger.info(f"获取学习建议: user_id={user_id}, canvas_id={canvas_id}, type={recommendation_type}")

        if kg_layer and kg_layer.enabled:
            result = await kg_layer.get_learning_recommendations_query(
                user_id, canvas_id, recommendation_type, limit
            )
        else:
            # 使用模拟数据
            dashboard_data = get_fallback_dashboard_data(user_id, canvas_id)
            all_recommendations = dashboard_data["efficiency_analysis"]["recommendations"]

            # 添加类型标签
            typed_recommendations = [
                {"type": "time_management", "priority": "high", "title": "优化学习时间", "description": rec, "action_items": [rec]}
                for i, rec in enumerate(all_recommendations[:2])
            ] + [
                {"type": "content_learning", "priority": "medium", "title": "加强内容学习", "description": rec, "action_items": [rec]}
                for i, rec in enumerate(all_recommendations[2:])
            ]

            # 根据类型过滤
            if recommendation_type != "all":
                filtered_recommendations = [r for r in typed_recommendations if r["type"] == recommendation_type]
            else:
                filtered_recommendations = typed_recommendations

            # 限制数量
            limited_recommendations = filtered_recommendations[:limit]

            result = {
                "recommendations": limited_recommendations,
                "metadata": {
                    "total_recommendations": len(typed_recommendations),
                    "filtered_count": len(filtered_recommendations),
                    "returned_count": len(limited_recommendations),
                    "recommendation_type": recommendation_type,
                    "limit": limit
                },
                "query_info": {
                    "query_time_ms": 80,
                    "cache_used": False
                }
            }

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"获取学习建议失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/export/<user_id>/<canvas_id>')
async def export_data(user_id: str, canvas_id: str):
    """导出学习数据"""

    try:
        export_format = request.args.get('format', 'json')
        include_analytics = request.args.get('include_analytics', 'true').lower() == 'true'

        logger.info(f"导出数据: user_id={user_id}, canvas_id={canvas_id}, format={export_format}")

        if kg_layer and kg_layer.enabled:
            result = await kg_layer.export_learning_data_comprehensive(
                user_id, canvas_id, export_format, include_analytics
            )
        else:
            # 使用模拟数据
            dashboard_data = get_fallback_dashboard_data(user_id, canvas_id)

            export_data = {
                "export_metadata": {
                    "user_id": user_id,
                    "canvas_id": canvas_id,
                    "export_date": datetime.now().isoformat(),
                    "export_format": export_format,
                    "version": "1.0",
                    "data_range": "30天"
                },
                "learning_progress": dashboard_data,
                "summary": {
                    "total_sessions": 12,
                    "total_events": 8,
                    "total_study_hours": 8.0,
                    "mastery_rate": 66.7
                }
            }

            if export_format == "json":
                result = {
                    "data": export_data,
                    "filename": f"learning_data_{canvas_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "mime_type": "application/json"
                }
            else:
                result = {"error": f"模拟数据不支持{export_format}格式"}

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"导出数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "canvas_utils_available": CANVAS_UTILS_AVAILABLE,
        "canvas_reader_available": CANVAS_READER_AVAILABLE,
        "graphiti_reader_available": GRAPHITI_READER_AVAILABLE,
        "graphiti_reader_initialized": graphiti_reader.initialized if graphiti_reader else False,
        "knowledge_graph_enabled": kg_layer.enabled if kg_layer else False,
        "data_source_priority": [
            "graphiti_real_time" if (graphiti_reader and graphiti_reader.initialized) else None,
            "real_canvas_files" if canvas_reader else None,
            "knowledge_graph" if (kg_layer and kg_layer.enabled) else None,
            "simulated"
        ]
    })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "success": False,
        "error": "API端点不存在"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"服务器内部错误: {error}")
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500

def main():
    """主函数"""
    print("=" * 60)
    print("Canvas学习进度仪表板 API服务器")
    print("=" * 60)

    # 初始化知识图谱
    print("正在初始化知识图谱层...")
    asyncio.run(initialize_knowledge_graph())

    print("服务器配置:")
    print(f"  - 主页: http://localhost:5000")
    print(f"  - API文档: http://localhost:5000/api/health")
    print(f"  - Canvas工具可用: {CANVAS_UTILS_AVAILABLE}")
    print(f"  - Canvas数据读取器可用: {CANVAS_READER_AVAILABLE}")
    print(f"  - Graphiti时间线读取器可用: {GRAPHITI_READER_AVAILABLE}")
    print(f"  - Graphiti初始化状态: {graphiti_reader.initialized if graphiti_reader else False}")
    print(f"  - 知识图谱启用: {kg_layer.enabled if kg_layer else False}")

    # 显示当前使用的数据源
    if graphiti_reader and graphiti_reader.initialized:
        data_source = "Graphiti真实学习时间"
    elif canvas_reader:
        data_source = "真实Canvas文件"
    elif kg_layer and kg_layer.enabled:
        data_source = "知识图谱数据"
    else:
        data_source = "模拟数据"

    print(f"  - 数据源: {data_source}")
    print()

    print("可用API端点:")
    print("  - GET /api/dashboard/<user_id>/<canvas_id> - 获取仪表板数据")
    print("  - GET /api/viewer/<user_id>/<canvas_id> - 获取交互式查看器")
    print("  - GET /api/query/progress/<user_id>/<canvas_id> - 查询学习进度")
    print("  - GET /api/timeline/<user_id>/<canvas_id> - 获取时间线数据")
    print("  - GET /api/recommendations/<user_id>/<canvas_id> - 获取学习建议")
    print("  - GET /api/export/<user_id>/<canvas_id> - 导出数据")
    print("  - GET /api/health - 健康检查")
    print()

    print("启动服务器...")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)

    # 启动Flask服务器
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    main()