#!/usr/bin/env python3
"""
Graphiti时序知识图谱集成模块 - Gemini版本

本模块实现Canvas学习系统与Graphiti时序知识图谱的集成，
使用Gemini API作为LLM服务，提供学习会话记录、概念关系提取、智能检索等功能。

Author: Canvas Learning System Team
Version: 1.0 (Gemini支持)
Created: 2025-01-22
"""

import asyncio
import json
import uuid
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from loguru import logger

# Graphiti imports
from graphiti_core import Graphiti
from graphiti_core.nodes import EntityNode, EpisodeType

# 导入Gemini客户端
from gemini_llm_client import GeminiLLMClient, GeminiEmbeddingClient


class GraphitiGeminiIntegration:
    """Graphiti时序知识图谱管理器 - Gemini版本"""

    def __init__(self, config_path: str = "config/gemini_api_config.yaml"):
        """
        初始化Graphiti-Gemini集成

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()

        # 初始化Neo4j连接
        neo4j_config = self.config["neo4j_config"]
        self.neo4j_uri = neo4j_config["uri"]
        self.username = neo4j_config["user"]
        self.password = neo4j_config["password"]

        # 初始化Gemini客户端
        self.llm_client = None
        self.embedding_client = None
        self.graphiti = None

        self._initialize_clients()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _initialize_clients(self):
        """初始化各种客户端"""
        try:
            # 初始化Gemini LLM客户端
            self.llm_client = GeminiLLMClient(self.config)
            logger.info("✅ Gemini LLM客户端初始化成功")

            # 初始化嵌入客户端
            try:
                self.embedding_client = GeminiEmbeddingClient(self.config)
                logger.info("✅ Gemini嵌入客户端初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 嵌入客户端初始化失败: {e}")
                self.embedding_client = None

            # 初始化Graphiti（基础版本，不使用外部LLM）
            self.graphiti = Graphiti(
                uri=self.neo4j_uri,
                user=self.username,
                password=self.password
            )
            logger.info("✅ Graphiti数据库连接成功")

        except Exception as e:
            logger.error(f"❌ 客户端初始化失败: {e}")
            raise

    async def initialize(self) -> None:
        """异步初始化Graphiti，建立索引和约束"""
        try:
            await self.graphiti.build_indices_and_constraints()
            logger.info("✅ Graphiti索引和约束构建成功")
        except Exception as e:
            logger.error(f"❌ 构建索引和约束失败: {e}")
            raise

    async def close(self) -> None:
        """关闭所有连接"""
        try:
            if self.graphiti:
                await self.graphiti.close()
            if self.llm_client:
                self.llm_client.close()
            if self.embedding_client:
                self.embedding_client.close()
            logger.info("✅ 所有连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭连接时出错: {e}")

    async def analyze_canvas_with_gemini(self, canvas_path: str) -> Dict:
        """
        使用Gemini分析Canvas文件

        Args:
            canvas_path: Canvas文件路径

        Returns:
            分析结果
        """
        canvas_file = Path(canvas_path)
        if not canvas_file.exists():
            raise FileNotFoundError(f"Canvas文件不存在: {canvas_path}")

        try:
            # 读取Canvas文件
            with open(canvas_file, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)

            # 提取文本内容
            canvas_text = self._extract_text_from_canvas(canvas_data)

            # 使用Gemini分析概念
            analysis_result = await self.llm_client.analyze_concepts(canvas_text)

            logger.info(f"✅ 成功分析Canvas文件: {canvas_path}")
            return {
                "canvas_path": canvas_path,
                "analysis_result": analysis_result,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Canvas分析失败: {e}")
            raise

    def _extract_text_from_canvas(self, canvas_data: Dict) -> str:
        """从Canvas数据中提取文本"""
        text_parts = []

        # 提取节点文本
        for node in canvas_data.get("nodes", []):
            if "text" in node and node["text"].strip():
                text_parts.append(node["text"])

        # 提取边的标签
        for edge in canvas_data.get("edges", []):
            if "label" in edge and edge["label"].strip():
                text_parts.append(edge["label"])

        return " ".join(text_parts)

    async def record_learning_session(self, session_data: Dict) -> str:
        """
        记录学习会话到知识图谱

        Args:
            session_data: 学习会话数据

        Returns:
            会话记录ID
        """
        # 验证必要字段
        required_fields = ["canvas_file", "session_type", "duration_minutes"]
        for field in required_fields:
            if field not in session_data:
                raise ValueError(f"缺少必要字段: {field}")

        # 生成会话ID
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

            logger.info(f"✅ 成功记录学习会话: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"❌ 记录学习会话失败: {e}")
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

Gemini-Powered Analysis:
This session leveraged Gemini AI for concept extraction and relationship analysis.
        """.strip()

        return episode_body

    async def create_concept_nodes(self, analysis_result: Dict) -> List[str]:
        """
        基于Gemini分析结果创建概念节点

        Args:
            analysis_result: Gemini分析结果

        Returns:
            创建的节点ID列表
        """
        node_ids = []
        concepts = analysis_result.get("analysis_result", {}).get("concepts", [])

        for concept in concepts:
            try:
                # 创建概念实体节点
                concept_node = EntityNode(
                    name=concept["name"],
                    labels=["Concept", "Gemini-Analyzed"],
                    summary=concept.get("description", "")[:200],
                    group_id="canvas_concepts"
                )

                # 添加到Graphiti
                node_result = await self.graphiti.add_nodes([concept_node])
                node_ids.extend(node_result)

                logger.debug(f"创建概念节点: {concept['name']}")

            except Exception as e:
                logger.warning(f"创建概念节点失败 {concept.get('name', 'unknown')}: {e}")

        logger.info(f"✅ 成功创建 {len(node_ids)} 个概念节点")
        return node_ids

    async def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        return {
            "api_provider": "Gemini",
            "model": self.config["api_config"]["model"],
            "base_url": self.config["api_config"]["base_url"],
            "status": "active" if self.llm_client else "inactive"
        }


# 便捷测试函数
async def test_gemini_integration():
    """测试Gemini集成"""
    try:
        # 初始化集成
        integration = GraphitiGeminiIntegration()
        await integration.initialize()

        # 测试Canvas分析
        test_canvas = "笔记库/离散数学/离散数学.canvas"
        if Path(test_canvas).exists():
            result = await integration.analyze_canvas_with_gemini(test_canvas)
            print(f"✅ Canvas分析测试成功: {result}")

            # 创建概念节点
            node_ids = await integration.create_concept_nodes(result)
            print(f"✅ 概念节点创建成功: {len(node_ids)} 个节点")

        # 测试学习会话记录
        session_data = {
            "canvas_file": test_canvas,
            "session_type": "test",
            "duration_minutes": 10,
            "learning_outcomes": {
                "new_concepts_learned": 2,
                "concepts_reviewed": 1
            }
        }

        session_id = await integration.record_learning_session(session_data)
        print(f"✅ 学习会话记录成功: {session_id}")

        # 获取使用统计
        stats = await integration.get_usage_stats()
        print(f"✅ 使用统计: {stats}")

        await integration.close()
        print("🎉 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_gemini_integration())