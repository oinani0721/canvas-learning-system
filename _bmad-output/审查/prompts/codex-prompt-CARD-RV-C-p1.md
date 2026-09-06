# 独立复审请求 — CARD-RV-C prompt-1／2（W4 端口门本体，合并态 `e06009bc` 首次外审）

## 一 读取面（写死；请只读这些对象，不要读工作区同名文件）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y8-w4-ast`

本 prompt 的读取面是**两个 git 对象**，共约 1204 行：

```
git show e06009bc:backend/tests/support/live_port_guard.py          # 1093 行（全量，非 diff）
git show 65cfd8ff:_bmad-output/审查/codex-review-CARD-W4-3a-r2.md   # 111 行（上一轮外审存档）
```

请**逐行读全量**，不要用摘要或作者自述代替原文。

⚠️ 工作区里的 `backend/tests/support/live_port_guard.py` 正在被另一张并行卡修改，与本次审查对象**不是同一份**。一律用上面的 `git show`。

背景：`e06009bc` = `fix(w4-guard): NEO4J_TEST_URI 改正面白名单 + driver canonical 契约`，其父 `004e08cc`。该 commit 已合入主干 `03ac8bf8`。前两轮外审都**没有绑定到这个 commit**：round-1 审的是未提交的工作区文件，round-2 钉的是旧行号并引用了此后已被删除的函数。所以这是这份合并态代码的**第一次**外部审查。

这道门的作用：让 pytest 进程连不上现网 Neo4j（7691 / 7687）。承重层是 CPython 的 `socket.connect` 审计钩子。

## 二 作者自述（请独立核对，不要采信）

作者声称：

1. `_is_selftest_address`（:448-476）已重写，解决了 round-2 存档 HIGH-1 所述的问题——「真实地址被分类成自证地址，于是拦截不进账本」。新实现用三道判据：`type(address) is tuple`（:468）、`tuple.__getitem__` 读底层槽位（:473）、`type(host) is str`（:476）。**round-2 那一轮没有审过这份新实现。**
2. `extract_port`（:340-386）与 `port_is_trustworthy`（:388-420）对 tuple **子类**地址改为「读底层槽位后放行」，而不是早先那版的「子类一律按不可信处理」。理由写在 :361-372：驱动自己的地址类就是 tuple 子类，早先那版会把合法的 7692 测试容器连接一并拦掉。
3. `install()`（:581-616）的次序是 :602 `poison_uvloop()` → :603-604 条件调用 `assert_neo4j_target_blocked()` → :605 装审计钩子 → :606 注册最终总账 → :610-615 装 belt。
4. `canonical_target_ports`（:730 起）在函数体内延迟 import neo4j；:764-768 论证了这样做的合法性。
5. :980 的段落标题与 :986 `register_final_accounting` 的 docstring 对「最终总账何时执行」的表述不同。

## 三 请按重要性回答（每条给 `文件:行` + 代码依据 + 结论）

1. **`_is_selftest_address` 的新实现是否闭合**：还有没有别的输入能走进 :497-498 那条「抛 `_SelfTestBlocked`、不调 `STATE.record()`」的免记账分支？请把该分支的可达输入枚举完整（含各 socket 协议族、以及直接 `sys.audit(...)` 合成事件），并说明每种情况下有没有真实连接随之建立。
2. **`extract_port` / `port_is_trustworthy` 对 tuple 子类的处理是否安全**：请分别回答两头——(a) 会不会放行一个实际指向受拦端口的地址；(b) 会不会误拦驱动的合法地址。特别请判定：端口值是一个**有状态的 `__index__` 对象**（第一次求值给受拦端口、第二次给安全端口）时，这两个函数当前是否仍按不可信处理。
3. **:493 那条判据的完备性**：`if port in BLOCKED_PORTS or not port_is_trustworthy(address)`。请检查有没有一类地址能让**两个子句同时为假**从而被放行，尤其注意 `port_is_trustworthy` 对非 tuple 输入返回 `True`（:413）这条分支。
4. **装门时机**：:603-604 的预检早于 :605 装钩子。这个窗口内会发生什么？窗口在什么条件下存在、什么条件下不存在？窗口期间若有网络动作，门会不会留下记录？
5. **`canonical_target_ports` 的延迟 import 论证（:764-768）**是否与本文件里该函数的**全部**调用点一致。
6. **:980 段落标题 vs :988-996 docstring**：哪一句与 `atexit` 的实际执行次序一致？采信另一句的人会写出什么样的门？
7. **豁免路径**：`STATE.record`（:234-258）在 `exempt` 为真时返回 `False`，于是 :512-513 不抛异常、连接放行并只计入 advisory。请判断这条路径的作用域控制（`_GEN_CV` / `_OWNER_CV` / :240-244 的 stale 处理）是否足以保证「豁免只在打了对应 marker 的用例内生效」。
8. 若你认为某一项**只读判定不了**，请写「未验证」并说明需要什么证据，不要给推测结论。

## 四 输出格式

- 每条发现：级别（BLOCKER / HIGH / MEDIUM / LOW）+ `文件:行` + 代码依据 + 建议方向。
- 结尾给一句整体裁定（各级别计数）。
- 不确定的一律写「未验证」。

## 五 边界

- **只读**。不要修改任何文件，不要连接任何端口，不要运行 pytest。
- 以下事项**不在本卡范围**（已各自另立卡，正在并行处理），除非合并态 `e06009bc` 相对其父 `004e08cc` 的改动**让它们变得更糟**，否则不必重复提出：
  - 结算原子性（`STATE` 置位与取快照之间无锁）；
  - 「先启用豁免、后做 session URI 预检」的次序问题；
  - :603-604 预检早于装钩子这一条的**修复**（本 prompt 第 4 问只要**判定**，不要给实施方案之外的整改承诺）；
  - 负控脚本的静态检查条目、以及 runtime sha 脚本的环境变量问题。
- 契约测试文件与探针脚本在 prompt-2 里审，本 prompt 不必涉及。
