# 独立审查请求（round-4，绑最终 HEAD） — CARD-RED-NEW（BATCH-2026-09-07-第十三批 / 车道 U11-C）

## 一 背景 + 最小读取面（请只读下列内容，不要扩大读取面）

本卡把 `backend/tests/unit` 既有红基线（202 nodeid @ `da690bf8`）里被分诊为「新」类的 **8 条**，逐条给出「回归 / 契约演进 / 测试写错」三选一裁定 + 依据，再据裁定分派处置。安全面那条（`test_path_traversal_windows_style`）的断言一个字都不许改，实现只能更严。

轮次历史（每轮车道均**全部接受、无驳回**）：

| 轮 | 绑定 | 结论 | 主要整改 |
|---|---|---|---|
| r1 | `9a5bc79d` | 0 / **1 HIGH** / 4 / 1 | #8 归一化只做了一侧 ⇒ storage base 含反斜杠时误拒每次普通上传 → 补 `normalized_root` |
| r2 | `9848c2c1` | 0 / 0 / 3 / 1 | #3 裁定行与 §〇 自相矛盾（真实疏漏）；#1/#2 补排除项；format 判据补位置维度 v3 |
| r3 | `0266fb08` | 0 / 0 / **2** / 1 | **MEDIUM-1：归一化后的 root 是另一条真实路径，其上若有外指符号链接则普通上传再次被误拒** → 见下 |
| **r4（本轮）** | 最终 HEAD | 请判定 | — |

**本轮请复审 r3 三条发现的整改，并判定是否还有 BLOCKER / HIGH。**

请读（仓库根 = 本工作树根）：

1. 全卡代码 diff：`git diff --no-color b17b710d HEAD -- . ':(exclude)_bmad-output'`
2. **r3 之后的增量 diff**：`git diff --no-color 0266fb08 HEAD -- . ':(exclude)_bmad-output'`
3. 裁定表（含 §五/§六/§七 三轮整改记录）：`_bmad-output/审查/evidence-red-new/new-verdicts.md`
4. 前三轮存档：`codex-review-CARD-RED-NEW.md` / `-r2.md` / `-r3.md`（均在 `_bmad-output/审查/`）
5. 生产判定行：`backend/app/services/multimodal_service.py:494-545`，含两个调用方 `:578-590` 与 `:722-734`
6. 证据（全在 `_bmad-output/审查/evidence-red-new/`）：
   - `sec-r3-M1-fix-verify.txt` —— **本轮最重要的一份**：[A] 你 r3 给的构造逐例复现 + 修后结果；[B] 单调性 60 例（真实生产对象）；[C] 合法上传误拒 0 例；[D] 返回值不变
   - `format-position-gate-v3.txt`（整改后重跑，六文件 A∩B 合计 0）
   - `sec-monotonicity-real-service.txt` / `sec-monotonicity-selfcheck.txt` / `sec-alias-edgecase-selfcheck.txt`
   - 最终裁判：`unit-after-r3fix-*.txt` / `files-r3fix-*.txt` / `subset-r3fix-*.txt` / `red-diff-*.txt`

## 二 作者自述，请独立核对（不要采信，请自行验证）

r3 的 3 条发现**全部接受、无驳回**：

1. **MEDIUM-1（合法路径误拒，第三次改生产）** → 先按你给的构造实测复现（真实存储 `/T/a\b/image`，而 `/T/a/b/image -> /T/outside`），确认成立；随后把修法从「两侧都归一化」改成 **root 完全不参与归一化，只把 storage root 之下的那段按 `\` 重读一遍**：
   ```python
   try:
       below_root = str(file_path.relative_to(self.storage_base_path))
   except ValueError:
       below_root = None
   reinterpreted = (
       (storage_root / below_root.replace("\\", "/")).resolve() if below_root is not None else resolved_path
   )
   if not resolved_path.is_relative_to(storage_root) or not reinterpreted.is_relative_to(storage_root):
   ```
   自述：base 的拼写从此**完全不影响判定**，r1 与 r3 两类误拒一并消失；`resolved_path.is_relative_to(storage_root)` 这个必要条件仍在，返回值仍是 `file_path.resolve()`。
2. **MEDIUM-2（format v3 仍不完备）** → **改主张而非改判据**：v2/v3 都保留，但表述改为「两个独立判据均未发现新增」，**不再声称「证明新增为零」**，并把你给的「纯删除 + 纯插入」反例写进裁定表 §六。
3. **LOW（收窄未同步完整）** → 两处都改：`test_calibration_tracker.py` 的 docstring 不再写 `it was never a regression`，改为「排除『后来某次改动把它弄红了』这个解释，不是对每个中间 commit 的主张」；裁定表 §〇 同步加措辞边界。裁定表 §七 已如实记录**这是同一个病第三次出现**。

**本轮增量（`0266fb08..HEAD`）的代码改动只有 `multimodal_service.py`**：上述判定逻辑 + 一处三元表达式按 ruff 期望折行（位置判据 v3 抓到的、我自己引入的 format 债）。终态行号：判定行 `:507-527`、返回行 `:538`、调用方 `:584`/`:728`，`backend/app` diff **+20/−1**。

## 三 按重要性排序的问题

1. **新修法是否仍存在「原本应被拒、现在被放行」的输入**（安全回退）？`relative_to` 用的是**未 resolve 的字面路径**比较，`below_root` 可能包含 `..`——请检查这是否给出了新的放行面。
2. **新修法是否还有合法路径误拒**？这是同一处第三次改，前两版都在「让判定更严」时引入误拒。请特别检查：`file_path` 不在 `storage_base_path` 字面之下时（`below_root is None`，此时 `reinterpreted = resolved_path`）的行为、`storage_base_path` 是相对路径时、以及 `below_root` 本身含 `..` 时。
3. **`try/except ValueError` 是否吞掉了本该拒绝的情形**？当 `relative_to` 抛 ValueError 时我让 `reinterpreted = resolved_path`，等于第二重检查退化为第一重——这是安全的降级还是漏洞？
4. **本轮增量是否只碰了该判定逻辑**，没有触碰任何断言、类型注解、别的车道地盘、conftest？
5. **诚实性**：裁定表 §七 对 r3 的记录、以及「一条贯穿三轮的教训」那段，有没有夸大整改效果或把「已接受但未完全解决」写成「已解决」？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：`file:line` + 一句话复现思路。若某级为空请显式写「无」。不需要给出补丁。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接任何数据库。
- 不评价第十四批的 MOCKFIX / ENVDEP 卡。
- 不需要提供修复补丁，只需指出问题。
