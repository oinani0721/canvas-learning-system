# UAT — CARD-RED-A1-auth（2026-09-09）

> 批次 `[BATCH-2026-09-07-第十三批 / CARD-RED-A1-auth]` · 车道 `card-u10-red-a` · 分支 `card/u10-red-a`
> 基线 commit `7004a365`（同车道前一张卡 CARD-RED-E 末 commit）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U10-C.md`
> 证据目录 `_bmad-output/审查/evidence-red-a1-auth/`

---

## 1. 🎯 一句话目标

有 37 个自动检查长期报错，但报的不是它们真正要查的东西——开工时它们全都卡在门口的一道"钥匙"检查上。这张卡给它们配了钥匙：其中 32 个恢复到了各自该走的路（有的进业务逻辑，有的按设计就该在门口被挡回），剩下 5 个卡在另一道"这是不是你自己的书架"的检查上，交给下一张卡处理。

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
| 第一层 鉴权 503 | 37 | 全部由 `authed_client` 解除；其中 15 条在**迁移 + sync 两桩之后**转绿（Codex r5 LOW-2 更正：那 15 条含 /sync/batch 六条，不能全归因于鉴权解除） |
| 第二层 409 | 17（chat 10 + deep_mode 7） | **本卡修**：fixture patch `app.config.get_current_vault_id`（先例 `test_sync_batch_auth.py:98`） |
| 第二层 哨兵 | 1（`test_enrich_context_happy_path`，409 解除后才显形） | **本卡修**：fixture patch `app.api.v1.endpoints.chat.get_memory_service` |
| 第二层 前提未适配 | 5（`test_enrich_context_vault_isolation`） | **移交 U5-C `CARD-RED-R`** —— 本卡不改用例代码 |

⚠️ **这 5 条的移交理由已按 Codex round-1 MEDIUM-1 收窄**（原版论证过强，如实更正）。
本卡**没有**证明这 5 条断言是错的：它们验的是 ContextVar 注入 / 中文保留 / subject_id 可选 /
路径净化 / emoji 剥离，**没有一条把「请求属于另一个 vault」当作被测前提**——只是没安排
「payload vault 与 active vault 一致」这个新前提。给它们配匹配的 active vault **也不等于「关掉隔离」**，
`vault_scope.py:162-176` 的判定仍真实执行。所以不能说「必须重写」或「本卡修不了」。

实际处置依据是**分工**：① 要修需**按用例适配 active-vault 前提**（5 条各用不同 vault_id，
一个固定 `return_value` 的 fixture 级单桩覆盖不到）——但这**不等于「必须改用例体」**
（Codex round-2 MEDIUM-1 更正：function-scope fixture 完全可以按用例配置前提）；
本卡不做是因为地盘约定「只换测试装置、不动被测用例这一面」。② 这 5 条属 vault 隔离面，
与本卡「解开鉴权装置」不同轴，同批 U5-C `CARD-RED-R` 专门承接 RED 收敛。

⚠️ **本节先前写过一条「覆盖缺口」，那句话是错的，此处推翻**。Codex round-2 MEDIUM-2 指出它范围过宽；
复核后发现问题比「过宽」更严重——它在任何范围下都不成立。实测：

- `tests/unit/test_vault_scope_409.py:333-343` `test_chat_enrich_context_mismatch_409` 就是对
  **enrich-context** 的 409 断言（异 vault payload → `assert 409`），且它在开工与收工红集里
  **都不存在**，且两次目录级存档都正面记录该文件全部通过
  （`unit-open-20260909T132605.txt:279` / `unit-after-20260909T134347.txt:279`）。
  ⚠️ 措辞按 Codex round-3 收窄为「这两次存档均通过」，不写「一直绿」——本卡没跑过更早的历史。
- 同文件 `:345-373` `test_chat_enrich_context_match_path_executes` 用的正是本卡这组桩
  （`get_current_vault_id` + `get_memory_service` 的 `AsyncMock`），是本卡打桩形态的**直接先例**。
- 该文件还覆盖 sync / mastery / memory / exam_sessions / boards 五个端点面的 409。

**这反而加强了移交决定**：409 门本身有专门的、绿着的回归覆盖，vault_isolation 那 5 条正向用例
并不承担这道门的把关职责，接手卡为它们适配 active-vault 前提不会留下覆盖缺口。

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
| r2 | `codex-review-CARD-RED-A1-auth-r2.md` | `7004a365..faeda37f` | **0** | **0** | 2 | 2 | 4 条**全部采纳整改**，故必再送一轮 |
| r3 | `codex-review-CARD-RED-A1-auth-r3.md` | `7004a365..bcbe2741` | **0** | **0** | **0** | 2 | 两条 MEDIUM 确认已落实；2 LOW 采纳整改，故必再送一轮 |
| r4 | `codex-review-CARD-RED-A1-auth-r4.md` | `7004a365..1e326860` | **0** | **0** | **0** | 1 | 已达停轮条件；那条 LOW 采纳整改，故再送末轮 |
| r5 | `codex-review-CARD-RED-A1-auth-r5.md` | `7004a365..385078b8` | **0** | **0** | **0** | 4 | **末轮，停轮条件达成**（轮次上限 5/5） |

### 停轮判定（协议 §1 / D-15）

r5 绑最终 HEAD `385078b8`，**BLOCKER = 0、HIGH = 0** ⇒ 停轮条件达成。轮次 5/5 用尽。
r5 之后的整改**只动 `_bmad-output`**，协议 §1 的绑定判据
`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 排除该目录，**绑定不失效**。

**r5 四条 LOW 的处置**：

| # | 内容 | 处置 |
|---|---|---|
| LOW-1 | §1 总述与 §8.6 仍笼统涵盖 37 条 | ✅ 已改：明写 32 条各归其位（含 3 条校验 + 1 条提前返回本就不该进业务层）、5 条移交 |
| LOW-2 | 「15 条解开鉴权即绿」漏掉同期的 sync 两桩 | ✅ 已改：改为「完成 authed_client 迁移 + sync 两桩之后转绿」 |
| LOW-3 | `_dev_settings` docstring「只在鉴权相关字段一致」**收窄过度** | ⛔ **登记不改**，理由见下 |
| LOW-4 | 耗时归因与日志相反 | ✅ 已推翻：实测那次初始化仅约 1.9 ms、请求 128.12 ms，改为「来源未闭合」 |

**LOW-3 为何登记不改**（如实说明，不是遗漏）：
- 该条**成立**。作者逐字段实测：两份 Settings 有 **5 个字段相同**（`VERSION` / `DEBUG` / `LOG_LEVEL` /
  `CANVAS_BASE_PATH` / `INTERNAL_API_KEY`），只有 `PROJECT_NAME` 与 `CORS_ORIGINS` 不同。
  现 docstring 写「只在鉴权相关字段上一致 / 其余字段并不相同」确实收窄过度。
- 但整改它要动 `backend/tests/unit/test_sync_exception_classification.py` 这个**代码文件**，
  会让末轮绑定判据非空 ⇒ 按 D-15 必须再送一轮，而**轮次上限 5 已用尽**。
- 权衡：这是一句「比实际更保守」的说明（说少了相同字段，没有夸大任何保证），
  不影响任何判据与行为。故**登记移交**，由主 session 复核时人审或并入下一张卡。
- 建议改法（Codex 原文）：「鉴权相关字段一致；`PROJECT_NAME` 与 `CORS_ORIGINS` 不同，
  因此整份 Settings 并不等价」。

⚠️ **本卡已知的未复审面**：上述 LOW-1/2/4 三条整改**本身未经 Codex 复审**（轮次已满）。
它们都是纯 `_bmad-output` 文档改动、零代码改动，但如实登记在此，供主 session 复核。

**r4 一条 LOW 整改落点**：台账 §9.6 仍写 `test_sync_exception_classification.py:48-58 _dev_settings`
——那是本卡文件的行号，与 r3 立下的「本卡位置一律用名称」自相矛盾（且 `:48-58` 只覆盖函数头与部分
docstring，函数实际延伸到 `:69`，带 key 的赋值在 `:68`）。已改为
`test_sync_exception_classification.py::_dev_settings`。
改后全面复查：验收单、`second-layer`、三处 fixture docstring、`authed_client.py` 里
**指向本卡五个文件的行号引用已清零**（`grep` rc=1）。

**r4 逐项确认无误**：chat 校验计数 3 条用例 / 4 次 POST；三处 docstring 与 second-layer 已用名称；
「两次存档均通过」措辞成立且三份文档无相互矛盾；外部引用 `test_vault_scope_409.py:333-343`/`:345-373`、
`tests/unit/conftest.py:395-418`（含 `:412-413` no-op）、`tests/conftest.py:441-452`/`:490`/`:494-517`、
`test_sync_batch_auth.py:81-84`/`:98-99`、`security.py:110-142` 全部准确（作者亦独立实测 15 处，一致）。
r4 还核了三个 commit 之间五个 Python 文件**去掉 docstring 后的可执行 AST 一致**。

**r3 两条 LOW 整改落点**（两条恰是作者在 r3 运行期间自查发现的同一批问题，已一并处理）：
- LOW-1（chat 校验用例少算一条）→ fixture docstring 补上 `test_enrich_context_rejects_invalid_mode`，
  三条校验用例齐（r3 确认正确计数为 16 = 10 条 enrich-context 正向 + 3 条校验 + 3 条 rag hook）
- LOW-2（行号仍在漂）→ **本卡内引用同一文件位置的地方一律改用「用例名」**，不再写行号：
  两轮 docstring 整改让行号整体下移，`:434/:463/:485` 已指向 `AsyncMock` 导入行、`:114` 指向有效
  deep 请求、`:173` 指向空行。行号是工作树指纹，抄旧值即失实
- 另采纳 r3 的一处精确化：把「一直绿」收窄为「本卡开工/收工两次目录级存档均通过」
  （`unit-open-*.txt:279` / `unit-after-*.txt:279` 正面记录），红集缺席只是必要条件

**r3 确认无误的计数**：study 七条有效正向 + 一条非法 mode；isolation 七条 HTTP + 一条并发；rag hook 三条。

**r2 四条整改逐条落点**：
- MEDIUM-1（旧结论残留 + 「必须改用例代码」仍过强）→ 验收单 `:244`/`:264` 清掉「断言过期」「判契约演进」，
  `second-layer` §A.1 改为「按用例适配前提」并明写 function-scope fixture 本可做到、本卡不做是地盘约定
- MEDIUM-2（把 enrich-context 的缺口说成全仓无覆盖）→ **复核后发现比「过宽」更严重：该说法在任何范围下
  都不成立**。`test_vault_scope_409.py:333-343` 就是 enrich-context 的 409 断言，在本卡两次目录级
  存档中均通过；其 `:345-373`
  还用了与本卡同一组桩。两处 fixture docstring + `second-layer` §A.3 + 验收单判据 6 与 §8.9 全部改写为
  「这条性质另有覆盖且绿」，并说明这**加强**而非削弱移交决定
- LOW-1（rag hook 三条全归「进业务处理」）→ `second-layer` 把 `short_prompt_skips_lazy_init`
  改归第 (ii) 类「端点内提前返回」，POST 行号更新为 `:434/:463/:485`
- LOW-2（三处「每条/全文件」过宽）→ `test_chat_endpoint.py` 限定为「enrich-context 请求」、
  `test_study_question_deep_mode.py` 限定为「七条有效输入的正向用例」、
  `test_enrich_context_vault_isolation.py` 限定为「使用 client 的 HTTP 用例」

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
6. **未证明这 37 条背后的业务断言当前仍是正确契约** —— 本卡只是解除了鉴权阻挡，让 32 条恢复到各自
   预期的路径（其中 3 条校验类与 1 条提前返回类**本就不该进业务层**，见判据 6 的三类划分）；
   断言本身对不对没有重新评估
   （vault_isolation 那 5 条只是**前提未适配**，本卡并未证明它们的断言是错的——见判据 6）。
7. **未证明 `X-CLS-Internal-Key` 头名与生产插件一致** —— header 名从 `app.security.INTERNAL_API_KEY_HEADER_NAME`
   import（不抄字面量），但没有与前端 `api-client.ts` 侧交叉核对。
8. **未证明 32 条转绿的用例"验的还是它原本想验的东西"** —— 本卡打了 3 类桩
   （`get_current_vault_id` / `get_memory_service` / `get_canvas_schema_gate`）。桩的等价性有论证
   （见各 fixture docstring 与三分类表），但没有做变异验证。这一条已列入 Codex 提问 §三.4/§三.5。
9. **未证明「请求 vault 与 active vault 不一致时会被拒」——但这条性质另有覆盖，且是绿的**。
   本卡给 chat / deep_mode 两个文件加了 active-vault 桩，等于在这两个文件里把该前提设成恒一致，
   所以**本卡的改动不为这条性质提供任何证据**。它由 `test_vault_scope_409.py:333-343` 把关
   （开工收工均绿）。⚠️ 本条先前写成「全仓没有这样的测试」，是错的，已于 Codex round-2 后更正。
10. **未证明四文件级耗时从 1.07s 涨到 51-96s 的来源** —— ⚠️ 本条先前把它归因于那次被拦的真连，
   **与日志相反**（Codex r5 LOW-4）：实测那次 MemoryService 初始化仅约 1.9 ms、整个请求 128.12 ms，
   解释不了几十秒。耗时增长是观测事实，来源**未闭合**；初判方向是解开鉴权后 `search_supplementary`
   等下游第一次真正被执行到，但本卡未证实。「非本卡引入」只能限定为「本卡未改任何相关生产代码」
   （`git diff -- backend/app` 为空），不能据此宣称没有性能影响。

---

## 9. 📒 台账待登记条目

1. **新文件射程**：`backend/tests/support/authed_client.py` —— 目前被 `tests/unit` 四个文件 import；
   承诺「禁 autouse / 禁进任何 conftest / 禁 os.environ 注入」，AST 门证据见
   `evidence-red-a1-auth/gate-fixture-constraints-*.txt`。U10-D 计划复用它。
2. **第二层红三分类表**：`evidence-red-a1-auth/second-layer-20260909T134842.txt`，
   17 条 409 + 1 条哨兵本卡修，5 条判**前提未适配**（非断言证伪）**移交 U5-C `CARD-RED-R`**。
3. **`security.py:13-22` docstring 矩阵与实现矛盾**：`:15` 行写 `| True | empty | any | allow + structured
   warning (dev mode) |`，与 `:110-142` 的 fail-closed 实现相反。登记不改（本卡零生产写面）。
4. **`chat.py:39-47` 旧矩阵注释过期**：尤其 `:43`「DEBUG=True + key 未配置 → allow + warning log」，
   在 `c9bb6c9a` 后失效。登记不改。
5. **REST / WS 鉴权不一致**：`security.py:228-234` 的 WS 分支仍 dev 放行。登记不改。
6. **`test_sync_exception_classification.py::_dev_settings` 的失效前提已处置**：本卡**保留**该 helper
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
