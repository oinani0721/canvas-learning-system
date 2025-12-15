"""
UltraThink检验白板生成器 - 版本化迭代系统

本脚本实现版本化检验白板生成功能:
- v1: 从原白板提取所有红色/紫色节点
- v2+: 继承上版本未完成节点 + 原白板新增红/紫节点

Author: Canvas Learning System Team
Version: 1.0 (UltraThink Upgrade)
Created: 2025-10-16
"""

import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Fix Windows console encoding
# Note: Using reconfigure instead of replacing sys.stdout/stderr to avoid argparse issues
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass  # Python < 3.7 or encoding already set

from canvas_utils import (
    CanvasBusinessLogic,
    CanvasJSONOperator,
    COLOR_CODE_RED,
    COLOR_CODE_PURPLE,
    COLOR_CODE_BLUE,
    COLOR_CODE_YELLOW,
)

from yellow_node_analyzer import UnderstandingLevelAnalyzer
from strategy_generator import StrategyNodeGenerator


# ========== 常量定义 ==========

# 文件路径常量
PROGRESS_TRACKER_FILENAME = "检验进度追踪.json"

# 布局常量
TITLE_NODE_Y = -600
TITLE_NODE_HEIGHT = 500
QUESTION_START_Y = 0
QUESTION_WIDTH = 500
QUESTION_HEIGHT = 300
UNDERSTANDING_WIDTH = 400
UNDERSTANDING_HEIGHT = 200
HORIZONTAL_GAP = 200
VERTICAL_GAP = 400

# 智能策略布局常量
EXPLANATION_NODE_X_OFFSET = 800   # 解释节点在问题右侧800px
EXPLANATION_NODE_WIDTH = 600
EXPLANATION_NODE_HEIGHT = 400
SUMMARY_NODE_X_OFFSET = 1600      # 总结节点在问题右侧1600px
SUB_QUESTION_X_OFFSET = 800       # 子问题组在问题右侧800px
SUB_ANSWER_X_OFFSET = 1400        # 子答案在问题右侧1400px
SUB_ANSWER_VERTICAL_GAP = 250     # 子答案垂直间隔


# ========== 核心类 ==========

class UltraThinkReviewGenerator:
    """UltraThink版本化检验白板生成器

    负责生成和管理版本化的检验白板:
    - 首次生成v1: 提取原白板所有红/紫节点
    - 后续生成v2+: 继承未完成节点 + 扫描新节点
    - 更新进度追踪JSON
    - 管理TodoList集成
    """

    def __init__(self, original_canvas_path: str, notes_dir: Optional[str] = None,
                 overview_text: Optional[str] = None):
        """初始化生成器

        Args:
            original_canvas_path: 原始Canvas白板路径
            notes_dir: 笔记库目录路径，默认为original_canvas_path的父目录
            overview_text: 用户提交的综述文本（可选）
        """
        self.original_canvas_path = original_canvas_path
        self.original_canvas_name = Path(original_canvas_path).stem

        # 笔记库目录（进度追踪文件存放处）
        if notes_dir is None:
            self.notes_dir = str(Path(original_canvas_path).parent)
        else:
            self.notes_dir = notes_dir

        # 进度追踪文件路径
        self.progress_tracker_path = os.path.join(
            self.notes_dir,
            PROGRESS_TRACKER_FILENAME
        )

        # 加载或初始化进度追踪
        self.progress_data = self._load_or_init_progress_tracker()

        # 初始化原白板业务逻辑
        self.original_logic = CanvasBusinessLogic(original_canvas_path)

        # 初始化理解分析器
        self.understanding_analyzer = UnderstandingLevelAnalyzer()

        # 初始化策略生成器
        self.strategy_generator = StrategyNodeGenerator()

        # 综述文本
        self.overview_text = overview_text

    def _load_or_init_progress_tracker(self) -> Dict[str, Any]:
        """加载或初始化进度追踪JSON

        Returns:
            Dict: 进度追踪数据
        """
        if os.path.exists(self.progress_tracker_path):
            with open(self.progress_tracker_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 初始化空的进度追踪
            return {
                "canvas_name": self.original_canvas_name,
                "original_canvas_path": self.original_canvas_path,
                "latest_version": 0,
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "review_sessions": [],
                "unfinished_nodes": [],
                "metadata": {
                    "total_nodes_ever_reviewed": 0,
                    "total_nodes_completed": 0,
                    "completion_rate": 0.0,
                    "average_attempts_to_complete": 0.0
                }
            }

    def _save_progress_tracker(self):
        """保存进度追踪JSON到文件"""
        with open(self.progress_tracker_path, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 进度追踪已更新: {self.progress_tracker_path}")

    def generate_next_version(self) -> Dict[str, Any]:
        """生成下一个版本的检验白板

        根据当前版本号决定生成逻辑:
        - version=0: 生成v1（首次生成，提取所有红/紫节点）
        - version>0: 生成v(n+1)（继承未完成 + 新增节点）

        Returns:
            Dict: 生成结果
                {
                    "version": int,
                    "canvas_path": str,
                    "nodes_count": int,
                    "source": str  # "first_generation" or "iteration"
                }
        """
        current_version = self.progress_data["latest_version"]
        next_version = current_version + 1

        print(f"\n{'='*60}")
        print(f"🚀 开始生成检验白板 v{next_version}")
        print(f"{'='*60}\n")

        if current_version == 0:
            # 首次生成v1
            result = self._generate_v1()
        else:
            # 迭代生成v2+
            result = self._generate_iteration(next_version)

        # 更新latest_version
        self.progress_data["latest_version"] = next_version
        self._save_progress_tracker()

        print(f"\n{'='*60}")
        print(f"✅ 检验白板 v{next_version} 生成成功!")
        print(f"📁 文件路径: {result['canvas_path']}")
        print(f"📊 节点数量: {result['nodes_count']}")
        print(f"{'='*60}\n")

        return result

    def _generate_v1(self) -> Dict[str, Any]:
        """生成v1检验白板（首次生成）

        流程:
        1. 从原白板提取所有红色/紫色节点
        2. 为每个节点生成检验问题
        3. 创建v1 Canvas文件
        4. 初始化进度追踪

        Returns:
            Dict: 生成结果
        """
        print("📝 [步骤 1/4] 从原白板提取红色/紫色节点...")

        # 使用已有的extract_verification_nodes方法
        extracted = self.original_logic.extract_verification_nodes()

        red_nodes = extracted["red_nodes"]
        purple_nodes = extracted["purple_nodes"]
        all_nodes = red_nodes + purple_nodes

        print(f"   ✓ 提取完成: {len(red_nodes)}个红色节点, {len(purple_nodes)}个紫色节点")

        print("\n📝 [步骤 2/4] 智能策略分析...")

        # 智能策略分析和节点生成
        review_nodes = []
        strategy_stats = {"provide_explanation": 0, "split_questions": 0, "deep_verification": 0}

        for node in all_nodes:
            # 提取黄色理解内容（第一个related_yellow，如果有的话）
            yellow_understanding = ""
            if node.get("related_yellow") and len(node["related_yellow"]) > 0:
                yellow_understanding = node["related_yellow"][0]

            # 分析理解程度
            analysis = self.understanding_analyzer.analyze(yellow_understanding)

            # 记录策略统计
            strategy_stats[analysis["recommended_strategy"]] += 1

            review_node = {
                "id": node["id"],
                "content": node["content"],
                "color": COLOR_CODE_RED if node in red_nodes else COLOR_CODE_PURPLE,
                "related_yellow": node.get("related_yellow", []),
                "yellow_understanding": yellow_understanding,
                "verification_question": self._generate_simple_verification_question(node),
                "attempts": 0,
                "status": "unfinished",
                # 新增：智能策略信息
                "analysis": analysis,
                "strategy": analysis["recommended_strategy"]
            }
            review_nodes.append(review_node)

        print(f"   ✓ 智能分析完成: {len(review_nodes)}个节点")
        print(f"   📊 策略分布: 补充解释{strategy_stats['provide_explanation']}个, "
              f"拆分问题{strategy_stats['split_questions']}个, "
              f"深度检验{strategy_stats['deep_verification']}个")

        print("\n📝 [步骤 3/4] 创建v1检验白板Canvas文件...")

        # 创建v1 Canvas
        v1_canvas_path = self._create_review_canvas(1, review_nodes)

        print(f"   ✓ Canvas创建完成: {v1_canvas_path}")

        print("\n📝 [步骤 4/4] 更新进度追踪...")

        # 初始化review session
        session = {
            "version": 1,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "canvas_path": v1_canvas_path,
            "nodes_reviewed": len(review_nodes),
            "nodes_completed": 0,
            "interventions": []
        }
        self.progress_data["review_sessions"].append(session)

        # 添加到unfinished_nodes
        for node in review_nodes:
            self.progress_data["unfinished_nodes"].append({
                "node_id": node["id"],
                "original_content": node["content"],
                "color": node["color"],
                "attempts": 0,
                "last_score": None,
                "interventions": []
            })

        # 更新metadata
        self.progress_data["metadata"]["total_nodes_ever_reviewed"] = len(review_nodes)

        print("   ✓ 进度追踪已更新")

        return {
            "version": 1,
            "canvas_path": v1_canvas_path,
            "nodes_count": len(review_nodes),
            "source": "first_generation"
        }

    def _generate_iteration(self, version: int) -> Dict[str, Any]:
        """生成迭代版本v2+的检验白板

        流程:
        1. 读取上版本未完成节点
        2. 扫描原白板新增红/紫节点
        3. 合并并生成更深层次问题
        4. 创建新版本Canvas
        5. 更新进度追踪

        Args:
            version: 要生成的版本号

        Returns:
            Dict: 生成结果
        """
        print(f"📝 [步骤 1/5] 读取v{version-1}未完成节点...")

        # 从进度追踪获取未完成节点
        unfinished = self.progress_data["unfinished_nodes"]
        print(f"   ✓ 未完成节点: {len(unfinished)}个")

        print(f"\n📝 [步骤 2/5] 扫描原白板新增红/紫节点...")

        # 提取原白板当前所有红/紫节点
        extracted = self.original_logic.extract_verification_nodes()
        current_red = extracted["red_nodes"]
        current_purple = extracted["purple_nodes"]

        # 识别新增节点（不在unfinished_nodes中的）
        existing_ids = {node["node_id"] for node in unfinished}
        new_nodes = []
        for node in (current_red + current_purple):
            if node["id"] not in existing_ids:
                new_nodes.append(node)

        print(f"   ✓ 新增节点: {len(new_nodes)}个")

        print(f"\n📝 [步骤 3/5] 生成更深层次检验问题...")

        # 为未完成节点生成深层次问题
        review_nodes = []
        for uf_node in unfinished:
            review_node = {
                "id": uf_node["node_id"],
                "content": uf_node["original_content"],
                "color": uf_node["color"],
                "attempts": uf_node["attempts"],
                "verification_question": self._generate_deeper_verification_question(uf_node),
                "status": "unfinished"
            }
            review_nodes.append(review_node)

        # 为新增节点生成基础问题
        for node in new_nodes:
            review_node = {
                "id": node["id"],
                "content": node["content"],
                "color": COLOR_CODE_RED if node in current_red else COLOR_CODE_PURPLE,
                "related_yellow": node.get("related_yellow", []),
                "verification_question": self._generate_simple_verification_question(node),
                "attempts": 0,
                "status": "unfinished"
            }
            review_nodes.append(review_node)

        print(f"   ✓ 总计: {len(review_nodes)}个检验问题")

        print(f"\n📝 [步骤 4/5] 创建v{version}检验白板Canvas文件...")

        # 创建新版本Canvas
        canvas_path = self._create_review_canvas(version, review_nodes)

        print(f"   ✓ Canvas创建完成: {canvas_path}")

        print(f"\n📝 [步骤 5/5] 更新进度追踪...")

        # 添加新session
        session = {
            "version": version,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "canvas_path": canvas_path,
            "nodes_reviewed": len(review_nodes),
            "nodes_completed": 0,
            "interventions": []
        }
        self.progress_data["review_sessions"].append(session)

        # 添加新节点到unfinished_nodes
        for node in new_nodes:
            self.progress_data["unfinished_nodes"].append({
                "node_id": node["id"],
                "original_content": node["content"],
                "color": COLOR_CODE_RED if node in current_red else COLOR_CODE_PURPLE,
                "attempts": 0,
                "last_score": None,
                "interventions": []
            })

        # 更新metadata
        total_ever = self.progress_data["metadata"]["total_nodes_ever_reviewed"]
        self.progress_data["metadata"]["total_nodes_ever_reviewed"] = total_ever + len(new_nodes)

        print("   ✓ 进度追踪已更新")

        return {
            "version": version,
            "canvas_path": canvas_path,
            "nodes_count": len(review_nodes),
            "source": "iteration"
        }

    def _create_review_canvas(self, version: int, review_nodes: List[Dict]) -> str:
        """创建检验白板Canvas文件

        Args:
            version: 版本号
            review_nodes: 检验节点列表

        Returns:
            str: Canvas文件路径
        """
        # 生成文件名
        canvas_filename = f"{self.original_canvas_name}-检验白板-v{version}.canvas"
        canvas_path = os.path.join(self.notes_dir, canvas_filename)

        # 创建Canvas数据结构
        canvas_data = {
            "nodes": [],
            "edges": []
        }

        # 添加标题节点
        title_text = f"""# 🎯 UltraThink检验白板 v{version}

**创建时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**来源**: {self.original_canvas_name}
**检验节点数**: {len(review_nodes)}个

---

## 📝 使用说明

1. 在黄色节点中填写你的理解（不要查看原白板）
2. 完成后调用scoring-agent进行评分
3. 系统会自动生成follow-up节点（澄清路径/记忆锚点/深层问题）
4. 持续迭代直到所有节点变绿

## 🔄 版本说明

- **v{version}**: 本次检验包含 {len(review_nodes)} 个待验证节点
- **目标**: 所有节点评分≥80分（绿色）"""

        title_node = {
            "id": "review-title",
            "type": "text",
            "text": title_text,
            "x": 0,
            "y": TITLE_NODE_Y,
            "width": 800,
            "height": TITLE_NODE_HEIGHT,
            "color": COLOR_CODE_BLUE
        }
        canvas_data["nodes"].append(title_node)

        # 添加检验问题节点和理解节点（智能策略）
        current_y = QUESTION_START_Y
        for idx, node in enumerate(review_nodes, 1):
            # 问题节点（保持原有颜色）
            q_id = f"review-q{idx}"
            q_text = f"""# 检验问题 {idx}

**原始内容**:
{node['content'][:200]}{'...' if len(node['content']) > 200 else ''}

**你的理解**:
{node['yellow_understanding'][:100]}{'...' if len(node['yellow_understanding']) > 100 else ''}

**理解程度**: {node.get('analysis', {}).get('understanding_percentage', 50)}%
**推荐策略**: {node.get('strategy', 'deep_verification')}

---

**检验问题**:

{node['verification_question']}"""

            q_node = {
                "id": q_id,
                "type": "text",
                "text": q_text,
                "x": 0,
                "y": current_y,
                "width": QUESTION_WIDTH,
                "height": QUESTION_HEIGHT,
                "color": node["color"]
            }
            canvas_data["nodes"].append(q_node)

            # 根据策略生成不同的节点组
            strategy = node.get("strategy", "deep_verification")

            if strategy == "provide_explanation":
                # 补充解释策略：解释节点 + 总结节点
                strategy_result = self.strategy_generator.generate_explanation_strategy_nodes(
                    node_id=q_id,
                    node_content=node["content"],
                    yellow_understanding=node["yellow_understanding"],
                    understanding_percentage=node.get('analysis', {}).get('understanding_percentage', 10),
                    base_x=0,
                    base_y=current_y
                )
                canvas_data["nodes"].extend(strategy_result["nodes"])
                canvas_data["edges"].extend(strategy_result["edges"])
                # 解释策略节点更高，需要更大间距
                current_y += (QUESTION_HEIGHT + VERTICAL_GAP + 200)

            elif strategy == "split_questions":
                # 拆分问题策略：子问题组 + 多个回答节点
                strategy_result = self.strategy_generator.generate_split_questions_strategy_nodes(
                    node_id=q_id,
                    node_content=node["content"],
                    yellow_understanding=node["yellow_understanding"],
                    base_x=0,
                    base_y=current_y,
                    num_sub_questions=3
                )
                canvas_data["nodes"].extend(strategy_result["nodes"])
                canvas_data["edges"].extend(strategy_result["edges"])
                # 拆分问题策略需要更大间距（3个子问题）
                current_y += (QUESTION_HEIGHT + VERTICAL_GAP + 600)

            else:
                # 深度检验策略：保持简单问题 + 理解节点
                u_id = f"review-u{idx}"
                u_text = f"""# 💡 我的理解 {idx}

在这里写下你对这个问题的理解...

（不要查看原白板！尝试用自己的话解释）"""

                u_node = {
                    "id": u_id,
                    "type": "text",
                    "text": u_text,
                    "x": QUESTION_WIDTH + HORIZONTAL_GAP,
                    "y": current_y + 50,
                    "width": UNDERSTANDING_WIDTH,
                    "height": UNDERSTANDING_HEIGHT,
                    "color": COLOR_CODE_YELLOW
                }
                canvas_data["nodes"].append(u_node)

                # 连接边
                edge = {
                    "id": f"edge-q{idx}-u{idx}",
                    "fromNode": q_id,
                    "fromSide": "right",
                    "toNode": u_id,
                    "toSide": "left",
                    "label": "我的理解"
                }
                canvas_data["edges"].append(edge)

                # 更新Y坐标
                current_y += (QUESTION_HEIGHT + VERTICAL_GAP)

        # 保存Canvas文件
        CanvasJSONOperator.write_canvas(canvas_path, canvas_data)

        return canvas_path

    def _generate_simple_verification_question(self, node: Dict) -> str:
        """生成简单的检验问题（用于首次生成或新节点）

        TODO: 未来可调用verification-question-agent生成更智能的问题

        Args:
            node: 节点数据

        Returns:
            str: 检验问题文本
        """
        # 简化版：基于节点内容生成通用问题
        return """请用自己的话解释这个概念的核心含义。如果完全不懂，请尝试从你已知的相关概念出发，猜测它可能是什么意思。"""

    def _generate_deeper_verification_question(self, unfinished_node: Dict) -> str:
        """为未完成节点生成更深层次的检验问题

        TODO: 未来可根据unfinished_node的attempts、last_score、interventions生成更针对性的问题

        Args:
            unfinished_node: 未完成节点数据

        Returns:
            str: 更深层次的检验问题
        """
        attempts = unfinished_node.get("attempts", 0)

        if attempts == 0:
            return """请用自己的话重新解释这个概念，并举一个具体例子。"""
        elif attempts == 1:
            return """请详细解释这个概念，并说明它与相关概念的区别和联系。"""
        else:
            return """请从应用角度解释这个概念：什么时候用？为什么用？怎么用？"""


# ========== 命令行接口 ==========

def main():
    """命令行主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="UltraThink检验白板生成器 - 版本化迭代系统"
    )
    parser.add_argument(
        "canvas_path",
        help="原始Canvas白板文件路径"
    )
    parser.add_argument(
        "--notes-dir",
        help="笔记库目录路径（可选，默认为canvas文件所在目录）"
    )
    parser.add_argument(
        "--overview",
        help="学习综述文本（可选，用于宏观判断学习路线）"
    )
    parser.add_argument(
        "--overview-file",
        help="学习综述文件路径（可选，从文件读取综述）"
    )

    args = parser.parse_args()

    # 验证文件存在
    if not os.path.exists(args.canvas_path):
        print(f"❌ 错误: Canvas文件不存在: {args.canvas_path}")
        sys.exit(1)

    # 处理综述
    overview_text = args.overview
    if args.overview_file:
        if os.path.exists(args.overview_file):
            with open(args.overview_file, 'r', encoding='utf-8') as f:
                overview_text = f.read()
            print(f"📄 已读取综述文件: {args.overview_file}")
        else:
            print(f"⚠️ 警告: 综述文件不存在: {args.overview_file}")

    # 创建生成器并生成下一个版本
    generator = UltraThinkReviewGenerator(
        args.canvas_path,
        args.notes_dir,
        overview_text
    )

    result = generator.generate_next_version()

    # 输出结果
    print("\n" + "="*60)
    print("📊 生成结果汇总")
    print("="*60)
    print(f"版本: v{result['version']}")
    print(f"文件: {result['canvas_path']}")
    print(f"节点数: {result['nodes_count']}")
    print(f"来源: {result['source']}")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
