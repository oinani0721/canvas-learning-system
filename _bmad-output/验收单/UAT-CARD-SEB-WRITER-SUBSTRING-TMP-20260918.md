# UAT · CARD-SEB-WRITER-SUBSTRING-TMP

> **批次** `[BATCH-2026-09-18-第十五批 / CARD-SEB-WRITER-SUBSTRING-TMP]` · 车道 `card-p6-skills-w`（分支 `card/p6-skills-w`）本车道 **1/4** 首卡
> **终态字段（收工重算）**：最终代码 SHA `13ab1b37bd7840a26e568a71a5c77bd3e6d30b13`（= 唯一的代码 commit，也是两轮 Codex 的审查绑定 SHA）· commit 数 `2`（`13ab1b37` = 代码 + 证据；第二个 commit **仅** `_bmad-output`：Codex 两轮存档 + 本单收口 —— ⛔ 这里**不写它的 SHA**：本单是它的内容之一，写了就成自指，改一次 SHA 变一次。它不进终审绑定面，绑定只看 `13ab1b37 → HEAD` 排除 `_bmad-output` 的 diff）· Codex 轮次 `2`（末轮 r2 绑最终 HEAD，BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 0）
> **B15_BASE** `9c4e7e82` · 卡文 `…/goal-cards/第十五批-goals/P6-A.md` · 协议 `.claude/rules/card-batch-protocol.md`
> **手册地盘行（原文抄录，§452）**：`| **P6** | card-p6-skills-w | **P6-A**（CARD-SEB-WRITER-SUBSTRING-TMP） | P6-A → P6-B → P6-C → P6-D | C2-06 首张（数据丢失面：新事件被当重复丢弃）。改 SKILL.md 后 tests/skills 目录级 + lint 指纹基线随卡更新并声明。⛔ canvas-vault/.claude/scripts/fsrs_bridge.py / decay_beta.py 零写者；两张 SKILL.md 改动不在 da…`
> **证据目录** `_bmad-output/审查/evidence-seb-writer/`（承重存档全文件名见各段，⛔ 不用 glob 引用）

---

## 1. 🎯 一句话目标

出检验白板时那条「我今天考了这个节点」的学习记录，以后不会再因为**名字碰巧撞上以前某条记录里的一个字**而悄悄没写进去；账本里有一行坏掉的旧内容，也不会把新记录挡在门外。

---

## 2. 📖 你的视角

作为一个用 `/start-exam-board` 出检验白板的学习者，
我想要**每出一张板，就确实留下一条对应的学习记录**，
以便后面的复习排期、掌握度演化、Dashboard 统计都建立在一本**不缺条目**的账上。

---

## 3. 🖥️ 交互流程（用户屏幕变化）

```
你在 Obsidian 侧栏输入 /start-exam-board（或带 node <节点> 定向考察）
        ↓
屏幕上出现一张新的检验白板（检验白板/<板名>-<时间戳>.md），第一道题已经在上面
        ↓
屏幕底部出现一行回执：「事件已落日志: exam_created」
        ↓
（改前的坏情况）某些时候这行回执照常出现、白板也照常生成，
  但账本里那条记录**根本没写进去** —— 屏幕上看不出任何异常
        ↓
（改后）同样的情况下，记录确实写进去了；屏幕行为完全不变
```

---

## 4-A. 🤖 Claude 已代验（技术断言全归本段）

### (a) 第 0 分钟 + §〇 file:line 核对

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-p6-skills-w` ✅ |
| 分支 / HEAD | `card/p6-skills-w` / `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680` ✅ = B15_BASE |
| `git status --porcelain` | 0 行 ✅ |
| `backend/.venv/bin/pytest` / `backend/.env` | 均在位 ✅ |
| pyright 自证 | `card-v5-lance/backend/.venv/bin/pyright` 可执行 ✅（本卡零 `backend/app` 改动，(h) 不适用） |
| `grep -vc '^#' "$BASE"` | **33** ✅（BASE = `feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b15/unit-red-baseline-9c4e7e82.txt`） |

**§〇 file:line 逐条核对结果**：`SEB:430/:435/:473/:477`、`cas:46-52/:144`、`schema:964/:1012/:1018/:1022`、`lint:86/:115/:1989-1999/:2043-2050/:3213`、`lint-test:243/:262/:1291/:1993/:2071` **全部与卡文逐字同**。

**两处漂移（如实登记）**：
1. 卡文 §〇 写 `os.remove(P)` 在 `:494` → **实测 `:493`**（`:494` 是 `PYEOF`、`:495` 是 fence 关闭）。§二.1 的 `sed -n '…;494p'` 因此取到的是 `PYEOF` 而非 `os.remove(P)`；不影响任何判据（承重判据不含行号锚）。
2. 卡文 §〇 提到 `test_skill_portability_lint.py` docstring 里写 schema 侧钉点 `:1013/:1017`，**实测 `:1018/:1022`**（卡文已预告此更正）；本卡改 docstring 时一并换成「文件名 + 条目名」形态，不再写行号。

### (b) 先红（改代码前落档）

| 判据 | 实测 | 存档全文件名 |
|---|---|---|
| ① 结构基线 | `in_ln=1 replace=1 eq=0 card=0`；三文件 `bare=2 ns=0`；`tmp_all=6 tmp_ns=4`；sha `0f2c085a…` | `struct-open-20260918T165458.txt` |
| ② AST 门改前 | `HEAD (1, 0, ['Exception','OSError'])`、`BASE (1, 0, …)` | `ast-gate-open-20260918T165538.txt` |
| ③ 新门改前红 | `collected 5`；门① 门② **FAILED 且红在 `_count_event_id(...) == 1`**（`assert 0 == 1`），门③④⑤ passed；`rc=1` | `seb-red-20260918T165731.txt` |
| ④ 既有四文件改前绿 | `collected 412` → `411 passed, 1 skipped`，**0 failed**，`rc=0` | `named-open-20260918T165801.txt` |

> ⚠️ **一次自查到的假值（如实登记）**：首次跑 ① 时把 `grep -cF 'decode("utf-8", "replace")'` 写在双引号 `echo` 里的命令替换中，引号被吃掉 ⇒ 该项输出 `replace=0`（文件里明明有 1 处）。按「期望 0/空 的判据必须先证输入面非空」当场复验，确认是引号问题而非文件问题，改成逐行赋值 + 单引号并**给六个模式各配一条独立正例验伪锚**（`anchor …=1` 六项）。那份带假值的存档已删除、不入库；现存 `struct-open-*` 是修正后的运行。

### (c)(d) 实现

- **(c) 写规修复**（`SKILL.md` Step 6.5 fence 内，原 `:473-477` 五行 → 31 行）：`raw = b"".join(_chunks)` → `raw.split(b"\n")` + 尾 LF 去除 → 逐行 `json.loads(_bl.decode("utf-8"))`、`except (ValueError, RecursionError): continue` → `isinstance(_rec, dict) and _rec.get("event_id") == evid` ⇒ `seen = True; break`。形态**逐字沿用 T7-B 的 ai-linked-doc `:300-334`**，注释保留三条「为什么」（禁 splitlines / 禁整本 replace / 禁整本严格）。
  锁段、短写守卫、失败契约、`os.remove(P)` **一个字节没动**（见 (l) diff）。
- **(d) 裸 `/tmp` 真解耦（5 文件同批）**：SKILL.md `:430` prose 自带 `mkdir -p /tmp/cls-exam/`（⛔ **不能靠 Step 3 那次** —— `:126` 写明 `node` 参数命中时 Step 3 整步跳过）、`:435` `P = "/tmp/cls-exam/exam-created-event.json"`；`test_g3_3_cas.py` 仅 `:49/:144`；`test_learning_events_schema_contract.py` 仅 `:1018/:1022`；lint 模块两张表 + digest + docstring；lint 测试 `bare_tmp(seb) 2→0` + ⑦ 负控改靶。

> ⛔ **卡文遗漏项（本卡实跑发现并处置）**：卡文 (d) 只点名 `BASELINE` / `ESCAPING_TMP_BASELINE` / `MANAGED_FILE_DIGESTS` 三张表，实跑 `named-close-20260918T171034.txt` 抓到**另有 4 张按行号/内容指纹钉 start-exam-board 的表**同样漂移 —— `TMP_BLOCK_BASELINE`（块指纹）、`SUSPICIOUS_TMP_LINES_BASELINE`、`OPAQUE_TMP_BASELINE`、以及依赖它们的 6 条负控与 `test_negative_control_untouched_copy_is_green`。根因是查重段由 5 行展开成 31 行 ⇒ 其后每一行 `+26`。四张表**全部实测后贴入**（`lint-table-close-20260918T171623.txt`），仍在「仅数据表 + docstring」的地盘内；手册 §452 原文「lint 指纹基线随卡更新并声明」即覆盖此面。
> ⚠️ 因此证据目录里有**两份** `named-close`：`named-close-20260918T171034.txt` = 4 张表未同步时的中间态（18 failed，正是它抓出遗漏）；`named-close-20260918T171558.txt` = **终态**（411 passed / 1 skipped / 0 failed）。引用时勿混。

### (e) 普查（只登记不改）

| 结论 | 实测 |
|---|---|
| 9 份 SKILL.md 中 **T7-B 形态（写点嵌在 prompt 模板 fence 内）= 0 处** | `files= 9  flagged_fences= 1` |
| 唯一 FLAG = `start-exam-board/SKILL.md:303-308`（无标签 fence，`Bash: curl … targeting-material`） | **判非缺陷**：它是给**执行者**的指令 fence，不是给生成器的 prompt 模板 |
| tag=`markdown` 的模板 fence 共 7（board-recap 1 / exam-quick 1 / start-exam-board 1 / study-question 4），其内执行动作关键词 **0 命中** | 同上存档 |
| 同族有损解码残留 1 处 = `quiz-answer/SKILL.md:3087` | **本卡只登记不改**（P6-B 地盘）。它 `:3091-3095` 逐行 `json.loads` + 跳过 `ValueError`、**`:3096`** 做 `event_id` 等值判断（行号由 Codex r2 独立核对更正，原写 `:3091-3095` 未含等值那一行） ⇒ **无子串面，只剩有损解码半个同族** |
| 验伪锚（证明脚本真读到 fence 内容） | ```bash fence 内 PYEOF：ai-linked-doc 2 / quiz-answer 4 / start-exam-board 6 ✅ |

存档：`skill-fence-census-open-20260918T170045.txt` / `skill-fence-census-close-20260918T173255.txt`。
**两侧 diff 只有 2 行消失**（SEB 自身 `:473/:477` 的同族命中），其余逐字不变 ⇒ 普查确实只登记未改。

### (f) 结构判据（改前 X / 改后 Y **成对**）

存档：`struct-open-20260918T165458.txt` ↔ `struct-close-20260918T171044.txt`（**同一个脚本 `struct-judge.sh` 跑两侧**，口径逐字同）

| # | 判据 | 改前 | 改后 |
|---|---|---|---|
| ① | `grep -cF 'in ln for ln in _lines' $SEB` | 1 | **0** ✅ |
| ② | `grep -cF 'decode("utf-8", "replace")' $SEB` | 1 | **0** ✅ |
| ③ | `grep -cF '_rec.get("event_id") == evid' $SEB` | 0 | **1** ✅ |
| ④ | 裸字面量 SEB / cas / schema | 2 / 2 / 2 | **0 / 0 / 0** ✅ ；命名空间字面量 0/0/0 → **2/2/2** ✅ |
| ⑤ | lint `bare_tmp(seb)` | 2 | **0** ✅（`tmp_all 6→8, tmp_ns 4→8`，两端均实测） |
| ⑥ | **AST 门** `In`-Compare-左侧-`json.dumps` / `Eq`-Compare-含-`.get("event_id")` | (1, 0) | **(0, 1)** ✅ ；`except` 处理器集合含 `(ValueError, RecursionError)` ✅ |
| ⑦ | `grep -c 'CARD-SEB-WRITER-SUBSTRING-TMP' $SEB` | 0 | **1** ✅，且 ④ 的裸 0 同时成立 ⇒ 变更记录没把旧字面量写回去 |

**AST 门验伪锚**：同一脚本喂 `git show 9c4e7e82:<SKILL.md>` 的旧文本 → **`BASE (1, 0, ['Exception','OSError'])` 两侧恒定**。它证明脚本在数 AST 节点而不是数文本 —— 修复后的注释**故意保留**「禁用原来的子串写法 `json.dumps(evid) in line`」字样，文本 grep 会在那里假红，AST 不受影响。
**结构判据验伪锚**：六个 grep 模式各喂一条已知为真的独立正例，`anchor in_ln=1 replace=1 eq=1 card=1 bare=1 ns=1` 六项全中 ⇒ 改后的 0 是「文件里真没有」而不是「模式写错了」。

### (g) 承重行为门（新文件 `backend/tests/skills/test_seb_writer_exact_match.py`）

DD-03 禁 mock：`subprocess.run([sys.executable, "-c", code])` 真跑从 SKILL.md **逐字提取**的 PYEOF 块；`vault` / 账本 / 输入 JSON 全部 `tmp_path` 派生；不连任何库。

| 门 | 断言 | 改前 | 改后 |
|---|---|---|---|
| ① `test_substring_dedup_false_positive_loses_event` | 历史行 `event_id="derive:别的"` 而 `node_id` 值恰 `== evid` ⇒ 新事件必须落账 | **FAILED**（`assert 0 == 1`） | passed ✅ |
| ② `test_undecodable_line_is_not_dedup_evidence` | 历史行 `event_id == evid` 但 payload 含 `b"\xff"` ⇒ 坏行不构成 duplicate 证据 | **FAILED**（`assert 0 == 1`） | passed ✅ |
| ③ `test_true_duplicate_is_still_skipped`（对照） | 真重复仍只写一遍 | passed | passed ✅ |
| ④ `test_empty_ledger_twice_writes_once_and_removes_input`（对照） | 二跑幂等 + `P` 每次被 `os.remove` | passed | passed ✅ |
| ⑤ `test_deeply_nested_bad_line_does_not_abort_append`（对照·纵深） | `b"[" * 100000` 坏行不逸出为整次失败（rc 0 + stdout 含「事件已落日志」） | passed | passed ✅ |

`collected 5` 两侧一致。存档 `seb-red-20260918T165731.txt`（rc=1）↔ `seb-green-20260918T171003.txt`（`5 passed`，rc=0）。

### (h) pyright

本卡**零 `backend/app` 改动**（见 (l) 地盘），pyright 不适用。环境自证：`card-v5-lance/backend/.venv/bin/pyright` `test -x` 通过。未用 `LEFTHOOK_EXCLUDE=python-typecheck`。

### (i) 既有套件不回退

| 面 | 开工 | 收工 | 判定 |
|---|---|---|---|
| 点名四文件 | `collected 412` → 411 passed / 1 skipped / **0 failed** | 同左，逐字一致 | ✅ 无回退；`test_managed_files_match_digest_baseline` / `test_bare_values_match_card_expectations` / `test_escaping_tmp_paths_match_baseline` / `test_negative_control_equal_count_swap_must_redden` 四条收工全绿 |
| `tests/skills` 目录级 | `collected 555` → **555 passed，0 红** | `collected 560` → **560 passed，0 红** | ✅ 红集两侧均为空集，diff 无 `>`；+5 = 本卡新门 |
| `tests/regression` 目录级 | `1912 passed, 7 skipped, 1 xfailed`，**0 failed** | `1913 passed, 6 skipped, 1 xfailed`，**0 failed** | ✅ 红集两侧均为空集（`grep -cE '^(FAILED\|ERROR) tests/'` 两侧皆 **0**），diff 无 `>`；收敛耗时 9m10s（< 20min 上限） |
| `tests/unit` 目录级 | 32 failed（BASE 33，差 1 = 基线头自述的 flaky `test_candidate_service::test_accept_candidate_already_accepted_returns_422`）；`diff base.nodeids unit-open.nodeids` **只有一个 `<`，无 `>`** | 32 failed；`diff unit-open.nodeids unit-close.nodeids` **完全相同（diff_rc=0）**；`diff base.nodeids unit-close.nodeids` 仍只有那**一个 `<`** | ✅ 无 `>` |

> **regression 两侧 `7 skipped` → `6 skipped` 的解释（已定位到具体行，不是行为变化）**：`backend/tests/regression/test_daily_review_pick.py:1860` 的 `pytest.skip(f"基线 {_BASELINE_SHA} 不可达 (git show 失败)…")`。开工侧跑在 `git archive` 展开的净树上，那棵树**没有 `.git` 目录** ⇒ `git show` 失败 ⇒ 跳过；收工侧跑在工作树上，`git show` 可用 ⇒ 该条运行并 **passed**。总收集数两侧同为 **1920**。这条恰好把上面那条「判据的环境是判据的一部分」的声明坐实了。

> ⛔ **开工侧目录级的取得方式（如实声明）**：本卡开工时只跑了「点名四文件」，`tests/skills` / `tests/regression` 的**目录级开工侧**是在改动落地后补跑的 —— 补跑**不在工作树上还原**（禁 stash / 禁 checkout-HEAD），而是用 `git archive 9c4e7e82 | tar -x` 在 scratchpad 拉出一份 **B15_BASE 净树**（`backend/.venv` symlink + `backend/.env` 拷入），在那棵树上跑。净树自证：其 `SKILL.md` sha = `0f2c085a1bae1244…` = B15_BASE 原值。⚠️ 这与收工侧**换了运行目录**（「判据的环境是判据的一部分」）：两侧 `rootdir` 不同、`.venv` 为同一个 symlink 目标、`.env` 逐字节相同；两侧均 0 红，故 diff 结论不依赖该差异，但此处如实标出。

存档：`skills-open-20260918T172040.txt` / `skills-close-20260918T172219.txt` / `regression-open-20260918T172204.txt` / `regression-close-20260918T173240.txt` / `unit-open-20260918T165104.txt` / `unit-close-20260918T173240.txt`；nodeid 集 `base.nodeids` / `unit-open.nodeids` / `unit-close.nodeids`。

### (j) openapi

不改端点、零 `backend/app` 改动 ⇒ lefthook `spec-sync-root` 不触发，不适用。

### (k) 负控三段（承重 · 各只拆一层 · 红必须落在指定断言）

> ⛔ **还原基准的偏离声明**：卡文 (k) 写 trap 用 `git show HEAD:<path> > <path>`。本卡跑负控时 **HEAD 仍是 B15_BASE `9c4e7e82`（修复尚未 commit）** ⇒ 照抄会把**整个修复**一起还原掉，而且还原后 sha 与 HEAD 自洽、看起来"还原成功" —— 那是个静默的假绿。按「还原基准是变异前的 sha 不是 HEAD」改为**变异前字节快照**还原，并贴四行 shasum 互证。脚本 `negctl.sh`（入库）。

| 段 | 只拆的那一层 | 期望 | 实测 | 存档全文件名 |
|---|---|---|---|---|
| ① | `_rec.get("event_id") == evid` → 改回子串 `json.dumps(evid, …) in _bl.decode(…, "replace")`（**一行**） | 只红门① | `1 failed, 4 passed`；`FAILED …::test_substring_dedup_false_positive_loses_event`，红在 `assert got == 1`（`assert 0 == 1`）；门②③④⑤ 绿 ✅ | `negctl-seg1-20260918T171824.txt` |
| ② | 逐行 `_bl.decode("utf-8")` → `decode("utf-8", "replace")`（**一处**，查重方式不动） | 只红门② | `1 failed, 4 passed`；`FAILED …::test_undecodable_line_is_not_dedup_evidence`，红在同一条 `assert got == 1`；**门① 仍绿** ✅ | `negctl-seg2-20260918T171856.txt` |
| ③ | `test_g3_3_cas.py` 模块级过滤字面量改回旧值 | collect-time ERROR | `collected 0 items / 1 error`；`ERROR collecting tests/regression/test_g3_3_cas.py` + `assert len(_SEB_BLOCKS) == 1`；`pytest_rc=2` ✅ | `negctl-seg3-20260918T171926.txt` |

**段①②互证**：同一组 5 条门，拆等值层只红①、拆解码层只红② ⇒ 两门测的是**两条不同路径**，不是同一条判据的两个说法。
**段③ 的证明范围（Codex r1 LOW-3 指出后收窄，如实）**：它变异的是 `test_g3_3_cas.py:49` 那处**模块级**过滤字面量，实证的是 **「不同批改模块级钉点 ⇒ 整个文件 collect-time ERROR」** 这一件事 —— 即「同批改钉点不是多余动作」。
⛔ 它**不**证明 T7-C 未证明 #1 的全部内容：`:144`（在 `_exam_board_code()` **函数体内**）单独回退不会造成 collect-time ERROR，而是替换不到目标、`SEB_CODE` 里的路径保持不变；宿主侧的 `mkdir -p → Write` 端到端也**完全不在**本段覆盖内（见「本卡未证明什么」#2）。原表述「闭合 T7-C 未证明 #1」范围过宽，已改为下面这句：**段③ 闭合的是该未证明项里「模块级钉点必须同批改」的那一半**。
**四行 shasum（每段）**：快照 = 变异前 = 还原后，变异后必不同。三段跑完后工作树逐字还原（SEB `c3c0434d…`、cas `6177f313…`），**未与任何目录级长跑重叠**。

### (l) 地盘

```
git --no-pager diff --stat --no-color 9c4e7e82 HEAD -- . ':(exclude)_bmad-output'
```
```
 backend/tests/regression/test_g3_3_cas.py          |   4 +-
 .../test_learning_events_schema_contract.py        |   4 +-
 backend/tests/skills/skill_portability_lint.py     | 106 +++++---
 .../tests/skills/test_seb_writer_exact_match.py    | 296 +++++++++++++++++++++
 .../tests/skills/test_skill_portability_lint.py    |  56 ++--
 .../.claude/skills/start-exam-board/SKILL.md       |  41 ++-
 6 files changed, 440 insertions(+), 67 deletions(-)
```
**恰 6 文件，⊆ 白名单** ✅ 。验伪锚（commit 后才非空洞）：去掉 `':(exclude)_bmad-output'` 后 `--name-only` 多出 **36** 条 `_bmad-output/` 路径。存档 `territory-20260918T175853.txt`。

| 文件 | 约束 | 实测 |
|---|---|---|
| `canvas-vault/.claude/skills/start-exam-board/SKILL.md` | 查重段 + `:430/:435` + 变更记录一条 | 3 个 hunk（`@@ -427,12 +427,12 @@` / `@@ -470,11 +470,37 @@` / `@@ -575,3 +601,4 @@`），共 40 行 ±。**删除行恰 7 条**：`:430` prose 1 条、`:435` `P = …` 1 条、原 `:473-477` 查重段 5 条 —— 锁段 / 短写守卫 / 失败契约 / `os.remove(P)` **一个字节没动** ✅ |
| `backend/tests/regression/test_g3_3_cas.py` | 仅 `:49/:144` | `grep -c '^[-+][^-+]'` = **4**（2 删 2 增）✅ |
| `backend/tests/regression/test_learning_events_schema_contract.py` | 仅 `:1018/:1022`（函数体内） | `grep -c '^[-+][^-+]'` = **4**（2 删 2 增）✅ |
| `backend/tests/skills/skill_portability_lint.py` | 仅数据表 + docstring | ✅ 零 `check_*` 本体 / 零正则 / 零 `TMP_NAMESPACE` 改动 |
| `backend/tests/skills/test_skill_portability_lint.py` | 断言值 + ⑦ 负控靶 + docstring | ✅ |
| `backend/tests/skills/test_seb_writer_exact_match.py` | 新增 | ✅ |

**不得出现且实测零出现**：`quiz-answer/SKILL.md`（P6-B）、`test_g3_2_review_ledger.py`（P6-B）、`vault_lint.py`（P6-C）、任何 `backend/app/**`、`canvas-vault/.claude/scripts/**`、`conftest`、`openapi.json`、别车道文件。
**fsrs_bridge / decay_beta 零写者自证**：B15_BASE sha 与工作树 sha 逐字同（`a766fbcc…` / `3bf4ed94…`，存档 `no-writer-attest-20260918T173320.txt`）。
**ruff 自证**：改动的 4 个已跟踪 `.py` `All checks passed! rc=0`（`ruff-20260918T172407.txt`）；新增未跟踪文件 `git diff` 看不见，**显式补跑** `All checks passed! rc=0`（`ruff-newfile-20260918T172442.txt`）。验伪锚 `F821` 探针 `probe_rc=1`（`backend/ruff.toml` 无 F401，锚必须用 F821），探针已删、`git status` 零残留。

### (m) 现网只读

新门全部路径 `tmp_path` 派生；不读不写 live vault `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/**`；不连 7691/7687/7692（本卡无库需求）。W4 哨兵各承重跑末尾均为 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。
`daily-review-wrapper.sh:99-100` 的 live `cmp` 门只覆盖 `decay_beta.py` / `fsrs_bridge.py` ⇒ **SKILL.md 改动不需要合入当天部署 live**。

### (n) Codex

**模型 / 参数固定**：`gpt-6-astra` + `model_reasoning_effort="ultra"`，`codex-cli 0.153.3`，`--sandbox read-only`。两轮存档首部均按协议 §2.1 抄了 `.stderr` 的三行自证（`OpenAI Codex v0.153.3`(L2) / `model: gpt-6-astra`(L5) / `reasoning effort: ultra`(L9)）；`*.stderr*` **不入库**。两份存档 `grep -c 'gpt-5'` 均为 **0**。

| 轮 | 存档全文件名 | 绑定 SHA | B / H / M / L |
|---|---|---|---|
| r1 | `codex-review-CARD-SEB-WRITER-SUBSTRING-TMP-r1.md`（6152 B） | `13ab1b37bd7840a26e568a71a5c77bd3e6d30b13` | **0 / 0 / 1 / 3** |
| r2 | `codex-review-CARD-SEB-WRITER-SUBSTRING-TMP-r2.md`（4700+ B） | 同上（r1 之后**零代码改动**，只改 `_bmad-output/` 文档） | **0 / 0 / 0 / 0** |

**为什么要 r2**：r1 自己写明「④的独立重算、⑤的全文计数、⑥的原文核对需要超出限定读取面，额外读取请求尚未获答复」——即三个问题它**没有独立核实**，只能转述作者自述。r2 **不改一行代码**，只把那三块读取面补上（lint 判据函数本体 + SKILL.md 全文 + `quiz-answer:3070-3100`），请它独立重算。

**r2 结论（逐项独立重算相符）**：`_body_counts` `tmp_all=8 / tmp_ns=8 / bare=0`；`escaping_tmp_paths` 多重集 `prose:/tmp` ×1 + `prose:Bash: mkdir -p /tmp/cls-exam` ×2；`suspicious_tmp_lines` `[603]`；`opaque_tmp_lines` 4 项；`tmp_block_fingerprints` 7 项；整文件 SHA-256 `c3c0434d385c66f33c097c051d4aac2d05f908a881bc1471785beeaf52493473` —— **与仓库里那四张表 + `MANAGED_FILE_DIGESTS` 逐项一致**，且与作者落档的 `lint-table-close-20260918T171623.txt` / `lint-table-head-20260918T175932.txt` 一致。它还自跑了一段**负控**：内存里把 `603`/`S603` 基线退回 `577`/`S577`，opaque / tmp-block / suspicious 三条判据**全部报不符** ⇒ 这些表不是摆设。
⑤ 全文件五项计数实测 **`0 / 2 / 1 / 0 / 0`**（旧裸字面量 0、命名空间字面量 2 在 `:430/:435`、卡号 1 在 `:604`、`in ln for ln in _lines` 0、`decode("utf-8", "replace")` 0）。
⑥ 同族登记**准确**，并更正了一处行号（等值判断在 `quiz-answer/SKILL.md:3096`，本单已随改）。

**r1 的 MEDIUM×1 + LOW×3 处置（协议：登记不阻断）**：
- MEDIUM「五门未约束字段精确等值」→ **登记，不改代码**（见「本卡未证明什么」#8 + 台账 #11）。⛔ 不扩门的理由：卡文 (g) 明确规定五条门，加第六条属扩范围；且改门 ⇒ 必须再送一轮 + 在新 HEAD 重跑全套承重裁判。建议主 session 另排补门卡。
- LOW①「五门未验证历史保留（`O_TRUNC`）」→ 登记（#9）。
- LOW②「验收单把函数内替换误归为导入期、且扩大了负控③的证明范围」→ **本单已改正**（(k) 段与台账 #2 均已按「`:49` 模块级 / `:144` 函数体内、破法不同」重写，段③ 的证明范围收窄为「模块级钉点必须同批改」那一半）。
- LOW③「台账锚点 `:293` 不存在」→ **是我的 prompt 路径没写全**：权威台账在 `feature-obsidian-hybrid-dev` 树（**295 行**，`:293` = §三.22 (a)(b) 确实存在），车道树里那份 225 行是过期副本。r2 prompt 已注明正确路径。不是内容缺陷。

**末轮绑定自证**：`git --no-pager diff --stat --no-color 13ab1b37bd7840a26e568a71a5c77bd3e6d30b13 HEAD -- . ':(exclude)_bmad-output'` → **空**（见 (l) 段收尾）。

---

## 4-B. 👤 你来验（3 分钟，全在 Obsidian 里完成）

- [ ] 我在 Obsidian 侧栏输入 `/start-exam-board`，选一块原白板 → 我看到一张新的检验白板出现、上面有第一道题 → 我感觉**和以前一模一样，没有任何新步骤要我学**。
- [ ] 我看屏幕底部那行回执「事件已落日志」→ 我看到它照常出现 → 我感觉**踏实**：以前这行字有时候是在骗我（它出现了，记录却没写进去），现在它说写了就是真写了。
- [ ] 我换一个**名字比较特别**的节点（比如名字里带中文破折号、或者和以前某条记录里的字眼撞上），再出一张板 → 我看到这次也照常留下了记录 → 我感觉**这本账终于值得信**：它不会因为"名字碰巧撞上"就把我今天做过的事悄悄抹掉。
- [ ] 我用 `node <某个节点>` 做一次单节点定向考察（这条路会跳过挑选节点那一步）→ 我看到白板照样生成、回执照样出现 → 我感觉**放心**，走捷径的那条路没有被落下。

---

## 5. 🚦 验收结果

- **通过** → 回一句「P6-A 通过」，同车道继续 P6-B（CARD-HARNESS-TREE-PARSE-R2）。
- **不通过** → 在下面批注区写 `[!error]+`，说清楚「你做了什么 / 看到什么 / 期望看到什么」，我按批注修并更新本单 v2。

---

## 6. 📝 批注区

> [!question]+ 你的提问
>

> [!error]+ 你发现的问题
>

---

## 7. 🔗 技术 spec 引用

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P6-A.md`
- 协议：`.claude/rules/card-batch-protocol.md`（§1 合并门 + D-15 / §2.1 存档首部 / §2.2 裁判落盘 / §3 最低覆盖）
- 交接：`_bmad-output/审查/evidence-skill-port-lint-parser/HANDOFF-seb-tmp-decoupling.md`（4 处钉点权威描述）
- T7-B 参照：`canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:300-334` + `backend/tests/skills/test_ai_linked_doc_writer.py`
- 本卡代码：`canvas-vault/.claude/skills/start-exam-board/SKILL.md`（Step 6.5）、`backend/tests/skills/test_seb_writer_exact_match.py`
- 证据目录：`_bmad-output/审查/evidence-seb-writer/`

---

## 五 本卡未证明什么（≥4）

1. **未证明** SEB 块在「尾行截断无 LF」与「event_id 形态非法（裸 U+2028 / 首尾空白 / 超长）」两类输入下的行为 —— ai-linked-doc 的 ③④（LF 守卫 / 形态门）是**本卡刻意不做的相邻面**（加了会改 `test_g3_3_cas.py` CAS 门的字节面），只登记。
2. **未证明** `/tmp/cls-exam/` 迁移在真实 Claude Code 会话下端到端成立。本卡只证明了 prose 的**顺序**（`mkdir -p` 写在 `Write` 之前）与 python 块本身；`Write` 是**宿主动作**，测试跑不到它，`node` 参数路径上目录是否真的被建出来未实跑。
3. **未证明** `quiz-answer/SKILL.md:3087` 的有损解码在真实输入下丢过事件 —— 只做了静态普查登记（它已有等值查重，缺陷面只剩解码半个），归 P6-B / 另立卡。
4. **未证明** 普查脚本的关键词集合完备。它只认 `python3 ` / `PYEOF` / `` `Bash` `` / `Bash:` / `mkdir -p` / `os.write` / `` `Write` `` **七个词**，此外的执行动作形态看不见 —— 这是普查的**已知假阴面**。
5. **未证明** `test_g3_3_cas.py` 目录级以外的 CAS 并发面在 bytes 读回改法下无回归。只跑了其显式文件与 `tests/regression` 目录级，**未做** T7-B 式「两进程同屏障 busy-spin」并发复现。（改法保持在**同一个 fd** 上 `os.lseek` + `os.read`，未新开 `open()`，故 POSIX 记录锁的 fd 生命周期语义未变 —— 但这是**代码阅读**结论，不是并发实测结论。）
6. **未证明** Python 3.11（CI）下 `RecursionError` 路径与本地一致。本机 3.14.4 实测 `json.loads("[" * 100000)` 抛的是 `JSONDecodeError`（ValueError），门⑤ 因此走的是 **ValueError 分支**；`RecursionError` 分支在本卡**没有任何一次实跑覆盖**（T7-B 记 3.9.6 复现 / 3.14.4 不复现）。
7. **未证明** 4 张「行号/指纹」基线表在**别的卡再改 SKILL.md 之后**仍然成立 —— 它们按行号钉，任何后续改动都会再漂一次（P6-B/C/D 同车道串行时尤其要注意）。

### 五 bis · Codex 独立复核补充的「未证明」（r1 提出，本卡接受并登记，**未改代码**）

8. **未证明五条门约束了「字段精确等值」**（r1 **MEDIUM**，本卡确认属实）。对照输入：把 `_rec.get("event_id") == evid` 改成 `evid in _rec.get("event_id", "")`，**五门现有输入的结果全部不变**（门① `evid ∉ "derive:别的"` → 仍写；门③ `evid ∈ evid` → 仍不写），门**全绿**；而该变异在历史 ID 为 `exam:测试节点-检验-另一场` 时会误拦新增的 `exam:测试节点-检验`。
   ⛔ **这是门的缺口，不是当前实现的缺陷** —— Codex 内存核验确认当前代码在该对照输入下 `seen=False`（正确），变异版才是 `True`。本卡按协议「MEDIUM 登记不阻断」处置，**不扩门**（卡文 (g) 明确规定五条门，加第六条属扩范围；且改门 = 再送一轮 + 全套重跑）。建议主 session 排一张补门卡：加一条「历史 event_id 是 evid 的**真前缀扩展**（`evid + 后缀`）时新事件仍须落账」的门。
9. **未证明五条门验证了「历史保留」**（r1 LOW）。门未覆盖的路径：给 `os.open` 加 `O_TRUNC`（清空历史后再写一条目标事件），五门的计数断言**仍可全部满足**。当前 flags 无 `O_TRUNC`，不计为本次实现缺陷。
10. **「捕到异常 = 语法坏行」并不严格成立**（r1 ① 的实测发现，本卡登记）：解释器的**资源限制**也会触发同样的异常 —— Codex 本机实测**一个 5000 位的合法 JSON 整数即触发 `ValueError`**；合法但深嵌套的内容也可能触发 `RecursionError`。这类**本身合法**的历史行会被当成「坏行」跳过（后果方向是「可能重复写」而不是「丢事件」，与本卡要修的方向相反，但如实登记）。`MemoryError` 不被内层捕获，落到既有外层失败处理。
11. **五门未覆盖的其余输入面**（r1 ⑦ 枚举，本卡如实抄录）：多条历史行与不同 JSON 编码形态、参数文件（`P`）损坏 / 缺键 / 类型错误、**固定参数文件路径下的并发覆盖与删除竞争**、锁超时路径、I/O 失败 / 短写 / `os.remove` 清理失败。⚠️ 只能断言「**本卡这五门**未覆盖」，不能断言既有 regression 门也未覆盖。

---

## 六 台账待登记条目（≥4）

1. **修复 sha + 结构成对**：`13ab1b37bd7840a26e568a71a5c77bd3e6d30b13`；`in_ln 1→0` / `replace 1→0` / `eq 0→1` / 裸字面量 `2,2,2→0,0,0` / 命名空间 `0,0,0→2,2,2`；AST 门 `(1,0)→(0,1)`、`BASE` 侧恒 `(1,0)`。新门 5 条 nodeid：`tests/skills/test_seb_writer_exact_match.py::{test_substring_dedup_false_positive_loses_event, test_undecodable_line_is_not_dedup_evidence, test_true_duplicate_is_still_skipped, test_empty_ledger_twice_writes_once_and_removes_input, test_deeply_nested_bad_line_does_not_abort_append}`。负控三段存档全文件名：`negctl-seg1-20260918T171824.txt` / `negctl-seg2-20260918T171856.txt` / `negctl-seg3-20260918T171926.txt`。
2. **T7-C 交接（部分闭合，范围如实）**：`HANDOFF-seb-tmp-decoupling.md` 的 4 处钉点已由本卡同批改齐 —— cas 侧 `:49`（**模块级**列表推导过滤，其后模块级 `assert len(_SEB_BLOCKS) == 1` 在**导入期**炸）与 `:144`（在 `_exam_board_code()` **函数体内**，单独回退不炸 collect，只是替换不到目标）；schema 侧 `:1018/:1022` 两处**都在** `test_real_producer_start_exam_board_writer` 函数体内，运行期断言红。
   ⛔ **破法不同，不能都说成「导入期」**（Codex r1 LOW-3 指出，原表述已改）。T7-C「未证明 #1：未证明 `:430/:435` 真解耦方案正确」由负控段③ **闭合其中「模块级钉点必须同批改」的那一半**；另一半（宿主 `mkdir -p → Write` 端到端）**仍未证明**，见「本卡未证明什么」#2。HANDOFF §四 LOW 那句「这两处都在模块级」的歧义已在 lint 模块 docstring 中更正为「位置不同、破法相同（因为只要模块级那处不中，导入期就炸）」。
3. **lint 模块基线变更（7 项，全部实测）**：`BASELINE["start-exam-board"]` `tmp_all 6→8 / tmp_ns 4→8`；`ESCAPING_TMP_BASELINE["start-exam-board"]` 6 条 → **3 条**（`prose:/tmp` + `prose:Bash: mkdir -p /tmp/cls-exam` ×2）；`MANAGED_FILE_DIGESTS["skills/start-exam-board/SKILL.md"]` `0f2c085a…` → **`c3c0434d385c66f33c097c051d4aac2d05f908a881bc1471785beeaf52493473`**；**⛔ 卡文未点名但同样必改的 4 项**：`TMP_BLOCK_BASELINE`（`B433` 指纹换、`S430` 指纹换、`S577→S603`、新增 `S604`）、`SUSPICIOUS_TMP_LINES_BASELINE` `[577]→[603]`、`OPAQUE_TMP_BASELINE`（`430` 指纹换、`577→603`、新增 `604`）、以及 6 条依赖它们的负控 + `test_negative_control_untouched_copy_is_green`。
4. **quiz-answer 同族登记**：`canvas-vault/.claude/skills/quiz-answer/SKILL.md:3087` `_txt_lock = _raw_lock.decode("utf-8", "replace")` 有损解码 —— 其 `:3091-3095` 逐行 `json.loads` + 跳过 `ValueError`、**`:3096`** 做 `event_id` 等值判断（行号由 Codex r2 独立核对更正，原写 `:3091-3095` 未含等值那一行） ⇒ **无子串面，缺陷面只剩解码半个**。建议 P6-B 顺带或另立卡。
5. **普查结论**：9 份 SKILL.md 中 **T7-B 形态 0 处**；`start-exam-board/SKILL.md:303-308` 无标签 fence 的 `Bash: curl` 是**执行者指令 fence**、非缺陷；tag=`markdown` 的 7 个模板 fence 内执行动作关键词 0 命中。
6. **相邻面登记**：SEB 落账块**缺 LF 守卫**与 **event_id 形态门**（ai-linked-doc 的 ③④ 已有、backend `append_event` 已有）⇒ 四写者在这两条上仍不齐，建议另立卡。
7. **⑦ 负控改靶交接**：`test_skill_portability_lint.py::test_negative_control_equal_count_swap_must_redden` 的靶已从 start-exam-board 改挂 **quiz-answer `:233` `P = "/tmp/quiz-answer-payload.json"`**（`BASELINE["start-exam-board"]` 两端换成 `QUIZ_ANSWER_BASELINE` 两端）。⚠️ **U5-B / P6-B 若把 quiz-answer 的 4 处裸 `/tmp/` 也迁入命名空间，该负控需要再改靶**（否则 `swapped != text` 预置断言先炸）。
8. **卡文两处 file:line 漂移**：`os.remove(P)` 实测 `:493`（卡文 `:494`）；lint 测试 docstring 里 schema 侧钉点实测 `:1018/:1022`（旧文案 `:1013/:1017`，本卡已改成「文件名 + 条目名」形态）。
9. **开工侧目录级取得方式**：`tests/skills` / `tests/regression` 开工侧是在 `git archive 9c4e7e82` 拉出的 scratchpad 净树上补跑的（工作树不还原、禁 stash / checkout-HEAD），净树 sha 自证 `0f2c085a…`；两侧 rootdir 不同，此差异已在 (i) 如实标注。
10. **Codex 各轮**：r1 `codex-review-CARD-SEB-WRITER-SUBSTRING-TMP-r1.md` 绑 `13ab1b37…` **B0/H0/M1/L3**；r2 `codex-review-CARD-SEB-WRITER-SUBSTRING-TMP-r2.md` 绑同一 SHA **B0/H0/M0/L0** 且 ④⑤⑥ 独立重算相符。两份首部三字段齐、非 0 字节、`gpt-5` 计数 0。**末轮 BLOCKER=0 / HIGH=0 且绑最终 HEAD ⇒ 满足 D-15。**
11. **r1 MEDIUM 转补门建议（待主 session 排卡）**：`test_seb_writer_exact_match.py` 五门**未约束「字段精确等值」** —— 变异 `evid in _rec.get("event_id", "")` 可通过全部五门，而它在历史 ID 为 `evid + 后缀`（如 `exam:测试节点-检验-另一场`）时会误拦新增事件。建议补一条门：历史 `event_id` 是 evid 的**真前缀扩展**时新事件仍须落账。当前实现正确，这是**门的缺口不是代码缺陷**。
12. **卡文 (k) 的 trap 写法在「commit 排在判据之后」的卡上是陷阱**（与台账 §三.22 (e) 同族）：`git show HEAD:<path> > <path>` 在修复未提交时会把整个修复一起还原且还原后 sha 自洽 = 静默假绿。本卡改用**变异前字节快照**还原 + 四行 shasum 互证。建议回写协议 §2.2 / 卡文模板。
