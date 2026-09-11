# 独立审查请求（round-5，协议轮次上限，绑最终 HEAD） — CARD-RED-NEW（BATCH-2026-09-07-第十三批 / 车道 U11-C）

## 一 背景 + 最小读取面（请只读下列内容，不要扩大读取面）

本卡把 `backend/tests/unit` 既有红基线（202 nodeid @ `da690bf8`）里被分诊为「新」类的 **8 条**，逐条给出「回归 / 契约演进 / 测试写错」三选一裁定 + 依据，再据裁定分派处置。安全面那条（`test_path_traversal_windows_style`）的断言一个字都不许改，实现只能更严。

轮次历史（每轮车道均**全部接受、无驳回**）：

| 轮 | 绑定 | 结论 | 该轮促成的改动 |
|---|---|---|---|
| r1 | `9a5bc79d` | 0 / **1 HIGH** / 4 / 1 | 路径判定**第二版**（补 `normalized_root`） |
| r2 | `9848c2c1` | 0 / 0 / 3 / 1 | 仅文档与一处 docstring |
| r3 | `0266fb08` | 0 / 0 / 2 / 1 | 路径判定**第三版**（root 不参与归一化） |
| r4 | `7f16c916` | 0 / 0 / 2 / 1 | 路径判定**第四版**（`relative_to` 两侧都用 resolve 后的路径） |
| **r5（本轮）** | 最终 HEAD | 请判定 | — |

> ⚠️ **本轮是协议规定的轮次上限（5）**。若本轮仍有 BLOCKER 或 HIGH，车道将停下交主 session 人审，不再自行整改。请据此把握判定尺度：**请明确区分「必须改的缺陷」与「可登记的改进建议」**。

请读（仓库根 = 本工作树根）：

1. 全卡代码 diff：`git diff --no-color b17b710d HEAD -- . ':(exclude)_bmad-output'`
2. **r4 之后的增量 diff**：`git diff --no-color 7f16c916 HEAD -- . ':(exclude)_bmad-output'`
3. 裁定表（含 §五~§八 四轮整改记录）：`_bmad-output/审查/evidence-red-new/new-verdicts.md`
4. 前四轮存档：`codex-review-CARD-RED-NEW.md` / `-r2.md` / `-r3.md` / `-r4.md`
5. 生产判定行：`backend/app/services/multimodal_service.py:494-545`，含两个调用方 `:580-592` 与 `:724-736`
6. 证据（全在 `_bmad-output/审查/evidence-red-new/`）：
   - `sec-r4-M1-fix-verify.txt` —— **本轮最重要**：[A] 你 r4 给的输入场景（相对/绝对 base）逐例复现 + 修后结果；[B] r3 的输入场景；[C] 60 例单调性 + 误拒；[D] 返回值不变
   - `format-position-gate-v3.txt`（**已按你的 LOW 重跑并落盘**，六文件 A∩B 合计 0，并写明 v2/v3 的不完备性）
   - `sec-r3-M1-fix-verify.txt` / `sec-monotonicity-real-service.txt` / `sec-alias-edgecase-selfcheck.txt`
   - 最终裁判：`unit-after-r4fix-*.txt` / `files-r4fix-*.txt` / `subset-r4fix-*.txt` / `red-diff-*.txt`

## 二 作者自述，请独立核对（不要采信，请自行验证）

r4 的 3 条发现**全部接受、无驳回**：

1. **MEDIUM-1（`ValueError` 分支让第二重检查退化，未被拦下）** → 先按你给的输入场景复现（相对 `base=Path("backend")` + 绝对候选 ⇒ r3 拒绝、r4 接受）确认成立；随后改为**第四版**：
   ```python
   below_root = (
       str(resolved_path.relative_to(storage_root)) if resolved_path.is_relative_to(storage_root) else None
   )
   reinterpreted = (
       (storage_root / below_root.replace("\\", "/")).resolve() if below_root is not None else resolved_path
   )
   if not resolved_path.is_relative_to(storage_root) or not reinterpreted.is_relative_to(storage_root):
   ```
   自述：两侧都在 `resolve()` **之后**取，base 的拼写（相对/绝对、含不含 `..`、是不是符号链接）在比较前已归一 ⇒ 不再影响结果；`try/except ValueError` 随之消失（第一重已保证 `relative_to` 必然成功）。实测相对 base 与绝对 base **结果一致**。
2. **MEDIUM-2（§七 误记 D-15 达成）** → §七 标题去掉「D-15 达成轮」，并加注「达成以**最后一轮**为准」。
3. **LOW（format 存档与结论不一致）** → 承认那份存档是**修 format 债之前**的快照（重跑时用了内联脚本、忘了 `tee`）。已绑最终代码重跑并落盘（六文件 A∩B 合计 0），同时把 v2/v3 的**不完备性**写进存档与裁定表。

**本轮增量（`7f16c916..HEAD`）的代码改动只有 `multimodal_service.py` 的该判定逻辑**。终态：判定行 `:507-529`、返回行 `:540`、调用方 `:586`/`:730`，`backend/app` diff **+22/−1**。

## 三 按重要性排序的问题

1. **第四版是否仍有「原本应被拒、现在被放行」的输入**（安全回退）？特别请检查：`resolved_path` 已解析符号链接，用它做 `relative_to` 后再拼回 `storage_root` 重读——这个「先解析、再重读」的顺序有没有引入新的放行面？
2. **第四版是否仍有合法路径误拒**？这是同一处第四次改。请检查 `storage_base_path` 本身是符号链接、`below_root` 为 `"."`（file_path 恰等于 base）、以及 `below_root` 含 `..` 的情形。
3. **`below_root is None` 分支现在是否真的不可达**？若可达，`reinterpreted = resolved_path` 的退化是否安全？
4. **本轮增量是否只碰了该判定逻辑**，没有触碰任何断言、类型注解、别的车道地盘、conftest？
5. **前四轮的记录是否仍有不实之处**：裁定表 §五~§八 有没有把「已接受但未完全解决」写成「已解决」、或仍有与终态不符的数字/表述？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：`file:line` + 一句话复现思路。若某级为空请显式写「无」。不需要给出补丁。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接任何数据库。
- 不评价第十四批的 MOCKFIX / ENVDEP 卡。
- 不需要提供修复补丁，只需指出问题。
