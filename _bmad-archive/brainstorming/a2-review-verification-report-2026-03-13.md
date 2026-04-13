# A2 Review Session — 独立对抗性验证报告

**日期:** 2026-03-13
**Session ID:** session-review-a2-verification-2026-03-13
**角色:** 独立验证者（NOT 决策制定者）
**验证对象:** S7-A2 Brainstorming 4 条 PENDING Decision-Review

---

## 执行摘要

对 A2 方案的 5 个核心假设进行了独立社区验证（12+ WebSearch、15+ 论文/教程、3 个代码审查），发现 **2 项重大分歧 + 1 项必须调整 + 2 项确认有效**：

| 假设 | 验证结果 | 影响 |
|------|---------|------|
| bge-reranker-v2-m3 | ✅ 条件性推荐 | 需教育场景 A/B 测试 |
| fusion/ 扩展到 6 源 | ❌ **推荐反转** | 保持 inline 代码 |
| 三阶段上下文压缩 | ❌ **推荐反转** | 改为 Top-5 截断 |
| CRAG 二级路由 | ✅ 确认合理 | 3 项小调整 |
| Prompt 模板设计 | ✅ 整体通过 | timeout 需调整 |

---

## 阶段 1: 社区验证 — 5 个核心假设

### 假设 1: bge-reranker-v2-m3 在教育中文 RAG 上的效果

**验证结论: 条件性推荐 ✅**

| 指标 | 数据 |
|------|------|
| CMTEB-R (中文 reranking) | **72.16** — 同参数量级（0.6B class）最高 |
| MIRACL (多语种) | **69.32** — 领先 jina-reranker-v3 的 66.50 |
| BEIR (英文) | 57.03 — 落后新一代模型 5-9 分 |
| FP16 VRAM | ~1-2 GB — RTX 4060 完全够用 |
| 参数量 | 278M |

**已知限制:**
- 指令感知能力缺失（FollowIR = -0.01）
- 微调优化长度仅 1024 tokens（教育长文档需分 chunk）
- 无教育领域专项 benchmark（通用训练，教育术语理解未验证）

**替代方案:**
- Qwen3-Reranker-0.6B: 指令感知但 CMTEB-R 低 0.85 分
- Qwen3-Reranker-4B: CMTEB-R 75.94 但需 8GB VRAM
- jina-reranker-v3: 延迟极低(188ms) 但中文非重点

**必须完成的验证:** 在 50-100 条真实 CS188 教育 QA 对上做 A/B 测试。

---

### 假设 2: CRAG 二级路由在 ~120 文件小知识库上的合理性

**验证结论: 确认合理 ✅（需 3 项小调整）**

**核心发现:**
1. **二元分类正确** — LangGraph 官方 + 所有社区教程均使用 binary grading（yes/no）。禁 web search 后 AMBIGUOUS 类无独立处理路径，三元退化为二元。
2. **阈值 0.85 不推荐** — 社区无 0.85 案例。教育场景 false positive 代价低（多看些材料不是坏事），应偏宽松。推荐维持 0.5 作为 score-based fallback。
3. **循环上限从 3 降为 2** — 小知识库第 3 次 rewrite 边际价值极低，额外增加 ~3s 延迟和 3 次 LLM 调用。

**发现的代码问题:**
- 当前 3 处阈值体系混乱（quality_checker 0.7 / agent_graph 0.5 / nodes.py 0.7）需统一
- `generate_answer` 缺少 retry 用尽时的"信息不足"提示

**来源:** CRAG ICLR 2024、DataCamp/Meilisearch/Analytics Vidhya 教程、RaFe EMNLP 2024、Google VentureBeat 研究

---

### 假设 3: 三阶段上下文压缩 vs 直接 Top-5 截断

**验证结论: ❌ 推荐 Top-5 截断取代三阶段压缩**

这是对 A2 方案第 2 批第 5 项的重大挑战。

| 维度 | 三阶段压缩 | Top-5 截断 |
|------|-----------|-----------|
| 质量提升 | 理论上可聚焦关键信息 | Reranker 已完成最有效筛选 |
| Lost in the Middle | 通过排列缓解 | **5 个文档天然不受影响**（效应在 15-20+ 文档才显著）|
| 公式/代码安全 | 需额外"跳过"逻辑，**无社区验证** | 天然保留完整原文 |
| 延迟 | +1-3 秒额外 LLM 调用 | 无额外延迟 |
| 实现复杂度 | 高 (prompt + 模板 + 保护逻辑) | 极低 |
| Token 预算 | 15K → 3K | 直接 ~3K (5×600) |

**核心论据:**
1. Rerank → Top-5 **本身就是最有效的 extractive compression**（NAVER 研究确认 reranker-based extractive 是所有压缩方法中效果最好的）
2. 在 2WikiMultihopQA 上，reranker-based extractive 压缩在 4.5x 压缩率下 F1 **反而提升 +7.89 分**
3. RECOMP 在复杂查询上因过度压缩导致性能下降
4. 教育笔记公式/代码密度高，压缩破坏风险 > 收益

**来源:** RECOMP ICLR 2024、ACC-RAG EMNLP 2025、PISCO NAVER、LLMLingua Microsoft、Stanford Lost-in-the-Middle 2023

---

### 假设 4: fusion/ 扩展到 6 源

**验证结论: ❌ 推荐保持 inline 代码，不激活 fusion/**

这是对 A2 DR3 融合统一方案的重大挑战。

**对抗性审查发现:**

| fusion/ 文件 | 评级 | 原因 |
|-------------|------|------|
| unified_result.py | 可复用（微修） | 加 3 个 enum 值 |
| evaluator.py | 可复用 | 与源数量无关 |
| rrf_fusion.py | 需修复 | 硬编码 3 源映射 |
| weighted_fusion.py | **需重写** | 2 源硬编码 |
| cascade_retrieval.py | **需重写** | 2 源硬编码 |
| strategy_selector.py | **需重写** | 全部签名/配置 2 源 |

**关键差异:**
- nodes.py inline 已天然支持 6 源（dict 遍历），是生产代码
- fusion/ 从未在生产中运行，是完全的死代码
- 输出格式不兼容：fusion/ 返回 `UnifiedResult` dataclass，下游消费 `List[dict]`
- 扩展成本 ~300-400 行重写 + 全链路适配 + 18 种组合测试

**发现的 bug:** nodes.py `_fuse_cascade_multi_source` 遗漏了 `vault_notes` 源（Tier 1 和 Tier 2 都没有处理它，尽管 `all_source_results` 中包含了它）。需修复约 2 行。

**推荐路径:**
- 修复 inline 代码的 vault_notes bug（~2 行）
- 保留 `evaluator.py` 和 `unified_result.py` 作为独立评估工具
- 废弃 `weighted_fusion.py`、`cascade_retrieval.py`、`strategy_selector.py`

---

### 假设 5: Prompt 模板设计

**验证结论: 整体通过 ✅（1 项必须调整）**

| 假设 | 验证结果 | 详情 |
|------|---------|------|
| Gemini response_schema 三元分类 | ✅ VALIDATED | 格式 100% 可靠，enum 天然约束输出空间 |
| 6 个 few-shot (2/类) | ✅ VALIDATED | 处于推荐上限（社区推荐 2-5 个），建议 A/B 测试 |
| Grading Notes 技术 | ✅ STRONGLY VALIDATED | Databricks 实测 96.3% 人类对齐率 |
| Langfuse Prompt Management | ✅ STRONGLY VALIDATED | 2026 最广泛采用开源 LLM 可观测平台 |
| `<student_note>` delimiter | ✅ VALIDATED | 教育场景威胁极低 |
| 30s timeout + 2 次重试 | ⚠️ **需调整** | Gemini 2.5 thinking TTFT 可达 21-31s |

**必须调整:**
- Timeout: 30s → **45s**
- 重试: 2 次 → **3 次**，加入指数退避 + jitter
- 如使用 Gemini 2.5 分类任务，考虑 `thinking_budget: 0` 禁用 thinking

**来源:** Google 官方文档、Databricks blog、OWASP、Artificial Analysis benchmark

---

## 阶段 2: 严格验收标准 — 8 项具体化

### AC-A2-1: 上下文 Token 控制

> **原标准:** 15K → ≤3K tokens
> **修正:** 基于社区验证，改为 "Rerank → Top-5 后上下文 ≤ 3500 tokens"

| 条件 | 判定 |
|------|------|
| **PASS** | 95% 的测试查询，rerank 后 top-5 chunks 总 token 数 ≤ 3500 (tiktoken cl100k_base) |
| **PARTIAL** | 80-95% 的查询满足 ≤ 3500 |
| **FAIL** | <80% 的查询满足 ≤ 3500 |

**前提条件:** A1 chunking 策略已实施，chunk size ~512-768 tokens。
**测量工具:** tiktoken cl100k_base 编码器。
**注意:** 如果 A1 chunk size > 700 tokens，5 chunks 可能超 3500，需调整 top-K 为 4 或减小 chunk size。

---

### AC-A2-2: Faithfulness（回答忠实度）

> **原标准:** Faithfulness ≥ 0.85
> **修正:** 维持 ≥ 0.85，但明确评估方法和测试集要求

| 条件 | 判定 |
|------|------|
| **PASS** | 平均 Faithfulness ≥ 0.85 **且** 单个查询最低 ≥ 0.60 |
| **PARTIAL** | 平均 0.75-0.85 或个别查询 < 0.60 但 ≤ 2 个 |
| **FAIL** | 平均 < 0.75 或 > 2 个查询 < 0.60 |

**评估方法:** DeepEval FaithfulnessMetric（已在代码中有引用），基于 NLI 的 claim-level 验证。
**测试集:** 最少 30 个查询（统计显著性），覆盖 6 种 query 类型。
**前提条件:** 需要 Session C 的 Golden Test Set。

---

### AC-A2-3: Reranker MRR 提升

> **原标准:** MRR 提升 ≥ +0.10
> **修正:** 明确基线定义和测量方法

| 条件 | 判定 |
|------|------|
| **PASS** | MRR@5 (reranked) - MRR@5 (original) ≥ +0.10 |
| **PARTIAL** | 提升 +0.05 到 +0.10 |
| **FAIL** | 提升 < +0.05 或回归 |

**基线:** 当前无 reranking（rerank 函数是 no-op，直接返回原始排序）= 原始检索排序的 MRR@5。
**测试集:** 最少 20 个查询 × 人工标注前 10 个结果的相关性（binary: relevant/irrelevant）。
**前提条件:** 需要人工标注的 relevance judgments（可作为 Session C Golden Test Set 的一部分）。

---

### AC-A2-4: CRAG 触发率

> **原标准:** CRAG 触发率 < 20%
> **修正:** 限定在"笔记覆盖的查询"上测量

| 条件 | 判定 |
|------|------|
| **PASS** | 在笔记覆盖的查询中，CRAG rewrite 触发率 < 20% |
| **PARTIAL** | 触发率 20-30% |
| **FAIL** | 触发率 > 30% |

**测量方法:** 对 50 个已知笔记覆盖的查询（答案确定存在于 CS188 笔记中），统计 `route_after_grading → rewrite_query` 的比例。
**排除:** 笔记不覆盖的查询（如"什么是 Bayes Nets 的 d-separation？"）不计入触发率，因为这些查询 CRAG 触发是正确行为。
**注意:** 如果 reranking 质量好，触发率应显著低于 20%。

---

### AC-A2-5: Reranker 延迟

> **原标准:** Reranker 延迟 < 500ms
> **修正:** 区分冷启动和热启动

| 场景 | PASS | PARTIAL | FAIL |
|------|------|---------|------|
| **热启动** (warmup 后) | < 500ms | 500-800ms | > 800ms |
| **冷启动** (首次推理) | < 2000ms | 2000-3000ms | > 3000ms |

**测量条件:**
- 输入: 10-20 个 documents（实际 rerank 输入量）
- GPU: RTX 4060 (8GB VRAM), FP16
- 每个 document ~200-500 tokens
- 测量 5 次取中位数

**warmup 要求:** 服务启动时执行 1 次 dummy 推理以触发模型加载和 CUDA 初始化。

---

### AC-A2-6: Top-5 截断后回答质量

> **原标准:** 压缩后质量保持 ≥ 90%
> **修正:** 改为 "Top-5 截断 vs 全量上下文的质量对比"

| 条件 | 判定 |
|------|------|
| **PASS** | Top-5 回答质量 ÷ 全量回答质量 ≥ 0.90（LLM-judge 1-5 分制）|
| **PARTIAL** | 比值 0.80-0.90 |
| **FAIL** | 比值 < 0.80 |

**测量方法:**
1. 对 10 个测试查询，分别用 top-5 和全量（15-20 个 chunks）上下文生成回答
2. 由 LLM-judge 对每对回答打分（1-5 分，维度：准确性、完整性、教育价值）
3. 计算 top-5 平均分 ÷ 全量平均分

**预期:** 基于社区研究（NAVER extractive compression +7.89 F1），top-5 截断质量可能**等于甚至超过**全量传入（因为去除了噪声）。

---

### AC-A2-7: CRAG 循环终止

> **原标准:** CRAG 循环终止（max 2 次，无死循环）
> **修正:** 维持，增加对抗性场景

| 条件 | 判定 |
|------|------|
| **PASS** | 100% 的查询在 2 次循环内终止 **且** retry 用尽时正确降级 |
| **FAIL** | 任何查询超过 2 次循环 **或** retry 用尽时未降级/死循环 |

**必须测试的对抗性场景:**
1. 完全无关查询（"今天天气怎么样？"）
2. 笔记中部分相关但不足的查询
3. 空检索结果（所有源都返回空）
4. Rewrite 后仍然无结果
5. LLM grading 服务不可用（fallback 路径）

**降级验证:** 当 retry 用尽且 relevant_documents 为空时，generate_answer 必须包含"信息不足"提示。

---

### AC-A2-8: 融合无回归

> **原标准:** 融合统一后无回归
> **修正:** 基于 code review 发现，改为 "inline 代码修复后无回归"

| 条件 | 判定 |
|------|------|
| **PASS** | 修复 vault_notes bug 后，对 20 个固定查询，**Top-3 结果不变**（允许 4-10 名微调）|
| **PARTIAL** | Top-3 中有 1-2 个查询结果变化，但变化合理（vault_notes 被正确纳入）|
| **FAIL** | Top-3 中 > 2 个查询结果不合理变化 |

**测量方法:**
1. 修复前：记录 20 个查询的完整 top-10 结果（含 source、rank、score）
2. 修复后：重复相同查询
3. 对比 top-3 结果的一致性
4. 预期变化：vault_notes 源被纳入后可能改善某些查询的结果

**注意:** A2 原方案是"nodes.py 改为调用 fusion/"，但 code review 建议反转为保持 inline。如果最终决策改为保持 inline，此验收标准仅验证 vault_notes bug 修复的影响。

---

## 阶段 3: 测试用例集 — 40 个用例

### 测试数据来源
- **CS188 Vault:** C:\Users\Heishing\Desktop\spring course 2026\CS188
- **内容:** UC Berkeley CS188 (AI) 课程笔记，涵盖 Search, CSPs, Game Trees, MDPs, RL
- **特征:** 中英文混合、数学公式、代码片段、图片引用、视频转录
- **文件数:** ~120 个 markdown 文件

### 查询类别定义

| 类别 | 说明 | 用于测试 |
|------|------|---------|
| **C1: 标准覆盖查询** | 笔记中有明确答案 | AC 1-6 |
| **C2: 跨文件查询** | 需要融合多个来源 | AC 3, 6, 8 |
| **C3: 模糊查询** | 不精确或过于宽泛 | AC 4, 7 |
| **C4: 无答案查询** | 笔记中没有答案 | AC 4, 7 |
| **C5: 中英混合查询** | 跨语言检索 | AC 1-3 |
| **C6: 公式/代码查询** | 包含数学或代码内容 | AC 1, 6 |

### 测试用例（按验收标准分组）

#### AC-A2-1 测试用例（上下文 Token 控制）

| # | 查询 | 类别 | 预期 |
|---|------|------|------|
| 1.1 | "什么是 A* 搜索？" | C1 | top-5 chunks ≤ 3500 tokens |
| 1.2 | "Explain the minimax algorithm and alpha-beta pruning" | C2 | 跨 lecture 7-8，token 控制 |
| 1.3 | "V*(s) 的 Bellman equation 递归公式" | C6 | 含公式的 chunks，检查 token 计数 |
| 1.4 | "对比所有搜索算法的时间复杂度" | C2 | 跨多 lecture，可能需要多 chunks |
| 1.5 | "reinforcement learning 的 exploration vs exploitation" | C5 | 中英混合，检查 chunk 大小 |

#### AC-A2-2 测试用例（Faithfulness）

| # | 查询 | 类别 | 预期 |
|---|------|------|------|
| 2.1 | "A* 搜索的最优性条件是什么？" | C1 | 回答应完全基于 clarification 文档，无幻觉 |
| 2.2 | "CSP 中 forward checking 和 arc consistency 的区别" | C2 | 应引用 lecture 5-6 内容 |
| 2.3 | "什么是 TD learning？" | C1 | 应基于 lecture 11-12，不编造公式 |
| 2.4 | "Deep Blue 和 AlphaGo 的策略有什么不同？" | C1 | lecture 7 有明确内容 |
| 2.5 | "解释 policy iteration 和 value iteration 的收敛性" | C6 | 涉及公式，faithfulness 对公式特别敏感 |

#### AC-A2-3 测试用例（MRR 提升）

| # | 查询 | 类别 | Golden Relevant Docs |
|---|------|------|---------------------|
| 3.1 | "admissible heuristic 的定义和例子" | C5 | clarification-bccdf951-161852.md |
| 3.2 | "minimax 算法的伪代码" | C1 | lecture 7.md |
| 3.3 | "Q-learning 的更新规则" | C6 | lecture 12, clarification 文件 |
| 3.4 | "CSP 的 backtracking search" | C1 | lecture 5.md |
| 3.5 | "MDP discount factor γ 的作用" | C5 | lecture 9-10, clarification 文件 |

#### AC-A2-4 测试用例（CRAG 触发率）

| # | 查询 | 类别 | 预期触发？ |
|---|------|------|----------|
| 4.1 | "什么是 A* 搜索？" | C1 | 否（笔记有详细覆盖）|
| 4.2 | "UCS 的时间复杂度" | C1 | 否 |
| 4.3 | "Bayes Nets 的 d-separation" | C4 | 是（不在考试范围，笔记薄）|
| 4.4 | "如何用 Python 实现 minimax？" | C4 | 可能（取决于笔记覆盖度）|
| 4.5 | "alpha-beta 剪枝能剪掉多少节点？" | C1 | 否（lecture 7 有覆盖）|

#### AC-A2-5 测试用例（Reranker 延迟）

| # | 场景 | 输入 | 测量 |
|---|------|------|------|
| 5.1 | 热启动，10 docs | 标准长度 chunks | 中位数 latency |
| 5.2 | 热启动，20 docs | 标准长度 chunks | 中位数 latency |
| 5.3 | 冷启动，10 docs | 标准长度 chunks | 首次 latency |
| 5.4 | 热启动，10 docs | 长 chunks (~800 tokens each) | 中位数 latency |
| 5.5 | 热启动，5 docs | 短 chunks (~200 tokens each) | 中位数 latency |

#### AC-A2-6 测试用例（Top-5 截断质量）

| # | 查询 | 类别 | 比较 |
|---|------|------|------|
| 6.1 | "详细解释 A* 搜索的工作原理" | C1 | top-5 vs 全量 |
| 6.2 | "对比 BFS、DFS、UCS、A* 的优缺点" | C2 | top-5 vs 全量（跨多 lecture）|
| 6.3 | "MDP 的 Bellman optimality equation 推导" | C6 | top-5 vs 全量（含公式）|
| 6.4 | "Game Tree 中 expectimax 的应用场景" | C1 | top-5 vs 全量 |
| 6.5 | "RL 中 model-based 和 model-free 的区别" | C2 | top-5 vs 全量 |

#### AC-A2-7 测试用例（CRAG 循环终止）

| # | 查询 | 类别 | 预期行为 |
|---|------|------|---------|
| 7.1 | "今天天气怎么样？" | C4 | 2 次循环内终止 + 信息不足提示 |
| 7.2 | "量子计算在 AI 中的应用" | C4 | 2 次循环内终止 + 信息不足提示 |
| 7.3 | "那个用树的搜索算法" | C3 | 可能 rewrite 后找到 DFS/BFS |
| 7.4 | "" (空查询) | C3 | 直接终止，不进入循环 |
| 7.5 | "search but not A* and not BFS" | C3 | 可能 rewrite 后找到 DFS/UCS |

#### AC-A2-8 测试用例（融合无回归）

| # | 查询 | 预期检查 |
|---|------|---------|
| 8.1 | "A* 搜索" | top-3 不变 |
| 8.2 | "CSP arc consistency" | top-3 不变 |
| 8.3 | "minimax alpha-beta" | top-3 不变 |
| 8.4 | "Q-learning update" | top-3 不变 |
| 8.5 | "policy iteration" | vault_notes 源被正确纳入后的影响 |

---

## 阶段 4: 对 A2 Decision-Review 的验证结论

### DR1: 完整实施方案（三批九项）

| 项目 | 验证结果 | 调整建议 |
|------|---------|---------|
| 1. Reranking 重写 | ✅ 确认 | bge-reranker-v2-m3 条件性推荐，需教育 A/B 测试 |
| 2. CRAG 激活 | ✅ 确认（小调整） | 阈值 0.85→0.5, MAX_RETRIES 3→2, 加信息不足提示 |
| 3. 融合统一 | ❌ **推荐反转** | 保持 inline 代码，修复 vault_notes bug，不激活 fusion/ |
| 4. Mastery-as-context | ✅ 确认 | 轻量操作，无需验证 |
| 5. 上下文压缩 | ❌ **推荐反转** | 改为直接 Top-5 截断，不实施三阶段压缩 |
| 6. 学生查询上下文化 | ✅ 确认 | 独立于压缩方案 |
| 7. Mastery 教学过滤层 | ✅ 确认 | 独立于压缩方案 |
| 8. Phase 迁移 | ✅ 确认 | 渐进式迁移策略合理 |
| 9. 先修知识检测 | ✅ 确认 | 中期优先级合理 |

### DR2: 补充发现 5 项

| 项目 | 验证结果 |
|------|---------|
| VRAM ~1.8GB | ✅ 确认（社区数据 1-2GB）|
| warmup 机制 | ✅ 确认（必须）|
| CRAG 二级路由 | ✅ 确认 |
| rewrite 并行检索 | ✅ 确认（RaFe EMNLP 2024 支持）|
| Langfuse 集成 | ✅ STRONGLY VALIDATED |

### DR3: 七大 Gap 实施方案

| Gap | 验证结果 | 调整 |
|-----|---------|------|
| lazy singleton reranker | ✅ 确认 | — |
| 共享 query_rewriter.py | ✅ 确认 | — |
| fusion 扩展 6 源 | ❌ **反转** | 保持 inline，修复 vault_notes bug |
| State 4 字段 | ✅ 确认 | — |
| 接口 no-op fallback | ✅ 确认 | — |
| 5 个 prompt 模板 | ✅ 确认 | timeout 调整 |
| 8 项验收标准 | ✅ 已具体化 | 见阶段 2 |

### DR4: 冲突解决 + Prompt 规则

| 项目 | 验证结果 | 调整 |
|------|---------|------|
| config 读取统一 | ✅ 确认 | — |
| mastery 提前到第一批 | ✅ 确认 | — |
| CR 归 A1 | ✅ 确认 | — |
| Langfuse 管理 | ✅ STRONGLY VALIDATED | — |
| Gemini response_schema | ✅ VALIDATED | — |
| 6 个 few-shot | ✅ VALIDATED | 建议 A/B 测试 4 vs 6 |
| 30s timeout | ⚠️ 需调整 | **45s + 3 retries + 指数退避** |
| delimiter 防注入 | ✅ VALIDATED | 教育场景足够 |

---

## 关键分歧汇总（需决策 session 确认）

### 分歧 1: fusion/ 扩展 → 保持 inline

**A2 原方案:** 扩展 fusion/ 到 6 源，nodes.py 改为调用 fusion/
**审查建议:** 保持 nodes.py inline 代码（已支持 6 源），仅修复 vault_notes bug
**分歧原因:** fusion/ 有 3 个文件需完全重写，输出格式不兼容，成本远大于收益
**影响:** 减少 ~300-400 行改动，降低回归风险

### 分歧 2: 三阶段压缩 → Top-5 截断

**A2 原方案:** 三阶段压缩（信号提取→证据排列→约束模板）15K→3K
**审查建议:** 直接 Rerank → Top-5 截断 (~3K tokens)
**分歧原因:** Rerank→Top-5 本身是最有效的 extractive compression，5 个文档不受 Lost-in-the-Middle，额外压缩对公式/代码有风险
**影响:** 简化第 2 批实施，去除 prompt 模板 3（context_compression）

---

## 待执行（A2 实施完成后）

- [ ] 阶段 4 执行验证：逐条运行 40 个测试用例
- [ ] 记录每项 PASS / FAIL / PARTIAL 结果
- [ ] 对 FAIL 项分析根因并提出修复建议
- [ ] 记录 [Test] 结果到 Graphiti canvas-dev

---

## Graphiti 记录清单

| 已记录 | 前缀 | 标题 |
|--------|------|------|
| ✅ | [Session-Start] | A2 Review Session — 独立对抗性验证 |
| ✅ | [Code-Review] | fusion/ 扩展对抗性审查 — 推荐反转为 inline 路径 |
| ✅ | [Research-Tech] | bge-reranker-v2-m3 社区验证 — 条件性推荐 |
| ✅ | [Research-Tech] | 上下文压缩社区验证 — 推荐 Top-5 截断取代三阶段压缩 |
| ✅ | [Research-Tech] | Prompt 模板假设社区验证 — 整体通过，timeout 需调整 |
| ✅ | [Research-Tech] | CRAG 二级路由社区验证 — 确认二元分类+阈值调整+循环降为2 |
| 待记录 | [Acceptance-Criteria] | A2 八项验收标准具体化 |
