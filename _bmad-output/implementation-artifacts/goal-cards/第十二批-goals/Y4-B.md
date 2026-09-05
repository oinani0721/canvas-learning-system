> ⚠️ 本文件是 CARD-TOOL-typecheck-glob 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十二批手册 §三 Y4-B 块。
> 批次标记 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-typecheck-glob]`。车道：`card-z7-tool`（分支 `card/z7-tool`，HEAD `df39bf21` 起，主 session 已预合主干 03ac8bf8，venv symlink 已建 → `card-v5-lance/backend/.venv`，**含 pyright 1.1.411**），**前提 Y4-A 已独立 commit 且工作树干净**。**用户已裁（2026-09-05，D-1 = 丙：python-typecheck glob 收到 `backend/app`，测试面存量债另卡；主干 venv 暂不装 pyright）**——记录：主干 commit 03ac8bf8 body「D-1 pyright 丙」+ 台账 Z7-B 行「D-1 用户裁丙」。勘探 2026-09-05 于主干 03ac8bf8。协议：`.claude/rules/card-batch-protocol.md`（§2.1 存档首部 / §2.2 裁判落盘 / §2.3 环境通告）。

# CARD-TOOL-typecheck-glob — D-1 丙落地：python-typecheck glob 收窄到 `backend/app`（单条 `backend/app/*.py`）+ include 口径实数对齐（不装 pyright、不改 pyrightconfig）

## 〇 事实
| 事实 | 位置 |
|---|---|
| `python-typecheck` 块 :146-172：glob :147 = `{backend,src}/**/*.py`；`run:` :148；解析 pyright 路径 :151-158；SKIP 分支 :159-162（两行 SKIP 提示 + `exit 0`，诚实 SKIP）；真跑分支 :164-172（`"$PYRIGHT_BIN" {staged_files}` :165，`exit $PYRIGHT_EXIT` :172）；HONESTY CONTRACT 注释 :131-145 | `sed -n '131,172p' lefthook.yml` |
| lefthook 2.1.6 glob 引擎实测矩阵（X8 钉死，:40-48 注释）：单 `*` 跨任意层级；`**` 反要求至少跨一级；矩阵里「根文件 skip」是**花括号子目录** `{api,models,schemas,mcp}` 造成的，不是单星本身 ⇒ D-1 丙的正确写法是**单条** `backend/app/*.py`，无花括号故不需 flat+root 拆分。仍须 (a) 探针实测后定稿 | `sed -n '40,48p' lefthook.yml` |
| 实数（主干 `git ls-files`）：backend/app **263** 个 .py（根级 5：`__init__.py` / `config.py` / `dependencies.py` / `main.py` / `security.py`）；src **0**（目录不存在，glob 里的 `src` 是死枝）；tests（仓库根）**41** ⇒ pyrightconfig include 面 = 263+0+41 = **304**。backend 全部 **846** 个 .py，其中 backend/tests **493**。**禁写 258/35**（第十一批手册旧数，已被推翻） | `git ls-files backend/app \| grep -c '\.py$'` 等，见 §二.1 |
| 门可达面 ≠ include 面：:165 把 `{staged_files}` 作为**位置实参**传给 pyright，位置实参**覆盖** pyrightconfig 的 include ⇒ 现行门可达面 = backend 全部 846 个 .py（含 tests 493），这就是台账 Z7-B 行「18/19 = 94% 提交被拦」的机制。收窄到 backend/app 后门面 ⊂ include 面 | `lefthook.yml:165`；台账 §一.b Z7-B 行 |
| 原 glob `{backend,src}/**/*.py` 漏掉 backend 一级 2 文件：`backend/mutmut_config.py`、`backend/start_server.py`——本卡**有意不收** | `git ls-files backend \| grep -E '^backend/[^/]+\.py$'` |
| pyright 所在分两树：**主干** `backend/.venv` → `/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv`，**无 pyright**（`ls backend/.venv/bin/pyright` No such file）⇒ 主干门恒走 :159-162 SKIP，改 glob 后**仍不真跑**；**车道** `card-z7-tool/backend/.venv` → `card-v5-lance/backend/.venv`，**有 pyright 1.1.411** ⇒ 车道门真跑。两句都要写进验收单，不得混为一句 | `ls -ld backend/.venv` 两树 |
| `pyrightconfig.json`：include `["backend/app","src","tests"]`（:2-6），pythonVersion 3.11（Z7-B 改），typeCheckingMode basic——本卡**一字不改**（注释只落 lefthook.yml 与验收单） | `pyrightconfig.json` |
| 执行次序约束 :259-268：无 priority 的命令按命令名字母序；任何 priority 值排最前 ⇒ 禁改命令名、禁加 priority | `sed -n '259,268p' lefthook.yml` |
| lefthook 2.1.6 `run` flag：`--command <name>`（单数、可重复）/ `--force`（无文件变化也跑）/ `--no-auto-install`；本机 git hook 用 `/opt/homebrew/bin/lefthook`；`npx lefthook` = 1.13.6 禁用 | `/opt/homebrew/bin/lefthook run --help` |

## 一 完成条件（AND）
- (a) `lefthook.yml:147` glob 由 `{backend,src}/**/*.py` 改为**单条** `backend/app/*.py`。改前在 **scratch worktree**（`git worktree add --detach <scratchpad>/y4b-probe HEAD`，内建 `backend/.venv` 目录级 symlink → `card-v5-lance/backend/.venv`）先把新 glob 写进 scratch 的 lefthook.yml，用 2.1.6 逐档探针：分别暂存 `backend/app/main.py`（根级）/ `backend/app/mcp/server.py`（1 级）/ `backend/app/api/v1/endpoints/health.py`（3 级）各一次（文件末追加一行 `# probe` 后 `git add`），`/opt/homebrew/bin/lefthook run pre-commit --command python-typecheck --no-auto-install; echo rc=$?` → 三档都必须出现 `[Python] Running pyright type check (backend/.venv/bin/pyright)...`（= 命中；pyright 对存量报错 rc≠0 属预期，如实记 rc）。负控两档：暂存 `backend/mutmut_config.py`、`backend/tests/conftest.py`（各追加 `# probe`）→ 命令因无匹配文件被 lefthook 跳过（抄 lefthook 的原字面输出）。每档跑完 `git reset -q HEAD -- <f> && git checkout HEAD -- <f>` 还原；scratch 最后 `git worktree remove --force`。五份 transcript 落 `_bmad-output/审查/evidence-typecheck-glob/`。
- (b) 若 (a) 根级探针证伪（main.py 不命中），退化为两条零重叠命令（如 `python-typecheck`（`backend/app/*/*.py`）+ `python-typecheck-root`（`backend/app/{__init__.py,config.py,dependencies.py,main.py,security.py}`）），新命令名的**字母序**不得打乱 :259-268 记录的次序（mutant-residue-scan 仍在 python-lint、pyright 门、README 门、两个 spec-sync 之前），并把探针矩阵写进块注释。默认路径是 (a) 单条。
- (c) 注释只落 `lefthook.yml`（HONESTY CONTRACT 块 :131-145 之后追加）与验收单：写清 D-1 丙的口径与实数——backend/app 263 / src 0（死枝）/ tests(仓库根) 41 = include 面 304；位置实参覆盖 include ⇒ 原门可达面 backend 846（含 backend/tests 493）= 94% 被拦机制；收窄后门面 ⊂ include 面。**禁写 258/35**。新增注释行数 **N** 写进验收单并通报 Y4-C / Y4-D（其 :286-340 与 pre-push 行锚整体 +N）。
- (d) 显式登记两条死枝：`src/` 零 tracked；原 glob 漏的 backend 一级 2 文件 `backend/mutmut_config.py` / `backend/start_server.py` 本卡有意不收（写进注释与验收单）。
- (e) 验收单必须并列写两句：「**主干**合入后 `backend/.venv` 无 pyright ⇒ 门仍走 :159-162 honest-SKIP，改 glob 后仍未真跑」「**车道**（symlink card-v5-lance）门真跑，本卡 commit 时 hook 输出见 evidence」。任何「类型已检查 / 类型检查已通过 / 收窄并通过」表述 = 假绿，禁写。
- (f) `pyrightconfig.json` 一字不改：`git diff HEAD~1 HEAD -- pyrightconfig.json` 为空。
- (g) 本卡 commit 只改 `lefthook.yml`（.yml 不在 python-typecheck / python-lint 的 glob 内，那两门本次不触发是**正常**；如实抄 lefthook 摘要每个 command 的 ✔️/skip 与 rc），**不得** `LEFTHOOK_EXCLUDE`。
- (h) Codex 一轮：prompt `codex-prompt-CARD-TOOL-typecheck-glob.md`，读取面 = `git diff HEAD~1 HEAD -- lefthook.yml` + `lefthook.yml:40-48` 矩阵 + 五份探针 transcript；问题按重要性：glob 单星语义是否被探针证实（三档命中 + 两档负控）/ 注释实数是否与 `git ls-files` 一致 / 是否引入任何「已类型检查」假绿措辞 / 命令名集合与次序是否未变。存档首部按协议 §2.1。
- (i) 「本卡未证明什么」必填：未证明 backend/app 263 文件类型正确（存量 592 err 未动）；主干门仍 SKIP；未接 CI；backend/tests 493 文件的类型债**未清**（另卡）；backend 一级 2 文件不在门内；探针只证 glob 命中，不证 pyright 结论。「台账待登记条目」必填：Z7-B 行 D-1 丙「已落地 <sha>」；「258/0/35 → 263/0/41 勘误」；「pyright 装进主干 venv」仍悬（用户裁暂不装）；backend/tests 类型债卡待排；行锚偏移 N。

## 二 裁判命令
（车道树；承重 `2>&1 | tee _bmad-output/审查/evidence-typecheck-glob/<name>-$(date +%Y%m%dT%H%M%S).txt`，末行 rc）
1. 改前实数：`git ls-files backend/app | grep -c '\.py$'`（263）；`git ls-files src | wc -l`（0）；`git ls-files tests | grep -c '\.py$'`（41）；`git ls-files backend | grep -c '\.py$'`（846）；`git ls-files backend/tests | grep -c '\.py$'`（493）；`git ls-files backend | grep -E '^backend/[^/]+\.py$'`（mutmut_config.py / start_server.py）；`git ls-files backend/app | grep -E '^backend/app/[^/]+\.py$'`（5 个根级）。
2. `/opt/homebrew/bin/lefthook version` → 2.1.6；`ls -ld backend/.venv && ls backend/.venv/bin/pyright && backend/.venv/bin/pyright --version` → 车道有 pyright 1.1.411。
3. scratch 探针（(a)）：三档命中 + 两档负控，各一份 transcript；命中判据是块内 `[Python] Running pyright type check` 字面出现，不是 rc。
4. 改后：`grep -n -A2 '^    python-typecheck:' lefthook.yml` → glob 行 = `glob: "backend/app/*.py"`（含新增注释后 :147 会漂 N 行，不按 147 硬读）。
5. 次序不变：`git diff HEAD~1 HEAD -U0 -- lefthook.yml | grep -E '^@@'` → 所有 hunk 落在 python-typecheck 注释块与 glob 行；`diff <(git show HEAD~1:lefthook.yml | grep -E '^    [a-z-]+:$') <(grep -E '^    [a-z-]+:$' lefthook.yml)` → 空（命令名集合与顺序不变）。
6. `git diff HEAD~1 HEAD -- pyrightconfig.json` → 空；`git diff HEAD~1 HEAD --stat -- . ':(exclude)_bmad-output'` → 只有 `lefthook.yml`。
7. 提交时 hook 真跑：commit 输出（lefthook 摘要每个 command ✔️/skip）整段贴验收单 + evidence；`echo rc=$?`。

## 三 禁改与隔离
- 禁改命令名、禁加 `priority:`；禁改 `python-lint`(:117-129) / `spec-sync-flat`(:51) / `spec-sync-root`(:62) / `mutant-residue-scan`(:286-334，Y4-C 面) / pre-push 两命令(:391-435，Y4-D 面) 任一字节。`lefthook.yml` 本批只 Y4 写，Y4 内部 :147（本卡）/ :286-340（Y4-C）/ pre-push（Y4-D）互斥。
- 禁改 `pyrightconfig.json`（include / exclude / pythonVersion / typeCheckingMode）；禁把 pyright 装进任何 venv（含主干 `backend/.venv` 与共享 `card-v5-lance/backend/.venv`——后者已有 1.1.411，也禁升级；动共享环境 = 协议 §2.3 批级事件）。
- 禁在车道树 / 主干树造真实 commit 做探针（一律 scratch worktree）；禁 `npx lefthook`。
- 设计稿 §0 的 D-14 pyright 绕过口径对本车道**不适用**：本卡 commit 不得 `LEFTHOOK_EXCLUDE=python-typecheck`；hook 真跑并贴 rc 与每个 command 的 SKIP/PASS。
- 禁写「类型已检查」类措辞；禁写 258/35。
- live vault 只读；禁连 7691/7687；本卡不跑 pytest；别人的地盘（设计稿 §5）不碰；台账不改；`*.stderr*` 不入库；不 push。

## 四 Codex / 验收单
命令同协议 §2，1 轮（`codex-prompt-CARD-TOOL-typecheck-glob.md` → `codex-review-CARD-TOOL-typecheck-glob.md`，首部按协议 §2.1，绑定 = 本卡 commit sha）。顺序：门定稿 → 全部裁判 → Codex → 之后只改 `_bmad-output`；审后再改 lefthook.yml = 失绑须登记。验收单 `_bmad-output/验收单/UAT-CARD-TOOL-typecheck-glob-<日期>.md`：DoD-3 双段；4-B「无变化（提交代码前的类型检查只看后端应用目录，不再因为测试文件里的旧问题把提交拦下；主仓那台机器上这项检查依旧显示「跳过」，不是「通过」）」零技术词；(e) 两句并列；「本卡未证明什么」「台账待登记条目」按 (i)。commit header ≤100 含 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-typecheck-glob]`，body 行 ≤100（`wc -m`）；不 push；跑完说「复核第十二批 Y4」。**独立 commit 后同车道继续 Y4-C。**
