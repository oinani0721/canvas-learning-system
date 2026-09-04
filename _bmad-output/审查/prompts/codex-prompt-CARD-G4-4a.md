# CARD-G4-4a 定向复审请求（round-4 of G4-4 族，唯一一轮）

你是对抗性代码审查员。审查对象：worktree
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope`
（分支 `card/x3-vaultscope`，主干基线 `1f249b33`）上
`BATCH-2026-09-04-第十批 / CARD-G4-4a` 的**移植结果**。

## 这张卡的性质（先读，决定你该审什么）

CARD-G4-4a **不是新实现**。它把 `card/w8-scope` 上已经过你三轮审查
（round-1 REJECT → 整改 → round-2 → round-3 到顶）的 7 个 G4-4 commit，
以 `git cherry-pick -x` **逐条移植**到从主干新切的干净车道，再做四处补口，
然后 cherry-pick OBS 三提交。

因此本轮**不要重审 G4-4 的设计取舍**（那已经在 round-1~3 裁决过）。
本轮要回答的是三个移植特有的问题：

1. **移植是否等价**：cherry-pick 后的代码语义，与 `card/w8-scope@6a732e1b` 上
   被你 round-3 审过的那一版，是否一致？主干在 `1f249b33` 上已合入的 V5
   （G2-4 / G2-5）、W6、W9、W5、DEBT-8 有没有让某个前提失效？
2. **补口是否正确**：四处补口（见下）有没有引入新缺陷或过宽声明？
3. **OBS 归一是否正确**：OBS 与 G4-4 在 `rag.py` 的日志兜底口径合并得对不对？

## 只审这个 diff

```
git diff 1f249b33..HEAD -- \
  backend/app/api/v1/endpoints/rag.py \
  backend/lib/agentic_rag/nodes.py \
  backend/app/api/v1/endpoints/agents.py \
  backend/tests/api/v1/endpoints/test_rag_vault_scope_api.py \
  backend/tests/unit/test_agentic_rag_vault_scope.py \
  backend/tests/api/v1/endpoints/test_rag_four_state_api.py
```

（约 1248 insertions / 45 deletions，6 个文件。）
验收单：`_bmad-output/验收单/UAT-CARD-G4-4a-显式VaultScope-2026-09-04.md`。
移植源验收单（含 round-1~3 全记录）：
`_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md`。

## ⛔ 已裁决清单（不要重开，除非你能证明裁决前提已失效）

| # | 事项 | 裁决 |
|---|---|---|
| A1 | `test_neighbor_expansion_respects_subject_boundary` 用 `xfail(strict=True)` 而不是修复 | **已裁决**（round-3）。同 vault 跨 subject 邻居泄漏是主干既有缺陷，收口面 `lancedb_client.py` 是本卡硬禁改面，拆给 CARD-G4-4b。本卡只把 reason 改绑到 4b。按「登记类整改」评判（声明诚实性），不要按「未修复」判 BLOCKER |
| A2 | `agents.py` 的「双缺失推导 active vault」偏离总账「缺参 fail-closed」 | **已登记**（round-1 裁决②，验收单 §6.5）。本卡未改变该行为 |
| A3 | `scope_source` 走响应头 `X-Vault-Scope-Source` 而非响应体字段 | **已裁决**（round-1/2）。`schemas.py` 不在独占面 |
| A4 | 主干既有 3 条 `test_lancedb_vault_isolation.py` 红 | **基线登记**，非本卡引入。本卡已实证基线同名三条 |
| A5 | `vault_id` 必填是 breaking API | **待用户裁决 D2**，不是技术缺陷。插件 `main.ts` 对 `/rag/query` 零调用方已 grep 实证 |

## 本轮四处补口（重点扫描）

1. **(g)** `test_agentic_rag_vault_scope.py` 的 xfail `reason` 改绑 CARD-G4-4b。
   `strict=True` 不变。请核：reason 的措辞有没有比证据宽？有没有留 `skip`？
2. **(m)** 「裸表旁路」门是否假绿的实测结论。卡文担心：主干已由 CARD-G2-4
   **删除** `resolve_table_name` 的 B0.7 裸表回退，`aaecf696` 的
   `test_wikilink_neighbor_expansion_stays_in_vault` 可能因此恒真。
   本卡的结论是「该门仍活」，理由：`expand_neighbors` 内部是
   `self._db.open_table(传入名)`，**根本不调 `resolve_table_name`**，
   B0.7 与这条路径无关；变异 M6（改回裸 `"vault_notes"`）实测杀门（exit=1）。
   **请独立复核这个因果链**，特别是「M6 的击杀是否由被测防线贡献」——
   有没有可能是别的层（比如 fixture 里裸表根本没被建）造成的假杀？
3. **(k) OBS 归一**：cherry-pick OBS `78c9e6e7` 时 git **没有冲突**，但
   `rag.py` 因此一度两种口径并存：入口日志走 OBS 的模块级
   `logger = nothrow(...)` + 直调，而 `a3c41075` 新增的 scope 日志仍保留
   调用点 `try/except`。本卡删除了后者。请核：
   - 删除是否正确（OBS 在 `rag.py:300-305` 的注释里给出的「双层兜底会让注入门
     测不到包装器」这个理由，是否真的适用于 scope 日志这一行）？
   - 删除后，scope 日志抛错时是否真的**不会**变成业务失败源？
   - `test_nothrow_logging_api.py:462` 的 `record.filename == "rag.py"`
     stacklevel 断言是否仍成立？
4. **证据剔除**：按卡文 (j)，`evidence-g44` 只保留 `g44_mutations.py` +
   `mutation-run.txt`；`final-judge*.txt` / `baseline-judge*.txt` /
   三份 `codex-review-*.stderr` 未随卡入库。验收单加了「移植注」说明这些
   引用的去向，数字逐字保留在正文。请核：有没有因此产生**无法复核的声明**？

## 移植等价性的具体复核点

- 7 条 cherry-pick 中，**只有第 7 条**（`6a732e1b`）产生真冲突，落点是
  `未合卡追踪台账.md`，按卡文取 ours（台账逐字节 = 主干态）。
  请核：`git diff 1f249b33..HEAD -- <台账>` 是否为空。
- `merge-tree --write-tree` 对全部 7 条都报 rc=1，冲突全在 DEBT-8 祖先文件
  （`review_service.py` / `test_debt8*` / `evidence-debt8` / `UAT-DEBT-8`）。
  本卡的判断是：这是 merge-tree 做**整树三方合并**的产物，与 cherry-pick 取
  **单 commit patch** 无关。请核这个判断是否成立。
- 主干 `1f249b33` 相对 w8-scope 的 merge-base 多了 V5(G2-4/G2-5)/W6/W9/W5/DEBT-8。
  请核：G4-4 依赖的任何前提（`resolve_vault_scope` 语义、
  `resolve_table_name` 行为、`DEFAULT_TABLES`、`current_vault_id` 契约）
  有没有在这些合入中变化，而移植过来的代码或测试仍按旧前提写。

## 证据锚点（可直接复核）

- 裁判 1：`test_rag_vault_scope_api.py` + `test_rag_four_state_api.py` +
  `test_recommend_action.py` + `test_agents_learning_event.py`
  → **107 passed / 0 failed**（主干基线同四文件去掉前者 = 89 collected，含 1 条既有红）。
- 裁判 2：`test_agentic_rag_vault_scope.py` + `test_lancedb_vault_isolation.py`
  → **28 passed + 1 xfailed + 3 failed**（3 红 = 主干既有，同名）。
- OBS：`test_nothrow_logging_api.py` → 21 passed。
- 变异：`evidence-g44/mutation-run.txt` 尾部「移植后复跑」段，8/8 杀门
  （判据 exit==1），外部锚点三条（三文件 sha256 一致 / `git status` 空 /
  `grep MUTANT` rc=1）。
- 禁改门：`git log --format= --name-only 1f249b33..HEAD -- lancedb_client.py
  exam_service.py verification_service.py rag_service.py chat.py` → 空。
- `(h)` grep `DEFAULT_GROUP_ID|get_current_vault_id` 三文件 → 零命中。
- `(i)` f-string 日志计数：`rag.py` 7→0，`agents.py` 15→15，`nodes.py` 32→32。

## 已知并如实声明的未证明项（验收单 §「本卡未证明什么」，7 条）

subject 边界未修（归 4b）／未连真库（全 tmp_path）／未穷举 `/rag/query`
外部调用方／未证明 handler 对非预期异常类型的降级行为／`test_agents_dedup.py`
未跑（等 W4 门）／`lancedb_client.py` 零验证／主干 3 条既有红未诊断根因。

如果你认为其中任何一条**应该**在本卡范围内证明，请明确说是哪一条、依据卡文哪一段。

## 输出要求

逐条给 verdict：BLOCKER / HIGH / MEDIUM / LOW / PASS，每条附 `file:line` 证据。
不要复述代码。发现「声明比证据宽」（验收单/注释/commit message 声称了它没证明
的东西）按 HIGH 起。

**本批合并门只看一件事**：是否存在**阻断级**问题 —— 定义为：数据丢失 /
向 live vault 或 Neo4j 7691 写入 / 安全 / 指定裁判红 / 负控假绿。
请在输出**最后一行**明确给出：`阻断级 = 0` 或 `阻断级 = N（逐条列出）`。
其余等级一律登记不阻断。
