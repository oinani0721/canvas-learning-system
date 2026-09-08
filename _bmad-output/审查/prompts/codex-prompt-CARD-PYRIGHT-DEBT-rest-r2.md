# 一 背景与最小读取面

同一张卡的第 2 轮：`CARD-PYRIGHT-DEBT-rest`（BATCH-2026-09-07-第十三批），仓库根
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u2-pyright-rest`。
范围：把 `backend/app` 里非 `services/` 的 pyright 报错清到 0，纪律是**只做类型层改动，不改运行期行为**。
本轮审的仍是**阶段 0 + 阶段 1**（阶段 2 还要合并候选树再清两个共享文件，故本轮**不绑最终合并态**）。

round-1 给了 BLOCKER 0 / HIGH 0 / MEDIUM 1，作者已按其整改；本轮请**重点复核整改本身**，
并把 round-1 因读取面不足而无法独立核对的四项一并判定（证据已直接贴在下面第二节）。

**请只读**：

1. round-1 之后的整改 diff：`git diff 41cc849c HEAD -- backend/app`
2. 全卡代码 diff：`git diff da690bf8 HEAD -- pyrightconfig.json backend/app ':(exclude)backend/app/services'`
3. `pyrightconfig.json`
4. 新增测试：`backend/tests/unit/test_exam_models_rubric_required_u2a.py`
5. ignore 清单：`_bmad-output/审查/evidence-pyright-rest/ignore-table-p1.md`
6. 验收单 §7-bis（round-1 逐条处置）：`_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-rest-2026-09-08.md`
7. 证据：`evidence-pyright-rest/` 下的 `negctl-p1r2-*.txt`、`judges-p1r2-*.txt`、`q4-schema-delta-*.txt`、`multiset-p1r2-*.txt`

# 二 round-1 四项"读取面不足"的补充证据（请核对这些数字本身是否支持结论）

**(a) round-1 Q9 —— `exam.py` 延后是否获授权。** 卡文 §三 原文（本轮直接引来，供你独立判定这是"阶段安排"还是"放宽判据"）：

> **与 U1-A 的交集面 `backend/app/api/v1/endpoints/exam.py`（10 条，实测 `:225 :245 :260 :288 :303 :317 :352 :379 :410 :436`）**：这 10 条与 `services/exam_service_ext.py` 的猴子补丁**同根**，U1-A §一(e) 已把该文件声明为跨包组 ① 的交集面（优先方案 = 在 `ExamService` 里加 `TYPE_CHECKING` 方法声明，api 侧随之消、**不动 api**）。本卡处置：**先不动 `exam.py`**，等 U1 的声明进候选树（阶段 2 merge 后）再只清残余；……阶段 1 若本卡确实动了它，必须在验收单写明理由并同步告知 U1。

作者据此**一字未动** `exam.py`（可用 `git diff da690bf8 HEAD -- backend/app/api/v1/endpoints/exam.py` 验证应为空）。

**(b) round-1 Q3 —— 四维必填化是否有遗漏调用点。** 全仓 grep 结果（`backend/app` + `backend/tests`）：
`AutoScoreResult` 的实例化点仅 `services/autoscore.py:141` 与 `:197`（两处都显式传四维）；
`exam_service.py:179` 只作形参类型、不实例化；`scoring_faithfulness.py:389` 只在 docstring 提及；
`RubricDimension` 的实例化点仅 `services/autoscore.py` 内 8 处；
`AutoScoreResult.(model_validate|parse_obj|model_construct)` 与 `AutoScoreResult(**` 在**生产代码中 0 命中**（唯一命中在新增测试里）。

**(c) round-1 Q4 —— schema 变化量化。** 基线树与当前树各自 `AutoScoreResult.model_json_schema()` 逐键比，差异恰 **5** 处：
四个 `properties/<dim>/description` 新增；`required` 由 `['node_id','exam_id','overall_score','grade']` 变为再加四个维度名。
`backend/openapi.json` 的 `components.schemas`（354 个）中 **`AutoScoreResult` 与 `RubricDimension` 均不存在** ⇒ 对外契约无影响。

**(d) round-1 Q1 —— 两条 ignore 的依据实测值。**
`metadata.py` 的 `drop_table(..., ignore_missing=True)`：lancedb 0.30.2 `inspect.signature` 实测
`DBConnection.drop_table(self, name, namespace=None)`（无该参数）而
`LanceDBConnection.drop_table(self, name, namespace=None, ignore_missing=False)`（**有**）⇒ pyright 读的是抽象基类 = 假阳。
`health.py` 的 `len(tables)`：`lancedb.connect(...).table_names()` 运行期返回 `list`（`type(...)__name__ == 'list'`，`__len__` 存在）。

**(e) multiset 存档的关键行**（round-1 只看了末行 `rc=`，该数字行在其上方）：
`base=356 work=232 NEW=0 GONE=124`（基准=阶段 0 sha）；
`base=232 work=232 NEW=0 GONE=0`（基准=round-1 绑定的 `41cc849c`，即整改零副作用）；
`base=421 work=232 NEW=1 GONE=190`（基准=主干 `da690bf8`，全卡视角；唯一那条 NEW 落在 `services/rag_service.py`，属并行卡 U1 的地盘，本卡不能改）。

# 三 round-1 整改内容（请独立核对是否真的修好、且没有引入新问题）

1. **MEDIUM-1（`neo4j_client.py`）**：`driver = self._driver` 已从闭包**外**移入 `_execute_with_retry` **内**，每次重试重新读，并补 `assert driver is not None, "…"`。
2. **Q8 等价性**：作者接受你的质疑并**推翻了自己的结论**——实测 anthropic 0.88.0 的 12 个块类型 `model_config.extra` **全部为 `'allow'`**，`ThinkingBlock.model_validate({...,"text":"x"})` 得到 `hasattr(text)=True` 而 `isinstance(TextBlock)=False`。故三处**退回 `hasattr`** + 行级 ignore，并删掉 `TextBlock` 导入。
3. **Q2**：本卡新增的 4 条 `assert` 全部补了消息，使异常正文不弱于它替换掉的 `AttributeError`。
4. 新增负控 3：摘掉一条 `block.text` 的 ignore → `Cannot access attribute "text"` 回到 **11** 条；还原自 scratchpad 副本，sha 逐字节相同。

# 四 请按重要性排序回答

1. 整改后的 `neo4j_client.py` 是否真的恢复了"每次重试重新读 `self._driver`"？新加的 `assert` 有没有制造出原代码没有的失败路径（注意 `RETRYABLE_EXCEPTIONS` 与 `RetryError` 的处理）？
2. 退回 `hasattr` + ignore 之后，`claude_client.py` 三处的行为是否与 `da690bf8` **逐字相同**？有没有别的地方还残留 round-1 那次 `isinstance` 改写的痕迹？
3. 25 条（整改后请重新计数）`# pyright: ignore` 里，还有没有把**真错误**写成假阳的？
4. 4 条 `assert` 是否都落在"原本遇 None 也会崩"的位置？
5. 第二节 (a)~(e) 的证据，是否**足以**支撑作者的对应结论？哪一条仍然不够，请说清缺什么。
6. 位置默认机械改写有无漏改误改（必填 `Field(...)` 被误动、`default_factory` 被动过、多行形态改坏）。
7. 阶段 1 末 `api` 包剩 21 条（`exam.py` 10 + `review.py` 7 + `system.py` 4）——结合 (a) 的卡文原文，这是阶段安排还是放宽判据？

# 五 输出格式

`BLOCKER / HIGH / MEDIUM / LOW` 四级，每条 `file:line` + 一句问题陈述 + 一句"什么输入或状态下它会真的出问题"。没有就写"无"。

# 六 边界

- 只读，不修改任何文件；不连接任何数据库；不跑 `tests/integration` / `tests/e2e`。
- `backend/app/services/**` 的 pyright 残余不在本卡范围（并行卡 U1-A）。
- `review.py:1543` 族（对 dict 取属性）是已知的 api 侧真缺陷，不在本卡范围。
- 本轮不要求给出最终合并态结论：阶段 2 还会 merge 候选树并清 `review.py` / `system.py`，那一轮才绑最终 HEAD。
