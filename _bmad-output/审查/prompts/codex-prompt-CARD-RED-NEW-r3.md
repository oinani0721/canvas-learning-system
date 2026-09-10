# 独立审查请求（round-3，绑最终 HEAD） — CARD-RED-NEW（BATCH-2026-09-07-第十三批 / 车道 U11-C）

## 一 背景 + 最小读取面（请只读下列内容，不要扩大读取面）

本卡把 `backend/tests/unit` 既有红基线（202 nodeid @ `da690bf8`）里被分诊为「新」类的 **8 条**，逐条给出「回归 / 契约演进 / 测试写错」三选一裁定 + 依据，再据裁定分派处置。安全面那条（`test_path_traversal_windows_style`）的断言一个字都不许改，实现只能更严。

轮次历史：
- **round-1**（绑 `9a5bc79d`）：BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 1，车道**全部接受、无驳回**，整改后提交为 `9848c2c1`。
- **round-2**（绑 `9848c2c1`）：结论见存档，车道处置见下。
- **round-3（本轮）**：绑最终 HEAD，请判定是否还有 BLOCKER / HIGH。

> ⚠️ **一处必须先声明的作业瑕疵**：round-2 运行**期间**，车道修改了工作树上的三个文件——`evidence-red-new/new-verdicts.md`（#4 措辞按 round-1 的提醒校准）、`验收单/UAT-CARD-RED-NEW-2026-09-09.md`、以及 `backend/tests/unit/test_difficulty_matcher.py` 的一处 **docstring**（同一措辞校准，非行为改动）。其中 `new-verdicts.md` 在 round-2 的读取面内，因此 round-2 读到的可能是中间态。本轮绑定的是把这些改动一并提交后的最终 HEAD，请以本轮为准。

请读（仓库根 = 本工作树根）：

1. 全卡代码 diff：`git diff --no-color b17b710d HEAD -- . ':(exclude)_bmad-output'`
2. **round-2 之后的增量 diff**：`git diff --no-color 9848c2c1 HEAD -- . ':(exclude)_bmad-output'`
3. 裁定表（含 §五/§六 整改记录）：`_bmad-output/审查/evidence-red-new/new-verdicts.md`
4. 前两轮存档：`_bmad-output/审查/codex-review-CARD-RED-NEW.md`、`_bmad-output/审查/codex-review-CARD-RED-NEW-r2.md`
5. 生产判定行：`backend/app/services/multimodal_service.py:490-535`，含两个调用方 `:570-580` 与 `:715-725`
6. 证据（全在 `_bmad-output/审查/evidence-red-new/`）：
   - `sec-monotonicity-selfcheck.txt`（60 例：旧接受→新拒绝 10 例，**旧拒绝→新接受 0 例**；含符号链接 base）
   - `sec-alias-edgecase-selfcheck.txt`（真实文件系统：base 名含反斜杠且 `a/b` 同时存在、符号链接指向含反斜杠目录）
   - `codex-r1-HIGH1-repro.txt`、`codex-r1-followup-git.txt`、`format-multiset-compare-v2.txt`、`pyright-baseline-compare.txt`
   - `flaky-check-*.txt`（#3 10/10、Tier2 30/30）
   - 最终裁判：`unit-after-*.txt` / `red-diff-*.txt` / `files-*.txt` / `subset-multimodal_service-*`

## 二 作者自述，请独立核对（不要采信，请自行验证）

round-2 的 4 条发现（MEDIUM×3 + LOW×1）车道**全部接受、无驳回**，处置如下：

1. **MEDIUM-1（#1/#2 主张超出证据）** → 补齐你点名的排除项：在诞生 commit `43d291d8` 上实测——该常量全模块只有 2 处出现（定义 `0.15` + 使用）、**无** `_load_calibration_thresholds`、**无** `global`、**无**环境变量读取、**无**模块级副作用调用、**全树除定义模块外 0 处引用**、当时的测试文件**不 monkeypatch 该常量**。同时把主张收窄为「**只证明诞生那一刻即红**」，明确不覆盖中间 commit。证据 `codex-r2-M1-threshold-writepoints.txt`。
2. **MEDIUM-2（#3 裁定行与 §〇 自相矛盾）** → 承认是真实疏漏（在一处收窄了却没从结论行里减掉），已改：裁定列改为「async 竞态：等待原语选错」，依据列明写「**本条不主张该测试历史上曾为绿**」并列出未分离的候选 `c01bd39c`。
3. **MEDIUM-3（format v2 仍丢位置）** → 补位置维度 v3：在**同一文件同一版本**上取 `A = 本卡改动行（git diff -U0 的 +hunk）`、`B = ruff 真正要替换的行（--diff 里带 '-' 前缀的行，不是整个 hunk 范围）`，判据 `A ∩ B = ∅`，六文件合计 **0**。证据 `format-position-gate-v3.txt`。
   - ⚠️ 该判据的**初版实现有假阳性**（把 hunk 整个范围含上下文当成 B），在 `test_calibration_tracker.py` 误报 291–293；查证后确认那三行本身 format-clean、只是落在针对存量行的 hunk 上下文里。已如实记录在裁定表 §六。
4. **LOW（「未放宽」没限定基线）** → 已写明该表述**只对 `b17b710d` 成立**；相对 round-1 初版的放宽正是修复本身，并把你给的 `base=Path(r"/storage\..")` 反例（`b17=True / r1=False / r2=True`）原样收录，注明它不是新增磁盘越界面。

另有两份**非卡文要求的自查**：`sec-monotonicity-selfcheck.txt`（60 例枚举，「旧拒绝→新接受」= 0，含符号链接 base）与 `sec-alias-edgecase-selfcheck.txt`（真实文件系统：base 名含反斜杠且 `a/b` 同时存在、符号链接指向含反斜杠目录）。

**本轮增量（`9848c2c1..HEAD`）只有一处代码改动**：`test_difficulty_matcher.py` 的一处 **docstring**（把 round-1 提醒的「空窗不告警」措辞校准为「health_monitor 确实报 warning，只是不读 is_healthy」）。纯注释，行为不变，该文件 19 passed。

## 三 按重要性排序的问题

1. **#8 是否仍存在任何「原本应被拒、现在被放行」的输入**（安全回退）？作者的单调性自查是 60 例枚举 + 真实文件系统的符号链接/别名场景，判据是「旧拒绝→新接受 = 0 例」。这个枚举面是否有明显缺口？
2. **#8 是否引入了新的合法路径误拒**？round-1 已抓到一次（归一化只做了一侧），本轮请检查修复后是否还有：storage base 与候选路径的反斜杠出现在不同位置、base 为符号链接、base 含 `..`、归一化后的 root 恰好指向另一个真实目录等情形。
3. **本轮增量 diff（`9848c2c1..HEAD`）是否只含 docstring 与文档**，没有触碰任何断言、判定行、类型注解或别的车道地盘？
4. **前两轮已核验通过的项有没有被本轮改动破坏**：#5/#6 的断言与负控、#3 的新断言、#7 的数据与公式、#1/#2 的防自证写法。
5. **诚实性**：裁定表 §五/§六 对前两轮的记录，有没有把「已接受但未完全解决」写成「已解决」，或夸大整改效果？作业瑕疵（round-2 期间改文件）是否已如实声明？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：`file:line` + 一句话复现思路。若某级为空请显式写「无」。不需要给出补丁。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接任何数据库。
- 不评价第十四批的 MOCKFIX / ENVDEP 卡。
- 不需要提供修复补丁，只需指出问题。
