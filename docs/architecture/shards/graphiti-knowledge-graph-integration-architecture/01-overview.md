# GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE - Part 1

**Source**: `GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md`
**Sections**: 📋 概述, 🏗️ 1. 知识图谱数据模型设计, 🏛️ 2. Graphiti集成架构, 💾 3. 记忆功能架构设计

---

---
document_type: "Architecture"
version: "1.1.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# Canvas学习系统 - Graphiti知识图谱集成架构设计

**版本**: v1.1 (LangGraph Checkpointer集成版)
**创建日期**: 2025-10-18
**最后更新**: 2025-11-11 (**NEW**: Section 8.6 与LangGraph Checkpointer的职责边界)
**作者**: Claude Code
**状态**: 技术方案设计

---


## 📋 概述

本文档详细设计了Canvas学习系统与Graphiti知识图谱的集成架构，实现Canvas节点逻辑关系的持久化记忆、学习进度的实时追踪，以及智能检验白板生成优化。

### 核心目标

1. **持久化记忆**: Canvas节点和边的逻辑关系持久化存储
2. **进度追踪**: 实时追踪学习进度和知识掌握状态
3. **智能检索**: 基于知识图谱的智能检索和推荐
4. **时间感知**: 追踪学习进展时间线和知识演化
5. **性能优化**: 确保知识图谱操作不影响Canvas系统性能

---


## 🏗️ 1. 知识图谱数据模型设计

### 1.1 实体类型定义

```python
# 知识图谱实体类型枚举
class EntityType(Enum):
    CANVAS = "canvas"                    # Canvas画布
    NODE = "node"                        # Canvas节点
    CONCEPT = "concept"                  # 知识概念
    TOPIC = "topic"                      # 知识主题
    LEARNING_SESSION = "learning_session" # 学习会话
    UNDERSTANDING_STATE = "understanding_state" # 理解状态
    AI_EXPLANATION = "ai_explanation"     # AI解释文档
    PERSONAL_UNDERSTANDING = "personal_understanding" # 个人理解
    VERIFICATION_QUESTION = "verification_question" # 检验问题
    DECOMPOSITION = "decomposition"      # 问题拆解
```

### 1.2 关系类型定义

```python
# 知识图谱关系类型枚举
class RelationType(Enum):
    # Canvas结构关系
    CONTAINS = "contains"                # Canvas包含节点
    CONNECTS_TO = "connects_to"         # 节点连接到节点
    DECOMPOSES_TO = "decomposes_to"      # 拆解关系

    # 知识语义关系
    IS_ABOUT = "is_about"                # 节点关于概念
    BELONGS_TO_TOPIC = "belongs_to_topic" # 属于主题
    PREREQUISITE_OF = "prerequisite_of"  # 前置知识
    SIMILAR_TO = "similar_to"           # 相似概念
    CONTRASTS_WITH = "contrasts_with"   # 对比概念

    # 学习进度关系
    HAS_UNDERSTANDING_STATE = "has_understanding_state" # 具有理解状态
    EVOLVES_TO = "evolves_to"           # 状态演化
    SCORED_AS = "scored_as"             # 评分结果
    NEEDS_REVIEW = "needs_review"       # 需要复习

    # 时间关系
    CREATED_IN_SESSION = "created_in_session" # 在会话中创建
    UPDATED_AT_TIME = "updated_at_time" # 更新时间
    REVIEWED_AT_TIME = "reviewed_at_time" # 复习时间
```

### 1.3 节点属性映射

```python
# Canvas节点到知识图谱的属性映射
class NodeAttributes:
    """Canvas节点属性映射到知识图谱"""

    def __init__(self, canvas_node: dict):
        self.canvas_id = canvas_node.get('id')
        self.node_type = canvas_node.get('type')
        self.text = canvas_node.get('text', '')
        self.color = canvas_node.get('color')
        self.position = {
            'x': canvas_node.get('x', 0),
            'y': canvas_node.get('y', 0)
        }
        self.size = {
            'width': canvas_node.get('width', 200),
            'height': canvas_node.get('height', 100)
        }

        # 学习相关属性
        self.learning_metadata = self._extract_learning_metadata()

    def _extract_learning_metadata(self):
        """提取学习相关元数据"""
        metadata = {
            'color_meaning': self._get_color_meaning(),
            'content_type': self._detect_content_type(),
            'complexity_score': self._calculate_complexity(),
            'learning_timestamp': time.time()
        }

        # 如果是黄色节点，提取个人理解内容
        if self.color == "6":  # 黄色节点
            metadata['personal_understanding'] = self.text
            metadata['understanding_length'] = len(self.text)
            metadata['understanding_quality_indicators'] = self._analyze_understanding_quality()

        return metadata

    def _get_color_meaning(self):
        """获取颜色含义"""
        color_meanings = {
            "1": "不理解/未通过",
            "2": "完全理解/已通过",
            "3": "似懂非懂/待检验",
            "5": "AI补充解释",
            "6": "个人理解输出区"
        }
        return color_meanings.get(self.color, "未知状态")

    def _detect_content_type(self):
        """检测内容类型"""
        text_lower = self.text.lower()
        if any(keyword in text_lower for keyword in ['什么是', '定义', 'definition']):
            return "definition"
        elif any(keyword in text_lower for keyword in ['例子', 'example', '例如']):
            return "example"
        elif any(keyword in text_lower for keyword in ['为什么', 'why', '原因']):
            return "explanation"
        elif '?' in self.text or '如何' in text_lower:
            return "question"
        else:
            return "general"

    def _calculate_complexity(self):
        """计算内容复杂度"""
        # 基于文本长度、关键词密度等计算复杂度
        text_length = len(self.text)
        technical_terms = count_technical_terms(self.text)
        return min(10, (text_length / 100) + (technical_terms * 2))

    def _analyze_understanding_quality(self):
        """分析个人理解质量（仅黄色节点）"""
        indicators = {
            'has_examples': any(keyword in self.text.lower() for keyword in ['例子', '比如', '例如', 'example']),
            'has_analogies': any(keyword in self.text.lower() for keyword in ['像', '好比', '类似于', 'like']),
            'has_personal_connection': any(keyword in self.text.lower() for keyword in ['我觉得', '我认为', '我的理解']),
            'structured_explanation': self._is_structured_explanation()
        }
        return indicators

    def _is_structured_explanation(self):
        """判断是否为结构化解释"""
        # 检查是否有逻辑连接词、分点说明等
        logical_connectors = ['因为', '所以', '首先', '其次', '然后', '最后', '一方面', '另一方面']
        return any(connector in self.text for connector in logical_connectors)
```

### 1.4 知识图谱三元组模型

```python
class KnowledgeGraphTriplet:
    """知识图谱三元组数据模型"""

    def __init__(self, subject: str, relation: str, object: str,
                 subject_type: str, object_type: str, metadata: dict = None):
        self.subject = subject
        self.relation = relation
        self.object = object
        self.subject_type = subject_type
        self.object_type = object_type
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.confidence = 1.0

    def to_graphiti_format(self):
        """转换为Graphiti格式"""
        return {
            "subject": self.subject,
            "predicate": self.relation,
            "object": self.object,
            "subject_type": self.subject_type,
            "object_type": self.object_type,
            "metadata": {
                **self.metadata,
                "timestamp": self.timestamp,
                "confidence": self.confidence
            }
        }
```

---


## 🏛️ 2. Graphiti集成架构

### 2.1 新增Layer 4: KnowledgeGraphLayer

```python
class KnowledgeGraphLayer:
    """Layer 4: 知识图谱层 - Graphiti集成"""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.graphiti = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password
        )
        self.batch_size = 50  # 批量操作大小
        self.cache = {}  # 本地缓存
        self.session_id = None

    async def initialize_session(self, canvas_path: str):
        """初始化学习会话"""
        self.session_id = f"session_{int(time.time())}_{hash(canvas_path)}"

        # 创建会话实体
        session_triplet = KnowledgeGraphTriplet(
            subject=self.session_id,
            relation=RelationType.CREATED_AT_TIME.value,
            object=str(time.time()),
            subject_type=EntityType.LEARNING_SESSION.value,
            object_type="timestamp",
            metadata={"canvas_path": canvas_path}
        )

        await self.add_triplet(session_triplet)
        return self.session_id

    async def add_triplet(self, triplet: KnowledgeGraphTriplet):
        """添加单个三元组"""
        try:
            await self.graphiti.add_triplet(
                subject=triplet.subject,
                predicate=triplet.relation,
                object=triplet.object,
                subject_type=triplet.subject_type,
                object_type=triplet.object_type,
                metadata=triplet.metadata
            )
        except Exception as e:
            logger.error(f"添加三元组失败: {e}")
            raise

    async def add_triplets_batch(self, triplets: List[KnowledgeGraphTriplet]):
        """批量添加三元组"""
        for i in range(0, len(triplets), self.batch_size):
            batch = triplets[i:i + self.batch_size]
            tasks = [self.add_triplet(triplet) for triplet in batch]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def search_knowledge(self, query: str, limit: int = 10) -> List[dict]:
        """搜索知识图谱"""
        try:
            results = await self.graphiti.search(
                query=query,
                limit=limit,
                search_type="hybrid"  # 混合搜索：语义+BM25
            )
            return results
        except Exception as e:
            logger.error(f"知识图谱搜索失败: {e}")
            return []

    async def get_node_evolution(self, node_id: str) -> List[dict]:
        """获取节点演化历史"""
        evolution_query = f"""
        MATCH (n:node {{id: "{node_id}"}})
        -[r:evolves_to]->(m:node)
        RETURN n, r, m
        ORDER BY r.timestamp
        """
        return await self.graphiti.custom_query(evolution_query)

    async def get_learning_progress(self, canvas_path: str) -> dict:
        """获取学习进度统计"""
        progress_query = f"""
        MATCH (c:canvas {{path: "{canvas_path}"}})
        -[:contains]->(n:node)
        -[:has_understanding_state]->(s:understanding_state)
        RETURN s.color_meaning as state, count(*) as count
        """
        results = await self.graphiti.custom_query(progress_query)

        # 计算进度统计
        total_nodes = sum(r['count'] for r in results)
        progress = {
            'total_nodes': total_nodes,
            'green_nodes': 0,  # 完全理解
            'yellow_nodes': 0, # 个人理解
            'purple_nodes': 0, # 似懂非懂
            'red_nodes': 0,    # 不理解
            'blue_nodes': 0    # AI解释
        }

        for result in results:
            state = result['state']
            count = result['count']
            if '完全理解' in state:
                progress['green_nodes'] = count
            elif '个人理解' in state:
                progress['yellow_nodes'] = count
            elif '似懂非懂' in state:
                progress['purple_nodes'] = count
            elif '不理解' in state:
                progress['red_nodes'] = count
            elif 'AI解释' in state:
                progress['blue_nodes'] = count

        # 计算掌握率
        if total_nodes > 0:
            progress['mastery_rate'] = (progress['green_nodes'] / total_nodes) * 100
        else:
            progress['mastery_rate'] = 0

        return progress
```

### 2.2 扩展现有架构

```python
# 扩展 Layer 1: CanvasJSONOperator
class CanvasJSONOperatorWithKG(CanvasJSONOperator):
    """带知识图谱功能的Canvas JSON操作器"""

    def __init__(self, canvas_path: str, kg_layer: KnowledgeGraphLayer = None):
        super().__init__(canvas_path)
        self.kg_layer = kg_layer
        self.canvas_id = self._generate_canvas_id()

    def _generate_canvas_id(self):
        """生成Canvas唯一ID"""
        return f"canvas_{hash(self.canvas_path)}_{int(time.time())}"

    async def sync_canvas_to_kg(self):
        """同步Canvas到知识图谱"""
        if not self.kg_layer:
            return

        # 创建Canvas实体
        canvas_triplet = KnowledgeGraphTriplet(
            subject=self.canvas_id,
            relation=RelationType.CREATED_AT_TIME.value,
            object=str(time.time()),
            subject_type=EntityType.CANVAS.value,
            object_type="timestamp",
            metadata={
                "path": self.canvas_path,
                "name": os.path.basename(self.canvas_path)
            }
        )
        await self.kg_layer.add_triplet(canvas_triplet)

        # 同步所有节点
        canvas_data = self.read_canvas()
        await self._sync_nodes_to_kg(canvas_data.get('nodes', []))
        await self._sync_edges_to_kg(canvas_data.get('edges', []))

    async def _sync_nodes_to_kg(self, nodes: List[dict]):
        """同步节点到知识图谱"""
        node_triplets = []

        for node in nodes:
            node_id = f"node_{self.canvas_id}_{node['id']}"
            node_attrs = NodeAttributes(node)

            # 创建节点实体
            node_triplet = KnowledgeGraphTriplet(
                subject=node_id,
                relation=RelationType.CREATED_AT_TIME.value,
                object=str(time.time()),
                subject_type=EntityType.NODE.value,
                object_type="timestamp",
                metadata={
                    **node_attrs.__dict__,
                    "canvas_id": self.canvas_id
                }
            )
            node_triplets.append(node_triplet)

            # Canvas包含节点关系
            contains_triplet = KnowledgeGraphTriplet(
                subject=self.canvas_id,
                relation=RelationType.CONTAINS.value,
                object=node_id,
                subject_type=EntityType.CANVAS.value,
                object_type=EntityType.NODE.value
            )
            node_triplets.append(contains_triplet)

            # 如果是黄色节点，创建个人理解实体
            if node['color'] == "6":
                understanding_id = f"understanding_{node_id}"
                understanding_triplet = KnowledgeGraphTriplet(
                    subject=understanding_id,
                    relation=RelationType.CREATED_AT_TIME.value,
                    object=str(time.time()),
                    subject_type=EntityType.PERAL_UNDERSTANDING.value,
                    object_type="timestamp",
                    metadata={
                        "content": node.get('text', ''),
                        "node_id": node_id,
                        "quality_indicators": node_attrs.learning_metadata.get('understanding_quality_indicators', {})
                    }
                )
                node_triplets.append(understanding_triplet)

                # 节点具有个人理解关系
                has_understanding_triplet = KnowledgeGraphTriplet(
                    subject=node_id,
                    relation=RelationType.HAS_UNDERSTANDING_STATE.value,
                    object=understanding_id,
                    subject_type=EntityType.NODE.value,
                    object_type=EntityType.PERAL_UNDERSTANDING.value
                )
                node_triplets.append(has_understanding_triplet)

        # 批量添加三元组
        await self.kg_layer.add_triplets_batch(node_triplets)

    async def _sync_edges_to_kg(self, edges: List[dict]):
        """同步边到知识图谱"""
        edge_triplets = []

        for edge in edges:
            from_node_id = f"node_{self.canvas_id}_{edge['fromNode']}"
            to_node_id = f"node_{self.canvas_id}_{edge['toNode']}"

            # 创建连接关系
            connect_triplet = KnowledgeGraphTriplet(
                subject=from_node_id,
                relation=RelationType.CONNECTS_TO.value,
                object=to_node_id,
                subject_type=EntityType.NODE.value,
                object_type=EntityType.NODE.value,
                metadata={
                    "fromSide": edge.get('fromSide', 'bottom'),
                    "toSide": edge.get('toSide', 'top'),
                    "canvas_id": self.canvas_id
                }
            )
            edge_triplets.append(connect_triplet)

        await self.kg_layer.add_triplets_batch(edge_triplets)
```

---


## 💾 3. 记忆功能架构设计

### 3.1 记忆系统架构

```python
class CanvasMemorySystem:
    """Canvas记忆系统 - 基于Graphiti的持久化记忆"""

    def __init__(self, kg_layer: KnowledgeGraphLayer):
        self.kg_layer = kg_layer
        self.memory_cache = {}
        self.current_session = None

    async def start_learning_session(self, canvas_path: str):
        """开始学习会话"""
        self.current_session = await self.kg_layer.initialize_session(canvas_path)

        # 记录会话开始
        memory_content = {
            "session_id": self.current_session,
            "canvas_path": canvas_path,
            "start_time": time.time(),
            "action": "start_learning_session"
        }

        await self.kg_layer.add_episode(memory_content)
        return self.current_session

    async def remember_canvas_structure(self, canvas_path: str, canvas_data: dict):
        """记忆Canvas结构"""
        structure_memory = {
            "session_id": self.current_session,
            "canvas_path": canvas_path,
            "structure": {
                "nodes_count": len(canvas_data.get('nodes', [])),
                "edges_count": len(canvas_data.get('edges', [])),
                "color_distribution": self._analyze_color_distribution(canvas_data.get('nodes', [])),
                "topics": self._extract_topics(canvas_data.get('nodes', []))
            },
            "timestamp": time.time(),
            "action": "remember_structure"
        }

        await self.kg_layer.add_episode(structure_memory)

    async def remember_learning_progress(self, canvas_path: str, node_id: str,
                                       old_color: str, new_color: str, score: dict = None):
        """记忆学习进度变化"""
        progress_memory = {
            "session_id": self.current_session,
            "canvas_path": canvas_path,
            "node_id": node_id,
            "progress_change": {
                "old_color": old_color,
                "new_color": new_color,
                "score": score,
                "improvement": self._calculate_improvement(old_color, new_color)
            },
            "timestamp": time.time(),
            "action": "progress_change"
        }

        await self.kg_layer.add_episode(progress_memory)

        # 更新知识图谱中的节点状态
        kg_node_id = f"node_{hash(canvas_path)}_{node_id}"
        await self._update_node_understanding_state(kg_node_id, new_color, score)

    async def remember_ai_explanation(self, canvas_path: str, concept: str,
                                    explanation_type: str, explanation_content: str):
        """记忆AI解释"""
        explanation_memory = {
            "session_id": self.current_session,
            "canvas_path": canvas_path,
            "explanation": {
                "concept": concept,
                "type": explanation_type,
                "content": explanation_content,
                "content_length": len(explanation_content)
            },
            "timestamp": time.time(),
            "action": "ai_explanation_generated"
        }

        await self.kg_layer.add_episode(explanation_memory)

    async def remember_verification_questions(self, canvas_path: str,
                                            node_id: str, questions: List[str]):
        """记忆检验问题"""
        questions_memory = {
            "session_id": self.current_session,
            "canvas_path": canvas_path,
            "node_id": node_id,
            "questions": questions,
            "questions_count": len(questions),
            "timestamp": time.time(),
            "action": "verification_questions_generated"
        }

        await self.kg_layer.add_episode(questions_memory)

    async def recall_canvas_history(self, canvas_path: str,
                                  time_range: tuple = None) -> List[dict]:
        """回忆Canvas历史"""
        query = f"canvas_path:{canvas_path}"
        if time_range:
            start_time, end_time = time_range
            query += f" timestamp:[{start_time} TO {end_time}]"

        episodes = await self.kg_layer.retrieve_episodes(query)
        return episodes

    async def recall_learning_insights(self, canvas_path: str) -> dict:
        """回忆学习洞察"""
        # 获取学习进度
        progress = await self.kg_layer.get_learning_progress(canvas_path)

        # 获取困难节点
        difficult_nodes = await self._get_difficult_nodes(canvas_path)

        # 获取学习模式
        learning_patterns = await self._analyze_learning_patterns(canvas_path)

        # 获取知识关联
        knowledge_connections = await self._get_knowledge_connections(canvas_path)

        return {
            "progress": progress,
            "difficult_nodes": difficult_nodes,
            "learning_patterns": learning_patterns,
            "knowledge_connections": knowledge_connections
        }

    def _analyze_color_distribution(self, nodes: List[dict]) -> dict:
        """分析颜色分布"""
        distribution = {"1": 0, "2": 0, "3": 0, "5": 0, "6": 0}
        for node in nodes:
            color = node.get('color', '')
            if color in distribution:
                distribution[color] += 1
        return distribution

    def _extract_topics(self, nodes: List[dict]) -> List[str]:
        """提取主题"""
        topics = set()
        for node in nodes:
            text = node.get('text', '')
            # 简单的主题提取逻辑
            words = text.split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    topics.add(word)
        return list(topics)[:10]  # 返回前10个主题

    def _calculate_improvement(self, old_color: str, new_color: str) -> float:
        """计算改进程度"""
        color_weights = {"1": 0, "3": 0.5, "6": 0.7, "2": 1.0}
        old_weight = color_weights.get(old_color, 0)
        new_weight = color_weights.get(new_color, 0)
        return new_weight - old_weight

    async def _update_node_understanding_state(self, node_id: str,
                                              color: str, score: dict = None):
        """更新节点理解状态"""
        state_id = f"state_{node_id}_{int(time.time())}"

        state_triplet = KnowledgeGraphTriplet(
            subject=state_id,
            relation=RelationType.CREATED_AT_TIME.value,
            object=str(time.time()),
            subject_type=EntityType.UNDERSTANDING_STATE.value,
            object_type="timestamp",
            metadata={
                "color": color,
                "color_meaning": self._get_color_meaning(color),
                "score": score or {},
                "node_id": node_id
            }
        )

        await self.kg_layer.add_triplet(state_triplet)

        # 节点具有理解状态关系
        understanding_triplet = KnowledgeGraphTriplet(
            subject=node_id,
            relation=RelationType.HAS_UNDERSTANDING_STATE.value,
            object=state_id,
            subject_type=EntityType.NODE.value,
            object_type=EntityType.UNDERSTANDING_STATE.value
        )

        await self.kg_layer.add_triplet(understanding_triplet)

    def _get_color_meaning(self, color: str) -> str:
        """获取颜色含义"""
        meanings = {
            "1": "不理解/未通过",
            "2": "完全理解/已通过",
            "3": "似懂非懂/待检验",
            "5": "AI补充解释",
            "6": "个人理解输出区"
        }
        return meanings.get(color, "未知状态")
```

### 3.2 智能记忆索引系统

```python
class MemoryIndexSystem:
    """智能记忆索引系统"""

    def __init__(self, kg_layer: KnowledgeGraphLayer):
        self.kg_layer = kg_layer
        self.index_cache = {}

    async def build_semantic_index(self, canvas_path: str):
        """构建语义索引"""
        # 获取所有节点内容
        nodes_query = f"""
        MATCH (c:canvas {{path: "{canvas_path}"}})
        -[:contains]->(n:node)
        RETURN n.id as node_id, n.text as text, n.color as color
        """

        nodes = await self.kg_layer.custom_query(nodes_query)

        # 为每个节点构建语义向量
        for node in nodes:
            await self._index_node_semantically(node)

    async def _index_node_semantically(self, node: dict):
        """为节点构建语义索引"""
        text = node.get('text', '')
        node_id = node.get('node_id')

        # 提取关键词
        keywords = self._extract_keywords(text)

        # 构建概念三元组
        for keyword in keywords:
            concept_triplet = KnowledgeGraphTriplet(
                subject=f"node_{node_id}",
                relation=RelationType.IS_ABOUT.value,
                object=f"concept_{keyword}",
                subject_type=EntityType.NODE.value,
                object_type=EntityType.CONCEPT.value,
                metadata={"relevance": self._calculate_relevance(text, keyword)}
            )

            await self.kg_layer.add_triplet(concept_triplet)

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        import jieba
        words = jieba.lcut(text)
        keywords = [word for word in words if len(word) > 2 and word.isalpha()]
        return list(set(keywords))[:5]  # 返回前5个唯一关键词

    def _calculate_relevance(self, text: str, keyword: str) -> float:
        """计算关键词相关性"""
        count = text.lower().count(keyword.lower())
        return min(1.0, count / len(text.split()))

    async def build_temporal_index(self, canvas_path: str):
        """构建时间索引"""
        # 按时间组织学习活动
        temporal_query = f"""
        MATCH (c:canvas {{path: "{canvas_path}"}})
        -[*]->(n)
        WHERE n.timestamp IS NOT NULL
        RETURN n.timestamp as timestamp, labels(n) as types, n
        ORDER BY n.timestamp
        """

        temporal_data = await self.kg_layer.custom_query(temporal_query)

        # 构建时间序列索引
        for i, item in enumerate(temporal_data):
            timestamp = item['timestamp']
            node_types = item['types']

            # 创建时间索引三元组
            time_triplet = KnowledgeGraphTriplet(
                subject=f"time_index_{int(timestamp)}",
                relation=RelationType.CREATED_AT_TIME.value,
                object=str(timestamp),
                subject_type="time_index",
                object_type="timestamp",
                metadata={
                    "sequence": i,
                    "node_types": node_types,
                    "canvas_path": canvas_path
                }
            )

            await self.kg_layer.add_triplet(time_triplet)
```

---
