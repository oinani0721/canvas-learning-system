---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-23"
status: "draft"
iteration: 5

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

compatible_with:
  prd: "v1.1.8"
  epic: ["Epic 16"]

changes_from_previous:
  - "Initial Cross-Canvas Association Architecture document"
---

# 跨Canvas关联学习架构

**版本**: v1.0.0
**创建日期**: 2025-11-23
**架构师**: Architect Agent

---

## 1. 概述

本文档定义跨Canvas关联学习系统的架构，实现不同Canvas之间的知识关联和智能推荐。

### 1.1 设计目标

- 自动发现Canvas间的知识关联
- 基于Graphiti知识图谱的语义关联
- 跨Canvas学习路径推荐
- 关联可视化展示

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                 跨Canvas关联系统                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │ Association │────▶│ Knowledge   │────▶│ Path      │ │
│  │ Detector    │     │ Graph       │     │ Recommender│ │
│  └─────────────┘     └─────────────┘     └───────────┘ │
│         │                   │                   │       │
│         ▼                   ▼                   ▼       │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │ Canvas      │     │ Graphiti    │     │ UI        │ │
│  │ Parser      │     │ + Neo4j     │     │ Visualizer│ │
│  └─────────────┘     └─────────────┘     └───────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 关联检测器

### 3.1 关联类型

```typescript
// 关联类型定义
type AssociationType =
    | 'prerequisite'      // 前置知识
    | 'related'          // 相关概念
    | 'application'      // 应用场景
    | 'comparison'       // 对比概念
    | 'part_of'          // 包含关系
    | 'example_of';      // 示例关系

interface CanvasAssociation {
    sourceCanvas: string;
    sourceNodeId: string;
    targetCanvas: string;
    targetNodeId: string;
    associationType: AssociationType;
    confidence: number;  // 0-1
    metadata: {
        sharedConcepts: string[];
        semanticSimilarity: number;
        discoveredAt: Date;
    };
}
```

### 3.2 检测算法

```python
# ✅ Verified from Graphiti Skill (SKILL.md - Section: Hybrid Search)
from graphiti_core import Graphiti
from typing import List

class AssociationDetector:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti

    async def detect_associations(
        self,
        canvas_path: str
    ) -> List[CanvasAssociation]:
        """
        检测Canvas与其他Canvas的关联
        """
        associations = []

        # 1. 获取当前Canvas的所有节点
        canvas_nodes = await self.get_canvas_nodes(canvas_path)

        for node in canvas_nodes:
            # 2. 在知识图谱中搜索相关实体
            results = await self.graphiti.search(
                query=node.content,
                num_results=10
            )

            # 3. 过滤其他Canvas的节点
            for result in results:
                if result.canvas_path != canvas_path:
                    association = self.create_association(
                        source_canvas=canvas_path,
                        source_node=node,
                        target=result
                    )
                    if association.confidence > 0.6:
                        associations.append(association)

        return associations

    async def detect_prerequisites(
        self,
        canvas_path: str
    ) -> List[CanvasAssociation]:
        """
        检测前置知识关联
        """
        # 查询知识图谱中的前置关系
        query = f"""
        MATCH (source:LearningNode)-[:PREREQUISITE]->(target:LearningNode)
        WHERE source.canvas_path = $canvas_path
        RETURN target
        """

        results = await self.graphiti._driver.execute_query(query, {
            'canvas_path': canvas_path
        })

        return self._parse_prerequisite_results(results)
```

---

## 4. 知识图谱集成

### 4.1 图谱模式

```python
# ✅ Verified from Graphiti Skill (SKILL.md - Section: Custom Entity Types)
# Neo4j节点模式

class LearningNode:
    """学习节点实体"""
    node_id: str
    canvas_path: str
    content: str
    concepts: List[str]      # 提取的概念
    embedding: List[float]   # 语义向量
    created_at: datetime

class ConceptNode:
    """概念实体"""
    concept_id: str
    name: str
    domain: str              # 学科领域
    description: str

# 关系类型
RELATIONSHIP_TYPES = [
    'CONTAINS_CONCEPT',      # 节点包含概念
    'PREREQUISITE',          # 前置知识
    'RELATED_TO',           # 相关联
    'APPLIES_TO',           # 应用于
    'CONTRASTS_WITH',       # 对比
    'PART_OF',              # 组成部分
    'EXAMPLE_OF'            # 作为示例
]
```

### 4.2 关联写入

```python
# ✅ Verified from Graphiti Skill (SKILL.md - Section: Episodes)
class AssociationWriter:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti

    async def write_association(
        self,
        association: CanvasAssociation
    ) -> None:
        """
        将关联写入知识图谱
        """
        # 记录为Episode
        episode_content = f"""
        Association detected:
        - Source: {association.sourceCanvas}#{association.sourceNodeId}
        - Target: {association.targetCanvas}#{association.targetNodeId}
        - Type: {association.associationType}
        - Confidence: {association.confidence}
        - Shared concepts: {', '.join(association.metadata['sharedConcepts'])}
        """

        await self.graphiti.add_episode(
            name=f"association_{association.sourceNodeId}_{association.targetNodeId}",
            episode_body=episode_content,
            reference_time=datetime.now()
        )

        # 创建Neo4j关系
        await self._create_relationship(association)

    async def _create_relationship(
        self,
        association: CanvasAssociation
    ) -> None:
        """在Neo4j中创建关系"""
        relationship_type = self._map_association_type(
            association.associationType
        )

        query = f"""
        MATCH (source:LearningNode {{node_id: $source_id}})
        MATCH (target:LearningNode {{node_id: $target_id}})
        MERGE (source)-[r:{relationship_type}]->(target)
        SET r.confidence = $confidence
        SET r.created_at = datetime()
        """

        await self.graphiti._driver.execute_query(query, {
            'source_id': association.sourceNodeId,
            'target_id': association.targetNodeId,
            'confidence': association.confidence
        })
```

---

## 5. 学习路径推荐

### 5.1 路径推荐器

```python
from typing import List, Optional

class PathRecommender:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti

    async def recommend_learning_path(
        self,
        start_concept: str,
        target_concept: str,
        max_depth: int = 5
    ) -> List[LearningPathStep]:
        """
        推荐从起始概念到目标概念的学习路径
        """
        # 使用图算法找最短路径
        query = """
        MATCH path = shortestPath(
            (start:ConceptNode {name: $start})-[*..%d]-(end:ConceptNode {name: $target})
        )
        RETURN path
        """ % max_depth

        result = await self.graphiti._driver.execute_query(query, {
            'start': start_concept,
            'target': target_concept
        })

        return self._parse_path(result)

    async def recommend_next_canvas(
        self,
        current_canvas: str,
        mastered_concepts: List[str]
    ) -> List[CanvasRecommendation]:
        """
        推荐下一个要学习的Canvas
        """
        # 找到当前Canvas的后续Canvas
        query = """
        MATCH (current:LearningNode {canvas_path: $canvas})
              -[:PREREQUISITE]->(next:LearningNode)
        WHERE NOT next.concept IN $mastered
        RETURN DISTINCT next.canvas_path as canvas,
               count(*) as relevance
        ORDER BY relevance DESC
        LIMIT 5
        """

        results = await self.graphiti._driver.execute_query(query, {
            'canvas': current_canvas,
            'mastered': mastered_concepts
        })

        return [
            CanvasRecommendation(
                canvas_path=r['canvas'],
                relevance_score=r['relevance']
            )
            for r in results
        ]
```

### 5.2 推荐结果

```typescript
interface LearningPathStep {
    stepNumber: number;
    canvasPath: string;
    nodeId: string;
    concept: string;
    estimatedTime: number;  // 分钟
    prerequisitesMet: boolean;
}

interface CanvasRecommendation {
    canvasPath: string;
    relevanceScore: number;
    sharedConcepts: string[];
    missingPrerequisites: string[];
    estimatedDifficulty: 'easy' | 'medium' | 'hard';
}

interface LearningPathResult {
    startConcept: string;
    targetConcept: string;
    totalSteps: number;
    estimatedTotalTime: number;
    steps: LearningPathStep[];
}
```

---

## 6. 关联可视化

### 6.1 关联图生成

```typescript
interface AssociationGraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

interface GraphNode {
    id: string;
    label: string;
    type: 'canvas' | 'concept' | 'node';
    data: {
        canvasPath?: string;
        mastered?: boolean;
        score?: number;
    };
}

interface GraphEdge {
    source: string;
    target: string;
    type: AssociationType;
    weight: number;
}

class AssociationVisualizer {
    async generateGraphData(
        centerCanvas: string,
        depth: number = 2
    ): Promise<AssociationGraphData> {
        // 获取关联数据
        const associations = await this.getAssociations(centerCanvas, depth);

        // 构建图数据
        const nodes: Map<string, GraphNode> = new Map();
        const edges: GraphEdge[] = [];

        // 添加中心Canvas
        nodes.set(centerCanvas, {
            id: centerCanvas,
            label: this.getCanvasName(centerCanvas),
            type: 'canvas',
            data: { canvasPath: centerCanvas }
        });

        // 添加关联Canvas和边
        for (const assoc of associations) {
            if (!nodes.has(assoc.targetCanvas)) {
                nodes.set(assoc.targetCanvas, {
                    id: assoc.targetCanvas,
                    label: this.getCanvasName(assoc.targetCanvas),
                    type: 'canvas',
                    data: { canvasPath: assoc.targetCanvas }
                });
            }

            edges.push({
                source: assoc.sourceCanvas,
                target: assoc.targetCanvas,
                type: assoc.associationType,
                weight: assoc.confidence
            });
        }

        return {
            nodes: Array.from(nodes.values()),
            edges
        };
    }
}
```

### 6.2 UI集成

```typescript
// Obsidian视图中的关联图
class AssociationGraphView extends ItemView {
    private graphData: AssociationGraphData | null = null;
    private canvas: HTMLCanvasElement | null = null;

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1];
        container.empty();

        // 创建canvas元素
        this.canvas = container.createEl('canvas') as HTMLCanvasElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;

        // 加载并渲染关联图
        await this.loadAndRenderGraph();
    }

    async loadAndRenderGraph(): Promise<void> {
        const currentCanvas = this.getCurrentCanvas();
        if (!currentCanvas) return;

        const visualizer = new AssociationVisualizer();
        this.graphData = await visualizer.generateGraphData(currentCanvas);

        this.renderGraph();
    }

    private renderGraph(): void {
        if (!this.graphData || !this.canvas) return;

        const ctx = this.canvas.getContext('2d')!;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 使用力导向布局
        const positions = this.calculateLayout(this.graphData);

        // 绘制边
        this.graphData.edges.forEach(edge => {
            const from = positions.get(edge.source)!;
            const to = positions.get(edge.target)!;

            ctx.beginPath();
            ctx.moveTo(from.x, from.y);
            ctx.lineTo(to.x, to.y);
            ctx.strokeStyle = this.getEdgeColor(edge.type);
            ctx.lineWidth = edge.weight * 3;
            ctx.stroke();
        });

        // 绘制节点
        this.graphData.nodes.forEach(node => {
            const pos = positions.get(node.id)!;

            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 20, 0, Math.PI * 2);
            ctx.fillStyle = this.getNodeColor(node);
            ctx.fill();

            ctx.fillStyle = '#000';
            ctx.textAlign = 'center';
            ctx.fillText(node.label, pos.x, pos.y + 35);
        });
    }
}
```

---

## 7. API接口

### 7.1 关联API

```python
# ✅ Verified from FastAPI Context7 documentation
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/associations", tags=["associations"])

@router.get("/{canvas_path}")
async def get_associations(
    canvas_path: str,
    depth: int = 2,
    detector: AssociationDetector = Depends(get_detector)
) -> List[CanvasAssociation]:
    """获取Canvas的关联"""
    return await detector.detect_associations(canvas_path)

@router.get("/path/recommend")
async def recommend_path(
    start: str,
    target: str,
    recommender: PathRecommender = Depends(get_recommender)
) -> LearningPathResult:
    """推荐学习路径"""
    return await recommender.recommend_learning_path(start, target)

@router.get("/next-canvas")
async def get_next_canvas(
    current: str,
    mastered: List[str] = Query([]),
    recommender: PathRecommender = Depends(get_recommender)
) -> List[CanvasRecommendation]:
    """推荐下一个Canvas"""
    return await recommender.recommend_next_canvas(current, mastered)

@router.get("/graph/{canvas_path}")
async def get_graph_data(
    canvas_path: str,
    depth: int = 2,
    visualizer: AssociationVisualizer = Depends(get_visualizer)
) -> AssociationGraphData:
    """获取关联图数据"""
    return await visualizer.generateGraphData(canvas_path, depth)
```

---

## 8. 配置

```yaml
# association_config.yaml
detection:
  min_confidence: 0.6
  max_associations_per_node: 10
  semantic_similarity_threshold: 0.7

recommendation:
  max_path_depth: 5
  max_recommendations: 5

visualization:
  max_display_nodes: 50
  layout_algorithm: "force_directed"

graphiti:
  search_num_results: 10
  embedding_model: "text-embedding-3-small"
```

---

## 9. 相关文档

- [Graphiti知识图谱架构](GRAPHITI-KNOWLEDGE-GRAPH-INTEGRATION-ARCHITECTURE.md)
- [3层记忆系统](COMPREHENSIVE-TECHNICAL-PLAN-3LAYER-MEMORY-AGENTIC-RAG.md)
- [Canvas操作架构](canvas-3-layer-architecture.md)

---

**文档版本**: v1.0.0
**最后更新**: 2025-11-23
**维护者**: Architect Agent
