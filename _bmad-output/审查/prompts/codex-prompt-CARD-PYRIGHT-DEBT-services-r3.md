# 独立复核请求 — CARD-PYRIGHT-DEBT-services（阶段 1，round-3 · MEDIUM 整改复审）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc`
分支 `card/u1-pyright-svc`，基线 `da690bf8`，本轮审 SHA **`82d15aac`**。

round-2 你的总判是「**BLOCKER=0、HIGH=0**」，但指出 MEDIUM 未闭环。**我采信并继续整改**，
所以按规则再送一轮。本轮请复核这批整改。

### 请只读以下内容

1. `git diff 958f20a3 82d15aac -- backend/app/services` —— **本轮整改的全部改动**，最重要。
2. `_bmad-output/审查/evidence-pyright-svc/r2-fix-message-verification-*.txt` —— 异常消息的三态对照。
3. `_bmad-output/审查/evidence-pyright-svc/assert-message-leak-audit-*.txt` —— 我做的全量审计。
4. 需要看累计改动时：`git diff da690bf8 82d15aac -- backend/app/services`。

---

## 二 本轮整改说明

### MEDIUM-1（r2）：剩余 assert 有可观察的返回内容变化

**你是对的，而且比你点名的更多。** 你点了 `autoscore.py:310`、`question_generator.py:778`、
`scoring_faithfulness.py:269/:351`、`conversation_distiller.py:319`。

我按你的定性做了**全量 AST 审计**（`assert-message-leak-audit-*.txt`）：
对每个新增 assert 找出其所在 `try` 的全部 handler，检查 handler 体内是否对异常变量做格式化
（`{e}` / `str(e)` / `%s % e` / `, e)`），并区分「写进返回值」与「仅写日志」。
结果：**12 个 (文件, assert, handler) 组合受影响，涉及 9 个 assert 位置**：

`autoscore.py`(×2)、`error_classifier.py`(×2)、`scoring_faithfulness.py`(×2)、
`question_generator.py`、`exam_service_ext.py`、`rag_service.py`、`canvas_projection_sync.py`

**整改**：这 9 个位置的 assert 全部删除，改为在使用点 `cast`（运行期 no-op）。
共删掉 **10 个** assert（`error_classifier` 的两处各含 1 个），新增 assert 数 36 → **26**。

三态实证（`r2-fix-message-verification-*.txt`，用户实际看到的字符串）：

| 版本 | 用户看到 |
|---|---|
| 基线 | `Evidence extraction failed: the JSON object must be str, bytes or bytearray, not NoneType` |
| round-1 的 assert | `Evidence extraction failed: ` |
| 本轮的 cast | `Evidence extraction failed: the JSON object must be str, bytes or bytearray, not NoneType` |

**请核对**：① 这 9 处是否真的恢复了基线的异常类型**与消息**？
② 我的审计判据（handler 体内对异常变量的格式化）有没有漏掉别的泄漏形态
（例如 `logger.exception()`、`raise ... from e`、异常被存进对象字段后延迟格式化）？
③ **剩余的 26 个 assert** 里，是否还有会改变可观察行为的？

### MEDIUM-2（r2）：审计方法「最内层 try + handler 集合」不足以证明等价

**采信。** 你指出还需比较「原异常与新异常命中的 handler、外层传播、重抛、返回字段、日志和副作用」。
本轮我把判据从「handler 是否捕获 AssertionError」**扩展到「handler 是否格式化异常消息」**，
覆盖了「返回字段」和「日志」两个维度。

**仍未覆盖的维度（如实声明，已写进验收单的「本卡未证明什么」）**：
- 外层传播 / 重抛链：25 → 现在 **26 个不在 try 内的 assert**，其异常类型仍是 `AssertionError`。
  我只量化了风险面（全仓 `backend/app` 有 104 处按 `AttributeError`/`TypeError` 分流的 except；
  与本卡改过文件有 import 关系的调用方共 8 个组合），**没有**逐条追调用链证明那些 except
  不会包住本卡 assert 的路径。
- 副作用顺序：assert 比原异常**更早**失败（在解引用之前），若解引用前还有别的副作用，顺序会变。

**请判断**：这两个未覆盖维度，在这张纯类型卡上「登记移交」是否可接受，还是应当在本卡内闭环。

### LOW-1（r2）：证据文件措辞错误

**采信。** 已在该 evidence 文件**末尾追加更正**（保留原文不删，以免篡改已落盘证据），
写明「诊断被 ignore 显式抑制，而非 pyright 仍能看见」，并区分 cast 与 ignore 的语义差别。

### LOW-2（r2）：`rag_service` 属性面差异

**保留登记，不修。** 你的意见是「若坚持零运行行为变化，建议保留显式重导出」。
我的判断：加回 `CanvasRAGConfig` 的重导出属于**新增代码**，而删除它的依据是它确实是死 import
（全仓无消费者，`grep` 仅命中 docstring 与该文件自身的 placeholder）。
这一条我作为**已知的属性面变化**移交给主 session 裁定，不在本卡自行决定。
**请判断**该处置是否可接受。

### 顺带修的一处格式

`rag_service.py` 我这轮改动的那行原本写成三行调用，`ruff format` 会把它压成单行（100 字符 < 120），
导致我的内容口径 format 判据报 DIFFER。已直接写成 ruff 的产出形态（单行）。
这是**纯换行**，同一表达式。

---

## 三 请按重要性排序回答

1. 这 9 处 `assert → cast` 是否真的恢复了基线的异常类型与消息？有没有哪一处改错了？
2. 我的「异常消息泄漏」审计判据有没有方法学漏洞？剩余 26 个 assert 里还有会改变可观察行为的吗？
3. 本轮整改是否引入任何新问题（新死 import、新类型放宽、注释与实际不符、新格式漂移）？
4. 「26 个不在 try 内的 assert 的异常类型变化」与「副作用顺序变化」这两个维度，
   登记移交是否可接受？
5. `rag_service` 属性面：不加回重导出、作为已知变化移交，是否可接受？

---

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` 与一句话定级理由。
每节若无问题请明确写「该节无发现」。**最后给出一句总判：本轮 BLOCKER 与 HIGH 是否均为 0。**

---

## 五 边界

- **只读**，不改文件；不连数据库；不跑 `tests/integration` / `tests/e2e`。
- 不在本卡范围：`api/v1/endpoints/review.py:1543/:1560/:1561`；
  `services/review_service.py:1809-1813`（共享文件，阶段 2）。
- 10 个共享文件（`review_service` / `mastery_engine` / `mastery_store` / `multimodal_service` /
  `difficulty_matcher` / `canvas_service` / `calibration_tracker` / `event_bus` / `mastery_fusion` /
  `agent_service`）阶段 1 禁改，仍有 60 条错误 = 预期。
- 另有 18 条错误等另一张卡的 `extraPaths` 合入后才判。
