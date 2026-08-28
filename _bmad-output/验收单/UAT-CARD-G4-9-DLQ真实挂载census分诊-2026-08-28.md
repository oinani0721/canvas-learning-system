---
type: uat
title: "UAT · CARD-G4-9 DLQ 真实挂载 census 分诊（2026-08-28）"
date: 2026-08-28
status: awaiting_user
scope: "BATCH-2026-08-28-第五批 / CARD-G4-9 — live DLQ 92 条只读 census：分类/SHA 对账/可恢复性三态/挂载真相，产出 G4-10 交接台账"
worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s5-census"
---

# UAT · CARD-G4-9 DLQ 真实挂载 census 分诊

> [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查：
> 线上 Graphiti 写入失败后落进死信文件的 92 条记录，逐条查清"是什么死的、还能不能救、去哪里救"，
> 给后续的 G4-10（真正做恢复的卡）留一份带稳定编号的台账。卡面如实标注：离日常使用价值远，属恢复能力地基。

## 📌 你需要过目的三个结论

1. **92 条死信全部查清、零"待定"**：89 条是"内容太长超过本地模型 16384 token 上限"（未修，根因归 G4-10）；2 条是 5 月 14 日的 schema 冲突、1 条是旧 group_id 冒号格式——这 3 条的根因**当天之后就已修复**，不会再新增。
2. **一条都不算丢**：4 条正文完整躺在死信文件里（可逐字节恢复）；88 条只存了前 200 字预览，但每一条都顺着线索找回了**唯一**源头会话记录（7 个会话的原始 transcript 全部还在你电脑上）——可近似重建（找到了源头 ≠ 已经恢复，真正重建是 G4-10 的活）。**不可恢复：0 条**。另清点出 6 组重复（29 条是同内容反复入队），G4-10 恢复时会先去重，不会把同一段写 16 遍。
3. **死信文件的"真身"只有一处**：线上容器读写的是 `feature-obsidian-hybrid-dev` worktree 的 `backend/data/`（容器内实测 sha 一致）；主仓那份 685 行是 4 月的陈旧副本，另有两处孤儿残留——报告里有四址对照表，以后不会再查错文件。

## ✅ 技术验证（Claude 已代跑）

| 项 | 结果 | 证据 |
|---|---|---|
| 全程零写入（裁判判据 e） | 运行前后 四份 DLQ 文件 + qa_metrics.db 的 sha256 **逐字节不变**（diff 为空 → PASS） | `_bmad-output/审查/G4-9-evidence/shasums-before.txt` / `shasums-after.txt` |
| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；写模式 open 仅台账 `--out` 1 处 | `G4-9-evidence/grep-selfattest.txt` |
| live 挂载真相（判据 c） | 容器内 `sha256sum /app/data/dead_letter_episodes.jsonl` = 宿主 live 地址同值（92 行，`3b37460f…`）；compose :206-212 遮蔽史入报告 §1 | `G4-9-evidence/container-sha-check.txt` + 报告 §1 |
| 分类零偏差（判据 b） | budget_400×**89** / schema×**2**（P0-4 已修，`entity_types.py:343`）/ group_id×**1**（sanitize 已兜，`group_id_compat.py:64`）——与勘探预期逐条一致，脚本 `class_deviation` 字段为空 | 台账 JSON `class_distribution` |
| inline 完整性 + SHA 对账（判据 b） | 92/92 重算 sha256 对账：4 条 full_verified、88 条 truncated_prefix（`to_dict()` 的 `[:200]` 截断，`episode_worker.py:107`）、**0 条 anomaly** | 台账 JSON 逐条 `inline_state`/`sha_check` |
| 源指针核销（判据 b，qa_metrics.db 只读 mode=ro） | `qa_error_logs` **0 行** → 0/92 可经 qa_metrics.db 溯源（诚实记录）；附加核销：llm_call_logs.db 无正文、outbox 空、episode_body_full 0 条；**有效源指针 = request_id 组内 session 归因 → 7 个 transcript 全部在盘实测存在** | 报告 §4 + 台账 `qa_metrics_probe` |
| 可恢复性三态（判据 b） | 可字节级 **4** / 近似 **88** / 不可恢复 **0**；不可恢复清单显式成段 0 条、"待定" 0 条 | 报告 §5 + 台账 `recoverability_distribution` |
| G4-10 稳定键（判据 d） | 逐条复合键 `{line_no, sha256_prefix, request_id}` + 台账头部冻结文件 sha；request_id 92 条仅 25 唯一值的实测证明单列不可作键 | 报告 §6 + 台账 `records[].stable_key` |
| Codex 独立审查 round-1 | **BLOCKED**（3 BLOCKER：--out 可截断输入 / 快照不原子 / 交付物未冻结；3 HIGH：inline 判定 fail-open / request_id 归因传染 / transcript 归因折叠；3 MEDIUM + 4 LOW。同时确认：**当前 92 条数字逐项 0 mismatch**、class/三态/家族计数全对） | `_bmad-output/审查/codex-review-CARD-G4-9.md` |
| Codex findings 逐条整改 | **13/13 完成**（见下）；整改版脚本负例门全过；全量重跑数字与整改前逐项一致 | 报告 §7/§7b + 证据包 |
| Codex 复审 round-2 | **仍阻断**（10/13 CLOSED；BLOCKER-1/HIGH-1/HIGH-3 未真正闭合 + 3 新 LOW）。同时独立复算确认：67ccebe1 冻结生效、92 条数字与 6/29 重复簇全部可复算 | `_bmad-output/审查/codex-review-CARD-G4-9-round2.md`（codex 被 cyber 误拦，内容由 stdout 抢救存档） |
| round-2 findings 逐条整改 | **6/6 完成**：inode 身份守卫封 hardlink+大小写别名 / full_body 长度门+anomaly 前置 / 不可读根 exit 2+symlink 逃逸拒采信 / 3 新 LOW。5 条新负例实测全过、正例无回归、数字仍逐项一致 | 报告 §7/§7c + `grep-selfattest.txt` |
| Codex 复审 round-3 | **仍阻断**（4/6 CLOSED；BLOCKER-1/HIGH-3 判 PARTIAL + 1 新 MEDIUM + 2 新 LOW）。同时确认：HIGH-1 与三条 LOW 已闭合、台账数字有效且与 commit 字节一致 | `_bmad-output/审查/codex-review-CARD-G4-9-round3.md` |
| round-3 findings 逐条整改 | **6/6 完成**：transcript 并入保护集 / O_NOFOLLOW+fstat 消 TOCTOU / os.walk 替 glob（不跟随目录 symlink+遍历错误显式捕获）/ 不可读候选 fail-closed / JSONL 严格 LF 分帧 / 非 dict 归 unparseable。6 条新反例实测全过、数字第三次不变 | 报告 §7d + `grep-selfattest.txt` |
| Codex 复审 round-4 | **仍阻断**（1/6 CLOSED；2 新 BLOCKER + 1 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round4.md` |
| round-4 findings 逐条整改 | **9/9 完成**：全候选入保护集 / 读侧 fd 身份消源侧 TOCTOU / 新增 unverifiable 第四态 / FIFO 设备门 / strict UTF-8 / 3 条错型与边界 LOW / provenance receipt。5 条新反例实测全过；第四次全量重跑数字仍不变 | 报告 §7e + `grep-selfattest.txt` |
| 独立 Workflow 4-agent 复核 | G4-9 数字 agent：92 条重算 **0 mismatch**（class/inline/三态/25 request_id/7 transcript 在盘/台账 sha 全 CONFIRMED，仅 2 处描述区间 REFUTED 已修正）；只读契约 agent：与 Codex 同源的 3 条 blocker（已随上整改） | Workflow wf_737b1a95-20b journal |

## 🔧 Codex round-1 整改记录（13/13 关闭，BLOCKED → 整改完毕）

- **BLOCKER-1 --out 截断风险**：任意 --out 路径 "w" 无守卫，可覆盖 DLQ 自身（双审查独立实测复现）。整改：写前 resolve() 路径碰撞守卫，命中输入集合即 exit 2；负例实测拒绝、DLQ 完好。
- **BLOCKER-2 快照不原子**：records 与头部 sha 来自两次读取。整改：单次 read_bytes()，头部与逐条同源同字节。
- **BLOCKER-3 交付物漂移**：审查期间脚本/报告 sha 变化且未 track。整改：本卡 commit 冻结全部 exact bytes；自证文件内嵌脚本 sha 前缀。
- **HIGH-1 inline 判定 fail-open**：sha 匹配但长度不符会误判 full_verified（反例实测）。整改：长度精确匹配门 + 64-hex 合法性门 + anomaly 一律 fail-closed（unrecoverable + 如实 basis）。
- **HIGH-2 request_id 归因传染**：缺失值合入 "None" 组、跨类型合组、多 token 静默取长。整改：(类型,值) 复合键 + 缺失单条成组 + 前缀一致门（冲突拒采信）。
- **HIGH-3 transcript 归因折叠**：多命中照单全收、目录缺失误判 unrecoverable=88（实测复现）。整改：恰 1 常规文件命中门 + 递归 glob + 目录缺失 exit 2 拒诊。
- **MEDIUM-1~3**：episode_body_full 采信通路 / duplicate_clusters 6 簇 29 行 + reference_time 透传 / privacy 字段与 private-only 声明。
- **LOW-1~4**：两处区间修正（16948–20831、205–8036）/ 稳定键语义重写为"冻结快照 occurrence key" / schema 双处证据（LearningConcept.name + LearningTip.created_at）/ 挂载历史证据边界声明。

整改后全量重跑：92 条数字与整改前**逐项一致**（4/88/0、89/2/1、冲突 0、unparseable 0）——整改只收紧契约与通用鲁棒性，不改变本次 census 结论。

## 🔧 Codex round-2 复审整改记录（10/13 CLOSED → 剩 3 项 + 3 新 LOW 全关闭）

round-2 用真实入口反例证明我 round-1 的三处整改**没有真正闭合**（这正是二轮审查的价值）：

- **BLOCKER-1 未闭合**：守卫比的是路径字符串，**hardlink 与大小写别名照样截断 DLQ**。→ 改比**文件 inode 身份**；两种绕过实测双双 exit 2、DLQ sha 不变。
- **HIGH-1 未闭合**：`episode_body_full` 分支只核 sha 不核长度且排在 anomaly 之前，**anomaly 记录能翻案成"可字节级恢复"**。→ 加长度门 + 判定顺序改为 anomaly 优先；反例实测翻转。
- **HIGH-3 未闭合**：`chmod 000` 的目录仍 exit 0 并把全部记录**假判不可恢复**；symlink 可指到目录外冒充源。→ 不可读即 exit 2；symlink 与逃逸目标一律不采信；正例（真实唯一命中）无回归。
- **3 新 LOW**：full_verified 长度范围修正 131–180；台账三个 distribution 补零并新增 `inline_state_distribution`；`line_count` 与 records 改用同一 `splitlines()` 口径。

round-2 整改后再次全量重跑：92 条、4/88/0、89/2/1、6 簇 29 行、shasum 不变——**数字全程未变**。

## 🔧 Codex round-3 复审整改记录（4/6 CLOSED → 剩 2 项 + 3 新发现全关闭）

round-3 确认 HIGH-1 与三条 LOW 真正闭合、台账数字有效，又在两项路径安全上找到更深的绕过：

- **BLOCKER-1 仍 PARTIAL**：① 保护集漏了**归因到的 transcript**——`--out` 指向它会截断恢复源；② check-then-open 的 **TOCTOU** 仍在。→ ① transcript 写前并入保护集；② 改 `O_NOFOLLOW` 打开且**不带 O_TRUNC**，对实际 fd `fstat` 校验后才 `ftruncate`。反例实测：exit 2、transcript 完好。
- **HIGH-3 仍 PARTIAL**：Python 3.14 的 `glob` 在过滤前就已递归、跟随目录 symlink 且**静默吞掉不可读子树错误**；mode 000 的文件仍过 `isfile()` 被当可用源。→ 改 `os.walk(onerror=, followlinks=False)` + `os.access(R_OK)` 门；遍历受阻或有不可读候选一律拒绝裁定。三反例实测 fail-closed。
- **新 MEDIUM（JSONL 分帧）**：`splitlines()` 会把含 U+2028 的合法单行记录劈成两条坏行。→ 严格按 LF 分帧，header 与 records 共用同一函数。
- **新 LOW ×2**：非 dict JSON（`null`/数组）归 unparseable 不再炸全量；报告头补 artifact commit 链。

round-3 整改后第三次全量重跑：**92 条、4/88/0、89/2/1、6/29、shasum 不变——三轮整改数字全程未变**，改的全是通用鲁棒性与路径安全。

## 🔧 Codex round-4 复审整改记录（1/6 CLOSED → 9 项全关闭）

round-4 只认 1 项闭合，用更深的反例推翻其余"闭合"——两条新 BLOCKER 都是真的：

- **不可读但可写（mode 0200）的 transcript 绕过保护集**：我在"不可读"分支把候选路径清空了，于是它没进保护集，`--out` 指向它照样截断——不需要任何竞态。→ 新增"全候选清单"，无论可读与否一律并入保护集。
- **源侧 TOCTOU**：保护身份按路径 stat 采集、DLQ 稍后才按路径读取，中间可换 inode。→ 改为**从 fd 读取**：打开一次 → `fstat` 取身份 → 从同一 fd 读全量，保护的就是实际读到的那个对象。
- **把"看不见"说成"不可恢复"**：扫描受阻时仍输出 `unrecoverable`，与报告里"既不宣称不可恢复"自相矛盾。→ 新增第四态 **`unverifiable`**，逐条写明是遍历受阻还是候选不可读。
- **其余 5 项**：FIFO/设备节点门（`O_NONBLOCK`+`S_ISREG`）、非法 UTF-8 不再经 replace 冒充有效记录（strict decode）、三条错型与边界 LOW（`name=None`/`request_id=[]`/根为 `/`）、既有输出文件 `fchmod` 收紧（台账现为 `-rw-------`）、provenance 改后置 receipt 绑定精确 commit 链。

round-4 整改后第四次全量重跑：**92 条、4/88/0（unverifiable 0）、89/2/1、6/29、shasum 不变——四轮整改数字全程未变**。

## 📄 交付物清单（全部新增，零业务代码改动）

- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
- `_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md` — census 报告（挂载真相/分类/三态/交接契约）
- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
- `_bmad-output/审查/G4-9-evidence/` — 证据包（shasums ×2、grep 自证、容器 sha 实测、运行日志）
- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档

## ⏭️ 移交（不在本卡范围）

- **G4-10**：89 条 budget_400 根因修复（16384 context 超限 → 切块或提 budget）+ 按台账重放；3 条 `vault:default` 旧格式重放前需 group 重映射。
- **DeadLetterStore 全量正文开关**：`DEAD_LETTER_STORE_FULL_BODY` live 未启用是 88 条只剩前缀的直接原因——是否开启（隐私 vs 可恢复性权衡）留 G4-10 连根因一并裁。
