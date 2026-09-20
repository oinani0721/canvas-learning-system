你是本仓的独立审查者。只读，不改任何文件，不连任何数据库或服务。

**先看这条**：本轮**不要向我提问**。完成任务所需的任何文件都可以直接读——源码、测试、验收单、存档、协议与计划书的任意段落。若某项确实无法核实，就在报告里标注「未核实」并说明原因，不要停下来等我批准。

## ① 背景

仓库根: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs
卡: CARD-G1-3 [BATCH-2026-09-18-第十五批]。**审查绑定: bba95195**（基线 9c4e7e82；三个 commit：35b919fe、ed5b3a85、bba95195）。

上一轮（r2，绑 ed5b3a85）你给出 BLOCKER 0 / HIGH 2 / MEDIUM 7 / LOW 2。本轮请核对整改。

起点：`git --no-pager diff --no-color ed5b3a85 bba95195`（本轮改动面）、`docs/release-evidence/capability-ledger.md` 全文、`_bmad-output/审查/evidence-g13/` 全目录（`ledger_lint.py`、`l3_semantics_control.py`、`protocol-ledger-row.patch`、全部 `*.txt` 存档）。

## ② 本轮整改清单（请逐条核对是否到位，不要默认它对）

| 你的发现 | 整改 | 我方给出的负控 |
|---|---|---|
| HIGH-1 第二张表不受检查 | 新增 **L13**：与能力表同列数的表格行不得出现在能力表之外；判据用列数不用 id 前缀 | 段⑦ `negctl-7-L13-*.txt` |
| HIGH-2 核验 SHA 未绑主干 | L9 增加「核验 SHA 必须是 `--trunk` 的祖先」，基准改由外部传入 | 段⑧ `negctl-8-L9-*.txt`（用的正是你给的 7e1d6b53 / 79134975） |
| M-3 overflow 与 .synced. 删除规则混淆 | 台账改写：overflow 按数量删最老（`failure_counters.py:153`），30 天管的是 `.synced.`（`fallback_sync_service.py:931`）；「丢的是最新」改为只陈述原文证明的那一种情形 | — |
| M-4 对照门覆盖范围写宽 | 台账回填：该门只比函数体与类、不含模块常量，并引 `UAT-CARD-G6-9c` 第 ⑱ 条的实测 | — |
| M-5 索引删除行测试不对应 | 换成 `test_wave5_stageb_continued_vault_id_injection.py` 与 `test_lancedb_cross_vault_drop_g29f1.py` | — |
| M-6 L3 路径发现靠整串正则 | 改 `find_manifest_refs`：按 token 归一化筛选，不依赖路径中段写法 | 段⑨ `negctl-9-L3-*.txt` |
| M-8 L4 只报合计 | 改逐行报本行对象数，并要求证据列至少有一个文件路径 | 段⑩ `negctl-10-L4-*.txt` |
| M-9 台账引用不存在的验收单；3 条遗漏 | 引用改为具体路径（验收单随下一 commit 落盘）；3 条遗漏已实测核实并补入验收单遗漏清单 | — |
| M-7 L12 挡不住 tag 错配 / 降级面算入口 | **登记为已知限制**，未修；另附 `l12-known-weakness-probe-*.txt` 自证「顺带碰过入口文件的别卡 squash 能过 L12」 | — |
| L-10 对照实验结论超范围 | 措辞收窄，明说它没有调用正式 L3 | — |
| L-11 与 P8 patch「不冲突」无证据 | patch 注释改为「未核实」，请主 session 实测后再定顺序 | — |

## ③ 请按重要性排序回答

**⓪ 整改是否真的堵住了你指出的路径？** 特别是 L13 与 L9：有没有新的未被拦下的输入？例如列数不同的藏行写法、`--trunk` 传入一个本身就在分支上的引用、L13 对 HTML 表格或代码块内表格行的处理。

① 新增的 L9/L13 有没有**引入新的假绿或假红**？L13 扫全文按列数判定，会不会误伤台账里合法的其它表格（说明段里的 E 级规则表是 2 列、承重门表是 3 列）？

② M-3 / M-4 / M-5 三处台账改写是否**准确**？请直接读 `failure_counters.py:153` 一带、`test_g6_9c_single_tz_source.py`、以及新引的两份索引测试，核对改写后的描述与源码一致。

③ 再抽 5 行（**与 r2 不同的 5 行**）做反查：入口 `file:line` 是否成立、证据正文是否真支撑该行的 E 级与限制。

④ 十段负控里，有没有哪一段其实红在别的原因上？`negctl-origin-sha-*.txt` 能否支持「原件全程未被触碰」这个说法（注意它只比较前后两个时刻）？

⑤ 台账现在还有没有 §12.7 禁止的声明、或与源码不符的描述？

## ④ 输出格式

BLOCKER / HIGH / MEDIUM / LOW 分级，每条给 `file:line` + 一句话说明如何观察到。措辞请用「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」。若本轮 BLOCKER 与 HIGH 均为 0，请明确写出这一结论。

## ⑤ 边界

只读。不评 CARD-R-RC、CARD-R-SLO、G1-6 三张卡的面；不评 G8-9 底账内容本身的正误；不要求本卡去修台账之外的文件。
