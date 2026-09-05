# Codex 复核 — CARD-TOOL-lint-glob [BATCH-2026-09-05-第十一批]

你是一名严格的代码复核者。请只做**只读**审查，不要修改任何文件。

## 仓库与审查面

工作树根目录：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool`

基线 `304f03ca`，本卡两个 commit：

- `1ffd6d36` — `lefthook.yml` 的 `python-lint` glob 扩面 + 根 `ruff.toml` 两个配置口径 + 新增 `mutant-residue-scan` 块
- `b20fe550` — `ruff format` 落盘 86 个 `scripts/*.py`（纯格式化，无手改）

审查面 = `git diff 304f03ca b20fe550`。`b20fe550` 是机器生成的格式化输出，请把注意力放在 `1ffd6d36`（`lefthook.yml` + `ruff.toml`）以及 `b20fe550` 是否真的只是格式化。

## 本卡自称做到了什么（请逐条判断真伪，不要采信我的措辞）

1. **glob 改写正确**：`{backend,src}/**/*.py` → `{backend,src,scripts}/*.py`。依据是 lefthook 2.1.6 的 glob 引擎里单 `*` 跨目录层级、`**` 反而要求至少跨一级，因此 `{backend,src,scripts}/**/*.py` 会漏掉 `scripts/` 一级的 49 个文件和 `backend/` 一级的 2 个文件（`mutmut_config.py` / `start_server.py`）。我在本机跑了 3 个 glob 变体 × 9 个真实 tracked 文件的探针，判据绑定的是 `python-lint` 的 run 体自己 echo 的 `Running ruff lint` 这行，而不是退出码。
   请判断：这个判据是否足够；是否存在这套 glob 会**过宽**匹配到不该匹配的文件的情形；`src/` 分支保留是否有害。

2. **配置口径**：根 `ruff.toml` 新增 `line-length = 120` 与 `target-version = "py312"`，`[lint] select = []` 保持不动。
   理由：`ruff check --show-settings scripts/send_bark.py` 实测 Settings path 落在根 `ruff.toml`，行宽此前是 ruff 缺省的 88，而 `pyproject.toml [tool.ruff]` 与 `backend/ruff.toml` 都声明 120；`target-version` 缺省 py39 会把合法的 PEP 701 f-string 报成 `invalid-syntax`。
   请判断：这两项改动的影响半径是否被我低估（例如是否影响到 `backend/` 或其它未被 lint 门覆盖但会被人手动 `ruff` 的目录）；`py312` 与 `backend/ruff.toml` 里仍写着的 `py39` 并存是否会造成后续混乱；把行宽从 88 改到 120 是否属于本卡不该做的范围扩张。

3. **`mutant-residue-scan` 门**：位于 `pre-commit.commands` 段末，**没有 glob 键**，扫 `git diff --cached -U0 --diff-filter=AM` 的新增行，命中一个大写标记串即 `exit 1`。排除名单硬编码为两个变异 harness 文件与 `_bmad-output/**`。标记串在 shell 里由两段字符串拼接得到，目的是让 `lefthook.yml` 自身不含该字面量，否则每次编辑该块都会被自己拦下。
   请重点审查这个 shell + awk 实现的边界情况，例如：
   - 文件名含空格 / 非 ASCII / 被 git 引号转义时的行为；
   - `awk` 从 `-U0` 的 hunk 头推算新文件行号的算法是否正确（含 `@@ -a +b @@` 无逗号形态、多 hunk、纯删除 hunk）；
   - 管道进 `while` 造成的子 shell 语义、临时文件命名、以及命令失败时是否可能静默放行；
   - 排除名单用 `case` 前缀匹配是否可被路径写法差异影响；
   - 这个门在 `parallel: false` 之外的配置下是否仍安全。

4. **诚实性**：块内注释声明「本门抓不到不带标记的残留」，并把唯一可靠锚点指向全文件 sha 基线。`python-lint` 块的注释声明「对 `scripts/` 而言本门只拦 `invalid-syntax` 与格式漂移，不拦未定义名一类的规则违规」。
   请判断：仓库里现在写下的任何声明，是否有**比实际证据更宽**的地方；注释里引用的事实（91 / 49 / 845 / 0 等数字，以及那处 F821）是否与仓库现状一致。

5. **`b20fe550` 是否真的只是格式化**：请抽查若干文件，判断是否混入了任何非格式化的改动。

## 我明确知道自己没有证明的事

- 没有跑 CI，只在本机 macOS + lefthook 2.1.6 + ruff 0.15.9 上验证。
- 没有验证 `scripts/` 下任何脚本格式化后的**运行时**行为，只对全部 91 个文件做了 `py_compile` 前后对账（结果逐行相同：90 通过 / 1 失败，失败的恒为 `scripts/spec-tools/api-reality-dashboard.py`）。
- `scripts/spec-tools/api-reality-dashboard.py` 是真语法错误（Python 3.14 下 `py_compile` 失败），因此没有被格式化，也没有被修复，已登记为待办。
- 没有在本卡内运行任何变异 harness。

## 输出要求

给出一份结构化清单：每条写明 **严重度（BLOCKER / HIGH / MEDIUM / LOW）**、**位置（文件:行）**、**问题**、**判断依据**、**建议处置**。
如果某条你无法从仓库现状直接判定，请标注为「需要额外证据」并写清楚需要什么证据，不要给出猜测性的结论。
最后请单独回答一句：这两个 commit 里有没有**数据丢失 / 安全 / 越权写入**级别的问题。
