# ChatGPT Deep Research — Story 2.5 错误自动提取与分类（D 方案双标签）

> **使用方式**：把整个文档复制粘贴给 ChatGPT (推荐 GPT-5 / o3 / o4-mini-high with **deep research** mode)。让它做学术 + 产业 + 改进方向的综合研究，不是简单 code review。

---

## 你的角色（System Prompt）

你是一位有 **教育心理学 + 学习科学 + AI 工程** 跨领域 15 年经验的 staff researcher。今天为一个学习辅助工具（Canvas Learning System）做 **deep research**，不是普通 code review。

任务：

1. **学术对齐度评估**：评估我们提出的 PRD 4 主类错误分类（`conceptual_confusion / procedural_error / careless_slip / metacognitive_error`）与教育心理学/学习科学经典分类框架的对齐度，引用 3-5 篇论文或主流框架（Bloom / Anderson / Ericsson / Hattie / VanLehn / Chi 等）。

2. **产业实践对比**：找 3-5 个**真实开源产品**（不要 toy projects）做"对话错误自动提取 + 分类"的 GitHub repo / 产品线（如 Khan Academy / Duolingo / Quizlet / Anki 周边 plugin / Coursera autograder / Carnegie Mellon Cognitive Tutor 系列），分析它们：
   - 用什么分类法
   - 怎么"提取"错误（LLM / heuristic / 人工标注）
   - 怎么"利用"错误（间隔复习 / 出题 / 推荐）
   - 数据 schema 长啥样

3. **D 方案评估**：我们选的 D 方案（双标签共存：legacy 4 类 + PRD 4 类，含 SUPERFICIAL 二义消解）是否合理？给出 3 个可能的弱点 + 3 个改进建议。

4. **Phase 2 路径建议**：基于 Story 2.5 已 ship 的能力（`record_error` MCP tool + 双写 + LLM 提取），下一步哪个方向最高 ROI？
   - (a) 间隔复习算法（FSRS / SM-2）+ 错误驱动的题型选择
   - (b) Hub penalty / query-aware rerank（接 Story 2.9 RAG Phase 2）
   - (c) 跨概念错误模式发现（用 Graphiti 群组 N 个 Misconception 找共同 pedagogy_type pattern）
   - (d) 其他你建议的方向

请引用具体论文 / GitHub 链接 / 产品名作为支撑，不要泛泛而谈。

---

## 项目坐标

```
项目: Canvas Learning System
仓库: https://github.com/oinani0721/canvas-learning-system
分支: worktree-feature-obsidian-hybrid-dev   ← 不是 main
HEAD: 268c9aa
Story: 2.5 错误自动提取与分类
Status: ✅ done (2026-05-04)
```

**关键文件**：
- `backend/app/graphiti/entity_types.py` — `PedagogyErrorType` + `LEGACY_TO_PEDAGOGY` + `disambiguate_superficial` + `PEDAGOGY_TYPE_TO_REMEDIES`
- `backend/app/services/error_classifier.py` — `ClassifiedError` + `ErrorClassifier.classify_with_pedagogy()`
- `backend/app/services/error_extractor.py` — `ErrorExtractor.extract_errors_from_dialog()` + `extract_and_classify()`
- `backend/app/services/error_writer.py` — `write_error_to_frontmatter()` + `write_error_to_graphiti()` + `write_error_dual()`
- `backend/app/mcp/tools/error_tools.py` — `record_error` MCP tool
- `backend/tests/integration/test_error_extraction_e2e.py` — 5 e2e tests

**测试基线**：162 pytest passed（含 Story 2.5 共 55 tests + Story 2.1 共 107 tests）

---

## Story 2.5 PRD 期望（§FR-CONV-06）

> 系统在每轮 AI 对话后自动分析对话内容，提取学习者的误解 / 错误，分类到 4 主类，并：
> 1. 写入节点 `.md` frontmatter `errors[]` 数组（本地优先）
> 2. 通过 `record_error` MCP tool 写入 Graphiti 知识图谱（跨 session 记忆）
> 3. 关联补救策略（differentiated remedy strategy）
>
> **PRD 4 主类**：
> - `conceptual_confusion` 概念混淆 → 辨析题 + 对比练习
> - `procedural_error` 推理谬误 → 找错练习 + 反例构造
> - `careless_slip` 粗心 → 同结构新题练习
> - `metacognitive_error` 元认知错误 → 迁移应用题 + 自我解释
>
> **AC #2**: 分类附带置信度 0.0-1.0，< 0.6 标记 `AMBIGUOUS`
> **AC #4**: frontmatter `errors[]` schema = `{type, description, corrected_at: null, tags}`
> **AC #6**: Graphiti 写入失败时 frontmatter 仍成功（本地优先）+ 3 次重试

---

## D 方案核心：双标签共存（不破坏现有 production data）

### 背景：分类冲突

Story 3.6（earlier sprint，已 ship for production data）已经定义了 4 类：

```python
class ErrorType(str, Enum):
    PROBLEM_FRAMING = "problem_framing"       # 破题: 审题失误, 条件遗漏
    REASONING_FALLACY = "reasoning_fallacy"   # 推理谬误: 逻辑跳步, 因果倒置
    KNOWLEDGE_GAP = "knowledge_gap"           # 知识点缺失: 缺前置知识
    SUPERFICIAL = "superficial"               # 似懂非懂: 能复述不能应用
```

**与 PRD 4 主类不匹配**：
- `careless_slip` ≈ `PROBLEM_FRAMING`（粗心审题）— 但概念不完全一致
- `procedural_error` ≈ `REASONING_FALLACY`（推理谬误）— 几乎等价
- `conceptual_confusion` ≈ `KNOWLEDGE_GAP`（缺概念≈混淆）— 部分重叠
- `metacognitive_error` 没有直接对应（拆自 `SUPERFICIAL`）
- `SUPERFICIAL` 在 PRD 4 类里被拆成 `conceptual_confusion`（表面理解→混淆）和 `metacognitive_error`（无法迁移）

### D 方案选择（vs A/B/C）

| 方案 | 做法 | 优缺 |
|---|---|---|
| A 重命名 | rename ErrorType 4 类 → PRD 4 类 | ❌ 破坏 production data |
| B 双套并存 | 保留 + 新增双套 enum + 双向映射 | ✅ 不破坏，可演化（**选这个**） |
| C 取代 | 完全用 PRD 4 类替代现有 | ❌ 重写 prompt + 全部测试 |
| D 共识扩展 | B + SUPERFICIAL 二义消解（sub_tag + 关键词） | ✅ 选 D |

### D 方案核心代码（精简版）

```python
# entity_types.py

class ErrorType(str, Enum):
    """Story 3.6 — production data 用 (legacy)."""
    PROBLEM_FRAMING = "problem_framing"
    REASONING_FALLACY = "reasoning_fallacy"
    KNOWLEDGE_GAP = "knowledge_gap"
    SUPERFICIAL = "superficial"


class PedagogyErrorType(str, Enum):
    """Story 2.5 — PRD §FR-CONV-06 教育心理学 4 主类."""
    CONCEPTUAL_CONFUSION = "conceptual_confusion"
    PROCEDURAL_ERROR = "procedural_error"
    CARELESS_SLIP = "careless_slip"
    METACOGNITIVE_ERROR = "metacognitive_error"


# 静态映射表
LEGACY_TO_PEDAGOGY: dict[ErrorType, PedagogyErrorType] = {
    ErrorType.PROBLEM_FRAMING: PedagogyErrorType.CARELESS_SLIP,
    ErrorType.REASONING_FALLACY: PedagogyErrorType.PROCEDURAL_ERROR,
    ErrorType.KNOWLEDGE_GAP: PedagogyErrorType.CONCEPTUAL_CONFUSION,
    ErrorType.SUPERFICIAL: PedagogyErrorType.CONCEPTUAL_CONFUSION,  # 默认, 可被消解
}


# SUPERFICIAL 二义消解（关键设计点）
_METACOGNITIVE_KEYWORDS = (
    "迁移", "应用", "新场景", "新情境", "transfer", "metacogniti",
    "过度自信", "过度信心", "self-explanation", "无法应用",
)
_METACOGNITIVE_SUB_TAGS = frozenset({
    "transfer_failure", "metacognitive", "overconfidence", "application_failure",
})


def disambiguate_superficial(
    error_description: str,
    sub_tags: list[str] | None = None,
) -> PedagogyErrorType:
    """SUPERFICIAL → CONCEPTUAL_CONFUSION (默认) 或 METACOGNITIVE_ERROR (有迁移信号).

    优先级:
    1. sub_tags 含 transfer_failure / metacognitive / overconfidence → METACOGNITIVE
    2. description 含 迁移/应用/新场景/transfer → METACOGNITIVE
    3. 否则默认 → CONCEPTUAL_CONFUSION
    """
    if sub_tags:
        if any(t in _METACOGNITIVE_SUB_TAGS for t in sub_tags):
            return PedagogyErrorType.METACOGNITIVE_ERROR
    text = error_description.lower()
    if any(kw in text for kw in _METACOGNITIVE_KEYWORDS):
        return PedagogyErrorType.METACOGNITIVE_ERROR
    return PedagogyErrorType.CONCEPTUAL_CONFUSION


# 补救策略 (PRD AC #3)
PEDAGOGY_TYPE_TO_REMEDIES: dict[PedagogyErrorType, list[RemedyStrategy]] = {
    PedagogyErrorType.CONCEPTUAL_CONFUSION: [RemedyStrategy.DISCRIMINATION_COMPARISON],
    PedagogyErrorType.PROCEDURAL_ERROR: [RemedyStrategy.FIND_ERROR_COUNTEREXAMPLE],
    PedagogyErrorType.CARELESS_SLIP: [RemedyStrategy.SAME_STRUCTURE_NEW_PROBLEM],
    PedagogyErrorType.METACOGNITIVE_ERROR: [RemedyStrategy.TRANSFER_SELF_EXPLANATION],
}


# ClassifiedError 数据模型 (双标签 + 双 remedy)
class ClassifiedError(BaseModel):
    legacy_type: ErrorType                      # Story 3.6 兼容
    pedagogy_type: PedagogyErrorType            # PRD §FR-CONV-06
    description: str
    context: str
    confidence: float                            # PRD AC #2
    legacy_remedy: RemedyStrategy
    pedagogy_remedies: list[RemedyStrategy]
    sub_tags: list[str]

    @property
    def is_ambiguous(self) -> bool:
        return self.confidence < 0.6  # PRD AC #2
```

### LLM 提取阶段 prompt（核心设计）

```python
EXTRACTION_PROMPT = """你是一位专业的学习诊断专家. 分析下面这段学习者与 AI 老师的对话, 找出学习者表现出的误解或错误理解.

对话内容:
{dialog_text}

提取规则:
1. 只提取学习者明显说错或理解错误的地方 (例如"学生说 X 但正确答案是 Y").
2. 如果学习者主动询问 / 表达困惑而 AI 给出正确解释, **不算错误** (这是正常学习过程).
3. AI 的纠正是错误存在的信号, 但提取的 description 应聚焦学习者的错误本身, 不包含 AI 的纠正内容.
4. 如果对话中没有明确错误, 必须返回空数组 [].
5. 每条错误用 {"description": "...", "context": "..."} 格式.

返回严格 JSON 数组 (不要 markdown 代码块, 不要解释文字):
[{"description": "学生混淆了 X 和 Y", "context": "对话第 3 轮: 学生说 X 就是 Y"}]
"""
```

---

## 写入流程（Task 4 + Task 5）

### Frontmatter（本地优先，原子写入）

```python
# error_writer.py:write_error_to_frontmatter

new_record = {
    "type": error.pedagogy_type.value,             # PRD pedagogy 标签
    "legacy_type": error.legacy_type.value,        # Story 3.6 兼容
    "description": error.description,
    "corrected_at": None,
    "tags": list(error.sub_tags),
    "remedy_strategies": [r.value for r in error.pedagogy_remedies],
    "confidence": round(error.confidence, 3),
    "created_at": datetime.now(timezone.utc).isoformat(),
}
errors_list.append(new_record)
fm_dict["errors"] = errors_list

# 原子写入: NamedTemporaryFile + os.replace
```

### Graphiti（fire-and-forget + 3 次重试）

```python
# error_writer.py:write_error_to_graphiti

GRAPHITI_TIMEOUT_S = 0.5
GRAPHITI_MAX_RETRIES = 3
GRAPHITI_RETRY_INTERVAL_S = 1.0

for attempt in range(1, GRAPHITI_MAX_RETRIES + 1):
    try:
        await asyncio.wait_for(
            memory_svc.record_knowledge_entity(
                event_type="misconception",
                content=f"Error ({pedagogy_type} / {legacy_type}): {description}",
                metadata={...双标签 + remedies + confidence},
                group_id=DEFAULT_GROUP_ID,
            ),
            timeout=GRAPHITI_TIMEOUT_S,
        )
        return True
    except asyncio.TimeoutError | Exception:
        # warning + 间隔 1s 重试
```

### MCP Tool record_error 升级（Task 5）

```python
# error_tools.py:record_error (向后兼容地扩展)

# Input 加 sub_tags 字段 (Story 2.5 SUPERFICIAL 二义消解)
class RecordErrorInput(BaseModel):
    node_id: str
    session_id: str
    error_description: str
    context: str = ""
    sub_tags: list[str] = []  # NEW

# Output 加 5 个新字段 (向后兼容地保留 Story 3.6 字段)
class RecordErrorOutput(BaseModel):
    # Story 3.6 legacy fields (保留)
    error_type: Optional[str]
    error_type_label: Optional[str]
    remedy_strategy: Optional[str]
    remedy_description: Optional[str]
    # Story 2.5 D 方案新字段
    pedagogy_type: Optional[str]                # NEW
    pedagogy_remedies: list[str]                # NEW
    confidence: Optional[float]                  # NEW
    is_ambiguous: bool                           # NEW (confidence < 0.6)
    frontmatter_written: bool                    # NEW
    graphiti_status: str                         # NEW
```

---

## 单元测试 + e2e 测试（55 tests, 全 PASS）

| 测试文件 | tests | 覆盖 |
|---|---|---|
| `test_error_classification_mapping.py` | 24 | 4 类映射 + SUPERFICIAL 二义 + remedy 完整性 + classify_with_pedagogy 集成 + 向后兼容 |
| `test_error_extractor.py` | 11 | 空消息 / 无错误 / 含错误 / 空描述过滤 / LLM 失败降级 / markdown fence 剥离 / 中文角色 / extract_and_classify 完整链路 |
| `test_error_writer.py` | 15 | frontmatter 追加/新建/原子/双标签 + Graphiti 成功/不可用/3 retry 耗尽/中途成功 + dual write fire-and-forget/skip/sync ok/sync failed |
| `test_error_extraction_e2e.py` | 5 | dialog→frontmatter+Graphiti / 无错误无写入 / record_error MCP 双标签 / low confidence ambiguous / Graphiti 失败仍 frontmatter 成功 |

---

## 你要回答的 4 个 deep research 问题

### Q1：学术对齐度评估

我们的 PRD 4 主类（`conceptual_confusion / procedural_error / careless_slip / metacognitive_error`）与以下学术框架对齐度如何？

- **Bloom's Revised Taxonomy**（Anderson & Krathwohl 2001）的 4 知识维度 / 6 认知过程
- **Knowledge Tracing** 经典研究（Corbett & Anderson 1995 BKT, Piech et al. 2015 DKT）的错误类型
- **Cognitive Tutor / ASSISTments** 系列错误模式（VanLehn 2006 cognitive task analysis）
- **Chi's Self-Explanation** 研究（Chi et al. 1989, 1994）对元认知错误的定义
- **Ericsson Deliberate Practice** 对 careless errors 的处理

我们的 4 类是否有学术支撑？哪些类需要 rename / 拆 / 合？

### Q2：产业实践对比（找 3-5 个真实开源/产品）

GitHub 或开源世界里真正在做"对话错误自动提取 + 分类"的项目（不是 toy / demo），分析它们：

候选方向（你不必全部覆盖）：
- **Khan Academy Khanmigo** 对话辅导器
- **Duolingo Max + GPT-4** 错误分析
- **CodeT / Codeium** 编程错误分类
- **OpenAI Function Calling** 教育领域应用
- **LangChain Memory + ChatGPT for Education** 类项目
- **Anki AI plugins** （间隔复习 + 错误追踪）
- **NotebookLM** 学习追踪

输出 schema 对比表：
| 项目 | 分类法 | 提取方式（LLM/heuristic/manual） | 利用方式（间隔复习/出题/推荐） | 数据 schema 简化 |

### Q3：D 方案评估

我们选了 D 方案（双标签共存 + SUPERFICIAL 二义消解 sub_tag/关键词）。你认为：

1. **3 个潜在弱点**（具体场景）
2. **3 个改进建议**（可执行的代码或设计）
3. **如果你是该项目的 senior engineer，你会选 A/B/C/D 还是其他？理由？**

特别关注：
- SUPERFICIAL 二义消解的关键词列表是否够（中文 6 + 英文 4）
- `confidence < 0.6 → AMBIGUOUS` 的 0.6 阈值合理吗？
- frontmatter `errors[]` 数组随时间无限增长怎么办？
- 双标签会不会让下游消费方（间隔复习算法、UI 展示）困惑？

### Q4：Phase 2 ROI 路径建议

Story 2.5 已 ship 后，下面 4 个方向哪个 ROI 最高？给排序 + 理由。

**(a) 间隔复习算法**：FSRS / SM-2 + `pedagogy_type` driven 题型选择（错过 conceptual_confusion 的题倾向 discrimination_comparison 出题）
**(b) Hub penalty / query-aware rerank**：Story 2.9 RAG Phase 2 的 Task 1+2，让邻居装载更智能
**(c) 跨概念错误模式发现**：用 Graphiti 群组 N 个 Misconception 找共同 pedagogy_type pattern（"用户 X 经常 conceptual_confusion 在线性代数概念上"）
**(d) Tip 自动生成**：从用户错误反推 actionable tips（`如果你下次再说 admissibility = consistency，记住...`）

或者你建议的其他方向。

---

## 输出 format

```
## Q1 — 学术对齐度

| 学术框架 | 对齐度 | 引用 | 建议 |
|---|---|---|---|
| ... | ... | (论文 + 年份 + 关键摘录) | ... |

## Q2 — 产业实践对比

| 项目 | 链接 | 分类法 | 提取方式 | 利用方式 | schema |
|---|---|---|---|---|---|
| ... |

## Q3 — D 方案评估

弱点 1: ...
弱点 2: ...
弱点 3: ...
改进 1: ...
改进 2: ...
改进 3: ...
我的方案选择: [A/B/C/D/其他] + 3 条理由

## Q4 — Phase 2 ROI 排序

1. (X) — 理由
2. (Y) — 理由
3. (Z) — 理由
4. (W) — 理由

## 总评：项目当前阶段评估

[Story 2.5 是否符合教育产品成熟度? 0-10 分 + 关键 next step]
```

---

不要客气，请给具体引用 + 链接 + schema 对比。深度研究模式启动。
