# UAT — CARD-REDBASE-R2「清掉对外契约面残留的 D16 前 group_id 示例」

> 批次 `[BATCH-2026-09-05-第十一批 / CARD-REDBASE-R2]`
> 车道 `card/z4-redbase`（同车道串行，前置 Z4-A commit `7283a8df`）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十一批-goals/Z4-B.md`
> 微卡 1.5h，按卡文默认**不送 Codex**

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：无变化（接口文档里的示例改成现在的写法）。**

后端有一份给插件/前端看的接口说明书（OpenAPI）。里面举例说「学习记录的归属标签长这样：
`math54:离散数学`」——那是 2026-05-05 之前的老写法。系统实际发出去的早就是
`vault:cs_61b:math54:离散数学`（前面多了 vault 段，用来隔离不同 vault 的数据）。

**说明书写的和实际发的对不上**，照着说明书写代码的人会踩坑。这次把示例改对了。

**产品行为一行没改**，接口返回什么、怎么算，全部照旧。你不需要做任何事。

---

## 4-A 技术验收

### 一 六处逐条（卡文 §〇 点名，开工 grep 重取，行号完全吻合）

| # | 位置 | 性质 | 改前 | 改后 |
|---|---|---|---|---|
| 1 | `app/models/metadata_models.py:52` | `CanvasMetadataResponse.group_id` Field description | `Graphiti group_id (e.g., 'math54:离散数学')` | `Graphiti group_id (D16 格式, e.g., 'vault:cs_61b:math54:离散数学')` |
| 2 | `app/models/metadata_models.py:62` | `CanvasMetadataResponse` json_schema_extra example | `"group_id": "math54:离散数学"` | `"group_id": "vault:cs_61b:math54:离散数学"` |
| 3 | `app/models/metadata_models.py:177` | `CanvasIndexResponse` example | 同上 | 同上 |
| 4 | `app/models/metadata_models.py:292` | `SubjectInfo` example | 同上 | 同上 |
| 5 | `app/api/v1/endpoints/metadata.py:125` | 端点 docstring（进 OpenAPI path description） | `- **group_id**: Graphiti group_id (e.g., "math54:离散数学")` | `…(D16 格式, e.g., "vault:cs_61b:math54:离散数学")` |
| 6 | `app/services/subject_resolver.py:48` | 类 docstring 的 doctest 风格示例 | `>>> print(info.group_id)  # "math54:离散数学"` | `>>> print(info.group_id)  # "vault:cs_61b:math54:离散数学"` |

### 二 偏差登记（两条，如实不擅改）

**偏差 1 — 示例的 canvas 段取 `离散数学`，不是卡文写的 `线性代数`。**

卡文 (a) 写「示例值用中性 `vault:cs_61b:math54:线性代数`」。**照字面套用会让契约示例自相矛盾**：
这六处的上下文 canvas 全部是「离散数学」——

```
metadata_models.py:59   "canvas_path": "Math 54/离散数学.canvas",   ← 与 :62 的 group_id 同一个 example
metadata_models.py:172  "canvas_path": "Math 54/离散数学.canvas",   ← 与 :177 同一个 example
subject_resolver.py:46  >>> info = resolver.resolve("Math 54/离散数学.canvas")  ← :48 的上一行
metadata.py:105/:176    canvas_path 的 Query example 也是 "Math 54/离散数学.canvas"
```

group_id 的末段来自 canvas 名，写成 `…:math54:线性代数` 会让消费方看到
「输入 `离散数学.canvas` → 输出 `…:线性代数`」这种不可能的对应关系。
**这是发给外部的契约文档，内部矛盾比测试里的矛盾更严重。**

处置：取卡文的**实质约束**——D16 四段格式 + **vault 段用中性 `cs_61b`（不写本机 `canvas_vault`）**，
canvas 段跟随各处上下文取 `离散数学`。全仓 `grep -c 'canvas_vault' backend/app` 对本卡新增行为 0。
**若主 session 认为必须逐字采用 `线性代数`，需连同 3 处 `canvas_path` 示例一起改**（那会超出卡文的「六处」范围），请裁决。

**偏差 2 — 裁判 1 的字面判据不可能满足（子串必然命中）。**

卡文裁判 1 写 `grep -rn 'math54:离散数学\|math54:线性代数' backend/app backend/tests` → 空。
但 `math54:离散数学` 是 `vault:cs_61b:math54:离散数学` 的**子串**——改成任何 D16 形态后 grep 都还会命中；
换成卡文指定的 `线性代数` 同样如此。该判据**对任何合法改法都判失败**。

处置：用等价但精确的判据——「命中行的 `math54:` 前面必须有 `vault:<vid>:`」，即**裸格式归零**（卡文 (d) 的原话）：

```
$ grep -rn 'math54:离散数学\|math54:线性代数' backend/app backend/tests \
  | grep -vE 'vault:[a-z0-9_]+:math54:|vault:\{[^}]+\}:math54:'
backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py:311:        CARD-REDBASE-R1 翻新: 期望值 ``math54:线性代数`` 写于 8222daef
```

**唯一剩余命中是 Z4-A docstring 里引述历史旧期望值的陈述句**（「期望值 `math54:线性代数` 写于 8222daef」），
不是示例、不发给任何消费方；把它改成 `vault:` 前缀等于**篡改历史记述**（那句话的信息就是「当年期望的是裸格式」）。
按卡文 (d) 的排除精神（Z4-A 产物）保留。

### 三 裁判命令逐条

| # | 裁判 | 结果 |
|---|---|---|
| 1 | 裸格式复扫（精确版，见偏差 2） | **裸格式归零**，唯一命中是 Z4-A 的历史引述句 |
| 2 | `pytest -q -p no:cacheprovider tests/api/v1/endpoints/test_metadata_subject_mapping.py tests/unit/test_subject_resolver.py tests/contract/test_openapi_snapshot_drift.py` | **81 passed**；单独跑 contract → **23 passed**（与卡文要求一致） |
| 3 | `git diff 7283a8df HEAD -- backend/app \| grep -E '^\+' \| grep -vE '^\+\+\+' \| grep -vE '("\|#\|\*\|例\|e\.g)'` | **空** |
| 4 | `--snapshot openapi.json` | **`DRIFT: none (paths=193 schemas=353)`** |

### 四 零逻辑改动（卡文 (b)）

`backend/app` 的**全部 6 行新增**：

```
+    - **group_id**: Graphiti group_id (D16 格式, e.g., "vault:cs_61b:math54:离散数学")
+        ..., description="Graphiti group_id (D16 格式, e.g., 'vault:cs_61b:math54:离散数学')"
+                "group_id": "vault:cs_61b:math54:离散数学",
+                "group_id": "vault:cs_61b:math54:离散数学",
+                "group_id": "vault:cs_61b:math54:离散数学",
+        >>> print(info.group_id)  # "vault:cs_61b:math54:离散数学"
```

`if` / `return` / `else` / `elif` / 赋值行变更计数 = **0**。裁判 3 输出为空。

### 五 OpenAPI 快照（卡文 (c)，禁手改）

只经 X8 的 `--write`，**未手改 `backend/openapi.json`**：

```
$ cd backend && ./.venv/bin/python ../scripts/spec-tools/check-openapi-drift.py --write openapi.json
WROTE: openapi.json (paths=193 schemas=353, x-generated-at=2026-09-04T23:41:22.277947+00:00)

$ ... --snapshot openapi.json
DRIFT: none (paths=193 schemas=353)
```

快照 diff **5 增 5 删**，逐条：

| 变化 | 类别 |
|---|---|
| `components.schemas.CanvasMetadataResponse.example.group_id` | example 文本 ✓ |
| `components.schemas.CanvasIndexResponse.example.group_id` | example 文本 ✓ |
| `CanvasMetadataResponse.properties.group_id.description` | description 文本 ✓ |
| `/api/v1/canvas-meta/metadata` 的 path `description` | description 文本 ✓ |
| `x-generated-at` 时间戳 | ⚠️ **不是 example/description** —— 见下 |

⚠️ **`x-generated-at` 如实登记**：卡文裁判 4 说「快照 diff 只含 example/description 文本」，
但 `--write` **必然**更新这个时间戳（`21:00:02` → `23:41:22`）。这是 X8 工具的固有行为、
不是本卡的额外改动；`--snapshot` 的漂移比较会把它当易变字段剔除，所以复验仍是 `DRIFT: none`。

**六处源码改动为什么只反映为四处快照变化**（不是遗漏，逐条查过）：

| 源码处 | 是否进 OpenAPI | 依据 |
|---|---|---|
| `:52` `:62` `:177` `metadata.py:125` | **进** | 前三者属 `CanvasMetadataResponse` / `CanvasIndexResponse`，两个 schema 都在 `components.schemas` 里（实查确认）；后者是端点 docstring → path description |
| `:292`（`SubjectInfo` example） | **不进** | `SubjectInfo` 不是任何端点的 response_model，实查 `components.schemas` **无该 schema** |
| `subject_resolver.py:48` | **不进** | 服务层类 docstring，不参与 OpenAPI 生成 |

### 五之二 格式门（本卡零新增漂移）

`ruff check` 三文件 **All checks passed**；`ruff format --check` **rc=1**
（`metadata_models.py` / `subject_resolver.py` 想被 reformat）。

按老教训先查基线（Z4-A `7283a8df`）。⚠️ **第一次对比方式是错的**：我把基线文件复制到
scratch 目录后跑 `ruff format --diff --config <pyproject>`，命令直接失败
（`For more information, try '--help'`），错误输出被当成「基线无漂移」，
于是逐行对比显示「本卡新增 87 处漂移」——**全是假证据**。

正确做法是让 ruff 按**真实路径**发现配置，用 `--stdin-filename` 喂基线内容：

```
$ git show 7283a8df:backend/<f> | (cd backend && ruff format --diff --stdin-filename "<f>")
基线漂移行数 = 215
当前漂移行数 = 215
$ diff <(基线 +/- 行, 含空行) <(当前 +/- 行, 含空行)
2c2
< -        ..., description="Graphiti group_id (e.g., 'math54:离散数学')"
> -        ..., description="Graphiti group_id (D16 格式, e.g., 'vault:cs_61b:math54:离散数学')"
4c4
< +    group_id: str = Field(..., description="Graphiti group_id (e.g., 'math54:离散数学')")
> +    group_id: str = Field(..., description="Graphiti group_id (D16 格式, e.g., 'vault:cs_61b:math54:离散数学')")
```

**行数完全相同（215 = 215），逐行只有 2 处差异，而这 2 处差异就是本卡改的那个字符串本身。**
即：这条 hunk（ruff 想把三行 `Field(...)` 合成一行，合成后 ~104 字符 < `line-length = 120`）
在 Z4-A 基线上**就已存在**，本卡只是让 hunk 内的字符串内容变了。**本卡零新增漂移。**

### 五之三 类型门（pyright，同为存量）

本卡改到 `backend/app/` → `pre-commit::python-typecheck` 触发并**拦下了第一次提交**
（`[Python] Type errors found!` / `Typecheck done (exit: 1)`）。Z4-A 只改 `backend/tests/` 未触及。

同样做基线对照——临时把三个文件还原到 Z4-A `7283a8df` 跑 pyright，再强制还原（try/finally + sha 对账）：

```
基线 7283a8df : rc=1, 5 errors
本卡 (R2)     : rc=1, 5 errors
本卡新增的错误：无（全部为存量）
本卡消除的错误：无
RESTORED_IDENTICAL = True
```

存量 5 条（全在本卡未触碰的行，类型也与字符串改动无关）：

```
app/api/v1/endpoints/metadata.py:76:16  - Import "os" is not accessed (reportUnusedImport)
app/api/v1/endpoints/metadata.py:78:14  - Import "agentic_rag.clients.lancedb_client" could not be resolved
app/api/v1/endpoints/metadata.py:464:34 - Arguments missing for parameters "subject", "category"
app/api/v1/endpoints/metadata.py:673:40 - "open_table" is not a known attribute of "None"
app/services/subject_resolver.py:18:8   - Import "logging" is not accessed (reportUnusedImport)
```

本卡改的行是 `:52 / :62 / :125 / :177 / :292 / :48`，与上述 5 条**无一重叠**。

### 五之四 门处置汇总（如实登记，不含糊）

| 门 | 结果 | 处置 |
|---|---|---|
| `pre-commit::python-lint` → `ruff check` | rc=0 | — |
| `pre-commit::python-lint` → `ruff format --check` | rc=1 | **存量**（§五之二 逐行证明），绕过 |
| `pre-commit::python-typecheck` → pyright | rc=1 | **存量**（§五之三 差集双向为空），绕过 |
| `pre-commit::spec-sync-flat` | ✔️ 通过 | 照常执行（它自己也跑了一次 `--write` 并 stage） |
| `pre-commit::ghost-files` | ✔️ 通过 | 照常执行 |
| `commit-msg::commitlint` / `spec-reference` | ✔️ 通过 | 照常执行 |

绕过用 `LEFTHOOK_EXCLUDE=python-lint,python-typecheck`。两个门被绕过前都**单独跑过、
并与 Z4-A 基线做过差集对照**——「被绕过的门会说什么」已经验过，不是盲绕。

### 六 本卡未证明什么

1. **未证明仓外消费方已适配。** 本卡只改了后端发出去的**说明书**，没有也无法证明
   Obsidian 插件 / 前端 / 任何第三方调用方已经按 D16 四段格式解析 `group_id`。
   若有消费方在按裸 `<subject>:<canvas>` 切分（例如 `split(":")` 取 `[0]` 当 subject），
   它拿到 `vault:cs_61b:math54:离散数学` 会解析成 `subject="vault"` —— **这个风险本卡没有排查**。
   注意：**实际返回值早就是四段了**（D16 于 2026-05-05 落地），所以本卡不新增该风险，
   只是让文档追上现实；但「文档改对了」不等于「消费方已适配」。建议独立卡做消费方侧扫描。
2. **未证明 `cs_61b` 这个示例 vault 段对读者最优。** 它只是一个中性占位（避免写本机
   `canvas_vault`），并非真实存在的 vault。
3. **未送 Codex**（卡文默认不送）。本卡无对抗性复核，只有上述自查。
4. **未验证 lefthook 的两条 spec-sync 命令在本次提交中的实际行为**——本卡提交时它们照常执行，
   但没有单独构造「快照过期」的场景去验证它们会拦。

### 七 台账待登记条目（本卡不改台账）

1. **新增行**：CARD-REDBASE-R2（`card/z4-redbase`，同车道 Z4-A 之后）——对外契约面 6 处
   D16 前 group_id 示例清零；零逻辑改动；openapi 快照经 `--write` 重生成，`DRIFT: none`。
2. **待裁决（偏差 1）**：示例 canvas 段取 `离散数学`（与上下文一致）而非卡文字面的 `线性代数`。
   若主 session 坚持逐字，需连带改 3 处 `canvas_path` 示例（超出卡文「六处」范围）。
3. **判据修订（偏差 2）**：卡文裁判 1 的字面 grep 对任何合法改法都判失败（子串问题），
   后续同类卡请直接用「裸格式归零」判据：
   `grep -rn '<subject>:<canvas>' <path> | grep -vE 'vault:[a-z0-9_]+:<subject>:'`。
4. **新增 backlog**：仓外消费方是否已按 D16 四段解析 `group_id`（见 §六.1），建议独立卡。
5. **工具行为登记**：`check-openapi-drift.py --write` 必然更新 `x-generated-at`，
   凡是要求「快照 diff 只含 X」的卡文都要把这个时间戳算进预期内。
