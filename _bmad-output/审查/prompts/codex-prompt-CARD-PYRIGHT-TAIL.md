# 独立审查请求 — CARD-PYRIGHT-TAIL（第十四批 / 车道 T8-F）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`（分支 `card/t8-tools`）。

本卡做两件事，**不改任何运行行为**：
1. 把 U1/U2 两条 pyright 清债车道清不掉的存量逐条写成 census 表（登记，不修）；
2. 只改「注释 / 死配置 / 冗余 ignore」三类**零行为**改动。

硬门：`pyright app` 在基准 `f493a4e1` 上是 `0 errors, 81 warnings, 0 informations`，本卡必须保持 **0 errors**（实测改后 `0 errors, 80 warnings`，warnings 少 1 = 清掉的那条冗余 ignore）。

审查绑定 SHA：`bcd487db`（`BASE_F` = `f493a4e170a88b5eb2c4af05b275055d005adfe9`）。

**最小读取面（只读这些，不要扩散到全仓）**：
- `git diff f493a4e170a88b5eb2c4af05b275055d005adfe9 bcd487db -- . ':(exclude)_bmad-output'`
- `_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md`
- `_bmad-output/审查/evidence-pyright-tail/pyright-app-before-*.txt` 与 `pyright-app-after-*.txt`
- `backend/app/dependencies.py:1020-1040`
- `pyrightconfig.json:1-60`

## 二 作者自述，请独立核对

① 删 `backend/app/dependencies.py` 原 `:1035` 行尾的 `# pyright: ignore[reportArgumentType]` 之前，该行**确已被 pyright 标为** `reportUnnecessaryTypeIgnoreComment`（即该 ignore 已不承重，不是把一条真诊断压掉）；删后 `pyright app` 的 errors 仍为 0、warnings 由 81 变 80。证据在 `evidence-pyright-tail/red-before-*.txt`（改前该诊断计数 1，原文含 `:1035:63`）与 `pyright-dependencies-after-*.txt`（改后计数 0）。

② 移除 `pyrightconfig.json` 的 `include` 里的 `src` 条目对 pyright 的分析文件集**无影响**，因为 `git ls-files src` = 0（全仓无该目录），该 include 项匹配 0 个文件。

③ 三处注释改动**没有任何代码行变化**：`git diff -U0` 里非注释的 `+`/`-` 行**恰 2 行**，且是同一处 `canvas_base_path=canvas_base_path,`（`-` 带行尾 ignore、`+` 不带，代码本体逐字相同）。其余 `+`/`-` 全是 `#` 或 `//` 注释行。

④ census 表里每条的处置（本批改 / 本批其他卡 / 第十五批立卡 / 只登记）与 §〇 事实一致，且每条都给了「生产调用方」「测试覆盖」两列的实测数字。

⑤ 本卡刻意让 `canvas_service.py` 与 `review_service.py` **逐行等量替换**（`numstat` 为 `1 1` 与 `3 3`），目的是不让本卡自己制造新的行号漂移——因为这两个文件的行号被别处注释引用着（例如 `question_generator.py:208` 引用 `canvas_service.py` 的行号，而该文件不在本卡可改范围）。请核对这个「等量替换」的说法是否属实。

## 三 请按重要性排序回答的问题

⓪ **有没有哪一条被本卡判为「只登记 / 第十五批立卡」的 TAIL 项，其实是本批就应该修的活路径漏网？** 特别关注 census 第四节里标注为「活路径」的 T-new-7，以及被判「双零」的那几条——判定依据是否站得住。

① 删掉那条冗余 ignore 之后，**有没有门未覆盖的路径**会让 pyright 在别处新冒 error？本卡的硬门只跑了 `app` 全量，**没有**跑 `backend/tests` 与仓根 `tests/`（`pyrightconfig.json` 的 `include` 里有 `tests`）。请指出这个覆盖缺口可能藏着什么。

② 改后的三处注释措辞**是否仍有超出证据的断言**？本卡的收敛口径是：凡基于 grep + AST 得出的「没有调用方」，一律只能写「未发现直接生产调用，动态可达性未证」，不得写「零调用方 / 零曝光」。请检查改后的文字有没有在别的地方犯同型错误。

③ census 判「死路径」用的**对照输入**（「生产调用方 = 0」与「测试覆盖 = 0」两列）是否充分？有没有别名取用、回调注册、字符串反射、路由注入这类**未被这两列拦下的输入**，会让某条被判「死」的项其实是活的？

④ census 第六节自报了两条本卡新发现但**不改**的项（T-new-9 同型措辞、T-new-10 注释行号引用成批漂移）。这两条「登记不改」的理由是否成立，还是其中某条本就该在本卡范围内处理？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- 级别
- `file:line`
- 一句话说明问题
- 一句话说明如何独立确认（读哪一段、比对什么）

没有问题的级别请明写「无」。请在开头给出四级各自的计数。

## 五 边界

- **只读**。不要修改任何文件，不要连数据库，不要运行 pyright / pytest / ruff。
- 不要评价被判「第十五批立卡」的那些行为变化项**本身该怎么修**——那不在本卡范围，本卡只负责登记得对不对。
- 不要扩散到最小读取面之外的文件。
