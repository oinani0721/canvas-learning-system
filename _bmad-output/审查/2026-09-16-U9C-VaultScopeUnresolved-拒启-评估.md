# U9-C「VaultScopeUnresolved 拒启」评估 — 前提更正 + 真实表征

> 批次: `BATCH-2026-09-11-第十四批` · 车道 **T4**（4/4）· 卡 **CARD-U9C-EVAL**
> 树: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3`（分支 `card/t4-g3`）
> 开工 HEAD（= T4-C CARD-U9B-OPENSPEC 末 commit）: `9400ba26b816e8cad605b2a81e5fdf14e396541e`
> 实测日期: **2026-09-16**（下列每条命令均在本树本 HEAD 上实跑，输出逐字抄录，**无一条来自勘探转抄**）
> 授权: **R-07**（U9 系列 = 第十四批产品动作/评估面授权来源）· **D-38**（U9-C 以评估卡落地；legacy 兼容重做作为设计级议题不排本批）
> 本卡**零生产改动**：`backend/app/**` 全程只读。交付 = 本文档 + 一个新回归测试文件。

---

## 〇 一句话结论

U9-C 原立面「**CLI/后台无 vault 上下文实例化 ReviewService ⇒ 拒启**」**不成立**——
全仓没有任何 CLI/后台脚本会实例化 `ReviewService`。真正的拒启面是
**后端启动之后、命中 `get_review_service()` 的 HTTP 请求**：进程照常起得来。

该请求的后果**不是单一结论**，取决于两件事：

- **该端点的 `except` 接不接 `VaultScopeUnresolved`**（不是「有没有 `try`」——
  `/review/progress/multi` 有 `try` 但只接 `CanvasNotFoundException`）：
  不接 ⇒ 异常逸出到 `CORSExceptionMiddleware` ⇒ **500，且 `CARD-G3-5` 原文
  （含绝对路径）就在响应体 `message` 里**；接了且吞掉 ⇒ **HTTP 200** +
  `reason` 带同样的原文（`/review/fsrs-state` 即如此，按状态码告警的监控看不见）。
- **解析到哪个 vault**：同名冲突分支只查当前桶，换一个 vault 可能直接实例化成功，
  不必先跑迁移脚本。

> ⚠️ **本文档 ③ 节初稿的结论已被推翻并重写**（Codex r1 HIGH-1）：初稿称消息被
> `generic_exception_handler` 屏蔽。实测**生产从未调用 `register_exception_handlers`**
> （`app.exception_handlers` 里没有 `Exception` 键），那个处理器在此路径上是死代码；
> 真正兜底的中间件**不屏蔽**消息。⇒ 设计稿「500 带 CARD-G3-5 消息」在生产栈上
> 其实是**对的**，本卡初稿对它的「一半成立」判定予以撤回。

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
| 用户可见 | 服务不可用 | 视端点与 vault 而定：500 带原文 / 200 带原文 / 换 vault 可能正常（见 ④.4） |

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

## ③ 关键发现（**Codex r1 HIGH-1 整改后重写**）— 生产栈上消息**会**进 500 响应体

> ⚠️ **本节初稿结论是错的，且错得彻底。** 初稿写「CARD-G3-5 被
> `generic_exception_handler` 从 500 响应体屏蔽」，并把它当成生产表征。
> Codex r1 HIGH-1 指出，本卡实测确认并加强：**生产上根本没有那个处理器，
> 且即便有也轮不到它**。真实表征与初稿**相反**。
> 错因是「**能力存在 ≠ 能力接上**」：从 `exception_handlers.py` 读出处理器
> 的行为，就推断成生产 HTTP 表征，漏掉了「这个处理器有没有被生产 app 装上」
> 这一步。原始错误结论保留在下方 3.5 供追溯，不做静默抹除。

### 3.1 `VaultScopeUnresolved` 无专用处理器（这一条初稿正确，保留）

```zsh
grep -n 'VaultScopeUnresolved' backend/app/main.py backend/app/core/exception_handlers.py backend/app/dependencies.py
```
实测：**无输出**（0 命中）。而 `sed -n '359p' backend/app/core/vault_scope.py`
→ `class VaultScopeUnresolved(Exception):`
⇒ 它是裸 `Exception` 子类且无专用 handler，逸出请求处理器后落到某个兜底层。
**关键在于：兜底层是谁。**

### 3.2 ⛔ `register_exception_handlers` 在生产从未被调用

```zsh
git --no-pager grep -n --no-color 'register_exception_handlers' -- '*.py' | grep -v '/tests/'
```
实测输出恰 3 行，**全部在 `exception_handlers.py` 自身**：

```
app/core/exception_handlers.py:275:def register_exception_handlers(app: FastAPI) -> None:
app/core/exception_handlers.py:294:        from app.core.exception_handlers import register_exception_handlers
app/core/exception_handlers.py:297:        register_exception_handlers(app)
```

`:294`/`:297` 是该函数自己 docstring 里的**用法示例**（`Example:` 代码块内），
不是调用点。⇒ **全仓没有任何生产代码调用它。**

**运行时自证**（比 grep 更强——直接问生产 app 实例装了什么）：

```zsh
PYTHONPATH=. .venv/bin/python -c "
from app.main import app
print([getattr(k,'__name__',k) for k in app.exception_handlers.keys()])
print([m.cls.__name__ for m in app.user_middleware])"
```
实测：

```
exception_handlers keys = ['HTTPException', 'RequestValidationError', 'WebSocketRequestValidationError']
user_middleware         = ['MetricsMiddleware', 'CORSMiddleware', 'EncodingValidationMiddleware', 'CORSExceptionMiddleware']
```

**没有 `Exception`，也没有 `CanvasException`。**
⇒ `generic_exception_handler` 与 `canvas_exception_handler` 在生产 app 上
就这条路径而言是**死代码**。（`HTTPException` / `RequestValidationError`
两个键来自 FastAPI 自带的默认注册，不是本仓 `register_exception_handlers` 装的。）

### 3.3 真正兜底的是 `CORSExceptionMiddleware`，它**不屏蔽**消息

`backend/app/main.py`：

- `:634` `class CORSExceptionMiddleware(BaseHTTPMiddleware):`
- `:757` `app.add_middleware(CORSExceptionMiddleware)`

> ⚠️ **`main.py:751` 那条注释（「1. CORSExceptionMiddleware ← 最外层，
> 捕获所有异常」）与代码不符，本文档初稿照抄了它**（Codex r2 LOW-1）。
> 实测 `grep -n 'add_middleware' app/main.py`：`:757` 之后还有
> `:762 EncodingValidationMiddleware`、`:767 CORSMiddleware`、`:779 MetricsMiddleware`。
> starlette 里**后 add 的在更外层** ⇒ 实际从外到内是
> **Metrics → CORS → Encoding → CORSException**。
> ⇒ `CORSExceptionMiddleware` 是**最内层**的 user middleware，
> 它接住的是「路由与更内层抛出的异常」；比它更外层的三个中间件自身抛的异常
> 它接不到。本卡结论只依赖前者（`from_persisted` 在路由内抛），不受影响；
> 但「捕获所有未处理异常」这个说法**过强**，已在本文档各处收窄。
> 那条生产注释本身是否要改，属生产改动，不在本卡范围，登记移交。
- `:694` `except Exception as e:` 接住一切
- `:709-715` 消息提取：
  ```python
  try:
      error_message = str(e)
  except (UnicodeEncodeError, UnicodeDecodeError):
      error_message = repr(e)
  safe_message = error_message.encode("utf-8", errors="replace").decode("utf-8")
  ```
  ⇒ `safe_message` 就是 `str(e)` 的 UTF-8 round-trip，**无任何脱敏**
- `:738-741` 响应体：
  ```python
  content={
      "code": 500,
      "message": safe_message[:500],   # ← 异常原文，截前 500 字符
      "error_type": type(e).__name__,
      "bug_id": bug_id,
  }
  ```

### 3.4 运行时实证（本卡两条用例，栈形态是唯一变量）

新测试 `backend/tests/regression/test_u9c_startup_rejection_eval.py` 的
`TestHttpLayerMasksMessage` 两条用例，异常源同为真
`_VaultScopedCardStates.from_persisted`，差别只在**中间件挂没挂**：

| 用例 | 栈 | 实测响应体 |
|---|---|---|
| `test_handler_only_stack_masks_message_and_does_not_crash` | 只挂 `register_exception_handlers` | `{"code":500,"message":"Internal server error","bug_id":"BUG-…"}`（3 键） |
| `test_production_stack_exposes_message_in_500_body` | 再挂真 `CORSExceptionMiddleware` | `{"code":500,"message":"CARD-G3-5: …请先跑 …migrate_fsrs_card_states_vault_key_g35.py --apply --vault-id <vault> 裁定归属。","error_type":"VaultScopeUnresolved","bug_id":"BUG-…"}`（4 键） |

独立探针（`scratchpad/probe_mw_order.py`，同时挂 handler + 中间件）实测：

```
status = 500
body   = {"code":500,"message":"CARD-G3-5: SENTINEL-MESSAGE-XYZ 指引原文","error_type":"RuntimeError","bug_id":"BUG-4CE6332F"}
SENTINEL in body = True
error_type key   = True (中间件独有字段)
```

⇒ 两者共存时**中间件先接住**，`generic_exception_handler` 不被调用
（响应体带 `error_type`，而 handler 的 body 没有这个键）。

> **⛔ 附带更正：初稿的「排他性断言」是无效的。**
> 初稿称「`code == 500` + 存在 `bug_id` 共同证明这个 500 出自
> `generic_exception_handler`」。实测两层的 body **都有**这两个键，
> 它什么也证明不了。真正的分层指纹是 **`error_type`**：中间件有、handler 没有。
> 两条用例现已各自断言该键的**在**与**不在**，从而各自证明自己测到了哪一层。

### 3.5 结论更正对照（初稿 → 实测）

| 命题 | 初稿判定 | **实测判定** |
|---|---|---|
| 请求返回 500（工厂在端点 `try` 之外时） | ✅ | ✅ 成立 |
| CARD-G3-5 进日志 / bug_log | ✅ | ✅ 成立 |
| CARD-G3-5 进 **HTTP 响应体** | ❌ 不成立（「被屏蔽」） | ⚠️ **成立** —— 中间件把原文（前 500 字符）放进 `message` |
| `generic_exception_handler` 是生产兜底层 | 隐含假定成立 | ❌ **不成立** —— 生产未注册，该处理器在此路径上是死代码 |
| `code+bug_id` 可作产出方指纹 | 称成立 | ❌ **不成立** —— 两层都有；`error_type` 才是 |

⇒ **U9-C 设计稿「请求 500 带 CARD-G3-5 消息」在生产栈上其实是对的**，
本卡初稿对它的「一半成立」判定应予撤回。

> ⚠️ **但「运维能从 HTTP 直接看到完整指引」这句不能说满**（Codex r2 LOW-4，本卡实算证实）：
> `main.py:739` 取的是 `safe_message[:500]`，而同名冲突分支（`:593`）的消息长度
> **随冲突键数量增长**。实算（5 个 36 字符 UUID 键，`scratchpad/probe_truncation.py`）：
>
> ```
> len(msg) = 538
> script name in full msg  = True
> script name in msg[:500] = False        ← 被截断
> tail of msg[:500]        = '…请先跑 backend/scripts/migrate_f'
> '--vault-id' in full msg = False        ← 该分支原文本来就没有这个参数
> ```
>
> 对照 None 分支（`:570`）：`len = 311`，脚本名与 `--vault-id` **都在** 500 字符内。
> ⇒ 准确表述：**`:570` 分支能看到完整指引；`:593` 分支只在冲突键较少时能看到脚本名，
> 且从来不含 `--vault-id`**。泄漏结论（绝对路径进响应体）不受影响，
> 「完整操作指引」这一保证不成立。

⇒ 反过来，**评估文档 ⑤ 的议题 α 需要重新定性**：它不再是「要不要把指引
暴露出来」（已经暴露了），而是「**暴露得太多**」——`str(e)` 未脱敏，消息里
含 `_CARD_STATES_FILE` 的**绝对路径**（实测原文含
`/Users/…/worktrees/card-t4-g3/backend/data/fsrs_card_states.json`），
等于向任何能打到该端点的人泄漏部署布局。详见 ⑤。

---

## ④ 进程不崩；但「持续 500」这一表述**过强**（Codex r1 MEDIUM-1/3 整改）

### 4.1 进程不崩（实测，初稿正确）

本卡两条 HTTP 用例都在 probe 请求之后立刻再请求 `/_alive`，实测均
**200 + `{"alive": true}`**。⇒ 未处理异常被兜底层接住，app 继续服务后续请求。
叠加 ①.1.3（lifespan 不预先实例化），**后端在含 legacy 坏数据时仍然起得来**。

### 4.2 singleton 恒 `None` 这一条成立

`get_review_service()`（只读摘录，存档 `evidence-u9c-eval/factory-readonly-20260916T145559.txt`）：

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
初稿按摘录序号推算，整块偏了 1，已更正；`:2996` 恰好未受影响。）

赋值是工厂最后一步，`ReviewService.__init__` 在 `:850` 就抛
⇒ 该次调用的赋值不发生。

**准确表述（Codex r3 LOW-1 收窄）**：
「singleton 恒 `None` ⇒ 每个 review 请求都会重入」需要两个限定，否则过强：

1. **只限实际调用该工厂的请求**。反例：`/review/verification-history`
   （`review.py:1320` 起）直接用 `get_graphiti_temporal_client()`，
   **根本不经过** `get_review_service()`，不受影响。
2. **只限 singleton 尚未被任何一次调用成功初始化之前**。反例序列：
   数据为 `{"a": {"x": "old"}, "x": "legacy"}`；作用域 `a` 的请求因同名冲突失败，
   而作用域 `b` 的请求（B 桶无同名）**成功**并把全局 singleton 赋了值；
   此后作用域 `a` 的请求会在 `:2953` 的快路径直接返回那个已建好的实例，
   **不再走 `from_persisted`、也就不再触发冲突检查**。

3. **只限本次的数据与作用域仍满足拒绝条件时**。上面第 2 条的反例同时说明了
   这一点：同一份数据下，作用域 `b` 的请求**满足**前两条限定（singleton 仍空、
   确实调了工厂），却**成功**构造——因为 B 桶没有同名冲突。

⇒ 成立的是：**在 singleton 尚未成功初始化、该请求确实调用了这个工厂、
且本次的数据与作用域仍满足拒绝条件时**，该次调用会重走实例化链并再次抛出。

### 4.3 ⛔ 但由它**推不出**「每个请求都 500，直到跑迁移脚本」

初稿这句话三处都不准，实测三条反例：

**(a) 后果取决于端点是否捕获**这个异常类型**——「有没有 `try`」不是判据。**

> ⚠️ 上一轮整改把判据写成「包进 `try` 就是 200」——**仍然过强**
> （Codex r2 MEDIUM-1）。反例：`/review/progress/multi/{path}`
> （`review.py:1225` 起）**也**在 `try` 内调工厂，但它只
> `except CanvasNotFoundException`（`:1230`），`VaultScopeUnresolved`
> 直接穿过 ⇒ 仍是 500。
> ⇒ 正确判据是「该端点的 `except` 子句**接不接这个异常类型**，以及接住后返回什么」。

已实测的三种端点形态：

| 端点 | 工厂调用位置 | `except` | 结果 |
|---|---|---|---|
| `/review/history`（`:693`） | `try` **之外** | — | 逸出 ⇒ 中间件 500 + 原文 |
| `/review/progress/multi`（`:1225`） | `try` 内 | 只 `CanvasNotFoundException` | 穿过 ⇒ 中间件 500 + 原文 |
| `/review/fsrs-state`（`:1458`） | `try` 内 | `except Exception`（`:1507`） | **HTTP 200** + `reason` 带原文 |

第三种的返回体：

```python
return FSRSStateQueryResponse(
    concept_id=concept_id, fsrs_state=None, card_state=None,
    found=False, reason=f"error: {e}", ...
)
```

⇒ **HTTP 200**，且 `reason` 里带异常原文。
> ⚠️ **这比 500 更值得警惕**：CARD-G3-5 原文（含绝对路径）从一个
> **200 响应**里泄出，按状态码告警的监控完全看不见，用户界面上也只表现为
> 「这张卡没有 FSRS 状态」。本卡把它作为**新发现**登记（见 ⑤ 与验收单台账）。

对照：同文件 `:693` 的 `/review/history` 把工厂调用放在 `try` **之外**，
异常逸出 ⇒ 走 3.3 的中间件 ⇒ 500 + 原文。
⇒ **后果取决于端点怎么写，不是一个全局结论。**

**(b) 换一个 vault 就可能成功实例化，无需先跑迁移脚本。**
`review_service.py:589` 的
`clobbered = sorted(cid for cid in legacy if cid in bucket)` 检查的是
**当前作用域那一桶**。若首次以 `vault_a` 失败（legacy 与 A 桶同名），
换 `vault_b` 时 B 桶内无同名 ⇒ `:602 bucket.update(legacy)` 正常执行 ⇒ 实例化成功。
⇒ 「直到运维跑迁移器」不成立；该分支下**换个 vault 即可**。
（注意这不是好事：legacy 会被**推定**归进 B 桶并在下次落盘固化——
正是 `from_persisted` docstring `:541-545` 警告的那个反例。）

**(c) 重入开销：部分复用、部分真重建——两种一刀切说法都不对。**

初稿称「每次重入会重建一遍 memory / canvas / graphiti 依赖」——过强。
但上一轮整改改成「依赖都是 singleton，重入不重建」——**又过头了**
（Codex r2 MEDIUM-2）。逐项实测：

| 工厂内建立的东西 | 行 | 重入时 | 证据类型 |
|---|---|---|---|
| `memory_client`（`await get_memory_service()`） | `memory_service.py:2908` 快路径 | **上次成功后**复用 singleton | 读码 |
| `graphiti_client`（`get_graphiti_temporal_client()`） | `dependencies.py:779` 快路径 | **上次成功后**复用；⚠️ **失败不缓存**（`:798-815` 三个 `except` 全 `return None`）⇒ 下次**完整重试初始化** | 读码 |
| `BackgroundTaskManager` | `:2979` 直接 `BackgroundTaskManager()` | **复用** singleton | **运行时自证** `first is second = True` |
| `CanvasService` | `:2976` 直接 `CanvasService(...)` | **每次新建** | **运行时自证** `is-same = False` |
| `FSRSManager` | `:2982 create_fsrs_manager(settings)` → `:756 FSRSManager(...)` | `USE_FSRS=True` 且包装模块可 import 时**每次新建** | **运行时自证**（本机 `USE_FSRS=True`）`is-same = False` |

> **⛔ 「py-fsrs 装没装」决定不了它返不返 `None`**（Codex r4 MEDIUM-1）。
> 本卡 round-3 曾写「py-fsrs 缺失时工厂返 `None`」——错在把两个**同名不同义**
> 的标志当成了一个：
>
> | 位置 | `FSRS_AVAILABLE` 的含义 |
> |---|---|
> | `lib/memory/temporal/fsrs_manager.py:24` | **底层 `fsrs` 库**可导入 |
> | `app/services/review_service.py:94` | **包装模块** `memory.temporal.fsrs_manager` 可导入 |
>
> `:750` 的 `if not FSRS_AVAILABLE` 读的是**后者**。而底层 `fsrs` 缺失时，
> 包装模块 `:21-29` 捕获 `ImportError`、定义 fallback 类后**仍然导入成功**
> ⇒ `review_service.FSRS_AVAILABLE` 仍为 `True` ⇒ **照样新建** `FSRSManager`，
> 只是该实例的 `library_available`（`:122`）为 `False`。
> 真正让它返 `None` 的是：`USE_FSRS=False`，或**包装模块本身**导入失败。
>
> ⚠️ **本机两个标志实测都是 `True`**（底层 fsrs 已安装），故「底层缺失时仍新建」
> 这一条是**代码路径推演**，不是本机运行时观测；如实标注，不冒充实测。

> ⚠️ **上一轮我把 `BackgroundTaskManager` 判成「每次新建」，那是错的**
> （Codex r3 MEDIUM-1）。它的 `background_task_manager.py:91 __new__` 返回缓存的
> `cls._instance`，`:99-101` 再防重复 `__init__`。本轮已运行时自证
> （`BackgroundTaskManager() is BackgroundTaskManager()` → `True`）。
>
> 这是本卡第二次在「纠正过强表述」时**矫枉过正**：r1 指出「不是全部重建」，
> 我改成「全部复用」（r2 打回）；r2 指出「有些确实新建」，我又把
> `BackgroundTaskManager` 一并算进新建（r3 打回）。教训写在 §6.9。

⇒ 重入的真实开销（在「依赖此前都已成功初始化」这个前提下）=
「三次 singleton 查表命中」+「两个对象真新建（`CanvasService` +
`USE_FSRS=True` 时的 `FSRSManager`）」+「再抛一次」。

两处会让上式失效，都不能省：
- **graphiti 上次没成功** ⇒ 这次不是查表命中，而是**完整重试初始化**；
- **`USE_FSRS=False` 或包装模块导入失败** ⇒ `create_fsrs_manager` 返 `None`，
  新建对象降为 1（**注意不包括**「底层 py-fsrs 缺失」这一情形，见上框）。

> **证据边界（Codex r4 LOW-5 更正）**：上表的「证据类型」列区分了两种情况——
> 标「运行时自证」的三行是**单独对该依赖做过实例化探针**（`is`/`is-same` 实测）；
> 标「读码」的两行只有源码依据。但**无论哪一行，本卡都没有执行过完整的
> `get_review_service()` 工厂**（会连真服务，硬边界禁止），
> 所以「工厂重入时这些对象各自会怎样」仍是**由单点实测 + 控制流拼出来的推演**，
> 不是对工厂重入本身的观测。⑦ 的「工厂中段未执行」声明不变。

### 4.4 更正后的可用性表述

> **三条限定同时成立时**（缺一不可，逐条见 4.2），该次调用才会重走实例化链
> 并再次抛出：① singleton 尚未被任何一次调用成功初始化；② 该请求**确实调用了**
> `get_review_service()`（`/review/verification-history` 就不调）；
> ③ **本次的数据与作用域仍满足拒绝条件**——同一份数据下换一个无冲突的 vault
> 即可成功构造，此时前两条仍成立而结果相反。
>
> **而「用户看到什么」更不是一个全局结论**，还取决于两件事：
>
> 1. **该请求解析到哪个 vault** —— 同名冲突只查当前桶，换一个 vault 就可能
>    直接实例化成功（4.3b），不必先跑迁移脚本；
> 2. **该端点的 `except` 接不接 `VaultScopeUnresolved`** —— 不接（无论有没有
>    `try`）⇒ 逸出到 `CORSExceptionMiddleware` ⇒ **500 + `message` 带原文**；
>    接了且吞掉 ⇒ 如 `/review/fsrs-state` 那样返回 **HTTP 200 + `reason` 带原文**。
>
> ⇒ 「review 面持续 500 直到运维跑迁移脚本」**只在「同一 vault + 端点不接这个
> 异常」这个交集上成立**，不能作为该面的整体描述。

## ⑤ legacy 兼容重做 = 设计级议题（D-38，登记不排本批）

两条出路，**都影响产品行为、都需用户裁**，本卡只登记移交，不动代码：

### 议题 α —— 异常消息的暴露口径（**已因 ③ 更正而反向**）

> ⚠️ **本议题已因 ③ 的更正而反向**。初稿设想的是「要不要把指引**暴露**出来」；
> 实测表明指引**早已暴露**，真正的问题是**暴露得太多、且暴露面不受控**。

**实测到的三个问题**（都不需要「加处理器」才成立，现在就存在）：

1. **未脱敏**：`CORSExceptionMiddleware` 的 `safe_message` 就是 `str(e)`
   （`main.py:709-715`，只做 UTF-8 round-trip），整条异常消息前 500 字符进响应体。
   本卡实测原文含 `_CARD_STATES_FILE` 的**绝对路径**
   （`/Users/…/worktrees/card-t4-g3/backend/data/fsrs_card_states.json`）
   ⇒ 任何能打到该端点的人都能读到部署布局。这不限于本异常，但**也不是「所有
   未处理异常」**——准确范围是「从路由或更内层逸出、**既没被端点自己接住、
   也没有已注册处理器**的异常」。两类不走这条路：
   - **被更内层的 `ExceptionMiddleware` 处理掉的异常类型**：如 `review.py:1315`
     的 `HTTPException(400)`，由它的默认处理器就地处理，根本到不了 CORS 中间件
     的 `except`（Codex r4 LOW-2）。
     > ⚠️ 这里必须说「**内层** `ExceptionMiddleware` 的处理器」，不能笼统说
     > 「有已注册处理器」（Codex r5 LOW-2）：`Exception` / 500 的处理器归
     > **外层** `ServerErrorMiddleware`，它比 CORS 中间件更靠外，注册了也拦不住
     > ——本卡第二条 HTTP 用例正是「`Exception` 处理器已注册 + 挂中间件」，
     > 结果仍由中间件返回原文。两者不是一回事。
   - **比它更外层的 Metrics / CORS / Encoding 三个中间件自身抛的异常**
     （见 ③.3.3 的拓扑更正）。
2. **意图与实现相反**：`generic_exception_handler` 的 `:210` docstring 明写
   `IMPORTANT: In production, this should NOT expose internal error details.`，
   `:261` 行内注释再复述一次。这份「不暴露」的设计意图**从未生效**，
   因为该处理器生产未注册（3.2）。
   > ⛔ **注意：「让生产真的注册它」并不是一个可行的收口办法**
   > （Codex r2 MEDIUM-3 / r3 MEDIUM-2）。本卡
   > `test_production_stack_exposes_message_in_500_body` 的配置**正是**
   > 「先 `register_exception_handlers`，再挂真中间件」，结果仍返回原文——
   > 因为中间件在更内层先接住，压根轮不到那个 handler。
   > ⇒ 需要裁定的是：这份意图是**要落地**（那就得改**中间件**的脱敏口径，
   > 不是补注册），还是**已作废**（认可透出行为，把那两处注释改掉以免误导后人）。
3. **200 泄漏面**：`/review/fsrs-state` 这类端点接住了异常并把原文放进
   **HTTP 200** 的 `reason` 字段（4.3a）。即便给 500 加了脱敏，
   这条路径也不会被覆盖——它压根不经过异常处理层。

**若要收口，至少三处要一起裁**（只改一处等于没改）：
① `CORSExceptionMiddleware` 的 `safe_message` 脱敏口径（**主战场**）；
② 那两处「不暴露内部细节」的注释是落地还是作废；
③ 端点 `except` 分支往响应里塞 `str(e)` 的做法。

**连带**：一旦改动，本卡 `TestHttpLayerMasksMessage` 的**两条**用例断言方向
都要重新裁定——它们钉的是**当前口径**，不是永久不变量。

### 议题 β — legacy 兼容整体重做

隔离区 / 保留键命名空间 / 多份候选 / 毒条目预检那一整套。

- **历史**：CARD-G3-5 卡内 Codex r2→r5 在这套设计上**每一轮修复都长出新缺陷**，
  用户 2026-09-09 裁定 ③「缩小本卡」，只保留键化核心（vault 分桶 + fail-closed + 迁移器），
  legacy 兼容整体移交。该裁定的原文就写在 `from_persisted` 的 docstring 里（**`:530-534`**）。
- **现状**：当前口径是「凡是归不掉的 legacy 一律 fail-fast」——**最简且可证**，
  代价是可用性（④.4：在「同一 vault + 端点不接该异常」的交集上持续 500；
  其余形态是 200 带原文，或换 vault 后正常）。
- **D-38 裁定**：作为**设计级**议题登记，**不排第十四批**。

### 移交建议

α 与 β **可以分开裁**，但 α **不是**「加一个 handler」那么小：

> ⚠️ Codex r2 MEDIUM-3 指出、本卡新测试**自己就是反例**：
> `test_production_stack_exposes_message_in_500_body` 的配置正是
> 「先 `register_exception_handlers`，再挂真中间件」，结果**仍返回原文**。
> ⇒ **只把现有 `generic_exception_handler` 接上，不会改变这条路由异常的响应**
> （中间件在更内层先接住），也管不到 `/review/fsrs-state` 已吞异常后的 200。

α 的真实工作量 = 至少三处一起裁（见上），而且要先确定「不暴露内部细节」
这份设计意图是**要落地**还是**已作废**；注意 200 泄漏面来自
「端点 `except` 接住了这个异常并把 `str(e)` 塞进响应」，
不是「端点有没有 `try`」（④.3a）。建议：
- 先裁**意图**（一句话决策：异常原文该不该进 HTTP 响应），再谈实现；
- β 大改数据处置语义，单独立卡走完整设计流程；
- 两者都不在第十四批（D-38）。

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

**⛔ 这个别名有两份，堵一份不够**（本卡实测踩到）：

| 命名空间 | 谁在用 | 谁负责重定向 |
|---|---|---|
| `app.main.bug_tracker`（`main.py:57` import、`:721` 使用） | `CORSExceptionMiddleware` | `tests/conftest.py:121-129` 的 session fixture |
| `app.core.exception_handlers.bug_tracker`（`:27` import、`:243` 使用） | `generic_exception_handler` | **没人**——本卡测试自己照同一形状补了一次 |

两份都指向同一个模块级单例，但**替换是按命名空间生效的**：换掉一份，
另一份仍指向真单例。conftest 明确声明它只换 `app.main` 那份、
**不碰单例本身**（单例默认路径契约另有测试在锁）。

**隔离自证（本卡实测，含一次真实翻车）**：

- **pytest 路径零写** —— 已用跑前/跑后 `sha256` + `mtime` 逐字节比对证明，
  并带验伪锚（故意追加一行，`sha` 确实变）。见 ⑦.7.4 与存档
  `evidence-u9c-eval/zero-write-proof-20260916T190821.txt`。
- **pytest 之外的探针真写了** —— 本卡 scratchpad 探针只重定向了
  `exception_handlers` 那份，而它挂的是 `CORSExceptionMiddleware`（用 `app.main` 那份），
  于是真写了 `backend/data/bug_log.jsonl` 一条。详情与处置见 ⑦.7.4。

> 初稿此处写「跑完全部测试后 `ls` → No such file or directory ⇒ 零写车道树」。
> 那个观测当时为真，但**它证明的比它声称的少**：它只说明那一刻文件不存在，
> 并没有区分「pytest 没写」与「还没有人写过」。后来探针一跑，文件就出现了。
> 正确的零写判据是 ⑦.7.4 那种**跑前/跑后对照 + 验伪锚**，不是单次存在性检查。

换的是**落盘路径**不是**行为**：`log_error` 仍真跑完整记账链
（③ 的 `bug_logged` 日志即其产物），没有 mock 掉任何被测层。

### 6.3 ⛔「能力存在」不等于「能力接上」（本卡最贵的一条）

本卡初稿 ③ 整节结论是错的，错法值得单独记：

- 我读了 `exception_handlers.py`，确认 `generic_exception_handler` 的行为是
  「不暴露内部细节」——**这一步没错**；
- 然后我把它当成了「生产 HTTP 表征」——**这一步跳过了一个必须问的问题：
  这个处理器被生产 app 装上了吗？**
- 实测答案是**没有**：`app.main.app.exception_handlers` 里压根没有 `Exception` 键。

⇒ **测一个 helper / handler 的行为，不等于测它在系统里的接线。**
判据要锚在「运行时的 app 实例上装了什么」，而不是「源码里定义了什么」。
本卡的运行时自证（打印 `app.exception_handlers.keys()` 与 `user_middleware`）
只要一行，却是唯一能戳破这个错误的东西——grep 再多遍源码也戳不破。

同族：`docs/known-gotchas.md` 的 G-FAKE（名字像 A 身体是 B）与
G-PIPE（已实现但无调用方）。本条是 **G-PIPE 的变体**：
实现了、注册函数也写好了，但**没人调那个注册函数**。

### 6.4 ⛔ 排他性判据必须先验证它真的排他

初稿用「`code == 500` 且存在 `bug_id`」断言「这个 500 出自
`generic_exception_handler`」。实测两个可能的产出方：

```
generic_exception_handler : {code, message, bug_id}            ← 3 键
CORSExceptionMiddleware   : {code, message, error_type, bug_id} ← 4 键
```

两者**都**满足初稿的「排他」条件 ⇒ 该判据排他性为零。
一个不排他的排他判据比没有判据更危险：它让人以为已经确认了产出方。

**修法**：找**只有一方产出**的字段（这里是 `error_type`），
让每条用例都断言它的**在**或**不在**，从而各自证明自己测到了哪一层。

### 6.5 ⛔ `rc=` 只能当场取，隔一条命令就不是它了

本卡 (h) 的 unit 存档末行写了 `rc=0`，而同一文件里是 `35 failed … 29 errors`
——自相矛盾（Codex r1 LOW-2 抓到）。根因是我写成了：

```zsh
... | tee "../$UNIT" | tail -6; echo "rc=$pipestatus[1]"   # ← 这句对，屏幕上输出 rc=1
echo "rc=$pipestatus[1]" >> "../$UNIT"                      # ← 这句的 $pipestatus 已经是
                                                            #    **上一条 echo** 的，恒 0
```

第二条 `echo` 重新计算了 `$pipestatus`，取到的是前一条 `echo` 的管道状态。
**正确写法**：当场存进变量再复用——

```zsh
... | tee "../$UNIT"; RC=$pipestatus[1]
echo "rc=$RC" | tee -a "../$UNIT"
```

本卡整改后的 `pytest-u9c-r2-*.txt` 用的就是这个写法。
**历史存档 `unit-20260916T144844.txt` 里那行错误的 `rc=0` 保持原样不改**——
存档记录的是当时实际发生的事，事后改它等于伪造；更正写在这里。
该存档的真实结论以其正文 `35 failed, 5077 passed, …, 29 errors` 为准，
而「本卡是否引入新红」由 `unit-new-red.txt`（空）判定，与那行 `rc` 无关。

> 同族已登记教训：`reference_pipeline_eats_rc_three_times`。本卡是第四次。

### 6.9 ⛔ 纠正过强表述时，最容易犯的是**反向过强**

本卡同一个论点（工厂重入的依赖开销）被连打**三轮**，每一轮都是我在修上一轮
的过强表述时，朝反方向又说过了头：

| 轮次 | 我写的 | 被指出 |
|---|---|---|
| 初稿 | 「每次重入**重建**一遍 memory / canvas / graphiti 依赖」 | r1 M3：memory、graphiti 是 singleton |
| r1 整改 | 「依赖**都是** singleton，重入**不重建**」 | r2 M2：`CanvasService` / `FSRSManager` 确实每次新建 |
| r2 整改 | 逐项表，但把 `BackgroundTaskManager` 判成「每次新建」 | r3 M1：它 `__new__` 返缓存 `_instance`，实测 `is same = True` |

**根因不是粗心，是每轮都在用「整体判断」回应「反例」。**
对方给的是「A 不成立」，我回的是「那就是 ¬A」——而真相是「逐项各不相同」。

**做法**：论点涉及 N 个对象时，**逐个列**并**逐个给运行时自证**，
不要写任何形如「都是 / 都不是 / 全部 / 一律」的概括。本轮的表格给每一行
配了 `is-same` 实测列，就是为了让「某一项判错」在下一轮可以被单点纠正，
而不是整句话推倒重来。

> 同族：`reference_backlog_entry_is_not_conclusion_update`、
> `reference_coverage_reattribution_must_list_gaps`——都是「结论层面的
> 概括掩盖了逐项事实」。

### 6.7 ⛔ 一条**不采纳**的审查意见（如实记录，附实测依据）

Codex r2 LOW-2 末句称：「另一个小行号偏差：冲突条件实际在 `:590`，
不是说明中的 `:589`。」——**本卡不采纳这一条**，实测如下：

```zsh
grep -n 'clobbered = sorted' backend/app/services/review_service.py
# → 589:        clobbered = sorted(cid for cid in legacy if cid in bucket)
```

`:589` 是**冲突集合的计算行**（本文档与测试 docstring 引用的就是它），
`:590` 是紧随其后的 `if clobbered:` 判定行。两者都对，取决于指的是哪一行；
本卡引用的是计算行，没有写错。

> 记这一条不是为了争对错，而是留下一个**审查意见也需要复核**的样本：
> 本卡对 r1/r2 的其余全部 finding 都逐条实测后采纳（并有两条在实测中被加强），
> 唯独这一条经 `grep -n` 实测判定不成立。**照单全收和一概不收都不是复核。**

### 6.8 行号偏移汇总（勘探 → 本树实测）

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

### 7.1 三层里真跑了两层

| 层 | 覆盖方式 | 本卡是否执行 |
|---|---|---|
| 实例化层（`from_persisted` 两抛出点 `:570`/`:593`） | 真函数真抛，断言消息 | ✅ 真跑 |
| HTTP 层（两个栈形态：仅 handler / 加真中间件） | 真 handler + 真中间件 + 最小 app | ✅ 真跑 |
| 工厂中段（`get_review_service` 建重依赖 → `:2996`） | 只读证据 + 控制流推演（④.2） | ❌ **未执行**（会连 7691/LanceDB，硬边界禁连） |

### 7.2 本卡替换了哪些真实现（全列，不留「唯一」这种未经清点的措辞）

初稿写「唯一被替换的是 `bug_tracker` 落盘路径」——**不准确**（Codex r1 C 项）。
实际替换三处，逐条列明：

| 被替换对象 | 替换内容 | 为什么不构成「mock 掉被测层」 |
|---|---|---|
| `subject_config.get_current_subject_id` | 恒返回 `DEFAULT_SUBJECT_ID` | 用于**制造**「作用域解析失败」这个被测前置条件；被测逻辑（`from_persisted` 的分支判定）本身未被替换 |
| `subject_config.default_vault_group_id` | 抛 `RuntimeError` | 同上；两者均在 `finally` 显式还原 |
| `exception_handlers.bug_tracker` | 换 `log_path` 指向 pytest 临时目录 | 只换**落盘位置**，`log_error` 行为一行未改；与 `tests/conftest.py:121-129` 对 `app.main` 的做法同型 |

被测链上的 `from_persisted`、`generic_exception_handler`、`CORSExceptionMiddleware`
全是真实现。

### 7.3 本卡明确**未**证明的事

1. **真工厂路径的端到端行为**——`get_review_service()` 建立 memory / canvas /
   graphiti 依赖后到 `:2996` 的那一段未执行（硬边界禁连真服务）；④ 对它的论述
   是只读代码证据 + 控制流推演，不是运行时实测。
2. **现网 `fsrs_card_states.json` 是否真的含 legacy 裸键**——本卡未连 live、
   未读现网文件。全部输入都是测试内构造的字典。
3. **迁移脚本 `migrate_fsrs_card_states_vault_key_g35.py --apply` 能否真正解开
   拒启**——本卡只断言异常消息里**提到**了它，没有执行过它。
4. **日志 / bug_log 的落盘侧**——本卡断言的是「异常对象自身含消息」与
   「响应体含/不含消息」。③ 引用的结构化日志是 pytest 捕获输出，可佐证
   消息进了日志通道，但**不是本卡的断言对象**，也未断言 `bug_log.jsonl`
   文件内容。
5. **LanceDB 隔离**——W4 哨兵只覆盖 Neo4j 端口；本卡没有针对 LanceDB 的
   零连接判据。依据是「测试代码里没有任何 LanceDB 调用路径」这一读码结论，
   不是运行时观测。
6. **「整个车道树零写入」**——7.4 的实验只证明了 `backend/data/bug_log.jsonl`
   这一个文件在 pytest 前后逐字节未变，不等于全树零写。
7. **多 vault 同进程下真相源串库**（`_VaultScopedCardStates` docstring 自己
   登记的前提缺口）是否影响本拒启面——未探。

### 7.4 一处自造污染（如实登记，未清理）

`backend/data/bug_log.jsonl` 现存 **1 条**记录，来自本卡的 scratchpad 探针
`probe_mw_order.py`（19:04）——该探针在 **pytest 之外**运行，因此
`tests/conftest.py` 对 `app.main.bug_tracker` 的重定向不在场，
而探针只重定向了 `exception_handlers.bug_tracker`（中间件用的是前者）。

> **教训**：在 pytest 之外跑探针 = 主动放弃了**全部** conftest 防线
> （W4 端口守卫、`bug_tracker` 重定向、bark 外发守卫都不在）。
> 同一能力在两个命名空间各有一份别名时，只堵一份等于没堵。

**pytest 路径本身零写**，已用实验证明（存档 `evidence-u9c-eval/zero-write-proof-20260916T190821.txt`）：
跑前 / 跑后 `sha256` 逐字节相同、`mtime` 未变（仍是探针那次），
并带验伪锚（故意追加一行，`sha` 确实改变 ⇒ 判据能测出写入）。

该文件被 `backend/data/.gitignore:5` 的 `*.jsonl` 覆盖，**不入库、不影响地盘核**。
删除动作受用户级只读守卫约束，本卡**不自行清理**，登记交主 session 处置。

---

## ⑧ 可复核索引

| 内容 | 存档 |
|---|---|
| ① 抛出点 grep | `evidence-u9c-eval/grep-raise-20260916T144314.txt` |
| ① scripts 零实例化方 | `evidence-u9c-eval/grep-scripts-20260916T144314.txt`（0 字节 = 0 命中） |
| ① 生产唯一实例化点 | `evidence-u9c-eval/grep-prod-ctor-20260916T144314.txt` |
| ① lifespan grep | `evidence-u9c-eval/grep-main-20260916T144314.txt` |
| ③ 初稿「先红」验伪锚（历史，结论已被推翻） | `evidence-u9c-eval/u9c-antigate-20260916T144639.txt` |
| ③ 初稿 4 passed（历史） | `evidence-u9c-eval/pytest-u9c-20260916T144743.txt` |
| ③④ r1 整改后 5 passed（历史，早于 r3/r4 整改） | `evidence-u9c-eval/pytest-u9c-r2-20260916T190729.txt` |
| ③④ **最终 5 passed（绑最终代码态；`rc=` 当场取，见 §6.5）** | `evidence-u9c-eval/pytest-u9c-final-20260916T194319.txt` |
| ④ 工厂链只读摘录 | `evidence-u9c-eval/factory-readonly-20260916T145559.txt` |
| 7.4 pytest 零写实验 | `evidence-u9c-eval/zero-write-proof-20260916T190821.txt` |
| (h) tests/unit 目录级 | `evidence-u9c-eval/unit-20260916T144844.txt` + `unit-{base,now}.nodeids` + `unit-new-red.txt`（空） |
| (g) 地盘核 | `evidence-u9c-eval/territory-20260916T145925.txt` |

本卡新增测试文件：`backend/tests/regression/test_u9c_startup_rejection_eval.py`
（**5 条**用例：实例化层 3 条 + HTTP 层 2 条）。
