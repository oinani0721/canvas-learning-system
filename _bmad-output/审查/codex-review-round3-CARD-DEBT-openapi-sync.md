终裁：**FAIL**。`94b0c43b` 修复了 Round‑2 点名窄例，但新引入/遗留 **2 个 BLOCKER、1 个 HIGH、1 个 MEDIUM**；23 个门测试全绿不能支持收官。

| 验证项 | 裁决 | 关键复现 |
|---|---|---|
| B1 语境切分 | **FAIL / BLOCKER + HIGH** | 点名反例已修，但合法 OpenAPI 仍可假绿/误红 |
| B3 双命令 | **FAIL / BLOCKER** | PID tmp、覆盖集、失败传播均通过；双 job 的 `git add` 仍争抢 index lock |
| oasdiff 非数组 | **PASS** | `{}` → `PARSE_ERROR` → exit 1 |
| 隐私 | **PARTIAL / MEDIUM** | raw stderr 已删除且摘录安全；新增报告/提示词仍有 16 处未脱敏 home 路径 |
| 回归门 | **PASS** | 23 passed、负控 PASS、DRIFT none |
| 禁改面 | **PASS** | `FORBIDDEN_COUNT=0` |

### 1. B1 — FAIL

实现位于 [check-openapi-drift.py:127](<repo>/scripts/spec-tools/check-openapi-drift.py:127) 和 [check-openapi-drift.py:142](<repo>/scripts/spec-tools/check-openapi-drift.py:142)。

- a) enum + `type/properties` 反例：**PASS**，`clean=False, details=2`。
- b) default、enum 多层数组：**PASS**，均 `clean=False`；数组穿透在 `:170` 生效。
- c) 普通 Schema required 反序：**PASS**，`clean=True`。
- d) 真实快照：**PASS**：

```text
required_string_arrays=281
value_context_required=0
old_vs_new_equal=True
```

- e) **找到规范内反例 / BLOCKER**：

```text
x_extension parent_clean=False head_clean=True
Link requestBody literal required 反序: head clean=True
```

OpenAPI 3.1 明确允许 Schema 任意属性/扩展值，以及 Link `requestBody`、`parameters` 中的任意字面值；其内部 `required` 数组属于数据，不能排序。[Schema Object](https://spec.openapis.org/oas/v3.1.0.html#schema-object)、[Specification Extensions](https://spec.openapis.org/oas/v3.1.0.html#specification-extensions)、[Link Object](https://spec.openapis.org/oas/v3.1.0.html#link-object)

另有 **HIGH 反向误判**：合法 Schema 属性名若叫 `enum/const/default/example/examples/value`，其 Schema 子树被错误标为实例数据，required 反序全部误报漂移：

```text
properties.value schema parent_clean=True head_clean=False
```

当前快照已经存在 `properties.value`，[backend/openapi.json:474](<repo>/backend/openapi.json:474)，只是目前为标量，尚未触发。

### 2. B3 — FAIL

- PID tmp：**PASS**。[check-openapi-drift.py:303](<repo>/scripts/spec-tools/check-openapi-drift.py:303)

```text
8 processes: CHILD_FAILURES=0
JSON_VALID=1
RESIDUAL_TMP=0
```

- 覆盖集：**PASS**。[lefthook.yml:46](<repo>/lefthook.yml:46)、[lefthook.yml:57](<repo>/lefthook.yml:57)

```text
FLAT=85 ROOT=2 INTERSECTION=0 UNION=87
MISSING=0 EXTRA=0
```

- `git add || exit 1`：**PASS**，见 `:55`、`:66`；预置 index lock 时退出 1。

但 [lefthook.yml:16](<repo>/lefthook.yml:16) 仍为 `parallel: true`。一次 commit 同时修改 flat 文件和 `main.py` 时，两条命令仍会并发 `git add backend/openapi.json`：

```text
同步双 git-add: COLLISION_ROUNDS=100/100
真实 --write && git add: 4/4 每对一个失败
实际 Lefthook 入口四轮 rc: 1 1 0 1
失败原因: .git/index.lock already exists
```

因此“文件覆盖集零重叠”并不等于“两条 job 互斥”，正常提交仍会被误阻断，判 **BLOCKER**。

### 3. MEDIUM 与回归面

- oasdiff：**PASS**。[workflow:214](<repo>/.github/workflows/api-spec-sync.yml:214)

```text
input={}
BREAKING_COUNT=PARSE_ERROR
selected-branch=exit-1
rc=1
```

- stderr 替换窄项：**PASS**。父提交 raw blob 为 545,951 bytes/7,384 行，HEAD 已不存在；两份脱色摘录各 81 行，无真实用户名路径、session UUID、secret 或 ANSI。
- commit 整体隐私：**PARTIAL / MEDIUM**。新增 [Round‑2 报告:14](<repo>/_bmad-output/审查/codex-review-round2-CARD-DEBT-openapi-sync.md:14) 仍有 15 处、[Round‑2 提示词:4](<repo>/_bmad-output/审查/prompts/codex-prompt-round2-CARD-DEBT-openapi-sync.md:4) 仍有 1 处未脱敏 user-home 绝对路径。
- 回归：**PASS**：

```text
23 passed, 10 warnings in 0.84s
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0
NEGATIVE-CONTROL: PASS
DRIFT: none (paths=192 schemas=353)
FORBIDDEN_COUNT=0, TOTAL_CHANGED=11
```

新增 LOW：

- [check-openapi-drift.py:171](<repo>/scripts/spec-tools/check-openapi-drift.py:171) 是不可达旧 `return`。
- `git diff --check 94b0c43b^ 94b0c43b` 仍 exit 2：Round‑2 报告 EOF 多余空行。

未运行 GitHub Actions；未使用 TestClient、7691/7687。tracked/cached diff 均为空，开场已有的 3 个 untracked 审查文件未读取或修改。

BLOCKER/HIGH 清零: 否


