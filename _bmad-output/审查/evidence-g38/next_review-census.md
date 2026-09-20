# CARD-G3-8 — `next_review` 读/写 census（只读，14 文件 / 63 行）

> **批次**：`[BATCH-2026-09-18-第十五批 / CARD-G3-8]` · 车道 `card-p4-fsrs` · 分支 `card/p4-fsrs`
> **勘探基准**：`PREV = 49e426263caa0356e8c947c701e206efb11ae97f`（P4-A `CARD-CARD-STATES-ATOMIC-WRITE` 末 commit）
> **命令**：`rg -c next_review backend/app | sort` → **14 行**；逐文件计数之和 = **63**
> ⛔ **本 census 面的 14 个文件本卡零改动**（含注释）。地盘门实测见验收单 §(l)。

---

## 一 三公式并存（对账的根因）

同一个 concept 的「下次该什么时候复习」，在系统里由**三个互不相同的公式**各自算了一份。
D0 T1（`docs/fsrs-truth-source-d0-revision.md:10/:45`）裁定 frontmatter `fsrs_due` 为唯一真相源之后，
另外两个既没有退役，也从未与真相源对过账。

| # | 公式 | 写点 / 派生点 | 形态 | 与 FSRS 调度的关系 |
|---|---|---|---|---|
| ① | **frontmatter `fsrs_due`** = FSRS 库算出的 `card.due` | `canvas-vault/.claude/scripts/fsrs_bridge.py:329` `"fsrs_due": _iso(card.due)` | 整秒 UTC-Z 字符串（schema v1 `docs/learning-events-schema-v1.md:324`） | **就是** FSRS 调度结果 = 真相源 |
| ② | **Neo4j `LEARNED` 边固定 +1 天** | `backend/app/clients/neo4j_client.py:1034` `r.next_review = datetime() + duration('P1D')`<br>重放侧同式 `backend/app/services/fallback_sync_service.py:774`<br>JSON 镜像同式 `neo4j_client.py:718` → `:734`/`:745` | Cypher `datetime`（带微秒）/ JSON 里是 **naive 本地** ISO | **完全无关**：无论 FSRS 算出 3 天还是 90 天，一律写「明天」 |
| ③ | **`last_interaction_ts + stability 天`** | `backend/app/services/learning_context_service.py:96-102` → `result["next_review"]` | ISO 字符串，**不落盘**（读时派生） | 借用 FSRS 的 stability，但**不是** FSRS 的调度公式 |

**现网活体证据（2026-09-19 只读实测）**：live vault 全库唯一同时含两个字段的节点
`canvas-vault/节点/csm-tutoring-unit-credit.md`：

```
:8   fsrs_due: 2026-08-11T13:56:58Z     ← ① 真相源
:19  next_review: 2026-04-21            ← 与 ① 相差约 112 天
```

命令：`grep -rl '^fsrs_due:' "$LV" --include='*.md' | wc -l` → `1`；`grep -rl '^next_review:' …` → `1`（同一个文件）。

> ⚠️ vault 侧脚本对 frontmatter 字段 `next_review` **零写者**：`rg -c next_review canvas-vault/.claude` 命中 0 文件。
> 即该字段是**历史遗留**，没有任何现存写方在维护它，而 `board_manifest_service.py:645` 仍在读它。

---

## 二 逐文件逐行 census（63 行）

分类口径：**写方**（把值落到存储）/ **读方**（从存储取值投影给消费方）/ **派生公式**（读时算一个新值）/ **模型字段**（Pydantic/dataclass 声明与透传）/ **文档注释**（docstring、注释、示例）。

### 2.1 `backend/app/clients/neo4j_client.py`（17 行）

| 行 | 类 | 语义 |
|---|---|---|
| `:663` | 读方（路由） | JSON 兜底派发：`"MATCH"+"LEARNED"+"next_review"` ⇒ 走 review 分支 |
| `:718` | **写方** | `next_review = now + timedelta(days=1)` —— 公式 ②，`now` 是 **naive 本地** |
| `:734` | **写方** | 更新既有关系：`rel["next_review"] = next_review.isoformat()` |
| `:745` | **写方** | 新建关系：`"next_review": next_review.isoformat()` |
| `:762` | 文档注释 | docstring 描述 `WHERE r.next_review < datetime()` |
| `:763` | 文档注释 | docstring 描述 `ORDER BY r.next_review` |
| `:804` | 读方 | `next_review_str = rel.get("next_review")`（JSON 分支） |
| `:805` | 读方 | 空值短路 |
| `:807` | 读方 | `datetime.fromisoformat(next_review_str)` |
| `:808` | 读方 | `if next_review < now:` —— `now` 是 **naive** `datetime.now()`（:794） |
| `:831` | 读方 | 投影成 `"due_date": next_review.isoformat()` |
| `:863` | 文档注释 | 注释说明派发条件 |
| `:1034` | **写方** | `r.next_review = datetime() + duration('P1D')` —— 公式 ② 的**主写点** |
| `:1122` | 读方 | Cypher `WHERE r.next_review < datetime()` |
| `:1129` | 读方 | `r.next_review as due_date` |
| `:1130` | 读方 | `ORDER BY r.next_review` |
| `:2471` | 文档注释 | docstring 列 JSON 行字段 |

> **⛔ 已知下游后果（本卡显形、不修）**：`:808` 拿 **naive** 的 `datetime.now()` 与 `:807` 解析出的值比大小。
> 若把整秒 UTC-Z（**tz-aware**）写进 JSON 镜像，该比较抛 `TypeError`，被 `:834` 的
> `except (ValueError, TypeError): continue` **静默跳过** —— 该 concept 会从 JSON 降级路径的复习建议里消失。
> 本机 Python 3.14.4 实测：`datetime.fromisoformat('2026-09-20T03:00:00Z') < datetime.now()` →
> `TypeError: can't compare offset-naive and offset-aware datetimes`。
> 修读方属 **P1/P2 地盘**，不在本卡范围；迁移器把它做成报告里的 `warnings[].code = W-JSON-MIRROR-AWARE-READER`，
> 并由单测 `test_report_warns_about_json_mirror_aware_reader` 锁住「必须显形」。

### 2.2 `backend/app/api/v1/endpoints/review.py`（10 行）

| 行 | 类 | 语义 |
|---|---|---|
| `:1137` | 文档注释 | 注释说明 service 返回 `next_review` |
| `:1139` | 读方 | `result.get("next_review") or result.get("next_review_date")` |
| `:1140` | 读方 | 串形态判定 |
| `:1141` | 读方 | `date.fromisoformat(next_review_raw[:10])` —— **截断到日**，丢掉时分秒 |
| `:1142` | 读方 | `date` 类型分支 |
| `:1143` | 读方 | 直接取用 |
| `:1145` | **派生公式** | 兜底 `date.today() + timedelta(days=interval)` |
| `:1148` | 读方 | 投影成 `next_review_date=` |
| `:1158` | 文档注释 | 分歧时由 `degraded_reason` 说明 |
| `:1185` | **派生公式** | 降级分支 `date.today() + timedelta(days=interval)` |

### 2.3 `backend/app/services/learning_context_service.py`（9 行）

| 行 | 类 | 语义 |
|---|---|---|
| `:10` | 文档注释 | 模块 docstring 列 MasteryStore 字段 |
| `:58` | 模型字段 | 空 mastery 骨架 `"next_review": None` |
| `:75` | 文档注释 | 返回值 docstring |
| `:82` | 模型字段 | 结果骨架初值 |
| `:102` | **派生公式** | 公式 ③ 的落点：`result["next_review"] = next_dt.isoformat()`（`next_dt` 由 `:99-101` 的 `last_interaction_ts + timedelta(days=fsrs_stability)` 算出） |
| `:339` | 读方 | 透传 `mastery_data["next_review"]` |
| `:472` | 读方 | 存在性判断 |
| `:475` | 读方 | `datetime.fromisoformat(mastery["next_review"])` |
| `:478` | 读方 | 渲染「- 下次复习: …」 |

> ⚠️ 逐行核对：`rg -n` 对该文件的 9 处命中是 `:10 :58 :75 :82 :102 :339 :472 :475 :478`。
> 公式 ③ 的**算式**在 `:99-101`，那三行本身不含 `next_review` 字面量、因而不在 census 计数内；
> 落点 `:102` 才是命中行。上表逐行与该命中集一一对应。

### 2.4 `backend/app/services/review_service.py`（6 行，**P4-A 地盘，本卡只读**）

| 行 | 类 | 语义 |
|---|---|---|
| `:1658` | 文档注释 | docstring：`next_review` 是 ISO 时间戳 |
| `:1744` | 文档注释 | G3-7 裁定 ①「**不覆盖** next_review」 |
| `:1824` | 读方/投影 | `"next_review": due_date.isoformat()` —— 来自 FSRS `due_date`，**与真相源同款公式** |
| `:1880` | 文档注释 | Story 32.9 AC-1 注释 |
| `:1882` | **派生公式** | `now_utc + timedelta(days=interval)`（降级路径） |
| `:1888` | 读方/投影 | `"next_review": next_review_date.isoformat()` |

### 2.5 `backend/app/api/v1/endpoints/mastery.py`（5 行）

| 行 | 类 | 语义 |
|---|---|---|
| `:210` | 文档注释 | 端点 docstring |
| `:239` | 模型字段 | `fsrs_next_review = None` 初值 |
| `:246` | 读方 | 从 FSRS card `due` 取值 |
| `:248` | 读方 | `due.isoformat()` |
| `:258` | 读方 | 投影成 `"fsrs_next_review"` |

### 2.6 `backend/app/services/memory_service.py`（4 行，全部文档注释）

`:1098` / `:1101` / `:1103` / `:1192` —— 均为 docstring 描述「查 `next_review` 已过的概念 / `ORDER BY next_review` / `SET r.next_review`」，**无代码写点**。

### 2.7 模型与透传（共 10 行）

| 文件:行 | 类 | 语义 |
|---|---|---|
| `models/snapshot_v3.py:31` | 文档注释 | docstring 列字段名 |
| `models/snapshot_v3.py:318` | 模型字段 | 恒 `"next_review": None` |
| `models/schemas.py:1029` | 模型字段 | `next_review_date: date = Field(...)` |
| `models/schemas.py:1063` | 文档注释 | Field 描述文案 |
| `models/board_manifest.py:125` | 模型字段 | `next_review: str \| None = None` |
| `mcp/tools/mastery_tools.py:108` | 模型字段 | `next_review: Optional[str] = None` |
| `api/v1/endpoints/mastery_ws.py:22` | 文档注释 | 示例 payload |
| `api/v1/endpoints/mastery_ws.py:130` | 读方 | 透传 `payload.get("fsrs_next_review")` |
| `api/v1/endpoints/context.py:12` | 文档注释 | 模块 docstring |
| `api/v1/endpoints/context.py:43` | 模型字段 | `next_review: str \| None = None` |

### 2.8 `backend/app/services/board_manifest_service.py`（1 行）

`:645` `"next_review": _iso(fm.get("next_review"))` —— **读 frontmatter 字段 `next_review`**（不是 `fsrs_due`）。
vault 侧对该字段零写者，现网全库仅 1 个文件有它、且与 `fsrs_due` 相差约 112 天 ⇒ **疑似死读 / 字段并存**，登记待裁（§三.4）。

### 2.9 `backend/app/services/fallback_sync_service.py`（1 行）

`:774` `r.next_review = CASE WHEN should_update THEN datetime($ts) + duration('P1D') …` —— 公式 ② 的重放侧同式写方。

---

## 三 残余写方清单（本卡**不改**，只登记为移交项）

| # | 写点 | 公式 | 本卡处置 | 移交给 |
|---|---|---|---|---|
| 1 | `neo4j_client.py:1034` | ② 固定 `P1D` | **不改**、不退役 | P1 `C1-14` 或后续 G3 卡 |
| 2 | `neo4j_client.py:718` → `:734`/`:745`（JSON 镜像） | ② 固定 +1 天（naive 本地） | **不改** | P1 `C1-14` |
| 3 | `fallback_sync_service.py:774` | ② 重放侧同式 | **不改** | P2 `REPLAY-REWRITE` |
| 4 | `learning_context_service.py:96-102` | ③ `stability` 天派生（不落盘） | **不改** | P8 `C2-13` census |

> ⛔ **对账是快照，不是不变量**：这四处写方在本卡之后**依然存在**。
> apply 之后只要用户再评一次分，`neo4j_client.py:1034` 就会把「明天」重新写回那条边，
> 分歧立刻复发。「让真相源成为唯一写方」是退役这四处写方之后才成立的性质，
> 本卡**没有证明**它（见验收单「本卡未证明什么」①④）。

---

## 四 身份映射：节点文件 stem ↔ `Concept.name`

**契约来源**：`openspec/specs/concept-identity/spec.md`（P4-A 刚落断言，本卡只引用不改）。

**写侧身份键**（`neo4j_client.py:1030-1032`）：

```cypher
MERGE (c:Concept {name: $concept, group_id: $groupId})
MERGE (u)-[r:LEARNED {group_id: $groupId}]->(c)
```

即 Concept 的身份是 `(name, group_id)` 复合键，**从不落 `c.id`**（W1 契约；`cypher-write-contract.md` §W1 #1 已由 G2-3 修复为复合键）。
JSON 镜像侧的行身份是 `(user_id, concept_name, group_id)` 三元组（`neo4j_client.py:721-726`）。

**frontmatter 侧身份**：节点文件 basename（stem），由 `frontmatter_signals._node_md_path`（`:33-40`）按
`_NODE_DIR_PREFIXES = ("节点", "原白板")` 的顺序解析。

**迁移器如何对齐这两侧**：
1. `--vault-dir` 下扫 `节点/*.md` 与 `原白板/*.md`，`concept_key = path.stem`；
   同 stem 在两个目录都出现时取 `节点/` 那份（与 `_node_md_path` **同序**），
   被遮蔽的那份写进报告的 `shadowed[]`，⛔ 不静默丢弃。
2. 目标侧按 `--group-id`（**等值**过滤，不是前缀 —— 这是写身份面 W1，不是读召回面 R4）
   取 `LEARNED` 边；Cypher 对 `c` 与 `r` **两个 alias 都过滤**（R1 全覆盖）。
3. 两侧做**并集**枚举，映射不上的**两个方向都显形**：
   - `unmatched_no_target` —— **有效 due** 的 governed 节点在目标侧找不到边；
   - `unmatched_no_frontmatter` —— 目标侧的边没有任何 `.md` 载体。

   ⛔ 单向枚举会漏掉另一半孤儿数据，「对账」就不成立。

   > ⚠️ **口径精确化（Codex r1 MEDIUM-10 整改）**：上面两个计数按 `action` 互斥。
   > 一个 `fsrs_due` 坏掉／读不出的 governed 节点，其 `action` 是 `malformed_fsrs_due`，
   > **不会**同时进 `unmatched_no_target` —— 若只看这两个计数，「它在目标侧也没有边」
   > 这件事会被节点自身的毛病盖掉。因此每一行都另带一个与 `action` **正交**的布尔
   > `target_missing`，并汇总成 `counts.rows_without_target`：身份没对上永远看得见，
   > 不论该行因为什么原因不写。

**vault ↔ group 绑定（Codex r1 BLOCKER-1 整改）**：形态校验只能证明 `--group-id` *长得像*
一个物理组名，**证明不了它属于这个 vault** —— `--vault-dir A --group-id vault__B` 两个参数
各自都合法，合起来却把 A 的 `fsrs_due` 写进 B 的边。传错组是跨 vault 写的唯一入口，因此：

- 迁移器读 `<vault>/.canvas-config.yaml` 的 `vault_id`（round-11 扁平架构固化的 vault 自报身份载体，
  纯 stdlib 正则读单字段，不引 PyYAML），要求 `--group-id` == `vault__<vault_id>`
  或以 `vault__<vault_id>__` 开头（D16 的 vault 内二级作用域）；
- 读不到 `vault_id`、或 `vault_id` 不是纯 ASCII 形态（物理化含 punycode，属 app 侧能力，
  本脚本零 app 导入 ⇒ **算不出**物理组名）⇒ **fail-closed 拒绝**，要放行必须显式
  `--allow-unbound-vault`，而不是默默当成「验过了」；
- `--apply` 另可用 `--from-report` 断言与 dry-run 同组；`--rollback` 的绑定靠 pre-image
  自带的 `group_id` + `target_path` / `target_uri`（拒绝把一份备份还原到别的目标上）。

**仍未证明的部分**：`.canvas-config.yaml` 自报的 `vault_id` 与该目录**真实**归属是否一致 ——
本闸证明的是「调用方给的组名与 vault 自己说的名字对得上」，不是「vault 没有谎报」。

---

## 五 `rg` 原始输出（判据自证）

```
$ rg -c next_review backend/app | sort
backend/app/api/v1/endpoints/context.py:2
backend/app/api/v1/endpoints/mastery_ws.py:2
backend/app/api/v1/endpoints/mastery.py:5
backend/app/api/v1/endpoints/review.py:10
backend/app/clients/neo4j_client.py:17
backend/app/mcp/tools/mastery_tools.py:1
backend/app/models/board_manifest.py:1
backend/app/models/schemas.py:2
backend/app/models/snapshot_v3.py:2
backend/app/services/board_manifest_service.py:1
backend/app/services/fallback_sync_service.py:1
backend/app/services/learning_context_service.py:9
backend/app/services/memory_service.py:4
backend/app/services/review_service.py:6

$ rg -c next_review backend/app | wc -l
14

$ rg -c next_review backend/app | awk -F: '{s+=$2} END {print s}'
63
```

改前 / 改后两份落档：`census-before-20260918T230829.txt` / `census-after-<ts>.txt`，
`diff` 为空、`rc=0`（见验收单 §(f)）。

> **卡文事实更正（登记）**：草案清单的 `lanes[P4].notes` 写「census 的 14 个 backend/app 文件」却只列了 13 个文件名，
> **漏 `backend/app/models/snapshot_v3.py`**（`:31` docstring + `:318` `"next_review": None`）。
> 本次实测逐文件计数与卡文 §〇 第一行**逐字相同**，文件数 14 成立。
