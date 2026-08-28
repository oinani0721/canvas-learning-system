---
type: uat
title: "UAT · CARD-G8-6 14 天 dogfood 协议 v2（2026-08-28）"
date: 2026-08-28
status: awaiting_user
scope: "BATCH-2026-08-28-第五批 / CARD-G8-6 — 14 天 dogfood 协议 v2 文档（fix-forward 版，唯一 owner；卡状态 PARTIAL）"
worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood"
---

# UAT · CARD-G8-6 14 天 dogfood 协议 v2

> [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
> 这是纯协议文档卡（没有代码改动、没有浏览器新功能）。
> 你只需要过目 **四个关键点 + 一张待你锁版的表**。

## 📌 你需要过目的四个关键点

1. **修 bug 不再清零你的 14 天**：旧规则（计划书 §12.6）说"任何影响产品行为的修改都要从头再来 14 天"——对活跃开发中的系统这意味着窗口永远跑不完。新协议改为 **fix-forward**：修 bug 只登记变更 + 重跑受影响测试，天数照常累计；只有你本人可以裁定重开窗口。**但新功能不搭便车**：窗口中途合并的新能力不会自动算进已跑天数，怎么处置由你裁定。
2. **一个窗口只有一个协议**：三张卡（G8-6/G6-12/R-DOG）各造协议的隐患已按总账 v2 裁定收敛，本文档是唯一协议；"14 天无救火"变成窗口内的一个计数维度。裁定已作出，总账排程区的旧引用清理归主 session 簿记（文档头如实登记，不冒充已完成）。
3. **打卡防作弊、违规不能洗白**：每天的打卡靠 git 提交做时间戳（事后一次性补 14 天会在历史上显形）；数据丢失/串 vault/假成功一经确认**永久入账**，事后修好只能标"缺陷已修"，不能把违规改成没发生过。
4. **这张卡还没做完（诚实声明）**：协议文档是本批交付；配套的**自动打卡脚本**属于开窗前置——脚本没落地窗口不能启动，卡状态 = PARTIAL。
5. **两项没法机械证明的地方，协议不装**：①「完成一张板」——系统只记录"答了某题"，没有"完成整板"这个事件，所以选原义就得靠你手写板名背书；②「做了 5 次材料→白板」——同理只能手写登记。这两项若你选择保留原义，窗口结论会标成 `ACCEPTED_WITH_UNVERIFIED(N)` 而不是"完成"，不会把人工记录冒充机械证据。

## ✍️ 待你锁版的数值与语义（协议 §7，不锁版窗口不启动）

| 项 | 计划书原值（逐字） | 我的校准提案 | 你的裁定 |
|---|---|---|---|
| 窗口长度 | 连续 14 个日历日 | 14（不动） | ☐ |
| 补核宽限 | 无 | ≤2 次/窗口（漏勾次日中午前补核，依据=前日归档的复习清单副本） | ☐ |
| **"完成一张板"怎么算** | 有到期项时至少完成一张板 | 二选一：(a) 保原义"完成一张板"（机械上只能验到"当天答过题"+你登记板名）；(b) 改名"至少完成一题"（名实一致全机械） | ☐ |
| 学习 session | 至少 10 次 | ≥10（不动；人工登记口径） | ☐ |
| ingest→board | 5 次 | ≥5（不动；人工登记口径） | ☐ |
| 信息 skill | 3 次两类 | ≥3 次；类数=启动时冻结（当前 1 类 recap） | ☐ |
| **vault 切换怎么算** | 2 次 vault 激活切换 | 二选一：(a) "激活切换 2 次"（每次切换记一行变更登记）；(b) "窗口内用过 ≥2 个 vault"（推送清单+日志即可证明） | ☐ |
| **人工登记的两项算不算硬门** | L613 把它们列为最低活动量 | 二选一：(a) 算硬门——你接受"ingest→board / 信息 skill 次数由你手写登记"这一较弱口径；(b) 降为尽力项——不参与窗口完成判定，只在结案报告如实记录次数，等自动回执做出来再升级 | ☐ |
| 启动日期 | — | 你定（锁版+启动档案+脚本三件齐才开窗） | ☐ |

> 另有三项（故障 replay / 备份恢复 / visual export+import）因能力未上线**移出本窗口**（owner：G4-10 / G8-5 / G7-4·G7-5·G7-9·G7-10·G7-12），未装完成。

## ✅ 技术验证（Claude 已代跑）

| 项 | 结果 | 证据 |
|---|---|---|
| §6.2 判定命令 fixture 实测（C1/C2/C3/C4/C9，含修订版） | **正反例全过**：C1 失败日 exit 1 / 成功日 exit 0 / 无行 exit 1；C2 四例（今日+身份符 0、纯日期畸形 1、vault 身份错配 1、旧投影无 vault_id+Z 时区 0）；C3 当日 accepted 0 / 前日 1；C4 UTC→沪日换算正确、payload 内同名字符串不误计；C9 四例（全正常 0、Bark 失败走兜底 1、无 key+兜底失败 1、他库失败不误报 active 0） | scratchpad counter-test fixture（命令与协议 §6.2 逐字一致） |
| 协议引用代码实况逐条核对 | 通过（并据此改正两处硬伤） | 数据根实为主仓 `REPO`（`daily-review-push.sh:7`）而非 worktree → §0-A1 拆 `DATA_ROOT`/`CODE_WT`；log 实际取值为 `push:failed/skip-nokey`、`fallback:ok/fail/-`（`daily_review_run.py:216-249`）→ C9 重写；`_GENERATED_AT_RE`（`review_overview.py:41`）→ C2 采同一严格正则；wrapper 多库循环（`daily-review-wrapper.sh:30-36,52,91`）→ C8 语义改判 + 多库 preflight 门 |
| 上游裁定一致性（总账 v2 §三消三胞胎；R-DOG 三件套并入） | 通过 | 活动量清单 §7 表 B、计数器 §6.2、R-EVD 结案报告合同 §8 |
| L613 原值逐字引用 + 废止条款可追溯 | 通过 | §7 表 A/B「L613 原值（逐字）」列 + §3.1 显式废止（总账 v2 §五 SUPERSEDED 在案） |
| Codex 对抗审查 round-1（可执行性+判据机械性） | **FAIL**：5 BLOCKER + 6 HIGH + 5 MEDIUM + 2 LOW，全部核实属实 | `_bmad-output/审查/codex-review-CARD-G8-6.md` |
| round-1 整改 | 18 项全处置 → round-2 复核：11 RESOLVED / 6 PARTIAL / 1 STILL-OPEN | 协议全文重写 |
| Codex 复审 round-2 | **FAIL**：新增 4 BLOCKER + 4 HIGH + 4 MEDIUM（含 C9 匹配了生产从不输出的值、数据根指错、待裁绕过三零、degraded 只验字段不验恢复成功） | `_bmad-output/审查/codex-review-CARD-G8-6-round2.md` |
| round-2 整改 | 12 新增 + 7 遗留全处置：完成式补「14 日全日通过 / 零悬置裁定 / degraded 恢复成功 / 变更全闭合」四道门；C9 换真实取值；C2 加严格格式+vault 身份；A1 拆双根；A5/A6 命令修正；A7 改 IANA 一致才开窗；A11 冻结端口；多库 preflight 门；git 回执改诚实措辞；C6/C7 是否计硬门列为用户锁版项 | 协议 v2.2 |
| Codex 复审 round-3 | **BLOCKER 归零**：12 RESOLVED / 7 PARTIAL / 0 STILL-OPEN；新增 3 HIGH（preflight 漏 err.log 与单库场景、非 active 库不跑 C9 可漏记降级、结案合同仍写"五项"而完成门已七项） | `_bmad-output/审查/codex-review-CARD-G8-6-round3.md` |
| round-3 整改 | 3 HIGH + 2 MEDIUM/LOW 全闭合：每日对**每个** vault key 跑 C1+C9（fixture 实测 B 库 `push:failed fallback:fail` 被抓）；preflight 改无条件双日志源；结案合同改七项判定+接受清单；A3 冻结逐库 key；另主动加固 C2 入每日清单、未跟踪指纹改绑内容（fixture 验证内容变则指纹变）、判定 6 加"接受≠验证" | 协议 v2.3 |
| Codex 复审 round-4 | **BLOCKER 连续归零**：2 RESOLVED / 1 PARTIAL；新增 3 HIGH（err.log 缺失时假绿、A3 字面 key 与物理 key 因 symlink 分叉、A4 指纹依赖调用目录会产生假指纹）+ 对 7 项 PARTIAL 给出可文档闭合的具体建议 | `_bmad-output/审查/codex-review-CARD-G8-6-round4.md` |
| round-4 整改 | 3 HIGH + 5 项文档层加固：A3 改冻结 raw_name/REAL_VAULT/physical key 三元组；A4 改 subshell+pipefail；A7 改 fail-closed（时区不一致只能开 observation 窗口，不计 14 天）；引入变更行四态与窗口总状态二分；C2 进日通过式、身份错配按"串 vault"登记；git 回执标 `SELF_ATTESTED_GIT` | 协议 v2.4 |
| Codex 复审 round-5（最终） | **0 BLOCKER**；3 新 HIGH（游标竞态、不同真实库可碰撞同一 key、A4 另两条管道仍掩盖失败）+ 指出全局接受集漏算路径 | `_bmad-output/审查/codex-review-CARD-G8-6-round5.md` |
| round-5 整改（收官） | 全部闭合：err.log 游标改"先冻结终点 E 再读 [OFFSET,E)"并校验切片长度（防读写竞态永久跳字节）；A3 加 REAL_VAULT/key 唯一性门（防两个真实库共享 lock/state）；A4 整块统一 pipefail 逐行检查；**全局接受集改四类并集**（变更接受行 ∪ C2-null ∪ 一板(a) ∪ C6/C7(a)）堵死"全人工背书也标 VERIFIED_COMPLETE"；A5 加安装件↔repo 源↔launchd 三方等值绑定 | 协议 v2.5（终版） |
| 结构自检（脚本化） | 全绿 | §1 七门 / §3 八条 / §5.1 七步 / §5.2 五项日通过式 / 台账四区（打卡表 14 行×14 列表头一致）/ 零悬空章节引用 |

## 📄 交付物清单

- 协议本体：`_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md`（§0 启动档案 / §1 窗口与完成判定 / §2 能力冻结 / §3 fix-forward / §4 三零事件登记 / §5 每日清单与漏日 / §6 台账模板+计数器 / §7 待锁版表 / §8 残余与 R-EVD 合同）
- 卡状态：**PARTIAL** — 打卡脚本（开窗前置）与 C6/C7 机械回执归残余，逐项有承接与验收门（§8 表）。

## 📝 批注区

**User：**
