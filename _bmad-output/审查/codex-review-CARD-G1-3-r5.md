**BLOCKER 0 / HIGH 0 / MEDIUM 7 / LOW 3。**

审查绑定 `9764fdecf19ad567e41cd0c3a9fa17caafbe5dad`，提交链与指定基线一致。**原 r4 HIGH 的具体路径已堵住；本轮不触发“BLOCKER/HIGH 非零则停卡”的条件，但不能裁定全部整改完成。**

全程只读，未连接数据库或服务。负控输入在内存中构造，调用正式 `main()`，保留真实 Git、路径及证据检查；结束时 HEAD 与受版本控制文件未变。

**⓪ HIGH 与残余边界**

独立复现结果：

| 输入 | 实际结果 |
|---|---|
| 原稿 | `rows=21`、`rc=0` |
| 后六行改 E5，仅删除行首竖线 | L14 列出六行差集，L15 同时失败，`rc=1` |
| 上述输入再把自述改为 15 | L14 仍失败，`rc=1` |
| 后六行改成列表，自述保持 21 | 仅 L15 失败，`rc=1` |
| 列表输入同时把自述改为 15 | `rows=15`、`rc=0` |

[台账:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:31) 和验收单 `:101` 前半已明确限定保证范围，并承认最后一种未被拦下的输入。因此不据此重开 HIGH。不过验收单仍有过强概括，见 M-5。

**MEDIUM**

1. **M-1：L15 未可靠定位自述声明，存在新的假红与假绿。**  
   [ledger_lint.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:184)、`:585` 对全文取第一次正则命中，不排除代码块、不检查唯一性，也没有完整数字边界。

   保持正文自述 **21** 不变，在文首增加内容为 `**本版条目数**: 15` 的 fenced 代码块：完整台账仅 L15 假红；后六行改成列表后，反而得到 **L15 PASS、整体 rc=0**。此外，`21.5` 被读作 21，追加第二个冲突声明也不报错。**自述不仅能直接改小，还能被前置示例抢占。**

2. **M-2：原四种对照输入已修好，但 Markdown 解析仍有双向错误。**  
   [ledger_lint.py:166](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:166)、`:182`、`:227`：

   | 扩展输入 | 观察 |
   |---|---|
   | 能力名改为合法的 `Canvas 边理由 \| 向量化写入` | 判据解析器错分成 12 格，七条判据假红；L13/L14/L15 却全通过 |
   | 四空格缩进的三反引号行，空行后接合法新增表格 | 扫描器误开围栏，新增表格未被识别，`rc=0` |
   | HTML 前一个反引号、后两个反引号 | 被误剥为行内代码，`HTML表标签=0`、`rc=0` |
   | 合法跨行 code span 中包含 `<table>` | 仅 L13 假红 |
   | 合法围栏内部出现带 `text` 后缀的三反引号行 | 被误当闭合围栏，代码示例表引起假红 |

   上述版式另经本机 Markdown 渲染器交叉核实。**L14 只比较行号，不比较单元格解释是否一致。**

3. **M-3：每日选题行把实际接纳的节点写成被跳过。**  
   [capability-ledger.md:71](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:71) 写“FSRS 字段缺失的节点被静默跳过”；实际 `daily_review_pick.py:538、557–566` 将缺少 `fsrs_due` 的节点加入结果并置 `due_now=True`，`:441–442` 归为新卡，具名单测 `test_daily_review_pick.py:162–165` 也明确断言它被选入。E1 有据，限制描述写反。

4. **M-4：有界轮转行遗漏已存在的无界写入路径。**  
   [capability-ledger.md:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:73) 称“防无限增长”，但未登记 `failed_writes_constants.py:214–220` 明说的 `agent_service` 旁路不核上限、越限可无限持续；实际追加点在 `agent_service.py:130–131`。另 `failed_writes_constants.py:243–254` 在回灌窗口直接追加并返回，所引验收单 `:203–205` 已承认锁永久占用可无限期关闭上限。这些是应写进台账的**门未覆盖的路径**，不要求本卡修产品代码。

5. **M-5：验收单内部矛盾仍在，“逐条已修”不成立。**  
   [UAT:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/验收单/UAT-CARD-G1-3-2026-09-18.md:193) 声称已修，实际：
   - `:5` 要求从 §7 最后一行核最终绑定，`:132` 仍是“r3／本卡最终 SHA／待审”。
   - `:101` 末尾仍称不同列数无法识别、“只堵同构藏行”，与当前结构契约矛盾。
   - `:105` 仍把转义竖线、表中 HTML 一概列为“未测”，与 `:67–68` 的实测记录矛盾。
   - `:89` 仍称没根据的高等级“会被当场抓住”，与 `:101` 已承认的范围外路径矛盾。

6. **M-6：L9 仍依赖调用方提供可信 trunk；登记属实，未修。**  
   [ledger_lint.py:339](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:339) 默认 `HEAD`；独立负控以部署行为构造唯一 id，核验 SHA=`7e1d6b53`、证据 SHA=`79134975`，同时传入 `--trunk=7e1d6b53`，整体 **rc=0**。验收单 `:102` 如实登记了这条边界。

7. **M-7：L12 依赖交集与 tag 错配仍可放行；登记属实，未修。**  
   [ledger_lint.py:519](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:519)、`:477`：分别将索引删除行证据 SHA 换成仅命中依赖的 `8f3ee155`，以及将部署行 tag 换成 `merged-squash/card/t5-bugs-CARD-T-SWITCHVAULT`，两组负控均 **rc=0**。验收单 `:103` 没有将其说成已修。

**LOW**

1. **绑定稿哈希记录仍属于上一轮。**  
   [UAT:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/验收单/UAT-CARD-G1-3-2026-09-18.md:104) 称“本轮已补绑定稿 sha”，但对应存档 `ledger-sha-at-commit-20260918T181053.txt:5` 明绑 `9198c938`。当前台账／lint 哈希分别为 `b56e6e23…8904f22`／`4b783907…cf126d7`，与该历史记录不同；历史记录正确，不能充当本轮字节绑定。

2. **部分入口、具名代码证据没有指到执行位置。**  
   [capability-ledger.md:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:82) 所引变异脚本 `:545` 是启动时恢复残留，实际变异写入在 `:2454–2463`；另台账 `:73` 的入口 `failure_counters.py:74` 是常量，`:81` 的 `live_port_guard.py:1072` 是端口解析辅助函数，真正拦截在 `:773`。相关 E 级仍有其他证据支持。

3. **部署超时改写尾句缺少“运维手跑时”的限定。**  
   [capability-ledger.md:64](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:64) 称 build 外步骤不会被“两层”拦下；实际测试层 `test_deploy_vault_sh.py:90–96` 对整次脚本调用设置 timeout，覆盖测试执行中的非 build 等待。真实 build 上限、运维六步无统一内置上限这两项整改成立。

**三处指定改写的核验结果**

- **Skill lint：PASS。** `test_skill_portability_lint.py:234` 确实阻断漂移；正文及越界层分别遍历自己的 baseline，新限制准确。
- **部署超时：主要整改成立，余上述 LOW。** `deploy-vault.sh:932–944` 确有 alarm 与进程组终止逻辑。
- **内部鉴权链接：PASS。** 新存档记录三份内部鉴权测试，`auth-behavior-tests-20260916T194754.txt:6–9、30` 为 **30 passed**，已消除原链接错配。

**新增五行反查**

这五行不重复 r2–r4 的十五行抽查；r1 无正式抽查报告。

| 行 | 入口与证据正文 | 裁定 |
|---|---|---|
| CAP-LANCE-ISO-03 | `lancedb_client.py:1325` 为删除入口；具名单测真实使用 tmp_path LanceDB，存档记录 35 passed | **PASS，E2 有据** |
| CAP-DAILY-PICK-09 | `daily_review_pick.py:459` 为扫描入口；存档记录 324 passed | **PARTIAL，E1 有据，限制写反** |
| CAP-DEADLETTER-11 | 具名单测真实调用写者并核活动文件、归档 | **PARTIAL，E1 有据，遗漏无界路径** |
| CAP-W4-GUARD-19 | 源码支持 advisory 与双字段复核；存档记录 151 passed | **E1 有据，入口定位需收紧** |
| CAP-MUT-GATES-20 | 存档含真实变异与恢复，明确记录 134 KILLED／4 ANCHOR-ERROR、整体 FAIL | **E2 按本表口径有据，不能读成全量门绿** |

存档索引名单与实际目录一致，原 14 个失效文件名问题已解决；`undo_journal` 已移出“已合”清单并标未核实。验收单 14 条限制中的 trunk、依赖交集、缺少真树 E3 正例、测试未绑定最终树等说明基本诚实，但第 10、13、14 条仍有上述矛盾或过时内容。历史运行的全过程、flaky 归因及最新产品运行结果，本轮未重跑，均为**未核实**。
