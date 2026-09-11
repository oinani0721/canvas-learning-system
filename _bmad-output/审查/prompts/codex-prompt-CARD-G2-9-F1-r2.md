你是独立代码审查者，这是同一张卡的第二轮。仓库根目录：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance
（只读；不要连任何数据库，不要执行测试。）

## 一 背景 + 最小读取面（请只读这些）

第一轮（绑 `a78b49b7`）你给出：BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 9。
本轮 HEAD 是 `9da89fdd`。作者对第一轮的处置如下，请**独立核对处置是否恰当**，
并审查本轮**新增**的改动本身有没有引入新问题。

**本轮改动（只动两个文件）**：
1. `backend/lib/agentic_rag/clients/lancedb_client.py`
   - `_cache_tables`：把 `self.active_vault_id` 从列表推导内提到循环外（新局部变量 `owner_vault`）
   - `_owns_table` 的 docstring 追加「已知未闭合面」段落
2. `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`
   - 新增第五条门 `test_prefix_overlap_vault_is_not_isolated`，标 `xfail(strict=True)`

**最小读取面**（按此顺序，不要超出）：
- `git diff a78b49b7 9da89fdd -- . ':(exclude)_bmad-output'`（本轮增量）
- `git diff da690bf8 9da89fdd -- . ':(exclude)_bmad-output'`（整卡全量）
- `backend/lib/agentic_rag/clients/lancedb_client.py` 的 `:830-900`、`:1000-1060`
- `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` 全文（尤其末尾第五条门）
- 第一轮存档 `_bmad-output/审查/codex-review-CARD-G2-9-F1-r1.md`
- **负控与复核存档**（第一轮你提出这些记录不可核实，现列入读取面）：
  `_bmad-output/审查/evidence-g29f1/` 下的
  `g29f1-r2-negctl-*.txt`（五段负控，各含变异体 sha / `^E ` 失败行 / 跑前跑后 sha）、
  `codex-r1-followup-*.txt`（HIGH-1 与 MEDIUM-2 的实跑复核）、
  `owns-table-collision-*.txt`（新旧口径对撞 128 组合 + 验伪锚）、
  `gate1-positive-control-*.txt`（门① 正向对照的对照组）、
  `all-table-names-branches-*.txt`（两条分支等价）
- 验收单 `_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md` 的 §2.5 / §三 / §三.5 / §五

## 二 对第一轮的处置（请独立核对，不要采信）

### HIGH-1 前缀重叠 —— 作者复核后**确认成立**，但**不修**，改为加锁 + 收窄声称

作者的实跑复核（存档 `codex-r1-followup-*.txt`）：
`_owns_table('a_b_canvas_nodes','a')` 为 True；端到端 vault `a` 初始化后 `a_b_canvas_nodes`
确实消失；`sanitize_vault_id('cs 61b')` = `'cs_61b'`（本仓真实 vault id 含下划线）⇒ 可达。

作者的处置理由：这是 `resolve_table_name:790` 起的**既有**口径（原 `list_vault_tables:846` 同形），
本卡只做单点化；修它需要拿到全部 vault 列表做「最长前缀优先」，涉及三处同口径，超出本卡范围。
故：加第五条门以 `xfail(strict=True)` 锁住 + 移交 `CARD-G2-9-F2` + 三处收窄声称。

**请核对**：
- (a) 「这是既有口径、本卡未引入」这个说法对不对？请对照 `da690bf8` 的原实现确认。
- (b) `xfail(strict=True)` 这个交接方式是否恰当？该门在**缺陷被修好**时会不会真的报红？
- (c) 该门自身有没有假绿/假 xfail 的路径（例如夹具建表失败也会 xfail，与「缺陷仍在」不可区分）？
- (d) 三处收窄后的声称，是否仍有任何一处**宽于**实际证据？

### MEDIUM-2 —— 作者复核后认为「A1 对 `add_documents` 链无行为变化」

理由：`add_documents:3764` 先 `resolve_table_name`（表名恒本 vault）；且 `:3825` 的调用守卫
`table_name in self._db.table_names()` **本身是默认分页**，比 A1 改的内层判断更严 ⇒ 页外表
在守卫处即被挡下，内层不可达。实测：守卫为 False，`a_t11` 仍在，消失的表为空。
**请核对这个推理链是否完整**，特别是有没有第三条能到达 `_check_and_fix_dimension_mismatch` 的路径。

### LOW-5 / A3 —— 作者同意「AST 计数不承重」，已在验收单写明真正承重的是控制流

### LOW-10 —— 负控记录已列入本轮读取面，请据实核对（尤其「红在声称的那条断言」是否成立）

## 三 本轮新增改动的问题（请按重要性排序回答）

0. `owner_vault = self.active_vault_id` 提到循环外：在 `_cache_tables` 的执行期内，
   `active_vault_id` 有没有可能**中途改变**（ContextVar 被并发改写、循环内有 await 让出等），
   使「求值一次」与「每次求值」产生语义差异？如果会，哪种才是正确语义？
1. 第五条门标了 `xfail(strict=True)`：它会不会影响同文件其它四条门的收集或执行？
   它在 `tests/unit` 目录级跑里是否可能被计入失败集（作者称它记为 `xfailed`，不进红集）？
2. 五段负控是否各自只拆了一层？有没有哪两段实际拆的是同一层（那样其中一段就没有独立信息）？
   负控 4 与负控 5 都红在同一条断言 —— 这是否足以支持作者「两层都必须修」的结论？
3. `_owns_table` 的 docstring 现在很长且含多条历史裁定。有没有哪一句**与代码实际行为不符**？
4. 整卡（`da690bf8` → `9da89fdd`）范围内，还有没有第一轮和本轮都没提到的问题？

## 四 输出格式

逐条给出：`[BLOCKER|HIGH|MEDIUM|LOW]` + `file:line` + 一句话说明「在什么条件下会出问题」。
没有问题的维度请明确写「未发现问题」。最后给一句总体判断，并明确说明本轮是否仍存在 BLOCKER 或 HIGH。

## 五 边界

- 只读审查。不要修改任何文件，不要执行测试，不要连接任何数据库或网络服务。
- 不评 `_check_and_fix_dimension_mismatch` 的 drop 条件设计本身（既有裁定）。
- 不评 `list_vault_tables:845` 的裸表口径本身是否合理（RAG-S1 H3 既有裁定）；只评本次有没有改坏。
- 不评完整 canary 的端到端运行（本次未跑）。
- 前缀重叠的**修法设计**不在本轮范围（已移交下一张卡）；本轮只评「不修 + 加锁 + 收窄声称」这个处置是否恰当。
