# 独立复核请求 — CARD-G3-7-R2 round-3（r2 整改核验 · 绑定最终 HEAD）

你是独立复核者。请**只读**，不修改任何文件，不连数据库，不运行测试或脚本。
你的 round-2 意见（4 MEDIUM / 2 LOW，0 BLOCKER / 0 HIGH）作者已全部处置；本轮请**独立核验处置是否成立**。

---

## 一 背景 + 最小读取面（写死，请只读这些）

**仓库树根**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery`

round-2 审的是 `65e18d04`。之后有一个整改 commit（**本轮绑定 HEAD，请自行 `git rev-parse HEAD` 核对并写进正文首句**）。

**请读**：

1. 整改 diff：`git diff 65e18d04 HEAD -- . ':(exclude)_bmad-output'`
2. 你 round-2 原文：`_bmad-output/审查/codex-review-CARD-G3-7-R2-r2.md`
3. HEAD 版 `backend/tests/unit/test_mastery_fsrs_projection_boundary.py` **全文**（MEDIUM-1/2 与 LOW-6 的整改都在这）
4. HEAD 版 census：`_bmad-output/审查/evidence-g37r2/census-20260908T073936.md`（MEDIUM-3 / LOW-5 的整改：§0.3 原句已删、§0.5 加第三步仓外扫描、§七.7 补目录边界）
5. HEAD 版 `docs/fsrs-truth-source-d0-revision.md` `:65-:70`（MEDIUM-4：措辞收窄）
6. 验收单 `_bmad-output/验收单/UAT-CARD-G3-7-R2-2026-09-08.md` §10（未证明清单更新）

## 二 六条处置的作者自述（逐条独立核验，勿采信）

1. **MEDIUM-1（io.open 参数错位）**：`_open_is_write` 改为三分——内建 `open`（func 是 Name）mode=args[1]；模块函数 `io.open` / `builtins.open`（Attribute 且接收者是 io/builtins/os 模块名）mode 仍是 args[1]；绑定方法 `Path(p).open(mode)`（Attribute 且接收者是表达式）mode=args[0]。罕见形态按写处理。
2. **MEDIUM-2（档间衔接）**：回调式扫描扩到两档（第二档需 `_receiver_is_filesystem`）；新增 `_imported_fs_writers` 用 `ast.ImportFrom` 跟踪 `from os import replace` 一类**直接导入**（作者承认 r2 把它错归为「别名盲区」——直接导入 AST 完全可见）；`file_text.replace(...)` 变量名含提示片段的误拦与 `shutil.copyfileobj(BytesIO, BytesIO)` 误报**登记为已知从严面**（写在 `_find_write_calls` docstring，不修——fail-closed 方向）。矩阵扩到 **21 条**（加 io.open 写/读、builtins.open、二档回调、from-import 裸名）。
3. **MEDIUM-3（面④目录覆盖）**：census §0.5 加第三步——同六个方法名 grep `backend/lib scripts canvas-vault/.claude frontend` 全 0 命中，带正控（同目录 `def` 大量命中）；§七.7 补「仓外不在任何一步覆盖内」。
4. **MEDIUM-4（历史断言过宽）**：d0 与验收单的「从未一致」改为「未见一致的证据」并写明三条实测各自的限定（生产代码 / 单文件 / 无分桶），「从未在任何地方实现过」明确标为超出证据的推断、按边界登记。git log 命令路径补全为 `backend/app/services/review_service.py`。
5. **LOW-5（矛盾原句）**：census §0.3 的「N 恒等于 0」原句已删，更正注改为「撤回说明」。
6. **LOW-6（过期引用）**：`BANNED_WRITE_CALLS` 引用改为新常量名；矩阵注释「前四条全错」改为如实分轮描述（r1 版错在绑定 open 两行、r2 整改版回退在 io.open 三行、内建 open 两行始终对）。

## 三 按重要性排序的问题

1. MEDIUM-1/2 的整改是**第三轮改写**——越是后改的越没人看过。三分逻辑与 21 条矩阵有没有新的错向？特别注意：`_imported_fs_writers` 对 `node.module.split('.')[0]` 的处理（`from os.path import ...`）、asname 的处理。
2. 登记不修的两处（变量名误拦 / copyfileobj 误报）——「fail-closed 方向、逼人看一眼」的理由成立吗，还是应该真修？
3. MEDIUM-3 的第三步只扫了四个目录——定义里的「仓内非测试非文档代码」还有没有第四步没覆盖的目录？
4. 综合本轮 HEAD：还有没有 BLOCKER / HIGH？若没有，请明确写「本轮 BLOCKER=0、HIGH=0」。

## 四 输出格式

- **BLOCKER / HIGH / MEDIUM / LOW**，每条 `file:line` + 一句话结论 + 证据。
- 单列 **「已核实成立的处置」**（逐条对应你 round-2 的意见编号）。
- 信息不足明说「未核实」。

## 五 边界

- 只读；不连库；不跑测试/脚本；不评 G3-5 键化（U9-C 面）；不评 pyright 存量（U1/U2 面）；不评 `test_mastery_fusion` 既有红（U11-C 面）。
- 不要求也不需要任何攻击性内容；本轮只针对读取面内整改的正确性与诚实性。
