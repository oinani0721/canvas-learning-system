# U9-C「VaultScopeUnresolved 拒启」评估 — 前提更正 + 真实表征

> 批次: `BATCH-2026-09-11-第十四批` · 车道 **T4**（4/4）· 卡 **CARD-U9C-EVAL**
> 树: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`（分支 `card/t4-g3`）
> 开工 HEAD（= T4-C CARD-U9B-OPENSPEC 末 commit）: `9400ba26b816e8cad605b2a81e5fdf14e396541e`
> 实测日期: **2026-09-16**（下列每条命令均在本树本 HEAD 上实跑，输出逐字抄录，**无一条来自勘探转抄**）
> 授权: **R-07**（U9 系列 = 第十四批产品动作/评估面授权来源）· **D-38**（U9-C 以评估卡落地；legacy 兼容重做作为设计级议题不排本批）
> 本卡**零生产改动**：`backend/app/**` 全程只读。交付 = 本文档 + 一个新回归测试文件。

---

## 〇 一句话结论

U9-C 原立面「**CLI/后台无 vault 上下文构造 ReviewService ⇒ 拒启**」**不成立**——
全仓没有任何 CLI/后台脚本会构造 `ReviewService`。真正的拒启面是
**后端启动之后、首个命中 `get_review_service()` 的 HTTP 请求**：进程照常起得来，
该请求得到 **500**，而 `CARD-G3-5` 指引原文**不在响应体里**（被
`generic_exception_handler` 屏蔽），只进 `logger.error` 与 `bug_log.jsonl`。
此后 review 面**每一个**请求都重复这一过程，直到运维跑迁移脚本裁定归属。

---

## ① 前提更正 — 真拒启面不是 CLI，是首个命中工厂的请求

### 1.1 `scripts/` 与 `backend/scripts/` 零构造方

```zsh
git --no-pager grep -c --no-color "ReviewService(" -- 'scripts/*' 'backend/scripts/*'
```

实测输出：**无输出**，`rc=1`。
存档 `evidence-u9c-eval/grep-scripts-20260916T144314.txt`（0 字节 = 0 命中）。

> **验伪锚（同口径换已知正例，证「0 命中」不是正则失效或 ANSI 归零）**：
> ```zsh
> git --no-pager grep -c --no-color "ReviewService(" -- 'backend/app/services/review_service.py'
> ```
> → `backend/app/services/review_service.py:1`（rc=0）。同一 pattern 在正例上命中，
> 故 1.1 的 0 是**真的没有构造方**。
> （`--no-color` 依协议 §2.2：多 worktree 共用 `.git/config`，`color.ui` 会被并发车道改写，
> ANSI 前缀会让行首/字面量判据静默归零；重定向到文件不豁免。）

### 1.2 生产唯一实例化点在 HTTP 依赖链上

```zsh
git --no-pager grep -n --no-color "ReviewService(" -- '*.py' | grep -v '/tests/'
```

实测输出（**恰 1 行**）：

```
backend/app/services/review_service.py:2996:        _review_service_singleton = ReviewService(
```

存档 `evidence-u9c-eval/grep-prod-ctor-20260916T144314.txt`。
该行位于 `async def get_review_service()`（`:2939`）的双检锁内部；
`reset_review_service_singleton` 在 `:3006`。

### 1.3 lifespan 不预先实例化 ⇒ 进程启动本身不崩

```zsh
grep -nc 'get_review_service\|ReviewService(\|review_service' backend/app/main.py
```

实测输出：**`0`**（rc=1）。存档 `evidence-u9c-eval/grep-main-20260916T144314.txt`。

> **验伪锚（承重，必须用与判据**逐字相同**的三支交替 pattern）**：
> ```zsh
> grep -nc 'get_review_service\|ReviewService(\|review_service' backend/app/services/review_service.py
> ```
> → **`32`**（rc=0）。
> 再加一条语法级自证，排除「本机 grep 把 `\|` 读成字面量 ⇒ 假 0」：
> ```zsh
> /usr/bin/grep --version | head -1        # grep (BSD grep, GNU compatible) 2.6.0-FreeBSD
> /usr/bin/grep -c 'ZZZNOEXIST\|ReviewService(' backend/app/services/review_service.py   # → 1
> ```
> 左支是不存在的串而结果为 1，证明 `\|` 在本机确实是**交替**而非字面量。
> 只锚单支（如只 grep `get_review_service`）证明不了这一点——而那恰是「1.3 的 0」
> 最可能的失效面。

### 1.4 更正后的表述

| | U9-C 原立面 | 本卡实测 |
|---|---|---|
| 触发者 | CLI / 后台脚本 | **HTTP 请求**（首个命中 `get_review_service()` 的那个） |
| 失败时刻 | 进程启动期 | 请求处理期 |
| 进程后果 | 起不来 | **照常起得来**，worker 不死 |
| 用户可见 | 服务不可用 | 该请求 500；review 面**持续** 500（见 ④） |

---

## ② 双抛出点 — 都在实例化链上

```zsh
grep -n 'raise VaultScopeUnresolved(' backend/app/services/review_service.py
```

实测输出（**恰 2 处**）：

```
570:            raise VaultScopeUnresolved(
593:            raise VaultScopeUnresolved(
```

存档 `evidence-u9c-eval/grep-raise-20260916T144314.txt`。

> **行号更正**：勘探 recon C 记 `:573` / `:596`（取自 `286178d8`）；
> 本树（B14_BASE `08100483` 系）实测 **`:570` / `:593`**，该区 **−3**。
> 卡文 §〇 已做同向更正，本卡逐条 `sed -n` 复核确认卡文值正确。

### 2.1 两条分支的语义

| 抛出点 | 分支 | 触发条件 | 为什么不能「跳过」 |
|---|---|---|---|
| `:570` | **作用域解析不出来** | 存在 legacy 裸 `concept_id` 键，且 `_resolve_vault` 返 `None` | 连「归给谁」都答不上；若只是「这次不加载」，下一次成功写入的全量快照会把这些 legacy 从磁盘**永久删除**（Codex r2 H4） |
| `:593` | **同名冲突** | 作用域解析成功，但 legacy 裸键与该 vault 桶内已有条目同名 | 桶内那份有**明确** vault 身份，legacy 那份只是**推定**归属；保留任一方都是替人做裁定，且被跳过的那份同样会在下次全量写入时被删 |

### 2.2 实例化链（逐行 `sed -n` 复核，全部与卡文 §〇 一致）

```
:352   class _VaultScopedCardStates          （批次注释 :348 CARD-G3-5 第十三批）
:388       def _resolve_vault(context)       → 解析失败返 None
:521       def from_persisted(cls, raw)      → :570 / :593 两处 raise
:776   def __init__(                          ReviewService 构造函数
:850       self._card_states = self._load_card_states()
:876       def _load_card_states()
:893           states = _VaultScopedCardStates.from_persisted(loaded)
```

⇒ 两处抛出都发生在 `ReviewService.__init__` **尚未返回**的时候，
所以是「实例化失败」而不是「某个方法调用失败」——这正是 ④ 中
singleton 恒 `None` 的直接原因。

### 2.3 消息内容（两条都给出了运维出路）

本卡新测试实跑捕获的 `:570` 分支消息原文（`evidence-u9c-eval/u9c-antigate-20260916T144639.txt`）：

```
CARD-G3-5: .../backend/data/fsrs_card_states.json 含 1 条 legacy 裸 concept_id 键,
但当前作用域解析不出来 —— 无法判定它们归哪个 vault。拒绝启动 (不加载会让下一次
成功写入把它们从磁盘删掉)。请先跑 backend/scripts/migrate_fsrs_card_states_vault_key_g35.py
--apply --vault-id <vault> 裁定归属。
```

> **实测细节（值得记一笔）**：`:593` 分支的迁移脚本名在源码里被拆成**两个相邻字符串
> 字面量**（`"...请先跑 backend/scripts/"` + `"migrate_fsrs_card_states_vault_key_g35.py 裁定归属。"`），
> 单行 `grep` 找不到完整串，但运行时拼接后成立。新测试对两条分支都断言了拼接结果，
> 防未来有人换行时把指引拆断而 grep 类判据看不出来。

---

## ③ 关键发现 — CARD-G3-5 原文被从 500 响应体屏蔽

这是本卡**推翻设计稿措辞**的一条，优先级最高。

### 3.1 没有专用处理器

```zsh
grep -n 'VaultScopeUnresolved' backend/app/main.py backend/app/core/exception_handlers.py backend/app/dependencies.py
```

实测：**无输出**（0 命中）。而

```zsh
sed -n '359p' backend/app/core/vault_scope.py
```
→ `class VaultScopeUnresolved(Exception):`

⇒ 它是裸 `Exception` 子类且无专用 handler，逸出请求处理器后必然落到兜底处理器。

### 3.2 兜底处理器刻意不暴露内部细节

`backend/app/core/exception_handlers.py`（只读摘录）：

- `:200` `async def generic_exception_handler(request, exc)`
- `:312` `app.add_exception_handler(Exception, generic_exception_handler)` ← 以 `Exception` 注册
- `:262-266` 响应体构造：

```python
    body: Dict[str, Any] = {
        "code": 500,
        "message": "Internal server error",
        "bug_id": bug_id,  # 用于用户反馈和问题追踪
    }
```

- `:268` `return JSONResponse(`（`:267` 是空行——勘探写「返回 :267」，本树
  `sed -n '266,268p'` 实测更正为 **`:268`**）

消息原文的去向只有两处，都不是响应体：
- `:250` `logger.error("unhandled_exception", ..., error_message=str(exc), ...)`
- `:243` `bug_id = bug_tracker.log_error(endpoint=..., error=exc, ...)` → `data/bug_log.jsonl`

### 3.3 运行时实证（本卡新测试同一次请求的双侧观测）

新测试 `backend/tests/regression/test_u9c_startup_rejection_eval.py::
TestHttpLayerMasksMessage::test_unresolved_scope_surfaces_as_masked_500_not_crash`
用最小 `FastAPI()` + 真 `register_exception_handlers(app)` + 真
`_VaultScopedCardStates.from_persisted` 作异常源（**不调** `get_review_service()`，
避免连 7691/LanceDB），实测：

**响应体（屏蔽后）**：
```
{"code":500,"message":"Internal server error","bug_id":"BUG-894D9A2C"}
```

**同一次请求的日志侧（消息原文确实产生了）**：
```
{"bug_id": "BUG-894D9A2C", "endpoint": "/_u9c_probe", "error_type": "VaultScopeUnresolved",
 "event": "bug_logged", "logger": "app.core.bug_tracker", "level": "info", ...}
{"request_id": "unknown", "bug_id": "BUG-894D9A2C", "error_type": "VaultScopeUnresolved",
 "error_message": "CARD-G3-5: .../fsrs_card_states.json 含 1 条 legacy 裸 concept_id 键, ...
 请先跑 backend/scripts/migrate_fsrs_card_states_vault_key_g35.py --apply --vault-id <vault>
 裁定归属。", "path": "/_u9c_probe", "event": "unhandled_exception", ...}
```

traceback 显示抛出点正是 `review_service.py:570`（② 的 None 分支）。

> **先红验伪锚（承重）**：先把断言临时写成 `assert "CARD-G3-5" in resp.text` 跑一次，
> 存档 `evidence-u9c-eval/u9c-antigate-20260916T144639.txt`：
> ```
> E   assert 'CARD-G3-5' in '{"code":500,"message":"Internal server error","bug_id":"BUG-894D9A2C"}'
> ...
> 1 failed, 3 passed
> ```
> **必红且确实红**，红在「响应体里没有这个字符串」这一点上——证明后续翻成
> `not in` 的绿不是恒绿。翻转后 `4 passed`（`evidence-u9c-eval/pytest-u9c-20260916T144743.txt`）。

> **为什么只断言「响应体不含」不够**：若 probe 因别的原因抛（拼错属性名、import 失败……），
> 响应体同样不含该字符串，断言照过 = 假绿。故测试在**同一次请求**里同时钉两侧：
> 路由捕获真实异常对象，断言它是 `VaultScopeUnresolved` **且** `str()` **含** CARD-G3-5；
> 再断言响应体**不含**。两侧合起来才等于「消息产生了，但被处理器屏蔽了」。
> 另断言 `body["code"]==500` 且存在 `bug_id` 键——这是**排他性**判据，
> 证明这个 500 出自 `generic_exception_handler`（`:262-266` 的 body 形状），
> 不是 starlette 的某个默认 500 页面。

### 3.4 结论：设计稿措辞一半成立

| 设计稿「请求 500 带 CARD-G3-5 消息」 | 判定 | 证据 |
|---|---|---|
| 请求返回 **500** | ✅ 成立 | 3.3 响应 `status_code == 500` |
| CARD-G3-5 进**日志 / bug_log** | ✅ 成立 | 3.3 `error_message=...` + `bug_logged` 两条结构化日志 |
| CARD-G3-5 进 **HTTP 响应体** | ❌ **不成立** | 3.3 响应体仅 `code/message/bug_id` 三键 |

⇒ **运维只看 HTTP 响应拿不到任何指引**，必须去翻后端日志或 `bug_log.jsonl`
（凭响应体里的 `bug_id` 可定位到那条记录）。是否要改成友好暴露 = ⑤ 议题 α。

---

## ④ 进程不崩，但 review 面持续 500

### 4.1 进程不崩（实测）

3.3 的同一个测试在 probe 请求之后立刻再请求 `/_alive`，实测 **200 + `{"alive": true}`**。
⇒ 未处理异常被兜底处理器接住，app 继续服务后续请求，worker 不死。
叠加 ①.1.3（lifespan 不预实例化），**后端在含 legacy 坏数据时仍然起得来**。

### 4.2 但 singleton 恒 `None` ⇒ 每个请求重入重抛

`get_review_service()`（`:2939-3004`）只读摘录
（存档 `evidence-u9c-eval/factory-readonly-20260916T145559.txt`）的关键结构：

```
:2952    global _review_service_singleton
:2953    if _review_service_singleton is not None:
:2954        return _review_service_singleton              ← 快路径
:2956    async with _review_service_singleton_lock:
:2958        if _review_service_singleton is not None:     ← 双检
:2959            return _review_service_singleton
          ... 先建 CanvasService / memory_client / graphiti_client ...
:2996        _review_service_singleton = ReviewService(    ← 工厂最后一步
:3003        return _review_service_singleton
```

（上列行号由 `grep -n` **直接对文件**测得，不是从 `sed` 摘录的相对序号换算——
初稿曾按摘录序号推算，整块偏了 1，已更正；`:2996` 恰好未受影响。）

赋值 `_review_service_singleton = ReviewService(...)` 是**工厂的最后一步**，
且 `ReviewService.__init__` 在 `:850` 就会走到 `from_persisted` 抛出
⇒ **赋值永远不会发生** ⇒ singleton 恒 `None`
⇒ 下一个 review 请求进来，两道 `is not None` 检查都不成立，重新走完整条构造链，
再次在 `:570`/`:593` 抛出。

**可用性后果**：不是「一次性 500 然后自愈」，而是 **review 面整片持续 500**，
直到有人跑 `backend/scripts/migrate_fsrs_card_states_vault_key_g35.py` 裁定归属。
每次重入还会重建一遍 memory / canvas / graphiti 依赖（都在 `:2996` 之前），
即每个失败请求都付一次重依赖建立的开销。

> **本卡未执行真工厂**（硬边界禁连 7691 / 7687 / 现网 LanceDB）。
> 4.2 是**只读代码证据 + 控制流推演**，不是运行时实测；如实登记在验收单
> 「本卡未证明什么」。

---

## ⑤ legacy 兼容重做 = 设计级议题（D-38，登记不排本批）

两条出路，**都影响产品行为、都需用户裁**，本卡只登记移交，不动代码：

### 议题 α — 给 `VaultScopeUnresolved` 加专用处理器

把 CARD-G3-5 指引友好暴露进 500 响应体（或换 503 + `Retry-After`），
让运维不必翻日志就知道该跑哪个脚本。

- **赞成**：③ 已证当前「运维从 HTTP 侧零信息」；`bug_id` 虽可回查，但多一跳。
- **反对/风险**：`generic_exception_handler` 的「不暴露内部细节」是**刻意设计**
  （`:210` docstring 明写 `IMPORTANT: In production, this should NOT expose internal error details.`，
  `:261` 行内注释再复述一次 `don't expose internal details, but include bug_id`）。
  消息里含**绝对文件路径**（见 2.3 实测原文含 `/Users/.../backend/data/fsrs_card_states.json`），
  直接透出等于泄漏部署布局。若采纳，应先裁「暴露哪些字段」而不是整条 `str(exc)`。
- **连带**：一旦采纳，本卡新测试的 `assert "CARD-G3-5" not in resp.text` 必须同步翻转
  ——该测试是**当前口径**的钉，不是永久不变量。

### 议题 β — legacy 兼容整体重做

隔离区 / 保留键命名空间 / 多份候选 / 毒条目预检那一整套。

- **历史**：CARD-G3-5 卡内 Codex r2→r5 在这套设计上**每一轮修复都长出新缺陷**，
  用户 2026-09-09 裁定 ③「缩小本卡」，只保留键化核心（vault 分桶 + fail-closed + 迁移器），
  legacy 兼容整体移交。该裁定的原文就写在 `from_persisted` 的 docstring 里（**`:530-534`**）。
- **现状**：当前口径是「凡是归不掉的 legacy 一律 fail-fast」——**最简且可证**，
  代价是可用性（④：整片持续 500）。
- **D-38 裁定**：作为**设计级**议题登记，**不排第十四批**。

### 移交建议

α 与 β **可以分开裁**：α 是小改动（加一个 handler）、只改可观测性；
β 是大改动、改数据处置语义。建议先裁 α（若用户认为「运维看不到指引」是真问题），
β 单独立卡走完整设计流程。

---

## ⑥ 本卡判据口径更正（写给后续卡，防照抄踩坑）

### 6.1 ⛔ 卡文 (e) 的 W4 判据是**假红**判据

卡文 (e) 与 §二写：
> `grep -c 'blocked=' "$PYT"` → **期望 0、rc=1（无该行）**
> 「哨兵只在『有非豁免拦截 / 迟到连接』时才打印该行」

**本树实测：该前提不成立。** `tests/conftest.py:226-227`：

```python
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    terminalreporter.write_line(live_port_guard.STATE.summary_line())
```

**无条件**调用，而 `live_port_guard.py:454-460` 的 `summary_line()` 恒含
`blocked=` 字面量。⇒ **每一跑都必有一行 `blocked=`**，
卡文那条判据在本树恒得 `1`，照抄会读成「本卡误连了服务」的假红。

真正「只在出事时才打印」的是 `live_port_guard.py:1523-1526` 那条
`*** {BLOCK_REASON} —— 最终总账：blocked=... ***`，其中
`BLOCK_REASON = "live Neo4j port connect attempted"`（`:205`）。

**更正后的判据（本卡采用，强度不低于原判据）**：

```zsh
# ① 摘要行存在且三项全 0 —— 既证零连接尝试，又自证哨兵真的跑了
grep -c 'NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)' "$PYT"   # 期望 1
# ② BLOCK_REASON 总账行不出现 = 无非豁免拦截 / 无迟到连接
grep -c 'live Neo4j port connect attempted' "$PYT"                                          # 期望 0
# ②验伪锚：同口径 grep 在哨兵源码上必 >0（证「0」不是 pattern 写错 / 路径落空）
grep -c 'live Neo4j port connect attempted' backend/tests/support/live_port_guard.py        # 实测 1
```

本卡实测：① = **1**、② = **0**、②验伪锚 = **1**、pytest `rc=0`。
原判据 `grep -c 'blocked='` 实测 = **1**（如实记录，不作为通过依据）；
其源码侧验伪锚 `grep -c 'blocked=' tests/support/live_port_guard.py` = **6**（与卡文一致）。

> 为什么更正后的 ① 比原判据**更强**：原判据只说「没有那一行」，
> 一个压根没装哨兵的跑法同样能得 0；更正后的 ① 要求那一行**存在且全 0**，
> 「哨兵真跑了」与「零连接尝试」两件事被同一条判据钉住。

### 6.2 `bug_tracker` 单例会按 CWD 真写车道树

`app.core.bug_tracker.bug_tracker` 是模块级单例，
`log_path` 默认 `"data/bug_log.jsonl"`（`bug_tracker.py:89`）**相对 CWD**；
pytest 从 `backend/` 跑 ⇒ 真 handler 真写 `backend/data/bug_log.jsonl`。
`backend/data/.gitignore:5` 有 `*.jsonl`，所以它**不会弄脏 `git status`**——
也正因如此，污染是**静默**的。

`tests/conftest.py:121-129` 的成熟做法是换 `app.main` 命名空间里的**别名**、
**不碰单例本身**（单例默认路径契约另有测试在锁）。但那个 fixture 覆盖不到
`app.core.exception_handlers` 里的同名别名，本卡测试因此自己照同一形状做了一次重定向。

**隔离自证（本卡实测）**：跑完全部测试后
```zsh
ls -la backend/data/bug_log.jsonl   # → No such file or directory（rc=1）
```
⇒ 零写车道树。换的是**落盘路径**不是**行为**：`log_error` 仍真跑完整记账链
（3.3 的 `bug_logged` 日志即其产物），没有 mock 掉任何被测层。

### 6.3 行号偏移汇总（勘探 → 本树实测）

| 锚点 | 勘探 recon C | 本树实测 | 偏移 |
|---|---|---|---|
| `raise VaultScopeUnresolved(` ①② | `:573` / `:596` | **`:570` / `:593`** | −3 |
| `from_persisted` | `:524` | **`:521`** | −3 |
| `_card_states = _load_card_states()` | `:853` | **`:850`** | −3 |
| `_load_card_states` | `:879` | **`:876`** | −3 |
| `from_persisted(loaded)` | `:896` | **`:893`** | −3 |
| `class _VaultScopedCardStates` | `:356` | **`:352`** | −4 |
| `_resolve_vault` | `:391` | **`:388`** | −3 |
| `get_review_service` | `:2921` | **`:2939`** | +18 |
| `ReviewService(` 实例化 | `:2978` | **`:2996`** | +18 |
| `reset_review_service_singleton` | `:2988` | **`:3006`** | +18 |
| `generic_exception_handler` 的 `return JSONResponse(` | `:267` | **`:268`**（`:267` 空行） | +1 |

卡文 §〇 已按 B14_BASE 做过同向更正，本卡逐条 `sed -n` 复核**全部与卡文一致**；
上表 `勘探` 列为 recon C 原值，留作追溯。

---

## ⑦ 覆盖边界（如实声明，与验收单「本卡未证明什么」同源）

三层里本卡只真跑了两层：

| 层 | 覆盖方式 | 本卡是否执行 |
|---|---|---|
| 实例化层（`from_persisted` 两抛出点） | 真函数真抛，断言消息 | ✅ 真跑 |
| HTTP 层（屏蔽 + 进程不崩） | 真 handler + 最小 app | ✅ 真跑 |
| 工厂中段（`get_review_service` 建重依赖 → `:2996`） | 只读 grep + 控制流推演（④.2） | ❌ **未执行**（会连 7691/LanceDB，硬边界禁连） |

此外本卡**未**断言日志/bug_log 的**落盘侧**（只断言异常自身含消息 + 响应体不含）——
3.3 引用的结构化日志是 pytest 捕获输出，可佐证，但不是本卡的断言对象。

---

## ⑧ 可复核索引

| 内容 | 存档 |
|---|---|
| ① 抛出点 grep | `evidence-u9c-eval/grep-raise-20260916T144314.txt` |
| ① scripts 零构造方 | `evidence-u9c-eval/grep-scripts-20260916T144314.txt`（0 字节） |
| ① 生产唯一实例化点 | `evidence-u9c-eval/grep-prod-ctor-20260916T144314.txt` |
| ① lifespan grep | `evidence-u9c-eval/grep-main-20260916T144314.txt` |
| ③ **先红**验伪锚 | `evidence-u9c-eval/u9c-antigate-20260916T144639.txt` |
| ③④ 后绿（4 passed） | `evidence-u9c-eval/pytest-u9c-20260916T144743.txt` |
| ④ 工厂链只读摘录 | `evidence-u9c-eval/factory-readonly-20260916T145559.txt` |
| (h) tests/unit 目录级 | `evidence-u9c-eval/unit-20260916T144844.txt` + `unit-{base,now}.nodeids` + `unit-new-red.txt`（空） |
| (g) 地盘核 | `evidence-u9c-eval/territory-*.txt` |

本卡新增测试文件：`backend/tests/regression/test_u9c_startup_rejection_eval.py`（4 条用例）。
