**BLOCKER 0 / HIGH 0 / MEDIUM 6 / LOW 4。**

审查绑定 **`85c1284bd300a354b828c3365a086b846693337f`**。本轮未发现阻断 D-15 的问题，但“整改全部到位”不成立。全程只读、未连接数据库或服务；结束时 HEAD、受版本控制文件均未变化。

1. **MEDIUM M-1：`declared_rows()` 修复了指定输入，但引入新的假红。**  
   [ledger_lint.py:209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:209) 只排除 fenced 代码块；追加合法的四空格缩进代码示例 `**本版条目数**: 15`，会被误算成第二处声明。另 `:184` 将正常数字后的英文句号 `21.` 一并拒绝。两种对照输入在 r5 均 `rc=0`，本版均**仅 L15 假红、rc=1**，缩进代码的渲染语义已用本机 Markdown 解析器交叉核实。指定 h1/h2/h3 已修；未复现本轮新增假绿。

2. **MEDIUM M-2：已登记的四种解析边界仍存在。**  
   [ledger_lint.py:182](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:182)、`:258–274`：独立复算确认，四空格缩进围栏后接新增表格、反引号数量不对称包围 HTML，仍是 **rc=0 的未被拦下的输入**；合法跨行 code span、围栏内部带语言后缀的反引号行仍引起 L13 假红。属于已登记残余，未据此重开 HIGH。

3. **MEDIUM M-3：每日选题核心改正，但新增限制尾句仍写错。**  
   [capability-ledger.md:71](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:71) 的“解析不到的板块不会出现在结果里，用户看不出差别”过宽：`daily_review_pick.py:873` 收集未归板节点，`:1108` 放入结果，`:1221` 在 Markdown 中逐名警告；`test_daily_review_pick.py:168` 也验证点名可见。内存对照输入复现了该输出。**消除此项必须修改台账正文。**

4. **MEDIUM M-4：验收单仍把未完成的文案整改写成已完成。**  
   [UAT:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/验收单/UAT-CARD-G1-3-2026-09-18.md:218) 称三处已改，实际 `:101` 末尾仍写“不同列数不会识别／只堵同构藏行”，与当前结构契约矛盾，`:89` 仍保留“会被当场抓住”的概括。此外，`:13` 仍写 L0–L13，`:66` 仍写核心 11 段，`:203` 仍称 r5“协议上限轮”，`:105` 将 r5 已实测的四种边界称为“仍未测”。**可仅改 `_bmad-output`。**

5. **MEDIUM M-5：L9 仍依赖调用方提供可信 trunk，登记属实。**  
   [ledger_lint.py:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:370)：以部署行为构造 21 个唯一 ID，核验 SHA=`7e1d6b53`、证据 SHA=`79134975`，同时传入 `--trunk=7e1d6b53`，正式 `main()` 得 **rc=0**；该 trunk 并非本轮 HEAD 的祖先。验收单 `:102` 已诚实登记。

6. **MEDIUM M-6：L12 的依赖交集与 tag 错配仍可放行，登记属实。**  
   [ledger_lint.py:555](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:555)、`:514`：索引删除行证据 SHA 换成只命中依赖的 `8f3ee155`，或部署行 tag 换成 `merged-squash/card/t5-bugs-CARD-T-SWITCHVAULT`，两组负控输入均 **rc=0**。验收单 `:103` 没有将这两条门未覆盖的路径说成已修。

7. **LOW L-1：§7 的 r6 绑定记录仍旧。**  
   [UAT:135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/验收单/UAT-CARD-G1-3-2026-09-18.md:135) 仍写 `096979bb`，而 `:5` 要求从该行取得最终绑定。实际本轮是 `85c1284b`；两者代码面与 lint 字节相同，属于记录失准，**不构成本轮实际失绑**。

8. **LOW L-2：两条台账入口仍指向常量。**  
   [capability-ledger.md:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:73) 的 `failure_counters.py:74` 是后缀常量；`:79` 的 `validate_release_manifest.py:63` 是指纹常量。对应执行函数分别在 `failed_writes_constants.py:192`、`validate_release_manifest.py:762`。E 级仍有其他证据支持。**消除此项必须修改台账正文。**

9. **LOW L-3：台账藏行证据指引已失效。**  
   [capability-ledger.md:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:31) 引用 `evidence-g13/negctl-13-*`，当前没有匹配文件；相关结果实际位于 `negctl-all-20260918T184540.txt`。可修改台账引用，或**仅在 `_bmad-output` 补回内容准确的归档入口**。

10. **LOW L-4：负控汇总未保存精确输入，部分原执行不可追溯。**  
    [negctl-all:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/negctl-all-20260918T184540.txt:6) 声称段 4 仅红 L1，但仅截成 14 行会同时红 L15，必须把自述也改成 14；`:12` 又把历史 12a/12b 合成一条。目录没有相应输入或生成脚本，因此**原段 4 的构造、最新段 12 是否覆盖两种路径，均未核实**，不能据此认定原执行归因错误。可仅在 `_bmad-output` 补证据。

指定整改中，下列部分核验通过：

- **两侧切分统一有效**：能力名含 `\|` 的 h4 得 `rc=0`；另加第 12 格的负控输入仅 L14 红，新增宽度检查确实生效。
- **缺 `fsrs_due` 被当 New 卡选入**：`daily_review_pick.py:538、566、441` 与具名单测一致。
- **`agent_service` 无界旁路描述准确**：`failed_writes_constants.py:214–230` 与 `agent_service.py:129–131` 相符；回灌窗口直接追加也确在 `:243–254`。
- **LOW-2 两个新锚已定位到正确函数**：`g32b:2454` 是 `_arm_mutation`，真正写盘在 `:2463`；`live_port_guard:773` 是 `_audit_hook` 的说明，实际判断从 `:782` 开始。
- **哈希与部署超时限定已修**：`15935c81`、`096979bb`、`85c1284b` 的台账及 lint 哈希一致；运维手跑与测试 timeout 已区分。
- **无五轮上限的更正有据**：卡文 (n) 确实只对“有代码改动的卡”规定上限；验收单更正段实质正确，遗留标题见 M-4。

抽查数量存在客观限制：前四份正式报告已覆盖 **20 个不同 ID**，r1 无正式抽查报告，全表只有 21 行。因此本轮只能完成 **1 行全新＋4 行明确重抽**，不能声称又抽到五条不重复行。

| 类型／台账行 | 入口与证据正文反查 |
|---|---|
| **全新 CAP-REL-MANIFEST-17** | `validate_release_manifest.py:762` 为校验入口；`test_validate_release_manifest.py:1174` 真用 subprocess 跑 CLI；最终存档 `revd-suite-final-20260918T184717.txt:54` 为 168 passed。**E2 有据，限制准确，入口锚见 L-2。** |
| 重抽 CAP-DAILY-PICK-09 | `daily_review_pick.py:459` 为扫描入口；`evidence-g67r/four-LA-r4fix-20260909T140516.txt:59` 记 324 passed。**E1 有据，限制尾句见 M-3。** |
| 重抽 CAP-DEADLETTER-11 | `test_dead_letter_bounded_t6c.py:244` 起真调写者并检查文件与轮转。**E1 有据，旁路限制准确，入口锚见 L-2。** |
| 重抽 CAP-W4-GUARD-19 | `live_port_guard.py:772` 为承重函数；`evidence-w4final/contract-close-20260914T200632.txt:54` 记 151 passed，源码支持 advisory 与双字段复核限制。**E1 有据。** |
| 重抽 CAP-MUT-GATES-20 | `g32b_mutation_gates.py:2454` 真执行变异；`evidence-g32b/g32b-full-run.txt:186` 起包含恢复及整体 FAIL。**E2 按本表口径有据，不能读成全部门绿。** |

全部负控按描述重构后，调用正式 `main()` 的结果如下；保留真实 Git、路径及 manifest 检查：

| 输入组 | 复算结果 |
|---|---|
| 核心 1/2/3/5/6/8/9/10/12a/12b | 分别仅红 L4/L3/L3/L11/L12/L9/L3/L4/L3/L3 |
| 核心 4 | 截为 14 行且自述同步为 14，才仅红 L1 |
| 藏行 f1 | L14＋L15 |
| 藏行 f2–f5 | 仅 L15 |
| 藏行 f6 | L13＋L15 |
| 自述 h1–h3 | 仅 L15 |
| 对照 g1–g4、h4 | 全部 rc=0 |

除 L-4 的原输入留存问题外，**未发现重构负控输入红在其他原因上**。机器 `ARCHIVE-INDEX` 的文件名单与实际目录相符；14 条“未证明什么”总体诚实，但第 10、14 条仍有 M-4 所列旧文。历史测试全过程、flaky 成因及历史连接活动，本轮均未核实。

**需要改台账才能消除的是 M-3、L-2；其余发现可在 `_bmad-output` 修正或登记。**


