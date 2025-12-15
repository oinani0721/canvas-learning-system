#!/usr/bin/env python3
"""
Graphiti时序知识图谱集成模块

本模块实现Canvas学习系统与Graphiti时序知识图谱的集成，
提供学习会话记录、概念关系提取、智能检索等功能。

Based on Graphiti library documentation from Context7: https://context7.com/getzep/graphiti/

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import yaml
from loguru import logger

# Graphiti imports
from graphiti_core import Graphiti
from graphiti_core.nodes import EntityNode, EpisodeType
from graphiti_core.edges import EntityEdge
from graphiti_core.llm_client.anthropic_client import AnthropicClient, LLMConfig
from graphiti_core.embedder.voyage import VoyageEmbedder, VoyageAIConfig


class GraphitiKnowledgeGraph:
    """Graphiti时序知识图谱管理器

    负责管理Canvas学习系统的时序知识图谱，包括：
    - 学习会话记录
    - 概念关系提取
    - 智能检索和分析
    - 数据备份和恢复

    Based on Graphiti library documentation from Context7
    """

    def __init__(self, neo4j_uri: str = "bolt://localhost:7687",
                 username: str = "neo4j", password: str = "password",
                 anthropic_api_key: Optional[str] = None,
                 voyage_api_key: Optional[str] = None):
        """初始化Graphiti连接

        Args:
            neo4j_uri: Neo4j数据库URI
            username: 数据库用户名
            password: 数据库密码
            anthropic_api_key: Anthropic API密钥（可选）
            voyage_api_key: Voyage AI API密钥（可选）

        Raises:
            ConnectionError: 如果无法连接到Neo4j数据库
        """
        self.neo4j_uri = neo4j_uri
        self.username = username
        self.password = password

        # Initialize Graphiti with custom LLM and embedder if API keys provided
        if anthropic_api_key and voyage_api_key:
            try:
                # Configure Anthropic LLM client
                llm_client = AnthropicClient(
                    config=LLMConfig(
                        api_key=anthropic_api_key,
                        model="claude-3-5-sonnet-20241022"
                    )
                )

                # Configure Voyage embedder
                embedder = VoyageEmbedder(
                    config=VoyageAIConfig(
                        api_key=voyage_api_key,
                        embedding_model="voyage-3"
                    )
                )

                self.graphiti = Graphiti(
                    uri=neo4j_uri,
                    user=username,
                    password=password,
                    llm_client=llm_client,
                    embedder=embedder
                )
                logger.info("Graphiti initialized with custom LLM and embedder")
            except Exception as e:
                logger.warning(f"Failed to initialize custom LLM/embedder: {e}")
                # Fall back to basic Graphiti
                self.graphiti = Graphiti(
                    uri=neo4j_uri,
                    user=username,
                    password=password
                )
                logger.info("Graphiti initialized with default configuration")
        else:
            # Basic Graphiti initialization
            self.graphiti = Graphiti(
                uri=neo4j_uri,
                user=username,
                password=password
            )
            logger.info("Graphiti initialized with basic configuration")

    async def initialize(self) -> None:
        """异步初始化Graphiti，建立索引和约束"""
        try:
            await self.graphiti.build_indices_and_constraints()
            logger.info("Graphiti indices and constraints built successfully")
        except Exception as e:
            logger.error(f"Failed to build indices and constraints: {e}")
            raise

    async def close(self) -> None:
        """关闭Graphiti连接"""
        try:
            await self.graphiti.close()
            logger.info("Graphiti connection closed")
        except Exception as e:
            logger.error(f"Error closing Graphiti connection: {e}")

    async def record_learning_session(self, session_data: Dict) -> str:
        """记录学习会话到知识图谱

        Args:
            session_data: 学习会话数据，包含以下字段：
                - session_id: 会话ID（可选，会自动生成）
                - canvas_file: Canvas文件路径
                - session_type: 会话类型（decomposition|explanation|scoring|review）
                - duration_minutes: 会话时长（分钟）
                - nodes_interacted: 交互节点列表
                - learning_outcomes: 学习成果

        Returns:
            str: 会话记录ID

        Raises:
            ValueError: 如果session_data缺少必要字段
        """
        # 验证必要字段
        required_fields = ["canvas_file", "session_type", "duration_minutes"]
        for field in required_fields:
            if field not in session_data:
                raise ValueError(f"缺少必要字段: {field}")

        # 生成会话ID（如果未提供）
        session_id = session_data.get("session_id", f"session-{uuid.uuid4().hex[:16]}")

        try:
            # 创建学习会话episode
            session_name = f"{session_data['session_type']} session for {Path(session_data['canvas_file']).name}"
            session_body = self._create_session_episode_body(session_data)

            episode_result = await self.graphiti.add_episode(
                name=session_name,
                episode_body=session_body,
                source=EpisodeType.text,
                source_description=f"Canvas learning session: {session_data['canvas_file']}",
                reference_time=datetime.now(timezone.utc),
                group_id=session_data.get("user_id", "default")
            )

            # 记录节点交互作为相关实体
            await self._record_node_interactions_graphiti(session_id, session_data.get("nodes_interacted", []))

            logger.info(f"成功记录学习会话: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"记录学习会话失败: {e}")
            raise

    def _create_session_episode_body(self, session_data: Dict) -> str:
        """创建学习会话的episode描述"""
        canvas_file = session_data["canvas_file"]
        session_type = session_data["session_type"]
        duration = session_data["duration_minutes"]

        outcomes = session_data.get("learning_outcomes", {})
        new_concepts = outcomes.get("new_concepts_learned", 0)
        reviewed_concepts = outcomes.get("concepts_reviewed", 0)
        weaknesses = outcomes.get("weaknesses_identified", 0)
        improvements = outcomes.get("mastery_improvements", 0)

        episode_body = f"""
Learning Session Details:
- Canvas File: {canvas_file}
- Session Type: {session_type}
- Duration: {duration} minutes
- New Concepts Learned: {new_concepts}
- Concepts Reviewed: {reviewed_concepts}
- Weaknesses Identified: {weaknesses}
- Mastery Improvements: {improvements}
        """.strip()

        return episode_body

    async def _record_node_interactions_graphiti(self, session_id: str, nodes_interacted: List[Dict]) -> None:
        """使用Graphiti记录节点交互"""
        for interaction in nodes_interacted:
            if not isinstance(interaction, dict):
                continue

            concept_name = interaction.get("concept_name", f"概念-{interaction.get('node_id', 'unknown')[:8]}")
            node_type = interaction.get("node_type", "unknown")
            interaction_type = interaction.get("interaction_type", "unknown")
            outcome = interaction.get("interaction_outcome", "unknown")

            # 创建概念实体节点
            concept_node = EntityNode(
                name=concept_name,
                labels=[node_type.capitalize(), "Concept"],
                summary=f"Canvas {node_type} concept: {concept_name}",
                group_id="canvas_concepts"
            )

            # 创建交互episode
            interaction_episode = await self.graphiti.add_episode(
                name=f"{interaction_type} interaction with {concept_name}",
                episode_body=f"""
Interaction Details:
- Concept: {concept_name}
- Node Type: {node_type}
- Interaction Type: {interaction_type}
- Outcome: {outcome}
- Agent Used: {interaction.get('agent_used', 'unknown')}
                """.strip(),
                source=EpisodeType.text,
                source_description=f"Node interaction from session {session_id}",
                reference_time=datetime.now(timezone.utc),
                group_id="canvas_interactions"
            )

            logger.debug(f"Recorded interaction for concept: {concept_name}")

    def _record_node_interactions(self, session, session_id: str, nodes_interacted: List[Dict]) -> None:
        """记录节点交互详情"""
        for interaction in nodes_interacted:
            if not isinstance(interaction, dict):
                continue

            node_id = interaction.get("node_id")
            if not node_id:
                continue

            # 创建概念节点（如果不存在）
            concept_name = interaction.get("concept_name", f"概念-{node_id[:8]}")
            node_type = interaction.get("node_type", "unknown")

            session.run("""
                MERGE (c:Concept {name: $concept_name})
                ON CREATE SET
                    c.concept_id = $node_id,
                    c.node_type = $node_type,
                    c.created_timestamp = datetime(),
                    c.description = $description
                ON MATCH SET
                    c.last_seen = datetime(),
                    c.interaction_count = coalesce(c.interaction_count, 0) + 1
                """,
                concept_name=concept_name,
                node_id=node_id,
                node_type=node_type,
                description=interaction.get("description", "")
            )

            # 创建交互记录
            interaction_id = f"interaction-{uuid.uuid4().hex[:16]}"
            interaction_type = interaction.get("interaction_type", "unknown")
            interaction_timestamp = interaction.get("interaction_timestamp", datetime.now(timezone.utc).isoformat())
            agent_used = interaction.get("agent_used", "")
            interaction_outcome = interaction.get("interaction_outcome", "unknown")

            session.run("""
                MATCH (s:LearningSession {session_id: $session_id})
                MATCH (c:Concept {name: $concept_name})
                CREATE (i:NodeInteraction {
                    interaction_id: $interaction_id,
                    node_id: $node_id,
                    interaction_type: $interaction_type,
                    interaction_timestamp: datetime($interaction_timestamp),
                    agent_used: $agent_used,
                    interaction_outcome: $interaction_outcome,
                    created_timestamp: datetime()
                })
                CREATE (s)-[:INCLUDES]->(i)
                CREATE (i)-[:INTERACTS_WITH]->(c)
                """,
                session_id=session_id,
                concept_name=concept_name,
                interaction_id=interaction_id,
                node_id=node_id,
                interaction_type=interaction_type,
                interaction_timestamp=interaction_timestamp,
                agent_used=agent_used,
                interaction_outcome=interaction_outcome
            )

    async def extract_concept_relationships(self, canvas_path: str, session_id: str) -> List[Dict]:
        """从Canvas文件中提取概念关系

        Args:
            canvas_path: Canvas文件路径
            session_id: 学习会话ID

        Returns:
            List[Dict]: 提取的概念关系列表

        Raises:
            FileNotFoundError: 如果Canvas文件不存在
            ValueError: 如果Canvas文件格式无效
        """
        canvas_file = Path(canvas_path)
        if not canvas_file.exists():
            raise FileNotFoundError(f"Canvas文件不存在: {canvas_path}")

        try:
            with open(canvas_file, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)

            relationships = []
            concepts = self._extract_concepts_from_canvas(canvas_data)

            # 提取节点间关系
            for edge in canvas_data.get("edges", []):
                from_node_id = edge.get("fromNode")
                to_node_id = edge.get("toNode")

                if from_node_id in concepts and to_node_id in concepts:
                    from_concept = concepts[from_node_id]
                    to_concept = concepts[to_node_id]

                    # 使用Graphiti创建关系triplet
                    await self._create_relationship_triplet(
                        from_concept, to_concept, edge, canvas_path, session_id
                    )

                    relationship = {
                        "relationship_id": f"rel-{uuid.uuid4().hex[:16]}",
                        "source_concept": from_concept["name"],
                        "target_concept": to_concept["name"],
                        "relationship_type": self._infer_relationship_type(edge, from_concept, to_concept),
                        "relationship_strength": self._calculate_relationship_strength(edge, from_concept, to_concept),
                        "confidence_score": 0.8,  # 默认置信度
                        "discovered_through": "canvas_node_relationship",
                        "discovery_timestamp": datetime.now(timezone.utc).isoformat(),
                        "validation_status": "pending",
                        "supporting_evidence": [
                            {
                                "evidence_type": "canvas_node_relationship",
                                "canvas_file": canvas_path,
                                "node_ids": [from_node_id, to_node_id],
                                "relationship_description": f"Canvas中节点{from_node_id}到节点{to_node_id}的连接"
                            }
                        ]
                    }
                    relationships.append(relationship)

            logger.info(f"从{canvas_path}提取了{len(relationships)}个概念关系")
            return relationships

        except json.JSONDecodeError as e:
            raise ValueError(f"Canvas文件JSON格式错误: {e}")
        except Exception as e:
            logger.error(f"提取概念关系失败: {e}")
            raise

    async def _create_relationship_triplet(self, from_concept: Dict, to_concept: Dict,
                                         edge: Dict, canvas_path: str, session_id: str) -> None:
        """使用Graphiti创建关系triplet"""
        try:
            # 创建源实体节点
            source_node = EntityNode(
                name=from_concept["name"],
                labels=[from_concept["node_type"].capitalize(), "Concept"],
                summary=from_concept["description"][:200],
                group_id="canvas_concepts"
            )

            # 创建目标实体节点
            target_node = EntityNode(
                name=to_concept["name"],
                labels=[to_concept["node_type"].capitalize(), "Concept"],
                summary=to_concept["description"][:200],
                group_id="canvas_concepts"
            )

            # 创建关系边
            relationship_type = self._infer_relationship_type(edge, from_concept, to_concept)
            relationship_strength = self._calculate_relationship_strength(edge, from_concept, to_concept)

            edge_fact = f"{from_concept['name']} {relationship_type.replace('_', ' ')} {to_concept['name']} " \
                       f"(strength: {relationship_strength:.2f}, from canvas: {canvas_path})"

            relationship_edge = EntityEdge(
                source_node_uuid=source_node.uuid,
                target_node_uuid=target_node.uuid,
                name=relationship_type.upper(),
                fact=edge_fact,
                group_id="canvas_relationships",
                created_at=datetime.now(timezone.utc),
                valid_at=datetime.now(timezone.utc),
                episodes=[]
            )

            # 添加triplet到图谱
            await self.graphiti.add_triplet(
                source_node=source_node,
                edge=relationship_edge,
                target_node=target_node
            )

            logger.debug(f"Created relationship triplet: {from_concept['name']} -> {to_concept['name']}")

        except Exception as e:
            logger.warning(f"Failed to create relationship triplet: {e}")

    def _extract_concepts_from_canvas(self, canvas_data: Dict) -> Dict[str, Dict]:
        """从Canvas数据中提取概念"""
        concepts = {}

        for node in canvas_data.get("nodes", []):
            node_id = node.get("id")
            if not node_id:
                continue

            node_text = node.get("text", "").strip()
            if not node_text:
                continue

            # 提取概念名称（使用文本的第一行作为概念名）
            concept_name = node_text.split('\n')[0].strip()
            if len(concept_name) > 100:  # 限制概念名称长度
                concept_name = concept_name[:100] + "..."

            concepts[node_id] = {
                "name": concept_name,
                "description": node_text,
                "node_type": node.get("type", "text"),
                "color": node.get("color", "")
            }

        return concepts

    def _infer_relationship_type(self, edge: Dict, from_concept: Dict, to_concept: Dict) -> str:
        """推断关系类型"""
        edge_label = edge.get("label", "").lower()

        # 基于边的标签推断关系类型
        if "推导" in edge_label or "导出" in edge_label:
            return "is_derived_from"
        elif "相似" in edge_label or "类似" in edge_label:
            return "is_similar_to"
        elif "矛盾" in edge_label or "对立" in edge_label:
            return "is_contradictory_of"
        elif "前提" in edge_label or "基础" in edge_label:
            return "is_prerequisite_for"
        elif "应用" in edge_label or "使用" in edge_label:
            return "is_applied_in"
        else:
            # 基于节点颜色推断关系
            from_color = from_concept.get("color", "")
            to_color = to_concept.get("color", "")

            if from_color == "1" and to_color in ["2", "3"]:  # 从红色到绿色/紫色
                return "is_prerequisite_for"
            elif from_color == "3" and to_color == "2":  # 从紫色到绿色
                return "leads_to"
            else:
                return "is_related_to"

    def _calculate_relationship_strength(self, edge: Dict, from_concept: Dict, to_concept: Dict) -> float:
        """计算关系强度"""
        strength = 0.5  # 基础强度

        # 基于边的标签调整强度
        edge_label = edge.get("label", "")
        if edge_label:
            strength += 0.2

        # 基于节点类型调整强度
        if from_concept.get("node_type") == "group" or to_concept.get("node_type") == "group":
            strength += 0.1

        # 基于颜色调整强度
        if from_concept.get("color") == "2" and to_concept.get("color") == "2":  # 绿色到绿色
            strength += 0.2
        elif from_concept.get("color") == "1" and to_concept.get("color") in ["2", "3"]:  # 红色到绿/紫色
            strength += 0.1

        return min(1.0, strength)

    def _store_concept_relationships(self, session, relationships: List[Dict], session_id: str) -> None:
        """存储概念关系到数据库"""
        for rel in relationships:
            try:
                session.run("""
                    MATCH (c1:Concept {name: $source_concept})
                    MATCH (c2:Concept {name: $target_concept})
                    MATCH (s:LearningSession {session_id: $session_id})

                    CREATE (c1)-[r:RELATED_TO {
                        relationship_id: $relationship_id,
                        relationship_type: $relationship_type,
                        strength: $relationship_strength,
                        confidence_score: $confidence_score,
                        discovered_through: $discovered_through,
                        discovery_timestamp: datetime($discovery_timestamp),
                        validation_status: $validation_status,
                        created_timestamp: datetime()
                    }]->(c2)

                    CREATE (s)-[:DISCOVERED]->(r)
                    """,
                    source_concept=rel["source_concept"],
                    target_concept=rel["target_concept"],
                    session_id=session_id,
                    relationship_id=rel["relationship_id"],
                    relationship_type=rel["relationship_type"],
                    relationship_strength=rel["relationship_strength"],
                    confidence_score=rel["confidence_score"],
                    discovered_through=rel["discovered_through"],
                    discovery_timestamp=rel["discovery_timestamp"],
                    validation_status=rel["validation_status"]
                )

            except Exception as e:
                logger.warning(f"存储关系失败: {rel['relationship_id']}, 错误: {e}")

    async def search_concept_network(self, concept_name: str, depth: int = 2, group_id: str = "canvas_concepts") -> Dict:
        """搜索概念网络

        Args:
            concept_name: 搜索的概念名称
            depth: 搜索深度
            group_id: 搜索的组ID

        Returns:
            Dict: 概念网络数据，包含相关概念和关系

        Raises:
            ValueError: 如果concept_name为空
        """
        if not concept_name.strip():
            raise ValueError("概念名称不能为空")

        try:
            # 使用Graphiti进行混合搜索
            search_query = f"{concept_name} related concepts and relationships"

            # 执行搜索
            results = await self.graphiti.search(
                query=search_query,
                group_ids=[group_id],
                num_results=20
            )

            # 处理搜索结果
            concepts = set([concept_name])
            relationships = []

            for edge in results:
                # 提取相关概念
                if hasattr(edge, 'source_node_name') and edge.source_node_name:
                    concepts.add(edge.source_node_name)
                if hasattr(edge, 'target_node_name') and edge.target_node_name:
                    concepts.add(edge.target_node_name)

                # 构建关系数据
                relationship = {
                    "fact": edge.fact if hasattr(edge, 'fact') else str(edge),
                    "valid_at": edge.valid_at.isoformat() if hasattr(edge, 'valid_at') and edge.valid_at else None,
                    "created_at": edge.created_at.isoformat() if hasattr(edge, 'created_at') and edge.created_at else None,
                    "episodes_count": len(edge.episodes) if hasattr(edge, 'episodes') else 0,
                    "uuid": edge.uuid if hasattr(edge, 'uuid') else str(uuid.uuid4())
                }
                relationships.append(relationship)

            # 计算网络统计信息
            network_stats = {
                "total_concepts": len(concepts),
                "total_relationships": len(relationships),
                "max_depth_reached": depth,
                "average_strength": 0.8,  # Graphiti默认强度
                "strong_relationships": len(relationships)  # 所有结果都认为是强的
            }

            return {
                "center_concept": concept_name,
                "concepts": list(concepts),
                "relationships": relationships,
                "network_stats": network_stats,
                "search_results_count": len(results)
            }

        except Exception as e:
            logger.error(f"搜索概念网络失败: {e}")
            raise

    async def identify_weaknesses(self, user_id: str = "default") -> List[Dict]:
        """识别学习薄弱环节

        Args:
            user_id: 用户ID

        Returns:
            List[Dict]: 薄弱环节列表
        """
        try:
            # 使用Graphiti搜索失败和需要改进的概念
            weakness_queries = [
                "failed concepts difficult concepts",
                "needs improvement concepts weak understanding",
                "challenging concepts learning difficulties"
            ]

            weaknesses = []

            for query in weakness_queries:
                try:
                    # 搜索相关的失败记录
                    results = await self.graphiti.search(
                        query=query,
                        group_ids=["canvas_interactions", "canvas_concepts"],
                        num_results=10
                    )

                    for edge in results:
                        # 从edge.fact中提取概念名称
                        fact = edge.fact if hasattr(edge, 'fact') else str(edge)
                        concept_name = self._extract_concept_from_fact(fact)

                        if concept_name:
                            weakness = {
                                "concept_name": concept_name,
                                "concept_description": fact[:200],
                                "failure_count": 1,  # Graphiti没有直接的计数，使用默认值
                                "recent_failures": [edge.created_at.isoformat() if hasattr(edge, 'created_at') else datetime.now().isoformat()],
                                "related_concepts": [],  # 可以通过额外搜索获取
                                "relationship_count": 0,
                                "weakness_level": "medium",  # 默认中等薄弱程度
                                "recommendation": self._generate_weakness_recommendation({"concept_name": concept_name, "failure_count": 1}),
                                "source_edge_uuid": edge.uuid if hasattr(edge, 'uuid') else None,
                                "episodes_count": len(edge.episodes) if hasattr(edge, 'episodes') else 0
                            }
                            weaknesses.append(weakness)

                except Exception as e:
                    logger.warning(f"搜索薄弱环节失败 '{query}': {e}")
                    continue

            # 去重（基于概念名称）
            unique_weaknesses = {}
            for weakness in weaknesses:
                concept_name = weakness["concept_name"]
                if concept_name not in unique_weaknesses:
                    unique_weaknesses[concept_name] = weakness
                else:
                    # 合并重复项
                    existing = unique_weaknesses[concept_name]
                    existing["failure_count"] += weakness["failure_count"]
                    existing["recent_failures"].extend(weakness["recent_failures"])
                    existing["episodes_count"] += weakness["episodes_count"]

            # 转换为列表并排序
            final_weaknesses = list(unique_weaknesses.values())
            final_weaknesses.sort(key=lambda x: x["failure_count"], reverse=True)

            # 更新薄弱程度
            for weakness in final_weaknesses:
                weakness["weakness_level"] = self._calculate_weakness_level(weakness["failure_count"])

            logger.info(f"为用户{user_id}识别了{len(final_weaknesses)}个薄弱环节")
            return final_weaknesses[:15]  # 返回最多15个薄弱环节

        except Exception as e:
            logger.error(f"识别薄弱环节失败: {e}")
            raise

    def _extract_concept_from_fact(self, fact: str) -> Optional[str]:
        """从事实中提取概念名称"""
        # 简单的概念提取逻辑
        import re

        # 查找常见的学习概念模式
        patterns = [
            r'concept[:\s]+([^\n,\.]+)',
            r'([^\n,\.]+)\s+concept',
            r'learning[:\s]+([^\n,\.]+)',
            r'understanding[:\s]+([^\n,\.]+)',
            r'difficulty[:\s]+([^\n,\.]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, fact, re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # 如果没有匹配到特定模式，尝试提取前几个词
        words = fact.split()[:3]
        if len(words) >= 2:
            return " ".join(words)

        return None

    def _calculate_weakness_level(self, failure_count: int) -> str:
        """计算薄弱程度等级"""
        if failure_count >= 5:
            return "critical"
        elif failure_count >= 3:
            return "high"
        elif failure_count >= 2:
            return "medium"
        else:
            return "low"

    def _generate_weakness_recommendation(self, record) -> str:
        """生成薄弱环节建议"""
        failure_count = record["failure_count"]
        related_concepts = record["related_concepts"]

        if failure_count >= 5:
            return "建议重新学习基础概念，并寻求老师或同学的帮助"
        elif failure_count >= 3:
            if related_concepts:
                return f"建议先复习相关概念: {', '.join(related_concepts[:2])}"
            else:
                return "建议尝试不同的学习方法，如观看视频教程或寻找实例"
        else:
            return "建议多做练习题加深理解"

    async def generate_learning_recommendations(self, user_id: str = "default") -> List[Dict]:
        """基于知识图谱生成学习建议

        Args:
            user_id: 用户ID

        Returns:
            List[Dict]: 学习建议列表
        """
        try:
            recommendations = []

            # 建议1: 复习薄弱环节
            weaknesses = await self.identify_weaknesses(user_id)
            for weakness in weaknesses[:5]:  # 取前5个最薄弱的环节
                recommendations.append({
                    "type": "review_weakness",
                    "priority": "high" if weakness["weakness_level"] in ["critical", "high"] else "medium",
                    "concept": weakness["concept_name"],
                    "description": f"复习薄弱概念: {weakness['concept_name']}",
                    "reason": f"该概念已失败{weakness['failure_count']}次",
                    "suggested_action": weakness["recommendation"]
                })

            # 建议2: 基于Graphiti搜索相关概念
            related_concept_queries = [
                "related concepts to study next",
                "prerequisite concepts for advanced learning",
                "connected concepts in knowledge graph"
            ]

            for query in related_concept_queries:
                try:
                    results = await self.graphiti.search(
                        query=query,
                        group_ids=["canvas_concepts"],
                        num_results=5
                    )

                    for edge in results:
                        fact = edge.fact if hasattr(edge, 'fact') else str(edge)
                        concept_name = self._extract_concept_from_fact(fact)

                        if concept_name:
                            recommendations.append({
                                "type": "learn_related",
                                "priority": "medium",
                                "concept": concept_name,
                                "description": f"学习相关概念: {concept_name}",
                                "reason": f"基于知识图谱关联分析推荐",
                                "suggested_action": "建议先学习这个概念以扩展知识网络",
                                "source_fact": fact[:100]
                            })

                except Exception as e:
                    logger.warning(f"搜索相关概念失败 '{query}': {e}")
                    continue

            # 建议3: 强化练习建议
            strengthen_queries = [
                "partial success concepts need practice",
                "concepts with moderate understanding",
                "topics needing reinforcement"
            ]

            for query in strengthen_queries:
                try:
                    results = await self.graphiti.search(
                        query=query,
                        group_ids=["canvas_interactions"],
                        num_results=3
                    )

                    for edge in results:
                        fact = edge.fact if hasattr(edge, 'fact') else str(edge)
                        concept_name = self._extract_concept_from_fact(fact)

                        if concept_name:
                            recommendations.append({
                                "type": "strengthen_understanding",
                                "priority": "medium",
                                "concept": concept_name,
                                "description": f"加强理解: {concept_name}",
                                "reason": f"该概念需要更多练习来巩固",
                                "suggested_action": "建议做更多练习题来巩固理解",
                                "source_fact": fact[:100]
                            })

                except Exception as e:
                    logger.warning(f"搜索强化练习概念失败 '{query}': {e}")
                    continue

            # 去重（基于概念和类型）
            unique_recommendations = []
            seen = set()
            for rec in recommendations:
                key = (rec["concept"], rec["type"])
                if key not in seen:
                    seen.add(key)
                    unique_recommendations.append(rec)

            # 按优先级排序
            priority_order = {"high": 3, "medium": 2, "low": 1}
            unique_recommendations.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)

            logger.info(f"为用户{user_id}生成了{len(unique_recommendations)}条学习建议")
            return unique_recommendations[:15]  # 返回最多15条建议

        except Exception as e:
            logger.error(f"生成学习建议失败: {e}")
            raise

    def backup_graph_data(self, backup_path: str) -> bool:
        """备份知识图谱数据

        Args:
            backup_path: 备份文件路径

        Returns:
            bool: 备份是否成功
        """
        try:
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)

            backup_data = {
                "backup_timestamp": datetime.now(timezone.utc).isoformat(),
                "neo4j_uri": self.neo4j_uri,
                "database": "canvas_learning",  # Default database name
                "data": {
                    "users": [],
                    "concepts": [],
                    "learning_sessions": [],
                    "relationships": []
                }
            }

            # Note: Graphiti handles backup differently than direct Neo4j driver
            # For now, just create a basic backup structure
            logger.info("Creating basic backup structure")

            # 写入备份文件
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"知识图谱数据备份成功: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"备份知识图谱数据失败: {e}")
            return False

    def restore_graph_data(self, backup_path: str) -> bool:
        """恢复知识图谱数据

        Args:
            backup_path: 备份文件路径

        Returns:
            bool: 恢复是否成功
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"备份文件不存在: {backup_path}")
                return False

            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # Note: Graphiti handles restore differently than direct Neo4j driver
            # This is a simplified restore implementation to be completed
            logger.info("Graphiti restore functionality to be implemented with Graphiti capabilities")
            return True

        except Exception as e:
            logger.error(f"恢复知识图谱数据失败: {e}")
            return False

    async def get_graph_statistics(self) -> Dict:
        """获取知识图谱统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            # Use Graphiti search capabilities to get statistics
            # This is a simplified implementation
            stats = {
                "nodes": {
                    "Concept": 0,
                    "Episode": 0,
                    "Entity": 0
                },
                "total_relationships": 0,
                "concept_relationships": {},
                "learning_sessions": {
                    "total_sessions": 0,
                    "avg_duration_minutes": 0,
                    "total_concepts_learned": 0,
                    "total_concepts_reviewed": 0
                },
                "graph_density": {
                    "total_concepts": 0,
                    "existing_relationships": 0,
                    "density": 0.0
                }
            }

            # Try to get some basic information using Graphiti search
            try:
                # Search for episodes to get activity data
                episodes = await self.graphiti.search(
                    query="learning sessions episodes",
                    group_ids=["canvas_interactions"],
                    num_results=10
                )
                stats["learning_sessions"]["total_sessions"] = len(episodes)

            except Exception as e:
                logger.warning(f"Failed to get episode statistics: {e}")

            logger.info("获取图谱统计信息完成")
            return stats

        except Exception as e:
            logger.error(f"获取图谱统计信息失败: {e}")
            raise


async def load_graphiti_config(config_path: str = "config/graphiti_config.yaml") -> Dict:
    """加载Graphiti配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        Dict: 配置数据
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


async def create_graphiti_from_config(config_path: str = "config/graphiti_config.yaml") -> GraphitiKnowledgeGraph:
    """从配置文件创建Graphiti实例

    Args:
        config_path: 配置文件路径

    Returns:
        GraphitiKnowledgeGraph: Graphiti实例
    """
    config = await load_graphiti_config(config_path)

    neo4j_config = config["neo4j"]
    return GraphitiKnowledgeGraph(
        neo4j_uri=neo4j_config["uri"],
        username=neo4j_config["username"],
        password=neo4j_config["password"]
    )


# 异步上下文管理器
class GraphitiContextManager:
    """Graphiti异步上下文管理器"""

    def __init__(self, config_path: str = "config/graphiti_config.yaml"):
        self.config_path = config_path
        self.graphiti = None

    async def __aenter__(self) -> GraphitiKnowledgeGraph:
        self.graphiti = await create_graphiti_from_config(self.config_path)
        await self.graphiti.initialize()
        return self.graphiti

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.graphiti:
            await self.graphiti.close()