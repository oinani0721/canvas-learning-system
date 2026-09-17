# 独立复核请求 — CARD-TOOLCHAIN-UNIFY（BATCH-2026-09-11-第十四批 · 车道 T8 第 5/7 卡）

审查绑定：`99e15a4e08c4749500a59584c12edbaafcff0f3e`（本卡唯一 commit）
前提 commit：`7aacbc87cc0241130ddcc55c40892c4e95d8dbbe`（前一卡 T8-D 末 commit）
树：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`（分支 `card/t8-tools`）

---

## ① 背景

本仓的 git 提交门由 lefthook 驱动，但 lefthook 的版本在三个地方不一致：

- `package.json` devDependencies 声明的是**范围** `^1.6.0`；
- `package-lock.json` 的 root `packages[""].devDependencies` 也写 `^1.6.0`，而它的 `node_modules/lefthook` 条目 `resolved` 到的是 **1.13.6**；
- 本机 PATH 上的 brew 二进制是 **2.1.6**。

补充事实：`node_modules/` **未安装**（`node_modules/.bin/lefthook` 与 `node_modules/lefthook/package.json` 都不存在），所以本机没有可跑的 npm 侧二进制；共享 git hook `pre-commit` 的 `call_lefthook()` 依次尝试 `$LEFTHOOK_BIN` → PATH 上的 `lefthook` → `node_modules/...`，因此**实际执行者恒为 brew 2.1.6**。

第二条背景：仓根 `ruff.toml` 的 `[lint] select = []`。ruff 的规则是「同目录 `ruff.toml` 优先于 `pyproject.toml`，不合并」，所以这一份管的是 `backend/` 之外的全部 tracked `.py`（含 `scripts/`）。`select = []` 意味着该面上 **lint 规则为空集**，只剩解析器层的 `invalid-syntax`。而 `backend/ruff.toml` 长期开着必错级四条 `["E9", "F63", "F7", "F82"]`。这条缺口在台账 Z7-A 行已登记（「`scripts/` lint 规则集仍空…负控①a 未定义名放行 = 只是语法+格式门」）。

本卡的约束（由排批的主 session 定死，不可扩）：**install-free** —— 不跑 `npm install`、不升 brew、不改 `.git/hooks`、不装任何包、不改任何 `.py`。地盘恰三个文件：`ruff.toml`、`package.json`、`package-lock.json`。

### 最小读取面（请只读这些，不要遍历全仓）

1. `git diff 7aacbc87cc0241130ddcc55c40892c4e95d8dbbe 99e15a4e08c4749500a59584c12edbaafcff0f3e -- . ':(exclude)_bmad-output'` —— 本卡三文件 diff 全文
2. HEAD 上的 `ruff.toml` 全文（39→40 行）
3. HEAD 上的 `backend/ruff.toml` 全文（对照口径来源）
4. `grep -nF lefthook package.json` 与 `grep -nF lefthook package-lock.json`（lefthook 相关段；lock 的 `node_modules/lefthook` 条目在 `:1489-1511`）
5. `lefthook.yml` 的 `python-lint` 作业（`:117-131`，含 `glob` 与 `run` 两段）
6. `$(git rev-parse --git-common-dir)/hooks/pre-commit` 里的 `call_lefthook()` 函数体
7. 本卡 evidence（均在 `_bmad-output/审查/evidence-toolchain-unify/`）：
   - `ruff-scripts-before-20260917T124705.txt`（改前）
   - `ruff-scripts-probe-20260917T124705.txt`（改前的对照输入：命令行显式 `--select E9,F63,F7,F82`）
   - `ruff-scripts-after-20260917T124753.txt`（改后）
   - `ruff-before-after-diff-20260917T124809.txt`（两者逐条对照）
   - `rootsurface-before-after-v2-20260917T125857.txt`（root 治理面 288 文件的改前/改后普查；含对第一版判据缺陷的更正说明）
   - `ruff-array-and-rootsurface-20260917T125826.txt` 与 `rootsurface-before-after-20260917T125840.txt`（两份**有缺陷的**早期判据，已被上一条取代，保留以供核对更正是否成立）
   - `territory-gate-20260917T130018.txt`（地盘门）、`unit-diff-20260917T125806.txt`（tests/unit 对照基线）
   - `version-grep-before-20260917T124731.txt` / `version-grep-after-20260917T124753.txt`（版本判据的改前命中 / 改后零命中）
8. 台账（只读，不要修改）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md` 的 `Z7-A` 行（`:53`）与 `X8` 登记行（`:22` 末尾「lefthook 三版本统一」）

---

## ② 作者自述，请独立核对（不要采信下列任何一句，请自己看代码与 evidence）

1. **npm 侧内部自洽**：改后 `package.json:19` 与 `package-lock.json:14` 都是 exact `"1.13.6"`，与 lock 早已存在的 `node_modules/lefthook.version` / `.resolved`（`:1490` / `:1491`）一致；`integrity`、`resolved` URL、10 个 `optionalDependencies` 平台包**一个字节都没动**。
2. **runner-of-record = brew 2.1.6**：依据是 `call_lefthook()` 的优先级顺序 + `node_modules` 缺席这两条实测，而不是偏好。本卡提交时 lefthook 自己打印的横幅是 `lefthook v2.1.6`（见提交输出）。
3. **口径逐字同**：`ruff.toml` 新的 `select` 行与 `backend/ruff.toml:10` 逐字相同；`line-length = 120` 未动；**没有**新增 `target-version`（该文件 `:23-35` 的注释解释了为什么刻意不写）；没有启用任何风格规则。
4. **ruff 改前/改后的唯一语义差 = F821 由不报变报**：`scripts/` 面 `Found 24 errors`（统计行只有 `invalid-syntax`）→ `Found 25 errors`（`24 invalid-syntax` + `1 F821`）。`invalid-syntax` 两边都是 24（它属解析器层，不受 `select` 支配）。作者如实声明：两份 `--statistics` 输出的 diff 里，`invalid-syntax` 那行也有**列对齐空白**的变化（出现规则码列后 ruff 重排对齐），因此另补了按内容取值的计数断言。
5. **root 治理面的新增命中恰 2 条**：对 288 个非 `backend/` 的 tracked `.py` 做改前/改后对照（改前用内联 `--config 'lint.select=[]'`，使仓内配置发现与 `target-version` 推断保持不变），`invalid-syntax` 两侧都是 131，新增恰 `2 F821`、零 `E9`/`F63`/`F7`：`scripts/validate-source-citations.py:392`（`technology`）与 `_bmad-output/审查/evidence-w4-5/cases/case-d2.py:6`（`app`）。
6. **作者自曝的两处判据缺陷（已更正并留档）**：(i) 第一版普查用 `git ls-files` 取文件名，中文路径被 C-quoting 后 ruff 打不开，产生 129 条 `E902 io-error` 假命中 —— 改 `git -c core.quotepath=false ls-files`；(ii) 第二版把「改前」配置写在会话临时目录再 `--config` 指过去，导致 ruff 丢失同目录 `pyproject.toml` 的 `requires-python` 推断、`invalid-syntax` 从 131 变 127，两侧不可比 —— 改内联覆写。**请独立判断这两处更正本身是否成立，以及是否还有第三个同类问题。**
7. **本卡对 commit 门的影响**：本卡自己 staged 的三个文件都不是 `.py`，`python-lint` 的 glob `{backend,src,scripts}/*.py` 不命中，故本次提交不经过 ruff；但**将来**暂存 `scripts/validate-source-citations.py` 的提交会被新 `select` 拦下。作者顺带实测：`src/*.py` 的 tracked 计数为 **0**（glob 的 `src/` 段目前覆盖空集），`scripts/*.py` 顶层 94 个（`scripts/spec-tools/` 子目录不在单星 glob 内）。
8. **零副作用声明**：`tests/unit` 目录级（`--ignore tests/unit/test_deploy_vault_sh.py`，与 `08100483` 基线跑法逐字一致）改后 64 条红与基线**逐条相同**（0 新增、0 消失）。地盘门显示 `$PREV..HEAD` 在排除 `_bmad-output` 后恰三文件，`lefthook.yml` / `pyrightconfig.json` / `backend/ruff.toml` / 任何 `.py` / `backend/app` 改动数皆为 0。

---

## ③ 请回答的问题（按重要性排序）

**⓪** 「brew(2.1.6) ↔ npm(1.13.6) 跨 runner 未统一」被本卡登记为协议 §2.3 授权后续、本批不做。在 **install-free** 前提下（不跑 `npm install`、不升 brew、不改 `.git/hooks`、不装包），是否存在某条作者遗漏的路径能让两者版本一致？若确实不存在，请明确确认这一点。

**①** `package.json` 锁 exact `1.13.6` 而本机实际跑 brew `2.1.6`：在任何真实路径上（例如 fresh clone + `npm ci` 且无 brew 的 CI 环境 / 本机 brew 在 PATH 的开发者环境）是否造成行为分叉？该分叉是否已被「runner-of-record = brew 2.1.6」这个判定与本卡的版本判据说清楚？特别请看 `package.json:7` 的 `"prepare": "lefthook install"` —— 它在 `npm ci` 时会跑，此时 `node_modules/.bin` 在 PATH 前部，装出的 hook 将由 1.13.6 生成，这一点作者只在文档里登记、没有实测。

**②** root `ruff.toml` 加 `select` 对 `scripts/` 以外的 root 治理面（`tests/`、`canvas-vault/`、`_bmad-output/`、`.gdr/`、`docs/`、`tools/`、`_bmad-archive/`）是否产生了作者未登记的新必错级命中？请独立核 `rootsurface-before-after-v2-*.txt` 的两条 F821 是否穷尽，以及该普查的文件集（288）是否就是 root `ruff.toml` 的真实治理面。

**③** 把新 `select` 揭出的 `scripts/validate-source-citations.py:392` F821 登记不修（理由：`scripts/*.py` 不在本卡地盘，是 Z7-A 存量），是否恰当？还是应当扩地盘同批修？请给判断与理由。

**④** 「本卡 staged 的三个非 `.py` 文件不命中 `python-lint` 的 glob，因此本次提交不被新 `select` 影响」这个推断是否成立？作者是靠读 glob 推断的，没有真跑 hook 做对照。

**⑤** 只改 `package-lock.json` 的声明 range 而不跑 `npm install`，是否会让 `npm ci` 报 lock 与 manifest 不一致（或产生别的一致性问题）？lock 的 `lockfileVersion` 是 3。

**⑥** `ruff.toml` 文件头 `:2` 仍写着 `# NOTE: Lint rules temporarily disabled due to 2000+ pre-existing violations.`，而本卡已启用四条必错级规则。作者按卡文对 `ruff.toml` 的允许面（「只改 `[lint] select` + 上方一行注释」）**未动** `:2`，只在 `select` 上方新增一行注释说明启用范围。请判断这处文案是否构成名实不符，以及按什么级别处理合适。

---

## ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给：
- 一句话结论
- `file:line`
- 一句话说明在什么输入或什么路径下会显形

没有问题的级别请显式写「无」。

---

## ⑤ 边界

- **只读**：不要修改任何文件，不要跑 `npm install` / `npm ci` / 任何包管理器写操作，不要跑 git hook，不要连数据库（7691 / 7687 / 7692），不要写 live vault。
- **不要**评估「brew ↔ npm 跨 runner 统一」的执行方案细节 —— 那是协议 §2.3 需批级授权的后续动作，本卡只交 install-free 子集；问题 ⓪ 只问「install-free 下是否还有别的路径」。
- 措辞上，请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」来描述问题显形条件。
