# UAT — CARD-TOOL-openapi-R2

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-openapi-R2]` · 车道 `card-y5-review`（分支 `card/y5-review`）
> 开工基线 HEAD `36871263`（Y5-B / CARD-RV-B 末 commit） · 本卡 commit：`f0b1e282`（主体，Codex 审此 SHA）+ 整改 commit（见 §五）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y5-C.md` · 协议 `.claude/rules/card-batch-protocol.md`
> 裁判原始输出全部落盘 `_bmad-output/审查/evidence-openapi-r2/`；本文只引用路径与判据行，不自述数字（协议 §2.2）。

---

## 一 本卡做了什么（两件，同一对文件，故并卡）

1. **`scripts/spec-tools/check-openapi-drift.py:254` 的 FIX 提示串两缺陷同修**（同一 hunk）
   - 解析器：裸 `python` → 仓内 venv 解析器存在则用、否则回落 `python3`（口径对齐 `lefthook.yml:54`）
   - 路径：相对路径 → `Path(__file__).resolve()` 与 `BACKEND_DIR / "openapi.json"` 两个绝对路径，并各加一对双引号
   - 尾注 `  (禁手改快照)` 保留；`X_GENERATOR_NAME` 一字未改
2. **`backend/tests/contract/test_openapi_snapshot_drift.py` 补 round-3 三原形回归锁 3 门（23 → 26）**
   - 原形①：Schema 位置的 `x-*` 扩展里携带字面 `required` 数组
   - 原形②：Link Object 的字面 `requestBody`
   - 原形③：名叫 `enum` / `value` 的合法属性名
   - 三门定位 = **防止重新引入 required 排序启发式的回归锁**；当前实现（`_normalize` 一切数组保序）下**本来就绿**；依据 `check-openapi-drift.py:121-129` 的三轮终局结论

---

## 二 完成条件逐条对账

| 条 | 判据 | 证据 |
|---|---|---|
| (a) | FIX 串两缺陷同修，`X_GENERATOR_NAME` 未改 | `judge8-hunk-range-*.txt`、`judge8-recheck-nocolor-*.txt` 的「六处零改动」段 |
| (b) | 真实 FIX 串在仓库根与 `backend/` 各逐字执行一次，两次 `rc=0` + `WROTE:` | 取串 `judge3-real-fix-line-*.txt`；执行 `judge45-fix-verbatim-*.txt`（含 `rc_root` / `rc_backend` 与前后 sha） |
| (c) | 三门补齐，`grep -c '^def test_'` = 26 | `judge1-7-9-11-postrestore-*.txt` 的「裁判 2」段 |
| (d) | 三门 docstring 写明回归锁 / 当前本来就绿 / 引用 `:121-129` | 源码 `test_openapi_snapshot_drift.py:251-315`；Codex §三判「无问题」 |
| (e) | 四处（含 `_load_drift_module`、`X_GENERATOR_NAME`）零行为改动；26 门全绿；`DRIFT: none` | `judge8-recheck-nocolor-*.txt`（带验伪锚）、`judge1-7-9-11-postrestore-*.txt` |
| (f) | `openapi.json` 只变 `x-generated-at`，随后**还原**（见 §四） | `judge67-diff-and-drift-*.txt`；`git status --porcelain -- backend/openapi.json` 为空 |
| (g) | 面级裁判 + ruff 基线对比 + pyright 按 D-14 | `judge10-ruff-*.txt`、`judge1-7-9-11-postrestore-*.txt` 的「裁判 9」段、`pyright-d14-*.txt` |
| (h) | Codex 一轮五分节，prompt 禁用词计数 0 | `_bmad-output/审查/codex-review-CARD-TOOL-openapi-R2.md`（首部按协议 §2.1）；prompt 见同目录 `prompts/` |
| (i) | 「本卡未证明什么」+「台账待登记条目」 | §六 / §七 |

### 卡文之外自加的两条证明（卡文未要求，但不做就留白）

- **旧串对照**（`oldstring-control-*.txt`）：把改动前的 FIX 串在两个 cwd 逐字执行。仓库根 `rc=1`（裸 `python` 解析到 homebrew 3.14 而非仓内 venv，报 `ModuleNotFoundError: structlog`）；`backend/` 下 `rc=2`（`can't open file .../backend/scripts/...`）。两个缺陷都是本机实测复现，不是推断。
- **回落分支行为探针**（`fallback-branch-probe-*.txt`）：把 `BACKEND_DIR` 指到一个没有 `.venv` 的临时目录并走真实 `check_drift` 路径，断言回落分支产出的是「`"python3"` + 两个绝对路径 + 三对双引号 + 尾注」。这补上了「`else` 分支到底产出什么」这一块——**但仍不等于 CI 上能跑通**（见 §六）。

---

## 三 三门的承重证明（不是「加了三条 assert」）

`negctl-three-archetype-locks-*.txt`：把 `_normalize` 原地换成四种排序启发式，跑**真 pytest**，跑完无条件还原并比对全文件 sha（存档首行 / 末行的 `PROD-SHA-BEFORE` = `PROD-SHA-AFTER`、`RESTORE-OK = True`）。四种变体：朴素键名 / 形状守卫 / 语境切分 / 语境切分且把 `value` 也划为数据。

三点值得记：

1. **三门在前三种启发式下全部转为失败**；第四种下第三门保持通过而其余三门仍失败 —— 组合覆盖成立，但**单门不是万能锁**，这是诚实边界。
2. **第三门在「语境切分」下失败在细节断言那一条**（`>properties>value>required`），不是第一条 `assert not clean`。若该门只写 `assert not clean`，它在那种启发式下会假通过 —— 细节断言是这门唯一的牙齿。Codex §二独立复核后同判。
3. **三门不是覆盖缺口的填补**：既有 `test_required_order_is_drift` 已能捕获任何会排序裸 Schema `required` 的实现。三门的增量是把 `:121-129` 里三个反例从散文变成**可执行的具名失败**，让将来重新引入者当场看到崩在哪个原形上。

---

## 四 `backend/openapi.json` 的处置（卡文 (f) 二选一）

选 **①「还原」**。理由：本卡不碰 `backend/app/**`，快照内容零变化，`judge67-diff-and-drift-*.txt` 记录两次 `--write` 后全部增删行只有一对 `x-generated-at`；提交一个纯时间戳 diff 只是噪音。

执行：`git checkout HEAD -- backend/openapi.json`（执行前该文件**未暂存**，符合卡文限定）。还原后 `git status --porcelain -- backend/openapi.json` 为空，且本卡两个 commit 的文件清单都不含它。还原后复跑 `--snapshot openapi.json` 仍为 `DRIFT: none`（`judge1-7-9-11-postrestore-*.txt`）。

---

## 五 DoD-3

### 4-A Claude 已代验

**裁判 1-11 全部通过**，原始输出逐条落盘（路径见 §二 表格）。逐条说明只记与卡文表述不同之处：

- **裁判 1** 开工先跑 HEAD 版基线（`judge1-pytest-26-*.txt`，该份 rc 行为空 —— zsh 下 `${PIPESTATUS[0]}` 不生效，协议 §2.2 已记此坑；随后 `judge1-pytest26-*.txt` 用 `echo "rc=$?"` 重跑并正确记 rc）。整改后再复跑一次（`remediation-ast-equiv-*.txt` 的 (2) 段）。
- **裁判 3-5**：FIX 串**不是静态阅读得来的**，是先把快照复制到 scratch、改掉其中一处 `description` 造出真漂移，再从 stderr 原样取回，然后在两个 cwd 各逐字执行一次。
- **裁判 8** 复验时踩到一个坑，如实记录：共享 `.git/config`（`git rev-parse --git-common-dir` 指向主仓，多车道共用）在本卡作业期间被**并发改动**，`color.ui` / `color.diff` 一度为 `always`，使 `git diff | grep '^@@'` 与 `grep '^[-+] '` 静默归零 —— 那一轮的「hunk 为空」「六处零改动」是**假绿**。已改用显式 `--no-color` 标志重跑，并加**验伪锚**（同一管道对全树能数出 `@@` 与增删行 > 0，证明判据此刻是活的）：`judge8-recheck-nocolor-*.txt`。
  - **回头复验了本卡此前每一份存档**（`judge8-recheck-nocolor-*.txt` 之外另跑了一次全目录 ESC 计数）：
    commit 之前跑的那批（含**裁判 6**、裁判 8 首轮、pyright 的 `-U0` hunk 求交）ESC 计数为 0，
    且存档里逐字保留了 `-/+ "x-generated-at"` 两行原文与 `@@` 行 —— 说明那几次 grep **真的匹配到了**，
    结论有效，不需要重跑。受影响的只有整改后那一轮（`remediation-ast-equiv-*.txt` 的 (4)(5) 段），
    已被 `judge8-recheck-nocolor-*.txt` 取代。`judge3` / `judge45` 两份 ESC 非 0 是 LiteLLM 的彩色
    WARNING，与 git diff 判据无关。
- **裁判 9** 只做 `--collect-only`，不执行 `tests/contract` 目录级（同目录 schemathesis 单 operation 就要三分钟以上）。
- **裁判 10** 先对 HEAD 版跑基线（两文件均已 formatted、checks passed），本卡零新增漂移。
- **pyright / D-14**：`pyright-d14-*.txt` 贴了原始输出。命中 lefthook `python-typecheck` glob（`{backend,src}/**/*.py`）的只有那个测试文件，**0 errors** ⇒ 本卡**没有使用** `LEFTHOOK_EXCLUDE`，commit 正常通过该门。脚本文件不在 glob 内、有存量报错，其行号集与本卡改动行区间**求交为空**（同一份存档的第 (3) 段）。
- **补 Codex 自述的读取面缺口**：Codex §四明确声明「`check_drift` 前半段不在指定读取区间内，全函数作用域的重名/遮蔽未完成独立核验」。已用 AST 对全函数补验（`shadowing-full-func-audit-*.txt`）：四个新变量与既有局部名交集为空（既有 `snapshot` 在 `:222`，本卡用 `fix_snapshot` 避开）、各自只绑定一次、不遮蔽任何模块级名字、改动区间内未重新绑定任何既有名。

**Codex 一轮逐条采信 / 驳回**（存档 `codex-review-CARD-TOOL-openapi-R2.md`，末行 `BLOCKER/HIGH 清零：是`）：

| # | Codex 判 | 我的处置 | 依据 |
|---|---|---|---|
| §一 MEDIUM-1 | 整行仍不能原样粘贴执行（`bash -n` rc=2），与新增注释「逐字复制」的说法不一致 | **拆开：事实采信 + 定性部分驳回** | 我独立复验（`codex-medium1-verify-*.txt`）：**整行**在新旧两版**都** rc=2，**命令段**在新旧两版**都** rc=0 ⇒「整行不可执行」是 `FIX: <命令>  (说明)` 这个改动前就有的既有格式，**非本卡引入**；卡文 (b) 的判据本就指定复制命令段。但 Codex 指出的「注释措辞比证据宽」成立 ⇒ **已整改注释措辞**（§五 整改段） |
| §二 | 三门都有牙齿，无死门；第三门细节断言确实承重；组合覆盖成立 | **采信**（与我的负控矩阵一致） | Codex 独立给出的触发位置与语义，与 `negctl-*.txt` 的四变体结果互证 |
| §三 LOW-1 | 注释写「缺 fastapi 即 ImportError」，实测是缺 **structlog**；CI 未实跑却写成事实 | **全采信** | 属注释里的事实错误 ⇒ **已整改**：改为「本机实测报 `ModuleNotFoundError: structlog`；CI 上的表现未实跑」 |
| §三（三门措辞） | 三门定位无问题，标题里的「修复」指向 FIX 提示、未把三门包装成新修复 | 采信，无动作 | — |
| §四 | 六处符号与单 hunk 无问题；但全函数作用域重名未独立核验（读取面自限） | 采信 + **自行补验** | `shadowing-full-func-audit-*.txt` |
| §五 | `openapi.json` 恢复状态不在授权读取面，未独立核验 | 采信（属其读取面限制） | §四 + `git status` |

**整改（审后改代码 = 失绑，如实登记）**：按上面两条只改**注释文字**，做成独立 commit。零行为变化的证明不是「我看过了」，而是 **AST 等价**：审时版 `f0b1e282` 与整改后工作树的 `ast.dump` 逐字节相同，且带**验伪锚**（把 `python3` 改成 `python2` 后 AST 立刻不同，证明该判据不是恒真）—— `remediation-ast-equiv-*.txt`。整改后 26 门、ruff、hunk 范围、六处符号全部复跑通过。按协议 §1，本卡登记 **「整改未复审」**：整改后的注释文字未再送 Codex。

### 4-B 你来验

**无变化。**

这次动的两样东西，你在使用上都感觉不到：

1. 有一条给开发者看的「怎么修」提示。以前它写的那行字，如果你人在某些文件夹里照着敲，会敲不通（找错程序、找错文件）。现在不管你人在哪个文件夹，照着敲都能跑通。这条提示只在「东西对不上了」的时候才会冒出来，平时不出现。
2. 有一个旧办法，之前已经被想清楚不能用、删掉了。这次给它加了三道「别再把它加回来」的看门条。这三道看门条现在是**安静的**——不是因为它们不管用，是因为那个旧办法本来就不在了。将来谁要是又把它加回来，这三道条会立刻出声。

所以：你不需要点开任何页面、不需要做任何操作，也不会看到任何界面上的差别。

---

## 六 本卡未证明什么

1. **不证明任何历史行为被改变**。三门在当前实现下本来就绿；它们不检验、也不改变过去的任何行为。既有 `test_required_order_is_drift` 早已覆盖「排序裸 Schema required」这一面。
2. **不证明 CI 环境上 FIX 串可用**。无 `backend/.venv` 时回落 `python3` 的**串本身**已实测（`fallback-branch-probe-*.txt` 断言了它的形态），但那台机器上的 `python3` 是否装了项目依赖、能否成功导出 —— **未在 GitHub 实跑**。本机上的 `python3` 恰好就装不全（对照实验里报 `ModuleNotFoundError: structlog`）。
3. **不跑 `tests/contract` 目录级执行**。只做 `--collect-only`。schemathesis 那一面归 Y5-D。
4. **不证明 `openapi.json` 内容正确**。只证明它与 `app.openapi()` 归一化后一致。
5. **不证明三门能挡住任意排序实现**。已实测的是四种启发式；第四种下第三门保持通过 —— 组合覆盖成立，单门不成立。
6. **整改后的注释文字未经复审**（见 §五 失绑登记）。
7. **不证明含空格的仓库路径下 FIX 串真能跑通**。加了双引号使其在形态上成立（探针断言了三对引号），但本仓路径无空格，**未在含空格的路径上实跑**。

---

## 七 台账待登记条目

> 台账只由主 session 写（协议 §5）。以下为本卡请求登记的条目。

1. **X8（CARD-DEBT-openapi-sync-R1，`7ba8fc07`）残留 ⑥ 关闭** — FIX 提示两种 cwd 都不可照抄，已修并两 cwd 实测。
2. **X8 残留 ⑦ 关闭** — Codex LOW-3「23 门无 fixture 钉住 round-3 三原形」已补三门并做承重负控。
3. **勘误：FIX 串锚点 `:257` → `:254`**（台账 `:42` 写的 `:257` 是过期锚；本卡改动前实测在 `:254`）。
4. **门数 23 → 26**（`test_openapi_snapshot_drift.py`）。
5. **`backend/openapi.json` 处置 = 还原**（未提交时间戳再生版本，本卡两个 commit 均不含该文件）。
6. **本卡登记「整改未复审」** — 审后按 Codex MEDIUM-1 / LOW-1 只改注释措辞，AST 与审时版逐节点相同（带验伪锚），未再送 Codex。
7. **⚠️ 批级发现（建议通告全部在跑车道）** — 共享 `.git/config`（`git rev-parse --git-common-dir` = 主仓 `.git`，多 worktree 共用）在本卡作业期间被**并发写入**，`color.ui` / `color.diff` 一度为 `always`。任何形如 `git diff … | grep '^@@'` / `grep '^+'` / `grep '^[-+] '` 的车道判据在着色期间会**静默归零**，方向是**假绿**（「没有命中 = 通过」类判据尤其危险，例如卡文裁判 6 的 `grep -vc 'x-generated-at'` → 0）。建议：所有此类判据一律显式加 `--no-color` **标志**（不能只靠 `-c color.ui=false`，也不能依赖是否重定向），并配一条验伪锚证明管道此刻是活的。本卡已如此整改。
