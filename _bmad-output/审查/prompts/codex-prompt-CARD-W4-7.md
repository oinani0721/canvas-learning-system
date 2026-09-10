# 独立复核：CARD-W4-7（W4 测试隔离门 — RV-C 遗留六条）

## 一 背景与最小读取面

被审对象是一个 **pytest 测试进程内的隔离门**：它监听 CPython 的 `socket.connect` 审计
事件，阻止测试进程连上开发机上的 Neo4j（端口 7691 / 7687），并在进程退出前做一次
「最终结算」——发现有拦截记录无人认领，就把进程退出码强制成 3。

本卡处理上一轮复核（RV-C）留下的六条：H-1a / H-2 / M-1 / M-3 / M-4 / L-2。
其中 **M-4 实测出一个真漏洞**（详见 §二 (e)），其余五条是判据覆盖面的收紧与去重。

**请只读下面这几处，不要扩散到仓库其它部分**（工作目录 = 本仓库根）：

1. 本卡完整改动面：
   `git diff de6ea625 <审SHA> -- backend/tests/support/live_port_guard.py backend/tests/unit/test_live_port_guard_contract.py backend/scripts/lifespan_isolation_guard_probes.py`
   （`de6ea625` 是本卡开工前那一 commit；本卡未改 `backend/tests/conftest.py` 与
   `backend/tests/support/guard_plugin.py`）；
2. `backend/tests/support/live_port_guard.py` 的四段：
   - `:515-575`（`extract_port` :519，修改点是 `:563` 的 `except`），
   - `:640-760`（`_SELFTEST_HOST` :652、`_is_uvloop_module` :685、`_is_selftest_address` :713），
   - `:780-810`（`_audit_hook` 的 import 分支 :798），
   - `:1040-1090`（`canonical_target_ports` :1044，只核不改）；
3. `backend/tests/unit/test_live_port_guard_contract.py` 的三个类**全文**：
   `TestExtractPort` :37、`TestSelftestAddressClassification` :473、`TestGuardLiveness` :598
   （另 `TestPortTrustworthiness` :387 用于判断 H-1a 有没有连带翻掉既有语义）；
4. 新探针函数体：`backend/scripts/lifespan_isolation_guard_probes.py`
   `probe_uvloop_importlib_reimport_blocked` :309、
   `_run_minimal_pytest_session` :349、
   `probe_precheck_runs_through_the_real_entrypoint` :377、
   `probe_precheck_entrypoint_negative_control` :415；
5. 证据（用于核对作者自述是否与实测一致），全部在 `_bmad-output/审查/evidence-w47/`：
   `h1a-red-*.txt` / `h1a-green-*.txt`、`h2-negctl-*.txt`、`m1-negctl-*.txt`、
   `m3-negctl-*.txt`、`m4-importlib-*.txt`（修前）与 `m4-green-*.txt`（修后）、
   跑器 `h2-negctl.sh` / `m1-negctl.sh` / `m3-negctl.sh` / `negctl_patch_w47.py` /
   `m4-importlib-probe.py`。

## 二 作者自述（请独立核对，不要采信）

- **(a) H-1a / `extract_port` 只捕 `TypeError`**：该函数上半段读底层槽位用
  `except Exception`（fail-closed），下半段 `operator.index(raw)` 只捕 `TypeError`。
  `__index__` 是调用方给的任意用户代码，抛 `ValueError` / `RuntimeError` 时异常从这里
  逸出，而唯一调用点 `_audit_hook` 是在 `STATE.record()` **之前**调它的 ⇒ 连接被阻断、
  账本为零。修法：`except TypeError` → `except Exception`，并写明为什么不能只捕
  `TypeError`。作者声称**没有**改变返回语义（取不到端口 ⇒ None ⇒
  `port_is_trustworthy` 随后判不可信 ⇒ 照样走受拦分支、照样进账），
  且 `TestExtractPort` / `TestPortTrustworthiness` / 探针 `toctou-index-port` 一条没翻。
- **(b) H-2 / 哨兵常量无独立断言**：作者声称原 `TestSelftestAddressClassification` 的
  **6 条一条都拦不住**「把 `_SELFTEST_HOST` 改成 `"localhost"`」（4 条以该常量为输入或
  期望值、2 条本就不看它），负控 `h2-negctl-*.txt` 里逐条贴了 6 行 PASSED 原文。
  新增断言：`type(...) is str` / `ord(host[0]) == 0` / `len == 28` / `!= "localhost"` /
  `!= "127.0.0.1"` / `"\x00" in host`。
- **(c) M-1 / 缺普通 tuple 负例**：补三条字面调用
  （`("127.0.0.1", 7691)` / `("localhost", 7687)` / `("::1", 7691, 0, 0)` ⇒ 都是 False）。
  负控 `m1-negctl-*.txt`：把 `_is_selftest_address` 末行改成只判 `type(host) is str`
  （Codex 原话的那个实现）后，旧 6 条**全绿**、新 3 条**全红**。
- **(d) M-3 / 预检只在函数级被证**：既有静态门只锁「这行写在 `pytest_configure` 里」，
  既有探针 `guard-allowed-test-ports-cannot-admit-live` 是**直调**。本卡加一条走**真实
  pytest 入口**的探针（`-p tests.support.guard_plugin` + 临时目录里一个空用例，
  `NEO4J_TEST_URI` 指向 7691）要求会话 fail-closed（rc≠0 **且**输出含预检拒因串），
  外加一条验伪锚（URI 指向 7692 ⇒ rc=0 且无拒因）。翻转对照 `m3-negctl-*.txt`：
  把预检从 `pytest_configure` 摘走后，同一会话 rc 从 3 变 0、拒因串消失。
  作者声称测试文件刻意放在 `backend/tests` **之外**，以免那里的 conftest 做同一条预检
  把翻转喂饱。⛔ 只做 URI 字符串判定，不建任何连接。
- **(e) M-4 / uvloop 两层防御 —— 这条是实测出来的真漏洞**：
  实测（`m4-importlib-*.txt`，本树 CPython 3.14.4）——`import` 审计事件由 `__import__`
  （`import` **语句**）抛出，`importlib.import_module(name)` 走 `_bootstrap._gcd_import`，
  **不为顶层名抛事件**。于是 `del sys.modules["uvloop"]`（摘掉非承重的毒化层）之后，
  `importlib.import_module("uvloop")` **两层防御全都越过、uvloop 真的被导入成功**
  （修前实测 `IMPORTED (未被拦)`）。
  但 hook 并非没被调用：uvloop 的 `__init__.py` 自己 import 子模块，实测触发了
  `uvloop.includes` / `uvloop.loop` / `uvloop._noop` / `uvloop._version` 四个事件。
  修法：新增 `_is_uvloop_module(name)`（`name == "uvloop"` 或 `name.startswith("uvloop.")`，
  且 `type(name) is str`），`_audit_hook` 的 import 分支改用它。作者声称**承重方式没变**
  （仍是 audit `import` 事件这一层），模块 docstring 对「audit 承重、毒化不承重」的定性
  照旧。配套：5 条子模块契约门 + 4 条 lookalike 验伪锚（`uvloopx` 等不得误拦）+
  探针 `uvloop-importlib-reimport`。同一份实测脚本修后复跑从 `ESCAPED` 翻成 `BLOCKED`。
- **(f) L-2 / 参数化重复**：删掉 `LEGITIMATE_CONTAINER_URIS` 里的
  `"bolt://127.0.0.1:7692"`（**保留** `TestBlockedPortsContract::test_test_uri_on_container_port_is_fine`），
  理由是后者在那个类里承担局部验伪锚 —— 没有它，同类的「指向现网端口必须拒」会被
  「一律拒绝」的实现骗过；列表要覆盖的是 scheme/大小写/路径/query/IPv6 这些**变体**。
  `UNSUPPORTED_SCHEME_URIS` 的 ftp/http/https **保留不删**（删掉会让「这三种 scheme 都拒」
  失去用例 = 放宽），只加注释说明它们同分支。
- **(g) M-2 / L-1 只核不改**：M-2 的 docstring 已在上一卡改写（`模块 import 期` 在
  `live_port_guard.py:1082`）；L-1 的段头已改（`:1327`），模块 docstring 尾部
  `:127`「这段窗口无法在进程内闭合」的残留**本卡不动**，如实登记。
- **(h) 作者自己声明的局限**：见验收单「本卡未证明什么」，其中与你最相关的是 ——
  M-4 的结论只在**本机 CPython 3.14.4** 上实测；M-3 的探针只证明「这一种最小会话形态里
  预检跑到了」，不证明所有 pytest 入口形态。

## 三 请按重要性排序回答（每条给出结论 + 依据行号）

1. **`except Exception` 扩面后 `extract_port` 是否吞掉了本该 fail-closed 的情形**？
   有没有哪种输入原本会以异常形式暴露问题、现在变成静默返回 None 而**放宽**了判定？
   （注意后继链路：返回 None ⇒ `port not in BLOCKED_PORTS` ⇒ 但 `port_is_trustworthy`
   随后判不可信 ⇒ 仍走受拦分支。请独立确认这条链在**所有**返回 None 的路径上都成立。）
2. **M-4 的修法是否完整**：`_is_uvloop_module` 覆盖 `uvloop` 与 `uvloop.` 前缀，是否还有
   **未被拦下的输入**能让 uvloop 被加载？例如 `importlib.import_module("uvloop.loop")`
   直接导子模块、`importlib.util.spec_from_file_location` 按路径加载、
   `__import__("uvloop")`、`imp`/`zipimport` 之类的旁路。哪些会触发 `import` 事件、哪些不会？
   （只读判断即可，**不要真的跑**。）
3. **新哨兵断言是否仍能被「改常量」以外的手法满足**：`len == 28` / `ord(...[0]) == 0`
   这类判据，会不会被「比较值也从实现取」这种写法架空？现在的写法有没有从被测对象
   取期望值的地方？
4. **M-1 三条负例是否覆盖了 Codex 描述的全部形态**：把实现改成只判 `type(host) is str`
   之外，还有哪些改法能让这 3 条 + 旧 6 条全绿而分类仍然是错的？
5. **(d) 的行为探针是否真的经过了安装入口**（还是又一次直调）？临时目录 + `-p` 插件这条
   路，会不会因为 `pytest.ini` 的 rootdir / testpaths 而**仍然**加载了 `backend/tests/conftest.py`
   （那样翻转对照就被另一层喂饱了）？`m3-negctl` 的 B 跑 rc=0 是否足以证明 A 跑的 rc=3
   来自预检那一行？
6. **(f) L-2 删项是否让某条分支失去唯一用例**：删掉 `LEGITIMATE_CONTAINER_URIS[0]` 之后，
   `bolt://127.0.0.1:7692` 这条最朴素形态是否仍被**至少一条**用例覆盖？保留独立用例、
   删列表项这个取舍方向对不对？
7. **本卡新增的门里有没有恒真判据**（无论生产代码怎么改都不会红）？逐条给出「什么输入下
   它会红」。特别看 4 条 lookalike 验伪锚与 M-3 的那条负控探针。
8. **(e) 的结论是否只在本机 Python 版本成立**：`import` 审计事件由 `__import__` 抛出而
   `importlib.import_module` 不抛 —— 这是 CPython 的稳定行为还是版本相关？若版本相关，
   本卡的修法会不会在别的版本上变成误拦或漏拦？

## 四 输出格式

每条给：**级别**（BLOCKER / HIGH / MEDIUM / LOW）+ **文件:行** + **依据**（读到的代码/输出，
不要复述作者自述）+ **建议**。只读判定不了的写「未验证」，不要推测。
请在开头给一行总结：BLOCKER 数 / HIGH 数。

## 五 边界

- **只读**。不要修改任何文件，不要跑测试、探针或负控脚本。
- **不要连任何端口**（7691 / 7687 是开发机上的真库）。
- HIGH-2 / M4（账本发布顺序）/ M7（AST 契约收紧）/ M8（`repr` 出锁）已由上一卡
  CARD-W4-4b 处置，**不在本卡范围**；`backend/scripts/lifespan_isolation_negative_control.py`
  与四套 harness 归 U8；`backend/app/**` 不在本卡。
- 不需要评价 `_bmad-output/` 下的文档写法，只核对证据与代码是否一致。
