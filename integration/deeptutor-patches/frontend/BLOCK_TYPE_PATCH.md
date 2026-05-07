# BlockType Enum 扩展指南（Day 5）

DeepTutor 14 块写死在 `BlockType` Enum，加 Canvas 5 大核心需要 4 个新 block 类型。

## 风险预警

⚠️ **R1: Enum patch 触发 30+ 文件 Pydantic validation 失败**
- 缓解策略：**先加 1 个块（ORIGIN_WHITEBOARD）**，跑全部 DeepTutor 测试，验证无误后再加第 2 个。

## Step 1: 后端 Enum 扩展

**文件**: `deeptutor-fork/deeptutor/book/models.py`（约 L55-73）

```python
class BlockType(str, Enum):
    # ── 现有 14 块（不动）──
    TEXT = "text"
    CALLOUT = "callout"
    QUIZ = "quiz"
    USER_NOTE = "user_note"
    FIGURE = "figure"
    INTERACTIVE = "interactive"
    ANIMATION = "animation"
    CODE = "code"
    TIMELINE = "timeline"
    FLASH_CARDS = "flash_cards"
    DEEP_DIVE = "deep_dive"
    SECTION = "section"
    CONCEPT_GRAPH = "concept_graph"
    PLACEHOLDER = "placeholder"

    # ── Canvas 4 个新块（按依赖顺序加）──
    ORIGIN_WHITEBOARD = "origin_whiteboard"      # P0 (Day 5 先加这个)
    EXAM_WHITEBOARD = "exam_whiteboard"          # P1
    MASTERY_DASHBOARD = "mastery_dashboard"      # P0
    ERROR_CANDIDATE = "error_candidate"          # P1
```

## Step 2: 后端 Pydantic 模型

**文件**: `deeptutor-fork/deeptutor/book/schemas/blocks.py`（找到 `BlockBase` 继承点）

```python
class OriginWhiteboardBlock(BlockBase):
    """Canvas 原白板：用户思维拆解 + 7 callout + wikilink 双链。"""
    type: Literal[BlockType.ORIGIN_WHITEBOARD] = BlockType.ORIGIN_WHITEBOARD
    payload: OriginWhiteboardPayload


class OriginWhiteboardPayload(BaseModel):
    """原白板 payload：批注列表 + 双链 + 理解度。"""
    title: str
    callouts: list[CalloutItem] = []           # 7 种 callout 类型
    wikilinks: list[str] = []                  # 解析出的 [[xxx]] 目标列表
    understanding_level: float = 0.0           # 0.0-1.0
    graphiti_uuid: str | None = None           # Graphiti 节点 UUID（同步后端）
    canvas_node_id: str | None = None          # Canvas backend node_id


class CalloutItem(BaseModel):
    """单条 callout 批注。"""
    callout_type: Literal["note", "info", "warning", "error",
                          "question", "decision", "hint"]  # 现有 4 + 新增 3 = 7 种
    content: str
    line_number: int                            # 在 markdown 中的行号
    timestamp: str                              # ISO 8601
    user_understanding: float | None = None     # 0.0-1.0


class ExamWhiteboardBlock(BlockBase):
    """Canvas 检验白板：完全空白 + Active Recall + 三白板隔离不可嵌套。"""
    type: Literal[BlockType.EXAM_WHITEBOARD] = BlockType.EXAM_WHITEBOARD
    payload: ExamWhiteboardPayload


class ExamWhiteboardPayload(BaseModel):
    quiz_id: str
    canvas_pipeline_token: str                  # Canvas exam pipeline_token
    acp_context: dict                            # 5 层 ACP 上下文
    question_text: str
    student_answer: str | None = None
    score: dict | None = None                    # AutoSCORE 4 维结果
    constraint_no_nesting: Literal[True] = True  # D14 哲学底线


class MasteryDashboardBlock(BlockBase):
    """Canvas 个人记忆 Dashboard：FSRS 4 列卡片 + Day 0/3/7 schedule。"""
    type: Literal[BlockType.MASTERY_DASHBOARD] = BlockType.MASTERY_DASHBOARD
    payload: MasteryDashboardPayload


class MasteryDashboardPayload(BaseModel):
    today_due: list[MasteryCard] = []
    day_0_due: list[MasteryCard] = []
    day_3_due: list[MasteryCard] = []
    day_7_due: list[MasteryCard] = []
    last_updated: str                            # ISO 8601


class MasteryCard(BaseModel):
    node_id: str
    title: str
    bkt_mastery: float                           # 0.0-1.0
    fsrs_difficulty: float
    fsrs_stability: float
    fsrs_retrievability: float
    next_review: str                             # ISO 8601
    last_review_grade: int | None = None         # 1-4


class ErrorCandidateBlock(BlockBase):
    """Canvas 错误归因：4 类错误候选选择 dialog。"""
    type: Literal[BlockType.ERROR_CANDIDATE] = BlockType.ERROR_CANDIDATE
    payload: ErrorCandidatePayload


class ErrorCandidatePayload(BaseModel):
    error_id: str
    candidates: list[Literal["PROBLEM_FRAMING", "REASONING_FALLACY",
                             "KNOWLEDGE_GAP", "SUPERFICIAL"]]
    user_selected: str | None = None
    user_note: str | None = None                 # 用户批注内容
    related_node_id: str
```

## Step 3: 前端 BlockRenderer 扩展

**文件**: `deeptutor-fork/web/src/components/blocks/BlockRenderer.tsx`（约 L119-174）

找到现有 14 个 case 的 switch，在末尾加 4 个新 case：

```tsx
import { OriginWhiteboardBlock } from "./OriginWhiteboardBlock";
import { ExamWhiteboardBlock } from "./ExamWhiteboardBlock";
import { MasteryDashboardBlock } from "./MasteryDashboardBlock";
import { ErrorCandidateBlock } from "./ErrorCandidateBlock";

// ... existing cases ...

case BlockType.ORIGIN_WHITEBOARD:
  return <OriginWhiteboardBlock block={block} />;

case BlockType.EXAM_WHITEBOARD:
  return <ExamWhiteboardBlock block={block} />;

case BlockType.MASTERY_DASHBOARD:
  return <MasteryDashboardBlock block={block} />;

case BlockType.ERROR_CANDIDATE:
  return <ErrorCandidateBlock block={block} />;
```

## Step 4: 验证步骤

```bash
cd ~/Desktop/canvas/deeptutor-fork

# 1. 跑后端 Pydantic schema 测试
docker compose exec backend pytest tests/test_block_schemas.py -v

# 2. 跑前端 TypeScript 编译
docker compose exec frontend npm run typecheck

# 3. 启动后手动验证
docker compose up -d
# 浏览器: 创建一个 page → 插入 ORIGIN_WHITEBOARD → 看是否报错
```

## 失败回退

```bash
# 如果 Day 5 patch 触发太多 test failure：
git stash                              # 保存改动
git checkout mvp-baseline              # 回到 Day 0 baseline
# → 跳到 Day 6 决策点：选 B 路（独立包）或 C 路（混合）
```

## 依赖关系

| Block | 依赖 | 何时实装 |
|---|---|---|
| ORIGIN_WHITEBOARD | wikilink + Day 1-2 完成 | Day 5 |
| MASTERY_DASHBOARD | Canvas mastery API + Day 7 完成 | Day 7（不是 Day 5）|
| EXAM_WHITEBOARD | ACP proxy + Day 4 完成 | Day 5 末尾 |
| ERROR_CANDIDATE | EXAM_WHITEBOARD 完成 | Day 7 |
