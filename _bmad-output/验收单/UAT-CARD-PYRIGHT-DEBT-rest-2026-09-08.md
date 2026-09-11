# UAT — CARD-PYRIGHT-DEBT-rest（v1：阶段 0 + 阶段 1 完成，等候选树通告）

> 批次 `[BATCH-2026-09-07-第十三批 / CARD-PYRIGHT-DEBT-rest]` · 车道 `card-u2-pyright-rest`（分支 `card/u2-pyright-rest`）
> CODE_BASE `da690bf8` · 阶段 0 commit `5638ac6c` · 阶段 1 commit `41cc849c`
> 证据目录 `_bmad-output/审查/evidence-pyright-rest/`（本文件只**引用**路径与末行，不自述数字）

---

## 1. 这张卡做了什么（一句话）

把 `backend/app` 里**非 `services/`** 的那 174 条 pyright 报错清到 0（阶段 1 结束时只剩三个**按卡文延后**的共享/交集文件），过程中不改任何运行期行为——发现的 4 处**真缺陷**一条没修，全部如实登记移交。

---

## 2. 阶段 0（commit `5638ac6c`，已报给 U1）

| 项 | 前 | 后 | 证据 |
|---|---|---|---|
| `pyrightconfig.json` 加 `extraPaths: ["backend/lib"]` | 无 | 有 + 12 行注释 | `git show 5638ac6c -- pyrightconfig.json` |
| `models/**` 位置默认机械改写 | 266 处 / 12 文件 | 0 | `field-rewrite-models-*.txt` / `field-positional-base-*.txt` |
| 真 bug ① `AutoScoreResult` 四维必填化 | `default_factory=RubricDimension`（被用到即 ValidationError） | `Field(..., description=…)` | `rubric-regression-RED-*.txt`（5F/3P）→ `rubric-regression-GREEN-*.txt`（8P） |
| 全量 pyright | 421 | 356 | `pyright-app-base-text-*.txt` / `multiset-p0-state1-*.txt` |
| 多重集（BASE `da690bf8`） | — | `NEW=6 GONE=71` | `multiset-p0-state1-*.txt` |

**NEW=6 逐条**（全部是 `extraPaths` 让 `LanceDBClient` 从"解析不到 ⇒ Unknown ⇒ 属性访问一律放行"变成"解析得到 ⇒ 真报错"，即能力增强的副产品，**不是回归**）：
`edges.py` ×3（`delete` / `upsert` / `get_db`）、`metadata.py` ×2（`ignore_missing` / `drop_table` on None）、`services/rag_service.py` ×1（`ainvoke` config）。
**真 bug ① 引起的 NEW = 0**——两个实例化点 `services/autoscore.py:141/:197` 都显式传四维，必填化打不到任何调用点。

**为什么不给 `RubricDimension.score` 加默认 0**：那是"评分缺失静默为 0"的语义变化，用户未裁。本卡只把「实例化时报内层 `score` 缺失」改成「更早、更准地报四个维度名缺失」。

---

## 3. 阶段 1（45 个非共享文件）

### 3-A 分包主判据（`pyright-per-pkg-p1-*.txt`）

| 包 | 开工 | 阶段1末 |
|---|---|---|
| `clients` | 40 | **0 errors** |
| `mcp` | 22 | **0 errors** |
| `core` | 13 | **0 errors** |
| `models` | 11 | **0 errors** |
| `middleware` | 7 | **0 errors** |
| 其余（`dependencies.py`/`main.py`/`domains`） | 6 | **0 errors** |
| `api` | 75 | 21（= 共享 `review.py` 7 + `system.py` 4 + **`exam.py` 10**） |

`api` 剔共享**且**剔 `exam.py` 后 = **0**（同一份存档末段打印）。

> ⚠️ **`exam.py` 的 10 条按卡文 §三 延到阶段 2**：它与 `services/exam_service_ext.py` 的猴子补丁同根，U1-A 已把它声明为跨包交集面（优先方案 = 在 `ExamService` 里加 `TYPE_CHECKING` 方法声明，api 侧随之消、不动 api）。本卡**一字未动该文件**，因此 `api` 行不是 `0 errors`——这不是"解释掉"，是把数字与其构成一起交出来。

### 3-B 其他判据

| 判据 | 结果 | 证据 |
|---|---|---|
| 多重集（BASE = `5638ac6c`） | `base=356 work=232 **NEW=0** GONE=124` | `multiset-p1-state2-*.txt` |
| 全量分组 | `rest 21 / services 211`；rest 逐条 = exam.py 10 + review.py 7 + system.py 4，**零计划外残留** | `group-p1-*.txt` |
| AST 位置默认 | 366 → **14**（只剩共享 `api/v1/system.py`，阶段 2 清） | `field-positional-p1-*.txt` |
| `ruff check --select F401,F821` | `All checks passed!` | `ruff-p1-*.txt` |
| `ruff format` 集合差 | base 漂移 37 = now 漂移 37，**本卡新引入 0** | `ruff-p1-*.txt` + §5 |
| openapi 漂移 | `DRIFT: none (paths=194 schemas=354)` rc=0 | §5 |
| ignore 清单 | 25 条，全部行级 + 具体 rule + 理由；基线 `da690bf8` 为 **0** | `ignore-table-p1.md` / `ignore-list-p1-added.txt` |
| 负控 ×2 | 见 §4 | `negctl-*.txt` |

---

## 4. 负控（证明判据承重，不是死判据）

1. **位置默认**：把 `metadata_models.py` 的 `Field(default=None, …)` 写回 `Field(None, …)` → 调用方 `metadata.py:465` **重新报** `Argument missing for parameter "subject"`（命中数 1）。还原用 `git show + cp`（禁 `git checkout`），`shasum -a 256` 前后**逐字节相同**。
2. **`isinstance` 窄化**：还原 `claude_client.py` 一处 `isinstance(block, TextBlock)` → `hasattr(block,"text")` → `Cannot access attribute "text"` 计数从 0 回到 **11**（恰是除 `TextBlock` 外的 11 个块类型）。
   ⚠️ 该次还原我误用了 `git show HEAD:`（HEAD 是**阶段 0** commit，阶段 1 尚未提交），把本卡改动一并抹掉；已按**变异前捕获的 sha** 重放并核对 `ad54c7ab…` 逐字节相同（同一存档记录）。

**等价性前置实证**（没有它就没资格说"不改语义"）：anthropic 0.88.0 的 `ContentBlock` 联合共 12 个成员，`model_fields` 里**只有 `TextBlock` 有 `text`** ⇒ `isinstance` 与 `hasattr` 对该联合逐成员同真同假。

---

## 5. 三条容易被糊过去的判据，这里写清做法

1. **格式门**：12 个 models 文件 + 25 个其他文件在 `da690bf8` 就已 `ruff format` 漂移（`schemas.py` 单文件 585 行 diff），整文件 format = 越界改存量。
   - **不用**"两边 rc 都 1 ⇒ 是存量"这种口径（本项目记过的假绿）。用**集合差**：逐文件比 `format --check` 在 base 与 now 的通过/失败，`comm -13` 求"我新引入的" → 发现 **1 个**（`core/exception_handlers.py`，它在 base 是干净的），单独 format 掉它，复核集合差为空、37 = 37。
   - 另用**不动点内容口径**：`format(rewrite(format(HEAD版)))` vs `format(当前版)` → 11 个 models 文件逐字相同，`exam_models.py` 只差真 bug ① 那个 hunk（**验伪锚**：判据看得见差异，不是死判据）。存档 `format-content-proof-fixpoint-*.txt`。
   - ⇒ 阶段 0 commit 用 `LEFTHOOK_EXCLUDE=python-lint`，原始 hook 输出存 `lefthook-precommit-raw-*.txt`。**`python-typecheck` 未绕过且实测通过（`0 errors`）**——协议禁止改 `backend/app/**` 的卡绕过它。
2. **tests 基线**：开工那一跑与 `models/` 机械改写**并发**，按本项目教训本应作废。它能用不是因为"我觉得没影响"，而是**汇总行与主 session 在 `da690bf8` 独立采集的红基线逐字相同**（`173 failed / 4749 passed / 48 skipped / 29 errors`）——外部锚点，不是自证。
   nodeid 提取器收紧过：`^(FAILED|ERROR) ` 会把 pytest 捕获的 `logging` 输出行（`ERROR    app.main:…`）当成 nodeid，虚报 4 条差异；改成必须匹配 `tests/…py::` 并配**验伪锚**（3 行探针，噪音剔掉 / 真 nodeid 留下）。脚本 `nodeids.sh`。
3. **入库禁令的取名面**：协议禁的是 `*.stderr*`。第一版判据写成 `git ls-tree | grep -c stderr` 报了 1 条——查下去是 `_bmad-output/审查/G4-9-evidence/census-stderr.txt`（**连字符**形式，第五批 `67ccebe1` 引入，`da690bf8` 即存在，非本卡）。判据的取名面必须**恰好等于**其主张，改成 `grep -E '\.stderr'` 后 = 0，并配验伪锚（拿真 `.stderr` 路径试，确认判据看得见违规、同时放过 `census-stderr.txt`）。本卡两个 commit 新增文件里 `.stderr` = 0。
4. **U10-A 的 `/tmp` 负控窗口（共三次，第三次未通告本车道）**：窗口一 06:59:14–07:18:58 / 窗口二 07:44:00–07:50:26 / 窗口三 08:19:52–08:24:5x。窗口内 `tests/unit` 目录级会多一条 `新出现 /tmp/test-vault*` 的 teardown ERROR。
   **核对方式不是算时间窗，是直接找症状**（存档 `crosslane-tmpwindow-check-*.txt`）：真信号 `新出现 … test-vault` 在本卡全部 4 份 `tests/unit` 存档里 **0 命中**（配验伪锚，探针命中 1 证明判据不死）；四组 nodeid 全 202、与红基线的新红 `>` 全为 **0**。⇒ 三个窗口均未影响本卡证据。
   ⚠️ 附一次自己的假阳：第一版判据写成宽 `grep test-vault`，**4 份存档全命中**——查下去全是 pytest 自身的 `tmp_path`（`/private/var/folders/…/pytest-of-Heishing/pytest-NNNNN/test_endpoint_exists0/test-vault/`），与 `/tmp/test-vault*` 不同根。**今天同一形态第三次**（`grep stderr` 命中 `census-stderr.txt`、`pgrep -f` 命中别车道的 codex、这次），共性都是"判据的取名面比它的主张宽"。收敛办法：先写下要找的**确切字符串**，再决定 grep 怎么写。（06:59–07:19）：期间 `tests/unit` 目录级会多一条 `/tmp/test-vault*` 的 teardown ERROR。本卡阶段 1 的收工跑在窗口关闭后启动，未受影响。

---

## 6. DoD-3 双段

### 4-A Claude 已代验（全部引用 evidence 路径与末行）

- [x] 分包 pyright：`evidence-pyright-rest/pyright-per-pkg-p1-*.txt`（六包 5 个 `0 errors` + api 21 及其构成）
- [x] AST 前后：`field-positional-base-*.txt`（366/27）→ `field-positional-p1-*.txt`（14/1）
- [x] 多重集两态：`multiset-p0-state1-*.txt`（NEW=6 逐条）/ `multiset-p1-state2-*.txt`（NEW=0）
- [x] tests diff：见 §7（`unit-close-p1-*.txt` 等，与红基线 `unit-red-baseline-da690bf8.txt` 对账）
- [x] openapi：阶段 0 `openapi-required-diff-p0-*.txt`（required 差异 **0** 条、schemas 无增删）；阶段 1 `--snapshot` rc=0 `DRIFT: none`
- [x] 负控：`negctl-*.txt`（两条都点着 + 还原逐字节对账）
- [x] ruff：`ruff-p1-*.txt` + 集合差
- [ ] Codex 首部：见 §8

### 4-B 你来验（零技术词，约 5 分钟）

这张卡**没有加任何新功能**，它做的事情用一句话说是：**把代码里"这个东西是什么类型"标注错了的地方改对**。所以你要验的不是"新东西好不好用"，而是**"旧东西有没有被碰坏"**。

按你平时的顺序走一遍，每步只需要问自己"和昨天一样吗"：

1. **打开一张你常用的原白板** → 内容、连线、颜色和昨天一样吗？
2. **跑一次索引** → 跑完了吗？条数和你印象里差不多吗？（不用记准数，"没有突然变成 0"就行）
3. **看一眼今天的复习建议** → 有东西出来吗？还是空的？（空的话请立刻说 —— 本卡碰过复习相关的数据模型）
4. **随手问一次 AI**（挑一个概念让它解释）→ **回答是完整的一段话吗？有没有中途断掉、少了半截？**
   > 这一步请多花 10 秒。本卡在"怎么从 AI 的回复里把文字拼起来"那段代码上，一度改了一个"看起来更干净"的写法，后来发现它在某些情况下**会悄悄少拼一段文字**，已经改回去了。所以"回答完不完整"是这张卡最值得你亲自看一眼的地方。
5. **做一道检验题、给它打个分** → 分数存下来了吗？（本卡改了评分结果的数据结构：原先四个评分维度可以"不传"，但一旦真的不传就会报一个指错地方的错；现在改成"必须传"，报错会更早也更准）

**应该看到**：全程没有任何新的红字/报错弹窗，每一步都和昨天一样地出现。

一句示例：「我照常打开一张原白板、跑一次索引、看一眼复习建议、又让 AI 解释了一个概念 → 一切和昨天一样出现，AI 的回答是完整的一段没有断 → 我感觉这次『把代码里所有标错的类型改对』没有碰到我用的任何功能，踏实。」

**felt-sense（两处，请对照你的实际感受）**：

- **第一处 —— "安静"**：这张卡做对了的样子，是**什么都没发生**。如果你在任何一步冒出"咦，这里以前不是这样"的念头，哪怕说不清哪里不对，那就是本卡出了问题，请直接说出那个"咦"，不用去看任何日志或截图。
- **第二处 —— "少了半截"**：第 4 步 AI 回答那里，我要的不是"它答得好不好"，而是**有没有一种话说到一半被切掉的感觉**。这种缺失很滑，因为剩下的部分读起来是通顺的。如果有这种感觉，请把那次提问原样告诉我。

> 另外三件本卡**明确没有修**、你可能会撞到的旧毛病（不是本次引入的，已单独登记）：
> ① 回滚/快照相关的功能一直是不可用状态（会返回"服务不可用"）——本卡只让代码通过检查，没有让它复活；
> ② 保存"连线理由"的那个功能，写入知识图谱那一半是坏的；
> ③ 切换 vault 的那个内部工具一直报失败。
> 这三条如果你碰到了，属于**已知旧账**，不是本次改动造成的。

## 7. tests 对账（阶段 1 收工）

| 集合 | 基线 | 收工 | nodeid diff | 存档 |
|---|---|---|---|---|
| `tests/unit` 目录级 | 202 nodeid（主 session 于 `da690bf8` 采集） | **202** | **空**（0 条 `>`） | `unit-close-p1-20260908T072123.txt` |
| `tests/unit` skipped | 48 | **48** | — | 同上（防"类/模块级 skip 关掉原本绿的"盲区） |
| `tests/api` | 0 红 | **0 红**（268 passed） | — | `api-close-p1-20260908T072123.txt` |
| 29 个引用 models 的文件 + `tests/test_rollback_*.py` ×5 | 20F/631P/2S + 65F/27P = **85F/658P/2S** | **85F / 658P / 2S** | **空**（0 条 `>`） | `models29plus-rollback5-close-p1-20260908T074246.txt` |

- `tests/test_rollback_*.py` 的基线**不在**开工那几跑里（它们不匹配 models 模块正则），所以另建了一棵 `git archive da690bf8 backend` 的 scratch 树单独采集（`rollback5-base-da690bf8-*.txt`，65F/27P），并带**前置自证**：该树的 `rollback.py` 里 `grep -c 'TAIL T1'` = 0（确认是基线版），当前树 = 1。
- 合计口径自洽：20+65 = 85、631+27 = 658，与收工跑逐项相同；nodeid 级 diff 也为空。
- **W4 门计数三跑一致**：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)`——与开工基线**同数**，且 `blocked=1` 表示门拦住了，**没有真连 7691/7687**。

### ⚠️ `tests/contract/test_openapi_contract.py`：未纳入判据（如实登记）

卡文把它写成"若可跑"。实测它是 schemathesis property-based、对全部 194 条路径各生成 10 个样例，当前树与基线树各跑 >10 分钟仍未收敛；且它把**必需**的 29 文件 + rollback5 判据一起卡在同一条命令里。处置：**停掉两跑**，把半截存档改名为 `ABORTED-models29plus-contract-p1-*.txt.partial`（防被误当证据），必需集单独重跑。
⇒ 本卡**未对账** contract 测试，已进 §9「本卡未证明什么」。注：它用的是 `schemathesis.openapi.from_asgi("/api/v1/openapi.json", app)`，即从**活 app** 取 schema，不读 `backend/openapi.json` ⇒ 本卡对快照文件的改动不经由它体现。

---

## 7-bis. Codex round-1 逐条处置（BLOCKER 0 / HIGH 0 / MEDIUM 1）

> 存档 `_bmad-output/审查/codex-review-CARD-PYRIGHT-DEBT-rest-r1.md`，绑定 `41cc849c`。
> **这一轮抓到了我两处真错**，都不是"措辞不严谨"，是判断错误。逐条如下。

### MEDIUM-1 `neo4j_client.py:599` driver 钉在重试循环外 —— ✅ **成立，已修**

Codex：把 `driver` 绑在闭包**外**改变了原先"每次重试重新读 `self._driver`"的行为；请求 A 在重试等待期间若 `cleanup()` 关掉旧连接、别的请求建了新连接，A 仍会向已关闭的旧实例开 session。

**我错了**。我当时把它写成"语义相同，顺带把整次重试用同一个 driver 钉死"——那句"顺带"正是行为变化本身，我却把它当成好处描述了。
**整改**：把 `driver = self._driver` 移进 `_execute_with_retry` 内（每次重试重读），并补 `assert driver is not None, "…"`。⚠️ 按 Codex r2 收窄：新旧异常（`AttributeError` / 带消息 `AssertionError`）**分流不变**（都不在 `RETRYABLE_EXCEPTIONS` 内、都不转 `RetryError`、都跳过 JSON fallback 向外抛），但**异常类型与正文已变**，本卡不宣称「逐字等价」。
**判据**：`awk '/async def _execute_with_retry/,/async with driver.session/' | grep -c 'driver = self._driver'` = **1**（在闭包内）；全文件该赋值恰 1 处。⚠️ 该判据当时被我误标为「负控 4」，Codex r2 LOW-1 指出它并未执行变异——真负控见 §7-ter，结论是**没有任何自动门看得见这个回归**。存档 `negctl-p1r2-*.txt`（已就地标注更正）+ `negctl4-real-*.txt`。

### Q8 等价性 —— ✅ **Codex 的质疑成立，我的证明有洞，已推翻并回退**

Codex：「只有 TextBlock **声明** text」不足以证明实例不可能带额外属性。
**实测坐实**：anthropic 0.88.0 的 12 个块类型 `model_config.extra` **全部是 `'allow'`**；
`ThinkingBlock.model_validate({... , "text": "SMUGGLED"})` → `hasattr(text)=True` 而 `isinstance(TextBlock)=False`，`model_extra={'text': 'SMUGGLED'}`。
⇒ 若服务端在非 `TextBlock` 上多回一个 `text`，换 `isinstance` 会**静默漏掉那段文本** = 运行期行为变化。
**整改**：三处**退回 `hasattr`**，改用行级 `# pyright: ignore[reportAttributeAccessIssue]` + 写明上述实证；删掉不再需要的 `TextBlock` 导入。
**我的原错误在哪**：`model_fields` 回答的是"它声明了什么"，`hasattr` 问的是"这个实例现在有什么"——两个问题。我只枚举了**已声明字段**这一个轴，漏了**额外字段**轴，而"我做过实证"反而给了我假信心。
**新负控（负控 3）**：摘掉一条 ignore → `Cannot access attribute "text"` 精确回到 **11** 条；还原自 scratchpad 副本，sha 逐字节相同。

### Q2 裸 assert 的日志退化 —— ✅ **成立，已修**

Codex：`metadata.py:570` 遇 None 时异常从 `AttributeError` 变成**无消息的** `AssertionError`，日志内容有变化。
**整改**：本卡新增的 4 条 assert 全部补上消息（`"LanceDB 连接未初始化(force_rebuild)"` / `"…(index status)"` / `"IntelligentParallelService 单例未构造"` / `"Neo4j driver 在重试期间变为 None"`），使日志信息量**不低于**它替换掉的 `AttributeError`。

### Q4 openapi 证明强度 —— ✅ **成立，已量化**

Codex：`exam_models.py:150-153` 给四个属性新增了 `description`，模型 JSON Schema 除 `required` 外确有变化；是否进入实际 OpenAPI 本轮无法确认。
**量化**（存档 `q4-schema-delta-*.txt`，基线树 vs 当前树逐键比）：`AutoScoreResult.model_json_schema()` 恰好变 **5 处** = 4 个 `description` 新增 + `required` 从 `[node_id, exam_id, overall_score, grade]` 变为加上四个维度名。
**是否进 OpenAPI**：`AutoScoreResult` 与 `RubricDimension` **都不在** `backend/openapi.json` 的 `components.schemas`（354 个 schema 里均不存在，实测）⇒ 对外契约零影响。验收单原先只说"required 差集为 0"，现更正为上面这句更强也更准的表述。

### Q1 / Q3 / Q9 与 multiset 末行 —— 读取面所限，本轮补齐

- **Q1**：Codex 无法独立验证 `metadata.py:574` 的 SDK 签名与 `health.py:1169` 的实际返回类型（不在允许读取面）。r2 把这两条的实测输出直接写进 prompt。
- **Q3**：Codex 无法确认四维必填化全仓无遗漏。本卡补了全仓 grep（`AutoScoreResult` 仅 `services/autoscore.py:141/:197` 两个构造点，`RubricDimension` 仅同文件 8 处，全仓无 `model_validate` / `parse_obj` / `**dict` 生产路径），r2 附上该输出。
- **Q9**：Codex 指出"卡文 §三 不在读取面 ⇒ 不能认定 `exam.py` 延后已获授权"。**这条提醒很对**——r2 把卡文 §三 的原文段落贴进 prompt，让它能独立判定是"阶段安排"还是"放宽判据"。
- **multiset 末行**：存档最后一行是 `rc=`，`base=… work=… NEW=… GONE=…` 在其上方几行。r2 直接引用该行文本。

### 整改后复跑（全部仍绿）

| 判据 | 结果 |
|---|---|
| 分包 pyright | 5 包 `0 errors`；api 21 = 三个延后文件，剔后 **0** |
| 多重集 vs `41cc849c` | **`NEW=0 GONE=0`**（**诊断集合**零新增；按 Codex r2，这不等同于「运行期零副作用」） |
| 多重集 vs `da690bf8`（全卡视角） | **`421 → 232，NEW=1，GONE=190`**；唯一那条 NEW 是 `services/rag_service.py` 的 `ainvoke config`，由本卡 `extraPaths` 引出但**落在 U1 面**，本卡不能改 ⇒ 移交 U1（他们 merge 阶段 0 sha 后会看到） |
| AST | 14，只剩共享 `system.py` |
| ruff | `F401,F821` 全过；format 集合差 37 = 37，**新引入 0** |
| openapi | `DRIFT: none (paths=194 schemas=354)` |
| 负控 3 / 4 | 见上，都点着 |
| tests（整改后重跑） | `tests/unit` **202 = 202** diff 空、skipped 48=48；`tests/api` **0 红**；29 文件+rollback5 **85 = 85** diff 空。三项与整改前逐项相同。存档 `*-p1r2-20260908T075444.txt` |

> ⚠️ **口径更正**：阶段 0 记的"extraPaths 新冒 6 条"到阶段 1 末已过期——其中 5 条（`edges.py` ×3 + `metadata.py` ×2）已由本卡在自己地盘关掉，只剩 1 条在 `services/`。引用历史数字前必须重测。

## 7-ter. Codex round-2 逐条处置（BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 1）

> 存档 `codex-review-CARD-PYRIGHT-DEBT-rest-r2.md`，**绑定 `acbc79be` = 当前 HEAD**。
> 按 D-15（绑最终 HEAD 的一轮 BLOCKER=0 且 HIGH=0）：阶段 1 的轮次条件**已满足**。

### LOW-1 「负控 4」名不副实 —— ✅ **成立，已真跑并推翻我自己的记法**

Codex：所谓「负控 4」只检查当前赋值位置、末行写着"未改动 OK"，**并未执行标题所称的移出闭包变异**；拿它证明"错误变异已被判据拒绝"会把**没跑过的验证记成通过**。

**Codex 是对的，而且这正是本项目反复记的"把没做的说成做了"。** 「负控」有确切含义 = 把修复破坏掉、看判据变红；我那段只是结构断言。

**整改 = 真跑一遍**（存档 `negctl4-real-*.txt` + 对照组 `negctl4-control-*.txt`）：

| 判据 | 未变异 | 变异（driver 挪回闭包外，重演 r1 缺陷） | 结论 |
|---|---|---|---|
| 变异体语法 | — | `ast.parse` 通过 | 排除"因语法错而红"的假杀 |
| `pyright app/clients/neo4j_client.py` | `0 errors` | **`0 errors`** | ⛔ **类型门看不见** |
| `tests/unit -k neo4j` | 19F / 255P / 5E | **19F / 255P / 5E（逐项相同）** | ⛔ **测试也看不见**（它们本来就红） |
| 结构判据（闭包内该赋值计数） | 1 | **0** | ✅ 唯一看得见的 |
| 还原 sha | `2f5bdc2f…` | — | 与变异前**逐字节相同** |

**这条负控最有价值的产出不是"通过"，而是这个事实**：`driver` 那类"绑定位置改变语义"的回归，**不在本仓任何自动门的覆盖面内**——r1 那条 MEDIUM 是 Codex **读代码**抓到的，不是门抓到的。唯一能看见它的结构计数判据，是我在被指出**之后**才补的。已写进 §9「本卡未证明什么」。

### Codex r2 判"证据不足"的两项 —— ✅ **已补测，现已足够**

**(c) OpenAPI「对外契约零影响」**。r2：静态文件不含那两个名字，只能证明该制品；缺"基线与当前树**各自经应用入口重新生成**再逐键比"。
**已补**（存档 `codex-r2-cd-closure-*.txt`）：基线树（自证 `default_factory=RubricDimension` 计数 = 4）与当前树各跑 `check-openapi-drift.py --write` 到独立临时文件，剔除 `x-generated-at` / `x-generator` 后**逐键差异 = 0**；`paths 194 → 194`、`schemas 354 → 354`，两文件**字节数完全相同（903318 = 903318）**。⇒ 整张卡对 OpenAPI **零影响**，比原先的 `DRIFT: none` 强一档。

**(d) `metadata.py` 的 `ignore_missing` 假阳判定**。r2：两个 `drop_table` 签名只证明"具体类支持该参数"，还缺"运行期 `_db` 确实绑定 `LanceDBConnection`"。
**已补**：`lancedb.connect(...)` 运行期返回 `lancedb.db.LanceDBConnection`（`isinstance` = True），其 `drop_table(self, name, namespace=None, ignore_missing=False)` **含**该参数；生产侧绑定点 `lancedb_client.py:900 / :928` 均为 `self._db = lancedb.connect(self.db_path)`。⇒ 链条闭合，假阳判定成立。

### Codex r2 要求收窄的表述 —— ✅ **已逐条改口径**

| r2 指出 | 本验收单的更正 |
|---|---|
| `neo4j_client` 异常类型与正文确实变了（`AttributeError` → 带消息 `AssertionError`），**不能称"逐字等价"** | 改为：**分流不变**（两者都不在 `RETRYABLE_EXCEPTIONS` 内、都不转 `RetryError`、都跳过 JSON fallback 向外抛），但**异常类型与正文已变**；本卡不再宣称"逐字等价" |
| `claude_client.py` 三处**可执行逻辑**与基线相同，但**整份文件并非字节相同**（多了注释与类型声明） | 采纳，改为"三个循环的判断与累加表达式、AST 与 `da690bf8` 相同；`TextBlock` 在可执行代码中引用 0 次" |
| ignore 是 **28 条 / 29 个规则项**（`suggestions.py` 一行两规则） | 采纳，清单已注明 |
| 四条 assert **不能统一表述为"原位置遇 None 都会崩"** —— `intelligent_parallel.py` 基线处只是 `return _service`，不是属性解引用 | 采纳：前三条是"原本也会崩"，**第四条**成立的是"**不变式保证非 None**"，不是"遇 None 会崩"。这是我原表述的过度概括 |
| multiset 算术成立，但**只支持诊断集合结论，不能证明运行期"零副作用"** | 采纳，措辞已改为"诊断集合零新增"，不再说"零副作用" |
| 四维必填化确实改变 schema 与缺字段时的错误内容，**不是严格的运行期逐字等价** | 采纳，本就是本卡唯一的**有意**语义收紧（错误更早更准），已在 §2 写明 |
| **不能称"整个非 services 范围已清零"** | 采纳，全文改为"非 services 面**除三个按卡文延后的文件外** = 0" |

## 8. Codex

- **round-1**：绑 `41cc849c`。BLOCKER 0 / HIGH 0 / **MEDIUM 1**。逐条处置见 §7-bis——**两处是我的真错**（driver 钉在闭包外；`hasattr`→`isinstance` 的等价性证明只覆盖一个轴），均已整改并落 commit `acbc79be`。
- **round-2**：绑 **`acbc79be` = 当前 HEAD**。**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 1**。逐条处置见 §7-ter——LOW-1（「负控 4」名不副实）已真跑变异整改，并补齐 r2 判「证据不足」的 (c)(d) 两项。
- **D-15 轮次判定**：绑最终 HEAD 的那一轮（round-2）**BLOCKER = 0 且 HIGH = 0** ⇒ **阶段 1 的轮次条件已满足**。round-2 之后**只改了 `_bmad-output`**（本验收单 + 存档首部 + 三份新证据），代码树自 `acbc79be` 起零改动，判据：`git diff --stat acbc79be HEAD -- . ':(exclude)_bmad-output'` 为空。
- ⚠️ 阶段 2 会 `git merge` 候选树并清 `review.py` / `system.py`，届时**必须再送一轮并绑那时的最终 HEAD**（上限 5 轮，本卡已用 2 轮）。
- prompt：r1 / r2 各一份，五分节 + 最小读取面写死。协议 §2 点名的四类措辞两份自检均为 0（「构造」已中性化为「实例化」/「实参形态」）；`grep -c 'gpt-5.6'` = 0。
- 存档首部按协议 §2.1 六行 blockquote，三字段（模型 / reasoning_effort / codex 版本）齐，会话头自证抄自 `.stderr` 前三行（`.stderr` 本身不入库，`.gitignore:261-263` 覆盖）。

### openapi 逐 commit 记录

| commit | `backend/openapi.json` 变化 | `required` 差集 | schemas 增删 |
|---|---|---|---|
| `5638ac6c`（阶段 0） | 2 行：`x-generated-at` + `review_overview.py` 的**存量** description 漂移（来自 `d209622d`，U6 地盘，本卡未碰该文件；由 spec-sync 恒写行为带入） | **0** | 无 |
| `41cc849c`（阶段 1） | **1 行：只有 `x-generated-at`** | **0** | 无 |
| `acbc79be`（r1 整改） | **1 行：只有 `x-generated-at`** | **0** | 无 |

**全卡终局判据（Codex r2 (c) 收口，比逐 commit 更强）**：基线树 `da690bf8` 与当前树**各自经应用入口重新生成** openapi 到独立临时文件，剔除 `x-generated-at` / `x-generator` 后**逐键差异 = 0**；`paths 194 → 194`、`schemas 354 → 354`，两文件**字节数完全相同（903318 = 903318）**。⇒ 整张卡对 OpenAPI **零影响**。存档 `codex-r2-cd-closure-*.txt`。

---

## 9. 本卡未证明什么

1. 只证 pyright 归 0，**未证** anthropic / litellm / neo4j / lancedb 的真调用路径行为不变——类型层改动没跑真 API。
1-bis. **`claude_client.py` 的 `hasattr` 保持不动，但也因此没有任何门盯住它**：本卡证明了「换 `isinstance` 会漏文本」（`extra='allow'` 实测），却**未证明**服务端当前是否真的会在非 `TextBlock` 上多回 `text`——只证明了它**可能**发生。这条留作现状，不新增门。
1-ter. **`neo4j_client.py` 的 driver 重读只做了结构判据，未做并发行为门**：整改后我用「闭包内该赋值恰 1 处」证明结构对了，**未构造**「A 重试期间 B 重连」的并发场景实测它确实用上了新 driver。写这样一条门要起真 driver 生命周期，超出本卡（零 Neo4j 面）。
2. **未证** `rollback` 端点该退役——只让类型过门，端点与 503 行为一字未动（运行期实证 `_rollback_available=False`）；保留还是退役是产品裁定（T1）。
3. **未证** 366 处位置默认改写后 openapi schema 逐键相同——只证了 `--snapshot` 无漂移 + `required` 差集为 0 + schemas 无增删；`description`/`examples` 等键**未逐键比**。
4. `review.py:1543` 族（对 dict 取属性）是 api 侧真 bug，本卡**未修**，阶段 2 也只 ignore + 登记（归 U9 / 主 session）。
5. **未跑** `tests/integration` / `tests/e2e`。
6. **未清** `backend/tests` 与仓根 `tests/` 的 pyright 存量（T11）。
7. `RubricDimension` 必填化**未证明没有外部调用方**——只 grep 了 `backend/app` + `backend/tests`。
8. 多重集的键是 `(相对路径, rule, message)`，**不含行号** ⇒ 同文件同 rule 同消息的"位置搬家"看不见（已知盲区）。
9. `provider_factory.py:256/:261` 只让类型过门，**未证明**"有没有设了 `OPENAI_API_KEY` 的部署环境"——只查了仓内 `.env` / `.env.example` 与本机进程 env（都为 0）。本卡**没有**给 `Settings` 加该字段，故不存在"分支从不激活变激活"的风险；但也因此该 provider 分支**至今恒不激活**这件事本身仍未被任何门盯住。
10. **阶段 1 末 `api` 包不是 `0 errors`**：`exam.py` 10 条按卡文 §三 延到阶段 2（U1-A 声明交集）。本卡未证明 U1-A 的 `TYPE_CHECKING` 方法声明落地后这 10 条会自动消——那要等阶段 2 merge 候选树后实测。
11. 本树全量 `pyright app` **不为 0**（`services/` 211 条是 U1 面，U1-A 在本卡之后才 squash）。本卡只交「rest 面除三个延后文件外 = 0」+「残余全落 services/ 与那三个文件」两条；**未证明**这些残余会被 U1-A 清掉，也**未证明**集成候选树上全量会归 0——那是主 session 的合入门。
12. **未跑完 `tests/contract/test_openapi_contract.py`**（见 §7 末），故未证明本卡对 194 条路径的契约面零影响。
13. 4 处真缺陷（§10）只登记未修，**未证明**它们在生产上确实以我推断的形态发生——`edges.py:106` 与 `infra_tools.py:56/57` 的结论来自「运行期 `hasattr` 实证 + 读 `except` 元组」，不是从生产日志里看到的 traceback。

---

## 10. 台账待登记条目

1. **阶段 0 commit `5638ac6c`**：全量 421→356；本卡面 174→145；models 包 11→0；AST 366→100。新冒 6 条逐条见 §2。
2. **`pyrightconfig.json` 改动**：只加 `"extraPaths": ["backend/lib"]` + 12 行注释（解析器路径 ≠ 关规则，D-21 仍成立）；`include` 里的 `"src"` 死枝（`git ls-files src`=0）**只登记不改**。
3. **位置默认改写清单**：阶段 0 = 12 文件 / 266 处；阶段 1 = 14 文件 / 86 处；共享 `api/v1/system.py` 14 处留给阶段 2。前后 AST：366/27 → 100/15 → 14/1。
4. **真 bug ①** `models/exam_models.py` `AutoScoreResult` 四维 `default_factory=RubricDimension` → `Field(...)` 必填；回归测试 `backend/tests/unit/test_exam_models_rubric_required_u2a.py`（8 用例）。
   **更正**：勘探稿的"真 bug ② `metadata.py:467`"**不成立**——那是 `metadata_models.py:122/123` 的位置默认假阳，阶段 0 机械改写顺带清掉（负控 1 反向证明了这条因果）。
5. **ignore 清单全文**：`evidence-pyright-rest/ignore-table-p1.md`（25 条；基线 `da690bf8` 为 0）。
6. **openapi.json diff 形状**：阶段 0 commit 带 2 行变化 = `x-generated-at` + `review_overview.py` 的**存量** description 漂移（来自 `d209622d`，U6 地盘，本卡未碰该文件，由 spec-sync 的恒写行为带入）；`required` 差集 0、schemas 无增删。阶段 1 `--snapshot` `DRIFT: none`。
7. **TAIL 移交**：
   - **T1** `rollback.py` 族（`src/` 不存在，端点恒 503，G-PIPE 断裂管道）
   - **T3** `review.py:238` 死 import + `:184/:408` `GeminiClient(model=)`（阶段 2 处理）
   - **T6** `exception_handlers.py:305-307` starlette stub 逆变（已 `cast`）
   - **T8** `neo4j_client.py:608` `cast(LiteralString, query)`
   - **T10** `extraPaths` 新冒 6 条（lib 侧：`LanceDBClient` 无 `delete`/`upsert`/`get_db`）
   - **T11** `backend/tests` + 仓根 `tests/` 存量未清
   - **T14** `provider_factory.py:256/:261`（openai provider 分支恒不激活；加 `Settings.OPENAI_API_KEY` 会在设了该环境变量的部署上多注册一个 provider = 运行期行为变化，产品裁定。**本卡未改 `config.py` 一个字节**）
   - **T-EDGES（新，建议优先）** `api/v1/endpoints/edges.py:106` `neo4j.execute_query` —— `Neo4jClient` 只有 `run_query(query, **params)`；本函数 `except` 元组 `(RuntimeError, ConnectionError, TimeoutError, OSError)` **不含 `AttributeError`** ⇒ 异常穿过 `asyncio.gather` 把双写端点打成 **500**（不是记成半成功 207）。修法不是改名（`run_query` 收 `**params` 而现调用传的是位置 dict），需连调用形态一起改 + 决定是否真连 Neo4j ⇒ 另立卡。
   - **T-SWITCHVAULT（新）** `mcp/tools/infra_tools.py:56/57` —— `vault.switch_vault` 被 P0-3 隔离后恒返回 `JSONResponse`，读 `.vault_name`/`.vault_id` 必 `AttributeError`，被 `except Exception` 吞成 `success=False` ⇒ 该 MCP 工具**恒报失败**。
   - **T-UNREACH（新）** `boards.py:86` / `board_manifest_tools.py:67` 的 `except pydantic.ValidationError` 是**死分支**（`ValidationError` 是 `ValueError` 子类，pydantic 2.12.5 实测 MRO）⇒ 注释里写的"纵深兜底 500/结构化错误"从未生效，实际走的是上面的 `except ValueError`（422 / "非法参数"）。调顺序 = 改行为，本卡不动。
   - **跨车道** `dependencies.py:1032` 的 ignore 根因在 `services/canvas_service.py` 的隐式 Optional（U1 地盘）；U1 修好后该 ignore 会被 `reportUnnecessaryTypeIgnoreComment` 自曝，阶段 2 清理。
8. **Codex 轮次与绑定 SHA**：round-1 绑 `41cc849c`（B0/H0/M1）→ 整改 `acbc79be` → round-2 绑 `acbc79be`（B0/H0/M0/L1）。D-15 条件满足。阶段 2 必须再送一轮绑那时的最终 HEAD（已用 2/5 轮）。
8-bis. **⚠️ 门覆盖面缺口（真负控实测，建议进 PYRIGHT-TAIL）**：把 `neo4j_client` 的 `driver` 挪回闭包外（重演 r1 MEDIUM 的缺陷形态）后，`pyright` 仍 `0 errors`、`tests/unit -k neo4j` 结果与未变异态**逐项相同**（19F/255P/5E）——即「绑定位置改变语义」这类回归**不在本仓任何自动门的覆盖面内**，r1 那条是 Codex **读代码**抓到的。唯一看得见它的是本卡事后补的结构计数判据。存档 `negctl4-real-*.txt` + `negctl4-control-*.txt`。
8-ter. **openapi 全卡终局**：基线树与当前树各自经应用入口重生成后逐键差 = 0、字节数相同（903318）。
8-quater. **`ignore_missing` 假阳链条闭合**：`lancedb.connect()` → `LanceDBConnection`（`isinstance` True，其 `drop_table` 含该参数），生产绑定点 `lancedb_client.py:900/:928`。
9. **阶段 2 末的 `services/` 残余全清单**：阶段 2 才产出（本 v1 只记当前 211 条的分组计数，逐条清单见 `group-p1-*.txt` 的 services 侧）。
10. **格式门与 `LEFTHOOK_EXCLUDE`**：阶段 0 commit 用了 `LEFTHOOK_EXCLUDE=python-lint`（原始输出 + 集合差 + 不动点内容口径三份证据齐）；`python-typecheck` **未绕过**且实测 `0 errors`。
