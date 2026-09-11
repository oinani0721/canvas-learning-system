> 批次: BATCH-2026-09-07-第十三批 · 车道 U7（`card-u7-w4guard`） · 卡 CARD-W4-7 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-7.md)"`
> 审查绑定: `d172e7e4`（跑时 HEAD `d172e7e4` —— 同审 SHA）
> 会话头自证（抄 `codex-review-CARD-W4-7.stderr` 会话头含 model 行的三行，stderr 本身不入库；该文件**字面前三行**为 `Reading additional input from stdin...` / 版本行 / `--------`，不含 model 行，故按规则「含 model 行」抄取三要素并标注实际行号）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

**BLOCKER 0 / HIGH 2。**

审查对象：`de6ea625 → d172e7e4652dbc4e1f06f4eeedb36e5937df714b`。三份被审源码与 HEAD 一致。全程未修改文件，未运行测试、探针或负控，未连接本地端口；Python／pytest 机制另核对了官方源码。以下按重要性排序，保留原问题编号。

1. **HIGH｜问题 1：扩捕没有造成判定放宽，但 H-1a 仍有同型记账遗漏。**

   依据：[live_port_guard.py:553](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:553)、同文件 `599–607、754–775`。

   **“所有 None 都会判不可信”不成立。** 当前路径分别是：

   | `extract_port` 返回 None 的原因 | 后继处理 |
   |---|---|
   | 非 tuple，`:553–554` | `port_is_trustworthy` 返回 True，排除在射程外 |
   | tuple 长度不足，`:556–557` | 返回 True，同样排除在射程外 |
   | 底层槽位读取失败，`:559–560` | 对应读取失败时返回 False |
   | 端口对象转换抛 `Exception`，`:562–572` | 原始槽位不是精确 int，`:607` 返回 False，进入受拦分支 |

   前两项是既有语义；此次扩大捕获的第四项没有放宽。进入受拦分支后，精确哨兵地址仍会在 `:762–763` 跳过记账，这是另外一项明确豁免。

   **遗留问题是 `BaseException`。** `__index__` 抛 `SystemExit(0)`、`KeyboardInterrupt` 或自定义 `BaseException` 时，`:563` 仍不捕获；异常从 `:756` 逸出，可信度判断与 `:775` 的记账都不会发生。新测试仅覆盖 `ValueError/RuntimeError`（测试文件 `:72、112`）。

   静态反例是：端口对象第一次转换返回 7691，审计回调再次转换时抛 `SystemExit(0)`，调用者捕获后继续。CPython 的实际顺序确为地址转换 → audit → 发起连接，因此该反例没有要求连接先发生。[CPython socket 实现](https://github.com/python/cpython/blob/v3.14.4/Modules/socketmodule.c#L3467-L3485)、[异常继承关系](https://docs.python.org/3.14/library/exceptions.html#exception-hierarchy)。

   `h1a-red-20260909T101441.txt:7–11` 与 green 文件 `:1–6` 支持本卡指定异常的红绿翻转；**上述 BaseException 路径及最终退出码未实测**。所列日志也没有 `toctou-index-port` 的逐项结果，不能据此独立确认它未翻。

   **建议：**保留此次扩捕；在 hook 中先判原始端口可信度，对不可信对象直接进入记账阻断，避免再次执行其 `__index__`；或在账务边界确保异常传播前已记账。这是同型遗留，非此次扩捕造成的新回归。

2. **HIGH｜问题 2：M-4 新增了真实审计事件可到达的名称漏拦；完整加载封闭性未证明。**

   依据：[live_port_guard.py:708](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:708)、同文件 `:798`。

   `type(name) is not str → False` 把“不信任比较方法”变成了直接放行。即使是**没有任何重载**的 `str` 子类，值为 `"uvloop"`，也会返回 False；旧的顶层相等判断对此会返回 True。

   这不只是人工 `sys.audit` 才能构造的参数：CPython 接受 Unicode 子类，绝对导入保留原 name 对象，审计事件也原样传递；动态扩展加载同样不保证把名称转换为精确 str。[导入参数保留及审计](https://github.com/python/cpython/blob/v3.14.4/Python/import.c#L3495-L3587)、[扩展加载名称处理](https://github.com/python/cpython/blob/v3.14.4/Python/importdl.c#L103-L120)。

   **HIGH 指的是这个确定的事件级判定回退；不能据此声称整个 uvloop 已成功初始化。后续普通字符串子模块事件是否兜住，未验证。**

   其余路径的只读判断如下：

   | 路径 | 判断 |
   |---|---|
   | 未缓存的 `__import__("uvloop")` | 发出目标名称事件，当前会拦；缓存命中不能笼统保证再次发事件 |
   | `importlib.import_module("uvloop")` | 不在其入口为该纯 Python 顶层包补事件；既存修后输出证明后续被本门拒绝 |
   | `importlib.import_module("uvloop.loop")` | 父包缺失时先加载父包；标准动态扩展加载本身也能发 `uvloop.loop` 事件，精确字符串会被拦。此直接调用未实测 |
   | `spec_from_file_location` 加源码 `exec_module` | 创建 spec 不等于加载；直接执行源码不保证补顶层 import 事件，源码内部 import 仍可能被拦 |
   | 按 `"uvloop.loop"` 名加载 `.so` | 标准动态扩展加载发 import 事件，会命中当前判据 |
   | 用其他名称按路径加载 | hook 不核对 filename，别名事件不命中；本机 uvloop 后续初始化能否完成，**未验证** |
   | `zipimport` | 普通 import 前门仍受审计；直接 loader 执行需另看。ZIP 不能直接加载 `.so/.pyd`，不能据此断言完整 uvloop 可绕过 |
   | `imp` | 标准库入口已在 Python 3.12 删除；旧版本的不同 loader 未验证 |

   依据：[父包递归与导入实现](https://github.com/python/cpython/blob/v3.14.4/Lib/importlib/_bootstrap.py#L1208-L1301)、[源码／扩展 loader](https://github.com/python/cpython/blob/v3.14.4/Lib/importlib/_bootstrap_external.py)、[动态扩展审计](https://github.com/python/cpython/blob/v3.14.4/Python/import.c#L4447-L4487)、[ZIP 限制](https://docs.python.org/3/library/zipimport.html)、[imp 删除说明](https://docs.python.org/3/library/imp.html)。

   `m4-importlib-20260909T102600.txt:19–27` 的 `IMPORTED` 与修后 `m4-importlib-after-20260909T103735.txt:19–27` 的本门 `RuntimeError` 一致支持**指定路径修复**。但跑器 `m4-importlib-probe.py:74–80` 没有记录 audit 事件序列，所列四个具体子模块事件的“实测清单”在获准证据中**未验证**。

   **建议：**对字符串子类使用不调用重载的基础字符串操作判定实际名称，并补子类契约；将路径、别名加载的完整封闭性保留为未证明项。

3. **MEDIUM｜问题 8：不是 3.14.4 独有结构，但作者对事件来源的表述过宽。**

   依据：[live_port_guard.py:691](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:691)、探针文件 `:312–319`。

   官方 CPython **3.8.0、3.12.0、3.14.4** 均有 builtin 导入前门与 `import_module → _gcd_import` 的区别，因此不是本机偶然现象。[3.8 实现](https://github.com/python/cpython/blob/v3.8.0/Lib/importlib/__init__.py#L98-L115)、[3.12 实现](https://github.com/python/cpython/blob/v3.12.0/Lib/importlib/__init__.py#L66-L81)、[3.14 实现](https://github.com/python/cpython/blob/v3.14.4/Lib/importlib/__init__.py#L64-L79)。

   但“只有 `__import__` 发事件、`import_module` 不发”不能作为全称结论：动态扩展 loader 本身会发事件，缓存命中的导入又可能不发。

   其他版本多发正确的 `uvloop.*` 事件不会因此误拦无关名称；真正未证明的是：每个 Python／uvloop／loader 组合是否都必然产生一个能命中的事件。当前日志只绑定了 CPython 3.14.4，未给出跨版本运行证明。

   **建议：**保留本机实测限定，改成描述具体入口和 loader 的机制；不要将该前缀修复标成全版本、全加载路径通过。

4. **MEDIUM｜问题 7：正式新增门没有整体恒真项；证据跑器有假通过路径，哨兵内有冗余断言。**

   依据：[m4-importlib-probe.py:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/m4-importlib-probe.py:98)、同文件 `:112–128`。

   该证据跑器遇到缺失裁定行只保存 `None` 并继续；最终仅以 `escaped` 是否为空判定成功。因此：

   - 删除毒化后的导入因 `ModuleNotFoundError` 失败，也会被归入 blocked；
   - 所有案例都缺裁定行时，仍可能输出 `BLOCKED` 并返回 0；
   - 子进程 rc 被打印，却不参与最后的成功条件。

   **这是条件性假通过，不是恒真。** 现有修后日志逐案出现正确的本门拒因，仍支持那次结果；正式新增探针 `:329–337` 已明确拒绝 `ImportError`，没有同样的判据缺口。

   新增门的致红条件逐项如下；表内契约位置均指 `test_live_port_guard_contract.py`：

   | 判据／位置 | 会红的具体条件 |
   |---|---|
   | H-1a 两个异常参数，`:72–94` | 对相应 `ValueError/RuntimeError` 仍向外抛，或返回非 None |
   | H-1a 记账行为，`:114–119` | 未抛指定拒因，或 total／blocked／unaccounted 任一不是 1 |
   | 哨兵精确类型，`:548` | 改为 bytes 或 str 子类 |
   | 哨兵首字符，`:549` | 改为 `"localhost"`，或其他非 NUL 首字符 |
   | 哨兵长度，`:550` | 改为前导 NUL 加 28 个普通字符 |
   | 哨兵末三项，`:551–553` | **前两项已通过时，没有独立致红输入**；精确 str 且首字符 NUL 已蕴含这三项 |
   | M-1 三个地址，`:566、569、572` | 分类器只判 `type(host) is str`，三项均红 |
   | 五个 uvloop 名称，`:645、665–666` | 任一对应事件不再抛匹配拒因；只拦顶层会使四个子模块实例红 |
   | `uvloopx`、`uvloop_shim`，`:671–678` | 误写裸 `startswith("uvloop")` |
   | `myuvloop`，同上 | 误写 `"uvloop" in name` |
   | `uv`，同上 | 误写 `startswith("uv")` |
   | 正式 importlib 探针，探针 `:329–337` | 导入成功、非本门 RuntimeError，或 ImportError |
   | M-3 正探针，探针 `:400–403` | 7691 会话 rc=0，或输出没有专属拒因 |
   | M-3 7692 验伪锚，探针 `:425–428` | 合法会话非零，或出现专属拒因 |

   四个 lookalike 锚单独会被“完全删除 import 分支”放绿，但对应阳性门会红，这是有效的正反配对。空用例中的 `assert True` 只提供可收集对象，M-3 的裁定来自子进程结果。

   **建议：**收紧证据跑器的完整性、拒因身份和 rc 检查；哨兵末三项可保留作说明，但不能计为三份独立检出能力。

5. **LOW｜问题 5：确实经过 pytest 插件入口；A/B 组合支持此次归因，B 的 rc=0 单独不够。**

   依据：[lifespan_isolation_guard_probes.py:356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/scripts/lifespan_isolation_guard_probes.py:356)、同文件 `:365–367`。

   实际执行参数是 `python -m pytest … -p tests.support.guard_plugin <临时目录>`，没有直调预检。显式目录优先于 `testpaths`；conftest 搜索沿测试路径祖先展开。**`rootdir/testpaths` 本身不会自动引入另一目录下的 `backend/tests/conftest.py`。**[pytest 配置源码](https://docs.pytest.org/en/stable/_modules/_pytest/config.html)。

   `m3-negctl.sh:49、67` 对 A/B 使用相同会话函数和相同 URI；`:59–61` 只替换唯一预检调用。两份日志均记录：

   - `:5–6`：A 为 rc=3，带实际 URI／白名单拒因；
   - `:9、12`：变异已应用，B 为 rc=0、拒因消失；
   - `:16–18`：还原前后哈希相同。

   这些组合支持“该会话差异依赖被删调用”，不能单凭 B=0 证明 conftest 从未加载。另须区别：日志中的 `INTERNALERROR` 本身即可产生 pytest rc=3，**这里并未证明账本最终结算触发**。

   `:358–363` 仍继承 `PYTEST_ADDOPTS/PYTEST_PLUGINS` 等环境，没有完全隔离插件来源，故不能外推所有运行环境。

   **建议：**接受本次最小会话证明；需要进一步加强时，记录实际插件／conftest 清单及关键 pytest 环境。

6. **LOW｜问题 3：新哨兵断言没有从实现获取期望值；允许安全属性相同的其他常量。**

   依据：[test_live_port_guard_contract.py:547](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:547)。

   `host = guard._SELFTEST_HOST` 读取的是**实际值**；期望是独立的 `str、0、28` 和字符串字面量。没有 `len(实现常量)` 与自身比较一类循环判据。

   `h2-negctl-after-20260909T103735.txt:6–11` 确实列出旧六项 PASSED；`:15–20` 明确显示新增项因 `ord('l') == 108` 而失败。

   换成另一个“精确 str、长度 28、首字符 NUL”的常量仍可通过，这是当前属性契约允许的范围；同时改坏分类器，也不必然使**这条常量测试**失败，分类器需要自己的测试。

   **建议：**保留独立属性断言；不要把它描述成锁定完整拼写或证明分类器严格相等。

7. **LOW｜问题 4：三条负例覆盖指定缺口，但不能排除其他错误分类方式。**

   依据：测试文件 `:566、569、572`；[live_port_guard.py:733](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:733)。

   IPv4、主机名、IPv6 四元组都有字面负例。`m1-negctl-after-20260909T103735.txt:6–17` 确实记录旧六项绿、新三项红，证明杀掉了指定的 `type(host) is str` 变异。

   保留形状检查，只把末行改成以下方式，仍能让这些用例全绿：

   - `type(host) is str and host.endswith("w4-live-port-guard-selftest")`：无 NUL 的同名普通主机也会被误判；
   - 精确 str 且 host 不属于 `{"127.0.0.1", "localhost", "::1"}`：列举过的主机被拒，其他普通主机仍会误判。

   这是静态反例，未运行；**当前 `:741` 使用精确相等，并没有上述错误。**

   **建议：**本卡指定变异的覆盖成立；可补“去掉 NUL 的近似哨兵”负例，不必要求有限测试穷尽所有错误实现。

8. **LOW｜问题 6：L-2 去重没有丢失朴素 URI 用例，取舍方向正确。**

   依据：[test_live_port_guard_contract.py:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:188)、同文件 `:355–373`。

   `:189–190` 仍明确设置 `"bolt://127.0.0.1:7692"` 并调用 `assert_test_uri_not_blocked()`，不抛即通过。被删列表项原本执行相同设置、相同调用、相同预期，所以没有让此输入失去唯一覆盖。diff 也确认 ftp/http/https 均保留。

   **建议：**保留当前去重；独立容器用例与同类现网拒绝用例继续构成正反对照。
