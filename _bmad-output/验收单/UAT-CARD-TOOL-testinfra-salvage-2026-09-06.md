# UAT — CARD-TOOL-testinfra-salvage「fix/test-infra-paralysis 三 commit 定点抽取 + 管道退出码穿透 + tests/unit 基线对账」

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-testinfra-salvage]`
> 车道 `card/z7-tool`（本车道**第 4 卡 / 末卡**；前置 Y4-C / CARD-TOOL-residue-newline 已独立 commit，起点 HEAD `16b9e337`）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y4-D.md`
> 5h；代码面 13 文件 = **9 个测试文件 + 4 个配置/脚本**（`lefthook.yml` 仅 pre-push 的
> `frontend-test` 块 + `.claude/hooks/` 两个脚本 + 新增 `scripts/run_cmd_capture.sh`）
> 外审：Codex round-1（1 轮）—— **1 HIGH + 3 MEDIUM + 4 LOW，HIGH 是真缺陷且我错了**，见 (h)

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：无变化（推送与自动测试环节里几处「测试失败却显示通过」
的漏洞补上；一批早已失效的旧测试被标记为跳过而不是假装还在跑——跳过不等于修好）。**

系统里有好几道「交作业前的自检」：改完代码要跑一遍测试、推送前要再跑一遍、
写完一段话要自动验一遍。这些检查跑完都会给一句结论：通过，还是没通过。

问题出在**怎么把结论传出去**。这些检查原本都是「跑测试，然后只显示最后二十行」。
这是两件事接成的一串，而一串事情做完，报出来的成绩是**最后一环**的成绩——
也就是「显示最后二十行」这个动作的成绩。而「显示」这件事几乎不会失败。

结果就是：测试真的红了，但检查环节报的是「显示成功」，于是一路绿灯放行。
更糟的一处是：代码里明明写了「如果没通过就拦下」，可它拿去判断的是「显示」的成绩，
所以那句拦截**从来没有触发过**。

这次一共补了 6 处这样的口子（推送前 1 处、改完代码自动跑的 4 处、写完话自动跑的 1 处）。
补法是换一个中间人来跑：它把完整输出存到一个文件里，失败时把文件路径和最后几行打出来，
**并且如实报出原本的成绩**。

有一次实测最能说明问题：拿同一个真实的失败（前端测试跑不起来），
**旧写法报"通过"，新写法报"失败"**。这不是推理，是当场跑出来的两个数字。

**得说一件不体面但重要的事**：这处的第一版补丁其实没补干净。外部复核指出——
换了中间人之后，后面还跟着一句"打印：测试完成"，而这句话总是成功的，
于是它的"成功"又一次把前面的"失败"盖住了。也就是说第一版换汤没换药。
第二版才真正补上（失败就直接停，不再往下走到那句话）。
我原先的验证只测了"中间人"这一步，没测这一整段流程跑完是什么结果——
**测错了地方，所以第一版看起来是好的**。

另外一半的工作是清理一批**早就失效的旧测试**。有 43 条测试在测一个五个月前就被删掉的
内部函数，它们每次都报错，噪音盖住了真正该看的失败。这次把它们标成"跳过"，
并在每一条上写清楚"新的等价测试在哪个文件"。

**必须说清楚的一点：跳过不是修好。** 这 43 条对应的功能有没有被测到，取决于新文件里那
5 条测试够不够——本卡没有证明它够。账要这么记：**看起来少了 45 条红，其中只有 2 条是真
的修好了**（一个哈希长度的判断标准写错了，实际是 32 位却写着 16 位），
另外 43 条只是被藏起来了。

还有一件本卡自己发现、卡文没预料到的事：那 6 个文件里被"跳过"的其实是 47 条，
不是 43 条。多出来的 4 条**本来是绿的、正常在跑的测试**，因为跳过是按"整个文件"或
"整个分组"打的标记，把旁边好的也一起关掉了。这 4 条的覆盖是净损失，已登记。

---

## 4-A 技术验收

### 〇 证据索引（协议 §2.2：本单每个数字都指向下面某个存档，不自述）

全部在 `_bmad-output/审查/evidence-testinfra/`：

| 文件 | 内容 | 关键结论 |
|---|---|---|
| `unit-pre-20260906T132440.txt` | 开工基线（pick 前，HEAD=`16b9e337`） | 247 nodeid，与红基线 diff 空 |
| `unit-post-20260906T133608.txt` | 收工基线（三 pick 后 / 修复前，HEAD=`abc6fb78`） | 204，新增红 2 |
| `unit-post2-20260906T134314.txt` | 收工基线（Codex 整改前，HEAD=`aae845f8`） | 202 |
| `skip-detail-20260906T133844.txt` | 6 个 skip 文件的 SKIPPED 逐条 + 新增文件 | 47 SKIPPED |
| `judge-c-*.txt` / `judge-c4f-*.txt` | (c)(f) 静态判据 | 管道零命中 |
| `judge-78-*.txt` / `judge-7c-rewrite-*.txt` | 裁判 7/8 + 7c 判据重写 | 13 文件、禁改地盘 0 字节 |
| `canary-d-20260906T133716.txt` | (d) 四条金丝雀 | rc = 7 / 1 / 0 / 64 |
| `canary-d-extra-*.txt` / `canary-d-extra2-*.txt` | 卡文外的 5 条边界探测 | 3 条 wrapper 瑕疵 |
| `control-group-pipe-*.txt` | **修前 vs 修后同输入对照** | **rc 0 vs 127** |
| `frontend-wrapper-probe-*.txt` | frontend-test 命令体真实 cwd 传播 | rc=127 |
| `pipe-semantics-demo-*.txt` | `管道 + [ $? -ne 0 ]` 恒放行演示 | 修前放行 / 修后拦下 |
| `exclude-66d6a835-*.txt` | 排除第 4 个 commit 的实测证据 | 缺 5 个 hook 块 |
| `reconcile-e-*.txt` / `reconcile-e-fixed-*.txt` / `reconcile-final-*.txt` | (e) 三列对账 + 拆分修正 + PASS 直证 + 终版 | 43 / 2 / 0 |
| `skip-collateral-*.txt` | 47 SKIPPED vs 43 红基线的差额身份 | 4 条原本绿 |
| `syntax-check-*.txt` | 被改 hook 脚本的 `bash -n` / `node --check` + 权限位 | 全 rc=0，权限未变 |
| `high1-repro-*.txt` | **Codex HIGH-1 复现**：完整 run 块 vs 单行 | 单行 127 / 整块 **0** |
| `high1-fixed-*.txt` / `high1-three-way-*.txt` | HIGH-1 修后三场景 + 三端对照 | 终态 **127** |
| `medium3-recheck-*.txt` | dead-letter record 真实键（我的声明错在哪） | 正文仍在 |
| `codex-fix-verify-*.txt` | 整改后 5 条复验 + 两条承重变异 | 变异皆红 |
| `judge-after-codex-*.txt` | 整改后 lefthook 判据全量复跑 | 全部仍成立 |
| `unit-post3-*.txt` | **收工基线终版**（HEAD=`556ecc3d`，绑定最终代码） | **202**，与 post2 逐 nodeid 同 |

红基线对照文件（另一棵树，只读）：
`…/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b12/unit-red-baseline-03ac8bf8.txt`

四个 commit：

| # | sha | 内容 | 文件数 |
|---|---|---|---|
| 1 | `33fd106d` | 抽取 `f19dcff6`（含 lefthook 冲突手解 + ruff format） | 13 |
| 2 | `e6ad26e1` | 抽取 `7f495eda` | 1 |
| 3 | `abc6fb78` | 抽取 `0fd6d398` | 1 |
| 4 | `aae845f8` | 修 `f19dcff6` 带入的 2 条新增红（本卡新增，非 pick） | 1 |
| 5 | `556ecc3d` | **Codex round-1 整改 3 项**（HIGH-1 退出码仍被 echo 吞 + MEDIUM-3 口径 + MEDIUM-6 环境隔离） | 2 |

---

### (a) 定点抽取 + 显式排除 66d6a835

**开工前提钉死**（`judge` 开头输出与 `exclude-66d6a835-*.txt`）：

| 事实 | 实测 |
|---|---|
| `git merge-base fix/test-infra-paralysis 03ac8bf8` | `bc8d19c1f8048fd02e01598ab4f3258ef5d41437` |
| `--is-ancestor bc8d19c1 03ac8bf8` | 成立（`ANCESTOR`） |
| `git log --oneline 03ac8bf8..fix/test-infra-paralysis` | 4 行 |
| 三个 pick 均为 `cherry-pick --no-commit`，各成一 commit | ✓（上表 #1-#3） |

**排除 `66d6a835` 的理由（逐条实测，比卡文列的更具体）**：

1. **规模**：`57 files changed, 7830 insertions(+), 114 deletions(-)` —— 它是一次
   merge origin/main，不是一个修复。
2. **它的 `lefthook.yml` 是 185 行的旧版**（本车道 HEAD 是 513 行）。
3. **它缺 5 个 hook 块，逐个溯源到已合入的卡**：

   | 缺失的块 | 由哪个 commit 引入 |
   |---|---|
   | `spec-sync-flat` / `spec-sync-root` | `7ba8fc07` — 第十批 CARD-DEBT-openapi-sync-R1 |
   | `mutant-residue-scan` | `1ffd6d36` — 第十一批 |
   | `readme-claims-lint` | `81364293` — 第四批 CARD-G1-5 |
   | `cypher-vault-filter-lint` | `79da7460` — wave-5 stage-c |

   反向它多出 3 个块：`backup-push` / `origin-push` / `spec-sync`（后者即卡文所指的已死块）。
4. **它的 `python-typecheck` 块根本不阻断**：`pyright {staged_files}` 后
   `PYRIGHT_EXIT=$?`，随后只 `echo` 提示，**没有 `exit $PYRIGHT_EXIT`**。
   即使 pyright 未安装（rc=127）也只是打印一行。这是纯 advisory 形态。

⇒ 以任何形式引入它（`merge` / `cherry-pick`）都会把上述四张卡的 hook 改动回滚。
**本卡未执行 `git merge fix/test-infra-paralysis`**，三次都是 `cherry-pick --no-commit`。

---

### (b) lefthook.yml 冲突手解 —— 逐命令判定表

`f19dcff6` 对 `lefthook.yml` 只有**一个 hunk**（`@@ -134,26 +134,34 @@`），
覆盖 pre-push 的两个命令。解法：`git show HEAD:lefthook.yml > lefthook.yml` 复位到
车道版为底（复位后 `git hash-object` = `58e67f5f…` = `HEAD:lefthook.yml`，逐字节相同），
再只落「管道 → wrapper」这一个变换。

| 命令 | f19dcff6 的字面 | 主干现状 | 判定 | 理由 |
|---|---|---|---|---|
| `frontend-test` · **变换** | `… \| tail -20` → `run_cmd_capture.sh` | :466 有管道 | **取** | 管道吞退出码是本卡要修的缺陷本体 |
| `frontend-test` · **字面** | glob `frontend/src/**`；runner `npx vitest`；`--cwd frontend` | glob 已是 `frontend/obsidian-plugin/{src,tests}/**`（ChatGPT-Review P0-1 修过）；runner 已是 `npm test`（对应 `package.json:8` 的 esbuild + `node --test`） | **弃** | 落字面 = 退回一个**不存在**的 glob（门会因无文件匹配而静默跳过）+ 一个项目未使用的 runner |
| `backend-smoke` · **变换** | `cd backend; python -m pytest tests/unit/ … \| tail -5` → wrapper | :497-513 **已无管道**，用 `TEST_EXIT=$?` + `exit $TEST_EXIT` 显式捕获 | **弃** | 缺陷已不存在；改 wrapper 是零收益的重写，且卡文要求二者不并存 |
| `backend-smoke` · **字面** | `tests/unit/` 全目录；`command -v python` | 已收窄为 A11 两文件；已用 `.venv/bin/python` | **弃** | 落字面 = 把窄门换成 247 条红的全目录 + 退回系统 python（该门历史上就是因为系统 python 缺 pytest 而静默通过数周） |

**落地结果**（`git diff 16b9e337 HEAD -U0 -- lefthook.yml`）：仅 2 个 hunk（行号为
Codex 整改 `556ecc3d` 之后的终态；`aae845f8` 时的中间态是 `+461,8` / `+474`）

- 注释 hunk — 说明变换来源、「为何弃字面」、以及 Codex round-1 HIGH-1 的成因
- 命令体单行替换：
  `npm --prefix frontend/obsidian-plugin test 2>&1 | tail -20`
  → `./scripts/run_cmd_capture.sh --cwd frontend/obsidian-plugin --tail 120 -- npm test || exit $?`

> ⚠️ **`|| exit $?` 是 Codex round-1 补上的，不在初版里** —— 没有它，wrapper 传出的码会被
> 下一行 `echo` 的 0 盖掉，整个修复等于没做。见 (h) HIGH-1。

**隔离证明**（`judge-7c-rewrite-*.txt`）：

- hunk 覆盖的新文件行号集 = `{461…468, 474}`，全部 > `pre-push:` 起始行 453；
- 11 个 hook 块（`python-typecheck` :205 / `mutant-residue-scan` :345 / `python-lint` :117 /
  `spec-sync-flat` :51 / `spec-sync-root` :62 / `cypher-vault-filter-lint` :246 /
  `readme-claims-lint` :290 / `ghost-files` :75 / `commitlint` :411 / `spec-reference` :415 /
  `backend-smoke` :497）**逐个查表，全部未被 hunk 覆盖**；
- **`backend-smoke` 段与 `16b9e337` 版逐字节 `diff` 为空**（比行号判据更强）。

> ⚠️ **判据自身的整改（如实记录）**：本条判据的第一版写成
> `awk … | head -1 || true; echo "未被 hunk 覆盖 ✓"` —— `|| true` 之后**无条件**打印 ✓，
> 即使 awk 报了命中也照样绿，是**恒真死判据**。重写为「展开 hunk 行号集 → 逐块查表 →
> 汇总 FAIL 位」，并加**两个验伪锚**（把已知在 hunk 内的行 474 与 461 喂给同一判据，
> 二者都报 ⛔），证明判据能报红。

> ⚠️ **注释措辞的整改（如实记录）**：注释初稿里写了
> ``其 literal（glob `frontend/src/**`、`npx vitest`）…`` —— 这让「禁字面回退」的 grep
> 判据被自己的注释命中。改为描述性措辞（「其 literal glob 和 runner」）后，
> 四个禁用字面在 `^[^#]*` 口径下**非注释命中全部为 0**。
> 仅剩的含字面注释是 :457 的既有 ChatGPT-Review 说明，非本卡引入。

---

### (c) 落地判据（`judge-c-*.txt` / `judge-c4f-*.txt`）

| 判据 | 修前 | 修后 | 结论 |
|---|---|---|---|
| `test -x scripts/run_cmd_capture.sh` | 文件不存在（`git ls-files` = 0） | PASS | ✓ |
| `bash -n scripts/run_cmd_capture.sh` | — | rc=0 | ✓ |
| `git ls-files -s scripts/run_cmd_capture.sh` | — | `100755` | ✓ mode 保住 |
| `grep -nE '^[^#]*\| *tail -[0-9]+' lefthook.yml .claude/hooks/post-tool-router.sh` | **5 处**（lefthook :466；router :29/:37/:56/:63） | **零命中**（grep rc=1） | ✓ |
| `grep -nE '\| *head -[0-9]+' .claude/hooks/stop-test-runner.js` | 1 处（:34 execSync 内） | 真管道**零命中** | ✓（见下注） |
| `backend-smoke` 块内 `run_cmd_capture` / `TEST_EXIT=$?` | — | 0 / 1 | ✓ 二选一不并存 |
| `frontend-test` 块内 `run_cmd_capture` / `TEST_EXIT=$?` | — | 1 / 0 | ✓ |
| `grep -c 'test_kg_relevance_weighted.py\|test_a11_kg_relevance_e2e.py' lefthook.yml` | 2 | 2 | ✓ A11 目标未动 |

**补跑：被改脚本的语法与权限**（`syntax-check-*.txt`；卡文只要求验 wrapper，
另两个被改的 hook 脚本我一开始漏了，补跑）：

| 文件 | 检查 | rc | 权限位（Y4-C → 现在） |
|---|---|---|---|
| `.claude/hooks/post-tool-router.sh` | `bash -n` | 0 | `100644` → `100644`（未变） |
| `.claude/hooks/stop-test-runner.js` | `node --check` | 0 | `100644` → `100644`（未变） |
| `scripts/run_cmd_capture.sh` | `bash -n` | 0 | 新增 `100755` |

验伪锚：喂一个已知语法错的临时文件，`bash -n` rc=2、`node --check` rc=1
⇒ 这两条判据能报红，不是恒真。

> **`head` 判据的口径说明**：卡文给 lefthook 的正则带了 `^[^#]*` 排除注释，给 `.js` 的
> 那条没带。落地后原始正则仍命中 1 行 —— `stop-test-runner.js:13`，那是 `f19dcff6`
> 随 hunk 带来的 **JSDoc 注释**，正文是「Replaced `pytest ... | head -20` with …」，
> 即在描述被删掉的那个管道。排除 JS 块注释行（`grep -vE ':\s*\*'`）后零命中。
> 这与 `lefthook.yml:487` 注释里提到 `| tail -5` 属同类（卡文 §〇 已为后者定过性）。

---

### (d) 承重金丝雀（`canary-d-*.txt`）

卡文要求的 4 条：

| # | 命令 | 期望 | 实测 |
|---|---|---|---|
| ① | `run_cmd_capture.sh --tail 5 -- sh -c 'exit 7'` | rc=7 + `[TEST FAILURE] exit code: 7` | **rc=7**，头部字样一致 |
| ② | wrapper 包一个 `assert False` 的临时 pytest | rc=1 + 日志路径可见 | **rc=1**，完整 traceback + 日志路径 |
| ③ | `--tail 5 -- true`（正控） | rc=0 且无 `[TEST FAILURE]` | **rc=0**，输出 0 字节，字样 0 次 |
| ④ | `--tail 5 --`（无命令） | rc=64 | **rc=64** |

本卡自加的 5 条边界探测（`canary-d-extra*.txt`），**发现 3 条 wrapper 本体瑕疵**
（均为 `f19dcff6` 原样带入，非本卡引入，本卡不改——改它超出「只做管道→wrapper 变换」的范围）：

| # | 探测 | 实测 | 定性 |
|---|---|---|---|
| ⑤ | `--cwd /nonexistent … -- true` | rc=65 | 符合 docstring |
| ⑥ | 成功且有输出 | rc=0，**stdout+stderr 共 0 字节** | ⚠️ **瑕疵 1 — 成功路径完全静默**。原 `\| tail -20` 至少能看到测试摘要，现在通过时一个字都没有。可观测性净损失，换来 rc 正确 |
| ⑦ | `--cwd` / `--tail` 作为最后一个参数 | `$2: unbound variable`，**rc=1** | ⚠️ **瑕疵 2 — 用法错误的 rc 与「测试失败」撞车**。`set -u` 在 `"$2"` 上抛出，绕过了脚本自己的 usage 分支（那条给的是 64）。调用方无法区分「参数写错了」与「测试真红了」 |
| ⑧ | `--bogus`（未知 flag） | rc=64 | 符合 docstring |
| ⑨ | 日志文件名形态 | `run_cmd_capture_<pid>_<ts>.log.XXXXXX.<rand>` | ⚠️ **瑕疵 3 — `XXXXXX` 字面留在文件名里**。BSD `mktemp -t` 把整串当前缀、自行追加随机后缀（作者按 GNU 语义写的模板）。唯一性由 BSD 的后缀保证，功能无害 |

**Codex round-1 补登记的两条**（同样是 `f19dcff6` 本体、同样不修）：

| # | 探测 | 实测 | 定性 |
|---|---|---|---|
| ⑩ | `TMPDIR=/dev/null` 使 `mktemp` 失败 | `LOGFILE=""` → 重定向失败 → rc=**1**，**被包裹命令根本没启动**，却照样打 `[TEST FAILURE]` | ⚠️ **瑕疵 4 — 设施错误伪装成测试失败**。脚本 `:68` 未检查 `mktemp` 结果。这条比瑕疵 2 更值得修：它不需要参数写错就能触发 |
| ⑪ | `--tail` 传非数字 | `:46` 不校验；非法值让失败摘要里的 `tail` 报错，**成功命令则完全不暴露该错误** | ⚠️ **瑕疵 5 — 参数未校验**。不覆盖已保存的 rc |

**瑕疵 2 的可达性（措辞按 Codex LOW-5 更正）**：全部 **6 处**生产调用点
（`lefthook.yml`；`post-tool-router.sh:37/:46/:64/:69`；`stop-test-runner.js:52`）都
**显式给出了 `--cwd` / `--tail` 的值**——部分是字面量，部分是带引号的变量
（如 `"$PROJECT_ROOT/backend"`，原文写「均为字面量」不准确）。无论哪种，参数位都不会缺失
⇒ 瑕疵 2 在生产路径**不可达**这一结论仍成立。

> **口径更正（Codex MEDIUM-2）**：(d) 表原本可被读成「wrapper 所有路径都等于被包裹命令的
> 退出码」。准确说法是：**正常命令路径保留退出码成立**；参数错误路径给 64（或 `set -u`
> 的 1）、cd 失败给 65、日志创建失败给 1，这些都不是被包裹命令的码。

> ⚠️ **判据自身的整改（如实记录）**：⑧ 第一次跑用 `${PIPESTATUS[0]}` 取 rc，
> zsh 下该变量为空（zsh 用 `$pipestatus[1]`），打印出 `rc=` ——
> **是判据坏了，不是 wrapper 坏了**。重跑后 rc=64。

---

### (d+) 控制组：修前 vs 修后，同一失败输入（`control-group-pipe-*.txt`）

金丝雀只证明了 wrapper 本体正确。这一条对照的是**命令行**——
> ⚠️ **Codex round-1 HIGH-1 更正**：命令行不是 lefthook 实际执行的东西。lefthook 跑的是
> 整个 `run` 块，wrapper 后面还有一行 `echo`，它的 0 会盖掉 wrapper 的码。本表下方
> 「完整 run 块」一节才是修好的证据；本表只证明 wrapper 那一行传播正确。

两条命令**都逐字取自 git / 工作树**（`git show 16b9e337:lefthook.yml | sed -n '466p'`
与 `sed -n '474p' lefthook.yml`），不是手打的近似物：

| 端 | 命令 | rc |
|---|---|---|
| 基线端（`16b9e337` 版 :466） | `npm --prefix frontend/obsidian-plugin test 2>&1 \| tail -20` | **0** |
| 处理端（现行 :474） | `./scripts/run_cmd_capture.sh --cwd frontend/obsidian-plugin --tail 120 -- npm test` | **127** |
| **前提自证** | 裸 `npm test`（在 `frontend/obsidian-plugin` 内） | **127** ← 输入确实是失败的 |

同一个真实失败：**修前被吞成通过，修后被正确传出**。

补充演示（`pipe-semantics-demo-*.txt`）：`post-tool-router.sh` 那 4 处是
「管道 + `[ $? -ne 0 ] && exit 1`」结构，实测修前形态判定「通过，继续往下走」、
修后形态 `|| exit 1` 触发且 rc=3。修前原文
（`16b9e337:.claude/hooks/post-tool-router.sh` :29/:30、:37/:38、:56/:57、:63/:64）
四对结构已贴。`:43`（vulture）与 `:67`（knip）无管道、判的是真 rc，
`7f495eda` 保留它们直连是对的。

---

### (e) 基线对账（承重）

**口径**：`grep -E '^(FAILED|ERROR) tests/' | sed 's/ - .*//' | sort` 后逐 nodeid diff，
与红基线文件头部第 4 行规定的一致。分母是 **nodeid 数**，不是日志行数
（基线文件第 5 行已勘误「298 / 289」是含噪音的行数）。

| 时点 | commit | nodeid | 与红基线 diff |
|---|---|---|---|
| 红基线 `unit-red-baseline-03ac8bf8.txt` | `03ac8bf8` | **247**（FAILED 209 / ERROR 38） | — |
| **开工** `unit-pre-20260906T132440.txt` | `16b9e337` | **247** | **空 ✓**（无环境 / 主干漂移） |
| 三 pick 后 `unit-post-20260906T133608.txt` | `abc6fb78` | 204 | 减 45 / 新增 **2** ⛔ |
| 收工（Codex 整改前） `unit-post2-20260906T134314.txt` | `aae845f8` | **202** | 减 45 / 新增 **0** ✓ |
| **收工终版** `unit-post3-20260906T140952.txt` | `556ecc3d` | **202** | 减 45 / 新增 **0** ✓ |

收工终版末行：`173 failed, 4605 passed, 48 skipped, 122 warnings, 29 errors in 253.07s`

**post3 与 post2 逐 nodeid 完全相同** ⇒ Codex round-1 的三处整改零回归
（`reconcile-final-*.txt`）。收工基线因此绑定的是**最终代码树 `556ecc3d`**，不是审时的
`aae845f8`。

#### 三列表（`reconcile-e-*.txt` / `reconcile-e-fixed-*.txt`）

**第一列 — 由 skip 造成的减少 = 43（不是修复）**

| 文件 | 条数 | 被 skip 的范围 |
|---|---|---|
| `test_memory_service_write_retry.py` | **18** | 模块级 `pytestmark`（`TestWriteRetryStrictQA` 7 + `TestWriteToGraphitiJsonWithRetry` 11） |
| `test_graphiti_json_dual_write.py` | 8 | 模块级 `pytestmark`（`TestGraphitiJsonDualWrite`） |
| `test_story_30_10_idempotency.py` | 9 | 类级 ×3：`TestEpisodesDedup` 3 / `TestBatchEpisodesDedup` 2 / `TestGraphitiJsonWriteDedup` 4 |
| `test_failure_observability.py` | 3 | 类级 `TestMemoryServiceDualWriteFailure` |
| `test_qa_38_6_scoring_reliability_extra.py` | 2 | 类级 `TestFullCycleIntegration` |
| `test_story_38_6_scoring_reliability.py` | 3 | 类级 `TestAC3StartupRecovery` |
| **合计** | **43** | |

> **`test_memory_service_write_retry.py` 的 18 条 = 台账「memory_service 重试 18」那一项。
> 这 18 条是 `skipped（stale-mock）`，不是修复。** 整个文件测的是
> `MemoryService._write_to_graphiti_json_with_retry`，该方法已被
> `fix-rag-transform-and-episode-isolation` 删除，语义移到 `GraphitiEpisodeWorker`。

**第二列 — 真实修好 = 2**

| nodeid | 证据 |
|---|---|
| `test_story_30_10_idempotency.py::TestDeterministicEpisodeId::test_id_format` | 单跑 `-v` → **PASSED** |
| `test_story_30_10_idempotency.py::TestBatchDeterministicEpisodeId::test_batch_id_format` | 单跑 `-v` → **PASSED** |

由 `0fd6d398`（→ `abc6fb78`）修：断言 hash 长度 16，而
`memory_service.py:158/:172` 两处生成器都是 `sha256(...).hexdigest()[:32]`。
**运行时实测**：`episode-e27adf0eca6ba53e206256a9e55b2303`（前缀后 32 位）、
`batch-f820d5eac282e299c108a2154b3518e2`（32 位）。⇒ 断言是陈旧的，改 32 是对齐真实
行为，**不是迁就实现**。

> **分类不是靠猜的对照**：同一个文件里，`TestEpisodesDedup` 三条单跑是 **SKIPPED**、
> 这两条单跑是 **PASSED**（`reconcile-e-fixed-*.txt` 两段并列）。同文件内一半 skip
> 一半 pass，把「减少」拆成两类才有实证基础。

**第三列 — 新增红 = 0**

三 pick 后曾有 **2 条新增红**（`unit-post-20260906T133608.txt`）：
`test_episode_worker_retry.py::test_basic_enqueue_and_process` 与
`::test_dead_letter_on_retries_exhausted`。按卡文「修或撤」处置，**选修**
（见 `aae845f8`）——撤掉它等于抽掉那 43 条 skip 所承诺的「等价覆盖」，
每条 skip 的 reason 字符串都直指这个文件。

两条都是断言过期，**先读生产源码确认新行为是有意加固**才改：

| 断言 | 生产实况 | 处置 |
|---|---|---|
| `call_kwargs["group_id"] == "canvas-test"` | `episode_worker.py:588-601` 写 graphiti 时套 `semantic_group_id(...)`（D16 语义影子分组，`__semantic` 后缀），2026-04 写这条时影子分组尚不存在 | 改期望为字面量 `"canvas-test__semantic"`，并**补一条独立不变量**：`task.group_id == "canvas-test"`（影子分组不得就地改写 task 自身归属） |
| `"episode_body_full" in record` | `episode_worker.py:205-254`：**未截断**的 `episode_body_full` 只在 `DEAD_LETTER_STORE_FULL_BODY=true` 时落盘（且过 `_redact()`）。原断言在默认配置下**恒假** | 反向锁：`"episode_body_full" not in record` + sha256 / length 正确 + **截断正文锚点**（见下方更正） |

**期望值不与被测量同源**：`__semantic` 写字面量而非调 `semantic_group_id()` 求值；
sha256 对字面 body 独立计算而非从 `record` 反取。**承重变异**：把 `__semantic` 期望改回
旧值 → 该断言报红；把 sha256 的输入改一位 → 该断言报红。变异后 `shasum` 还原逐字节一致。

`test_episode_worker_retry.py` 现 **5 passed**（卡文要求）。

#### 卡文没预料到的一笔账：47 条 SKIPPED，其中 4 条原本是绿的

（`skip-collateral-*.txt`）6 个文件实际产生 **47 条 SKIPPED**，而红基线里只有 43 条。
差额 4 条**在红基线里不存在、在开工基线 `pre` 里也不是红的** ⇒ 它们本来是正常通过的测试，
被**模块级 / 类级** skip 顺带关掉：

| nodeid | 被哪个 skip 波及 |
|---|---|
| `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_config_flag_disables_dual_write` | 模块级 `pytestmark` |
| `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_fire_and_forget_doesnt_block_return` | 模块级 `pytestmark` |
| `test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::test_timeout_protection` | 模块级 `pytestmark` |
| `test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_no_file` | 类级 |

**这说明「按红基线对账」这个判据对覆盖损失是失明的**：只看红名单的增减，
永远看不见「原本绿的被一起关掉」。43 + 4 = 47，两个数字都要记。
这 4 条是**净覆盖损失**，本卡只登记不修复。

---

### (f) stop-test-runner.js —— exit 2 协议

只取 `f19dcff6` 的 wrapper 化 hunk，未改 Stop hook 协议本身。

| 项 | `16b9e337` | 现版 |
|---|---|---|
| `process.exit(2)` 处数 | 2（:41 / :49） | **1（:63）** |
| 失败检测方式 | `/FAILED\|ERROR/.test(result)` 文本匹配 | `execSync` 抛异常（= 进程退出码非 0） |
| timeout | 120000 | 300000 |
| 解释器 | `python` | `.venv/bin/python` |
| stdio | 默认（1MB maxBuffer） | `'inherit'` |

**减掉的那一处（旧 :49）原来负责什么，以及语义变化**——如实声明：

旧 :49 在外层 `catch` 里，条件是 `if (e.status === 2)`：只有当 execSync 抛出且退出码
**恰好是 2** 时才 exit 2。但旧代码用管道，rc 恒 0、几乎不抛；且 pytest 的 rc=2 语义是
「collection error / 用户中断」，与「有测试失败」（rc=1）不是一回事。

现版把判断挪进内层 `catch`：**pytest 任何非 0 退出码都 → exit 2（阻断）**，
外层 catch 一律 exit 0（git 命令等前置设施出错不阻断）。

⇒ **准确说法（Codex round-1 LOW-7 更正，原文写「从阻断变放行：无」与下一句自相矛盾）**：
**真实的非零测试结果没有从阻断变成放行**——方向相反，原本 rc=1（有测试失败）在旧版是
放行的（管道吞掉 + 正则未命中即放行），现在会阻断。确实存在**两处放宽**，但都不是测试结果：

1. 前置 `execSync` 最终抛出且 `status===2` 时，旧版阻断、新版外层放行（那是 git 等设施错误）；
2. 测试实际返回 0、但截断输出里恰好含 `FAILED`/`ERROR` 字样时，旧版正则会**误拦**，新版不再误报。

卡文 (f) 判据「`grep -c 'process.exit(2)'` ≥1 且失败分支是 exit 2」：**1 ≥ 1，
且 :63 正是 pytest 失败分支** ✓

---

### (g) hook 真跑 + ruff format 声明

四次 commit 全部**未使用** `LEFTHOOK_EXCLUDE`。逐次 hook 结果：

| commit | pre-commit | commit-msg |
|---|---|---|
| `33fd106d` | `ghost-files` ✔ / `mutant-residue-scan` ✔ / `python-lint` ✔（format 见下） / `python-typecheck` skip（无文件） / `spec-sync-*` skip / `cypher-vault-filter-lint` skip / `readme-claims-lint` skip | `commitlint` ✔ / `spec-reference` ✔ |
| `e6ad26e1` | `ghost-files` ✔ / `mutant-residue-scan` ✔ / `python-lint` skip（无 .py） | ✔ / ✔ |
| `abc6fb78` | ✔ / ✔ / `python-lint` ✔（Format OK） | ✔ / ✔ |
| `aae845f8` | ✔ / ✔ / `python-lint` ✔（Format OK） | ✔ / ✔ |
| `556ecc3d` | ✔ / ✔ / `python-lint` ✔（Format OK） | ✔ / ✔ |

**`ruff format` 声明（卡文 (g) 授权）**：`33fd106d` 第一次提交时 `python-lint` 的
format 检查对 9 个文件报红。**先查基线再动手**：逐个把 `HEAD~1` 版本喂给
`ruff format --check --stdin-filename`，8 个既有文件在**未 pick 状态就已 rc=1** ⇒
漂移是存量、非本卡引入；第 9 个是 `f19dcff6` 于 2026-04 新建的文件，用当时的 ruff 格式。
ruff 版本 `0.15.9`。同 commit 内 `ruff format` 收敛，额外改动 **+108 / −334 行，纯格式**。

> ⚠️ 过程记录：第一次跑 `ruff format $FILES` 用了一个空格分隔的变量，
> **zsh 不分词**，整串被当成单个文件名，rc=2 且一个文件都没改。改逐文件循环后正常。

**commitlint 拦截记录**：`abc6fb78` 第一次提交时 header 102 字符 > 100 被 commitlint
拦下（我在提交前已用 python 量过并看到超限，但没读就提交了）。缩到 96 字符后通过。

---

### (裁判 7/8) 隔离与面积（`judge-78-*.txt`）

| 裁判 | 结果 |
|---|---|
| `git diff 16b9e337 HEAD -- backend/tests/conftest.py backend/tests/support/live_port_guard.py backend/tests/unit/conftest.py` | **0 字节**（Y7-A / Y6-A 地盘未碰）✓ |
| `git diff 16b9e337 HEAD -U0 -- lefthook.yml \| grep '^@@'` | 2 个 hunk，均在 pre-push（起始 453）之后 ✓ |
| `git diff 16b9e337 HEAD --stat -- . ':(exclude)_bmad-output'` | **恰 13 文件**，rc=0 ✓ |

> pathspec 写法用 `':(exclude)…'` 而非 `':!…'`（协议 §1：后者在 zsh + git 2.50 下
> rc=128 且 stdout 空，「为空即通过」会假绿）。

---

### (h) Codex round-1

存档 `_bmad-output/审查/codex-review-CARD-TOOL-testinfra-salvage.md`（首部按协议 §2.1，
`gpt-6-astra` / `ultra` / `codex-cli 0.153.3`，会话头自证抄自 `.stderr`；stderr 本身不入库）。
**审查绑定 `16b9e337..aae845f8`；审后按本轮意见改了代码 ⇒ HEAD 已前进到 `556ecc3d`，
本轮结论对当前代码树失绑，「整改未复审」已登记（轮次用 1/3，未再发第 2 轮）。**

Codex 判定：**BLOCKER 无**，1 HIGH + 3 MEDIUM + 4 LOW。逐条处置：

| # | 级别 | 内容 | 我的复核 | 处置 |
|---|---|---|---|---|
| 1 | **HIGH** | `lefthook.yml:474` 的 wrapper 后面那行 `echo` 无条件执行，其 rc 成为整个 `run` 块的 rc。lefthook 2.1.6 用 `sh -c` 且不带 `-e` | **成立，我错了。自己复现**：只跑 wrapper 那行 rc=127，跑完整 run 块 rc=**0** | **修**（`556ecc3d`）：补 `\|\| exit $?` |
| 2 | MEDIUM | wrapper 第 4 条瑕疵：`mktemp` 结果未检查，失败后 `LOGFILE=""` → 重定向失败 rc=1，**命令根本没启动**却打「测试失败」 | 成立（Codex 用 `TMPDIR=/dev/null` 实测） | **登记不修**（f19dcff6 本体，超出「只做管道→wrapper 变换」范围）；(d) 表已补 |
| 3 | MEDIUM | 我声称「默认只留 sha256+length」不准确：`record` 由 `**task.to_dict()` 展开，`to_dict():108` 落 `episode_body[:200]` | **成立，我错了。**我在 traceback 里看到过 `'episode_body': '{"action":"test"}'` 却没意识到它与我的声明矛盾 | **修**（`556ecc3d`）：注释与验收单口径收窄为「默认不落**未截断**的 `episode_body_full`」+ 补一条截断正文锚点断言 |
| 4 | MEDIUM | 47/43 差额 4 条属实，三列账没造假 | 一致（Codex 用 `unit-pre` 的进度串点位独立验证那 4 条原本是 `.`，比我「不在红名单」的推断更强） | 无需处置 |
| 5 | LOW | 三条 wrapper 瑕疵定级合适，但登记不完整：`--tail` 不校验是否为数字；且「调用点全是字面量」不准确（有的是带引号的变量） | 成立 | **改措辞**（见 (d)）+ 补第 5 条瑕疵 |
| 6 | LOW | 测试 fixture 没清 `DEAD_LETTER_STORE_FULL_BODY`，开了它的机器上会假红 | 成立 | **修**（`556ecc3d`）：`monkeypatch.delenv` |
| 7 | LOW | (f) 写「阻断→放行：无」与紧接着承认外层放宽自相矛盾 | 成立 | **改措辞**（见 (f)） |
| 8 | LOW | 「10 个测试文件」应为 9 测试 + 4 配置/脚本；「每条 skip reason 都直指新文件」过宽 | 成立（`skip-detail:56-61` 的恢复用例理由只写「需另行设计」） | **改措辞**（见头部与 (e)） |

#### HIGH-1 的修复与验证（`high1-repro-*.txt` / `high1-fixed-*.txt` / `high1-three-way-*.txt`）

判据换成**完整 `run` 块**（从 `yaml.safe_load` 解析出来，不是手抄）：

| 场景 | rc | 说明 |
|---|---|---|
| `node_modules` 缺席（真实本机，走 else） | **0** | 正常跳过 |
| `if` 恒真 + `npm test` 真失败 | **127** | 修前是 0 |
| `if` 恒真 + 命令换成 `true` | **0**，且仍打印 `Plugin tests done.` | 成功路径不受影响 |

**三端对照**（每端都断言了脚本文件非空且含关键内容，防跑空文件的假证据）：

| 端 | 完整 run 块 rc |
|---|---|
| Y4-C 基线端（`16b9e337`） | **0**（吞） |
| 中间态 = 只换 wrapper、不加 `\|\| exit`（即 Codex 审到的那版） | **0**（仍吞） |
| 终态（`556ecc3d`） | **127**（传出） |

> 第一次跑三端对照时，「中间态」那条 `sed` 的分隔符 `\|` 与内容里的 `\|\|` 冲突而失败，
> 于是跑的是**空文件**、rc=0 —— 又一次「判据坏了，不是被测物坏了」。改用 python 构造
> 并对每个脚本断言「非空 + 含 `npm test` + 含/不含 `\|\| exit`」后重跑。

#### MEDIUM-3 的修复与验证（`medium3-recheck-*.txt` / `codex-fix-verify-*.txt`）

直接跑一次 `DeadLetterStore.store()` 把真实 `record` 的键打出来：

```
record 的键: ['created_at', 'episode_body', 'episode_body_length', 'episode_body_sha256',
              'error', 'error_type', 'failed_at', 'group_id', 'name',
              'reference_time', 'retry_count', 'source_description']
episode_body 字段值: '{"action":"test"}'
episode_body_full 在不在: False
```

⇒ **正文（截断到 200 字符）一直都在 `record["episode_body"]` 里，而且它走 `to_dict()`、
不过 `_redact()`**。隐私加固加的是「不落**未截断**全文」，不是「不落正文」。
对短 body 而言截断等于没截断。**这是存量隐私面，已登记（(i)-2 第 10 条），本卡不修。**

承重变异（跑前跑后 `shasum` 一致）：

| 变异 | 结果 |
|---|---|
| 拆掉 `monkeypatch.delenv`，在 `DEAD_LETTER_STORE_FULL_BODY=true` 下跑 | **红**，错误消息正是那条断言 ⇒ MEDIUM-6 的修复承重 |
| 把 `record["episode_body"]` 的期望改成 `'{"action":"WRONG"}'` | **红** ⇒ 新增的截断正文锚点承重 |

整改后 `test_episode_worker_retry.py` 仍 **5 passed**；`DEAD_LETTER_STORE_FULL_BODY=true`
环境下也 **1 passed**（fixture 隔离生效）。

#### Codex 独立确认的部分（比我自己的证据更强的几条）

- 9 个 python 文件从 `f19dcff6` 原版到格式化后的 `33fd106d` **AST 全等** ⇒ 我声称的
  「+108/−334 纯格式」得到独立验证（我只跑了 `ruff format --check`，没做 AST 对比）；
- 那 4 条「原本绿」的测试，它把基底源码收集顺序与 `unit-pre` 的进度点串对照定位到
  `unit-pre:112` 的第 2/4/5 个 `.` 和 `:241` 的第 9 个 `.` ⇒ 不是靠「不在红名单」推断；
- 总数独立复算：`4602 + 2 修正 + 5 新测试 − 4 被关闭 = 4605`，`1 + 47 = 48 skipped` ⇒ 与
  收工跑末行一致；
- `backend-smoke` 段两版**均为 626 字节**、逐字节相同；三份禁改文件基底与 HEAD blob 全同；
- `66d6a835` 不是 HEAD 祖先，区间内无 merge commit。

---

## (i)-1 本卡未证明什么

1. **tests/unit 剩余的红一条都没修**。减少的 45 条里 **43 条是被 skip 掩盖**，
   只有 2 条（`test_id_format` / `test_batch_id_format`）是真修好。
2. **43 条 skip 的「等价覆盖」承诺未验证**。每条 skip 的 reason 都指向
   `test_episode_worker_retry.py`，但那里只有 5 条测试。本卡没有做覆盖对照，
   不能声称「语义没丢」。
3. **另有 4 条原本是绿的测试被顺带 skip**（见 (e)）。这是净覆盖损失，本卡只登记不修复。
4. **pre-push 从未真实触发**。需要 `git push`（本卡禁 push）+ `frontend/obsidian-plugin/node_modules`
   存在（本机缺席，lefthook 的 `if [ -d ]` 守卫为假）。控制组是绕过守卫直接跑命令体，
   证明的是「命令体的退出码传播」，不是「lefthook 真的调用了它」。
5. **`post-tool-router.sh` / `stop-test-runner.js` 在 Claude 运行时下的真实触发未测**。
   只测了 wrapper 本体与命令体结构；这两个 hook 需要真实的 PostToolUse / Stop 事件才会跑。
6. **wrapper 的日志不清理**。`$TMPDIR/run_cmd_capture_*` 每次调用留一个文件，
   脚本 docstring 明说交给操作者定期清。本卡跑金丝雀已产生若干个。
7. **两个 integration 文件的 skip 未跑验证**（`test_dual_write_consistency.py` 模块级、
   `test_story_38_7_ac5_recovery_and_cross_story.py` 类级）。卡文禁跑
   `tests/integration` 目录级（advisory 会真连 7691）。
8. **`0fd6d398` 那 2 条转绿只在本机**（Python 3.14.4 / pytest 9.0.2 / 本车道 venv）。
9. **wrapper 的 5 条瑕疵未修**（见 (d)，其中 4/5 由 Codex round-1 补出）；瑕疵 2 的
   「生产不可达」结论依赖当前 6 处调用点都显式给出参数值——新增调用点时该结论需重验。
   **瑕疵 4（`mktemp` 失败伪装成测试失败）不需要参数写错就能触发，是这 5 条里最该修的。**
10. **Codex round-1 的整改未复审**：本轮绑定 `16b9e337..aae845f8`，整改后 HEAD 是
   `556ecc3d`。HIGH-1 / MEDIUM-3 / MEDIUM-6 三处改动**没有经过第二轮外审**（卡文只给 1 轮）。
   HIGH-1 的修复我自己用完整 `run` 块 + 三端对照验过，但那是自证。
11. **`|| exit $?` 只在 `sh` 语义下验过**。lefthook 2.1.6 在本机用 `sh -c`；
   若将来换 shell 或 lefthook 改了执行器，该结论需重验。
12. **`episode_body` 的存量隐私面未修**：dead-letter 默认落未脱敏的截断正文（见 (h) MEDIUM-3）。

---

## (i)-2 台账待登记条目

1. **salvage 三 sha 已抽**：`f19dcff6` → `33fd106d`、`7f495eda` → `e6ad26e1`、
   `0fd6d398` → `abc6fb78`（另 `aae845f8` 为本卡新增的修复，非 pick）。
2. **`66d6a835` 显式排除**，建议作废 `fix/test-infra-paralysis` 分支
   （tag 由主 session 打）。排除证据见 (a)：它缺 5 个 hook 块，分别来自第四批 G1-5、
   第十批 DEBT-openapi-sync-R1、第十一批、wave-5 stage-c。
3. **tests/unit 基线 247 → 202**：其中 skip 掩盖 43 / 真实修好 2 / 新增红 0。见 (e) 三列表。
4. **`test_memory_service_write_retry.py` 18 条**改记为「skipped（stale-mock）」，
   **不是修复**（= 台账原「memory_service 重试 18」那一项）。
5. **4 条原本绿的测试被类/模块级 skip 顺带关掉**（见 (e)）——净覆盖损失，需单独登记。
6. **wrapper 日志清理策略待定**：`$TMPDIR/run_cmd_capture_*` 无自动清理。
7. **wrapper 3 条瑕疵**（成功路径静默 / 参数缺失 rc 与测试失败撞车 / `mktemp -t` 的
   `XXXXXX` 未展开）——建议单开一张小卡，本卡范围内不改。
8. **`lefthook.yml:487` 注释仍提 `| tail -5`**（历史说明，非管道）；
   **`stop-test-runner.js:13` 注释提 `| head -20`**（同类）。判据用 `^[^#]*` /
   排除 JSDoc 行的口径即可，不必改注释。
9. **`f19dcff6` 的 `test_episode_worker_retry.py` 在当前主干上原样有 2 条红**——
   已由 `aae845f8` 修（断言过期，非生产缺陷）。若将来 revert 本卡的 pick，这条修复
   会一并消失。
10. **存量隐私面**：`DeadLetterStore` 默认落 `episode_body[:200]`（走 `to_dict()`，
    **不过 `_redact()`**），对短 body 等于落全文未脱敏。`episode_body_full` 的开关与
    `_redact` 只管未截断那一份。建议单开卡评估是否也该脱敏/去掉截断正文。
11. **`|| exit $?` 是 Codex round-1 才补上的**（`556ecc3d`）；`f19dcff6` 原版有同样缺陷。
    若别处照抄 `f19dcff6` 的 wrapper 用法，同一个坑会重现——建议把「wrapper 调用后必须
    `|| exit $?` 或显式 `exit`」写进规则文件。
12. **HIGH-1 / MEDIUM-3 / MEDIUM-6 三处整改未复审**（轮次用 1/3）。
