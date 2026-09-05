# Codex 复核 — CARD-TOOL-pyright [BATCH-2026-09-05-第十一批]

你是一名严格的代码复核者。请只做**只读**审查，不要修改任何文件。

## 仓库与审查面

工作树根目录：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool`

审查面 = `git diff 41470106 d21b0bc4`，共 4 个文件：`pyproject.toml`、`pyrightconfig.json`、
`requirements.txt`、`uv.lock`。**`lefthook.yml` 本卡零字节改动**（上一张卡 CARD-TOOL-lint-glob
改过它，那部分不在本次审查面内）。

背景：上一张卡 X5-A 把 `lefthook.yml` 的 `python-typecheck` 块从"缺工具也报 ✔"改成
"缺工具就明说 SKIP 且不冒充通过"。但本机既无 pyright 也无 mypy，于是该块 100% 走 SKIP，
门名义存在、实际零覆盖。本卡把工具装上，让那个块自动走真跑分支。

## 本卡自称做到了什么（请逐条判断真伪，不要采信我的措辞）

1. **工具二选一（pyright 而非 mypy）**：依据是 pyright 有配置（根 `pyrightconfig.json`）
   且有活的调用方（`lefthook.yml` 的 `python-typecheck`），而 mypy 全仓零配置零调用方、
   只剩 `requirements.txt` 两行声明。我把那两行改成了注释而不是删除。
   另外我断言：根 `requirements.txt` **没有任何安装方**（CI 里两处
   `pip install -r requirements.txt` 前面都有 `cd backend`）。
   请判断：这两个断言是否成立；把声明改注释而非删除是否留下了新的歧义。

2. **声明落点选在根 `pyproject.toml` 的 `[project.optional-dependencies].dev`**：
   依据是 `backend/requirements.txt` 文件头自己写的单一权威规则
   （"本文件管 backend 生产依赖 / pyproject.toml 管 dev extras"）。
   请判断：这个落点是否真的能让 pyright 到达它需要到达的地方；
   `uv.lock` 的更新是否只是增量（我声称 +24 行、只有 pyright 与 nodeenv、零删除）；
   注意 `backend/requirements.txt` 文件头写的是 `[tool.uv]` 而实际用的是
   `[project.optional-dependencies]`，这处文档漂移我没有修，请判断是否应该修。

3. **`pyrightconfig.json` 的 `pythonVersion` 由 3.14 改为 3.11**。我的实测（同一 include，
   只改这一项）：3.9=656 / 3.10=605 / 3.11=592 / 3.12=592 / 3.14=592 errors；
   3.9 相比 3.11 多出的 64 条里 51 条是 `X | Y` 联合类型语法（需 3.10+）。
   我据此断言"代码真实下限是 3.11"，并断言根 `pyproject.toml` 的
   `requires-python = ">=3.9"` 与 `backend/ruff.toml` 的 `target-version = "py39"` 都已失真。
   请判断：这个推理是否成立；把 pythonVersion 降到 3.11 是否有我没想到的副作用；
   我在 JSON 配置里加了 `//` 注释（pyright 用 JSONC 解析，我实测它接受），
   请判断这是否会影响其它可能读这个文件的消费方。

4. **存量债只测量不整改**：`type: ignore` 增量 0（仍 22 处），`typeCheckingMode` 未动，
   `reportMissingImports` 未关。全量基线（304 个文件）= 592 errors / 86 warnings。
   请核对这些数字，并判断我给出的 top-10 规则码分布是否与仓库现状一致。

5. **我自己报出的一个后果**（请判断我是否低估或高估）：卡文假设"pre-commit 只对 staged
   文件跑，所以存量债不阻断新代码"。我实测脏文件率是 `backend/app` 42%（111/263）、
   `backend/tests` 50%（249/493），因此装上之后约一半的 Python 改动会在 commit 时被拦。
   而且 `backend/tests`（1396 errors）**在 hook 的 glob 内却不在 `pyrightconfig.json`
   的 include 内**，所以 592 这个基线并不封顶这道门能报出的东西。
   请判断：这个不对称是否真实存在；我算的脏文件率口径是否正确；
   我提出的缓解选项（`--skipunannotated` 实测把 backend/tests 从 1396 降到 343）
   是否会削弱这道门本该承担的职责。

## 我明确知道自己没有证明的事

- 没有证明那 263 个 `backend/app` 文件的类型是正确的——只跑了检查器，没有逐条判断
  592 条诊断里哪些是真缺陷、哪些是检查器的误报。
- 没有跑 CI，也没有把 pyright 接进任何 workflow（没有任何 workflow 安装
  `[project.optional-dependencies].dev`，所以 pyright 目前只在本地 pre-commit 生效）。
- 本车道的 `backend/.venv` 是指向另一个工作树的 symlink，安装会影响所有共用它的车道；
  我做了装前装后对账（仅新增 nodeenv 与 pyright 两个包、4 个 bin，既有 227 个包未动），
  但没有验证其它车道当时是否正在使用该 venv。
- `python-typecheck` 的 glob 是 `{backend,src}/**/*.py`，它漏掉 `backend/` 一级的
  2 个文件（`start_server.py` / `mutmut_config.py`）——我实测证实了这一点但没有修
  （卡文禁止本卡改那个块）。

## 输出要求

给出一份结构化清单：每条写明 **严重度（BLOCKER / HIGH / MEDIUM / LOW）**、**位置（文件:行）**、
**问题**、**判断依据**、**建议处置**。
如果某条你无法从仓库现状直接判定，请标注为「需要额外证据」并写清楚需要什么证据，
不要给出猜测性的结论。
最后请单独回答一句：这次改动里有没有**数据丢失 / 安全 / 越权写入**级别的问题。
