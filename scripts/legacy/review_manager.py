"""
Canvas复习管理器 - Canvas学习系统v2.0

集成艾宾浩斯复习系统与Canvas白板功能，提供：
- Canvas节点自动创建复习计划
- 复习完成标记和满意度评分
- 批量处理多个Canvas文件
- 与Canvas颜色系统保持一致

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import os
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ebbinghaus_review import EbbinghausReviewScheduler
# 简化导入，避免canvas_utils版本问题
try:
    from canvas_utils import CanvasOrchestrator
except ImportError:
    # 如果导入失败，创建简化版本
    class CanvasOrchestrator:
        def __init__(self, canvas_path):
            self.canvas_path = canvas_path
            self.business_logic = type('CanvasBusinessLogic', (), {
                'canvas_data': {},
                'find_node_by_id': self._find_node_by_id,
                'update_node_color': self._update_node_color
            })()

        def _find_node_by_id(self, node_id):
            """简化版节点查找"""
            # 读取Canvas文件
            if os.path.exists(self.canvas_path):
                try:
                    with open(self.canvas_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    for node in data.get('nodes', []):
                        if node.get('id') == node_id:
                            return node
                except:
                    pass
            return None

        def _update_node_color(self, node_id, color):
            """简化版颜色更新"""
            try:
                with open(self.canvas_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 更新节点颜色
                for node in data.get('nodes', []):
                    if node.get('id') == node_id:
                        node['color'] = color
                        break

                # 写回文件
                with open(self.canvas_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"更新节点颜色失败: {e}")

# 导入常量
try:
    from ebbinghaus_review import COLOR_RED, COLOR_GREEN, COLOR_PURPLE, COLOR_YELLOW
except ImportError:
    # 备用常量定义
    COLOR_RED = "1"
    COLOR_GREEN = "2"
    COLOR_PURPLE = "3"
    COLOR_YELLOW = "6"

class CanvasReviewManager:
    """Canvas复习管理器

    集成Canvas白板操作和艾宾浩斯复习系统，实现：
    - Canvas节点复习计划创建
    - 复习进度可视化
    - 批量Canvas文件处理
    - 复习完成状态同步
    """

    def __init__(self, db_path: str = "data/review_data.db"):
        """初始化复习管理器

        Args:
            db_path: 复习数据库路径
        """
        self.review_scheduler = EbbinghausReviewScheduler(db_path)

    def integrate_review_with_canvas(self, canvas_path: str, node_id: str,
                                  auto_create_schedule: bool = True) -> Dict:
        """将复习功能集成到Canvas节点

        Args:
            canvas_path: Canvas文件路径
            node_id: 需要集成复习功能的节点ID
            auto_create_schedule: 是否自动创建复习计划

        Returns:
            Dict: 集成结果和复习计划信息
        """
        try:
            # 初始化Canvas操作器
            canvas_op = CanvasOrchestrator(canvas_path)

            # 获取节点信息
            canvas_data = canvas_op.business_logic.canvas_data
            node = canvas_op.find_node_by_id(node_id)

            if not node:
                return {
                    "success": False,
                    "error": f"节点不存在: {node_id}",
                    "canvas_path": canvas_path
                }

            # 检查是否已有复习计划
            existing_schedule = None
            schedules = self.review_scheduler.get_all_review_schedules(canvas_path)
            for schedule in schedules:
                if schedule["node_id"] == node_id:
                    existing_schedule = schedule
                    break

            if existing_schedule:
                schedule_id = existing_schedule["schedule_id"]
                next_review = existing_schedule["next_review_date"]
                return {
                    "success": True,
                    "action": "existing_schedule_found",
                    "schedule_id": schedule_id,
                    "node_id": node_id,
                    "concept_name": existing_schedule["concept_name"],
                    "next_review_date": next_review,
                    "canvas_path": canvas_path,
                    "message": f"节点已有复习计划，下次复习: {next_review}"
                }

            # 获取或生成概念名称
            concept_name = node.get("text", "").strip() or f"节点-{node_id[:8]}"
            if len(concept_name) > 50:
                concept_name = concept_name[:47] + "..."

            # 自动创建复习计划
            if auto_create_schedule:
                schedule_id = self.review_scheduler.create_review_schedule(
                    canvas_path=canvas_path,
                    node_id=node_id,
                    concept_name=concept_name
                )

                # 获取创建的复习计划信息
                schedule_info = self.review_scheduler.get_review_schedule(schedule_id)

                # 在Canvas中添加复习状态标记（可选）
                review_status_text = f"📅 复习计划: {schedule_info['next_review_date']}\n💪 强度: {schedule_info['memory_strength']:.1f}"

                return {
                    "success": True,
                    "action": "schedule_created",
                    "schedule_id": schedule_id,
                    "node_id": node_id,
                    "concept_name": concept_name,
                    "next_review_date": schedule_info["next_review_date"],
                    "review_interval_days": schedule_info["review_interval_days"],
                    "memory_strength": schedule_info["memory_strength"],
                    "canvas_path": canvas_path,
                    "review_status_text": review_status_text
                }
            else:
                return {
                    "success": True,
                    "action": "ready_for_schedule",
                    "node_id": node_id,
                    "concept_name": concept_name,
                    "canvas_path": canvas_path,
                    "message": "节点已准备好创建复习计划"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Canvas集成失败: {e}",
                "canvas_path": canvas_path,
                "node_id": node_id
            }

    def create_review_schedules_from_canvas(self, canvas_path: str,
                                         target_colors: List[str] = None) -> List[Dict]:
        """从Canvas文件批量创建复习计划

        Args:
            canvas_path: Canvas文件路径
            target_colors: 目标颜色节点列表，None表示所有节点

        Returns:
            List[Dict]: 创建结果列表
        """
        if target_colors is None:
            # 默认为红色和紫色节点（需要复习的）
            target_colors = [COLOR_RED, COLOR_PURPLE]

        try:
            # 读取Canvas文件
            canvas_op = CanvasOrchestrator(canvas_path)
            canvas_data = canvas_op.business_logic.canvas_data

            # 获取目标颜色节点
            target_nodes = []
            for node in canvas_data.get("nodes", []):
                if (node.get("color") in target_colors and
                    node.get("type") == "text" and
                    node.get("text", "").strip()):

                    target_nodes.append(node)

            results = []
            for node in target_nodes:
                result = self.integrate_review_with_canvas(
                    canvas_path, node["id"], auto_create_schedule=True
                )
                results.append(result)

            success_count = sum(1 for r in results if r.get("success", False))
            total_count = len(results)

            return {
                "canvas_path": canvas_path,
                "total_nodes": total_count,
                "successful_schedules": success_count,
                "results": results,
                "summary": f"从Canvas创建复习计划: {success_count}/{total_count} 成功"
            }

        except Exception as e:
            return [{
                "success": False,
                "error": f"批量创建失败: {e}",
                "canvas_path": canvas_path
            }]

    def complete_canvas_review(self, canvas_path: str, node_id: str, score: int,
                           confidence: int, time_minutes: int, notes: str = None) -> Dict:
        """完成Canvas节点的复习并记录评分

        Args:
            canvas_path: Canvas文件路径
            node_id: Canvas节点ID
            score: 满意度评分 (1-10)
            confidence: 信心评分 (1-10)
            time_minutes: 复习用时
            notes: 复习笔记

        Returns:
            Dict: 完成结果
        """
        try:
            # 获取对应的复习计划
            schedules = self.review_scheduler.get_all_review_schedules(canvas_path)
            target_schedule = None

            for schedule in schedules:
                if schedule["node_id"] == node_id:
                    target_schedule = schedule
                    break

            if not target_schedule:
                return {
                    "success": False,
                    "error": f"未找到节点对应的复习计划: {node_id}",
                    "canvas_path": canvas_path,
                    "node_id": node_id
                }

            # 完成复习记录
            success = self.review_scheduler.complete_review(
                target_schedule["schedule_id"], score, confidence, time_minutes, notes
            )

            if not success:
                return {
                    "success": False,
                    "error": "复习记录失败",
                    "canvas_path": canvas_path,
                    "node_id": node_id,
                    "schedule_id": target_schedule["schedule_id"]
                }

            # 获取更新后的复习计划
            updated_schedule = self.review_scheduler.get_review_schedule(target_schedule["schedule_id"])

            # 根据评分更新Canvas节点颜色
            new_color = self._get_color_by_score(score)
            canvas_op = CanvasOrchestrator(canvas_path)
            canvas_op.update_node_color(node_id, new_color)

            # 计算复习建议
            if updated_schedule:
                next_review = updated_schedule["next_review_date"]
                interval = updated_schedule["review_interval_days"]
                memory_strength = updated_schedule["memory_strength"]
                retention_rate = updated_schedule["retention_rate"]

                suggestions = self._generate_review_suggestions(
                    score, confidence, memory_strength, retention_rate
                )
            else:
                suggestions = "复习计划更新失败"

            return {
                "success": True,
                "action": "review_completed",
                "canvas_path": canvas_path,
                "node_id": node_id,
                "schedule_id": target_schedule["schedule_id"],
                "concept_name": target_schedule["concept_name"],
                "score": score,
                "confidence": confidence,
                "time_minutes": time_minutes,
                "notes": notes,
                "new_color": new_color,
                "next_review_date": next_review,
                "next_interval_days": interval,
                "updated_memory_strength": memory_strength,
                "retention_rate": retention_rate,
                "suggestions": suggestions
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"完成复习失败: {e}",
                "canvas_path": canvas_path,
                "node_id": node_id
            }

    def process_canvas_directory(self, directory_path: str, recursive: bool = True,
                               file_pattern: str = "*.canvas") -> Dict:
        """批量处理目录中的Canvas文件

        Args:
            directory_path: Canvas文件目录路径
            recursive: 是否递归搜索子目录
            file_pattern: 文件匹配模式

        Returns:
            Dict: 批量处理结果统计
        """
        try:
            # 搜索Canvas文件
            search_path = os.path.join(directory_path, "**" if recursive else "", file_pattern)
            canvas_files = glob.glob(search_path, recursive=recursive)

            if not canvas_files:
                return {
                    "success": True,
                    "directory_path": directory_path,
                    "total_files": 0,
                    "processed_files": 0,
                    "message": "目录中未找到Canvas文件"
                }

            results = []
            total_schedules = 0
            successful_schedules = 0

            for canvas_file in canvas_files:
                print(f"处理Canvas文件: {canvas_file}")
                file_result = self.create_review_schedules_from_canvas(canvas_file)

                if isinstance(file_result, list):
                    # 错误情况
                    results.extend(file_result)
                else:
                    # 成功情况
                    results.append(file_result)
                    total_schedules += file_result["total_nodes"]
                    successful_schedules += file_result["successful_schedules"]

            return {
                "success": True,
                "directory_path": directory_path,
                "total_files": len(canvas_files),
                "processed_files": len([r for r in results if r.get("success", False)]),
                "total_schedules_created": total_schedules,
                "successful_schedules": successful_schedules,
                "success_rate": (successful_schedules / total_schedules * 100) if total_schedules > 0 else 0,
                "results": results,
                "summary": f"批量处理完成: {successful_schedules}/{total_schedules} 复习计划创建成功 ({successful_schedules/total_schedules*100:.1f}%)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"批量处理失败: {e}",
                "directory_path": directory_path
            }

    def generate_review_canvas(self, original_canvas: str, due_reviews_only: bool = True,
                            output_path: str = None) -> str:
        """生成复习专用Canvas

        Args:
            original_canvas: 原Canvas文件路径
            due_reviews_only: 是否只包含到期复习的节点
            output_path: 输出文件路径，None则自动生成

        Returns:
            str: 生成的复习Canvas文件路径
        """
        try:
            # 获取复习任务
            if due_reviews_only:
                today_reviews = self.review_scheduler.get_today_reviews()
                target_schedule_ids = {r["schedule_id"] for r in today_reviews}
            else:
                all_schedules = self.review_scheduler.get_all_review_schedules(original_canvas)
                target_schedule_ids = {s["schedule_id"] for s in all_schedules}

            if not target_schedule_ids:
                raise ValueError("没有找到要复习的节点")

            # 读取原Canvas
            canvas_op = CanvasOrchestrator(original_canvas)
            original_data = canvas_op.business_logic.canvas_data

            # 创建复习Canvas结构
            review_canvas = {
                "nodes": [],
                "edges": []
            }

            # 添加标题节点
            title_node = {
                "id": "review-title",
                "type": "text",
                "text": f"📚 复习白板 - {os.path.basename(original_canvas)}",
                "x": 100,
                "y": 50,
                "width": 500,
                "height": 100,
                "color": "5"  # 蓝色
            }
            review_canvas["nodes"].append(title_node)

            # 添加复习任务节点
            y_position = 200
            for i, schedule in enumerate(target_schedule_ids):
                # 这里需要获取实际的schedule对象，简化处理
                review_node = {
                    "id": f"review-task-{i}",
                    "type": "text",
                    "text": f"📋 复习任务 {i+1}\n{schedule}",
                    "x": 100 + (i % 3) * 200,
                    "y": y_position + (i // 3) * 150,
                    "width": 180,
                    "height": 120,
                    "color": COLOR_YELLOW  # 黄色表示需要处理
                }
                review_canvas["nodes"].append(review_node)

            # 生成输出文件路径
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(original_canvas))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"{base_name}-复习白板-{timestamp}.canvas"

            # 写入复习Canvas文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(review_canvas, f, ensure_ascii=False, indent=2)

            return output_path

        except Exception as e:
            raise ValueError(f"生成复习Canvas失败: {e}")

    def _get_color_by_score(self, score: int) -> str:
        """根据评分获取对应的Canvas颜色

        Args:
            score: 复习评分 (1-10)

        Returns:
            str: Canvas颜色代码
        """
        if score >= 8:
            return COLOR_GREEN  # 绿色 - 完全理解
        elif score >= 5:
            return COLOR_PURPLE  # 紫色 - 似懂非懂
        else:
            return COLOR_RED  # 红色 - 不理解

    def _generate_review_suggestions(self, score: int, confidence: int,
                                 memory_strength: float, retention_rate: float) -> str:
        """生成复习建议

        Args:
            score: 满意度评分
            confidence: 信心评分
            memory_strength: 记忆强度
            retention_rate: 记忆保持率

        Returns:
            str: 复习建议文本
        """
        suggestions = []

        if score < 5:
            suggestions.append("💡 建议: 重新学习基础概念")
            suggestions.append("📚 建议: 查看相关学习资料")
        elif score < 8:
            suggestions.append("🔄 建议: 增加练习频率")
            suggestions.append("📝 建议: 制作概念笔记")

        if confidence < 5:
            suggestions.append("🎯 建议: 增强基础理解")
        elif confidence > 8 and score < 7:
            suggestions.append("⚖️ 建议: 调整学习预期")

        if retention_rate < 0.6:
            suggestions.append("⏰ 建议: 缩短复习间隔")
        elif retention_rate > 0.8:
            suggestions.append("📈 建议: 可以适当延长复习间隔")

        if memory_strength < 5:
            suggestions.append("💪 建议: 专注巩固基础")
        elif memory_strength > 30:
            suggestions.append("🚀 建议: 挑战更高级概念")

        return "\n".join(suggestions) if suggestions else "👍 复习效果良好，继续保持！"