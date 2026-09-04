终裁：**FAIL**。共发现 **0 BLOCKER / 2 HIGH / 3 MEDIUM / 5 LOW**。

审查锚定提交 `78c9e6e7d0156b9dc7127e49743a07310031525a`。审查期间 HEAD 从 `ec62828e` 被外部施工前移，随后 `rag.py` 等又出现并发脏改；下列行号均指 `78c9e6e7` 固定 blob。动态四文件回归为 `110 passed`，但只作运行态佐证，不冒充纯净提交或全量 CI。本审查未写仓库。

1. [HIGH] `stacklevel` 在守护区外，直接击穿唯一 no-throw 承诺

证据：`backend/app/core/nothrow_logging.py:17-18,99-109`；`:106` 的

```python
kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + _STACKLEVEL_OFFSET
```

发生在 `try` 之前。

反例：`NoThrowLogger(logger).info("x", stacklevel=None)` → `TypeError` 直接传播，fallback 调用数为 0。若该错误出现在 `/weak-concepts` 入口，则请求仍会变成 500、service 不执行。`:139` 的 `log()` 参数绑定错误同样可能在进入 `_guarded` 前抛出。

施工方关于 stdlib 的辩解也只局部成立。本机 CPython 3.14：

- `logging/__init__.py:1011-1028` 的 `Handler.handle()` 没有 catch；
- `:1721-1738` 的 `Logger.callHandlers()` 也没有 catch；
- 只有 `StreamHandler.emit():1150-1159` 主动调用 `handleError()`，且 `:1156-1157` 明确重抛 `RecursionError`。

实测自定义 Handler、filter、`extra` 键冲突及 `RecursionError`：裸 Logger 会抛，NoThrowLogger 会新增吞掉。反过来，`:109` 只捕获 `Exception`，`KeyboardInterrupt/SystemExit` 仍传播。因此 `:20-24,35-41` 对吞错范围的声明与实际不一致。

建议：把 stacklevel 归一化移入 `try`；处理或明确排除方法参数绑定错误；文档区分常见 StreamHandler 自吞、包装器新增吞错以及不捕获的 `BaseException`。

2. [MEDIUM] 19 处“消息逐字相同”存在真实格式化反例

AST 复算确认旧版 rag 9 处、memory 10 处 f-string，新版均为 0；占位符数量和参数数量均正确。普通生产值下未发现差异：

- rag：`:296-301,455,576-580,589`
- memory：`:142,752-757`
- 三处跨行：父版本 rag `:292,571`、memory `:748`

13 个异常插值点存在反例：

- rag：`:418,422,477,533,598`
- memory：`:146,272,351,464,501,565,768,911`

输入：

```python
class E(RuntimeError):
    def __str__(self): return "STR-VIEW"
    def __format__(self, spec): return "FORMAT-VIEW"
```

旧 `f"{e}"` → `FORMAT-VIEW`；新 `LogRecord.getMessage()` 的 `%s` → `STR-VIEW`。因此无限定的“逐字相同”不成立，虽然当前内建异常及未覆写 `__format__` 的 RAG 异常结果相同。

未发现数值精度或丢参：新改写没有原始格式说明符；`memory.py:879-885` 原有两个 `%d` 未改，5 个占位符对应 5 个参数。

建议：将声明收窄到当前生产类型并增加 19 项渲染表测试；若要求任意对象严格等价，需使用惰性适配对象调用 `format(value, "")`。

3. [LOW] 二级 patch 真实，但诊断内容门可拼接假绿

`nothrow_logging.py:111` 在每次异常时读取模块全局 `_FALLBACK_LOGGER`，所以 `patch.object(nothrow_logging, "_FALLBACK_LOGGER", ...)` 确实命中。相关测试 `test_nothrow_logging_api.py:386,404` 都使用模块属性 patch；没有测试仅靠类级 warning patch 冒充二级路径。

问题在 `:408-415`：它先 join 所有 fallback 调用，再分别搜索 logger、method、cause。

反例：实现分别发三条残缺 warning——一条只有 logger、一条只有 method、一条只有 cause——现有断言全过，但没有任何一条日志包含完整诊断上下文。

建议：要求至少一条 rendered line 同时包含三项，并锁定异常类型或 `repr`。

4. [MEDIUM] `_ours` 只认模板前缀，错误参数导致日志无法渲染时仍假绿

证据：`test_nothrow_logging_api.py:205-215` 只检查 `call.args[0]`；而 `_kill():189-202` 在 `Logger._log` 和 LogRecord 创建前就抛错。

源码共 4 个 `_ours` 调用点，参数化后为 7 次断言、6 个唯一 needle：

- `:238` → rag `:455`
- `:253` → rag `:477`
- `:292` 两例 → rag `:418,422`
- `:364` 三例 → memory `:272,351,464`

反例：

```python
logger.error("RAG service unavailable: %s", e, object())
```

输入上述错参后，HTTP 状态、detail、spy 和 `_ours` 都可继续通过；但正常 `record.getMessage()` 抛 `TypeError`，目标日志无法产生。`:430-439` 的正常渲染门只覆盖 weak-concepts info，没有覆盖五个 error 模板。

建议：断言完整模板、参数数量和值，并对截获参数实际执行 `getMessage()`；更强做法是用捕获 LogRecord 后再抛错的 Handler。

5. [LOW] 普通 Logger 的 `info/log/exception` 帧数未找到反例，但测试覆盖不足

`_STACKLEVEL_OFFSET=2` 对当前 plain `logging.Logger` 正确。CPython `findCaller():1592-1614` 会跳过 logging.py 内部帧，因此 `exception()` 多经 `Logger.error():1551-1555` 不额外消耗 stacklevel。实测三条路径均指向真实调用函数，`exception()` 也保留 `exc_info`。

现有门 `test_nothrow_logging_api.py:441-460` 只锁 info。合法 Logger 子类若在仓外覆写 `info()` 再调用 `super()`，会增加非 logging 内部帧，固定 `+2` 可把来源漂到 `nothrow_logging.py:125`。

建议：参数化测试 info/log/exception，并将透明承诺明确限制为 plain Logger，或为子类设计动态补偿。

6. [MEDIUM] patch 目标下移正确，但提交对象无法独立重放全部 passed 证据

`test_rag_four_state_api.py:197-217` 仍请求 `/rag/query`，patch `logger.inner.info`，断言 200 和 `query.await_count==1`；文件运行结果为 `30 passed`，提交 diff 没有增删测试。因此同一回归仍被锁住。

保留 call-site `try/except` 确实是不改测试的替代方案，但施工方已在验收单 `:128` 明确考虑，故“没考虑替代方案”不成立；目标下移只是选择收敛 call-site 保护后的直接后果。

证据缺口：四文件动态运行是 `13 + 30 + 49 + 18 = 110 passed`，但 `git ls-tree 78c9e6e7` 证明 `test_rag_vault_scope_api.py` 不在提交内、仍是 untracked。输入“纯净 checkout 78c9e6e7 → 执行验收单四文件命令”会在收集前得到 file-not-found，无法重放“后三文件不减”。

建议：先提交明确的 G4-4 前置测试对象，或把本卡可重放的测试集合与工作树联合回归分开登记。

7. [LOW] M3 配料准确、三门确实先红，但原因验证没有逐门绑定

`nothrow_logging_negative_control.py:62-75` 的 `_M3_OLD` 与 `_guarded` 实体一致，`count==1`（579 字符、629 UTF-8 bytes）。

因只读约束未运行会原地改源码的正式脚本；采用等价内存透明转发验证：

- 基线：3 passed
- M3：正常收集，无 fixture/collection error，恰好 3 failed
- 结果依次为 200→500、503→500、memory JSON detail→text/plain 500

因此当前实现下三道指定门确实最先红。

弱点在 `:229-232`：失败原因只对整份输出执行一次 `any(keyword in out)`。若第一门含 500，另外两门因别的测试体断言失败，脚本仍会宣称“三门原因匹配”。

建议：按 nodeid 分割 longrepr，逐门匹配各自原因。

8. [LOW] inventory 自检能防恒 False，但仍有未声明漏判及假包装

`nothrow_logging_inventory.py:244-278` 的 4 条合成自检和 rollback/health 锚均有效。`:33-35,494-497` 也确实声明了函数局部 logger、`.inner`、handler/装饰器三类盲区；提示中的三类没有漏写。

仍未声明的形态：

```python
logging.error("boom")
```

`_calls():193-217` 不识别 root-module convenience 调用，合成结果为 `bindings=[] calls=[]`。

另有假阳性：`_alias_table():66-74` 无条件把名字 `nothrow` 当合法包装器；本地定义 `def nothrow(x): return x` 后，裸 Logger 会被报告成 `wrapped=True`。当前 endpoints 未发现这两种形态，所以不是现存绕过点，但证明锚不足以支持一般化结论。

建议：验证 import 来源必须是 `app.core.nothrow_logging`，识别 `logging.<level>()`，并加入这两类正负自检。

9. [HIGH] 验收单仍是空模板，却把全部完成条件标成 ✅

证据：

- 验收单 `:18-25` 把 `(a)-(f)` 全标完成；
- `:22` 仍写“N 条”；
- `:35,44,53,62,71,78,87` 全是“落地后填”；
- `:110,114` 仍要求以后拷入改写表和 inventory；
- `:132` 仍是“送审后填写”。

全称断言方面：没有发现“所有绕过点均闭合”这种措辞，`:8` 还明确说不防“一切”；但仍有“每一次日志调用”、`:20`“七方法全 try/except”、`:120`“19处逐字不变”等全称，前两项已被本审查反例推翻。

其余子项：

- “本卡不防什么”完整覆盖 Handler、实参求值、`.inner`、未包装模块、exception traceback、SIGKILL、health memory_logger 第三链，见 `:96-106`。
- “待你裁决”在 `:10,122-128` 明确标注建议默认、非用户已批，未伪造裁定。
- 并非每道门都有“证明/不证明”：裁判5两者皆缺，裁判6缺“不证明”，裁判7两者皆缺。
- `:99` 声称其它模块 f-string 为 173 处；当前同一 inventory AST 实跑为 163 处。

错误结果：审查者读取 ✅ 会把“未执行、未留证、实际失败”三种状态都误判为已验收。

建议：在证据补齐前改成 `UNVERIFIED/NOT RUN`；记录固定 SHA、命令、退出码和逐字摘要，补齐 §§六/七及每道门的证明边界。

10. [LOW] 禁改面、HTTP 与 OpenAPI 未找到实现反例；原验收单没有落下声称的证据

用户指定的禁改命令从 merge-base `9af18b27` 到 `78c9e6e7` 输出为空。本卡 commit 单独检查也为空。

对 `HEAD^/HEAD` 固定 blobs 复算：

- rag 的 route/model surface 相同，5 个 `HTTPException` 调用逐字相同；
- memory 相同，8 个 `HTTPException` 调用逐字相同；
- 两个受影响 router 的归一化动态 OpenAPI 均为 44,023 bytes，SHA-256 均为 `f62f4ee196a7dc69fd2a651fe3d1655242bb5f39fa5d6e40025574a1f1bc319e`。

未找到状态码、detail 或 schema 漂移反例。限制：这是受影响 router 的动态 schema，不是完整 `app.main`/middleware/lifespan 快照；验收单 `:79` 只写了计划，实际输出仍空。

建议：把上述固定提交 OpenAPI 比对结果正式落入验收证据，并另行运行全应用快照门。

验证限制：未跑全量 CI、真实 Neo4j 或 live vault；Graphiti MCP 在本环境未暴露。它们不影响上述本地日志包装反例，但不能据此宣称全项目回归通过。

BLOCKER/HIGH 清零：否


