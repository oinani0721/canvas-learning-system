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

**该命令下唯一剩余命中是 Z4-A docstring 里引述历史旧期望值的陈述句**（「期望值 `math54:线性代数` 写于 8222daef」），
不是示例、不发给任何消费方；把它改成 `vault:` 前缀等于**篡改历史记述**（那句话的信息就是「当年期望的是裸格式」）。
按卡文 (d) 的排除精神（Z4-A 产物）保留。

⛔ **这条结论后来被 Codex 判定 FAIL——原因是判据本身，不是执行**（见 §八 E）。
上面这个判据只覆盖 `math54:` 这一个 subject 的两个字面量，属于「按字面量枚举」而不是「按形态匹配」，
于是同一契约面上换个 subject 值的同类缺陷（`数学:离散数学`，`intelligent_parallel_models.py:286,287`）
**必然漏掉**。该处已补修。本节结论应读作「**本卡 grep 的两个字面量**归零」，
**不是**「全仓裸格式归零」——全仓的完整分类见 §八 E 的逐条处置表。

### 三 裁判命令逐条

| # | 裁判 | 结果 |
|---|---|---|
| 1 | 裸格式复扫（精确版，见偏差 2） | ⚠️ **判据不够宽**：`math54:` 两个字面量归零（唯一命中是 Z4-A 的历史引述句），但 Codex 按形态全仓扫出同类遗漏一处，已补修 —— 见 §八 E |
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

⚠️ **证据与产物对不上号（本地编排 round-1 抓到，如实更正）**：上面这次 `--write` 的产物
**不是**最终进仓的那一份。`lefthook` 的 `pre-commit::spec-sync-flat` 在 commit 时**又跑了一次**
`--write` 并 `git add`（其输出 `[Spec Sync] + backend/openapi.json staged` 见提交日志），
于是 `a5e0ce79` 里的快照带的是 `23:47:48.360386+00:00`：

```
$ git show a5e0ce79:backend/openapi.json | grep -o '"x-generated-at": "[^"]*"'
"x-generated-at": "2026-09-04T23:47:48.360386+00:00"
```

内容层面无影响（两次生成除时间戳外逐字节相同，Codex 独立复算的
`ALIGNED_BYTES_EQUAL=True` / 同一 SHA-256 证明了这点），但**贴证据要贴产生产物的那一次**。

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

⚠️ **口径更正（Codex 复核）**：下文说的「215 行」是 `ruff format --diff` 的**完整输出行数**（含上下文），
实际 `+/-` 内容行是 **89 / 89**（逐文件 `metadata.py` 0/0、`metadata_models.py` 121→53、
`subject_resolver.py` 94→36）。两个口径下基线与本卡都相等，结论（零新增漂移）不变。

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

**送审整改后重算（四文件，含补修的 `intelligent_parallel_models.py`，基线仍是 Z4-A `7283a8df`）：**

```
完整 diff 行数 : 基线 485 → 当前 474
+/- 内容行     : 基线 217 → 当前 213
逐行差异（含空行）: 全部 4 行都是 '<'（基线有、当前没有），'>' 计数 = 0
```

即整改后不但**零新增漂移**，还**消除了 1 处存量**——把 `group_id` 那行
单行 `description=` 改成多行括号形式后（为写下 D16 溯源的准确措辞），
ruff 不再想把那三行合并，该 hunk 消失了。

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

⚠️ **判据口径如实说明（本地编排抓到）**：上面的「新增/消除」差集是按**诊断行全文**
（`file:line:col - error: message`）做集合比较的。若本卡新引入一条与某存量诊断**逐字相同**
的错误，集合差会把它吃掉——真正承重的是并列的 **`5 errors` vs `5 errors` 条数比对**，
两者一起看才成立。（本卡的六处改动是纯字符串，不可能产生新诊断，故此风险在本卡上不实际发生。）

⚠️ **送审整改后重算，暴露出这个判据的第二个缺陷（行号位移）**：
措辞整改把 `metadata.py:125` 的 docstring 从 1 行改成 3 行，后面的行号整体 +2。
按诊断行全文比较时，同两条既有错误**同时出现在「新增」和「消除」两边**：

```
新增: metadata.py:466:34 - Arguments missing ... / metadata.py:675:40 - "open_table" ...
消除: metadata.py:464:34 - Arguments missing ... / metadata.py:673:40 - "open_table" ...
```

换成忽略行号的 key（`(file, message)`，且用 `Counter` 差以免重复条目被吞）重算：

```
条数: 基线 5 | 最终 5
忽略行号后的差集 —— 新增: 无   消除: 无
位移证据: 464→466 / 673→675（同一条，仅行号 +2）
```

**四文件最终态：零新增、零消除，全部 5 条为存量。** 判据教训：诊断差集的 key
不能含行号，否则任何插入行的改动都会制造成对的假「新增+消除」。

⚠️ **pyright 门是刚上线的（跨车道环境变更，本地编排抓到）**：`pyright-1.1.411` 由**并行车道**
装进共享 venv（`card-v5-lance/backend/.venv`），装入时间就在本卡提交前几分钟。
这解释了为什么同车道的 Z4-A 提交时该门没拦（历史上 pyright 本机缺席即跳过）。
「5 条是存量」属实，但「门本身刚活起来」这一点原先没记。

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

`lefthook.yml` 的 `pre-commit` 实际有 **7 条**命令（初版此表只列了 5 条，漏 2 条 —— 本地编排抓到）：

| 门 | 结果 | 处置 |
|---|---|---|
| `pre-commit::spec-sync-flat` | ✔️ 通过 | 照常执行；⚠️ 它自己又跑了一次 `--write` 并 stage，最终产物出自它（见上） |
| `pre-commit::spec-sync-root` | (skip) | 无匹配 staged 文件 |
| `pre-commit::ghost-files` | ✔️ 通过 | 照常执行 |
| `pre-commit::python-lint` → `ruff check` | rc=0 | — |
| `pre-commit::python-lint` → `ruff format --check` | rc=1 | **存量**（§五之二 逐行证明），绕过 |
| `pre-commit::python-typecheck` → pyright | rc=1 | **存量**（§五之三），绕过 |
| `pre-commit::cypher-vault-filter-lint` | ⚠️ **未执行** | glob `backend/app/{services,clients}/**/*.py` 在本机 lefthook 2.1.6 下匹配 **0 个文件**——`**` 需跨一级，而这两个目录下的 .py 都直接躺在第一层。本卡 staged 的 `app/services/subject_resolver.py` 正在它的声明作用域内却没被扫到。**结构性死门，既有缺陷，登记移交**（详见 §八之二） |
| `pre-commit::readme-claims-lint` | ✔️ 通过 | 照常执行 |
| `commit-msg::commitlint` | ✔️ 通过 | 照常执行 |
| `commit-msg::spec-reference` | ✔️ 通过 | ⚠️ 该门判据是 `grep -qE "(@spec:\|FR-\|PLAN-\|Co-Authored-By)"`，而系统提示强制每个 commit 都带 `Co-Authored-By` → **该门对 agent 提交恒真**。本卡不是靠 spec 引用过的，是靠这个短路过的。既有缺陷，登记移交 |

绕过用 `LEFTHOOK_EXCLUDE=python-lint,python-typecheck`。两个门被绕过前都**单独跑过、
并与 Z4-A 基线做过差集对照**——「被绕过的门会说什么」已经验过，不是盲绕。

### 五之五 送审后补做的自查（用户要求送 Codex，附带补上原先没做的扫描）

原验收单 §六.1 只写「未证明仓外消费方已适配」——**但仓内我根本也没扫**。补做如下。

**(1) 仓内有没有按裸格式解析 group_id 的消费方 → 未找到。**

```
$ grep -rn "group_id\.split\|split(':')\|split(\":\")" backend/app frontend canvas-vault scripts .claude | grep -iv test
backend/app/core/vault_scope.py:97    parts = group_id.split(":")
backend/app/core/vault_scope.py:315   seg = canon.split(":")[1] if len(canon.split(":")) >= 2 else ""
backend/app/core/vault_scope.py:526   segments = value.split(":")[1:]
backend/app/graphiti/group_id_compat.py:86 / :105   （物理化/还原，按分隔符切）
backend/app/services/review_service.py:432 / :1347
frontend/src/hooks/useRecommendations.ts:95
```

逐条核过：

| 位置 | 是否裸格式假设 | 依据 |
|---|---|---|
| `vault_scope.py:97` `_vault_segment` | **否，四段感知** | 先 `if group_id.startswith("vault:")` 再取 `parts[1]`，非 `vault:` 前缀回落 fallback |
| `vault_scope.py:315` | **否** | 同样先判 `canon.startswith("vault:")` 再取 `[1]` |
| `vault_scope.py:526` | **否，比四段更严** | 不是 `vault:` 前缀直接抛 `VaultScopeUnresolved`，且拒绝空段 |
| `group_id_compat.py:86/:105` | **否** | 逐段编解码（punycode），不假设段数 |
| `review_service.py:1347` | **无关** | 切的是 `_card_states` 的 key，而该 dict 的 key 是 `concept_id`（`canvas:concept` 两段），不是 group_id |
| `review_service.py:432` | **无关** | `topic = text.split(":")[0]`，`text` 是文本不是 group_id |
| `useRecommendations.ts:95` | **无关** | `const [nodeIdA, nodeIdB] = key.split(':')`，切的是节点对 key |

**结论：仓内未找到按裸 `<subject>:<canvas>` 解析 group_id 的消费方。** 仓外仍未证明（见 §六.1）。

**(2) `subject_resolver.py:48` 的 `>>>` doctest 示例会不会被执行 → 不会。**

```
$ cat backend/pytest.ini | head -12
[pytest]
testpaths = tests
python_files = test_*.py
...
addopts =
    -v
    --tb=short
$ grep -rn 'doctest' backend/pytest.ini backend/setup.cfg   → 无匹配（rc=1）
```

`addopts` 无 `--doctest-modules`，`testpaths = tests` 也不含 `app/`。该示例是纯文档，改它零运行时影响。

**(3) example 内部一致性 → 成立，无新矛盾。**

```
$ grep -n 'Math 54' -A 3 backend/config/subject_mapping.yaml
2:- pattern: Math 54/**
3-  subject: math54
4-  category: math
```

`canvas_path: "Math 54/离散数学.canvas"` → 映射出 `subject=math54, category=math`，与 example 里写的完全一致；
group_id 的 subject 段 `math54` ✓、canvas 段 `离散数学` ✓。
vault 段 `cs_61b` 在 `backend/config` / `.env` / `canvas-vault/.canvas-config.yaml` 里**都不存在**（grep 无输出），
确是纯中性占位。「叫 cs_61b 的 vault 里装 Math 54 的白板」不构成矛盾——vault 是**笔记库**不是课程，
一个库装多门课的白板是常态（本机 `canvas_vault` 里就同时有 Math 54 与 CS 61B）。

**(4) 更宽扫描面（docs/ / openspec/ / canvas-vault/ / frontend/）→ 契约面归零。**

`docs/` 下的 group_id 提及全是研究文档与历史记述，不是发给消费方的接口示例；
`canvas-vault/.claude/skills/quiz-answer/SKILL.md:74` 的 `cs188` 是**已弃用默认值的历史陈述**
（根 CLAUDE.md 的「已弃用格式」里列着它），不是示例；
`frontend/src/` 只有 3 处注释提到 group_id，无解析代码。

⛔ **这条原来的结论「→ 契约面归零」被本地编排 2/3 判定为「声明比证据宽」，此处更正。**
致命处在于：**这四个补扫面恰好不含 `backend/`**，而真正的残留就在 `backend/app/models/`。
本节只能支持「**这四个目录**没有对外契约面残留」，支持不了「契约面归零」。
`backend/` 侧的完整结论见 §八 E 与 §八之二。

补记两条本节当时没扫、后由完备性批判补上的面（结论均为干净，但此前**未被证明**）：
- `frontend/obsidian-plugin/src/`（活插件）对 `group_id|groupId` **0 命中**、对 `canvas-meta` **0 命中**
  —— 我原来的 `grep --include='*.py'` 对 TS/TSX 恒零命中，「穷举」名不副实；
- D16 弃用清单里的 `cs188` / `canvas-dev` **不含冒号**，冒号对形状的判据**结构上看不见它们**；
  补扫 committed `openapi.json` 中两者均 **0 命中**，`backend/app/` 的 20 处全在 migration/compat
  代码且带弃用声明（`subject_config.py:287-288`、`group_id_migration_service.py:57-58`）。

### 八 Codex 复核（用户 2026-09-05 要求送审，卡文原写「默认不送」）

命令同协议（`npx -y @openai/codex@0.153.3`，`gpt-6-astra` + `ultra`；PATH 上的 homebrew
`codex-cli 0.147.0` 不支持该模型，见 Z4-A 验收单 §十.5）。审查面 `7283a8df..a5e0ce79`。

**终审：`BLOCKER/HIGH 清零 = 是`。** 七项验证里 **A/B/C/D/消费方/门处置 全 PASS，E FAIL**。

| 项 | 裁定 | 关键证据（Codex 原文） |
|---|---|---|
| A 零逻辑改动 | **PASS** | 精确还原六处文本后三个文件 `AST_EQUAL_AFTER_EXACT_TEXT_NORMALIZATION=True（3/3）`、`DOCTEST_CODE_ASTS_EQUAL=True`；确认 `pytest.ini:8,19` 未启用源码 doctest 收集 |
| B 快照未手改 | **PASS**（附限定） | 独立 `--write` 到临时目录后比对：`JSON_DIFFERENCE_PATHS=["/info/x-generated-at"]`、`ALIGNED_BYTES_EQUAL=True`，两侧 SHA-256 相同。限定：内容相同**不能证明作者历史上从未手改** |
| C 六处→四处解释 | **PASS** | `SUBJECTINFO_SCHEMA_PRESENT=False` / `SUBJECTINFO_REFS=[]` / `SUBJECTINFO_DIRECT_ROUTE_FIELDS=[]`；`metadata.py:148` 把内部 `SubjectInfo` 转成 `CanvasMetadataResponse` |
| D 示例值分歧 | **PASS，判本卡对** | 「只把末段换成线性代数会制造输入与输出示例矛盾」；未找到 `cs_61b` 与其它字段的新矛盾（`metadata_models.py:139-143` 的请求示例本就同时写 `vault_id="cs_61b"` 与 `subject="math54"`） |
| E 全仓裸格式归零 | **FAIL** | 见下 |
| 消费方（仓内） | **PASS** | 它二次检查了 **245 个**含 group 字段的源码文件，未找到旧两段误解析。比本卡自查多找出两处四段感知点：`lib/agentic_rag/nodes.py:83-90` 取 `[2]` 当 subject、`lancedb_client.py:719-729` 先剥 `vault:` 再取首段 |
| 门处置 | **PASS**（纠正口径） | 独立复算 ruff 0.15.9 与 pyright 1.1.411：`BASELINE_MINUS_TARGET=[]` / `TARGET_MINUS_BASELINE=[]`，五条错误逐条列出 |

另复验三组测试 **81 passed rc=0**，仓库写入尝试 **0**，Neo4j 禁连账本 `blocked=0 / unaccounted=0`。

#### E FAIL —— 我的扫描判据漏网，已补修一处

⛔ **根因：我按「字面量枚举」扫，而不是按「形态」匹配。** 只 grep 了 `math54:离散数学`
与 `math54:线性代数` 两个串，于是同一个契约面上换了 subject 值的同类缺陷**必然漏掉**。

Codex 扫了 6050 个 tracked 路径 / 5550 个文本，逐处分类（它明确说「197 个命中不能当 197 个缺陷」）。逐条处置：

| 位置 | Codex 裁定 | 本卡处置 |
|---|---|---|
| `app/models/intelligent_parallel_models.py:286,287` + `openapi.json:5880,5882` | **MEDIUM／既有、本卡遗漏**：公开字段 `subject_group_id` 仍说明 `{subject}:{canvas_name}`、示例 `数学:离散数学`，而实际生成早已是 vault 格式（`intelligent_grouping_service.py:198-214`），响应入口 `intelligent_parallel.py:205` | ✅ **已补修**（见下） |
| `frontend/src/stores/chat-store.ts:625`、`frontend/sidecar/sidecar.js:503` | LOW／既有：注释把 group_id 描述为 `subject:canvasName` | ❌ 不修：前端注释，非对外契约面，且本卡硬边界是 `backend/app`；登记移交 |
| `openspec/specs/algo-memory/spec.md:13,14,15` | LOW／既有：现行主规格仍用 `数学:微积分` | ❌ 不修：OpenSpec 主规格需走 `openspec` CLI 流程改，不能手改；登记移交 |
| `api/v1/endpoints/errors.py:248`、`error_rebuild_service.py:149`、`openapi.json:20387` 的 `cs_61b:main` | 端点**明确接受并归一化 legacy 输入**，不能仅据字符串判成缺陷 | ❌ 不修（Codex 亦未判缺陷） |
| `canvas-vault/节点/UAT-2.5.X-test.md:35,63` | 既有 UAT fixture | ❌ 不修：live vault 内容，本卡硬边界禁碰 |
| 本验收单 `:65,81` | **LOW／本卡引入的证据表述问题**：两个 `math54` 字面量的筛查不足以支持未限定的「裸格式归零」 | ✅ **已改**：§二偏差 2 与 §三裁判 1 的结论收窄为「**本卡 grep 的两个字面量**归零」，并列出上表 |

**补修内容**（`intelligent_parallel_models.py:284-288`）：

⚠️ 这处**不能照搬六处的四段形态**——Codex 在 D 项专门提醒「D16 原文是 `vault:<vault_id>[:<sub>]`，
四段来自 resolver 后续组合逻辑，不能据此要求全仓合法 group_id 一律四段」。实测该字段段数**不固定**：

```
$ build_vault_group_id('default', subject_id='数学', canvas_path='离散数学')
'vault:default:数学'          ← 三段：subject_id 与 canvas_path 互斥，canvas 段被抢占
$ ContextVar 已是 vault 格式 → 原样透传
'vault:cs_61b:math54:离散数学' / 'vault:cs_61b'   ← 四段或两段，随作用域
```

故 description 改为如实说明这个可变性（而不是写死某个段数），example 取 `vault:cs_61b:数学`
（D16 原文直接给出的三段形态 `vault:<vault_id>:<subject_id>`，与同 model 的 `subject` 字段
example `["数学"]` 一致）。

**补修的回归对照**（该文件有主干既有红，必须分清归属）：

```
当前树         : 4 failed, 24 passed   （tests/unit/test_intelligent_parallel_endpoints.py）
基线 a5e0ce79  : 4 failed, 24 passed   （临时还原该文件实跑，RESTORED_IDENTICAL = True）
```

**同为 4 failed / 24 passed —— 补修零影响**；那 4 条在 Z4-A 的目录级基线（225 failed）里就有。
快照经 `--write` 重生成，`--snapshot` → `DRIFT: none`；三组核心测试仍 **81 passed**。

#### Codex 纠正的两处我方口径（都采纳）

1. **「漂移 215 行 = 215 行」口径不准。** 215 是**完整 diff 行数**（含上下文），
   实际 `+/-` 内容行是 **89 / 89**。逐文件：`metadata.py` 0/0、`metadata_models.py` 121→53、
   `subject_resolver.py` 94→36。结论（零新增漂移）不变，但 §五之二 的措辞已按此更正。
2. **D16 溯源要精确。** D16 原文是 `vault:<vault_id>[:<subject_id>]` / `[:<canvas_name>]`，
   四段是 resolver 的组合形态——**不能推广成「全仓合法 group_id 一律四段」**。
   本卡的六处 docstring 未作此声称（Z4-A 的 L1 已把措辞收紧过），补修的第七处按实测写了可变性。

### 八之二 本地对抗审查编排（与 Codex 并行，交叉验证）

用户要求送 Codex 的同时，另起了一个六维对抗编排做交叉验证：
**六维并行发现 → 每条发现由 `reproduce` / `attribution` / `materiality` 三个独立视角尝试证伪
（≥2 票证伪即杀）→ 完备性批判**。

它与 Codex **独立命中同一条最重要的遗漏**（`intelligent_parallel_models.py` 的 `subject_group_id`，
两边都判「比本卡修的六处更严重——它把裸格式写成了**规范**而不只是过期样例」），
并另外找到几条 Codex 没提的。逐条处置：

#### 本卡引入（已全部整改）

| 级别 | 发现 | 整改 |
|---|---|---|
| MEDIUM | 验收单在 `a5e0ce79` **之后**又被追加内容，审查面 `git diff 7283a8df a5e0ce79` 里看不到 | ✅ 本次一并提交 |
| LOW | §五贴的 `WROTE:` 时间戳 `23:41:22` **不是**产生提交产物那次运行（进仓的是 `23:47:48`，出自 lefthook 的 `spec-sync-flat`） | ✅ §五 已更正并说明成因 |
| LOW | `metadata_models.py:52` / `metadata.py:125` 把四段值标注为「D16 格式」——**而 Z4-A 刚专门就这一点做过精确化**，同车道前后 commit 自相矛盾 | ✅ 两处措辞改为「D16 规定 vault: 前缀；SubjectResolver 在其上再拼 canvas 段，产出四段组合形态」，与 Z4-A 对齐；快照已重生成 |
| LOW | §五之三 pyright 差集**没写明 key**，真正承重的是并列的条数比对 | ✅ §五之三 已补口径说明 |
| LOW | §五之四 门处置表漏了 3 条 pre-commit 命令 | ✅ 已补全为 7 条 + 2 条 commit-msg |

#### 既有缺陷（本卡硬边界不改，登记移交）

| 级别 | 位置 | 内容 |
|---|---|---|
| **HIGH** | `lefthook.yml:165-166` | `cypher-vault-filter-lint` 是**结构性死门**：glob `backend/app/{services,clients}/**/*.py` 在本机 lefthook 2.1.6 下匹配 **0 个文件**（`**` 需跨一级，而这两个目录的 .py 都在第一层）。本卡 staged 的 `app/services/subject_resolver.py` 正在其声明作用域内却从未被扫到 |
| MEDIUM | `lefthook.yml:238` | `spec-reference` 门被 `Co-Authored-By` **恒真短路**：判据是 `grep -qE "(@spec:\|FR-\|PLAN-\|Co-Authored-By)"`，而系统提示强制每个 agent commit 都带该 trailer → 该门对 agent 提交从不生效 |
| **MEDIUM** | `app/core/subject_config.py:349-355` | `canonical_group_id` 对裸格式**静默升格且归错段**：`math54:离散数学` → `vault:math54:离散数学`，**把 subject 当成了 vault 段**。仓内没有任何一处会*拒绝*裸两段 group_id |
| MEDIUM | `backend/tests/unit/grouping/test_analyze_canvas.py:123,141` | 仓内唯一按裸两段断言 group_id 的消费方，且**当前是红的**——与 Z4-A 清的 12 条**同根因（D16 格式演进）但不在 Z4-A 清单内**。它就在 Z4-A 目录级基线那 213 failed 的 `tests/unit/grouping ×2` 里。**本卡实测证据链闭合**，见下 |
| LOW | `frontend/sidecar/sidecar.js:503` | 注释仍把 group_id 描述为 `subject:canvasName` 并称默认回落 `cs188`；我的补扫只扫了 `frontend/src/`，**漏了 `frontend/sidecar/`** |
| LOW | `PRD.md:142` | 仓根 PRD 仍以验收标准口吻规定 group_id = 白板名归一化（`CS 188` → `cs188`），与 D16 冲突且无「已被取代」声明。PRD 是锚定只读文档，禁改 |
| LOW | `_archive/.../obsidian-plugin/src/views/CanvasInfoView.ts:10` | 归档插件**逐字镜像**了本卡修掉的那句 `Group ID for Graphiti (e.g., "math54:离散数学")` |
| LOW | `api/v1/endpoints/errors.py:248`、`error_rebuild_service.py:149` | OpenAPI 上仍把根 CLAUDE.md 明列为「已弃用」的 `cs_61b:main` 当 group_id 示例（Codex 判该端点确实接受并归一化 legacy 输入，不算安全缺陷） |
| LOW | `openspec/specs/algo-memory/spec.md:13-15` | 主 spec 用 `数学:微积分`；但该 scenario 讲 per-group 缓存隔离，group_id 在此是不透明键（下一个 scenario 直接用 "A"/"B"），并未主张格式 |
| LOW | `subject_resolver.py:44-49` | 卡文与本验收单称其为「doctest 风格示例」，但它**不是合法 doctest**（期望输出写成同行注释而非下一行）；即使启用 `--doctest-modules`，改前改后一样会失败 |
| LOW | 共享 venv | `pyright-1.1.411` 由**并行车道**在本卡提交前几分钟才装进共享 venv——该门是**刚活起来**的（已记入 §五之三） |

#### ⚠️ 文档 / 测试 / 实现三方分裂——就在本卡补修的那个字段上

补修 `subject_group_id` 时顺手实跑了锁它的那两条测试，三方值**互不相同**：

```
$ pytest -q tests/unit/grouping/test_analyze_canvas.py
    assert result.subject_group_id == "数学:离散数学"
E   AssertionError: assert 'vault:default:数学' == '数学:离散数学'
    assert result.subject_group_id == "物理:力学"
E   AssertionError: assert 'vault:default:物理' == '物理:力学'
2 failed, 5 passed
```

| 面 | 值 | 状态 |
|---|---|---|
| **实现** `intelligent_grouping_service.py:202-214` | `vault:default:数学` | 现行正确（与本卡独立实测的 `build_vault_group_id('default', subject_id='数学', canvas_path='离散数学')` 输出逐字相同） |
| **文档** `intelligent_parallel_models.py:286` | 曾写 `{subject}:{canvas_name}` / `数学:离散数学` | ✅ **本卡已修** |
| **测试** `test_analyze_canvas.py:123,141` | 仍期望 `数学:离散数学` | ❌ **仍红，本卡不修** |

不修的理由：Z4-B 的完成条件是**契约面示例**、硬边界是「只改字符串字面量与 docstring」；
在本次整改里改测试断言会把不相关变更混进 diff。**登记移交**。

⚠️ **我先前把这条归因为「Z4-A 漏改」，被三视角验证 2/3 证伪，此处撤回。**
归属视角实测：`git show 7283a8df --name-only | grep -c analyze_canvas` = **0**，
`git diff --stat 304f03ca a5e0ce79 -- backend/tests/unit/grouping/ …` **输出为空** ——
从主干 HEAD 到本车道 tip，这一族一个字节都没动。Z4-A 的卡文范围是主 session 点名的文件
（从来不含 `tests/unit/grouping/`），且 Z4-A 自己的验收单 §六 已明确登记
「本卡只交付这一族 12 条清零，其余 213 条需独立排卡」——**它没有谎报清零**。
正确归属：**主干既有债**（早于 D16 的 Story 33.4 遗留）。

保留的教训只针对**排卡侧**：同根因的红若按文件清单分派，会分散在多张卡之间。
这与本卡「按字面量枚举扫描」是相似的判据形态，但**不是同一个责任主体**。

#### 完备性批判独有的两条（Codex 与六维都没碰）

**(1) 示例 vault 段的争议 —— 事实采纳，结论不采纳（附裁定依据）。**

批判指出：契约写 `vault:cs_61b:math54:离散数学`，而本机实测产出是 `vault:canvas_vault:...`；
并援引同车道 Z4-A 11 分钟前刚立的「vault 段用哨兵动态组装、禁硬编码仓内 vault 字面量」规矩，
判 `introduced_by_card=true` / HIGH。

**事实核实：属实。** 本卡实跑 `SubjectResolver().resolve('Math 54/离散数学.canvas')`
→ `'vault:canvas_vault:math54:离散数学'`。

**结论不采纳，三条硬证据：**

1. **`cs_61b` 正是 D16 规约自己的官方举例。** 根 `CLAUDE.md:34-36` 的三条格式定义
   **全部**用 `vault:cs_61b:...`（`vault:cs_61b` / `vault:cs_61b:algorithms` /
   `vault:cs_61b:admissibility`）；`subject_config.py:230,238-243` 的
   `build_vault_group_id` docstring 同样用 `cs_61b`。契约示例与规约原文举例一致。
2. **`vault_id` 是部署期变量，契约示例只能用占位。** 写本机的 `canvas_vault` 反而更糟 ——
   那是**这台机器**的 vault 名，别的部署照抄即错。卡文 (a) 明确要求「不写本机 `canvas_vault`」
   正是此意。契约面上不存在「唯一正确的 vault 值」。
3. **Z4-A 那条规矩的射程是测试断言，不是契约示例。** 断言硬编码本机 vault ⇒ 换环境即红，
   那正是 Z4-A 修的那批红的根因（`test_group_id_format_*` 三条）。契约示例不是断言，
   不会因环境变化而红。批判把两个场景混同了。

**但它的改进方向有价值，已采纳**：契约示例里混入部署期变量时应当**明说它是占位**。
两处 description 已补上「示例中的 vault 段是**部署期变量占位符**（取自 `get_current_vault_id()`），
实际值随部署而变 — 勿按字面值硬编码」，快照已重生成（`DRIFT: none`，81 passed）。

**(2) ⛔ CI 与本地解释器版本不一致 —— 本卡唯一可能真炸的地方，且未验证。**

```
$ grep -n 'PYTHON_VERSION' .github/workflows/api-spec-sync.yml
50:  PYTHON_VERSION: '3.11'
$ backend/.venv/bin/python -V
Python 3.14.4
```

本卡关于「快照生成确定性」的全部证据（本方的 `--snapshot DRIFT: none`、
Codex 的 `ALIGNED_BYTES_EQUAL=True` / 同一 SHA-256）都是**同一解释器两次运行**得出的，
**不覆盖跨版本**。pydantic / FastAPI 的 JSON schema 输出在 Python 版本间可能不同 ⇒
存在「本地 `DRIFT: none` 而 CI 漂移门红」的可能。

本卡**未验证**（本机无 3.11 环境；装一个会影响共享 venv 与并行车道）。
`.github/workflows/api-spec-sync.yml` 的 `paths` 同时含 `backend/app/models/**` 与
`backend/openapi.json` ⇒ **本卡必然触发它**，其中的 oasdiff 破坏性变更检测同样未跑。
登记为未证明项（§六.6）与移交项。

**(3) 审查面在审查期间被并发修改（流程缺陷，登记）。** 六维与 critic 跑的是 `a5e0ce79`，
而我在它们跑的同时就在工作树上做整改（补修 + 措辞）。多个 agent 都独立观察到了这一点并
明确声明「结论取自 committed 态 `git show`，未受工作树漂移影响」——它们处理得对，
但**下次应当先冻结审查面再派审**，否则按其命令复算的人会得到不同数字。

#### ⚠️ 一条完整的风险链（两条既有缺陷咬合，值得单独排卡）

`canonical_group_id` 把裸格式的 subject 段当 vault 段（`math54:离散数学` → `vault:math54:离散数学`），
而归档插件确实逐字抄过本卡修掉的那句裸格式文案。即：
**文档教消费方用裸格式 → 消费方回传 → 被静默归进一个不存在的「math54 vault」，数据落到错误作用域。**
这不是假想的传播路径，`_archive/.../CanvasInfoView.ts:10` 就是实证。
本卡修掉了链条的第一环（文档），**第二环（静默升格）与仓外已适配情况仍未处理**。

### 六 本卡未证明什么

1. **未证明仓外消费方已适配。**（⚠️ 原写的是「未证明消费方」——**仓内**部分已于送审时补扫，
   见 §五之五(1)：未找到按裸格式解析 group_id 的仓内消费方。这里收窄为**仓外**。）
   本卡只改了后端发出去的**说明书**，没有也无法证明 Obsidian 插件 / 任何第三方调用方
   已经按 D16 四段格式解析 `group_id`。
   ⚠️ **送审后这条风险从「假想」变成「有实证」**：归档插件
   `_archive/canvas-progress-tracker/obsidian-plugin/src/views/CanvasInfoView.ts:10`
   **逐字镜像**了本卡修掉的那句 `Group ID for Graphiti (e.g., "math54:离散数学")` ——
   证明该文案确实传播到过消费方侧。（活插件 `frontend/obsidian-plugin/src/` 已无此问题。）

   更糟的是回传路径：`app/core/subject_config.py:349-355` 的 `canonical_group_id`
   对裸格式**静默升格且归错段** —— `math54:离散数学` → `vault:math54:离散数学`，
   **把 subject 当成了 vault 段**；仓内没有任何一处会*拒绝*裸两段 group_id。
   即：文档教消费方用裸格式 → 消费方回传 → 数据被静默归进一个不存在的「math54 vault」。

   **实际返回值早就是四段了**（D16 于 2026-05-05 落地），所以本卡不新增该风险，
   只是修掉了链条第一环（文档）。**第二环（静默升格）与仓外已适配情况仍未处理**，
   建议独立卡：消费方侧扫描 + 给 `canonical_group_id` 的裸格式分支加显式拒绝或告警。
2. **未证明 `cs_61b` 这个示例 vault 段对读者最优。** 它只是一个中性占位（避免写本机
   `canvas_vault`），并非真实存在的 vault。
3. **~~未送 Codex~~ → 已送**（卡文默认不送，用户 2026-09-05 明确要求送）。
   结果见 §八；同时并行跑了一个本地六维对抗审查编排做交叉验证。
4. **~~未验证 lefthook 的两条 spec-sync 命令~~ → 部分已验**：送审时实测发现
   `spec-sync-flat` 确实会在 commit 时二次执行 `--write` 并 `git add`（§五 已据此更正证据），
   `spec-sync-root` 因无匹配 staged 文件而 skip。仍**未**构造「快照过期」场景验证它们会拦。
   另外送审查出 `cypher-vault-filter-lint` 与 `spec-reference` 两道门**实测从不生效**（§八之二）。
6. **未证明快照在 CI 的 Python 3.11 下不漂移。** 本卡与 Codex 的生成确定性证据都出自
   本地 Python 3.14.4 的两次运行，CI（`api-spec-sync.yml:50`）用 3.11。见 §八之二(2)。
   同一 workflow 的 oasdiff 破坏性变更检测也未跑。**这是本卡唯一可能在 CI 真炸的地方。**
7. **未证明本次送审整改本身没有引入新问题**：Codex 与本地编排审的都是 `a5e0ce79`，
   而补修（第 7 处契约面）与措辞整改都发生在**它们出结论之后**，未再经复审。
   整改的承重来自本卡自跑的门对照（ruff / pyright / 三组测试 / 快照 `DRIFT: none`）
   与补修处的基线回归（4 failed = 4 failed）。

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
6. **本卡补修（超出卡文枚举的「六处」，Codex 发现）**：
   `app/models/intelligent_parallel_models.py:284-288` 的公开字段 `subject_group_id`
   —— description 从 `{subject}:{canvas_name}` 改为 D16 vault: 格式并如实写明段数可变，
   example 从 `数学:离散数学` 改为 `vault:cs_61b:数学`。属卡文 (d)「全仓复扫裸格式示例归零」射程内。
7. **移交（Codex 判 LOW／既有，本卡按硬边界不修）**：
   - `frontend/src/stores/chat-store.ts:625`、`frontend/sidecar/sidecar.js:503` —— 注释仍把
     group_id 描述为 `subject:canvasName`（前端注释，非对外契约面；本卡硬边界只到 `backend/app`）；
   - `openspec/specs/algo-memory/spec.md:13,14,15` —— 现行主规格仍用 `数学:微积分`
     （需走 `openspec` CLI 流程改，禁手改）；
   - `canvas-vault/节点/UAT-2.5.X-test.md:35,63` —— live vault 内的 UAT fixture，本卡硬边界禁碰。
8. **判据教训（写给后续卡）**：契约面示例的复扫**必须按形态匹配，不能按字面量枚举**。
   本卡只 grep 了 `math54:` 两个串就宣称「裸格式归零」，Codex 按形态全仓扫（6050 路径 / 5550 文本）
   立刻找出同类遗漏。正确判据形如
   `grep -rnE '"[^":]+:[^":/ ]+"' <契约面文件> | grep -v 'vault:'` 再逐处人判，
   而不是枚举已知的 subject 值。
9. **Codex 的两条口径纠正（已采纳）**：
   - `ruff format --diff` 的「215 行」是完整输出行数，实际 `+/-` 内容行是 89/89；
   - D16 原文只到 `vault:<vault_id>[:<subject_id>]`，四段是 resolver 组合形态，
     **不能推广成「全仓合法 group_id 一律四段」**（补修的第七处正因此写的是段数可变）。
