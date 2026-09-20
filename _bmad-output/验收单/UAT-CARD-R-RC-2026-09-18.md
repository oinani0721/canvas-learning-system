# UAT · CARD-R-RC — clean RC 冻结脚本 + README 两段

> **批次**：`[BATCH-2026-09-18-第十五批 / CARD-R-RC]` · 车道 `card-p10-docs`（分支 `card/p10-docs`），本车道第 **2/3** 张
> **`<PREV>`**（P10-A CARD-G1-3 末 commit）：`ef8ace4a`（`ef8ace4a73b346790672a61e5308458fbfbcec4f`）
> **最终代码 SHA**：`5abcff162de43153d71c2dde84a0226a040918e2`（commit ①，收工重算）
> **commit 数**：2（① 代码+裁判+README；② 本验收单 + evidence + Codex 存档）
> **裁判条数**：**39 个函数 / 40 nodeid**（`test_missing_lockfile_refused` 参数化 ×2；AST 与 pytest 两口径实测）
> **独立复核轮次**：Codex r1（**不计配额**，绑定 SHA 是我写错的）· Codex r2（1H/7M/5L，已全数处置）· **Codex r3 = 配额耗尽，0 字节 ×2** · 内部 8 维对抗复核 119 agent（37→19 条）
> **⛔ (n) 未达**：没有任何一轮 Codex 绑到最终 HEAD `5abcff16`。详见 §6，交主 session。

---

## 0 一句话

这张卡给发布证据规范补上了**生成端**：一个「工作树不干净就拒绝盖章、而且拒绝时一个字节都不写」的 RC 冻结脚本。
过程中三轮独立复核找出 **1 HIGH + 11 MEDIUM + 6 LOW** 的真缺陷，全部先复现、后修、再用负控证明修到了点子上。

---

## 1 第 0 分钟（完成条件 a）

| 项 | 期望 | 实测 |
|---|---|---|
| `pwd` / 分支 | `…/card-p10-docs` / `card/p10-docs` | ✅ 同 |
| `git rev-parse --short=8 HEAD` | `<PREV>` | `ef8ace4a` |
| `log -1 --format=%s \| grep -c 'CARD-G1-3'` | 1 | `1` |
| `git status --porcelain \| wc -l` | 0 | `0` |
| venv pytest / `.env` / pyright `test -x` | 在场 | ✅ 三者均在（本卡不改 `backend/app`，pyright 仅环境完整性自证） |
| `grep -vc '^#' "$BASE"` | **33** | `33` |
| 手册地盘核 | 命中 P10 行 | 手册 `:38`（P10 车道行，G1-3 → R-RC → R-SLO）与 `:456`（P10-A→B→C 串行）。⛔ 未改手册 |

### §〇 file:line 核对（P10-A 已改 README，行号必漂）

| 卡文 | 实测 | 说明 |
|---|---|---|
| 校验器 `:57/:58/:63/:67/:74`、`:800/:812`；schema `:129/:142/:200/:208` | **未漂** | 逐条 `sed -n` 核过，内容与卡文一致 |
| README `grep -n '^## '` 卡文 9/19/38/81/100/126/154 | **实测 10/20/39/82/101/127/155** | 整体 **+1**（P10-A 在 `:8` 插了台账链接行） |
| README 卡文 `:13`/`:19-36`/`:34`/`:55`/`:79`/`:163`/`:167` | **实测 `:14`/`:20-37`/`:35`/`:56`/`:80`/`:164`/`:168`** | 同上 +1 |
| 卡文 `:7`「168 测试」 | **未漂** | 本卡 (g)③ 实测 `168 passed`；AST 函数口径 147。两个口径都成立，卡文 §〇 的说明正确 |

### ⚠️ 卡文一条事实在当前主干已过期（按实测写，未照抄）

卡文 (e)③ 写「`./data` 子挂载遮蔽 `backend/data`」。**实测 `docker-compose.yml:211-217`**：该行已于
**R11-BATCH2-2026-08-17 移除**，原因正是被父挂载 `./backend:/app` 遮蔽；移除后 `/app/data` 恒等于
`backend/data/`。README 新段按实测写，并显式标注「旧文案已不成立，别照抄」。

### 开工基线

存档 `unit-open-20260918T192059.txt`，末行 `rc=1`，`36 failed, 5727 passed, 44 skipped, 13 xfailed`。
与 B15 基线差集：`<` 1 条（已知 flaky `test_candidate_service::…_422`），`>` 4 条（`test_deploy_vault_sh` 的 preflight 墙钟用例）。

**归因**（不默认当噪声）：单跑同一文件（`deploy-vault-solo-20260918T194246.txt`）得 `1 failed, 290 passed`。
⚠️ 校正一处早先的表述失实（内部复核抓到）：单跑红的那条 `test_preflight_npm_build_cap_does_not_kill_a_fast_build`
**正是目录级四条之一**，不是「不同的一条」。成立的推论是：同一代码状态下红的**条数与集合随负载变化**（4 → 1 → 0），
这是时间敏感 flaky 的特征。收工跑里这 4 条**全部转绿**，反向印证。本卡对 `deploy_vault.sh` 与该测试文件零写者。

---

## 2 先红（完成条件 b）

| # | 判据 | 期望 | 实测 | 存档 |
|---|---|---|---|---|
| ① | `ls` 两个新文件 | 两行 `No such file` | 两行，`rc=1` | `red-ls-20260918T192110.txt` |
| ② | `git grep -l … -- backend docs scripts .github \| wc -l` | 0 | `0` | `red-grep-20260918T192110.txt` |
| ③ | `grep -c -e '重跑规则' -e '缝合体' README` | 0 | `0` | `red-readme-20260918T192110.txt` |
| ④ | 测试已写、脚本未写时跑一次 | 全红、收集数 ≥13 | **收集 21，19 failed, 2 passed** | `freeze-red-20260918T192434.txt` |

**④ 的 2 条假绿已定位并修掉**（本卡第一个真发现）：`test_validator_missing_exit_2` 与
`test_not_a_git_repo_exit_2` 在脚本不存在时照样绿——`python <缺席脚本>` 本身就退 **2**，而它们只断言
`returncode == 2`（数量判据）。修法：锚在只有本脚本会打的 `⛔ [env]` / `⛔ [reject]` 标记上（身份判据）。

---

## 3 DoD-3 · 4-A（Claude 已代验，逐条贴证据）

> ⛔ 以下承重裁判**全部在最终 HEAD `5abcff16` 上跑过**。

### (g)①② 两种跑法同 N passed

| 跑法 | 实测 | 末行 |
|---|---|---|
| `--noconftest --override-ini addopts=` | **40 passed** | `rc=0` |
| 不带 `--noconftest`（走 `tests/unit/conftest.py`） | **40 passed** | `rc=0` |

两者 N 相同 ⇒ 不是靠隔离才绿。（`920ae5b7` 中间态的独立存档为
`freeze-green-noconftest-920ae5b7-20260919T002953.txt` / `freeze-green-conftest-920ae5b7-20260919T002953.txt`，均 32 passed。）

### (g)③ / (i) 既有套件不回退

| 套件 | 开工 | 收工 | 存档 |
|---|---|---|---|
| `test_validate_release_manifest.py` | 168 passed | **168 passed, 0 failed** | `vrm-920ae5b7-20260919T002953.txt`（`rc=0`） |
| `test_check_readme_claims.py` | 120 passed | **120 passed, 0 failed** | `readme-claims-920ae5b7-20260919T002953.txt`（`rc=0`） |

### (g)⑤ 树内真跑 · 脏态拒绝

存档 `freeze-dirty-real-5abcff16-20260919T005336.txt`，末行 `rc=1`：

```
⛔ [reject] dirty tree (65 条未提交条目), 拒绝冻结。 脏树上跑出来的证据不成立(README/S17), 本脚本没有跳过开关: 先提交或清理, 再冻结。
rc=1
```

### (g)④ 树内真跑 · 干净态冻结

先证树干净（未跟踪件按 `-z` 逐个挪至 `$TMPDIR`）：`git status --porcelain --untracked-files=all | wc -l` → `0`。
存档 `freeze-real-5abcff16-20260919T005336.txt`（`rc=0`）/ `check-real-5abcff16-20260919T005336.txt`（`rc=0`）/
`rc-manifest-5abcff16-rc-20260919-5abcff16.json`：

| 字段 | 值 | 对照 |
|---|---|---|
| `candidate.sha` | `5abcff162de43153d71c2dde84a0226a040918e2` | 与 `git rev-parse HEAD` **逐字同** |
| `candidate.dirty` | `false` | 硬门产出 |
| `candidate.rechecked_before_write` | `true` | 校验器之后、首次 mkdir 之前复核过 HEAD 与 porcelain |
| `candidate.is_linked_worktree` / `worktree_rel_to_main` | `true` / `.claude/worktrees/card-p10-docs` | 双树消歧 |
| `candidate.main_root_source` | `worktree-list` | 来源如实记录（见 §5.3） |
| `candidate.dirty_scope_caveats` | **7 条** | 覆盖面如实声明，随产物走 |
| `validator.all_exit_code` | `0` | 校验器 subprocess 真调 |

**新门实跑**：同 SHA 换名再冻 → `freeze-dup-refused-5abcff16.txt`，`rc=1`，信息指出是哪个 rc 占了这个 SHA。

⛔ 本卡在 `docs/release-evidence/` 下**零 `<rc>/` 入库**（地盘门实测 `/journeys/` 与 `rc-manifest.json` 命中 **0**）。

### (k) 负控战役（19 段，全部带「工作树 == HEAD」前置守卫）

主存档 `negctl-battery-c6d5e3a5-20260919T004740.txt`（16 段）+ `negctl-supplement-5abcff16-20260919T005209.txt`（3 段）
+ `negctl-N13-rewrite-5abcff16-20260919T005303.txt`。**16/19 精确命中各自目标测试**，3 段 SURVIVED 已逐条验伪：

| 段 | 变异 | 结果 |
|---|---|---|
| N1 空串门 / N3 同 SHA / N4 TOCTOU / N6 cwd 遮蔽 / N7 非 dict(journey) / N8 自陈 / N9 校验器非 0 / N11 journey sha / N12 锁 sha / N14 前导点 / N15 非 dict(rc) | 各拆一层 | 各 **1 failed**，恰落在声称的那条 |
| N5 main_root | `if git_dir == git_common_dir:` → `if False:` | **2 failed**：`main_root_comes_from_worktree_list` + `separate_git_dir_topology` |
| N10 dirty 恒干净 | `dirty = bool(...)` → `False` | **2 failed**（加固前只红 1 条，见下） |
| N13c 判重 fail-open | 两处 `raise _Reject` → `continue` | **2 failed**：两条 `duplicate_scan_fails_closed` |
| **N2b SURVIVED（部分）** | 合并后的 rc 名门 → `if False:` | 只红 `rc_name_leading_dot`。**验伪**：`.`/`..` 被下游 `rc_dir.exists()` 与原子 `os.mkdir` 接住 = 纵深防御，不是判据缺口；该门的独占输入正是 `.`-前缀名 |
| **N13b 作废** | 正则命中 2 处 | 我自己的负控写错（`n=2`），已由 N13c 精确锚重写 |
| **N16 SURVIVED** | `os.mkdir(rc_dir)` → `mkdir(parents=True, exist_ok=True)` | **40 passed**。**验伪**：这道门防的是竞态（校验器跑的那几秒里 rc_dir 被做成软链），单测无法确定性复现 ⇒ **无用例覆盖，如实登记**（§9.1），未补假门 |

**shasum 还原**：每段都打了改前/改后/还原后三行，还原值与改前逐字同；前置守卫每段先证「工作树 == HEAD」。
⛔ 还原一律 `git show HEAD:<path> > <path>`，**未用** `stash` / `checkout HEAD --`。

> ⚠️ **一次整批作废的记录（值得后人看）**：第一版负控战役 12 段**全部无效**，还把脚本的 10 处修复从工作树上抹掉了。
> 根因是两个叠加的错误：① `git reset --soft` 之后索引仍是旧树，我没重新 `git add`，于是那次 commit ① 提交的是修复**前**的脚本；
> ② trap `git show HEAD:<f> > <f>` 忠实按 HEAD（旧内容）还原，把工作树里的修复覆盖了。
> 恢复方式：逐字重放全部补丁，重放后 sha256 回到 `6e5e9a16…`，与丢失前**逐字节相同**，可证恢复精确。
> 此后每段负控都带「工作树 == HEAD」前置守卫——这正是记忆条目
> `reference_mutation_control_restore_eats_uncommitted_work` 要求的那道守卫，我当时跳过了。

### (f) 结构判据（成对 + 验伪锚）— `struct-5abcff16-20260919T005351.txt`

| # | 判据 | 改前 | 改后 | 验伪锚 |
|---|---|---|---|---|
| ① | `git grep -l … -- backend docs scripts .github` | **0** | **3** | 去掉 pathspec → **5** |
| ② | AST 字符串常量门 | — | `porcelain 6 · untracked 4 · allow_dirty 0 · ignore_submodules 1 · no_optional_locks 1` | 见「allow-dirty 判据」 |
| ③ | `^from app` / `^import app` | — | 两文件各 **0** | 脚本 `import validate_release_manifest` **0**；裁判 **1** ⇒ 证明 grep 能命中 |
| ④ | `grep -cF '^[A-Za-z0-9._-]{1,64}$'` | — | 脚本 **1** / 校验器 **1** | 由 `test_rc_name_regex_shared_with_validator` 机械绑定 |
| ⑤ | README 关键词 | 0 | **3** | 删改行 `^-[^-]` → **0**；新增行 `^+[^+]` → **74** |
| ⑥ | 校验器 + schema + 其裁判 `diff --stat` | — | **空** | 零改动，未走 (c) 例外 |
| ⑦ | stdlib only（AST 取顶层 import，减 `sys.stdlib_module_names`） | — | **`[]`** | — |

### (l) 地盘恰三文件

```
backend/scripts/freeze_release_candidate.py        （新）
backend/tests/unit/test_freeze_release_candidate.py（新）
docs/release-evidence/README.md                    （只追加）
```

`… -- docs/release-evidence | grep -c -e '/journeys/' -e 'rc-manifest.json'` → **0**。
验伪锚见 §11（⚠️ 必须带 `-c core.quotepath=false`，否则中文路径被引号化，锚恒 0）。

### (m) 现网只读

两个新文件命中 **0**；同 grep 喂 `docker-compose.yml` → **5**（锚成立）。本卡零库面，(g)④ 未传 `--vault-root`。

### ruff — `ruff-5abcff16-20260919T005351.txt`

`files=2` / `All checks passed! rc=0` / `2 files already formatted fmt_rc=0` / F821 探针 `probe_rc=1`（写 `$TMPDIR`，零污染）。
⛔ 全程**无** `LEFTHOOK_EXCLUDE`；每次 commit 的 lefthook `python-lint` 均 `Lint OK / Format OK`。

### (h) pyright / (j) openapi

本卡零 `backend/app` 改动 ⇒ 均不适用。lefthook 每次实测打印
`python-typecheck (skip) no files for inspection`、`spec-sync-flat/root (skip) no matching staged files`，
与 (l) 恰三文件一致 ⇒ commit 未被塞入 `openapi.json`。

### 禁 mock（DD-03）的机械自证

⚠️ 文本 grep 会得 **1** ——命中的是裁判第 15 行那句「全文件 0 处 monkeypatch」的**诚实声明**（本卡第五次同型翻车）。
正确口径是 AST：

```
imports: ['__future__','argparse','freeze_release_candidate','hashlib','json','os','pathlib','pytest','re','shutil','subprocess','sys','validate_release_manifest']
mock 类 import: []        以 monkeypatch 为参数的函数: []        autouse fixture: []
```

---

## 4 DoD-3 · 4-B（零技术词）

以后要给一个版本「盖章」时，只要电脑上还有没保存的改动，盖章工具就会直接拒绝，而且不会偷偷留下半个章；
盖出来的章上写的是当时那个版本的唯一编号，后面谁想拿旧编号冒充新版本都对不上号——我感觉「这个版本到底是哪一版」
这件事终于有人管了。

**felt-sense**：写这张卡的过程里，那道「脏了就不给盖章」的门**反过来拦了我自己五六次**。头两次有点烦；
第三次我愣了一下——它列出来的东西里有四百多个我压根没想动的文件，我这才发现自己手滑把一整个历史目录挪错了地方。
后来还有一次更狠：它拦下来的时候，我才意识到自己前一步提交的根本不是修好的那版代码。
一个本来只是用来「保证证据干净」的规矩，两次替我挡下了真会丢东西的操作。那一刻我对这道门的感觉，
从「又要多一步」变成了「还好它在」。

---

## 5 设计取舍与如实声明

1. **拒绝路径零写入是结构性的**。顺序固定：参数校验 → git 身份 → dirty 门 → 锁在场 → vault → 校验器可用性
   → rc 名（合并门）→ 落点不存在 → 同 SHA 判重 → 校验器 `--all` → **写前复核 HEAD/porcelain** → 算锁摘要
   → `out_root.mkdir` + `os.mkdir(rc_dir)` ← **第一次写入**。任何一档拒绝时 `<out-root>/` 尚未被建出来。
2. **dirty 门的覆盖面随产物走**。`candidate.dirty_scope_caveats` 七条，含独立审查补的三条：
   未 checkout 的 gitlink 路径下的内容（git 既不跟踪也无法枚举，本仓 `_reference/obsidian-sample-plugin` 正是此态）、
   rebase/merge 进行中时的干净树（HEAD 事后可能不可达）、被 config 抑制的元数据变化（如 `core.fileMode=false`）。
3. **`main_root` 不靠路径推算**。实测本机 git 2.50.1 在 `--separate-git-dir` 仓里把**git 目录**报成 worktree 路径，
   于是「worktree-list 首条」与「common-dir 的父目录」两种推算法都错。现改判结构事实
   `--git-dir == --git-common-dir` ⟺ 主工作树；主树直接用 `--show-toplevel`；linked 才问 worktree list
   且校验其答案；都不成立记 `null` + `main_root_source: "unresolved"`。
4. **`--require-complete` 的 null 与「跑了得 exit 1」语义不同**：`--out-root` 在校验器证据根之外时这道门看不见本 rc，
   记 `null` + 说明而不是假象。主 session 在候选树上冻结时 out-root 落在证据根内，这道门会真跑，`missing` 会进回执。
5. **`check` 只证明绑定一致**，通过时会自陈「未验 schema / 未验 symlink 冒充 / 未判 RC 完整性」。
   零 journey 时不说「全部绑同一个 sha」（空集上恒真），改说「本次未比对任何 candidate.sha」。
6. **依赖锁只 hash 文件**：证明「这两份声明文件在冻结当刻长这样」，**不证明** venv 实装版本与之一致。
   摘要已挪到末次复核之后算，与 HEAD/status 同窗。
7. **验证替身的判定**：r2 判 `_write_validator_stub` 属 mock、违反 DD-03，**该判定成立，已接受**。
   现改为**真校验器实现 + 合成证据树**（缺 schema 让它自己退 2；畸形 manifest 让它自己退 1），
   与既有校验器裁判同口径（真实现 + 合成 fixture）。

---

## 6 ⛔ Codex 未绑最终 HEAD（交主 session）

卡文 (n) 要求「多轮直到**绑最终 HEAD** 的一轮 BLOCKER/HIGH = 0」。**本卡未达**：

| 轮 | 绑定 | 结果 | 计配额 |
|---|---|---|---|
| r1 | `ef8ace4a..5cd1cae1` | 0B / 1H / 4M / 1L | **否** —— prompt 是 amend 前写的，绑定 SHA 我没同步更新（Codex 自己指出）。结论已全数处置 |
| r2 | `ef8ace4a..920ae5b7` | 0B / 1H / 7M / 5L | 是，但**其结论促成了进一步整改**，最终 SHA 变为 `5abcff16` |
| r3 | `ef8ace4a..5abcff16` | **0 字节 ×2** | 否 —— `usage limit`，提示 2026-09-23 11:05 恢复 |

r3 两次调用（含协议规定的那次重发）存档均 0 字节，`.stderr` 明确 `You've hit your usage limit`。
会话头自证正常（`OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`），失败纯在配额。
⛔ **两份 0 字节存档未入库**；`*.stderr*` 未入库；r1/r2 存档已按协议 §2.1 补首部（三个必填字段齐全，含会话头自证行号）。

**主 session 需要做的**：配额恢复后按 `_bmad-output/审查/prompts/codex-prompt-CARD-R-RC-r3.md` 原文送一轮，
绑定 `ef8ace4a73b346790672a61e5308458fbfbcec4f..5abcff162de43153d71c2dde84a0226a040918e2`；
或按 §1 合并门自行人审裁定——本卡**阻断级 = 0**（无数据丢失 / 无 live vault 或 7691 写入 / 无安全面 / 无负控假绿）。
⚠️ 记忆里有一条「外部服务的重置时间是一次观测不是不变量」，所以已复测一次（仍受限）；接手时请**再复测一次**，别继承这个日期。

---

## 7 evidence 清单（`_bmad-output/审查/evidence-rrc/`，全文件名，不用 glob）

承重结论一律引带 `5abcff16` 的那一份；`920ae5b7` / `c6d5e3a5` / 更早的同名存档保留供追溯整改过程。

| 文件 | 内容 | 末行 |
|---|---|---|
| `unit-open-20260918T192059.txt` | 开工 tests/unit 目录级 | `rc=1` |
| `deploy-vault-solo-20260918T194246.txt` | deploy_vault 四条新红的归因单跑 | `rc=1` |
| `base.nodeids` / `open.nodeids` / `close.nodeids` | 三方 nodeid 集合 | — |
| `red-ls-…` / `red-grep-…` / `red-readme-…` / `freeze-red-20260918T192434.txt` | 先红四条 | 各带 rc |
| `freeze-real-5abcff16-20260919T005336.txt` | **(g)④ 最终干净态冻结** | `rc=0` |
| `check-real-5abcff16-20260919T005336.txt` | **(g)④ check** | `rc=0` |
| `freeze-dirty-real-5abcff16-20260919T005336.txt` | **(g)⑤ 最终脏态拒绝** | `rc=1` |
| `freeze-dup-refused-5abcff16.txt` | 同 SHA 重冻被拒（新门实跑） | `rc=1` |
| `rc-manifest-5abcff16-rc-20260919-5abcff16.json` | 冻结回执全文（**未**入 `docs/release-evidence/`） | — |
| `negctl-battery-c6d5e3a5-20260919T004740.txt` | 负控 16 段 | — |
| `negctl-supplement-5abcff16-20260919T005209.txt` | 负控补跑 3 段 | — |
| `negctl-N13-rewrite-5abcff16-20260919T005303.txt` | N13 精确锚重写 | 还原 sha256 |
| `negctl-N10-recheck-920ae5b7…-20260919T002859.txt` | N10 加固后复测（两条 dirty 都红） | 还原 sha256 |
| `negctl-battery-8fe7f228-20260919T002007.txt` | 上一轮 12 段负控 | — |
| `struct-5abcff16-20260919T005351.txt` | (f) + (l) + (m) + stdlib + 禁 mock 全套 | — |
| `ruff-5abcff16-20260919T005351.txt` | ruff + F821 锚 | `probe_rc=1` |
| `unit-close-5abcff16-20260919T005327.txt` | **最终收工 tests/unit 目录级** | `rc=1` |
| `vrm-920ae5b7-20260919T002953.txt` / `readme-claims-920ae5b7-20260919T002953.txt` | 点名套件 | 各 `rc=0` |

Codex 存档（`_bmad-output/审查/`）：`codex-review-CARD-R-RC.md`（r1）、`codex-review-CARD-R-RC-r2.md`（r2），
均已补协议 §2.1 首部。prompt：`prompts/codex-prompt-CARD-R-RC.md` / `-r2.md` / `-r3.md`
（禁用措辞自检各 0；绑定 SHA 均经 `git cat-file -t` 证实存在）。

> 失败跑产生的名不副实存档（正文是 dirty 拒绝却叫 `freeze-real`）已移至 `$TMPDIR/rrc-junk/`，**未入库**。

---

## 8 收工目录级 (i)

**最终收工跑（HEAD `5abcff16`）**：`unit-close-5abcff16-20260919T005327.txt`，末行 `rc=1`，
汇总 `32 failed, 5771 passed, 44 skipped, 13 xfailed in 397.14s`。

| 差集 | 结果 | 判定 |
|---|---|---|
| `diff base.nodeids close.nodeids`（协议 (i) 口径） | **只 1 条 `<`**（已知 flaky `test_candidate_service::…_422`），**零 `>`** | ✅ 满足「只允许 `<`」 |

**计数自洽核**：failed `36 → 32`（-4，即那 4 条 `test_deploy_vault_sh` flaky 转绿）；
passed `5727 → 5771`（**+44** = 本卡新增 **40 nodeid** 全绿 + 那 4 条转绿）。两条账对得上，没有被抵消的隐藏新红。

> 中间态对照保留：`920ae5b7` 上 `33 failed / 5762 passed`（base↔close **差集为空**）；
> `c6d5e3a5` 上的一次亦在库。三次的 base↔close 结论一致（零 `>`）。

---

## 9 本卡未证明什么

1. **`os.mkdir` 原子门防的那个竞态未被任何用例覆盖**。负控 N16 实测 SURVIVED——把它换回
   `mkdir(parents=True, exist_ok=True)`，40 条裁判全绿。原因是竞态（校验器跑的几秒里 rc_dir 被做成软链）
   在单测里无法确定性复现。**静态**软链已由 `test_rc_dir_preexisting_symlink_refused` 覆盖；竞态那一半只有代码审读。
2. **判重扫描对并发无排他**。两个进程同时扫同一 out-root、同一 SHA、不同 rc 名，可在任何回执落盘前都通过判重。
   未上文件锁（r2 指出）。README 的「按 SHA 机械判」只对**串行执行 + 可读旧件**成立。
3. **未在主 session 的合并候选树上真冻结过**。本卡树内真跑的 rc 指向车道 commit `5abcff16`，squash 后在主干不存在，
   故本卡不入库任何 `<rc>/`。
4. **未证明 `--vault-root` 对主仓 live `canvas-vault/` 的只读行为**。裁判只用 tmp 下的第二个独立 git 仓；live 面按批级只读原则不跑。
5. **未证明索引 SHA 的任何真实取值**。只提供「显式传值」与「`null` + 理由」两条出路。
6. **未证明 CI 侧 `GITHUB_RUN_ID` 路径**。本地无 CI，只测了环境变量注入与三档优先级。
7. **未证明 README 重跑规则在真实 dogfood 期间可操作**。「一个 SHA 一个 rc」+「文档改动也算新 SHA」意味着
   14 天窗口内代码不能动；代价已写进 README，但没在真实 dogfood 里跑过。
8. **未证明 `dependency_locks` 与 venv 实装版本一致**（只 hash 两份声明文件）。
9. **`check` 不拒 symlink**（那是校验器 `check_rc_completeness` 的职责），所以 `check` 绿不代表 RC 门绿。
10. **`main_root` 的 `unresolved` 分支未被覆盖**；bare 仓与 submodule 内执行两种拓扑也未实测（只测了主仓、
    linked worktree、`--separate-git-dir` 三种）。
11. **校验器路径过浅（`parents` < 3）的环境错分支未被覆盖**：要触发它得把校验器放在 `/` 下，
    而 `is_file()` 检查在它之前，测不到。守卫保留，仅经代码审读。
12. **没有任何一轮 Codex 绑到最终 HEAD**（§6）。最终状态 `5abcff16` 只经作者自查 + 机器判据 + 前两轮的整改闭环。
13. **`-z` 解析对含 NUL / 换行的畸形路径未证**（只在常规与中文路径上实测过）。

---

## 10 台账待登记条目

1. **本卡修复 sha**：commit ① `5abcff162de43153d71c2dde84a0226a040918e2`（脚本 + 39 函数/40 nodeid 裁判 + README 两段）；
   commit ② = 本验收单 + evidence + Codex 存档。**Codex：r1 不计配额（绑定 SHA 作者写错）、r2 已处置、r3 配额耗尽 0 字节 ×2，(n) 未达**。
2. **⛔ 主 session 集成期事项**：在合并候选树的候选 SHA 上跑一次
   `backend/.venv/bin/python backend/scripts/freeze_release_candidate.py freeze --index-sha-null-reason "…"`
   （`--out-root` 默认 = 树内 `docs/release-evidence/`，届时 `--require-complete` 会真跑并把 `missing` 写进回执），
   生成本批真 `<rc>/`；**G6-13 的 J07 落到该 rc**。
3. **⛔ Codex r3 待补**：配额恢复后按 `codex-prompt-CARD-R-RC-r3.md` 送一轮，绑 `ef8ace4a..5abcff16`。
   接手前**先复测配额**，别继承「9/23 恢复」这个观测。
4. **R-J01…R-J10 / G8-6 的 `rc_sha`** 统一改指 `<rc>/rc-manifest.json:candidate.sha`；
   ⚠️ `candidate.worktree` **不要照抄** `worktree_rel_to_main`，要填旅程实际执行的树（README 已写明判断方法）。
5. **索引 SHA 真实取值方式待定义**（LanceDB 表版本 / named volume 内快照），归 P1 storage / R-J01。
6. **README `:7`「168 测试」与 AST 147 函数的口径差**登记给 P10-A ledger / README claims 面，本卡不改该行。
7. **`jsonschema` 仍不在 `backend/requirements.txt`**（README `:168` 交接项）。
8. **卡文 P10-B (e)③ 一条事实已过期**（`./data` 子挂载），建议排批时更正模板，免得下一张卡照抄。
9. **`test_deploy_vault_sh.py` 四条 preflight 墙钟用例是负载敏感 flaky**，建议进 B15 flaky 名单。
10. **RC 判重的并发排他**（§9.2）登记为后续项：要么上文件锁，要么在 README 写明「冻结必须串行」。
11. **未走 (c) 例外**：`manifest.schema.json` / `validate_release_manifest.py` / `test_validate_release_manifest.py`
    三文件零改动（`diff --stat` 空），`SCHEMA_SHA256` 未动，无 CI 影响。

---

## 11 收尾自核

> ⚠️ 本节三条判据**第一次都测错了**，修正后的口径与真值一并留档——判据自身出错的方式，和被判对象出错一样值得记。

| 项 | 判据（修正后口径） | 结果 |
|---|---|---|
| commit header ≤100 | `printf '%s' "$l" \| wc -m`（**字符**） | 见文末实测<br>⚠️ 用 `awk length()` 会得字节数，中文按 3 字节算，会把合规 header 误判成超长 |
| 两个 commit 均含卡号 | `git log --format=%s \| grep -c 'CARD-R-RC'` | 见文末实测 |
| commit 数 | `git rev-list --count <PREV>..HEAD` | 见文末实测 |
| `*.stderr*` 入库 | `git diff --name-only \| grep -c 'stderr'`（**只数文件路径**） | 见文末实测<br>⚠️ 用 `git log --stat \| grep` 会把 commit **正文**里「`*.stderr*` 未入库」这句话数进去 |
| 0 字节 Codex 存档入库 | `find … -size 0` 的两份均未 `git add` | 见文末实测 |
| 地盘验伪锚 | `git -c core.quotepath=false … \| grep -c '^_bmad-output/'` | 见文末实测<br>⚠️ 不带 `core.quotepath=false` 恒得 0——中文路径被 git 引号化，行首多个 `"`，锚失效 |
| 是否 push / 改台账 / 装包 / 连库 / 写 live vault | — | 均 **否** |
| 工作树干净（P10-C 开工前提） | `git status --porcelain --untracked-files=all \| wc -l` | 见文末实测 |

> 文末实测值由 commit ② 后的一次性自核脚本产出，结果见 `_bmad-output/审查/evidence-rrc/final-selfcheck-*.txt`。
