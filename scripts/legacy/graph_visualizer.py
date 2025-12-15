#!/usr/bin/env python3
"""
图谱可视化器

生成知识图谱的交互式可视化，支持多种输出格式和自定义样式。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
from loguru import logger

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available, some features will be limited")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available, interactive visualizations will be limited")


class GraphVisualizer:
    """知识图谱可视化器

    支持多种可视化格式：
    - 交互式网络图 (Plotly)
    - 静态网络图 (NetworkX + Matplotlib)
    - 数据导出 (JSON, GraphML, SVG)
    """

    def __init__(self):
        """初始化可视化器"""
        self.color_schemes = {
            "default": {
                "concept": "#3498db",      # 蓝色
                "relationship": "#95a5a6",  # 灰色
                "weakness": "#e74c3c",     # 红色
                "session": "#2ecc71",      # 绿色
                "highlight": "#f39c12"     # 橙色
            },
            "dark": {
                "concept": "#5dade2",      # 浅蓝色
                "relationship": "#7f8c8d",  # 深灰色
                "weakness": "#ec7063",     # 浅红色
                "session": "#58d68d",      # 浅绿色
                "highlight": "#f7dc6f"     # 浅橙色
            }
        }

        self.layout_algorithms = {
            "spring": self._spring_layout,
            "circular": self._circular_layout,
            "kamada_kawai": self._kamada_kawai_layout,
            "hierarchical": self._hierarchical_layout
        }

        logger.info("图谱可视化器初始化完成")

    def visualize_concept_network(self,
                                concepts: Dict[str, Any],
                                relationships: List[Dict[str, Any]],
                                output_format: str = "json",
                                layout_algorithm: str = "spring",
                                color_scheme: str = "default",
                                highlight_concepts: Optional[List[str]] = None,
                                output_path: Optional[str] = None) -> Dict[str, Any]:
        """可视化概念网络

        Args:
            concepts: 概念字典
            relationships: 关系列表
            output_format: 输出格式 ("json", "plotly", "networkx", "svg", "graphml")
            layout_algorithm: 布局算法
            color_scheme: 颜色方案
            highlight_concepts: 需要高亮的概念列表
            output_path: 输出文件路径

        Returns:
            Dict: 可视化结果数据
        """
        try:
            # 构建图结构
            if NETWORKX_AVAILABLE:
                G = self._build_networkx_graph(concepts, relationships)
                pos = self._compute_layout(G, layout_algorithm)
            else:
                # 简单的图结构
                G, pos = self._build_simple_graph(concepts, relationships)

            # 计算节点和边的视觉属性
            node_visual_attrs = self._compute_node_attributes(concepts, pos, color_scheme, highlight_concepts)
            edge_visual_attrs = self._compute_edge_attributes(relationships, pos, color_scheme)

            # 生成可视化
            if output_format == "json":
                result = self._generate_json_visualization(
                    concepts, relationships, node_visual_attrs, edge_visual_attrs
                )
            elif output_format == "plotly" and PLOTLY_AVAILABLE:
                result = self._generate_plotly_visualization(
                    node_visual_attrs, edge_visual_attrs, color_scheme
                )
            elif output_format == "networkx" and NETWORKX_AVAILABLE:
                result = self._generate_networkx_visualization(G, pos, node_visual_attrs, edge_visual_attrs)
            elif output_format == "svg":
                result = self._generate_svg_visualization(node_visual_attrs, edge_visual_attrs)
            elif output_format == "graphml" and NETWORKX_AVAILABLE:
                result = self._generate_graphml_export(G, output_path)
            else:
                result = self._generate_json_visualization(
                    concepts, relationships, node_visual_attrs, edge_visual_attrs
                )

            # 保存文件
            if output_path:
                self._save_visualization(result, output_path, output_format)

            logger.info(f"概念网络可视化完成: {output_format}")
            return result

        except Exception as e:
            logger.error(f"概念网络可视化失败: {e}")
            raise

    def _build_networkx_graph(self, concepts: Dict[str, Any], relationships: List[Dict[str, Any]]) -> Any:
        """构建NetworkX图结构"""
        G = nx.Graph()

        # 添加节点
        for concept_name, concept_data in concepts.items():
            G.add_node(
                concept_name,
                **concept_data
            )

        # 添加边
        for rel in relationships:
            source = rel.get("source_concept")
            target = rel.get("target_concept")
            if source and target and source in concepts and target in concepts:
                G.add_edge(
                    source, target,
                    **rel
                )

        return G

    def _build_simple_graph(self, concepts: Dict[str, Any], relationships: List[Dict[str, Any]]) -> Tuple[Dict, Dict]:
        """构建简单图结构（当NetworkX不可用时）"""
        # 简单的节点和边结构
        G = {"nodes": list(concepts.keys()), "edges": []}

        for rel in relationships:
            source = rel.get("source_concept")
            target = rel.get("target_concept")
            if source and target and source in concepts and target in concepts:
                G["edges"].append((source, target))

        # 简单的布局
        pos = self._simple_layout(list(concepts.keys()))
        return G, pos

    def _simple_layout(self, nodes: List[str]) -> Dict[str, Tuple[float, float]]:
        """简单的圆形布局"""
        n = len(nodes)
        pos = {}
        for i, node in enumerate(nodes):
            angle = 2 * np.pi * i / n
            pos[node] = (np.cos(angle), np.sin(angle))
        return pos

    def _compute_layout(self, G: Any, algorithm: str) -> Dict[str, Tuple[float, float]]:
        """计算图布局"""
        if algorithm in self.layout_algorithms:
            return self.layout_algorithms[algorithm](G)
        else:
            return self._spring_layout(G)

    def _spring_layout(self, G: Any) -> Dict[str, Tuple[float, float]]:
        """Spring布局算法"""
        if NETWORKX_AVAILABLE:
            return nx.spring_layout(G, k=2, iterations=50)
        else:
            return self._simple_layout(list(G["nodes"]))

    def _circular_layout(self, G: Any) -> Dict[str, Tuple[float, float]]:
        """圆形布局算法"""
        if NETWORKX_AVAILABLE:
            return nx.circular_layout(G)
        else:
            return self._simple_layout(list(G["nodes"]))

    def _kamada_kawai_layout(self, G: Any) -> Dict[str, Tuple[float, float]]:
        """Kamada-Kawai布局算法"""
        if NETWORKX_AVAILABLE:
            return nx.kamada_kawai_layout(G)
        else:
            return self._simple_layout(list(G["nodes"]))

    def _hierarchical_layout(self, G: Any) -> Dict[str, Tuple[float, float]]:
        """层次布局算法"""
        if NETWORKX_AVAILABLE:
            try:
                return nx.drawing.nx_agraph.graphviz_layout(G, prog="dot")
            except:
                # 如果Graphviz不可用，使用简单层次布局
                return self._simple_hierarchical_layout(G)
        else:
            return self._simple_hierarchical_layout(G)

    def _simple_hierarchical_layout(self, G: Any) -> Dict[str, Tuple[float, float]]:
        """简单的层次布局"""
        nodes = list(G["nodes"]) if not NETWORKX_AVAILABLE else list(G.nodes())
        levels = {}

        # 简单的分层逻辑
        for i, node in enumerate(nodes):
            level = i % 3  # 简单分为3层
            if level not in levels:
                levels[level] = []
            levels[level].append(node)

        pos = {}
        for level, node_list in levels.items():
            for i, node in enumerate(node_list):
                x = i * 2 - len(node_list)
                y = -level * 3
                pos[node] = (x, y)

        return pos

    def _compute_node_attributes(self, concepts: Dict[str, Any], pos: Dict[str, Tuple[float, float]],
                               color_scheme: str, highlight_concepts: Optional[List[str]]) -> Dict[str, Any]:
        """计算节点视觉属性"""
        colors = self.color_schemes.get(color_scheme, self.color_schemes["default"])
        node_attrs = {}

        for concept_name, concept_data in concepts.items():
            # 基础属性
            attrs = {
                "name": concept_name,
                "x": pos[concept_name][0],
                "y": pos[concept_name][1],
                "size": 20,
                "color": colors["concept"],
                "label": concept_name,
                "description": concept_data.get("text_content", "")[:100]
            }

            # 根据概念置信度调整大小
            confidence = concept_data.get("confidence", 0.5)
            attrs["size"] = 10 + confidence * 20

            # 高亮特定概念
            if highlight_concepts and concept_name in highlight_concepts:
                attrs["color"] = colors["highlight"]
                attrs["size"] *= 1.5

            # 根据学科领域着色
            subject_areas = concept_data.get("subject_areas", [])
            if subject_areas:
                subject_colors = {
                    "数学": "#3498db",
                    "物理": "#e67e22",
                    "化学": "#9b59b6",
                    "计算机": "#2ecc71"
                }
                for subject in subject_areas:
                    if subject in subject_colors:
                        attrs["subject_color"] = subject_colors[subject]
                        break

            # 根据节点类型调整
            node_types = concept_data.get("node_types", [])
            if "question" in node_types:
                attrs["shape"] = "diamond"
            elif "explanation" in node_types:
                attrs["shape"] = "rectangle"

            node_attrs[concept_name] = attrs

        return node_attrs

    def _compute_edge_attributes(self, relationships: List[Dict[str, Any]], pos: Dict[str, Tuple[float, float]],
                               color_scheme: str) -> Dict[str, Any]:
        """计算边视觉属性"""
        colors = self.color_schemes.get(color_scheme, self.color_schemes["default"])
        edge_attrs = {}

        for i, rel in enumerate(relationships):
            source = rel.get("source_concept")
            target = rel.get("target_concept")

            if source and target and source in pos and target in pos:
                attrs = {
                    "source": source,
                    "target": target,
                    "x": [pos[source][0], pos[target][0]],
                    "y": [pos[source][1], pos[target][1]],
                    "width": 1,
                    "color": colors["relationship"],
                    "label": rel.get("relationship_type", "related"),
                    "strength": rel.get("relationship_strength", 0.5),
                    "confidence": rel.get("confidence_score", 0.5)
                }

                # 根据关系强度调整宽度
                strength = rel.get("relationship_strength", 0.5)
                attrs["width"] = 0.5 + strength * 3

                # 根据关系类型着色
                rel_type = rel.get("relationship_type", "")
                type_colors = {
                    "is_prerequisite_for": "#e74c3c",
                    "is_similar_to": "#3498db",
                    "is_contradictory_of": "#f39c12",
                    "is_derived_from": "#9b59b6",
                    "is_applied_in": "#2ecc71"
                }
                if rel_type in type_colors:
                    attrs["color"] = type_colors[rel_type]

                edge_attrs[f"edge_{i}"] = attrs

        return edge_attrs

    def _generate_json_visualization(self, concepts: Dict[str, Any], relationships: List[Dict[str, Any]],
                                   node_attrs: Dict[str, Any], edge_attrs: Dict[str, Any]) -> Dict[str, Any]:
        """生成JSON格式的可视化数据"""
        return {
            "format": "json",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "total_nodes": len(concepts),
                "total_edges": len(relationships),
                "node_attributes": ["name", "x", "y", "size", "color", "label", "description"],
                "edge_attributes": ["source", "target", "width", "color", "label", "strength"]
            },
            "nodes": list(node_attrs.values()),
            "edges": list(edge_attrs.values())
        }

    def _generate_plotly_visualization(self, node_attrs: Dict[str, Any], edge_attrs: Dict[str, Any],
                                      color_scheme: str) -> Dict[str, Any]:
        """生成Plotly交互式可视化"""
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly not available")

        # 创建边的轨迹
        edge_x = []
        edge_y = []
        edge_info = []

        for edge in edge_attrs.values():
            edge_x.extend(edge["x"] + [None])
            edge_y.extend(edge["y"] + [None])
            edge_info.append(f"{edge['source']} -> {edge['target']} ({edge['label']})")

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines',
            name='关系'
        )

        # 创建节点的轨迹
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        node_info = []

        for node in node_attrs.values():
            node_x.append(node["x"])
            node_y.append(node["y"])
            node_text.append(node["label"])
            node_colors.append(node["color"])
            node_sizes.append(node["size"])
            node_info.append(f"{node['name']}<br>{node['description']}")

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            hovertext=node_info,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            name='概念'
        )

        # 创建图形
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='知识图谱可视化',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20, l=5, r=5, t=40),
                           annotations=[
                               dict(
                                   text="知识图谱 - Canvas Learning System",
                                   showarrow=False,
                                   xref="paper", yref="paper",
                                   x=0.005, y=-0.002,
                                   xanchor='left', yanchor='bottom',
                                   font=dict(size=10)
                               )
                           ],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='white'
                       ))

        return {
            "format": "plotly",
            "figure": fig,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_networkx_visualization(self, G: Any, pos: Dict[str, Tuple[float, float]],
                                        node_attrs: Dict[str, Any], edge_attrs: Dict[str, Any]) -> Dict[str, Any]:
        """生成NetworkX可视化数据"""
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX not available")

        # 节点属性
        node_colors = [node_attrs[node]["color"] for node in G.nodes()]
        node_sizes = [node_attrs[node]["size"] * 10 for node in G.nodes()]
        node_labels = {node: node_attrs[node]["label"] for node in G.nodes()}

        # 边属性
        edge_colors = [list(edge_attrs.values())[i]["color"] for i in range(len(G.edges()))]
        edge_widths = [list(edge_attrs.values())[i]["width"] for i in range(len(G.edges()))]

        return {
            "format": "networkx",
            "graph": G,
            "layout": pos,
            "node_colors": node_colors,
            "node_sizes": node_sizes,
            "node_labels": node_labels,
            "edge_colors": edge_colors,
            "edge_widths": edge_widths,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_svg_visualization(self, node_attrs: Dict[str, Any], edge_attrs: Dict[str, Any]) -> Dict[str, Any]:
        """生成SVG格式的可视化"""
        # 计算SVG画布大小
        all_x = [attr["x"] for attr in node_attrs.values()]
        all_y = [attr["y"] for attr in node_attrs.values()]

        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)

            width = max(800, (max_x - min_x) * 50 + 100)
            height = max(600, (max_y - min_y) * 50 + 100)

            # 偏移到画布中心
            offset_x = width / 2 - (max_x + min_x) * 25
            offset_y = height / 2 - (max_y + min_y) * 25
        else:
            width, height = 800, 600
            offset_x = offset_y = 0

        # SVG头部
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
<defs>
    <style>
        .concept {{ fill: #3498db; stroke: #2c3e50; stroke-width: 2; }}
        .relationship {{ stroke: #95a5a6; stroke-width: 2; fill: none; }}
        .label {{ font-family: Arial, sans-serif; font-size: 12px; text-anchor: middle; }}
        .title {{ font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; }}
    </style>
</defs>
<rect width="{width}" height="{height}" fill="white"/>
<text x="{width//2}" y="30" class="title" text-anchor="middle">知识图谱可视化</text>'''

        # 绘制边
        for edge in edge_attrs.values():
            x1, x2 = edge["x"][0] * 50 + offset_x, edge["x"][1] * 50 + offset_x
            y1, y2 = edge["y"][0] * 50 + offset_y, edge["y"][1] * 50 + offset_y
            svg_content += f'''
<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="relationship" stroke="{edge["color"]}" stroke-width="{edge["width"]}"/>'''

        # 绘制节点
        for node in node_attrs.values():
            x = node["x"] * 50 + offset_x
            y = node["y"] * 50 + offset_y
            r = node["size"]
            svg_content += f'''
<circle cx="{x}" cy="{y}" r="{r}" class="concept" fill="{node["color"]}"/>
<text x="{x}" y="{y + r + 15}" class="label">{node["label"]}</text>'''

        svg_content += "\n</svg>"

        return {
            "format": "svg",
            "svg_content": svg_content,
            "width": width,
            "height": height,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _generate_graphml_export(self, G: Any, output_path: Optional[str]) -> Dict[str, Any]:
        """生成GraphML格式导出"""
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX not available")

        graphml_content = nx.generate_graphml(G)

        if output_path:
            output_file = Path(output_path)
            output_file.write_text(graphml_content, encoding='utf-8')

        return {
            "format": "graphml",
            "content": graphml_content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _save_visualization(self, result: Dict[str, Any], output_path: str, output_format: str) -> None:
        """保存可视化结果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if output_format == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        elif output_format == "plotly":
            if PLOTLY_AVAILABLE:
                result["figure"].write_html(str(output_file))
            else:
                raise ImportError("Plotly not available")
        elif output_format == "svg":
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result["svg_content"])
        elif output_format == "graphml":
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result["content"])

        logger.info(f"可视化已保存到: {output_path}")

    def visualize_learning_path(self,
                              start_concept: str,
                              end_concept: str,
                              concepts: Dict[str, Any],
                              relationships: List[Dict[str, Any]],
                              output_path: Optional[str] = None) -> Dict[str, Any]:
        """可视化学习路径

        Args:
            start_concept: 起始概念
            end_concept: 目标概念
            concepts: 概念字典
            relationships: 关系列表
            output_path: 输出路径

        Returns:
            Dict: 学习路径可视化结果
        """
        try:
            # 构建图结构
            if NETWORKX_AVAILABLE:
                G = self._build_networkx_graph(concepts, relationships)

                # 找到最短路径
                if start_concept in G and end_concept in G:
                    path = nx.shortest_path(G, start_concept, end_concept)

                    # 高亮路径上的节点和边
                    highlight_nodes = path
                    highlight_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]

                    # 生成可视化
                    result = self.visualize_concept_network(
                        concepts, relationships,
                        output_format="plotly",
                        highlight_concepts=highlight_nodes,
                        output_path=output_path
                    )

                    result["learning_path"] = {
                        "start_concept": start_concept,
                        "end_concept": end_concept,
                        "path": path,
                        "path_length": len(path) - 1
                    }

                    return result
                else:
                    raise ValueError(f"概念 {start_concept} 或 {end_concept} 不存在")
            else:
                raise ImportError("NetworkX not available for path finding")

        except Exception as e:
            logger.error(f"学习路径可视化失败: {e}")
            raise

    def generate_interactive_dashboard(self,
                                    concepts: Dict[str, Any],
                                    relationships: List[Dict[str, Any]],
                                    output_path: str) -> Dict[str, Any]:
        """生成交互式仪表板

        Args:
            concepts: 概念字典
            relationships: 关系列表
            output_path: 输出路径

        Returns:
            Dict: 仪表板数据
        """
        try:
            if not PLOTLY_AVAILABLE:
                raise ImportError("Plotly not available for dashboard")

            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('概念网络', '关系统计', '概念分布', '学习进度'),
                specs=[[{"type": "scatter"}, {"type": "bar"}],
                       [{"type": "pie"}, {"type": "indicator"}]]
            )

            # 1. 概念网络图
            network_result = self.visualize_concept_network(
                concepts, relationships, output_format="plotly"
            )
            network_fig = network_result["figure"]

            # 添加网络图到第一个子图
            for trace in network_fig.data:
                fig.add_trace(trace, row=1, col=1)

            # 2. 关系统计图
            rel_types = {}
            for rel in relationships:
                rel_type = rel.get("relationship_type", "unknown")
                rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

            fig.add_trace(
                go.Bar(
                    x=list(rel_types.keys()),
                    y=list(rel_types.values()),
                    name="关系统计"
                ),
                row=1, col=2
            )

            # 3. 概念分布饼图
            subject_counts = {}
            for concept in concepts.values():
                for subject in concept.get("subject_areas", ["未分类"]):
                    subject_counts[subject] = subject_counts.get(subject, 0) + 1

            fig.add_trace(
                go.Pie(
                    labels=list(subject_counts.keys()),
                    values=list(subject_counts.values()),
                    name="学科分布"
                ),
                row=2, col=1
            )

            # 4. 学习进度指标
            total_concepts = len(concepts)
            high_confidence_concepts = sum(
                1 for c in concepts.values() if c.get("confidence", 0) > 0.7
            )
            progress_percentage = (high_confidence_concepts / total_concepts * 100) if total_concepts > 0 else 0

            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=progress_percentage,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "学习进度"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ),
                row=2, col=2
            )

            # 更新布局
            fig.update_layout(
                title_text="知识图谱仪表板",
                showlegend=False,
                height=800
            )

            # 保存仪表板
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(output_file))

            result = {
                "format": "dashboard",
                "figure": fig,
                "output_path": str(output_file),
                "statistics": {
                    "total_concepts": total_concepts,
                    "high_confidence_concepts": high_confidence_concepts,
                    "progress_percentage": progress_percentage,
                    "total_relationships": len(relationships),
                    "subject_distribution": subject_counts,
                    "relationship_types": rel_types
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"交互式仪表板已生成: {output_path}")
            return result

        except Exception as e:
            logger.error(f"生成交互式仪表板失败: {e}")
            raise


# 便利函数
def visualize_canvas_knowledge_graph(canvas_path: str,
                                    output_format: str = "plotly",
                                    output_path: Optional[str] = None) -> Dict[str, Any]:
    """从Canvas文件可视化知识图谱的便利函数

    Args:
        canvas_path: Canvas文件路径
        output_format: 输出格式
        output_path: 输出路径

    Returns:
        Dict: 可视化结果
    """
    from concept_extractor import extract_concepts_from_canvas

    # 提取概念和关系
    import asyncio
    extraction_result = asyncio.run(extract_concepts_from_canvas(canvas_path))

    # 创建可视化器
    visualizer = GraphVisualizer()

    # 生成可视化
    return visualizer.visualize_concept_network(
        concepts=extraction_result["concepts"],
        relationships=extraction_result["relationships"],
        output_format=output_format,
        output_path=output_path
    )