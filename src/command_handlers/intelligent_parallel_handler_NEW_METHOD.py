"""
Story 10.2.3: _update_canvas_correct_structure() implementation

This file contains the new method to be added to IntelligentParallelCommandHandler
"""

import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _update_canvas_correct_structure(
    self,
    canvas_path: str,
    results: List[Dict[str, Any]],
    options: Dict[str, Any]
) -> None:
    """
    修复后的Canvas更新方法 - 使用正确的3层结构 (Story 10.2.3)

    正确结构:
    Yellow Node (理解节点, color="6")
        ↓ 边1: 带标签 "AI Explanation ({emoji})"
    Blue TEXT Node (说明节点, color="5", type="text")
        ↓ 边2: 无标签
    File Node (文档节点, type="file")

    Args:
        canvas_path: Canvas文件路径
        results: 执行结果列表，每个result包含:
            - success (bool): 是否成功
            - node_id (str): 黄色节点ID
            - doc_path (str): 生成的文档路径
            - node_data (dict): 黄色节点数据（包含x, y, width, height）
            - agent (str): 使用的Agent类型
        options: 选项配置
            - verbose (bool): 是否显示详细错误

    Raises:
        Exception: 如果Canvas保存失败

    Side Effects:
        - 更新 self.stats["created_blue_nodes"] (+2 per successful result)
        - 更新 self.stats["errors"] (如果有错误)

    Example:
        >>> handler = IntelligentParallelCommandHandler()
        >>> results = [{
        ...     "success": True,
        ...     "node_id": "yellow-abc123",
        ...     "doc_path": "/path/to/doc.md",
        ...     "node_data": {"x": 100, "y": 200, "width": 400, "height": 300},
        ...     "agent": "oral-explanation"
        ... }]
        >>> handler._update_canvas_correct_structure(
        ...     "test.canvas", results, {"verbose": False}
        ... )
        # Creates: Yellow → Blue TEXT → File (3-layer structure)
    """
    from canvas_utils import CanvasJSONOperator

    print("\n🔄 更新Canvas文件 (正确的3层结构)...")

    # Step 1: 创建备份
    backup_path = None
    try:
        backup_path = self._create_canvas_backup(canvas_path)
        print(f"   📋 备份创建成功: {backup_path}")
    except Exception as e:
        print(f"   ⚠️ 备份创建失败 (继续执行): {str(e)}")

    # Step 2: 读取Canvas
    try:
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)
    except Exception as e:
        error_msg = f"Canvas读取失败: {str(e)}"
        self.stats["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        raise

    # Step 3: 处理每个成功的结果
    nodes_created = 0
    for result in results:
        if not result.get("success", False):
            continue

        node_id = result["node_id"]
        doc_path = result["doc_path"]
        node_data = result["node_data"]
        agent_type = result["agent"]
        agent_info = self.supported_agents[agent_type]

        try:
            # 3.1 生成唯一ID
            blue_text_node_id = f"ai-text-{node_id}-{uuid.uuid4().hex[:8]}"
            file_node_id = f"ai-file-{node_id}-{uuid.uuid4().hex[:8]}"

            # 3.2 计算节点位置
            # Blue TEXT节点：在黄色节点右侧 300px
            blue_text_x = node_data["x"] + 300
            blue_text_y = node_data["y"]

            # File节点：在Blue TEXT节点右侧 300px
            file_x = blue_text_x + 300
            file_y = blue_text_y

            # 3.3 构建Blue TEXT节点文本内容
            agent_name_cn = {
                "oral-explanation": "口语化解释",
                "clarification-path": "澄清路径",
                "memory-anchor": "记忆锚点",
                "comparison-table": "对比表格",
                "four-level-explanation": "四层次解释",
                "example-teaching": "例题教学"
            }.get(agent_type, "AI解释")

            blue_text_content = f"{agent_info['emoji']} {agent_name_cn}\n\nAgent: {agent_type}\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # 3.4 创建Blue TEXT节点 (AC2)
            CanvasJSONOperator.create_node(
                canvas_data=canvas_data,
                node_type="text",
                x=blue_text_x,
                y=blue_text_y,
                width=250,
                height=150,
                color="5",  # Blue
                text=blue_text_content
            )

            # 手动设置节点ID (create_node生成的ID需要替换)
            canvas_data["nodes"][-1]["id"] = blue_text_node_id

            # 3.5 计算相对路径 (AC3)
            canvas_dir = Path(canvas_path).parent
            doc_abs_path = Path(doc_path).resolve()
            try:
                relative_path = doc_abs_path.relative_to(canvas_dir)
                file_path_str = str(relative_path).replace("\\", "/")
            except ValueError:
                # 如果无法计算相对路径,使用文件名
                file_path_str = doc_abs_path.name

            # 3.6 创建File节点 (AC3)
            CanvasJSONOperator.create_node(
                canvas_data=canvas_data,
                node_type="file",
                x=file_x,
                y=file_y,
                width=350,
                height=200,
                file=file_path_str
            )

            # 手动设置节点ID
            canvas_data["nodes"][-1]["id"] = file_node_id

            # 3.7 创建边1: Yellow → Blue TEXT (AC4)
            CanvasJSONOperator.create_edge(
                canvas_data=canvas_data,
                from_node=node_id,
                to_node=blue_text_node_id,
                from_side="right",
                to_side="left",
                label=f"AI解释 ({agent_info['emoji']})"
            )

            # 手动设置边ID
            edge1_id = f"edge-{node_id}-to-{blue_text_node_id}"
            canvas_data["edges"][-1]["id"] = edge1_id

            # 3.8 创建边2: Blue TEXT → File (AC4, 无标签)
            CanvasJSONOperator.create_edge(
                canvas_data=canvas_data,
                from_node=blue_text_node_id,
                to_node=file_node_id,
                from_side="right",
                to_side="left"
                # 注意: 不传label参数，保持无标签
            )

            # 手动设置边ID
            edge2_id = f"edge-{blue_text_node_id}-to-{file_node_id}"
            canvas_data["edges"][-1]["id"] = edge2_id

            # 3.9 更新统计 (AC6: +2 per result)
            nodes_created += 2
            self.stats["created_blue_nodes"] += 2

            print("   ✅ 创建3层结构:")
            print(f"      Yellow({node_id[:16]}...) → BlueText({blue_text_node_id[:16]}...) → File({file_node_id[:16]}...)")

        except Exception as e:
            error_msg = f"Canvas修改失败 (节点 {node_id}): {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"   ❌ {error_msg}")
            if options.get("verbose", False):
                import traceback
                traceback.print_exc()

            # 发生错误时回滚 (AC5)
            if backup_path and Path(backup_path).exists():
                try:
                    self._rollback_from_backup(canvas_path, backup_path)
                    print("   🔙 已回滚到备份版本")
                except Exception as rollback_error:
                    print(f"   ⚠️ 回滚失败: {str(rollback_error)}")
            raise

    # Step 4: 保存修改后的Canvas
    try:
        CanvasJSONOperator.write_canvas(canvas_path, canvas_data)
        print(f"✅ Canvas文件更新成功: {nodes_created} 个节点 (Blue TEXT + File)")
    except Exception as e:
        error_msg = f"Canvas保存失败: {str(e)}"
        self.stats["errors"].append(error_msg)
        print(f"❌ {error_msg}")

        # 保存失败时回滚 (AC5)
        if backup_path and Path(backup_path).exists():
            try:
                self._rollback_from_backup(canvas_path, backup_path)
                print("   🔙 已回滚到备份版本")
            except Exception as rollback_error:
                print(f"   ⚠️ 回滚失败: {str(rollback_error)}")
        raise


def _create_canvas_backup(self, canvas_path: str) -> str:
    """
    创建Canvas文件备份 (Story 10.2.3 AC5)

    Args:
        canvas_path: Canvas文件路径

    Returns:
        str: 备份文件路径

    Raises:
        IOError: 如果备份失败
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{canvas_path}.backup.{timestamp}"

    try:
        shutil.copy2(canvas_path, backup_path)
        return backup_path
    except Exception as e:
        raise IOError(f"创建备份失败: {str(e)}")


def _rollback_from_backup(self, canvas_path: str, backup_path: str) -> None:
    """
    从备份恢复Canvas文件 (Story 10.2.3 AC5)

    Args:
        canvas_path: Canvas文件路径
        backup_path: 备份文件路径

    Raises:
        IOError: 如果恢复失败
    """
    try:
        shutil.copy2(backup_path, canvas_path)
    except Exception as e:
        raise IOError(f"从备份恢复失败: {str(e)}")
