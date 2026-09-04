# UAT · CARD-DEBT-hook-pyright（lefthook python-typecheck 假绿收口）

> 批次：[BATCH-2026-09-04-第十批 / CARD-DEBT-hook-pyright] · 车道 `card/x5-micro`（从 `1f249b33` 切）
> 改动面：`lefthook.yml` 单块（`python-typecheck`），+29/-2，**不装 pyright、不动 requirements/pyproject/pyrightconfig**
> 提交：本卡单 commit，未 push、未合并

---

## ⛔ 先读这段：现状比卡文写的更严重一层

卡文 `X5.md:12` 记的事实是「缺 pyright 时 hook 退出码恒 0 = 假绿」。本卡实测**负控**证明范围更大：

> **旧块即使 pyright 真的报出类型错误（rc=1），块退出码依然是 0。**

也就是说这不是「工具缺失时假绿」，而是 **`python-typecheck` 这道门从来就不会拦住任何东西**——装上 pyright 也一样放行。根因是 shell 块的退出码取自最后一条命令，而 `:88` 末行是必定成功的 `echo`。

第二层缺陷（卡文未记）：`127`（command not found）与 `1`（真有类型错误）被同一个 `-ne 0` 分支吞进同一句 `[Python] Type errors found!`——**门的失败原因分不清「没跑」和「跑了不过」**。本卡把两者彻底分开。

---

## 1. 🎯 一句话目标

让 `python-typecheck` 这道 pre-commit 门**不再说谎**：没装 pyright 就明说没跑（不冒充通过），装了就真跑、真拦。

## 2. 📖 你的视角

作为提交代码的人，我想知道 pre-commit 打出的 `✔️ python-typecheck` 到底代表「类型检查过了」还是「压根没检查」，**以便**不把一个从未运行过的门当成质量保证。

## 3. 🖥️ 交互流程（你的屏幕变化）

本机没装 pyright，所以你现在 `git commit` 会看到：

```
[Python] SKIP: pyright not installed (looked for backend/.venv/bin/pyright, then PATH).
[Python] SKIP: typecheck did NOT run -- this is NOT a pass. See pyrightconfig.json.
```

提交**照常放行**（rc=0，不阻断你的工作流），但屏幕上明写着「没跑，这不算通过」。
等哪天装了 pyright（另一张卡），同一块会变成真跑 + 有类型错误就**真的拦住 commit**。

## 4-A. 🤖 Claude 已代验

裁判命令（⚠️ 卡文写的 `--commands` 在 lefthook 2.1.6 下报 `flag provided but not defined: -commands`，实际单数 `--command`；另加 `--no-auto-install` 避免隐式改写 `.git/hooks`）：

```bash
cd .../card-x5-micro
git add backend/app/__init__.py          # 一个空白改动，跑完已还原
PATH=/usr/bin:/bin /opt/homebrew/bin/lefthook run pre-commit \
  --command python-typecheck --force --no-auto-install
```

| # | 项 | 结果 | 证据（实测输出） |
|---|---|---|---|
| A1 | **先红（现状）**：缺 pyright 跑该块 → 无 SKIP 字样、rc=0 | ✅ 已复现 | `sh: line 3: pyright: command not found` → `[Python] Type errors found!` → `Typecheck done (exit: 127)` → lefthook `✔️ python-typecheck`，`LEFTHOOK_RC=0` |
| A1' | **负控（本卡新增，比卡文事实更强）**：把 HEAD 旧块原文抽出、喂一个 **rc=1** 的 pyright stub | ✅ 假绿确认 | 旧块打印 `Typecheck done (exit: 1)` 但 `OLD_BLOCK_RC=0` —— **有真类型错误也放行** |
| A2 | **后绿**：缺 pyright → 输出显式 SKIP 行，rc=0，不冒充跑过 | ✅ | 两行 `[Python] SKIP: …` + `LEFTHOOK_RC=0`；输出里**不再出现** `Type errors found` |
| A3-P1 | pyright 存在（PATH）且 rc=0 → **真跑**且 staged_files 真传进去 | ✅ | `Running pyright type check (<stub>)…` + `STUB-PATH-PYRIGHT invoked with args: backend/app/__init__.py` + `LEFTHOOK_RC=0` |
| A3-P2 | pyright 存在且 rc=1 → **真红** | ✅ | `Typecheck done (exit: 1)` + lefthook `🥊 python-typecheck` + `exit status 1` + `LEFTHOOK_RC=1` |
| A3-P3 | 优先 `backend/.venv/bin/pyright`（venv stub rc=0 与 PATH stub rc=1 同时在场） | ✅ 选中 venv | `Running pyright type check (backend/.venv/bin/pyright)` + `STUB-VENV-PYRIGHT invoked` + `✔️`（未走 PATH 的 rc=1 stub） |
| A4 | 只改 `:75-88` 一块 | ✅ | `git diff --stat` = `lefthook.yml \| 31 ++…` 单文件 +29/-2；三个 hunk 头全落在 `@@ -75..-88` 区间；**HEAD 1-74 行**与工作区 1-74 行 `diff -q` 逐字节相同；**HEAD 89..EOF** 与工作区 116..EOF 逐字节相同（偏移 +27 = 29-2，自洽） |
| A4' | 同级块零改动 | ✅ | `spec-sync`/`ghost-files`/`python-lint` 行号 HEAD=WORK=20/40/60 未移动；`cypher-vault-filter-lint` 仅整体下移 103→130 |
| A5 | 不装 pyright、不动依赖声明 | ✅ | `which pyright` 空、`backend/.venv/bin/pyright` 不存在、requirements/pyproject 无 pyright（均为改动前后同状态）；`git status --short backend/requirements.txt backend/pyproject.toml pyrightconfig.json` = 空 |
| A6 | 探针零残留 | ✅ | 空白改动已 `git reset` + `git checkout HEAD --` 还原；venv stub 用 `mv` 移出车道（guard-hook 拦 `rm`）；终态 `git status --short` 仅 ` M lefthook.yml` |

**stub 说明（防「假证」）**：A3 的三条用的是**假 pyright**（`/bin/sh` 脚本，按需 `exit 0` / `exit 1`），因为本卡默认裁决 (i) = 不安装真 pyright。它们证明的是**块的接线**（找得到就调用、参数真传、rc 真透传、venv 优先），**不证明真 pyright 在本仓能跑通/仓库类型干净**——见「本卡未证明什么」第 1 条。

## 4-B. 👤 你来验

**无变化。** 本卡不改任何产品行为，你在 Obsidian / 复习页 / 后端 API 上看到的东西完全一样。唯一可见处是你自己 `git commit` 时终端多出的两行 SKIP 提示。

## 5. 🚦 验收结果

- 技术侧（4-A）：**10/10 全绿**（含 1 条比卡文更强的负控 A1'）。
- 完成条件 A1-A5：全部满足。
- Codex 审查：按卡文「三张微卡默认不送」——**未送审**。你要的话每卡 1 轮，只审本卡 diff（12 行有效改动）。

## 6. 📝 批注区

[!question]+ 你的批注写在这里（Cmd+Shift+A）

[!note]+ 为什么保留 `source backend/.venv/bin/activate` 那行
> 它在 HEAD 里就存在，本车道无 `backend/.venv` 所以从未生效。删掉是「顺手清理」，会让 diff 超出「只改这块的假绿逻辑」的最小面；保留则零行为差（新代码用显式路径找 binary，不依赖 activate 改 PATH）。默认保留。

## 7. 🔗 技术 spec 引用

- 卡文：`goal-cards/第十批-goals/X5.md` § A（完成条件 A1-A5、默认裁决 (i)）
- 实现：`lefthook.yml:75-115`（`python-typecheck` 块）
- 配置（未动）：`pyrightconfig.json`（`typeCheckingMode: basic`，include `backend/app`/`src`/`tests`）

---

## 待你裁决（本卡默认值先行，均可改）

| # | 事项 | 本卡采取的默认 | 备选 |
|---|---|---|---|
| ① | 装不装 pyright | **不装**（卡文默认裁决 (i)）——本卡只让门停止说谎 | 开一张独立卡装 pyright 并把它写进 `requirements-dev`，届时 A3 的真红才对真代码生效 |
| ② | 缺工具时是 SKIP(rc=0) 还是硬红(rc=1) | **SKIP + rc=0**：工具本就没声明成依赖，硬红等于让所有人无法提交 | 硬红逼装工具（须与 ① 同批做，否则全员阻断） |
| ③ | 装上 pyright 后大概率一片红（存量类型债） | 本卡不预判——`exit $PYRIGHT_EXIT` 一旦装工具立刻生效 | ① 那张卡里同时决定：先 `basic` 全量红、还是只对 staged 文件的新增行红 |

---

## 本卡未证明什么（必填段，如实）

1. **没跑过真 pyright**：A3 三条全部用 stub。真 pyright 装上后本仓有多少存量类型错误、`pyrightconfig.json` 的 `pythonVersion: 3.14` / `venvPath` 在本机是否解析得动——**一次都没验过**。
2. **没验 venv 里装了真 pyright 的路径**：A3-P3 造的是 `backend/.venv/bin/pyright` 假文件（跑完已 `mv` 移走），车道里从来没有过真 venv；`source activate` 那行至今**从未执行过一次**。
3. **只验了 `--command python-typecheck` 单块，没跑整个 pre-commit**：`spec-sync` 会真改 `openapi.json` 并 `git add`（卡文 :14 明令避开），所以「本块改动不影响其它块」是靠**字节对比 + 行号未移动**推的，不是靠整钩子实跑。
4. **没验真实 `git commit` 路径**：全程用 `lefthook run … --force`。真 commit 时 lefthook 由 `.git/hooks/pre-commit` 触发（本次全程 `--no-auto-install`，未验证该钩子文件当前是否已安装、内容是否指向本配置）。
5. **没验并行块之间的干扰**：`pre-commit: parallel: true`，本卡单块跑，未验并行下多块同时 `git add`（记忆里有 lefthook 2.1.6 `parallel:true` + 多命令 `git add` 撞 `index.lock` 的先例）。
6. **`{staged_files}` 为空时的行为未验**：本次始终有 1 个 staged 文件。若 glob 匹配为空，lefthook 通常跳过该命令，但本卡没做这条断言。

## 移交登记

**台账待登记条目**（本卡按纪律**不动** `未合卡追踪台账.md`，条目列此供主 session 登记）：

1. **CARD-DEBT-hook-pyright 完成，未 push 未合并**，车道 `card/x5-micro`，合并序要求：**必须早于 X8（openapi 卡）**——X8 合入后 `spec-sync-flat` 会在直跑 lefthook 时真改 index，本卡裁判命令届时失效。
2. **新债：pyright 未安装**。本卡把「假绿」换成「诚实 SKIP」，但 `python-typecheck` 这道门**在本机仍然一次都没真跑过**。建议独立卡：装 pyright + 写进依赖声明 + 决定存量类型债口径（见待裁决 ①③）。
3. **事实更正**：卡文 `X5.md:12` 与台账 `:34` 的表述都可再收紧一档——旧块不只是「缺工具时假绿」，是**任何 pyright 非零退出都放行**（本卡负控 A1' 实证）。
4. **裁判命令勘误**：`lefthook 2.1.6` 用 `--command`（单数），卡文/手册里的 `--commands` 会直接报错退出。
