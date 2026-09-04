> ⚠️ 本文件是 CARD-G3-2c-E 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z6-B 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-G3-2c-E]`。车道：`card-x7-ledger-c`，**前提 Z6-A 已独立 commit**。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-G3-2c-E — g32cb 去硬编码 venv + `q_()` 纵深层补变异承重

## 〇 事实
| 事实 | 位置 |
|---|---|
| `g32cb_mutation_gates.py:47-49` 把 pytest 钉死在 `card-v5-lance/backend/.venv/bin/pytest` 绝对路径，无环境变量覆盖；该车道一旦清理脚本即报废。g32b 已在 `:497-517 _PYTEST_BIN()` 修过同型缺口（`G32B_PYTEST` → 车道 venv → SystemExit 报错），g32cb 没跟上 | 两脚本 |
| g32cb 共 8 条变异（M1–M8），流程：装 SIGTERM/INT/HUP handler → `_self_heal()` 还原残留 → 全文件 sha 基线 → **绿态前提**（每道门 rc=0 否则 return 2）→ 串行变异 → 跑后 sha 复核（不一致 return 3）→ `n/8 KILLED`（不足 return 1） | `g32cb:38 / :150-155 / :184-197 / :203-215 / :236-260` |
| M154/M159 退役后 `q_()` 的往返自证是**纯纵深、零承重**——UAT 自陈「那一层若失效不会被任何门发现」（X7-C 验收单 :185 附近） | UAT-CARD-G3-2c-C |
| g32cb 顶部 `:26-36` 记录 M4/M5 两次踩坑：拆防线不要改参数；门若从实现读常量，变异该常量对门不可见 | 教训 |

## 一 完成条件（AND）
- (a) g32cb 的 PYTEST 解析改为「环境变量 `G32CB_PYTEST` → 车道 `backend/.venv/bin/pytest` → 明确报错」，形态与 g32b `:497-517` 一致；不改其余判据与自愈逻辑。
- (b) 为 `q_()` 往返自证新增一条承重变异：变异体拆掉 `q_()` 的往返/转义，并**同时挂 depth 层**禁掉前置的字符轴校验器（否则必 SURVIVED）；绑定一道能独立归因的窄门。
- (c) 新变异必须过空变异对照：只加层时门为绿（或红但失败身份不同），否则判假杀、撤层重设计——对照结论逐条写进验收单。
- (d) 复跑 g32cb 全量：绿态前提全绿 → 9/9 KILLED（8 原 + 1 新）→ 跑后 sha 一致 → rc=0。
- (e) 若新变异实测 SURVIVED 且无法用合法 depth 层救活：如实结论「`q_()` 纵深不可变异，行为只由集成门锁定」写进 g32cb 顶部注释（与 M16/M21/M22/M25 同类处置），不得伪造击杀。
- (f) 跑前跑后全文件 sha 基线（SKILL.md / validate_learning_events.py）一致；`git status --porcelain` 空；`grep -rn 'MUTANT' canvas-vault/ backend/` → 0。
- (g) 一轮 Codex（gpt-6-astra ultra），审查面 = 本卡 diff（g32cb + 新门）。

## 二 裁判命令
1. `grep -n 'card-v5-lance' backend/scripts/g32cb_mutation_gates.py | wc -l` → 0；`grep -n 'G32CB_PYTEST' backend/scripts/g32cb_mutation_gates.py` 有命中。
2. `<venv>/python backend/scripts/g32cb_mutation_gates.py --list` → 9 条。
3. `G32CB_PYTEST=<venv>/pytest <venv>/python backend/scripts/g32cb_mutation_gates.py > _bmad-output/审查/evidence-g32cb/run-r2.txt 2>&1; echo rc=$?` → rc=0，末段 `9/9 KILLED`；「绿态前提」段 9 行全 `rc=0 ✅`。
4. 跑后 `shasum -a 256 canvas-vault/.claude/skills/quiz-answer/SKILL.md backend/scripts/validate_learning_events.py` 与跑前相同。
5. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/regression/test_g3_2_review_ledger.py` → 不回退。

## 三 禁改与隔离
禁为凑 KILLED 改门期望值或上限常量；禁把 depth 层拆到**被测那道防线本身**（制造假杀）；禁部署到 live skill；live vault 只读；禁 Neo4j 7691 写入；禁目录级 pytest 之外的变异并发（同车道串行）；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-G3-2c-E.md` → `codex-review-CARD-G3-2c-E.md`，1 轮）。验收单 `…/验收单/UAT-CARD-G3-2c-E-<日期>.md`：DoD-3 双段；4-B「无变化（一个检查脚本以前只能在特定电脑目录下跑，现在哪里都能跑；并多加了一条自检）」；「本卡未证明什么」必填：g32b 全量表由 Z6-C 负责；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z6-C。**
