# UAT — CARD-TOOL-pyright「装 pyright + 依赖声明归口 + 存量类型债一次性口径」

> 批次 `[BATCH-2026-09-05-第十一批 / CARD-TOOL-pyright]`
> 车道 `card/z7-tool`（Z7-A 的 4 个 commit 在其下）· 卡文
> `_bmad-output/implementation-artifacts/goal-cards/第十一批-goals/Z7-B.md`
> commit：`d21b0bc4`（配置与声明）+ `a01b1733`（Codex round-1 整改）· 基线 `41470106`
> 环境：pyright **1.1.411** / `backend/.venv` = Python **3.14.4** / lefthook 2.1.6
> **`lefthook.yml` 本卡零字节改动**——X5-A 写的分支逻辑本来就是「找得到就真跑」。

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：**

1. **提交前的类型检查，从"一直没开"变成"真的在跑"。** 之前那道检查会老老实实说
   "我没跑"（上一张卡改的），但它没跑的原因是**检查工具根本没装**。现在装上了，
   它会真的检查你这次改的文件，发现类型错误就拦住提交。

2. **但按现在的严格程度，它会拦下几乎所有提交。** 这是必须先告诉你的：仓库里现有的
   代码本来就有很多类型问题——每 10 个后端文件里约 4 个、每 10 个测试文件里约 5 个
   至少带 1 个错误。而一次提交通常会碰好几个文件，**只要其中一个是旧的脏文件就会被拦**。
   拿这个仓库最近的真实改动实测：最近碰过后端代码的 19 次提交里，**有 18 次会被拦下
   （94%）**，而被拦的原因基本都不是那次改的内容，是文件里本来就有的老问题。

3. **所以文末给了你一个选择题**（见「待你裁决」）：是接受这个严格程度、边改边清，
   还是先降一档让它只管更明确的问题。我没有替你决定，因为两条路的代价不一样。

**你需要做什么**：无变化（提交代码前多了一道类型检查，以前那道其实一直没开）。

---

## 4-A 技术验收

### 一 裁判命令逐条（卡文 §二）

| # | 裁判 | 结果 |
|---|---|---|
| 1 | `backend/.venv/bin/pyright --version` | **pyright 1.1.411** |
| 2 | `pyright --outputjson backend/app` summary | files **263** / errors **424** / warnings **85** |
| 3 | `grep -i 'pyright\|mypy'` 三个声明文件 | **有效声明行恰好 1 条**，见 §三 |
| 4 | `backend/app` 文件数 / `type: ignore` | **263**（卡文写 258，见下）/ **22**，增量 **0** |
| 5 | `lefthook run --command python-typecheck` | **真跑并按 rc 传递**，见 §七 |

> **裁判 4 的数字更正**：卡文写 `git ls-files 'backend/app/**/*.py'` → 258。该命令
> 复现无误，但它**漏掉 `backend/app` 一级的 5 个文件**（`__init__.py` / `config.py` /
> `dependencies.py` / `main.py` / `security.py`）——与 Z7-A 钉死的是**同一个 glob 语义**
> （`**` 要求至少跨一级）。真实分母 **263**，并由 pyright 独立佐证：
> `filesAnalyzed = 304 = 263(backend/app) + 41(tests) + 0(src)`。

---

### 二 (a) pyright vs mypy —— 选 pyright，依据是实测不是偏好

| | pyright | mypy |
|---|---|---|
| 配置 | 根 `pyrightconfig.json`，**13 项设置** | **零**（`[tool.mypy]` / `mypy.ini` / `setup.cfg` 段全无） |
| 调用方 | `lefthook.yml` 的 `python-typecheck` 块（活的） | **零**（任何 workflow / 脚本 / hook 都没有 `mypy` 命令） |
| 依赖声明 | 本卡之前**无** | 根 `requirements.txt` 两行 |
| 是否装过 | 否（本卡装） | 否 |

> ### ⛔ 自我更正（Codex round-1 #3 证伪，已在 commit-2 改掉）
>
> 我原先写的是：「根 `requirements.txt` **没有任何安装方**，所以那条 mypy 声明是
> **三重死的**（无配置、无调用方、无安装方），从未生效过一次。」——**这是错的。**
>
> Codex 指出 `scripts/deploy_epic12.py::install_dependencies()`（`:166-180`）用
> `Path(__file__).parent.parent / "requirements.txt"` 定位到**仓库根**的那份并执行
> `pip install -r`，且它在主流程 step 2（`:298`）被调用。我实测复现无误。
>
> **我为什么漏了它**：做「谁在装根 requirements」这个搜索时，我的 grep 限定了
> `--include='*.yml' --include='*.yaml' --include='*.sh' --include='*.md'
> --include='*.toml' --include='*.cfg' --include='Dockerfile*'` ——**把 `.py` 排除在外**。
> 安装方偏偏是个 Python 脚本。这与本车道上一张卡（Z7-A）漏掉 npx 缓存是**同一个毛病**：
> 搜索面自己划窄了，然后把「没搜到」当成「不存在」。
>
> **更正后的口径**：mypy **可能被装过**（走 `deploy_epic12.py` 的人会装到），但
> **从来没有任何东西调用它**（受版本控制的 workflow / 脚本 / hook 里零个 `mypy` 命令），
> 也没有任何配置。选 pyright 的依据不受影响；被删掉的只是那句无法证明的历史断言。

处置：两处 `mypy>=1.5.0` 声明**改注释不删除**（留追溯 + 写清取代理由），两处
`#   mypy .` 用法注释改指 pyright。

---

### 三 (b) 依赖落点 —— 根 `pyproject.toml` 的 dev extras

选它的依据不是我的偏好，是 **`backend/requirements.txt` 文件头自己写的单一权威规则**：

```
# 单一权威说明:
# - 本文件管 backend 生产依赖 (pip / docker build)
# - pyproject.toml [tool.uv] 管 dev/api extras (uv.lock 锁定)
```

⇒ 写进 `backend/requirements*.txt` 会**违反它自己的声明**；新建
`backend/requirements-dev.txt` 会造出**第三个口径**，与本卡"归口"的目的相反。

**裁判 3 结果（单一口径成立）**：

```
--- 有效声明行（非注释）---
  pyproject.toml:29:    "pyright>=1.1.411",
```

其余 14 处命中全部是注释（mypy 的两行已注释化 + 说明文字 + 用法示例）。

**安装与 `uv.lock`**：已装进 `backend/.venv`，`uv lock` 重生成后 diff **纯增量**：

```
 uv.lock | 24 ++++++++++++++++++++++++
 1 file changed, 24 insertions(+)
新增 name 行: nodeenv, pyright   删除: 0   其它包 version 变化: 0
```

> ⚠️ **共享 venv 影响（卡文要求写明）**：本车道 `backend/.venv` 是 **symlink**，指向
> `card-v5-lance/backend/.venv` 的真实目录。本次安装**落在那个真实 venv 里，因此影响
> 所有 symlink 到它的车道**。装前装后逐包对账：
>
> ```
> pip list diff:  +nodeenv==1.10.0   +pyright==1.1.411      （既有 227 个包，0 个变动）
> bin diff:       +nodeenv +pyright +pyright-langserver
>                 +pyright-python +pyright-python-langserver     ← 共 5 个
> ```
>
> 即**纯新增，未升级/降级/移除任何既有包**。
>
> 证据形态说明（回应 Codex round-1 #8）：上面两行不是事后推断，是**装前拍的快照**
> （`pip list --format=freeze | sort` 与 `ls .venv/bin | sort` 各存一份）与装后同命令
> 输出的 `diff`。Codex 只能看到仓库现状、看不到这两份快照，因此把它标为「需要额外证据」
> 是合理的——证据在这里。**但它指出的数字错误成立**：我在 commit-1 的消息与本单初版
> 写的是「4 个 bin」，实际 diff 是 **5 个**（pyright 提供 4 个命令 + nodeenv 1 个）。已更正。
>
> 未验证其它车道当时是否正在使用该 venv（见「本卡未证明什么」）。

> 文档漂移（如实登记，本卡未修）：上面那段头注写的是 `[tool.uv]`，而实际的 dev extras
> 段名是 `[project.optional-dependencies]`（`[tool.uv]` 在 `pyproject.toml` 里不存在，
> 但 `uv.lock` 确实存在）。

---

### 四 (c) pythonVersion 口径 —— 3.14 → **3.11**，零代价收紧

同一 include、**只改这一项**的实测：

| `--pythonversion` | errors | warnings | 说明 |
|---|---|---|---|
| 3.9 | **656** | 86 | 比 3.11 多 **64** |
| 3.10 | **605** | 86 | 比 3.11 多 13 |
| **3.11** | **592** | 86 | **拐点** |
| 3.12 | 592 | 86 | 与 3.11 逐条相同 |
| 3.14（原值） | 592 | 86 | 与 3.11 逐条相同 |

3.9 多出的那 64 条是什么（逐条差集）：

```
  51  Alternative syntax for unions requires Python 3.10 or newer     <- PEP 604 `X | Y`
  12  No parameter named "context"
   1  "timeout" is not a known attribute of module "asyncio"          <- asyncio.timeout 是 3.11
```

**结论**：选 3.11 的理由是**对齐 CI 的最低目标档**（`test.yml` 的 `['3.11','3.12']`、
`api-spec-sync.yml` 的 `PYTHON_VERSION: '3.11'`），且在当前代码上**诊断集合逐条不变**
（592 → 592）。类型检查器的 `pythonVersion` 该盯的是「代码必须能跑的最低版本」，
而不是开发机恰好装的那个。

> **措辞边界（Codex round-1 #5 整改，两句都曾说宽）**：
> - 我原写「本仓代码的**真实下限是 3.11**」——**过强**。证据只支持「**某些代码路径**
>   要求 ≥3.10（51 条 union）/ ≥3.11（13 条 asyncio 接口）」，不支持「整仓及其依赖
>   已在 3.11 上跑通」——后者需要 3.11 环境下的装包与关键流程验证，本卡没做。
>   （那条 ≥3.11 的证据我实测复核过：`background_task_manager.py:208` 是
>   `asyncio.create_task(wrapped_task(), context=ctx)`，**无兼容分支**，而它上面
>   `:205-206` 的注释自己写着「Python 3.11+ asyncio.create_task 原生支持 context= 参数」。
>   pyright 在 3.9 下于该行报 `No parameter named "context"`，3.11 下不报。）
> - 我原写「**零代价**的收紧」——**过强**。准确说法是「当前代码上诊断集合不变」；
>   目标版本还会影响 stub 选择与条件分支分析，不该承诺一般意义上的零副作用。

**连带线索（本卡不修，已登台账）**：根 `pyproject.toml:6` 的
`requires-python = ">=3.9"` 与相关 backend 代码路径**存在实际冲突**（那 51 条 union
指向 ≥3.10，13 条 asyncio 指向 ≥3.11）。`backend/ruff.toml` 的
`target-version = "py39"` 控制的是**规则与格式化目标**，不能当成「已完成的兼容性验证」，
所以它也只作线索登记，不作断言。

**这个改动对 hook 真生效吗？**（hook 传的是 `{staged_files}` 单个文件路径，如果 pyright
在这种调用形态下不读配置，那我改的口径就是摆设。）用**能翻转结论的验伪锚**验证——
把配置临时改成 3.9，看同一个单文件跑的结果是否跟着变：

| `pyrightconfig.json` 的 `pythonVersion` | `pyright backend/app/config.py` |
|---|---|
| `3.11`（现行） | union 语法报错 **0**，总 errors **0** |
| 临时 `3.9` | union 语法报错 **1**，总 errors **1** |

⇒ **配置被吃到了**。（顺带：`backend/app/config.py` 正是 `backend/app/**/*.py`
漏掉的那 5 个一级文件之一，它在 3.11 下干净、在 3.9 下报错。）验完还原，sha 逐字节相同。

> 实现细节：理由写在 `pyrightconfig.json` 里（pyright 用 JSONC 解析，实测接受 `//`
> 注释且不报配置错误）。全仓**只有这一个** pyright 配置源——`pyproject.toml` 没有
> `[tool.pyright]` 段，没有 `.vscode/`，无第二个解析它的程序（`lefthook.yml` 只是文字提及）。

---

### 五 (d) 存量类型债基线（最终配置 = typeCheckingMode `basic` / pythonVersion 3.11）

**全量（pyrightconfig include）**：`filesAnalyzed = 304`，**errors 592 / warnings 86 / infos 0**。

卡文只要 top-10，但第 10 名**存在并列**（`reportReturnType` 与 `reportOptionalCall`
同为 4，Codex round-1 指出，实测成立），截断会制造歧义，所以给**全表**（17 条，
合计校验 = 592）：

| 规则码（error） | 条数 | | 规则码（error） | 条数 |
|---|---|---|---|---|
| `reportUnusedImport` | **170** | | `reportOptionalOperand` | 5 |
| `reportAttributeAccessIssue` | **103** | | `reportReturnType` | 4 |
| `reportArgumentType` | **72** | | `reportOptionalCall` | 4 |
| `reportMissingImports` | **69** | | `reportAssignmentType` | 3 |
| `reportCallIssue` | **54** | | `reportOptionalSubscript` | 3 |
| `reportUnusedVariable` | **48** | | `reportUnusedExcept` | 2 |
| `reportOptionalMemberAccess` | **39** | | `reportOperatorIssue` | 2 |
| `reportGeneralTypeIssues` | **12** | | `reportInvalidTypeForm` | 1 |
| | | | `reportRedeclaration` | 1 |
| | | | **合计** | **592** |

| 规则码（warning，共 86） | 条数 |
|---|---|
| `reportUnnecessaryIsInstance` | 60 |
| `reportUnnecessaryTypeIgnoreComment` | **14** |
| `reportUnusedFunction` | 12 |

**按 include 目录**：

| 目录 | 文件数 | 诊断数 | 备注 |
|---|---|---|---|
| `backend/app` | 263 | 509（424 err + 85 warn） | |
| `tests`（仓库根） | 41 | 169（168 err + 1 warn） | |
| `src` | **0** | 0 | **`include` 里列着，但 tracked `.py` = 0 —— 空集** |

两条值得单独拎出来的：

- **`reportUnnecessaryTypeIgnoreComment = 14`**：现存 22 处 `# type: ignore` 里
  **14 处是多余的**（pyright 认为那些位置本来就没错）。这类注释是"曾经压过某个报错、
  后来代码改了但注释留着"的化石，它们会掩盖真实错误。本卡只报出，不动。
- **`reportMissingImports = 69`** 的模块分布（禁止关掉它，所以先看清是什么）。
  按**顶层包**分组、由脚本重算（不是对截断列表手工求和，合计校验 = 69）：

  | 顶层包 | 条数 | | 顶层包 | 条数 |
  |---|---|---|---|---|
  | `agentic_rag` | **36** | | `openapi_spec_validator` | 2 |
  | `planning_utils` | **11** | | `migrate_chromadb_to_lancedb` | 1 |
  | `src` | **6** | | `generate_file_index` | 1 |
  | `app` | 4 | | `imagebind` | 1 |
  | `bmad_orchestrator` | 4 | | | |
  | `memory` | 3 | | **合计** | **69** |

  绝大多数是**导入路径解析**问题而非缺包：`planning_utils` 的实体在 `scripts/lib/`、
  `src.*` 指向的 `src/` 是空目录（tracked `.py` = 0）、`app.*` 是相对 backend 的包根问题。
  只有 `imagebind` 一条看起来像真的缺三方包。本卡只报出，不动。

---

### 六 ⚠️ 债表并不封顶：门可达面 ≠ include 面（本卡最重要的发现）

`pyrightconfig.json` 的 include 与 `lefthook.yml` 的 glob **是两个不同的集合**，
而且方向相反地错开：

| 目录 | 在 hook glob `{backend,src}/**/*.py` | 在 pyrightconfig include | 实测诊断 |
|---|---|---|---|
| `backend/app`（263） | ✅ | ✅ | 424 err / 85 warn |
| `backend/tests`（**493**） | ✅ **在** | ❌ **不在** | **1396 err / 107 warn** |
| `tests`（根，41） | ❌ **不在** | ✅ **在** | 168 err / 1 warn |
| `backend/start_server.py`、`backend/mutmut_config.py` | ❌（`**` 漏一级） | ❌ | 1 err |
| `src`（0） | ✅ | ✅ | 空集 |

三条都是**实测**，不是推断：

- `backend/tests/__init__.py` 暂存 → hook 输出 `Running pyright type check` ⇒ **在 glob 内**；
- `backend/start_server.py` 暂存 → hook 输出 `python-typecheck (skip) no files for inspection`
  ⇒ **不在 glob 内**（与 Z7-A 修掉的 `python-lint` 同一个缺口，本卡受禁改边界未动）；
- 全量 `filesAnalyzed = 304` 不含 `backend/tests` 的 493 个 ⇒ **不在 include 内**。

⇒ **卡文 (d) 要求的「全量基线 592」并不封顶这道门能报出的东西。**

> ### ⛔ 自我更正（Codex round-1 #2 证伪）
>
> 我原先算的是 `592 + 1396 + 1 = 1989`。**两头都错**：
> - 592 里含**根 `tests` 的 168 条**，而根 `tests` **不在** hook glob 内 → 多算；
> - 只数了 `backend/app` 与 `backend/tests`，**漏掉 `backend/` 下其余 87 个可达文件**
>   （`backend/scripts` 48 + `backend/lib` 39）的 **269** 条 → 少算。
>
> 正确做法是直接构造 hook glob 的 tracked 集合再跑一次，实测：

```
$ git ls-files -- backend/ src/ | grep '\.py$' | awk -F/ 'NF>=3'   # {backend,src}/**/*.py
  843 个文件   (backend/tests 493 + backend/app 263 + backend/scripts 48 + backend/lib 39)
$ xargs pyright --outputjson < 该集合
  {'filesAnalyzed': 843, 'errorCount': 2089, 'warningCount': 207}
```

> **门可达债 = 843 文件 / 2089 errors / 207 warnings**，与 Codex 独立复测的数字逐项相同。
> 这仍然是**当前代码的集合扫描结果**，不是「未来提交的诊断上限」。

---

### 七 (e) 增量 0 + (f) 负控 —— 判据绑「走了哪条分支」

`type: ignore` = **22**（基线 22，**增量 0**）；`typeCheckingMode` 未动；
`reportMissingImports` 未关；`lefthook.yml` **0 行改动**。

> 判据设计：SKIP 分支与"真跑且通过"**都是 rc=0**，只看 rc 分不出来——而这正是 X5-A
> 修的那个病。所以每条负控都绑定 run 体自己 echo 的分支标识。

| 用例 | 期望分支 | 实际 | rc | 证据行 |
|---|---|---|---|---|
| **裁判 5**：暂存一个 pyright 零诊断的真实文件 | 真跑 | **真跑** | **0**（`✔️`） | `[Python] Running pyright type check (backend/.venv/bin/pyright)...` + `Typecheck done (exit: 0)` |
| **负控 ②**：暂存一个必然类型错误的文件 | 真跑 + 阻断 | **真跑** | **1** | pyright 报出 2 条具体错误 + `Typecheck done (exit: 1)` + `exit status 1` |
| **负控 ①**：遮蔽 pyright | SKIP | **SKIP** | **0**（`✔️`） | `SKIP: pyright not installed (looked for backend/.venv/bin/pyright, then PATH).` + `SKIP: typecheck did NOT run -- this is NOT a pass.` |

负控 ② 的完整拒因：

```
backend/app/_z7b_typeerr.py:8:15 - error: Type "int" is not assignable to declared type "str"
backend/app/_z7b_typeerr.py:8:23 - error: Argument of type "Literal['not an int']" cannot be
                                   assigned to parameter "x" of type "int" in function "add_one"
```

负控 ① 的**遮蔽手法**（重要，因为共享 venv 不能乱动）：没有动 `card-v5-lance` 的真实
venv，而是把**本车道的 `backend/.venv` symlink** 临时换成一个空目录，让那个块既找不到
`backend/.venv/bin/pyright` 也找不到 PATH 上的 pyright。收尾无条件还原并复核：
symlink 指向原目标、`pyright --version` 仍可用、探针文件逐字节相同、工作树只剩本卡改动。

产物（`backend/app/_z7b_typeerr.py`）当次移出工作树，**未进任何 commit**。

---

### 八 Codex 复核（卡文 (g)）—— 一轮已完成，8 条全部本机复现

**模型** `gpt-6-astra` + `model_reasoning_effort=ultra`，codex-cli 0.153.3，`--sandbox read-only`，
审查面 `41470106 → d21b0bc4`。产物 `_bmad-output/审查/codex-review-CARD-TOOL-pyright.md`。

**终裁摘要**：**BLOCKER 0 / HIGH 1 / MEDIUM 5 / LOW 2**。按 `card-batch-protocol.md` §1
的合并门（数据丢失 / live vault 或 7691 写入 / 安全 / 指定裁判红 / 负控假绿），
**阻断级 = 0**。Codex 原文末句：「本次四文件改动**未发现数据丢失／安全／越权写入级别的
问题**；此前共享 venv 安装是否超出授权，需要额外证据才能判断。」

> ⚠️ 纪律：以下每条我都自己跑了一遍再采信。其中 **#2 与 #3 直接证伪了我的断言**，
> 我没有辩护，直接改。

| # | 严重度 | Codex 指出 | 我的独立复现 | 处置 |
|---|---|---|---|---|
| 1 | HIGH | 「约一半提交被拦」未被证明——文件占比不能换算成提交阻断率 | 两个占比它复算无误（42.21% / 50.51%）；换算这一点成立 | ✅ 补做**提交级**度量（18/19 = 94%）并写明其口径边界（今天的诊断套历史文件集） |
| 2 | MEDIUM | 「门可达债 1989」算错 | **成立**：正确是 **843 文件 / 2089 err / 207 warn**，与它复测逐项相同 | ✅ 改正 + 写明错在哪两头 |
| 3 | MEDIUM | 「根 requirements 没有安装方 / 声明从未生效」不成立 | **成立**：`scripts/deploy_epic12.py:166-180` 装的就是根那份，`:298` 调用 | ✅ 撤回该断言 + 写明我的搜索面漏了 `.py` |
| 4 | MEDIUM | 可重复安装链未闭合（根安装说明装不到 pyright；`dev` extra 不自动同步；uv 默认环境是根 `.venv` 而非 `backend/.venv`） | 成立 | ✅ commit-2 在 `requirements.txt` 安装说明里补上装到 `backend/.venv` 的确切命令 + uv 环境差异警告 |
| 5 | MEDIUM | 「整仓真实下限 3.11」「零代价」过强 | 成立：51 条 union 只指向 ≥3.10，13 条 asyncio 指向 ≥3.11；且目标版本还会影响 stub 与条件分支分析 | ✅ 改述为「对齐 CI 最低目标档 + 当前诊断集合不变」，并写明不承诺一般性零副作用 |
| 6 | MEDIUM | `--skipunannotated` 会**一并跳过新写的无注解函数**，不是只消旧债 | 成立 | ✅ 写进 D-1 乙案的代价 |
| 7 | LOW | `backend/requirements.txt:14` 头注写 `[tool.uv]` 应为 `[project.optional-dependencies]`；JSONC 未发现实际消费方回归 | 成立 | 登台账（既有漂移，非本卡引入） |
| 8 | LOW | 「新增 4 个 bin」口径需解释（实为 5） | **成立**：实测 diff 是 5 个 | ✅ 改正为 5，并说明快照证据形态 |

**Codex 独立复核通过的数字**（它自己跑了一遍）：`uv.lock` +24/−0 且语义只增两包；
`type: ignore` 两个 commit 均 22、增量 0；`typeCheckingMode` 未改、`reportMissingImports`
仍为 `true`；error top-10 与 warning 60/14/12 全部吻合；五组 pythonVersion 的
656/605/592/592/592 与「3.11、3.12、3.14 诊断集合逐条相同」也全部重现。

它另补了一条我漏写的：**error top-10 的第 10 名存在并列**——`reportOptionalCall` 同样是 4 条。

---

## 本卡未证明什么

1. **没有证明那 263 个 `backend/app` 文件的类型是正确的。** 只是把检查器跑了一遍，
   **没有逐条判断** 592 条诊断里哪些是真缺陷、哪些是检查器误报。
2. **没有跑 CI，也没有把 pyright 接进任何 workflow。** 没有任何 workflow 安装
   `[project.optional-dependencies].dev`（`test.yml` 是 `cd backend && pip install -r
   requirements.txt` 再按名字显式装三个），所以 **pyright 目前只在本地 pre-commit 生效**。
3. **没有验证其它 symlink 车道当时是否正在使用那个共享 venv。** 做了装前装后逐包对账
   （纯新增两个包），但并发使用面未验证。
4. **没有验证 pyright 在 CI 的 3.11 / 3.12 解释器上的行为。** `pythonVersion = 3.11`
   是**分析目标**声明，与实际运行解释器（本机 3.14）是两回事；本卡只在 3.14 上跑过 pyright。
5. **没有修那两个被证伪的版本声明**（`requires-python >= 3.9`、`backend/ruff.toml`
   的 `py39`）——只给出了证据。
6. **没有修 `python-typecheck` 的 glob 缺口**（漏 `backend/` 一级 2 个文件），卡文禁改。
7. **没有验证 `reportUnnecessaryTypeIgnoreComment` 报出的那 14 处确实可以安全删除**
   ——只报出条数，没有逐处判断。
8. **没有在 `pyrightconfig.json` 加注释这件事上验证过全部潜在消费方**：只确认了
   pyright 自己接受、且全仓无第二个解析它的程序；编辑器插件（Pylance 等）未实测。
9. **没有跑任何变异 harness**，因此「这道门有多强」只有上面 3 条负控，没有变异证据。
10. **94% 那个提交阻断率不是历史事实**（Codex #1）：它是把**今天的**诊断套到**历史的**
    改动文件集合上算的，也没按改动频次加权。真正的实测需要「当时的 staged 集合 +
    当时的代码 + 固定环境」三者齐备。
11. **2089 是当前代码的集合扫描结果，不是「未来提交的诊断上限」**（Codex #2）。
12. **没有证明整仓及其依赖已经能在 3.11 上跑通**（Codex #5）。`pythonVersion = 3.11`
    是**分析目标**声明；证据只支持「某些代码路径要求 ≥3.10 / ≥3.11」，不支持
    「3.11 环境下装包与关键流程都通过」——后者本卡没做。
13. **没有证明「mypy 从未被安装过」**（Codex #3）——这是无法从当前状态推出的历史断言，
    已从仓库注释与本单里删除。能证明的只有「没有任何配置、没有任何调用方」。
14. **没有证明安装期间其它 symlink 车道未受影响**（Codex #8）。有装前/装后快照证明
    「包与 bin 只增不改」，但没有当时的占用记录。

---

## 台账待登记条目

> 台账只由主 session 写入，本卡不改。以下为建议登记内容。

| # | 条目 | 建议归属 |
|---|---|---|
| 1 | **门可达债 = 843 文件 / 2089 err / 207 warn，而非 include 面的 592**：`backend/tests`（493）+ `backend/scripts`（48）+ `backend/lib`（39）在 hook glob 内但**不在** pyrightconfig include；根 `tests`（41）方向相反。两个集合需要统一口径 | 新卡（中），**与下面第 2 条同批** |
| 2 | **装上 pyright 后几乎所有提交都会被拦**：脏文件率 `backend/app` 42%（111/263）、`backend/tests` 50%（249/493）；**按真实提交算是 18/19 = 94%**（最近 40 个 commit 中触及门覆盖面的 19 个）。卡文 (e)「staged-only 所以存量债不阻断新代码」的前提**在数据上不成立** | **本卡裁决点，见文末** |
| 3 | **`requires-python = ">=3.9"` 与实际代码路径冲突**：51 条 PEP 604 `X \| Y`（≥3.10）+ 13 条 asyncio 接口（≥3.11）。最硬的一条不是类型检查器推的，是**代码自己的注释**——`backend/app/services/background_task_manager.py:205-208` 写着「Python 3.11+ 原生支持 `context=` 参数」并直接用了 `asyncio.create_task(..., context=ctx)`，**无兼容分支**。是否上调 `requires-python` 是产品决定（会影响可安装的 Python 范围），本卡只给证据 | 新卡（小） |
| 4 | **`python-typecheck` 的 glob 漏 `backend/` 一级 2 个文件**（`start_server.py` / `mutmut_config.py`），与 Z7-A 修掉的 `python-lint` 同一缺口，本卡受禁改边界未动 | 新卡（微），Z7 车道 |
| 5 | **14 处多余的 `# type: ignore`**（`reportUnnecessaryTypeIgnoreComment`）：会掩盖真实错误，建议清理 | 新卡（小） |
| 6 | **69 条 `reportMissingImports` 绝大多数是导入路径解析问题不是缺包**：`agentic_rag` 36 / `planning_utils` 11（实体在 `scripts/lib/`）/ `src` 6（`src/` 是空目录）/ `app` 4 / `bmad_orchestrator` 4 / `memory` 3 / 其余 5。唯一像真缺包的是 `imagebind` 1 条 | backlog |
| 7 | **`backend/requirements.txt` 头注写 `[tool.uv]` 但实际是 `[project.optional-dependencies]`** —— 文档漂移，本卡未修 | backlog（微） |
| 8 | **pyright 未接入任何 CI workflow**：没有 workflow 安装 dev extras，因此 CI 上不跑类型检查 | 新卡（小） |
| 9 | **共享 venv 变更记录**：`card-v5-lance/backend/.venv` 新增 `pyright 1.1.411` + `nodeenv 1.10.0`（纯新增，既有 227 包未动，新增 5 个 bin），影响所有 symlink 车道 | 环境记录 |
| 10 | **`scripts/deploy_epic12.py` 是根 `requirements.txt` 的安装方**（`:166-180`，主流程 `:298` 调用）。本卡把 mypy 改注释后，走该脚本部署的人不再装 mypy——这是预期结果（mypy 零调用方），但该脚本本身与 backend 侧依赖的关系没人梳理过 | backlog |
| 11 | **安装链仍未完全闭合**：`dev` extra 不会自动同步；`uv` 默认项目环境是**仓库根 `.venv`**，而 hook 优先找 **`backend/.venv`**，两者不是同一个。本卡在 `requirements.txt` 安装说明里补了确切命令，但没有做成可一键复现的流程 | 新卡（小） |

---

## 待你裁决

**D-1（本卡）这道门要多严？** 两个口径的数据，后者才是决策相关的那个：

| 口径 | 结果 |
|---|---|
| **按文件**：随机改一个文件被拦的概率 | `backend/app` **42%**（111/263）、`backend/tests` **50%**（249/493） |
| **按真实提交**：最近 40 个 commit 中触及门覆盖面的 19 个里有多少会被拦 | **18 / 19 = 94%** |

按提交算远比按文件算严重，原因很直接：一次提交常触及多个文件，**只要有一个旧脏文件
就整条被拦**。样例：`32c8e325` 触及 35 个受检文件、其中 15 个带 error；多数提交是
「碰 2–5 个文件、其中 1–2 个脏」。也就是说，**被拦的原因基本都不是那次改的内容**。

> **这个 94% 的口径边界（Codex round-1 #1 提出，采纳）**：它是把**今天的**诊断结果
> 套到**历史的**改动文件集合上算出来的，回答的是「如果这 19 次提交今天再做一遍会怎样」，
> **不是**历史事实（当时那些文件未必带同样的错误）。它也没有对改动频次加权。
> 作为「这道门上线后好不好用」的估计够用，但不该当成实测的历史阻断率。
> Codex 独立复算了两个文件占比（42.21% / 50.51%）并确认无误，同时指出**文件占比不能
> 直接换算成提交阻断率**——这正是我补做提交级度量的原因。

卡文硬边界禁止下调 `typeCheckingMode`、
禁止关 `reportMissingImports`、禁止批量加 `# type: ignore`，所以常规的三条泄压阀都不能用。
我**没有擅自降门**，把选项和实测代价摆在这里：

- **甲（默认，当前状态）**：保持严格，边改边清。代价：一半提交会被拦；好处是债只会减不会增。
- **乙**：给 hook 加 `--skipunannotated`（跳过无注解函数）。**实测**：`backend/tests`
  从 1396 → **343**（−75%），`backend/app` 从 424 → 397（−6%）。它**不属于**被禁的三条
  （既没下调 `typeCheckingMode` 也没关 `reportMissingImports`）。
  ⚠️ **但它不是「只消旧债」**（Codex round-1 #6，采纳）：它跳过的是「无类型注解的函数」，
  **新写的无注解函数一样不检查**。那 −75% 也不代表「这些是误报」，只代表「这些函数
  从此不被分析」。若采纳，等于用**永久缩小覆盖面**换取当下的可用性。
- **丙**：把 hook 的 glob 收到 `backend/app`（把 493 个测试文件移出门外）。代价：测试代码
  从此不受类型检查；好处是阻断面立刻减半，且与 pyrightconfig 的 include 口径对齐。
- **丁**：先只当 warning 不阻断——**不推荐**，这正是 X5-A 刚修好的那个病（门在说谎），
  且违反卡文硬边界。

> pyright **没有** mypy 那种 baseline / 只拦新增的内建机制（`--help` 全选项已核，无
> `baseline` / `diff` / `incremental` 类选项），所以「只拦新增错误」这条路需要另写工具，
> 不在本卡范围。

---

*生成时间 2026-09-05 · 车道 `card/z7-tool` · commit `d21b0bc4` + `a01b1733` · 未 push*
