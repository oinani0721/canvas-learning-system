> 批次: BATCH-2026-09-05-第十一批 · Z3-B · CARD-W4-3a round-2（首部由主 session 2026-09-05 按协议 §2.1 补记，正文一字未改）
> 模型: `gpt-6-astra`（stderr 实测） · reasoning_effort: `ultra`（stderr 实测） · codex: 未自证（stderr 无版本行）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`（第十一批手册规定形态；实参见车道 stderr）
> 审查绑定: **不绑合并态 e06009bc**（钉 live_port_guard.py:425 旧区并引用已删 `_port_of_uri`）→ 第十二批 Y8-A 首次合并态外审
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4` / `model: gpt-6-astra`

---

**整体裁定：扣除已另立卡事项，本轮确认 0 BLOCKER / 2 HIGH / 1 MEDIUM；这套门目前仍不能通过承重验收。** 已修的端口白名单问题不再列入发现，但“拦截必然留下失败证据”和“配置预检先于豁免生效”仍有缺口。

以下结论来自指定文件的代码审查，以及抽取原函数后的纯内存执行。没有运行 pytest、修改文件或连接任何数据库端口；实际连接结果和完整 pytest 退出码均未实测。

1. **HIGH：真实地址可以伪装成自证地址，拦截异常因此不入账。**

   位置：[live_port_guard.py:425](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/support/live_port_guard.py:425)、同文件第 447、462 行。

   关键代码：
   ```python
   return isinstance(address, tuple) and len(address) >= 1 and address[0] == _SELFTEST_HOST
   ...
   if _is_selftest_address(address):
       raise _SelfTestBlocked(...)
   if _FINALIZING:
       ...
   if STATE.record(address):
       raise RuntimeError(...)
   ```

   端口检查已经拒绝信任 tuple 子类，但自证分类仍调用可重载的 `len`、`[0]` 和 `==`。因此存在两种伪装：

   - tuple 子类底层保存 `("127.0.0.1", 7691)`，但 `[0]` 返回自证主机名。
   - 地址是普通 tuple，主机名是内容为 `"127.0.0.1"` 的 str 子类，其 `__eq__` 对自证主机名返回真。

   两者都会进入阻断分支，随后在 `STATE.record()` **之前**抛出 `_SelfTestBlocked`。它继承 `RuntimeError`，普通异常捕获就能吞掉它。

   原函数纯内存复核结果：

   | 输入 | hook 结果 | blocked | unaccounted |
   |---|---|---:|---:|
   | 普通受拦地址 | `RuntimeError` | 1 | 1 |
   | 主机名子类伪装 | `_SelfTestBlocked` | 0 | 0 |
   | tuple 子类伪装 | `_SelfTestBlocked` | 0 | 0 |

   **连接仍被异常阻止，但账本为零，后续结账无法据此拒绝退出码 0。** 此分流还早于 `_FINALIZING` 检查；纯内存复核中将该标志设为真，伪装地址仍绕过强制退出分支。这是自证分类缺陷，独立于已归属的最终结算原子性。

   建议修法：免记账自证必须绑定合成事件身份，例如同时要求 `args[0] is None`、精确 tuple、精确 str 哨兵，避免执行地址子类的重载方法。现有[契约测试第 270 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/unit/test_live_port_guard_contract.py:270)使用的底层主机名本来就是哨兵，应补充“底层是真实地址、表面伪装成哨兵”的反例。

2. **HIGH：先启用 advisory，后做 session URI 预检，不能保证错误配置在连接前被拒绝。**

   位置：[tests/conftest.py:131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/conftest.py:131)、同文件第 92–106 行；[guard_plugin.py:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/support/guard_plugin.py:42)。

   用例协议先执行：
   ```python
   exempt, _why = live_port_guard.is_exempt(item, Path(__file__).parent)
   live_port_guard.begin_item(item.nodeid, exempt)
   return (yield)
   ```

   URI 校验则放在随后执行的 session fixture：
   ```python
   live_port_guard.assert_test_uri_not_blocked()
   ```

   因而存在一个确定的窗口：**advisory 已生效，URI 尚未预检。** 此时一个 `pytest_runtest_setup` wrapper 在其 `yield` 前消费错误的 `NEO4J_TEST_URI=:7687`，连接会被 advisory 放行；之后 fixture 报错不能回滚已发生的连接。

   这条发现针对预检顺序，不把有意 advisory 本身算作缺陷。**未验证的是当前套件是否已有利用该窗口的 fixture 或 hook**；六文件内没有确认到这样的消费者，因此不升级为已确认 BLOCKER。

   建议修法：至少在 `begin_item(..., exempt=True)` 前完成预检，并明确配置变更后的重新校验规则。仅依赖另一个同级 autouse fixture，不能建立可靠的前置顺序。

3. **MEDIUM：目标范围预检仍使用分叉解析器，会把 query／fragment 中的数字认作目标端口。**

   位置：[live_port_guard.py:819](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/support/live_port_guard.py:819)、同文件第 835–844 行。

   关键代码：
   ```python
   port = _port_of_uri(uri)
   ...
   tail = tail.split("/", 1)[0]
   port_str = tail.rsplit(":", 1)[1]
   return int(port_str)
   ```

   纯内存执行确认：

   | URI | 门提取的端口 | `urlparse` 的 authority 端口 |
   |---|---:|---:|
   | `bolt://127.0.0.1:11434#tag:7687` | 7687 | 11434 |
   | `bolt://127.0.0.1:7692?x=:7691` | 7691 | 7692 |

   因此 `W4_GUARD_REQUIRE_BLOCKED_TARGET=1` 可以错误确认“目标在受拦范围内”。这不是已经修好的 `NEO4J_TEST_URI=:0` 问题，而是另一处配置断言仍使用旧解析器。

   建议修法：复用驱动口径的规范化解析，并加入上述反例；调整调用位置，保持先安装 socket 门、再加载驱动的顺序。

   **未验证**实际驱动是否接受这些完整 URI，以及排除范围内是否另有检查将其拒绝。因此这里只认定预检假通过，不声称已经复现真实现网连接。

没有另列 LOW，也没有依据将已归属的最终结算原子性升级为 BLOCKER。

对你指定的四个问题，补充明确边界：

- **四条 socket 路径：**对已装门、非 advisory、普通 IPv4／IPv6 tuple 加精确 int 端口，没有找到能直接绕过受拦端口判定的路径。但上面的 HIGH 1 已证明“抛了却没有失败账”的路径。所读契约主要使用合成审计事件，不能替代四种真实 API 和完整退出码验证。

- **advisory 风险面仍然覆盖全部现网端口。** [第 253–255 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/support/live_port_guard.py:253)对豁免连接只增加 advisory 并返回 `False`，没有绑定已校验的目标。具体仍可放行：不设置／设置空 `NEO4J_TEST_URI`；设置合法 `:7692`，实际使用另一条 `NEO4J_URI=:7691` 或硬编码 `:7687`；session 预检后再改变测试 URI。纯内存调用原 hook 已确认 advisory 的 `:7687` 返回正常、`blocked=0`。这是有意设计的实际范围，白名单修复没有缩小它。

- **解析完备性只能给局部通过。** 普通地址、非 int 端口、tuple 子类的端口判据已有相应处理；旧 `:0` 路径从当前代码上已闭合。但自证分类仍有上述漏洞；`canonical_target_port()` 只检查初始 URI 端口，不能证明主机身份、代理后的数据库身份或后续路由／resolver 目标。后两者的实际驱动链本轮未验证。

- **装门时序是局部成立，全启动链未验证。** 根 [conftest.py:26–32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4/backend/tests/conftest.py:26)确实在自己的 `app.*` import 前安装；插件也在自身 import 期安装。但六文件不能证明它早于先行插件、包初始化或嵌入式 `pytest.main()` 之前的业务 import。需要实际启动命令、插件加载顺序及断网启动探针才能确认全局保证。

子进程新解释器、原生扩展／libc、已建立连接复用和其他映射端口，属于文件已经声明的覆盖边界，不重复计为新发现。另外，uvloop 的真实 `importlib` 加载链仍**未验证**：当前 hook 只匹配根名 `"uvloop"`，契约手发 `sys.audit("import", ...)`，不足以证明所有真实导入路径被封锁。

**如果当初尚未合入，今天我不会批准它以当前状态合入；应先关闭这两条 HIGH，再做承重验收。**
