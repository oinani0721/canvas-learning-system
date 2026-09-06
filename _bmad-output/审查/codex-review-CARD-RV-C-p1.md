> 批次: BATCH-2026-09-05-第十二批 · 车道 Y8 · CARD-RV-C round-1 prompt-1
> 模型: `gpt-6-astra`（stderr 实测） · reasoning_effort: `ultra`（stderr 实测） · codex: `codex-cli 0.153.3`（stderr 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-RV-C-p1.md)"`
> 审查绑定: `e06009bc`（全量 `live_port_guard.py` 1093 行）+ `65cfd8ff`（r2 存档 111 行）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: …/.claude/worktrees/card-y8-w4-ast` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a070d1-b222-7603-b2e4-8c7a47ef45ef`

---

已逐行读完指定的 **1093 行代码和 111 行旧审**。以下 `live_port_guard.py:行号` 全部绑定 **`e06009bc:backend/tests/support/live_port_guard.py`**。另对抽取的原函数做了纯内存复核；未修改文件、安装审计钩子、创建 socket 或运行 pytest。

1. **HIGH：记账前执行的不可信方法可以抛异常，留下“已阻断、零账本”。**

   位置：`live_port_guard.py:383–385、491–493、246、251–258、512`。

   两条路径具有同一问题：

   - `extract_port()` 执行 `operator.index(raw)`，却只捕获 `TypeError`。如果它抛 `ValueError` 或 `RuntimeError`，执行会直接从第 491 行退出，尚未检查可信性或调用 `STATE.record()`。
   - `STATE.record()` 在第 246 行执行 `repr(address)`，第 251 行才开始增加计数。合法 tuple 子类可以覆写 `__repr__` 并抛异常，同样在记账前退出。

   抽取原函数后的内存结果：

   | 输入 | hook 结果 | total / blocked |
   |---|---|---|
   | 端口第一次求值为 7691，第二次返回 7692 | `RuntimeError` | 1 / 1 |
   | 端口第一次求值为 7691，第二次抛 `ValueError` | `ValueError` | 0 / 0 |
   | 底层地址为 `("127.0.0.1", 7691)`，tuple 子类的 `__repr__` 抛异常 | `ValueError` | 0 / 0 |

   **这不是第 498 行的自证分支。** 它说明即使自证分类已经修正，拒绝路径仍可能没有失败账；调用者吞掉异常后，后续结账看不到此次事件。

   **未验证：**真实 CPython socket 调用的完整复现及最终进程退出码。上表第一次端口求值由内存复核显式调用，不能冒充 C 层实测。

   **建议方向：**先判断端口对象是否可信，避免在拒绝和记账前执行其 `__index__`；记账不能依赖地址的 `repr()` 成功，格式化应有异常兜底。

2. **MEDIUM：延迟 import 的合法性论证与实际调用链矛盾。对应问题 4、5。**

   位置：`live_port_guard.py:764–768、775–776、901、946、603–606`。

   第 765–767 行声称 `canonical_target_ports()` **只由 session fixture 中的 `assert_test_uri_not_blocked()` 调用**。本文件实际有两个调用点：

   ```text
   assert_test_uri_not_blocked() → :901 canonical_target_ports()
   install() → :604 assert_neo4j_target_blocked()
             → :946 canonical_target_ports()
             → :775–776 import neo4j
             → 返回后才到 :605 安装审计钩子
   ```

   因此，“import 放在函数体内，所以一定发生在装门之后”不成立。第一个调用者在真实 pytest 中的调用时机，本读取面也没有独立证明。

   预检窗口的条件可以静态判定：

   | 条件 | 结论 |
   |---|---|
   | 尚无承重钩子，开关为 `"1"`，`NEO4J_URI` 非空 | 预检、导入和解析发生于无门窗口 |
   | 开关不为 `"1"` | 跳过这段预检；不能据此证明此前整个启动过程受保护 |
   | URI 缺失或为空 | 第 936–939 行提前抛错，不进入 canonical，也执行不到安装钩子 |
   | 此前已成功安装承重钩子，再次调用 `install()` | 原钩子仍在，这次预检不是无门窗口 |
   | 首次预检失败 | 执行不到第 605 行，没有补装或事后补记 |

   `poison_uvloop()` 不提供 socket 连接拦截。**无门窗口内若发生连接，本门不会阻止，也不会留下连接记录。** 即使 neo4j 已在导入缓存中，解析仍发生在上述位置，不能因此认定窗口消失。

   **未验证：**实际导入、解析器或其他线程是否在该窗口发起网络动作；不能声称已经发生现网连接。

   **建议方向：**修正注释中的全部调用链与前置条件。预检窗口按本卡要求只作判定，不重复计为另一条 HIGH，也不作整改承诺。

3. **LOW：最终总账标题错误；docstring 的注册边界也不够准确。对应问题 6。**

   位置：`live_port_guard.py:980、989–996、1001、1025、499–511`。

   第 980 行“**所有 cleanup / atexit 之后**”错误。第 989–996 行关于 **LIFO、仍有更早注册的回调随后执行**的说明，符合实际次序。

   但准确分界是第 **1001 行执行 `atexit.register()` 的时刻**，不是模块 import 时刻。本文件没有模块尾自动安装：在 import 之后、注册总账之前注册的回调，也会排在总账之后执行。

   当前实现确实在第 1025 行置 `_FINALIZING=True`，并提供第 499–511 行的迟到连接强制退出路径。

   采信标题的人可能只写“一次最终账本扫描”，省略此后的强制失败机制；更早注册的回调随后尝试连接，异常被吞掉或仅被打印时，进程仍可能退出 0。

   **建议方向：**统一标题和 docstring，以实际注册时刻描述次序。

4. **问题 1：旧审两种自证伪装已闭合；跨所有原生协议族的更强保证未验证。**

   位置：`live_port_guard.py:468–476、489–498`。

   旧审的 tuple 子类伪装被 `type(address) is tuple` 排除；普通 tuple 中的 str 子类伪装被 `type(host) is str` 排除。底层取槽也不再调用子类的索引方法。

   在函数和常量未被改写的前提下，第 498 行的**完整代码可达集合**为：

   - 事件为 `"socket.connect"`，`args` 至少两个元素；`args[0]` 不受检查，可以是 `None`、真实 socket 或任意对象。
   - `args[1]` 是精确 tuple，底层长度至少为 2。
   - 槽 0 是精确 str，内容等于 `"\x00w4-live-port-guard-selftest"`。
   - 槽 1 为受拦的精确 int；**或者**槽 1 不是精确 int，且 `operator.index()` 正常返回或抛出被捕获的 `TypeError`。
   - 后续槽位不限；豁免状态和 `_FINALIZING` 不影响这条分支，因为它们在后面才检查。

   所以，`(哨兵, None)`、`(哨兵, True)`、`(哨兵, 非精确整数对象)`等合成地址也能进入免记账分支。长度不足 2、精确安全整数端口，以及 `__index__` 抛非 `TypeError` 的输入均不进入第 498 行。

   | 来源或协议族地址形式 | 第 498 行可达性与连接结论 |
   |---|---|
   | 本模块或外部直接 `sys.audit(...)` | 满足上述集合即可进入；即使 `args[0]` 是真实 socket，合成事件本身也不执行 connect |
   | AF_INET / AF_INET6 的真实地址 | 只有精确哨兵形状能通过分类器；目标 CPython 是否在发出 audit 前拒绝 NUL 主机名，**未验证** |
   | AF_UNIX 的 str / bytes 地址，包括抽象地址形式 | 非 tuple，不能进入自证分支；本门可能允许 UNIX 连接，不能将其认作 TCP 7691/7687 连接 |
   | 首槽为数值的 tuple 形式，如 NETLINK、VSOCK、TIPC、QIPCRTR | 有效数值首槽不能满足精确 str 哨兵条件 |
   | 首槽为字符串的其他形式，如 PACKET、CAN、Bluetooth、ALG 等 | 本门不检查 family；原生转换是否接受具体哨兵形状并触发 audit，**未验证** |
   | 其他平台专有形式 | 分类仍完全由上述集合决定；平台支持及原生接受性，**未验证** |

   **任何真实调用一旦到达第 498 行，抛出的异常都会阻止该次随后执行的 connect。** 但“含 NUL，所以任何协议族都不可能是有效地址”不能仅凭作者注释成立。

   结论：旧 HIGH-1 的两种具体伪装已修；实现识别的是地址形状，不能证明事件“由本模块自己合成”。没有依据据此重列一个已确认的 TCP 绕过 HIGH。

5. **问题 2、3：tuple 子类的正常返回路径成立；非 tuple 的放行不能直接等同于 TCP 漏洞。**

   位置：`live_port_guard.py:374–385、412–420、493`。

   两个函数都直接读取 tuple 底层槽位，内存复核确认覆写 `__len__`、`__getitem__` 不能隐藏底层端口。

   | 地址情况 | 判定 |
   |---|---|
   | tuple／子类，底层端口为精确 `7691` 或 `7687` | 第一子句命中 |
   | tuple／子类，底层端口为精确 `7692` | 两子句均假，允许通过 |
   | 有状态 `__index__` 第二次正常返回安全端口 | `type(raw) is int` 仍为假，第二子句命中 |
   | 普通非 tuple | `extract_port=None`、可信性 `True`，两子句均假 |
   | 底层长度不足 2 的 tuple | 同样为 `None / True`，两子句均假 |

   因此，用户指定的“**第一次受拦、第二次安全**”对象仍按不可信处理。异常返回路径则存在第 1 条 HIGH。

   代码已消除“仅因地址是 tuple 子类就误拦合法 7692”的问题。**未验证：**实际安装的 Neo4j 地址对象槽位类型、真实调用路径及连接兼容性；第 362–366 行作者自述不能替代这些证据。

   第 413 行确实存在明确放行面，例如列表 `["127.0.0.1", 7691]` 直接交给 hook 会返回且零账。但手发审计事件不建立连接。**是否存在目标 CPython 实际接受、并能指向受拦 TCP 端口的非 tuple 地址，未验证；本读取面没有证据据此认定 HIGH/BLOCKER。**

6. **问题 7：代次撤销局部成立；“只在对应 marker 用例内豁免”的完整保证不成立。**

   位置：`live_port_guard.py:234–258、309–327、159–164、1070–1081`。

   `begin_item()` 发放递增代次，`end_item()` 在同一把锁内换代，`record()` 持锁比较代次。过期时强制改为 `<unknown>`、`exempt=False`。内存复核确认：复制豁免 context 后执行 `end_item()`，旧 context 再触发受拦事件得到 **blocked=1、owner=`<unknown>`、exempt=False**。

   因此，正常换代后，旧 context 不能继续凭旧票获得 advisory。`_OWNER_CV` 是归属标签，实际撤销依据是 `_GEN_CV`。

   但完整保证有两项限制：

   - **并非仅 marker：**第 1079–1081 行明确允许未打 marker 的 `integration/`、`e2e/` 路径豁免。这是第 159–164 行声明的有意策略，不另列新 HIGH。
   - `begin_item(owner, exempt)` 直接接受布尔值，本身不验证 marker。真实 pytest 接线是否只传入合法判定、是否在所有异常路径执行 `end_item()`、任务和线程上下文是否正确归属，均为**未验证**。需要实际协议 hook 和跨用例上下文证据。

   代次检查约束的是检查时的授权；它也不能撤回已经在有效豁免期获准、随后才继续执行的连接操作。

**整体裁定：FAIL，计 0 BLOCKER / 1 HIGH / 1 MEDIUM / 1 LOW；既有预检窗口不重复计数，所有“未验证”项均不视为通过。**
