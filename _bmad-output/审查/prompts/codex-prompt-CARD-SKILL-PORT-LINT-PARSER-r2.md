# 独立复核请求 r2 — CARD-SKILL-PORT-LINT-PARSER（r1 LOW 整改后，绑最终 HEAD）

## 一 背景与最小读取面

worktree `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
（分支 `card/t7-skills`）。r1 判定 **BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 1**，作者已整改那条 LOW。
本轮目的：核整改是否到位、是否引入新问题，并绑**最终 HEAD**。

- 本卡基线 `<T7B_TIP>` = `17c14d2705e519d44cb7c4988c81a920b175d03f`（前卡 T7-B tip）
- r1 审 SHA = `1eab9358df306838c897163142647b1ea5424e27`
- **本轮审 SHA（最终 HEAD）** = `710b9ff6922d5d697675c24c7eb07843c7bd2dbe`

**最小读取面（请只读这些，不要扩散到全仓）**：

1. `git diff 1eab9358df306838c897163142647b1ea5424e27 710b9ff6922d5d697675c24c7eb07843c7bd2dbe -- . ':(exclude)_bmad-output'`
   —— **本轮唯一的代码改动**（应只有模块头 docstring）。
2. `git diff 17c14d2705e519d44cb7c4988c81a920b175d03f 710b9ff6922d5d697675c24c7eb07843c7bd2dbe -- . ':(exclude)_bmad-output'`
   —— 本卡累计改动（应只有两文件）。
3. 新模块 `backend/tests/skills/skill_portability_lint.py` 的**文件头 docstring**（交接登记，本轮改动处）。
4. 只读核对（**禁改**）：`backend/tests/regression/test_g3_3_cas.py` 的 `_SEB_BLOCKS` / `assert len(_SEB_BLOCKS) == 1` /
   `SEB_CODE` / `_exam_board_code()`；`backend/tests/regression/test_learning_events_schema_contract.py` 的
   `test_real_producer_start_exam_board_writer` 函数体。
5. `_bmad-output/审查/evidence-skill-port-lint-parser/` 下新增的
   `r1-low-fix-docstring-only-*.txt`（改动面自证）与 `skills-after-r1fix-*.txt`（整改后 tests/skills 重跑）。
6. r1 存档 `_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-PARSER-r1.md`（含首部）。

## 二 作者本轮自述，请独立核对

① **整改内容**：r1 的 LOW 指出「这两处都在模块级」指代不清，会把 `_exam_board_code()` 函数内的
   `.replace()` 误归为导入期执行。已改写为**按作用域分列两项**：
   - **模块级三行**：`_SEB_BLOCKS` 列表推导（含字面量过滤）、紧随的 `assert len(_SEB_BLOCKS) == 1`、
     `SEB_CODE = _SEB_BLOCKS[0]` —— 导入期即执行；
   - **函数体内一处**：`_exam_board_code()` 里的 `.replace(...)` —— 不在导入期执行，只消费模块级 `SEB_CODE`。
   并明写「collect-time ERROR 的归因只落在模块级那三行；函数体内那处根本轮不到执行，但解耦时同样要改」。
② **改动面**：唯一 hunk 起于 `:18`，全落在模块头 docstring（末行 `:40`）内。
③ **真代码零改动**：去 docstring 后 `ast.dump` 与 `1eab9358` 版逐字符**相同**；含 docstring 时**不同**
   （证明确实改了文案）。验伪锚：同一 `strip_doc` 对 `return 1` / `return 2` 判不同。
④ **整改后重跑**：`tests/skills` 仍 555 passed（存档首部自带工作树两文件 sha256 作自绑定）。
⑤ **regression 两文件本轮仍未改**（本卡对它们无写权）。

## 三 请按重要性排序回答的问题

① **整改后的作用域描述是否与实际代码一致**：请直接读 `test_g3_3_cas.py`，核对
   「模块级三行 / 函数体内一处」的划分、以及「改字面量 ⇒ 模块级 assert 在导入期失败 ⇒ collect-time ERROR、
   整文件不可收集」这条因果是否准确。若仍有歧义或事实错误，请指出。
② **schema 侧的描述是否准确**：`test_learning_events_schema_contract.py` 那一侧被描述为
   「`matches` 列表推导 + `assert len(matches) == 1` + 同函数体内 `.replace(...)`，均在
   `test_real_producer_start_exam_board_writer` 函数体内 ⇒ 运行期断言红，不是 collect-time ERROR」。
   这个判读是否成立？
③ **「4 处硬钉点」这个数目是否准确**：登记称 cas 侧 2 处 + schema 侧 2 处 = 4。作者另称 schema 侧的
   `tmp_path / "exam-created-event.json"`（无 `/tmp/` 前缀）不是钉点。请独立核对计数与这一排除是否正确。
④ **本轮是否引入任何新问题**：docstring 改写有没有引入与代码实际行为矛盾的新陈述、或破坏
   r1 已确认的任何结论（AST 等价、51 个导入对象身份、12 个判据 `__globals__` 归属、负控、ruff）。
⑤ **r1 遗留的两点，请给出本轮判断**：
   (a) r1 说「仅凭 555 全绿 + 无旧定义 + 无重名尚不是完整证明」，加上对象身份/全局绑定/AST 核验后
       「足以支持其余 10 条搬迁连线正确，不等于完成全部判据的语义变异覆盖」——
       作者已把这一限制写进验收单「本卡未证明什么」。这个限制陈述是否准确、是否够。
   (b) r1 说存档 `module-verifier-*.txt` 只保存断言身份计数、未保留原始 traceback，
       「历史命令实现是否全部消除同型缺陷，现有存档不足以证明」——作者已把这一点作为存档缺陷
       如实记入验收单（变异脚本 `print(out[-2600:])` 截断了 pytest 输出，但判定用的 `hits` 计数
       是对**完整** output 做的）。这个记录是否如实、还缺什么。

## 四 输出格式

BLOCKER / HIGH / MEDIUM / LOW 分级 + `file:line` + 每条一句**触发路径说明**
（哪种输入会走到这条路径、会看到什么现象）。若无问题请明确写出各级计数为 0。

## 五 边界

只读；不连任何数据库；不跑 `tests/regression` 目录级（pact/真服务会挂）；
不评 `SKILL.md :430/:435` 的真解耦方案设计（跨地盘，交主 session）；
不评第十三批已定版的 12 个判据**语义本身**。
