> 批次: BATCH-2026-09-18-第十五批 · 车道 P6 · 卡 CARD-HARNESS-TREE-PARSE-R2 · **人审替代轮 v2**
> ⚠️ **这不是 Codex 轮次**。Codex 通道 2026-09-19 实测断在**授权层**（400，`gpt-6-astra` 已不在
> 本账户可用模型列表，非配额），见 `codex-channel-diagnosis-20260919T041838.txt`。
> 形态: 主 session 编排的 4 维只读对抗复核 + 每条发现由 2 个独立镜头证伪（falsify / consequence）
> 审查绑定: `31dfd0de`（实测 `git diff --stat 31dfd0de HEAD -- . ':(exclude)_bmad-output'` = 0 行）
> 规模自证（数值来自 workflow 完成通知的 `<usage>` 段，**不在** result JSON 里 —— 首版生成脚本
>   从 JSON 取，取到空值打成了 `—` / `0s`；空字段比不写更糟，它占着位置让存档看起来合规，故改填实测值）:
>   `agent_count=36  agents_done=36  agents_error=0  agents_skipped=0  agents_empty_result=0`
>   `subagent_tokens=4,417,354  tool_uses=805  duration_ms=1,065,334`（≈ 17 分 45 秒）
> 口径: 存活 = **两个镜头都未证伪**；镜头分歧时取更严重的那一档；证伪方被要求「拿不准就判 refuted」

---

# 结果

原始发现 **16** 条 → 全部送证伪（`droppedByCap` = 0）→ 存活 **4** 条

```
BLOCKER 0   HIGH 1   MEDIUM 3   LOW 0
```

⇒ **HIGH = 1，不满足收口条件**（卡文要求绑最终 HEAD 的一轮 BLOCKER/HIGH = 0）。

## 存活

### 1. [MEDIUM] `realpath(..., strict=True)` 在项目自己声明支持的 Python 3.9 上抛未捕获 TypeError——而这条路径正是缺库拒因让用户照抄的那条安装命令通向的环境

- **锚**: `_real = os.path.realpath(_given, strict=True)`
- **场景**: `strict=` 形参是 Python 3.10 才加的，而仓根 `pyproject.toml` 写着 `requires-python = ">=3.9"`，写点又是用环境里的裸 `python3` 跑的。本机 `/usr/bin/python3` = 3.9.6：用户第一次跑 `/quiz-answer` 会先撞上「PyYAML 不可用」拒因，而那条拒因直接教他 `/usr/bin/python3 -m pip install pyyaml`；照做之后就进入「3.9 + 有 PyYAML」——此时只要 config 里**配了** harness_tree（也就是一键部署形态的必经之路），`_harness_tree` 走到 realpath 就抛 `TypeError: realpath() got an unexpected keyword argument 'strict'`，它不是 OSError、下面那个 `except OSError` 接不住，用户拿到的是一段裸 traceback：没有 `[quiz-answer]` 拒因、没有 `_HALFSTATE`（「分数保留、不回滚」）那句话，于是在 Step 4 触发时会以为 Step 3 记的分也丢了。实测：同一份抽出来的 `_harness_tree`，3.14 下正确返回 worktree_A，`/usr/bin/python3`（3.9.6）下抛该 TypeError（/private/tmp/.../scratchpad/clean39/probe_py39.py）。没配 harness_tree 的老布局走不到这一行，所以问题只打在新部署形态上。

<details><summary>镜头 1 判词（前 1200 字）</summary>

Not refuted — reproduced directly. `strict=` is Python 3.10+; on /usr/bin/python3 (3.9.6) `os.path.realpath(_given, strict=True)` (SKILL.md:694) raises `TypeError: realpath() got an unexpected keyword argument 'strict'`, which the following `except OSError` does not catch, so the user gets a bare traceback with no `[quiz-answer]` refusal and no `_HALFSTATE` sentence. Independent repro (AST-extracted `_harness_tree`, same extraction the Step 2.9 preflight uses, scratchpad py39probe/run.py): 3.14.4 returns worktree_A correctly, 3.9.6 raises at `<harness>` line 389. The path is reachable in the shipped deployment form: scripts/install-vault.sh writes `harness_tree: "$HARNESS_TREE"` into every newly installed vault (schema 2.1-vault-harness-2026-09-07); without that key `_tree` is empty and the line is never reached (both configs present in this repo lack it). 3.9 is a declared target (pyproject.toml:6 `requires-python = ">=3.9"`, README "Python 3.9+", ruff.toml:25 notes ruff infers py39 from it), no gate covers version-target portability (skill_portability_lint.py uses codeop = syntax-only under the running 3.14), all three fenced blocks compile clean on 3.9, and this kwarg is the onl

</details>

<details><summary>镜头 2 判词（前 1200 字）</summary>

技术事实全部复核属实，但后果落在本卡口径的 MEDIUM 档，不是 HIGH。

**已独立证实的事实**（只读，未动这棵树）：
1. `/usr/bin/python3 -c "import os;os.path.realpath('/tmp', strict=True)"` → `TypeError: realpath() got an unexpected keyword argument 'strict'`（3.9.6）；同一调用在 `python3`（3.14.4）正常。`strict=` 确为 3.10 新增。
2. 仓根 `pyproject.toml:6` = `requires-python = ">=3.9"`；写点三个块全部是裸 `python3 - <<'PYEOF'` heredoc，无解释器钉定。
3. `SKILL.md:693-696` 的 `try` 只接 `except OSError`，`TypeError` 确实逃逸；`if not _tree: return os.path.dirname(vault_dir)`（:682）在其之前，所以确实只打新部署形态。
4. 新部署形态确实配 `harness_tree`：`scripts/install-vault.sh` 的 `.canvas-config.yaml` 生成器（schema `2.1-vault-harness-2026-09-07`）产出该键，`backend/tests/unit/test_vault_install_manifest.py:2537/2544` 钉住；install-vault.sh 里 `python3`/`pyyaml` 零出现，不钉解释器也不装依赖。
5. 三个 heredoc 块全部能在 3.9 下 `py_compile` 通过，`strict=True` 是 block2 里**唯一**的 3.10+ API —— 即「3.9 只卡在这一行」这一点也成立，不是「3.9 本来就到处炸」。

**为什么是 MEDIUM 而不是 HIGH（按本卡三条口径逐条对）**：
- **不是静默绑错树**：TypeError 直接逃逸到顶层，`_harness_tree` 不返回任何值，没有任何回退分支吃掉它。进程 rc≠0，零写。方向上仍是 fail-closed，只是拒绝的**表皮**从 `[quiz-answer] …` 退化成裸 traceback。
- **不产生半态**：本卡新加的 Step 2.9 预检在 **Step 3 写分之前**跑 `_harness_tree`（预检块 `_NS["_harness_tree"](VAULT)`），所以首跑就停在 Step 2，分根本没写过，`_HALFSTATE` 那句话此时**无话

</details>

### 2. [MEDIUM] 预检对 Step 4 的 vault 侧依赖（.claude/scripts/fsrs_bridge、decay_beta）零覆盖 —— 绿灯放行后仍落半态，decay_beta 那条还是裸 traceback

- **锚**: `契约 ok — 库在、树在、契约对`
- **场景**: Step 4 主块硬依赖三条 import：(1) `REPO = _harness_tree(VAULT)`、(2) `from fsrs_bridge import rating_from_grade, …`（VAULT/.claude/scripts，try 包住 → SystemExit）、(3) `classify_card_state,… = _harness_contract(REPO)`。此外块内 line 1419 还有一条**裸的** `from decay_beta import PRIOR_A, PRIOR_B, from_legacy, mu, update_after_idle`（无 try）。Step 2.9 预检只抽取并执行 `_harness_tree` / `_harness_contract`，(2) 与 decay_beta 那条**一条都不跑**。实测（scratchpad 复现，未动本树）：造一个 vault —— 有 `.claude/skills/quiz-answer/SKILL.md`、有 `节点/概念.md`、`.canvas-config.yaml` 指向一棵 validator 为主干 symlink 的真 harness 树，但**没有 `.claude/scripts/`** ⇒ `env -u PYTHONDONTWRITEBYTECODE QUIZ_ANSWER_NODE='节点/概念.md' python3 <预检块>` 得 `rc=0` 并打印「harness=… 契约 ok — 库在、树在、契约对, **可以进 Step 3 写分**」；同一 vault 同一 cwd 跑 Step 4 的那两条 import 得 `ModuleNotFoundError: No module named 'fsrs_bridge'` / `'decay_beta'`。于是流程是：预检绿 → Step 3 `Edit` 写分 + `status: scored_pending_node_update` → Step 4 先 `os.makedirs(VAULT/.locks)` 建锁文件（落盘不为零）、读节点、然后死在 fsrs_bridge（SystemExit，且该拒因**不带** `_HALFSTATE`）或 decay_beta（**未捕获 ImportError，一段 traceback**）⇒ 「已记分、节点没更新」的半态白板 + 看不懂的报错，逐字就是 Step 2.9 开头声明要消除的那一幕。

<details><summary>镜头 1 判词（前 1200 字）</summary>

NOT refuted — the scenario is real and I reproduced it without touching this tree. Step 2.9 (SKILL.md:204-263) AST-extracts and execs only `_harness_tree` / `_harness_contract` (`_WANT` at :242, `_CUT` prelude gate at :251-256); neither touches `<vault>/.claude/scripts` (`_harness_tree` checks only `isdir(_real/backend/scripts)` at :698; `_harness_contract` imports only `validate_learning_events` from the harness tree at :743). Scratchpad fixture (vault with `.claude/skills/quiz-answer/SKILL.md` + `节点/概念.md`, harness tree via symlinked `backend/scripts`, no `.claude/scripts/`): preflight rc=0, prints "契约 ok — 库在、树在、契约对, 可以进 Step 3 写分". Same cwd, Step 4's deps fail: `from fsrs_bridge import …` (:812, try → SystemExit at :814 whose text carries no `_HALFSTATE`) and the bare `from decay_beta import … update_after_idle` (:1724, no try → uncaught ImportError traceback) both give ModuleNotFoundError. Writes do precede the failure: `os.makedirs(<vault>/.locks)` + `os.open(O_CREAT)` at :357-361 run well before both imports. No earlier judge intervenes (Step 0's fsrs_bridge import at :116 is in the A3 block, which only runs on the `done`+new-annotation branch), and this is not in the listed

</details>

<details><summary>镜头 2 判词（前 1200 字）</summary>

场景成立，我已独立复现（scratchpad 造 vault，本树零写入零 git 操作）：无 `.claude/scripts/` 的 vault 上预检 rc=0 并打印「契约 ok — 库在、树在、契约对, 可以进 Step 3 写分」，同一 vault 跑 Step 4 的两条 import 分别得 `No module named 'fsrs_bridge'`（SystemExit，line 814 的拒因确实**不带** `_HALFSTATE`）与 `No module named 'decay_beta'`（line 1724 裸 import，一段 traceback）。根因确认：`_harness_contract` 只从 REPO/backend/scripts 导 `validate_learning_events`，而该 validator 只依赖 stdlib，不传递触及 vault 侧的 fsrs_bridge/decay_beta；卡自己的 fixture `_preflight_vault`（test_harness_tree_parse_r2.py:779-787）也不建 `.claude/scripts/`，所以控制组 `..._passes_on_a_good_vault` 是在一个 Step 4 必死的 vault 上判绿 —— 这个洞真实且未被门识别，值得登记并补（两条都是 import-time 静态依赖，零 IO 可检，且正是 `daily-review-wrapper.sh` 逐字节 cmp 盯着的最易漂移的两份文件）。

但后果够不上 HIGH，按本卡口径落 MEDIUM：

1. **不是静默绑错树**——两条都是响亮失败（SystemExit / traceback），账本没被写、没绑错树。
2. **落盘不是有害半态**——锁获取（line 359-364）到 line 1724 之间唯一的写是 `.locks/` 目录 + 一个空锁文件，而那是**每次运行（含成功运行）都会建**的锁构件，不是用户数据；节点写与账本追加都在后面，一个字节都没发生。真正的「已记分」来自 Step 3，而那是**设计内、有文档、可续跑**的状态：Step 4d（line 3486）把任意 `exit≠0` 收成「分数已保存,节点更新失败,重跑 /quiz-answer 会自动续跑」，Step 0（line 166）按 `scored_pending_node_update` 续跑且 event_id 幂等。无分数丢失、无账本污染、无不可恢复态。
3. **不是本卡引入**——两条 import 在基线 `a05732c9` 就是这个形态（基线 line 510 / 1418），本卡一字未动；本卡只是**缩小**了半态面，

</details>

### 3. [HIGH] 词法否决的匹配规则整条没有门：正则里的 `[ \t]*` 和末尾的 `:` 都能改掉而全部格子仍绿

- **锚**: `_CFG_FORMS / _VALUE_NEST_FORMS（两张表里 `harness_tree` 后面都紧跟冒号，没有任何一格带空白）`
- **场景**: config 写 `vault_id: "v"\nharness_tree : /tmp/target-tree\n`（冒号前一个空格）。实测真 PyYAML 6.0.3 对它给出 `{'vault_id':'v','harness_tree':'/tmp/target-tree'}`，`_HEADED_LINES` 也把 `harness_tree : /a/b` 列为受支持写法。配上一个对两道探针都诚实、只对用户这份文件谎报无键的 yaml 模块（= `honest_probes_*` 那一类，也是词法否决唯一的用武之地）：当前代码正确拒写（scratchpad 实跑，返回 `exit`「.canvas-config.yaml 解析结果与文件内容不符 (文件第 2 行…)」）；把生产正则由 `^harness_tree[ \t]*:` 缩成 `^harness_tree:` 之后，**同一输入变成 `ok` 并返回父目录** —— 正是 r10 H1 那条静默绑错树。而这一改动在本文件 42 格上实测 42 passed，ledger 的 g33r2 183 格也看不见（那边 6 种 `_block_yaml` 模式没有一种是「探针诚实、文件说谎」，其余格子都用真 PyYAML、键确实在，`_lex` 与 `_doc` 永远一致）。反方向同理：把正则末尾的 `:` 去掉（让否决变宽，`harness_tree_backup: /x` 这类合法顶层键被误拒）也是 42 格全绿。

<details><summary>镜头 1 判词（前 1200 字）</summary>

不能证伪 —— 事实全部实测复现，但 HIGH 的分级不成立，应降 MEDIUM。

【实测（只读主干树；全部实验在 scratchpad 的副本上做，worktree 未被修改，git status 仍只有那一份未跟踪存档）】
1. 基线保真：把 SKILL.md + test_harness_tree_parse_r2.py + validate_learning_events.py 原样复制成独立树跑 → 42 passed（副本夹具有效）。
2. 收窄变异 `_lex = re.search(r"^harness_tree[ \t]*:", _raw, re.M)` → `r"^harness_tree:"`：**42 passed**。
3. 放宽变异 → `r"^harness_tree"`（去掉末尾冒号）：**42 passed**。
4. 差分复现（config = `vault_id: "v"\nharness_tree : <target>`，一个空格在冒号前；yaml 模块对 `"a: 1"` 与 `_KPROBE_DOC` 两道探针都老实、只对这份 config 返 `{}`）：
   · 生产原样 → `exit`：「.canvas-config.yaml 解析结果与文件内容不符 (文件第 2 行明文写着 harness_tree 键…)」
   · 收窄后 → `ok`，返回**父目录**，而 config 指着 target-tree = r10 H1 那条静默绑错树。

【逐条排除常见证伪原因】
· 更早的判据拦下？没有 —— 该假模块按构造过两道探针，生产拒因确实落在词法层，变异后径直穿过。
· 路径到不了？到得了 —— `harness_tree : v` 是官方支持写法，由 test_g3_2_review_ledger.py:7250（"键与冒号之间有空格"）钉住，真 PyYAML 6.0.3 给出该键（我的复现里前提断言通过）。
· ledger 183 格看得见？看不见 —— :7250 那格走真 PyYAML 的真写点子进程，`"harness_tree" in _doc` 为真 ⇒ 否决谓词在两个变体下都是 False；另一处空格写法 `_HEADED_LINES`:7613 在 no-PyYAML 语料门里，执行在 import 层就退出，`_lex` 根本不求值。
· 源码级门？没有 —— 该正则在测试里只出现在 test_harness_tree_parse_r2.py:362 / :633，是测试**自己那一份**用于前提自证，从未对 CODE 断言；skill_portability_lint.py 只在注释里提到词法否决。

【为什么降 MEDIUM】按本轮给定的 HIGH 门槛「在该场景下**这份

</details>

<details><summary>镜头 2 判词（前 1200 字）</summary>

发现成立，且我在 /tmp 镜像上逐条实测复现（本树只读，HEAD 仍 31dfd0de，代码面 diff 为空，git status 与开工时同一条未跟踪文件）。

【实测事实】
1. 真 PyYAML 6.0.3：`safe_load("harness_tree : /a/b")` → `{'harness_tree': '/a/b'}`。该写法是本项目**明确支持**的形态，ledger 侧还有专门的门 `test_g33r2_harness_tree_noncanonical_key_form_is_honored[键与冒号之间有空格]` 钉住「必须认」。
2. 当前生产代码 + config `vault_id: "v"\nharness_tree : <target>` + 对两道探针诚实、只对该文件谎报无键的 yaml 模块 ⇒ `exit`「.canvas-config.yaml 解析结果与文件内容不符 (文件第 2 行…)」。**当前代码是对的**。
3. 变异 A：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/quiz-answer/SKILL.md:650` 的 `_lex = re.search(r"^harness_tree[ \t]*:", _raw, re.M)` 缩成 `r"^harness_tree:"` ⇒ **同一输入变成 `ok` 并返回父目录** = r10 H1 那条静默绑错树，原样复活。
4. 变异 A 全绿：`backend/tests/skills/test_harness_tree_parse_r2.py` **42 passed**（同镜像基线 42 passed）；`backend/tests/regression/test_g3_2_review_ledger.py -k harness_tree` **165 passed**（基线亦 165 passed）。两处承重面共 207 格，一格不红。
5. 反方向变异 B（去掉末尾 `:`）：真 PyYAML 下 `vault_id: "v"\nharness_tree_backup: /x\n` 被误拒（生产正确返回 `ok`）；变异 B 同样 42 passed。
6. 测试里那两处正则字面量（`test_harness_tree_parse_r2.py:362`、`:633`，以及 ledger `:8011`）是**测试自带的副本**，只对测试自己的 `_raw` 做前提自证，从不读生产的那个字面量 ⇒ 生产正则改了它们照样绿。这正是本卡在 `_KPROBE_

</details>

### 4. [MEDIUM] 预检「纯读零写」在**通过**那条路上只查了 `__pycache__`，别的落盘一律看不见

- **锚**: `test_g33r2_preflight_passes_on_a_good_vault（整格没有 `_write_face` 对照）`
- **场景**: 在预检块 `_NS["_harness_contract"](_REPO)` **成功之后**加一行 `open(os.path.join(VAULT, ".preflight-cache"), "w").write(_REPO)` —— 实测 42 格全绿。三格拒绝路有 `_write_face(_vd) == _face0` + `.locks` 双重对照（把同样的写放在 `_harness_contract` 之前，`contract_broken` 那格会红），唯独通过路没有；而通过路恰恰是唯一一条真正走到 `import validate_learning_events`、最容易顺手落盘的路径。SKILL.md 对这个块的声称是「本块**纯读零写**：不建锁、不读 payload、不落任何文件」，这句话在成功路上没有判据兜着。

<details><summary>镜头 1 判词（前 1200 字）</summary>

CONFIRMED, not refuted — reproduced in scratchpad copies (worktree at 31dfd0de untouched). Baseline mirror: 42 passed. Inserting `open(os.path.join(VAULT, ".preflight-cache"), "w").write(_REPO)` right after `_NS["_harness_contract"](_REPO)` in SKILL.md's Step 2.9 block → 42 passed, and a manual run of the mutated block shows the file really lands (vault file set gains `.preflight-cache`, rc=0), so the green is not a never-executed mutation. Sensitivity anchor: the same write placed *before* `_harness_contract` → 1 failed / 41 passed, red exactly at test_harness_tree_parse_r2.py:881 `test_g33r2_preflight_refuses_before_step3[contract_broken]` with `Extra items in the left set: ('.preflight-cache', 134, …)` — so `_write_face` is a live judge that the refusal paths have and the pass path lacks. No refutation route holds: the pass path (test_g33r2_preflight_passes_on_a_good_vault, line 920) is reachable and is the only path that runs to the print; its sole zero-write judge is `_pycache_dirs(tmp_path) == []`, which sees only `__pycache__`; the three refusal格 never reach past the refusal so their `_write_face`/`.locks` checks cannot cover it; the block-content gate (line 998) only bans `

</details>

<details><summary>镜头 2 判词（前 1200 字）</summary>

不 refuted，但只到 MEDIUM：覆盖面缺口属实且可复现，后果不是「做错事」。

【事实复核（只读；本树零写，三份对照在 scratchpad 独立副本上跑）】
- 读 backend/tests/skills/test_harness_tree_parse_r2.py:920-957：test_g33r2_preflight_passes_on_a_good_vault 的断言集 = rc==0 + "契约 ok" in stdout + realpath(repo) in stdout + _pycache_dirs(tmp_path)==[]。确无 _write_face，**也确无 .locks**（原发现只提了 _write_face，.locks 同缺）。三格拒绝路（:834-888）两者都有。
- 复现①（写在 _NS["_harness_contract"](_REPO) 之后）：42 passed。
- 复现②（同一行写挪到 _harness_contract 之前）：contract_broken 格红在 :881 的 _write_face（Extra items in the left set: ('.preflight-cache', …)）⇒ 1 failed, 41 passed。不对称属实。
- 复现③（把写并进 _harness_contract(_REPO) 同一行、行数零位移，排除「别处按块起始行号钉的 baseline 顺手红」这条侥幸）：仍 42 passed。

【为什么不是 HIGH】按本卡三条口径逐条对：
1. 非「静默绑错树」：该位置在 _REPO = _harness_tree(VAULT) 与契约门之后，树已选定并校验完，此处落盘改不了绑哪棵树。
2. 非「写出半态」：整块仍排在 Step 3 写分之前。那次写若自己失败（EACCES / 只读 vault），异常逃出 ⇒ 预检 rc≠0 ⇒ 停在 Step 2、不写分 —— 正是本卡要的 fail-closed 方向，是可见的拒绝。残余危害只是「vault 里多一个文档说不会有的文件」或「预检抢建本属 Step 4 的锁」，后者也只会在 Step 4 表现为可见拒绝，不是静默坏数据。
3. 非「门恒绿」：该格现有的 _pycache_dirs 判据是敏感的（本卡自己的 A/B：不设 PYTHONDONTWRITEBYTECODE ⇒ 落 1 个），而 import 字节码恰是这条路径上唯一真实存在的落盘机制。缺的是「一般落盘」这一类断言，属判据缺席，不是判据恒真。
4. 今天生产代码在这条路上确实零写：逐行读 SKILL.md:204-265（读自身 SKILL.md、ast.parse、exec 两个函数、_harness_tree 读 con

</details>

## 被证伪（12 条，登记不阻断）

- **[HIGH]** config **存在但打不开**（EACCES / EIO / ELOOP）被当成「压根没写这个键」⇒ 静默回退父树（真 PyYAML，无需任何坏解析器）
  - 证伪要点: 核心事实成立但后果链被更下游的一道无条件判据掐断，所以这条 HIGH 不成立。

真的部分：SKILL.md:623-625 的 `except OSError: _cf = None` 确实同时接住 ENOENT 与 EACCES/ELOOP/EIO，注释却写「压根没有 .canvas-config.yaml」，于是 config 不可读时 `_tree=""`、`return os.path.dirname(vault_dir)`，Step 2.9 预检也会打印 `harness=<父树> 契约 ok`。复核方的沙箱观测在 `_harness_tree` 这一个函数的范围内是对的。

证伪的部分：声称的危害（静默绑错树 ⇒ 按错的 harness 语义写账本 ⇒ 全程零提示）走不到。同一个脚本里、同一份不可读的文件，被一道更下游的无条件判据再读一次：
- SKILL.md:806 `EV = os.path.join(VAU
- **[MEDIUM]** 词法否决只校验「键在不在」，从不校验值 ⇒ 丢掉**值**（而非丢掉键）的截断解析器，在生产写入的顶格裸键写法下照样静默回退父树
  - 证伪要点: 证伪。实测（scratchpad 内 AST 抽出生产 `_harness_tree`，未改本树、未跑 git 写操作）四条：

① **声称的机制根本走不到那条路径。** r10 H1 已把生产代码改成「先读原文、再解析这份原文」：`_raw = _cf.read()` 后递给 `yaml.safe_load(_raw)` 的是 **str，不是流**。于是发现里点名的「一次 `read(4096)` 就交给真 PyYAML」这种 wrapper 在**第一道探针** `yaml.safe_load("a: 1")` 上就 `AttributeError: 'str' object has no attribute 'read'` ⇒ `ImportError` ⇒ `SystemExit "[quiz-answer] PyYAML 不可用 … fail-closed 拒写"`。实测 `got=exit`、`PARENT-SI
- **[LOW]** 「拒写态零写入」对主写块不成立：`.locks/` 锁文件先于选树创建，且主写块没关字节码 ⇒ 拒绝前已往选中的树落 `__pycache__`
  - 证伪要点: 证伪。(1) 唯一**无限定**的零写承诺属于 Step 2.9 预检块（SKILL.md:196-197「本块纯读零写：不建锁、不读 payload、不落任何文件」），而该块自己 `sys.dont_write_bytecode = True`（L211，r3 已提到所有 import 之前）、不建锁，并由 `backend/tests/skills/test_harness_tree_parse_r2.py:883` 与 `:939` 的 `_pycache_dirs(tmp_path) == []` 在**拒绝路径与通过路径**双向立门，且 `_run_preflight`（:793-806）显式 pop 掉 `PYTHONDONTWRITEBYTECODE` 按真实用户环境跑 —— 正是 r2 复核 MEDIUM 已修项。(2) 发现锚定的那句并非无限定：SKILL.md:548-551 原文是「拒写发生在 Step 4
- **[HIGH]** 契约不探 `_golden_manifest`，一棵代码逐字相同但缺 `backend/tests/regression/fsrs_golden_manifest.json` 的树能全绿通过，随后 FSRS 算法身份真值绑定恒绿且 WARN 被丢弃
  - 证伪要点: REFUTED — the finding describes pre-existing behavior that this card did not touch, plus a designed degradation of the validator, and it is disclosed in-code.

(1) Not this card's code. Card base = a05732c9, HEAD = 31dfd0de. `git --no-pager diff --no-color a05732c9 31dfd0de -- canvas-vault/.claude/skills/quiz-answer/SKILL.md | grep -nE "^[+-].*(_GOLDEN_MF|_golden_manifest\(\))"` returns 0 matches (rc=1). Verifying an
- **[MEDIUM]** `_harness_contract` 与调用点的契约是**按位置**的，而两份名单的顺序无任何门/测试绑定；七个名字里有两个都是 `re.Pattern`，互换后完全静默
  - 证伪要点: REFUTED — experimentally, on three independent counts. Method: read-only. I never edited the tree (HEAD still 31dfd0de, `git diff --stat 31dfd0de HEAD -- . ':(exclude)_bmad-object'`-equivalent code diff empty, `git status` unchanged). The two swaps were applied **in memory only**, by a pytest plugin in the scratchpad (`/private/tmp/claude-501/.../scratchpad/plugindir/swap2.py`) that patches the `CODE` string the test
- **[MEDIUM]** _harness_contract 首条拒因漏 _HALFSTATE、点名一个本路径不碰的模块，且与 Step 4 另一处拒因逐字同文（该分支零门）
  - 证伪要点: 发现的三条事实全部属实（已实证，只读）：SKILL.md:745 的 import 失败拒因确是 `_harness_contract` 里唯一不带 `{_HALFSTATE}` 的一条（`_HALFSTATE` 定义在 :736，影子门 :756 与 `_refuse` :748 都带）；它点名 `fsrs_bridge` 而本函数从不 import 它（`git show 0168760e` 第 270 行新增，逐字抄自主块 :814 的既有串）；门覆盖确为零（13 个 `_CONTRACT_CASES` 全走 `_fake_validator_tree` 造得进的 validator；预检门三格 = no_pyyaml / bad_tree / contract_broken，没有一格删掉 validator 文件）。

但后果达不到 HIGH。该场景产出的是一次**正确、可见、fail-closed 的拒绝**：
1. 
- **[MEDIUM]** 「执行自检清单」没有 Step 2.9 条目 —— 先拒后写只靠叙述顺序，漏跑不会被任何一格 tick 或门抓到
  - 证伪要点: 事实部分属实（清单确实缺 Step 2.9 一格、速查表确实无「预检拒绝」行，Step 2.9 是唯一没有对应 tick 的 `## Step` 标题），但声称的场景与危害不成立，三处硬事实证伪：

（1）**本卡的 fail-closed 逻辑不在 Step 2.9，而在 Step 4 主写点本体**。SKILL.md:805 `REPO = _harness_tree(VAULT)`、:820 `… = _harness_contract(REPO)` 就在主 PYEOF 块里；预检块并不另写一份，而是用 AST 从主块里**逐字抽取同两个函数**（:237 `_ANCHOR`、:242 `_WANT`、:259-260 调用），注释明写「与主写点同一份实现，零第二份」。⇒ 漏跑 Step 2.9 **不会**回到 r10 H1：不会静默绑错树、不会记到别的账本、节点侧不产生半写。主写点自己就拒。

（2）**清单在结构上不
- **[MEDIUM]** `_harness_contract` 的 import 失败分支零门，而它恰好是唯一一条不带半态标记的拒因
  - 证伪要点: 证伪。核心声称「零门 / 换成任意字符串 42 格全绿」只对 test_harness_tree_parse_r2.py 那 42 格成立——门不在那个文件里，在本卡同一改动面的另一个文件里。

1) 门实在：backend/tests/regression/test_g3_2_review_ledger.py:6915，`test_g33r2_harness_tree_explicit_alt_tree_is_actually_used` 的**端点 A**：`_write_cfg(vault)` 写一份**无 harness_tree 键**的 config（⇒ `_harness_tree` 走回退 `dirname(VAULT)`，回退分支不做 isdir 检查），再把 `vault.parent/backend` 改名成 `backend-disabled`，然后 subprocess 真跑写点，断言 `rc != 0
- **[MEDIUM]** 契约形状层「合取只测一半」还剩三处：`_WHOLE_SECOND_RE` 的 re.Pattern、`_golden_manifest` 的 callable、两个纯函数探针的返回形状
  - 证伪要点: 发现的**前提**属实，**后果**不成立（不构成「做错事」）——按本卡口径判 refuted。

【前提确认，两半都实测】
(a) 三条变异确实能活过 42 格。结构性核实（scratchpad 读态，未动这棵树）：
  ① `_VALIDATOR_STUB_WRAPPED_RE` 的收尾锚 `(?:\.\d+)?Z$")` 在底本中恰出现 1 次且属 `_TS_RE`，实测 `"_WHOLE_SECOND_RE = _W(" in W` = False ⇒ 全仓没有任何一格把 `_WHOLE_SECOND_RE` 做成非 Pattern；
  ② 11 格逐格执行后取属性实测：只有 `missing_name` 碰到 `_golden_manifest`，而它是**整段删除** ⇒ 由 `hasattr` 那层接住，不经 `callable` 那层；故 callable 循环只被 `vault_id_of_not_calla
- **[MEDIUM]** 「误拒的拒因必须指明是第几行」这条断言实际没钉住行号，行号恒错或整个消失都全绿
  - 证伪要点: 事实前提成立，但后果够不上 HIGH —— 判 refuted。

**前提核实（只读，未动这棵树）**
- 生产拒因 `canvas-vault/.claude/skills/quiz-answer/SKILL.md:671` 的行号是 f-string 插值 `文件第 {_raw[: _lex.start()].count(chr(10)) + 1} 行明文写着`，当前算法正确（存档 `_bmad-output/审查/evidence-harness-tree-r2/verify-codex-r1-20260918T195846.txt:6` 实测「文件第 2 行」，与 `note: "open\nharness_tree: /a/b"` 的真实行号一致）。
- 唯一相关断言在 `backend/tests/skills/test_harness_tree_parse_r2.py:379`：`assert "行明文写着" i
- **[LOW]** `isdir(<tree>/backend/scripts)` 这半条判据两个测试文件都跑不到
  - 证伪要点: 覆盖事实成立，但后果判错——这份代码在该场景下没有做错事，所以按本卡口径不构成 HIGH，登记一条 LOW 即可。

1) 覆盖面的那半句我核实了，属实：新文件里唯一的坏树是 `tmp_path/'this-tree-does-not-exist'`（test_harness_tree_parse_r2.py:860）；ledger 的 `..._broken_is_fail_closed` 四个参数（test_g3_2_review_ledger.py:7063-7066）全是不存在的路径；`_build_alt_harness` / `_usable_tree` 造的树一律带 `backend/scripts`（isdir 恒真）；M-a 那格虽然 `_disable_tree(tree_a)`，但配置路径经 realpath 落到完好的 tree_b，isdir 仍恒真。⇒ 没有任何一格让 `isdir(<tree>/ba
- **[LOW]** 契约门 11 格不钉「拒在哪一层」，与忠实性门不同口径
  - 证伪要点: Refuted: the scenario's premise is factually correct but its consequence is coverage durability, not wrong behavior — the code does nothing wrong today, and the per-case attribution is already load-bearing by construction.

(1) Not 门恒绿 — verified, not assumed. I extracted `_harness_contract` verbatim from SKILL.md via the test file's own `_extract()` and ran the all-correct baseline plus all 11 `_CONTRACT_CASES` with

