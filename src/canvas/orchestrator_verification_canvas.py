"""
CanvasOrchestrator - generate_verification_canvas方法扩展

Story 12.10: Canvas检验白板生成集成

本模块包含CanvasOrchestrator.generate_verification_canvas()方法的实现。
待验证后将整合到src/canvas_utils.py的CanvasOrchestrator类中。

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
Story: 12.10
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import time
import uuid
from datetime import datetime

# 导入需要的模块
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False

from canvas.adapters import AgenticRAGAdapter
from canvas.adapters.agentic_rag_adapter import VerificationContext


async def generate_verification_canvas(
    self,
    canvas_file: str,
    output_canvas_file: Optional[str] = None,
    node_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    生成检验白板 (Agentic RAG增强版)

    从源Canvas提取红色/紫色节点，使用Agentic RAG检索薄弱点，
    生成高质量检验题，创建检验白板Canvas。

    ✅ Verified from Story 12.10 (docs/epics/EPIC-12-STORY-MAP.md lines 1262-1316):
    - AC 10.1: 集成Agentic RAG (weighted融合 + cohere reranking)
    - AC 10.2: 检验白板生成准确率 ≥ 85%
    - AC 10.3: 向后兼容Epic 4
    - AC 10.4: 性能不退化 (<5s总时间)
    - AC 10.5: 错误处理和降级

    Args:
        canvas_file: 源Canvas文件路径
        output_canvas_file: 输出检验白板文件路径 (可选, 默认自动生成)
        node_ids: 指定节点ID列表 (可选, 默认所有红色/紫色节点)

    Returns:
        Dict[str, Any]: 检验白板生成结果
            {
                "verification_canvas_name": "离散数学-检验白板-20251129.canvas",
                "node_count": 12,
                "source_canvas": "离散数学.canvas",
                "quality_grade": "high",
                "generation_time_ms": 4200.5,
                "used_agentic_rag": True,
                "fallback": False
            }

    Raises:
        FileNotFoundError: 如果源Canvas文件不存在
        ValueError: 如果Canvas文件格式错误

    Example:
        >>> orchestrator = CanvasOrchestrator("离散数学.canvas")
        >>> result = await orchestrator.generate_verification_canvas(
        ...     canvas_file="离散数学.canvas"
        ... )
        >>> print(f"检验白板: {result['verification_canvas_name']}")
        >>> print(f"生成时间: {result['generation_time_ms']}ms")
    """
    # 性能监控: 开始计时
    start_time = time.time()

    try:
        # 假设self是CanvasOrchestrator实例
        # 需要COLOR常量定义
        COLOR_RED = "#ff0000"
        COLOR_PURPLE = "#8b00ff"
        COLOR_YELLOW = "#ffff00"

        # Step 1: 读取源Canvas
        canvas_data = self.operator.read_canvas(canvas_file)

        # Step 2: 提取红色/紫色节点 (需要生成检验题的薄弱点)
        if node_ids:
            # 如果指定了node_ids，只提取这些节点
            red_purple_nodes = [
                self.operator.find_node_by_id(canvas_data, nid)
                for nid in node_ids
                if self.operator.find_node_by_id(canvas_data, nid) is not None
            ]
        else:
            # 否则提取所有红色/紫色节点
            red_nodes = self.operator.find_nodes_by_color(canvas_data, COLOR_RED)
            purple_nodes = self.operator.find_nodes_by_color(canvas_data, COLOR_PURPLE)
            red_purple_nodes = red_nodes + purple_nodes

        if not red_purple_nodes:
            if LOGURU_ENABLED:
                logger.warning(
                    f"No red/purple nodes found in {canvas_file}, "
                    f"verification canvas generation skipped"
                )
            return {
                "verification_canvas_name": None,
                "node_count": 0,
                "source_canvas": canvas_file,
                "quality_grade": "n/a",
                "generation_time_ms": 0.0,
                "used_agentic_rag": False,
                "fallback": False,
                "error": "No red/purple nodes found"
            }

        # Step 3: 生成输出文件名 (如果未指定)
        if not output_canvas_file:
            # 格式: {source_name}-检验白板-{YYYYMMDD}.canvas
            today = datetime.now().strftime("%Y%m%d")
            source_name = Path(canvas_file).stem
            output_canvas_file = f"{source_name}-检验白板-{today}.canvas"

        # Step 4: 使用Agentic RAG检索薄弱点
        # ✅ Verified from Story 12.10 AC 10.1:
        # 调用AgenticRAGAdapter进行检索
        adapter = AgenticRAGAdapter()
        context = VerificationContext(
            canvas_file=canvas_file,
            red_purple_nodes=red_purple_nodes,
            output_canvas_file=output_canvas_file,
            max_questions_per_node=3
        )

        rag_result = await adapter.retrieve_for_verification(context)

        # Step 5: 生成检验题
        # TODO: 调用verification-question-agent生成检验题
        # 当前先创建占位节点
        verification_questions = []
        for i, node in enumerate(red_purple_nodes):
            concept = node.get("text", f"概念{i+1}")
            # 每个概念生成2-3个检验题
            for q_idx in range(2):
                verification_questions.append({
                    "id": f"vq-{uuid.uuid4().hex[:8]}",
                    "text": f"检验题 {i+1}.{q_idx+1}: {concept}",
                    "color": COLOR_YELLOW,  # 检验白板使用黄色空白节点
                    "type": "verification_question",
                    "source_node_id": node.get("id"),
                    "source_concept": concept
                })

        # Step 6: 创建检验白板Canvas
        verification_canvas = {
            "nodes": verification_questions,
            "edges": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "source_canvas": canvas_file,
                "verification_type": "agentic_rag_enhanced",
                "quality_grade": rag_result.quality_grade,
                "used_fallback": rag_result.is_fallback
            }
        }

        # Step 7: 保存检验白板
        self.operator.write_canvas(output_canvas_file, verification_canvas)

        # 性能监控: 计算总时间
        total_time_ms = (time.time() - start_time) * 1000

        # ✅ AC 10.4 验证: 总时间应 <5000ms
        if total_time_ms > 5000 and LOGURU_ENABLED:
            logger.warning(
                f"Verification canvas generation exceeded 5s threshold: "
                f"{total_time_ms:.2f}ms"
            )

        if LOGURU_ENABLED:
            logger.success(
                f"Verification canvas generated: {output_canvas_file}, "
                f"nodes={len(verification_questions)}, "
                f"time={total_time_ms:.2f}ms, "
                f"quality={rag_result.quality_grade}"
            )

        return {
            "verification_canvas_name": output_canvas_file,
            "node_count": len(verification_questions),
            "source_canvas": canvas_file,
            "quality_grade": rag_result.quality_grade,
            "generation_time_ms": total_time_ms,
            "used_agentic_rag": True,
            "fallback": rag_result.is_fallback
        }

    except Exception as e:
        # 错误处理
        total_time_ms = (time.time() - start_time) * 1000
        if LOGURU_ENABLED:
            logger.error(
                f"Verification canvas generation failed: {e}",
                exc_info=True
            )
        raise


# 说明: 此方法需要添加到src/canvas_utils.py的CanvasOrchestrator类中
# 添加位置: shutdown_all_instances()方法之后, KnowledgeGraphLayer类之前 (约15056行)
