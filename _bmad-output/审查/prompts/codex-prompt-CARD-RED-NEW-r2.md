# 独立审查请求（round-2） — CARD-RED-NEW（BATCH-2026-09-07-第十三批 / 车道 U11-C）

## 一 背景 + 最小读取面（请只读下列内容，不要扩大读取面）

本卡处理 `backend/tests/unit` 既有红基线（202 nodeid @ `da690bf8`）里被分诊为「新」类的 **8 条**：逐条给出「回归 / 契约演进 / 测试写错」三选一裁定 + 依据（须含运行期或 git 证据），再据裁定分派处置。安全面那条（`test_path_traversal_windows_style`）的断言一个字都不许改，实现只能更严。

**round-1 的结论是 BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 1，车道全部接受、无驳回**，本轮请复审整改是否成立、是否引入新问题。

请读（仓库根 = 本工作树根）：

1. 本轮代码 diff：`git diff --no-color b17b710d HEAD -- . ':(exclude)_bmad-output'`
2. **round-1 之后的增量 diff**（本轮整改本身）：`git diff --no-color 9a5bc79d HEAD -- . ':(exclude)_bmad-output'`
3. 裁定表（含 §五 整改记录）：`_bmad-output/审查/evidence-red-new/new-verdicts.md`
4. round-1 存档：`_bmad-output/审查/codex-review-CARD-RED-NEW.md`
5. 生产判定行：`backend/app/services/multimodal_service.py:490-535`，含两个调用方 `:570-580` 与 `:715-725`
6. 本轮新增/更新的证据（全在 `_bmad-output/审查/evidence-red-new/`）：
   - `codex-r1-HIGH1-repro.txt`（HIGH 的逐场景复核 + 修后对照）
   - `codex-r1-followup-git.txt`（MEDIUM-1 的诞生 commit 直接验算；MEDIUM-2 的 `c01bd39c` diff）
   - `format-multiset-compare-v2.txt`（MEDIUM-3 加强后的判据）
   - `flaky-check-*.txt`（#3 新断言 10 次、#5/#6 各 10 次连跑）
   - `files-r1fix-*.txt` / `subset-multimodal_service-close-r1fix-*.txt` / `unit-after-r1fix-*.txt`（整改后重跑的全部裁判）
   - `red-diff-*.txt`（目录级 nodeid diff）

## 二 作者自述，请独立核对（不要采信，请自行验证）

1. **HIGH（#8 归一化只做了一侧）已修**：新增 `normalized_root`，令 `backslash_normalized` 与**同样归一化的 root** 比较。自述结论：storage base 含反斜杠时的误拒消除，且拒绝面一格未放宽。
2. **MEDIUM-1（#1/#2「从未绿过」未证）已补更强证据**：在诞生 commit `43d291d8` 上直接验算——`_load_calibration_thresholds` 命中数为 0（配置覆盖链当时不存在）、常量恒 `0.15`、判定用 `<`；历史 `mastery_config.json`（`9d3326ee`）内无 `calibration_thresholds` 键。自述结论：「阈值历史上曾是 0.155」这一反例被排除。
3. **MEDIUM-2（#3 归因缺绑定 + `c01bd39c`）已收窄表述**：不再声称「历史上曾经绿过」，改为「等待写法是致红的充分原因」，并如实写明致红点候选是 `14f0412d` 与 `c01bd39c` 两者、本卡未逐一分离。裁定仍为「测试写错」，理由不依赖历史归因。
4. **MEDIUM-3（format 多重集口径太弱）已加强**：改为 `<文件名>|<方向±>|<内容>` 多重集 + 显式绑定基线 SHA `b17b710d` + 两侧统一 `--config backend/ruff.toml`。
5. **MEDIUM-4（#8 未回答三选一）已归类**：#8 = **契约演进**，「防御深度加强」降为处置性质描述；计数更正为 测试写错 7 / 契约演进 1 / 回归 0。
6. **LOW（行号/改动量过期）已复核更正**：判定行 `:507-519`、返回行 `:530`、调用方 `:576`/`:720`、`backend/app` diff 实数 +12/−1。
7. 整改后**全部裁判已重跑**：六测试文件 143 passed；`multimodal_service` 子集 38 passed（与开工基线 diff 只有一个 `<`）；`tests/unit` 目录级 `>` 行为零、本卡贡献恰好 8 条。

## 三 按重要性排序的问题

1. **HIGH 的修复是否真的成立、是否引入新的放行**：`normalized_root = Path(str(self.storage_base_path).replace("\\", "/")).resolve()` 与 `storage_root = self.storage_base_path.resolve()` 在什么输入下会指向不同位置？两侧都归一化之后，是否存在**原本应被拒、现在被放行**的输入（即拒绝面被放宽）？请特别检查：base 与候选路径的反斜杠出现在不同位置、base 是符号链接、base 含 `..` 分量等情形。
2. **#8 的三选一归类是否恰当**：把它归入「契约演进」是否比「测试写错」或「回归」更站得住？还是说三选一分类本身在这一条上不完备、作者应当明说而不是强行归类？
3. **MEDIUM-1 的补证是否真的排除了反例**：在 `43d291d8` 上「`_load_calibration_thresholds` 命中数为 0」是否足以推出「阈值在该 commit 恒为 0.15」？有没有别的覆盖路径（环境变量、其他 import 时副作用、上游模块改写模块属性）？
4. **MEDIUM-2 的收窄是否收得够**：现在的表述有没有仍然隐含「曾经绿过」的推断？裁定「测试写错」在不依赖历史归因时是否仍然成立？
5. **MEDIUM-3 加强后的判据是否还有漏洞**：`<文件名>|<方向±>|<内容>` 多重集还能被什么样的等价替换骗过？
6. **回归检查**：本轮整改（`9a5bc79d..HEAD`）有没有碰到 round-1 已核验通过的部分——#5/#6 的断言、#3 的新断言、#7 的数据与公式、任何类型注解、别的车道地盘、conftest？
7. **诚实性**：裁定表 §五 对 round-1 的记录有没有夸大整改效果、或把「已接受但未完全解决」写成「已解决」？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：`file:line` + 一句话复现思路。若某级为空请显式写「无」。不需要给出补丁。

## 五 边界

- 只读审查，不要修改任何文件。
- 不要连接任何数据库。
- 不评价第十四批的 MOCKFIX / ENVDEP 卡。
- 不需要提供修复补丁，只需指出问题。
