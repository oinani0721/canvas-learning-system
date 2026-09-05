> ⚠️ 本文件是 CARD-RV-E 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y4-A 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-RV-E]`。车道：`card-z7-tool`（分支 `card/z7-tool`，HEAD `df39bf21`，主 session 已预合主干 03ac8bf8（4505ee90 merge，干净；代码面与主干逐字节等同：`git diff --stat 03ac8bf8 HEAD -- . ':(exclude)_bmad-output'` 为空），venv symlink 已建 → `card-v5-lance/backend/.venv`），**无前提**（本车道首卡）。只读 `--add-dir /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/resilient-mapping-forest`（fix/test-infra-paralysis 分支树 66d6a835，本卡不用，Y4-D 取证）。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 存档首部 / §2.2 裁判落盘 / §2.3 环境通告）。

# CARD-RV-E — Z7-A 门重写 870e52b3 复审 + 换行残孔定性（纯复审，零代码改动；把「Codex 审过的门」与「主干上跑的门」对上号）

## 〇 事实
| 事实 | 位置 |
|---|---|
| Z7-A 的 Codex 存档首部自证绑定止于 `304f03ca..b20fe550`；mutant-residue-scan 的**现行实现**是审后 commit `870e52b3`（`fix(lint): 变异残留门补 6 处静默放行 + 撤回 target-version`），零复核 | `_bmad-output/审查/codex-review-CARD-TOOL-lint-glob.md:4`；`git log --oneline -1 870e52b3` |
| 审面 = `git diff --stat b20fe550 870e52b3 -- lefthook.yml ruff.toml` → `2 files changed, 88 insertions(+), 32 deletions(-)`（lefthook.yml 98 / ruff.toml 22）；两文件在主干 HEAD 与 870e52b3 **逐字节相同**：`HEAD:lefthook.yml` = `870e52b3:lefthook.yml` = `17dacb73…`，`HEAD:ruff.toml` = `870e52b3:ruff.toml` = `fdc227b0…` ⇒ 可在主干 / 车道树整份读，不必切树 | `git rev-parse` |
| 主干 `lefthook.yml` 全文 435 行；残留门块锚：块头 `mutant-residue-scan:` :286 / `MARKER="MUT""ANT"` 两段拼接 :289 / `mktemp -d` :290 / `FAILED=0` :293 / `--name-only --diff-filter=AM -z` :294-295 / `tr '\000' '\n'` :298 / `while IFS= read -r f` :301 / 排除名单 case :303-307 / `--literal-pathspecs diff --cached … -- "$f"` :308-309 / FAILED 置位 :310、:319 / awk :312-319（`/^diff --git /` :313、`/^@@/` :314、`!inhunk` :315）/ `done < "$TMPD/list"` :320 / FAILED 出口 :321-324 / hits 出口 :325-333 / OK :334 | `awk 'NR>=286 && NR<=334 {print NR": "$0}' lefthook.yml` |
| 防御注释 :269-285 逐条对应 Codex round-1 的实测反例：`-z + tr`（:269-271，只声明防 `"`/`\`/TAB，**未提换行**）/ `--literal-pathspecs` :272 / `--no-color` :273-276（须用 diff 标志，`-c color.ui=never` 会被 `color.diff` 盖过）/ `--no-renames` :277-278 / awk inhunk :279-281（只有 `@@` 之前算文件头）/ FAILED 位 :282 / `mktemp -d` 0700 :283 | `sed -n '269,285p' lefthook.yml` |
| 执行时机注释 :259-268：lefthook 2.1.6 对无 `priority` 的命令**按命令名字母序**执行（c → g → m → python-lint → p → r → 两个 spec-sync），任何 `priority` 值都把该块排到最前——写的是「2026-09-05 实测」，**没有源码出处链接**（`grep -n 'exec_unix\|evilmartians' lefthook.yml` 零命中）。**勘误**：底稿 (e) 说「注释已给 exec_unix.go 链接」不成立 | `sed -n '259,268p' lefthook.yml` |
| 换行残孔（第十一批复核报告 §五.7 登记）：含换行的文件名经 :298 `tr` 拆成两段 → :301 逐段读 → :302 两段都非空 → :303-307 不在排除名单 → :308 对不存在路径取 diff。只读探针实证：`git --literal-pathspecs diff --cached -- "$(printf 'no/such\nfile')"; echo rc=$?` → **rc=0、无输出** ⇒ :310 不置位、awk 无输入无 hits → :334 OK。链条成立，属 fail-open | `_bmad-output/审查/2026-09-05-第十一批复核裁定与待裁决登记.md:56`；本机实测 |
| 主干 `ruff.toml`：`line-length = 120`（D-2 用户裁保留）、`[lint] select = []`、**刻意不写 target-version**（曾加 py312 已撤回，三条原因写在文件注释里）；`lefthook.yml` 自身无 `MUTANT` 字面量（`grep -c MUTANT lefthook.yml` = 0）、无 `priority:` YAML 键（唯一命中是 :266 注释） | `cat ruff.toml`；`grep` |
| 本机两个 lefthook：git hook 实际用 `/opt/homebrew/bin/lefthook` = **2.1.6**；`npx lefthook` = 1.13.6，flag 集不兼容（2.1.6 是 `--command` 单数、`--force`、`--no-auto-install`），且 `npx lefthook run` 会隐式重装共享 `.git/hooks` | `/opt/homebrew/bin/lefthook version`；`lefthook run --help`；台账 X8 ③④ |

## 一 完成条件（AND）
- (a) 审面写死且先证可读：`git rev-parse HEAD:lefthook.yml 870e52b3:lefthook.yml` 与 `git rev-parse HEAD:ruff.toml 870e52b3:ruff.toml` 每对两行相同；`git diff --stat b20fe550 870e52b3 -- lefthook.yml ruff.toml` = `2 files changed, 88 insertions(+), 32 deletions(-)`。复审读的是**这 120 行 diff + 主干 `lefthook.yml:250-334` 整段**，不读工作区、不读摘要。
- (b) 六处「静默放行」补法逐条判定，每条给 `lefthook.yml:行` + 一句「补上了 / 没补上 / 补出新洞」，写进验收单表格：① `-z + tr`（:294-295 + :298；对 `"`/`\`/TAB 补上了；对换行**补出新洞**，见 (c)）② `--literal-pathspecs`（:308）③ `--no-color`（:294、:308，须核是 diff 标志不是 `-c`）④ `--no-renames`（:294、:309，与 `--diff-filter=AM` 同行）⑤ awk inhunk（:313-315：`diff --git` 复位 / `@@` 进 hunk / 非 hunk 行丢弃）⑥ FAILED 位（:293 初值、:310/:319 置位、:321-324 出口；:291/:296/:299 直接 exit 1）。`mktemp -d` 0700（:290-292）是第七项加固，单列不计入六处。判定用原文与只读探针，不采信作者自述。
- (c) 换行残孔定性：写清链条 :298 → :301-302 → :308（rc=0 无输出，只读探针 `git --literal-pathspecs diff --cached -- "$(printf 'no/such\nfile')"; echo rc=$?` 实证）→ 不置 FAILED、不进 hits → :334 OK。按现行判据定级：**非数据丢失 / 非 live 写 / 需人为造含换行文件名 ⇒ 登记级**（不是阻断级）；同时如实写「与块自称 fail-closed 矛盾」。修法写成 **Y4-C（CARD-TOOL-residue-newline）的输入**：去掉 :298-299 `tr` 中转，:301 直接以 NUL 分隔消费 :294-295 的 `-z` 输出（bash 形态 `while IFS= read -r -d '' f`；:320 `done <` 改读 `$TMPD/names`），解释器由 Y4-C 实测。本卡**不落地**。
- (d) `ruff.toml` 22 行三条结论各一行：① `target-version` 已撤回且文件注释里的三条原因成立（pyproject `requires-python>=3.9` 推断 py39 / 原证据被自己的 format 抹掉 / CI 用 3.11-3.12）；② `line-length = 120` = D-2 用户裁保留，与 pyproject / backend/ruff.toml 对齐；③ `[lint] select = []` ⇒ `scripts/` 仍只是语法 + 格式门，未定义名放行——**本卡不动**，登记第十三批。
- (e) 执行时机断言复核：:259-268「按命令名字母序 / priority 排最前」是本机实测记录、**无源码出处**（勘误底稿）。Codex prompt 三节里问「该断言有无 lefthook 2.1.6 源码或文档出处」；无论有无，验收单如实登记为「有出处：<路径/链接>」或「仅本机实测，无出处」，**不追认**。
- (f) Codex 一轮：prompt `_bmad-output/审查/prompts/codex-prompt-CARD-RV-E.md`（五分节，读取面写死 = (a) 的 120 行 diff 文件 + `lefthook.yml:250-334` + `ruff.toml` 全文；问题按重要性：六处补法真伪 → 换行残孔定级 → 字母序断言出处 → ruff.toml 三条；措辞用「负控输入 / 未被拦下的输入 / 门未覆盖的路径」）；存档 `codex-review-CARD-RV-E.md` 首部按协议 §2.1 六行。0 字节按协议 §1 重发一次，再 0 字节报主 session 人审替代。
- (g) 零代码改动：收工 `git status --porcelain` 为空且 `git diff --stat df39bf21 HEAD -- . ':(exclude)_bmad-output'` 为空；commit 只含 `_bmad-output/`（prompt / 存档 / evidence-rv-e / 验收单）。
- (h) 「本卡未证明什么」必填：不修换行残孔（Y4-C）；不动 `scripts/` lint 规则集（第十三批）；不碰 pyright 门（Y4-B）；未在暂存区放任何含标记的文件试门，因此**没有**跑过一次真实 BLOCKED（Y4-C (b) 才做）；字母序断言若无出处则仍是「实测」不是「规格」。「台账待登记条目」必填：Z7-A 行补「870e52b3 已由 RV-E 复审，六处判定 = …」；§五.7 换行残孔定级「登记级 → Y4-C 修」；`ruff.toml` `select=[]` 移交第十三批；:259-268 无出处；本卡不引台账 Z3-A 行的任何「+962」类数字。

## 二 裁判命令
（车道树 `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool`；承重输出 `2>&1 | tee _bmad-output/审查/evidence-rv-e/<name>-$(date +%Y%m%dT%H%M%S).txt`，末行 `echo rc=$?`——`tee` 会吞退出码，用 `set -o pipefail` 或 zsh `$pipestatus[1]` 取被测命令的 rc）
1. `git rev-parse HEAD:lefthook.yml 870e52b3:lefthook.yml; git rev-parse HEAD:ruff.toml 870e52b3:ruff.toml` → 四行两两相同（`17dacb73…` ×2 / `fdc227b0…` ×2）。
2. `git diff --stat b20fe550 870e52b3 -- lefthook.yml ruff.toml` → `2 files changed, 88 insertions(+), 32 deletions(-)`；`git diff b20fe550 870e52b3 -- lefthook.yml ruff.toml > _bmad-output/审查/evidence-rv-e/audit-face.diff`（这就是送审面）。
3. `awk 'NR>=286 && NR<=334 {print NR": "$0}' lefthook.yml` → 286 块头 / 298 tr / 301 while / 308 literal-pathspecs / 320 done / 334 OK 逐一对上；对不上 = 主干漂移，停下报主 session。
4. 只读探针：`git --literal-pathspecs diff --cached -- "$(printf 'no/such\nfile')"; echo rc=$?` → 无输出、`rc=0`（(c) 链条的关键一环）。
5. `/opt/homebrew/bin/lefthook version` → `2.1.6`；`/opt/homebrew/bin/lefthook run pre-commit --command mutant-residue-scan --force --no-auto-install; echo rc=$?`（**空暂存区**）→ `[Mutant-Scan] OK …`、rc=0。禁 `npx lefthook`。
6. `grep -n 'exec_unix\|evilmartians' lefthook.yml; echo rc=$?` → rc=1（零命中，(e) 勘误证据）。
7. 收工：`git status --porcelain`（空）；`git diff --stat df39bf21 HEAD -- . ':(exclude)_bmad-output'; echo rc=$?`（stdout 空且 rc=0；写法必须是 `':(exclude)…'`，`':!…'` 在 zsh / git 2.50 下 rc=128 且 stdout 空会假绿）。

## 三 禁改与隔离
- 禁改 `lefthook.yml` / `ruff.toml` / `pyrightconfig.json` 任一字节——换行残孔修法只写成 Y4-C 输入；本卡是**纯复审**。
- `lefthook.yml` 本批只 Y4 写，Y4 内部三段互斥：:147（Y4-B）/ :286-340（Y4-C）/ pre-push 两命令 frontend-test :391-400 与 backend-smoke :419-435（Y4-D）；本卡零写。
- 设计稿 §0 的 D-14 pyright 绕过口径对本车道**不适用**：本车道改的就是门。本卡虽零代码，commit 时也不得带 `LEFTHOOK_EXCLUDE`，提交须让 hook 真跑并在验收单贴每个 command 的 SKIP/PASS 与 rc。
- 禁在暂存区放任何含 `MUT`+`ANT` 字面量的文件试门（只读探针取代）；禁 `npx lefthook`（1.13.6 flag 不兼容）与 `npx lefthook run`（隐式重装共享 `.git/hooks`）。
- live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/` 只读；禁连 7691/7687；本卡不跑 pytest。
- 别人的地盘（设计稿 §5）一律不碰：review_app / review_overview / daily_review_* / live_port_guard / conftest / g33 与 g32* / fsrs_bridge / decay_beta / quiz-answer SKILL.md / system.py / spec-tools / openapi.json。
- 台账不改（写「台账待登记条目」）；`*.stderr*` 不入库（`.gitignore:258-261`）；不 push。

## 四 Codex / 验收单
命令同协议 §2（`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat …/prompts/codex-prompt-CARD-RV-E.md)" > …/codex-review-CARD-RV-E.md 2> …/codex-review-CARD-RV-E.stderr </dev/null`，1 轮）；prompt 五分节参照 `_bmad-output/审查/prompts/codex-prompt-CARD-W4-3b.md`：一 背景 + 最小读取面写死（`evidence-rv-e/audit-face.diff` + `lefthook.yml:250-334` + `ruff.toml`）/ 二 作者自述请独立核对（六处补法表初稿 + 残孔链条 + 定级）/ 三 按重要性排序的问题 / 四 输出格式 / 五 边界（只读、不跑 hook、不提议改代码）。存档首部按协议 §2.1 六行（模型 / reasoning_effort / codex 版本 / 绑定 = `b20fe550..870e52b3`，并写明 HEAD 同 blob / 会话头三行）。顺序：裁判全跑 → 送 Codex → 之后只改 `_bmad-output`。验收单 `_bmad-output/验收单/UAT-CARD-RV-E-<日期>.md`：DoD-3 双段；4-B「无变化（把上一批改过的一道提交前检查重新读了一遍，确认它现在拦得住什么、拦不住什么；发现一种极端文件名会漏过去，安排下一张卡修）」零技术词；「本卡未证明什么」「台账待登记条目」按 (h) 必填。commit header ≤100 含 `[BATCH-2026-09-05-第十二批 / CARD-RV-E]`，body 行 ≤100（`wc -m`）；不 push；跑完说「复核第十二批 Y4」。**独立 commit 后同车道继续 Y4-B。**
