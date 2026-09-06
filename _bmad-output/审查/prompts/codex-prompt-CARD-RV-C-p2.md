# 独立复审请求 — CARD-RV-C prompt-2／2（W4 端口门的契约测试与探针，合并态 `e06009bc`）

## 一 读取面（写死；请只读这些对象，不要读工作区同名文件）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y8-w4-ast`

本 prompt 的读取面共约 715 行：

```
git show e06009bc:backend/tests/unit/test_live_port_guard_contract.py                    # 534 行（全量）
git diff 004e08cc e06009bc -- backend/scripts/lifespan_isolation_guard_probes.py         # 99 行 diff（+81 行新增）
git show 65cfd8ff:_bmad-output/审查/codex-review-CARD-W4-3a-r1.md                        # 82 行（更早一轮外审存档）
```

请**逐行读全量**，不要用摘要或作者自述代替原文。

被测对象本体 `backend/tests/support/live_port_guard.py` 在 prompt-1 里审；本 prompt 需要引用它时，请按 `git show e06009bc:backend/tests/support/live_port_guard.py` 读取，**不要**读工作区同名文件（它正被另一张并行卡修改）。

背景：`e06009bc` 已合入主干，但前两轮外审都没绑定到这个 commit（round-1 审未提交的工作区文件，round-2 钉旧行号并引用了已删除的函数）。本次是这份合并态的第一次外部审查。

## 二 作者自述（请独立核对，不要采信）

作者声称：

1. 契约测试用例**只用合成的审计事件与纯函数调用**，不发起任何真实网络连接。
2. `TestSelftestAddressClassification` 覆盖了两种伪装形态——tuple 子类覆写 `__getitem__`、以及 `str` 子类覆写 `__eq__`——并各配了一条「前提」断言，确认伪装本身确实成立。
3. 该类里的 `test_audit_hook_does_not_block_plain_safe_address` 是一条对照，用来防止「把钩子改成一律抛异常」也能让整组测试变绿。
4. 新增探针 `probe_allowed_test_ports_cannot_admit_live`（见 diff）用来证明：把现网端口放进测试白名单会被拒绝装门。

## 三 请按重要性回答（每条给 `文件:行` + 代码依据 + 结论）

1. **测试是否真的不碰网络**：逐条检查 534 行里有没有会触发真实 `socket.connect` 的用例。四条真实的 socket 入口（`socket.socket.connect` / `connect_ex` / `_socket` 层 / `socket.SocketType`）当中，哪几条被契约测试实际覆盖过，哪几条只在被测模块的注释里声称覆盖而测试里没有对应用例？
2. **`TestSelftestAddressClassification`（:407 起）的覆盖是否有缺口**：它是否包含「底层槽位是真实受拦地址、而表面看起来是哨兵」这一形态的反例？除了已有的两种伪装，还应该有哪些反例？
3. **一个具体问题**：该类的全部断言都通过符号引用 `guard._SELFTEST_HOST` 取哨兵值。如果有人把这个常量本身改成一个**普通的、可被解析的主机名**（例如 `"localhost"`），这 6 条断言是否仍然全部通过？如果仍然全绿，那么这组测试实际锁住的是什么、没锁住的是什么？请从「测试的期望值是否与被测实现读自同一处」这个角度作答。
4. **探针增量**（guard_probes diff）：`probe_allowed_test_ports_cannot_admit_live` 的判据是「装门被拒绝」。这个判据有没有可能被**别的原因**满足（即装门确实失败了，但失败原因不是探针想验的那一条）？如果有，探针应当怎样把失败原因与自己的预期绑定？
5. **round-1 存档**（82 行）里的 HIGH 是「早先那版把 tuple 子类一律按不可信处理，会误拦驱动的合法 7692 连接」。请核对：合并态的契约测试里，有没有一条用例把「驱动自己的地址类（tuple 子类、底层槽位是合法端口）必须被放行」这件事**钉成断言**？如果没有，那条 HIGH 的修复是否处于「改了实现但没留回归门」的状态？
6. **参数化与用例数**：`def test_` 的定义数与 pytest 实际收集数不同（前者 51，后者 84）。请检查参数化用例里有没有「参数不同但断言等价」的冗余，以及有没有哪个重要形态**只**出现在参数表里而没有独立断言。
7. 若某一项**只读判定不了**，请写「未验证」并说明需要什么证据。

## 四 输出格式

- 每条发现：级别（BLOCKER / HIGH / MEDIUM / LOW）+ `文件:行` + 代码依据 + 建议方向。
- 结尾给一句整体裁定（各级别计数）。
- 不确定的一律写「未验证」。

## 五 边界

- **只读**。不要修改任何文件，不要连接任何端口，不要运行 pytest。
- 以下事项**不在本卡范围**（已各自另立卡，正在并行处理），除非合并态 `e06009bc` 相对其父 `004e08cc` 的改动**让它们变得更糟**，否则不必重复提出：
  - 结算原子性（`STATE` 置位与取快照之间无锁）；
  - 「先启用豁免、后做 session URI 预检」的次序问题；
  - 负控脚本本身的静态检查条目（那是本车道下一张卡的面）；
  - runtime sha 脚本的环境变量问题。
- 被测模块本体的判据设计在 prompt-1 里审，本 prompt 聚焦「测试与探针能不能证明它声称的那些事」。
