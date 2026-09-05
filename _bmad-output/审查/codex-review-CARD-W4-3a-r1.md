**本卡未通过：发现 1 个 BLOCKER、1 个 HIGH、1 个 MEDIUM、1 个 LOW。** 原来的 `bolt://…:0` 已被拒绝，但驱动解析链仍存在可绕过预检的分叉。

审查基于 `HEAD=004e08ccaa8a` 的三个未提交文件，以及本机 **CPython 3.14.4 / Neo4j 6.1.0**。期间工作树追加了 scheme 检查，已重新核对；以下行号对应收尾版本。

**BLOCKER — 路由 URI 使用了错误的解析分支，可以放行 7687／7691。**

位置：[live_port_guard.py:756](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/support/live_port_guard.py:756)。

新预检统一调用 `Address.parse(parsed.netloc)`。实际驱动在 `_sync/driver.py:277–280` 对 `neo4j[+s|+ssc]` 走路由分支，随后 `_Routing._parse_targets:470–479` 调用 `Address.parse_list()`；后者在 `_addressing.py:216–218` **按空白拆分多个地址**。

使用真实 `GraphDatabase.driver()` 构造驱动、读取初始地址，未连接网络，得到：

| `NEO4J_TEST_URI` | 新预检 | 真实驱动的唯一初始地址 |
|---|---|---|
| `bolt://127.0.0.1:0` | 拒绝，canonical=7687 | `127.0.0.1:7687` |
| `neo4j://127.0.0.1 :7692` | **放行，canonical=7692** | **`127.0.0.1:7687`** |
| `neo4j://[::1]:7691 [::1]:7692` | **放行，canonical=7692** | **`[::1]:7691`** |

第二个反例换成 `neo4j+s`、`neo4j+ssc` 也成立。驱动 `_sync/io/_pool.py:701` 取 `addresses[0]`，因此不是随机选择地址。有效 advisory 上下文中，guard 的 `record():253–255` 返回 `False`，`_audit_hook:462–463` 不抛；新增 tuple 判据也不能阻断这个组合。

反方向也有误拒：`neo4j://127.0.0.1:7692 localhost:7692` 被预检拒绝，真实驱动却接受并保存初始地址 `127.0.0.1:7692`。

**建议：**使用真实 `parse_neo4j_uri()` 区分 direct／routing，按对应链路解析目标，并逐个验证端口白名单；加入上述反例。使用 `parsed.netloc` 本身正确，但不能据此声称完整复现了驱动链路。若声明覆盖“最终连接”，还须考虑服务器公布的后续路由地址。

**HIGH — 一律拒绝 tuple 子类，会误拦真实同步 Neo4j 驱动的合法 7692 连接。**

位置：[live_port_guard.py:363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/support/live_port_guard.py:363)、同文件 `391–393`。

实际驱动 `_addressing.py:85` 定义 `Address(tuple)`，DNS 解析结果是 `ResolvedIPv4Address`／`ResolvedIPv6Address`。同步连接入口 `_async_compat/network/_bolt_socket.py:512` **直接执行 `s.connect(resolved_address)`**，没有转换为精确 tuple。

纯内存调用真实地址对象和 `_audit_hook()`，IPv4、IPv6 的 7692 地址均得到：

```text
extract_port=None
port_is_trustworthy=False
非豁免：RuntimeError，blocked +1
豁免：返回，但 advisory +1
```

仓库存在实际非豁免调用：`test_cypher_contract_gate.py:56–81`、`test_migrate_write_identity_g23.py:36–60` 在模块收集阶段执行同步 `verify_connectivity()`。此时门已经安装，用例豁免尚未设置；合法容器连接到达 socket 层就会被阻断，模块探针吞异常后标记整文件 skip，并留下未结账拦截记录。

**建议：**对 tuple 及子类使用 `tuple.__len__()`、`tuple.__getitem__()` 读取底层槽位，保留精确 int 检查；补充真实 `ResolvedAddress(...7692)` 的 hook 正例。注释所谓“Python 无法读取底层槽位”“本仓库不存在这种写法”均不成立，新增契约自身就在第 300 行用 `tuple.__getitem__()` 读取了真实端口。

**MEDIUM — 新探针 B 可以因错误的拒绝原因通过。**

位置：[lifespan_isolation_guard_probes.py:989](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/scripts/lifespan_isolation_guard_probes.py:989)。

B 只检查异常包含 `"7687"`，但 guard 的解析失败分支 `812`、普通白名单拒绝分支 `819–820` 都会附带默认端口 7687。

在纯内存中执行原始探针 body，仅将 `:0` 的 helper 结果分别改为 `0`、`None`，**两种错误实现仍使 A/B/C 全部 PASS、退出码为 0**。A 当前能够识别相交自检；C 能排除整函数恒抛，却不能排除上述错误。

**建议：**B 直接断言 canonical 结果等于 7687，并绑定白名单拒绝分支或结构化异常字段。现有契约第 `148–149` 行能另行抓住这两种突变，因此这里属于探针证据缺口。

**LOW — “合法容器写法”的 query 正例实际被驱动拒绝。**

位置：[test_live_port_guard_contract.py:239](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/unit/test_live_port_guard_contract.py:239)。

`bolt://127.0.0.1:7692?routing=false` 通过 guard，但真实 `GraphDatabase.driver()` 立即抛 `ConfigurationError`：`_sync/driver.py:269–275` 禁止 direct driver 携带非空 routing context。

**建议：**合法 query 正例改为 `neo4j://127.0.0.1:7692?routing=false`，并独立验证 Bolt query 的驱动拒绝行为。另外，guard docstring 第 703 行声称 userinfo tail 会使 `Address.parse()` 抛 `ValueError`，本机实现实际返回字符串端口，也应修正文案。

其余核对结果：

- **导入时序无新增问题：**`conftest.py:28` 装门早于 `30–32` 的业务 import，预检在 `106`；冷导入 Neo4j 的离线验证未出现网络操作。
- **相交自检位置正确：**当前第 `798` 行先于 URI 读取；无 URI 时污染白名单也会拒绝。根 conftest 和 `guard_plugin.py:46` 均经过它。不过 `install()`、`_audit_hook()` 本身不调用它，不能把它描述为每次装门／连接都会执行的检查。
- **tuple 恶意重载防线生效，自证仍正常：**两处修改合看确实进入受拦分支；`audit_hook_alive()` 实测为 `True`。
- 13 个“合法”正例中，除上述 Bolt query 外，其余 12 个在预检和驱动构造阶段一致，包括安全 scheme、IPv6、大小写、末尾斜杠和 path。

全程未修改文件，未连接任何数据库端口。完整 pytest 退出结果、TLS／数据库连通性、实际服务器路由表均**未验证**；这些需要另行获准的隔离运行。收尾三文件 SHA-256 前缀分别为 `faefb1224fa33`、`16eaae298681`、`264b6ddb394b`，重复采样一致。

**整体裁定：阻断级问题共 2 个（BLOCKER 1、HIGH 1），本卡不能通过。**


