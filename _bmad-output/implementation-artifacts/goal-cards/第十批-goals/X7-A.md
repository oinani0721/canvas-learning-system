> ⚠️ 本文件是 CARD-G3-2c-A（安全/取证）的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十批手册 §三 X7-A 块。
> 批次标记 `[BATCH-2026-09-04-第十批 / CARD-G3-2c-A]`。主干基线 `1f249b33`；只读取证源 `card-w7-ledger @56bfe9d4` **及其未提交工作树改动**。勘探 2026-09-04。X7 车道三卡严格串行：A → B → C。

# CARD-G3-2c-A — quiz-answer 账本重切 · 第一张：安全/取证定案 + 移植快照

## 〇 一句话
G3-2b 停轮（round-17 绑当前 HEAD 仍 3B/1H，BLOCKER 集合与 round-16 完全不相交 = 再生非收敛）。重切前必须把三件「事实」定死：① 部署拓扑（合入 feature ≠ 替换 live）；② 车道工作树里**已写但未提交**的 round-17 修复怎么搬；③ stderr 与现网 data/ 残留怎么处置。然后做一次「移植快照」commit，给 B/C 两卡一个可红的基线。

## 一 关键事实（勘探实测）
| 事实 | 位置 / 命令 |
|---|---|
| 主干 `canvas-vault/.claude/skills/quiz-answer/SKILL.md` = 443 行（sha `0b14a974…`）；live vault 同名 = 439 行（sha `9652e1e1…`），**realpath 不同**，只差 4 行（主干多 `stage_recap` 排除段 `:87-90`） | `wc -l`、`shasum` |
| live vault 所在 checkout = `/Users/Heishing/Desktop/canvas/canvas-learning-system`（branch `main` @ `a55db2ab`）；该 SKILL.md 在 main 上是 **untracked**（`git status` = `??`，`git cat-file HEAD:` 报不在 HEAD）；feature 不是 main 祖先 | `git -C … status --short canvas-vault/.claude/skills/quiz-answer/SKILL.md` |
| ⇒ **合入 feature 不会自动替换 live**；若有一天把 feature 合进 main，git 会因「untracked file would be overwritten」中止，而不是替换 | — |
| 车道工作树未提交改动 = **4 文件 572+/59-**（台账写「+395/-34 三文件」失准）：`prompts/codex-prompt-CARD-G3-2b-round17.md` 38/2、`g32b_mutation_gates.py` 107/12、`test_g3_2_review_ledger.py` 168/1、`SKILL.md` 259/44 | `git -C card-w7-ledger diff --numstat` |
| 未提交改动里已含 round-17 BLOCKER③ 的修复：`_canon_tree` 改显式栈后序遍历 + 20 万节点预算 fail-closed（`SKILL.md:622` 注释直书） | 工作树 |
| 未提交改动在测试尾部新增 163 行 round-17 门（3 BLOCKER + 1 HIGH），首个 `test_round17_fsrs_applied_must_be_strict_bool` | `test_g3_2_review_ledger.py:5197` |
| 车道另有 2 个 untracked：`codex-review-CARD-G3-2b-round17.md`（23,588 B）、同名 `.stderr`（2,429,183 B） | `git status` |
| UAT `:1341` stderr 政策：round-1 stderr 含 `.env` 配置值截断前缀，**故意不入库**、保留 untracked；但 `4deb289b` 把 19 个 stderr 入库（与政策矛盾；主干 squash 时会剔除） | 验收单 |
| 裁决点⑭（`UAT:1316`）声称仓库根 `data/lancedb/canvas_vault_file_fingerprints.lance` 「只有 1 个 manifest」——实测 **11 个**（Sep 1 07:08-07:10）；根 `data/bug_log.jsonl` mtime Apr 6 无 9 月追加；被追加的是**车道自己的** `data/bug_log.jsonl`（6221 B，Sep 3 02:08）。`.gitignore:197` `data/*.jsonl` 与 `data/lancedb/` 盖住，git 判据恒绿 | `ls _versions`、`stat` |
| 主干无 `test_g3_2_review_ledger.py`（W7 未合）；`test_learning_events_schema_contract.py` 195 / `test_fsrs_bridge.py` 10 / `test_learning_event_log.py` 6 | collect-only |
| `docs/learning-events-schema-v1.md` §6.1 `:88` / §6.2 `:110` / §6.3 `:279` | grep |

## 二 车道与第 0 分钟
NEW：`git -C …/feature-obsidian-hybrid-dev worktree add ../card-x7-ledger-c -b card/x7-ledger-c 1f249b33f0d3380fd0fe7e0b26bdf08576da54ee`；cp `.env`；`mkdir -p _bmad-output/审查/prompts`；`PYTEST=…/card-v5-lance/backend/.venv/bin/pytest`。`card-w7-ledger` **只读**（不 commit、不 checkout、不 stash；工作树改动只能 `git -C card-w7-ledger diff > <scratchpad>/w7-worktree.patch` 导出后读）。

## 三 完成条件（AND）
- (a) **部署拓扑定案**写进验收单头部：live SKILL.md untracked、439 vs 443、合入 feature ≠ 上线；上线步骤 = 「备份 live 439 行副本（sha）→ 用户批准 → cp → 复核 sha」，本批不执行。
- (b) 移植快照 commit：从 `56bfe9d4` 取 `SKILL.md`、`backend/tests/regression/test_g3_2_review_ledger.py`、`g32b_mutation_gates.py`（evidence 目录）、`canvas-vault/.claude/scripts/fsrs_bridge.py`、`backend/app/services/learning_event_log.py`（若 W7 改过 `:86-88`），再叠加导出的工作树 patch（含 `_canon_tree` 显式栈修复 + 163 行 round-17 门）；commit body 写明来源 SHA + patch sha256；**不带任何 `*.stderr*`**。
- (c) 先红：`git ls-files '*.stderr*'` 必须为空（门）；round-17 的 md 正文（非 stderr）以 `codex-review-CARD-G3-2b-round17.md` 入库作取证。
- (d) 裁决点⑭ 更正：如实写「仓库根同表 11 manifest（Sep 1，非本卡写入者待查）；本卡残留在车道 data/」；处置默认「两者都不动，登记」（待用户）。
- (e) 工作树 4 文件改动逐文件归属：prompt md → 取证（入库）；mutation_gates → C 卡；ledger test 168 行 → B 卡（round-17 门）；SKILL.md 259/44 → 拆：`_canon_tree` 栈实现归 B，其余按 hunk 标注。
- (f) 移植后基线：`test_g3_2_review_ledger.py` collect 数记录（车道版 5300+ 行）；`pytest` 结果**如实**（预期 round-17 三门红——那是 B 卡的先红）；四个存量文件 195+10+6 全绿。
- (g) 与 G3-1 契约：`docs/learning-events-schema-v1.md` §6.1-6.3 冻结条款零改动（本卡只登记 R6「身份键排除裁决未回写 §6.2」为 B 卡加性追加项）。
- (h) round-17 其余 5 条（HIGH foreign 提升、MEDIUM pred_id 方向 / markerless legacy / mutation 假杀 2 条 + M141 / LOW 短语碰撞）分派：HIGH + pred_id → B；markerless → C；mutation + LOW → 本卡登记。
- (i) 不送 Codex（本卡是取证/移植，无产品语义变化）。

## 四 裁判命令
1. `cd …/card-x7-ledger-c && git ls-files '*.stderr*' | wc -l` → 0。
2. `cd …/card-x7-ledger-c/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/regression/test_learning_events_schema_contract.py tests/regression/test_fsrs_bridge.py tests/regression/test_learning_event_log.py` → 211 全绿。
3. `… $PYTEST -q -p no:cacheprovider tests/regression/test_g3_2_review_ledger.py -k "round17"` → 红态原文贴验收单（B 卡的先红基线）。
4. `shasum -a 256 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.claude/skills/quiz-answer/SKILL.md` = `9652e1e1…`（live 未动）；`shasum -a 256 …/canvas-learning-system/canvas-vault/learning_events.jsonl` 开工/收工同。
5. `git log --format='%s' 1f249b33..HEAD | grep -c 'CARD-G3-2c-A'` = 本卡 commit 数。

## 五 禁改与隔离
live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**` 只读；`card-w7-ledger` 只读；`docs/learning-events-schema-v1.md` §6 冻结；`learning_event_log.py` `append_event` 幂等语义不动；禁目录级 pytest（整目录 regression 收集会连现网并写 data/——UAT 自述就是这么污染的）；`*.stderr*` 不入库；不动台账；不 push。

## 六 默认裁决（待用户）
D1 拓扑：按「合入 ≠ 上线，上线另批」处理；D2 快照移植（不 cherry-pick 28 commit）；D3 ⑭ 两处残留都不动、登记；D4 stderr 只留 md；D5 round-17 5 条分派如 (h)。

## 七 验收单
`…/card-x7-ledger-c/_bmad-output/验收单/UAT-CARD-G3-2c-A-安全取证与移植-<日期>.md`：4-A 裁判 1-5 + 归属表 + patch sha；4-B「无变化（这一张只是把之前散落的工作收进仓库、把哪些文件在线上说清楚）」；「待你裁决」D1-D5；「本卡未证明什么」必填；「台账待登记条目」。commit header ≤100 含批次标记，body 行 ≤100；不 push。
