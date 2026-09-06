> 批次: BATCH-2026-09-05-第十二批 · 车道 Y8 · CARD-RV-C round-1 prompt-2
> 模型: `gpt-6-astra`（stderr 实测） · reasoning_effort: `ultra`（stderr 实测） · codex: `codex-cli 0.153.3`（stderr 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-RV-C-p2.md)"`
> 审查绑定: `e06009bc`（契约 534 行）+ `004e08cc..e06009bc`（guard_probes 增量 99 行）+ `65cfd8ff`（r1 存档 82 行）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: …/.claude/worktrees/card-y8-w4-ast` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a070d1-bdb2-7f21-a524-3ba7cc67d92e`

---

已逐行读完指定的 **534 行测试、99 行 diff、82 行存档**。以下测试及实现行号均绑定 `e06009bc`，存档绑定 `65cfd8ff`；未读取工作区同名文件，未修改文件、运行 pytest 或连接端口。

1. **HIGH — 哨兵的安全属性没有独立断言，修改常量后测试会一起漂移。**

   **位置：**`backend/tests/unit/test_live_port_guard_contract.py:417、424、427、441、459`；实现 `backend/tests/support/live_port_guard.py:439、476、497`。

   实现当前使用含 NUL 的哨兵，但测试的哨兵输入和比较值也来自 `guard._SELFTEST_HOST`。**按源码静态推演，将它改为 `"localhost"`，该类六个测试仍全部满足：**

   - 真哨兵正例随常量改成 `"localhost"`；
   - tuple、str 子类仍被精确类型检查拒绝；
   - 非 tuple、空 tuple 的结果不变；
   - 11434 安全对照不进入自证分类；
   - 最后一条仍获得 `_SelfTestBlocked`。

   因而测试锁住的是**“分类与当前常量一致”**及部分类型边界，没有锁住**“该常量不能代表真实连接目标”**。变更后的匹配地址会在实现 `:497–498` 提前抛出私有异常，跳过 `:512` 的记账。

   **建议：**独立断言哨兵是精确 `str` 且包含字面量 `"\x00"`，并补固定普通主机名的负例。动态变异执行结果**未验证**。

   精确说，这里是 **6 个测试、9 个显式 `assert` 和一个 `pytest.raises`**；并非每条断言都引用常量，例如 `:428` 的底层主机期望就是固定字面值。

2. **MEDIUM — 缺少“普通 tuple＋普通真实主机”的分类负例，主机匹配条件可失去作用而不被发现。**

   **位置：**`backend/tests/unit/test_live_port_guard_contract.py:416–459`；实现 `backend/tests/support/live_port_guard.py:476、493–498`。

   一个具体静态反例：把实现 `:476` 从

   ```python
   return type(host) is str and host == _SELFTEST_HOST
   ```

   改成仅判断 `type(host) is str`，该类六个测试仍能满足。已有两个伪装用例被类型检查挡住；`:453–454` 的安全对照使用 11434，在端口判断处便绕过自证分类。

   **建议：**至少补充以下独立负例：

   ```python
   _is_selftest_address(("127.0.0.1", 7691)) is False
   _is_selftest_address(("localhost", 7687)) is False
   _is_selftest_address(("::1", 7691, 0, 0)) is False
   ```

   若要完整锁住精确类型契约，还可加入“底层内容就是哨兵的 tuple 子类”“内容就是哨兵的 str 子类”，确认不能因内容相同而接受子类。

   **但用户提出的“底层真实受拦、表面伪装哨兵”并未漏测：**`:419–429` 明确构造 `Disguise(("127.0.0.1", 7691))`，`:427` 验表象，`:428` 验底槽，`:429` 验拒绝；str 的 `__eq__` 伪装及前提断言也在 `:431–442`。

3. **MEDIUM — 新探针证明了预检函数拒绝，尚不能证明实际安装入口保留该预检。**

   **位置：**`backend/scripts/lifespan_isolation_guard_probes.py:976、992、1005、1014、1021、1028`。

   增量 body 直接调用 `assert_test_uri_not_blocked()`，没有经过实际安装或 pytest 插件入口。实现 `backend/tests/support/live_port_guard.py:581–616` 的 `install()` 本身也不调用这个函数。

   因此，**即使外部入口漏掉此预检，探针里的直接函数调用仍可通过**。这属于安装级证明缺口；当前合并态外部入口是否接线正确，因不在读取面内，**未验证**。

   **同时，不能重报 round-1 的“任意失败都能冒充预期拒绝”：当前增量已加强判据。**

   | 段落 | 合并态代码要求 |
   |---|---|
   | A，`:973–980` | 清除 URI、污染白名单；必须得到含“相交”的 `RuntimeError` |
   | B，`:987–996` | canonical 必须等于 `(7687,)`，随后必须因“白名单”拒绝 |
   | B2，`:1000–1009` | canonical 必须等于 `(7687, 7692)`，随后必须因“白名单”拒绝 |
   | C/C2，`:1012–1023` | 合法单地址及多地址必须不抛异常 |
   | 收口，`:1025–1028` | `problems` 为空，子进程预期退出码为 0 |

   所以旧版 helper 返回错误的 `0`／`None` 却通过 B 的问题，已被新断言挡住。按当前源码，没有发现另一个现有失败分支能仅凭“失败了”满足整组判据。

   **建议：**将证明陈述限定为“预检函数因交集拒绝”；安装级证据另经真实入口取得。拒因接口可进一步使用专属异常或结构化 `reason`、`admitted_live`，精确断言交集为 `{7687}`，减少对文案子串的依赖。

4. **LOW — 存在完全重复的接受用例，84 项不能理解成 84 种独立安全形态。**

   **位置：**`backend/tests/unit/test_live_port_guard_contract.py:134–136、289、304–307`。

   参数表中的 `bolt://127.0.0.1:7692` 与前面的独立测试，输入、调用及“不抛异常”的期望完全相同，可合并。

   其他“结果相同”应区别对待：

   - `:200–203` 的 ftp/http/https 都覆盖当前实现的不支持 scheme 分支，存在分支层面的冗余。
   - `:157–158` 的 `:0`／`:00` 虽然期望相同，仍覆盖不同输入拼写。
   - `:249–251` 的三种 routing scheme 期望相同，但能检查各 scheme 是否正确分流，不宜全部删掉。

   **建议：**合并明确重复项，保留有输入形态意义的参数；不要以收集数量代替覆盖说明。

其余指定问题的核对结果如下，不额外计为缺陷。

**网络调用：四个真实入口的执行覆盖为 0/4。**

| 入口 | 契约测试实际覆盖 |
|---|---|
| `socket.socket.connect` | `test_live_port_guard_contract.py:498` 仅比较函数身份 |
| `socket.socket.connect_ex` | `:499` 仅比较函数身份 |
| `_socket.socket` 层 | 没有直接入口用例 |
| `socket.SocketType` | 没有直接入口用例 |

534 行中没有创建 socket 或调用真实 `connect()`／`connect_ex()` 的用例。`:393、454、459` 是直接调用 `_audit_hook()`；`:490、493、516` 的在位检查最终到实现 `live_port_guard.py:656`，执行的是合成 `sys.audit("socket.connect", ...)`，不会因事件名称而发起连接。

因此，可以确认**这些测试体没有真实连接调用**；实现 `live_port_guard.py:18–22、482–484` 声称的“四入口都会触发审计事件”，不能由该契约文件证明。需要绑定提交及解释器版本的独立入口探针执行证据，本轮**未验证**。

作者“只用纯函数”的措辞也不精确：测试会修改环境变量、`sys.modules`，并在 `:479–480` 创建临时文件；这些副作用不等于联网。整个 pytest 启动及依赖导入过程是否零联网，仍**未验证**。

**安全地址对照有效，但证明范围有限。**

`test_live_port_guard_contract.py:448–454` 确实能让“hook 一律抛异常”的实现失败；`:393` 还有驱动安全地址的另一条对照。但它不能补上发现 2 的主机分类缺口，因为 11434 不进入受拦分支。

**round-1 HIGH 已有明确回归门，不能裁定为“只修实现、没留测试”。**

`test_live_port_guard_contract.py:380–393` 使用真实 `neo4j.Address.parse("127.0.0.1:7692")`，依次断言：

- `:390`：确实为 tuple 子类；
- `:391`：提取端口为 7692；
- `:392`：端口可信；
- `:393`：合成 hook 调用返回 `None`。

`:395–404` 另有同类地址指向 7691 的分类对照。剩余边界是没有直接构造存档 `codex-review-CARD-W4-3a-r1.md:38–51` 所述的 `ResolvedIPv4Address`／`ResolvedIPv6Address`；这些具体类型的覆盖**未验证**。

**参数化计数与重要形态：静态展开支持 51 → 84。**

| 参数化测试位置 | 展开项数 |
|---|---:|
| `test_live_port_guard_contract.py:87` | 4 |
| `:104` | 3 |
| `:165` | 5 |
| `:171` | 5 |
| `:209` | 5 |
| `:257` | 5 |
| `:305` | 13 |

计算为 **44 个非参数化定义＋40 个参数实例＝84**；`:239` 的内部 scheme 循环不增加收集项。实际 pytest 收集数及通过结果**未验证**。

重要形态没有因为“只写在参数表中”而失去断言：

- `:253` 的“首地址 7692、第二地址 7691”，由 `:260` 断言完整端口序列，再由 `:262–263` 断言拒绝。
- `:159` 的 IPv6 零端口，由 `:178` 的固定 `(7687,)` 期望锁住。
- `:295–301` 的主机名、IPv6、大小写、query/path 等合法形态，仅共享 `:307` 的接受期望，没有逐项精确 canonical 结果断言。这是证明范围较窄，并非没有测试。

这些字面期望与发现 1 不同：它们没有从被测 helper 的当前结果取得期望值。

**整体裁定：本卡证明链尚未闭合，暂不通过；BLOCKER 0、HIGH 1、MEDIUM 2、LOW 1。**


