# 独立复核 round-2：CARD-W4-7（W4 测试隔离门 — RV-C 遗留六条）

## 一 背景与最小读取面

被审对象是一个 **pytest 测试进程内的隔离门**（监听 CPython `socket.connect` 审计事件，
阻止测试进程连上 7691/7687，退出前做最终结算）。

**这是 round-2。** round-1 给出 **BLOCKER 0 / HIGH 2**，两条 HIGH 作者均已整改，
另处置了 1 条 MEDIUM（证据跑器的条件性假通过）与若干措辞收窄。本轮请**独立核对整改**，
并继续审视是否引入了新的问题。

**请只读下面这几处**（工作目录 = 本仓库根）：

1. **round-1 之后的增量**（整改面）：
   `git diff d172e7e4 <审SHA> -- backend/tests/support/live_port_guard.py backend/tests/unit/test_live_port_guard_contract.py`
2. **本卡完整改动面**（如需回看全貌）：
   `git diff de6ea625 <审SHA> -- backend/tests/support/live_port_guard.py backend/tests/unit/test_live_port_guard_contract.py backend/scripts/lifespan_isolation_guard_probes.py`
3. `backend/tests/support/live_port_guard.py` 的两处整改点：
   - `extract_port` :519（整改点 `:563` 的 `except BaseException`），
   - `_is_uvloop_module` :692（整改点 `:732-735`）；
4. `backend/tests/unit/test_live_port_guard_contract.py` 新增的四条门：
   `test_index_raising_baseexception_is_also_fail_closed` :101、
   `test_selftest_lookalike_without_the_nul_is_not_selftest` :600、
   `test_str_subclass_module_name_is_still_blocked` :712、
   `test_lying_str_subclass_is_judged_by_its_real_value` :735；
5. 整改负控与证据（`_bmad-output/审查/evidence-w47/`）：
   `r1-high-negctl.sh` + `r1-high-negctl-r1-high{1,2}-after2-*.txt`、
   `m4-importlib-probe.py`（已收紧的证据跑器）+ `m4-importlib-after2-*.txt`、
   `negctl_patch_w47.py`（新增 `r1-high1` / `r1-high2` 两个修前形态）。

## 二 作者对 round-1 两条 HIGH 的整改自述（请独立核对）

- **HIGH-1（`extract_port` 仍漏 `BaseException`）**：`:563` 由 `except Exception` 改为
  `except BaseException`，理由写进注释：`__index__` 是调用方给的任意用户代码，抛
  `SystemExit` / `KeyboardInterrupt` / 自定义 `BaseException` 时仍会越过 `STATE.record()`；
  与 U7-B 立的 `_safe_repr` 口径统一为「记账之前执行的用户代码一律 fail-closed」。
  代价（微秒窗口内 Ctrl-C 被吞一次）已在注释里写明。
  新增契约门 `:101`（`SystemExit` / `KeyboardInterrupt` / 自定义 `BaseException` 三参数）。
  负控 `r1-high1`：把 `:563` 退回 `except Exception`，该门 FAILED 且正文命中
  `__index__ 抛 BaseException`。
- **HIGH-2（`type(name) is not str → False` 是判定回退）**：作者接受这条 ——
  第一版本意是「不信任可重载的比较方法」，实际效果**比旧实现更宽**（值为 `"uvloop"` 的
  普通 `str` 子类，旧的 `args[0] == "uvloop"` 拦得住，那一版放行）。
  改法：`isinstance(name, str)` 后用**未绑定**的 `str.__eq__` / `str.startswith` 读真实值
  （与本文件处理 tuple 子类时用 `tuple.__len__` / `tuple.__getitem__` 同一惯用法），
  而不是把整类输入放掉。新增两条门：`:712`（普通 `str` 子类，值为 `uvloop` / `uvloop.loop`，
  必须拦）与 `:735`（重载了 `__eq__`/`startswith` 的说谎子类，两个方向：真值是 uvloop 但
  谎称不是 ⇒ 仍拦；真值是 json 但谎称是 ⇒ 不误拦）。
  负控 `r1-high2`：把判据退回 `type(name) is not str → False`，`:712` 两个参数均 FAILED
  且正文 `DID NOT RAISE`。
- **MEDIUM（问题 7，证据跑器的条件性假通过）**：`m4-importlib-probe.py` 原来遇到缺裁定行
  只存 `None` 继续、最终只看 `escaped` 是否为空、子进程 rc 打印却不参与判定。现改为三条硬
  前提（缺裁定行 / rc 非 0 / 「被拦下」不是**本门**拒因 ⇒ 一律 `INCOMPLETE`/`INCONCLUSIVE`
  并返回非 0）。
- **MEDIUM（问题 8，事件来源表述过宽）**：`_is_uvloop_module` docstring 已加一段明说
  本函数**不**声称「只有 `__import__` 才发事件」，且「每个 Python/uvloop/loader 组合都必然
  产生一个能命中的事件」**未证明**，实测只覆盖本机 CPython 3.14.4 的四种形态。
- **证据补齐 + 一处自我更正**：round-1 指出「四个子模块事件」在获准证据里未验证。作者给
  `m4-importlib-probe.py` 加了旁观 audit hook（**装在门之前**，否则门一抛就记不到，第一版
  实测确实是空列表）。实测结果**更正了作者原先的说法**：装门后
  `importlib__poison-removed` 只看到**一条** `uvloop.includes`（门在第一条上就抛了）；
  那四条是**不装门**时的完整序列。两处 docstring 已按此更正。
- **LOW（问题 3 / 4）**：哨兵末三项已加注为「说明性、不算三份独立检出能力」；
  按 round-1 建议补了「去掉 NUL 的近似哨兵」负例 `:600`（杀后缀匹配型错误实现）。

## 三 请按重要性排序回答（每条给出结论 + 依据行号）

1. **HIGH-1 的整改是否闭合**：`except BaseException` 之后，`extract_port` 还有没有别的
   路径能让异常逸出并越过记账？上半段读槽位那个 `except Exception`（`:559`）要不要也改？
   （请判断：`tuple.__len__` / `tuple.__getitem__` 在 tuple 子类上会不会执行用户代码。）
2. **HIGH-2 的整改是否闭合**：`str.__eq__(name, "uvloop") is True` 与
   `str.startswith(name, "uvloop.")` 这两个未绑定调用，能不能被别的输入形态骗过？
   例如 `str` 的其他子类、实现了 `__class__` 伪装的对象、`UserString`、
   `bytes`/`bytearray` 名称、或 `isinstance` 被 `__instancecheck__` 影响的类型。
   `str.__eq__` 返回 `NotImplemented` 的情形在这里可能出现吗（`is True` 是否必要且充分）？
3. **整改有没有引入新的误拦**：`isinstance(name, str)` 比原来的 `type(...) is str` 宽，
   加上未绑定 `startswith`，会不会把某个**合法**模块名判成 uvloop？
   四条 lookalike 验伪锚（`uvloopx` / `uvloop_shim` / `myuvloop` / `uv`）够不够？
4. **新增的四条门有没有恒真项**：逐条给出「什么输入下它会红」。特别看 `:735` 那条说谎子类
   用例 —— 它的两个方向是否都真的绑定到了「按真实值判」这个性质。
5. **证据跑器的收紧是否彻底**：`m4-importlib-probe.py` 现在还有没有能返回 0 却其实没验到
   的路径？三条硬前提（missing / bad_rc / other）覆盖完整吗？
6. **作者的自我更正是否准确**：「装门后只见 `uvloop.includes` 一条、四条是不装门时的完整
   序列」——这个说法与你读到的证据是否一致？两处 docstring 的更正措辞还有没有过宽的地方？
7. **round-1 其余 MEDIUM/LOW 的处置是否恰当**（问题 8 的表述收窄、问题 3 的哨兵末三项加注、
   问题 4 的近似哨兵负例）？有没有哪条被「加了注释就当处置了」而实际仍是缺口？

## 四 输出格式

每条给：**级别**（BLOCKER / HIGH / MEDIUM / LOW）+ **文件:行** + **依据**（读到的代码/输出，
不要复述作者自述）+ **建议**。只读判定不了的写「未验证」，不要推测。
请在开头给一行总结：BLOCKER 数 / HIGH 数。

## 五 边界

- **只读**。不要修改任何文件，不要跑测试、探针或负控脚本。
- **不要连任何端口**（7691 / 7687 是开发机上的真库）。
- HIGH-2（部分安装态结算）/ M4（账本发布顺序）/ M7（AST 契约收紧）/ M8（`repr` 出锁）
  已由上一卡 CARD-W4-4b 处置，**不在本卡范围**；
  `backend/scripts/lifespan_isolation_negative_control.py` 与四套 harness 归 U8；
  `backend/app/**` 不在本卡。
- 不需要评价 `_bmad-output/` 下的文档写法，只核对证据与代码是否一致。
