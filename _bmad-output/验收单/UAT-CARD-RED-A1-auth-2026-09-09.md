# UAT — CARD-RED-A1-auth（2026-09-09）

> 批次 `[BATCH-2026-09-07-第十三批 / CARD-RED-A1-auth]` · 车道 `card-u10-red-a` · 分支 `card/u10-red-a`
> 基线 commit `7004a365`（同车道前一张卡 CARD-RED-E 末 commit）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U10-C.md`
> 证据目录 `_bmad-output/审查/evidence-red-a1-auth/`

---

## 1. 🎯 一句话目标

有 37 个自动检查长期报错，但报的不是它们真正要查的东西——它们全都卡在门口的一道"钥匙"检查上，从来没进过屋。这张卡给它们配了钥匙，让检查真正查到它该查的地方。

## 2. 📖 你的视角

作为在 Obsidian 里学习的人，我希望"在节点上问一句话，侧栏很快给出带上下文的回答"这条路是被真正检查过的，以便它哪天坏了能被提前发现，而不是等我用的时候才发现。

## 3. 🖥️ 交互流程

```
我在 Obsidian 打开一个概念笔记
   ↓
我按下问问题的快捷键，输入一个问题
   ↓
侧栏出现回答，里面带着这个概念的邻居笔记内容
   ↓
（而不是弹出一句"服务暂时不可用"）
```

---

## 4-A. 🤖 Claude 已代验

> 全部由 Claude 跑完并留存档，存档路径与末行 rc 逐条给出。本段只引用存档，不自述数字。

### 判据 1 — 统一裁判（tests/unit 目录级 nodeid diff）

| 项 | 存档 | 结果 |
|---|---|---|
| 开工 | `evidence-red-a1-auth/unit-open-20260909T132605.txt` | 汇总 `164 failed, 4763 passed, 48 skipped, 29 errors in 239.61s`，末行 `rc=1` |
| 收工 | `evidence-red-a1-auth/unit-after-20260909T134347.txt` | 汇总 `132 failed, 4795 passed, 48 skipped, 29 errors in 296.33s`，末行 `rc=1` |
| 收工 vs 202 基线 | `red-diff-after-20260909T134347.txt` | **零 `>` 行**（`grep '^>'` rc=1，无输出）；41 条 `<` |
| 收工 vs 开工 | `red-diff-open-vs-after-20260909T134347.txt` | **零 `>` 行** ⇒ 本卡零引入新红 |

⚠️ **与卡文 (b) 的一处不符，如实登记**：卡文写「开工目录级 diff 与 202 基线**为空**」，实测开工就有 **9 条 `<`**
（全部 `test_agent_templates_smoke.py`）。原因是卡文同时要求「HEAD = U10-B 末 commit」，而 U10-B（CARD-RED-E）
恰恰修好了这 9 条。两个条件互斥，实测以「零 `>`」为准。存档 `red-diff-open-20260909T132605.txt`。

### 判据 2 — 四文件级

| 阶段 | 存档 | 汇总 |
|---|---|---|
| 开工 | `four-open-20260909T133056.txt` | `37 failed, 1 passed`，rc=1 —— 恰 37，且与卡文 §〇 逐条一致（`red37-*.txt` diff 空） |
| 收工 | `four-after-20260909T135007.txt` | `5 failed, 33 passed`，rc=1 |

中间两态存档：`four-mid1-20260909T133341.txt`（22 failed）、`four-mid2-20260909T133815.txt`（6 failed）、
`four-mid3-20260909T134131.txt`（5 failed）。

### 判据 3 — 失败身份辅证（非判据）

| 串 | 开工 | 收工 |
|---|---|---|
| `Internal API key not configured` | 4 | **0** |
| `INTERNAL_API_KEY empty + DEBUG=True without explicit bypass` | 74 | 0 |
| `live Neo4j port connect attempted` | 0 | **0**（中间态 mid2 曾为 3 → 见下方说明） |
| `409` | 0 | 20（mid1 曾 85） |

哨兵计数如实说明：mid2 的「3」是**文本命中 3 行**，实际连接尝试**1 次**（哨兵标题 + stdout JSON + captured log
同一事件）。详见 `second-layer-20260909T134842.txt` §B。

### 判据 4 — fixture 硬约束（⚠️ 字面判据失效，已升级为结构判据）

存档 `gate-fixture-constraints-20260909T134437.txt`：

- 卡文原文口径 `grep -c 'autouse'` = **2**、`grep -c 'os.environ'` = **2** —— **不通过**。
- 逐行核实：4 条命中全在 docstring 的**禁令说明文字**里（`:23` 「⛔ 不得加 autouse」、`:26`「为什么不用
  os.environ」、`:28`「os.environ 是进程级的」、`:100` 引用 `tests/conftest.py` 那个 autouse fixture 的名字）。
- **结构判据（AST）VERDICT: PASS**：`autouse=` 关键字实参 = 无；`os.environ` 属性访问 = 无；
  `import os` = 无（没 import 就调不到）；全模块唯一 fixture 装饰器 = `pytest.fixture`（`:87`，无参数）。
- 该门自带**验伪锚**：同一逻辑对负控源码（`import os` + `@pytest.fixture(autouse=True)` + `os.environ[...]`）
  命中 1/1/1，证明门不是恒绿。

两个 conftest：`git diff --stat --no-color 7004a365 -- backend/tests/conftest.py backend/tests/unit/conftest.py`
→ **空输出 + rc=0** ✅。`authed_client` 出现面 = 新文件 + 四个测试文件，无外溢 ✅。

### 判据 5 — 裸 client 不再生长（⚠️ 字面判据双向失效，已升级为结构判据）

存档 `gate-bare-testclient-20260909T134533.txt`：

- 文本 `grep 'TestClient(app)'` 的 diff 出现 4 条 `>` —— 全是 docstring 里「原本是裸 `TestClient(app)`」这句
  引文，**假红**；同时该 grep 对 `TestClient(app, headers=...)` 这种真正的新写法**不命中**，是**假绿**。两个方向都不可用。
- **AST 结构判据 VERDICT: PASS**：扫 `tests/unit` 全部 252 个 `.py`，「裸构造」（函数名 TestClient、
  恰 1 个位置实参、0 关键字）从开工 **16** 处降到收工 **12** 处；消失的恰是本卡四个文件，**新增文件 = 无**。
- 三个验伪锚全部符合期望：裸构造→命中 1；带 `headers=`→命中 0；docstring 引文→命中 0。

### 判据 6 — 第二层红三分类表

`second-layer-20260909T134842.txt`（每行 `nodeid | 类别 | 依据 | 去向`）。摘要：

| 层 | 条数 | 去向 |
|---|---|---|
| 第一层 鉴权 503 | 37 | 全部由 `authed_client` 解除；其中 15 条解开即绿 |
| 第二层 409 | 17（chat 10 + deep_mode 7） | **本卡修**：fixture patch `app.config.get_current_vault_id`（先例 `test_sync_batch_auth.py:98`） |
| 第二层 哨兵 | 1（`test_enrich_context_happy_path`，409 解除后才显形） | **本卡修**：fixture patch `app.api.v1.endpoints.chat.get_memory_service` |
| 第二层 前提未适配 | 5（`test_enrich_context_vault_isolation`） | **移交 U5-C `CARD-RED-R`** —— 本卡不改用例代码 |

⚠️ **这 5 条的移交理由已按 Codex round-1 MEDIUM-1 收窄**（原版论证过强，如实更正）。
本卡**没有**证明这 5 条断言是错的：它们验的是 ContextVar 注入 / 中文保留 / subject_id 可选 /
路径净化 / emoji 剥离，**没有一条把「请求属于另一个 vault」当作被测前提**——只是没安排
「payload vault 与 active vault 一致」这个新前提。给它们配匹配的 active vault **也不等于「关掉隔离」**，
`vault_scope.py:162-176` 的判定仍真实执行。所以不能说「必须重写」或「本卡修不了」。

实际处置依据是**分工**：① 要修需逐用例改用例代码（5 条各用不同 vault_id，fixture 级单桩覆盖不到），
而本卡地盘约定是「不改被测用例本身、只换测试装置」；② 这 5 条属 vault 隔离面，与本卡「解开鉴权装置」
不同轴，同批 U5-C `CARD-RED-R` 专门承接 RED 收敛。

📌 顺带登记一个**真实的覆盖缺口**（Codex MEDIUM-2 实证）：全仓当前**没有任何测试**对 enrich-context
断言 409 —— 5 条正向被 409 阻断、2 条验 422、1 条验 ContextVar 并发，都不是「不一致时会拒绝」的回归
覆盖。接手卡宜在适配前提的同时补一条反向用例（显式异 vault → 期望 409）。

### 判据 7 — 地盘门

```
git diff --name-only --no-color 7004a365 -- . ':(exclude)_bmad-output'
  → backend/tests/unit/test_chat_endpoint.py
    backend/tests/unit/test_enrich_context_vault_isolation.py
    backend/tests/unit/test_study_question_deep_mode.py
    backend/tests/unit/test_sync_exception_classification.py     rc=0
未跟踪新增：backend/tests/support/authed_client.py
git diff --stat --no-color 7004a365 -- backend/app  → 空 + rc=0   ✅ 零生产写面
```

### 判据 8 — ruff

`ruff-20260909T134602.txt`：`ruff check` 五个文件 **All checks passed!** rc=0
（r1 整改后复跑见 `gates-after-r1fix-20260909T140659.txt`，同样 `All checks passed! check_rc=0`）。
⚠️ 同目录 `ruff-20260909T134550.txt` 是**没跑成**的那次：zsh 不做变量分词，`$FILES` 被当成单个路径，
`ruff` 报 `E902 No such file or directory`。留档以免后人把它读成一次真实结果。
`ruff format --check` 报 2 个文件待重排 —— **是既有漂移，本卡零引入**，三条证据：

1. 同一组文件在基线 `7004a365` 上就 `rc=1`，且是**同样这两个**文件（`ruff-format-drift-20260909T134644.txt` §A）；
2. 待重排 hunk 数与内容在基线/工作树完全相同（3+3 处，全是断言消息换行），位移量恰等于本卡在文件顶部的净增行数（§B/§C/§D）；
3. **硬证**：把基线副本与工作树副本**都 format 之后再 diff**，差异**只含本卡改动**、零格式差异
   （`ruff-format-drift-proof-20260909T134713.txt`）。

按卡文 §二.8「漂移只对本卡改动行处理，禁顺手 format 整文件」——那 3+3 处全在断言消息行，format 它们等于改断言，**不动**。

### 37 条闭合校验

`closure-37-20260909T134937.txt`：

```
本卡消掉 32 条，全部 ⊆ §〇 的 37 条（差集为空）
37 条里没消掉的 5 条 = 移交的那 5 条，逐条确认仍在收工红集里（非凭空消失）
算术闭合：202(基线) − 9(U10-B 的 agent_templates) − 32(本卡) = 161 = 收工红集实数 161
```

### §〇 复核（完成条件 a）

`00-recheck-section0.txt`。§〇 表内 file:line 逐条实测，**一处偏差**：

> §〇 说 `assert_identity` 的 autouse no-op 桩在 `tests/unit/conftest.py:137-160`
> → 实测在 **`:395-418`**（`:395` `@pytest.fixture(autouse=True)` / `:412-413` `_NoopRegistry.assert_identity`
> / `:417` `monkeypatch.setattr`）。`:137-160` 实际是 `_hygiene_scan_tmp_literals` 的 docstring。
> **结论不变**（「不必补 `assert_identity` 桩」的依据成立），仅行号引用错，本卡按实测行号记账。

### Codex 审查

见下方 §7「Codex 轮次」。

---

## 4-B. 👤 你来验

> 3 分钟，全程在 Obsidian 里完成。

- [ ] 我在 Obsidian 里打开一个概念笔记（比如"特征值"），按下问问题的快捷键，输入"这个和线性无关有什么关系" → 我看到侧栏给出的回答里**提到了相邻的那几篇笔记**，而不是只重复我这一篇的内容 → 我感觉这条路是通的（顺畅）。

- [ ] 我故意在没开后台服务的时候再问一次 → 我看到侧栏**明确告诉我暂时用不了**，而不是一直转圈或者给一个看不懂的编号 → 我感觉它至少是诚实的（信任）。

- [ ] 我连着在三个不同的概念笔记上各问一句 → 我看到每次回答**都换成了当前这篇的邻居**，没有串到上一篇去 → 我感觉它确实知道我在看哪一篇（不混乱）。

- [ ] 我把同一个问题问两遍 → 我看到两次回答都能出来，第二次**明显更快** → 我感觉它不是每次都从零开始（流畅）。

---

## 5. 🚦 验收结果

- 4-B 四条全部满意 → 回一句「U10-C 通过」，我接着做同车道的 U10-D。
- 任一条不满意 → 在下方批注区写一句你看到的实际现象（不用管技术），我来定位。

---

## 6. 📝 批注区

> [!question]+ 你的疑问
> （在这里写）

> [!error]+ 你发现的问题
> （在这里写）

---

## 7. 🔗 技术 spec 引用

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U10-C.md`
- 新文件：`backend/tests/support/authed_client.py`
- 改动文件：`backend/tests/unit/{test_chat_endpoint,test_enrich_context_vault_isolation,test_study_question_deep_mode,test_sync_exception_classification}.py`
- 相关生产代码（**本卡只读，零改动**）：`app/security.py:88-166`、`app/api/v1/endpoints/chat.py:48,283-330`、
  `app/api/v1/endpoints/sync.py:63,100-140`、`app/core/vault_scope.py:137-176`
- 证据目录：`_bmad-output/审查/evidence-red-a1-auth/`
- Codex prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-RED-A1-auth.md`

### Codex 轮次

| 轮 | 存档 | 绑定 | BLOCKER | HIGH | MEDIUM | LOW | 结果 |
|---|---|---|---|---|---|---|---|
| r1 | `codex-review-CARD-RED-A1-auth-r1.md` | `7004a365..工作区` | **0** | **0** | 2 | 3 | 5 条**全部采纳整改**，故必再送一轮 |
| r2 | `codex-review-CARD-RED-A1-auth-r2.md` | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |

**r1 五条整改逐条落点**：
- MEDIUM-1（移交理由过强）→ `second-layer-*.txt` §A 重写 + 本验收单 §4-A 判据 6 同步收窄
- MEDIUM-2（把不存在的 409 覆盖写成已有保障）→ `test_chat_endpoint.py` / `test_study_question_deep_mode.py`
  的 `client` fixture docstring 删除该保证，改为明写「本桩不证明什么」+ 登记覆盖缺口
- LOW-1（"非 HTTP 的 rag_enrich_hook"/"本就不进业务层"不实）→ `second-layer-*.txt` 按请求实际走到哪里
  重分三类（输入校验 / 端点内提前返回 / 确实进业务处理）
- LOW-2（conftest 机制描述错：具名非 autouse fixture 不会自动生效）→ `authed_client.py` 模块 docstring
  改为「限制可发现范围 + 要求显式导入」
- LOW-3（"Settings 逐字等价"不实）→ `test_sync_exception_classification.py::_dev_settings` docstring
  改为「只在鉴权相关字段上一致」

---

## 8. ❓ 本卡未证明什么

1. **未证明 vault 隔离逻辑本身正确** —— 那 5 条只做了分类与移交，没有验证 409 门在各种 vault_id 下的行为是否正确。
2. **未证明 `ALLOW_UNSAFE_DEV_AUTH_BYPASS` + loopback 那条放行路径** —— `TestClient` 的 host 恒为 `"testclient"`，
   到不了 loopback，本卡完全没碰这条分支。
3. **未证明 WebSocket 侧鉴权** —— `security.py:184-259` 的 `verify_websocket_internal_key` Branch 2（`:228-234`）
   仍是「dev + 空 key 放行」，与 REST 侧不一致。只登记，本卡不改也不测。
4. **未证明 `block_reason()` 在真 Neo4j 可用时的行为** —— 本卡只在测试侧把它打成返回 `None`。
5. **未证明 `authed_client` 在 `tests/api` / `tests/integration` 下可用** —— 只在 `tests/unit` 的四个文件里用过。
6. **未证明这 37 条背后的业务断言当前仍是正确契约** —— 本卡只把请求送进业务层；断言本身对不对没有重新评估
   （vault_isolation 那 5 条恰恰是反例：断言过期了）。
7. **未证明 `X-CLS-Internal-Key` 头名与生产插件一致** —— header 名从 `app.security.INTERNAL_API_KEY_HEADER_NAME`
   import（不抄字面量），但没有与前端 `api-client.ts` 侧交叉核对。
8. **未证明 32 条转绿的用例"验的还是它原本想验的东西"** —— 本卡打了 3 类桩
   （`get_current_vault_id` / `get_memory_service` / `get_canvas_schema_gate`）。桩的等价性有论证
   （见各 fixture docstring 与三分类表），但没有做变异验证。这一条已列入 Codex 提问 §三.4/§三.5。
9. **未证明「请求 vault 与 active vault 不一致时会被拒」有任何回归覆盖** —— 恰恰相反，Codex round-1
   MEDIUM-2 实证全仓当前**没有**这样的测试。本卡还给 chat/deep_mode 两个文件加了 active-vault 桩，
   等于在这两个文件里把该前提设成恒一致。这道覆盖缺口本卡不补，已登记移交。
10. **未证明四文件级耗时从 1.07s 涨到 51-96s 的全部来源** —— 哨兵归 0 后仍慢，初判是
   `search_supplementary` 侧的既有开销（本卡解开鉴权后这些代码才第一次真正执行到），非本卡引入，登记不处置。

---

## 9. 📒 台账待登记条目

1. **新文件射程**：`backend/tests/support/authed_client.py` —— 目前被 `tests/unit` 四个文件 import；
   承诺「禁 autouse / 禁进任何 conftest / 禁 os.environ 注入」，AST 门证据见
   `evidence-red-a1-auth/gate-fixture-constraints-*.txt`。U10-D 计划复用它。
2. **第二层红三分类表**：`evidence-red-a1-auth/second-layer-20260909T134842.txt`，
   17 条 409 + 1 条哨兵本卡修，5 条判契约演进**移交 U5-C `CARD-RED-R`**。
3. **`security.py:13-22` docstring 矩阵与实现矛盾**：`:15` 行写 `| True | empty | any | allow + structured
   warning (dev mode) |`，与 `:110-142` 的 fail-closed 实现相反。登记不改（本卡零生产写面）。
4. **`chat.py:39-47` 旧矩阵注释过期**：尤其 `:43`「DEBUG=True + key 未配置 → allow + warning log」，
   在 `c9bb6c9a` 后失效。登记不改。
5. **REST / WS 鉴权不一致**：`security.py:228-234` 的 WS 分支仍 dev 放行。登记不改。
6. **`test_sync_exception_classification.py:48-58 _dev_settings` 的失效前提已处置**：本卡**保留**该 helper
   但把 `INTERNAL_API_KEY=""` 改为带 key，并更正 docstring 说明「c9bb6c9a 后空 key 恒 503」。
   选择保留而非删除的理由：六条用例各自第一行都装这份 override，删 helper 要改 6 处用例代码；
   保留后用例一行未动，且 helper 名实重新一致。
7. **卡文 §〇 一处行号错**：`assert_identity` 的 autouse 桩实测在 `tests/unit/conftest.py:395-418`，
   非 §〇 所写的 `:137-160`。结论不变。
8. **卡文 (b) 的开工 diff 预期与「HEAD = U10-B 末 commit」互斥**：实测开工即有 9 条 `<`
   （U10-B 修好的 `test_agent_templates_smoke`）。建议后续卡文对串行车道改用「零 `>`」口径。
9. **两条卡文写死的 grep 判据在本卡上双向失效**（判据 4 的 `autouse`/`os.environ`、判据 5 的
   `TestClient(app)`）：docstring 说明文字计成违规（假红），带 `headers=` 的新写法不被命中（假绿）。
   本卡改用 AST 结构判据 + 验伪锚。**建议把这两条判据的结构版沉淀进协议**，后续卡不要再用文本 grep。
10. **Codex 轮次与每轮绑定 SHA**：见 §7 表。
