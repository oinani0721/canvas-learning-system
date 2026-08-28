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
> 这张卡**没有修任何东西，也没有恢复任何数据**——它是一次"清点尸体"的只读普查（脚本对输入零写入已逐次取证；安全边界见文末"诚实边界"段）：
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
| 脚本只读自证（判据 a） | import 行全 stdlib；neo4j/graphiti/bolt/app. import **0 命中**；`--apply` 定义 **0 命中**；**全文无任何截断调用**（写出走 O_EXCL 临时文件 + 原子替换） | `G4-9-evidence/grep-selfattest.txt` |
| 只读契约回归测试（round-9 必需项④） | **19 passed** —— 把 8 轮审查中实测封死的反例全部固化（DLQ/hardlink/恢复源区/根内 symlink/FIFO/不可读候选/扫描受阻/anomaly/bool 长度/坏 JSON/非法 UTF-8 等）。该测试当场抓出一个真实回归（架构改动丢了文件类型门），已修 | `backend/tests/regression/test_census_dead_letter_readonly_contract.py` |
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
| Codex 复审 round-5 | **仍阻断**（3/8 CLOSED；2 BLOCKER + 2 HIGH + 2 MEDIUM + 3 LOW）。台账数字仍被确认可采信 | `_bmad-output/审查/codex-review-CARD-G4-9-round5.md` |
| round-5 findings 逐条整改 | **9/9 完成**：先扫描后判定（冲突候选亦入保护集）/ QA DB fd 身份+复核 / 可见性优先于 anomaly / fchmod 后置于碰撞检查 / QA DB 特殊文件门 / no_token 归 unverifiable / 3 条 LOW。6 条新反例实测全过；第五次全量重跑数字仍不变 | 报告 §7f |
| Codex 复审 round-6 | **6/9 CLOSED**（visibility 优先/fchmod 顺序/no_token 语义/3 条 LOW 已闭合）；剩 2 BLOCKER + 1 MEDIUM 揭示保护集**依赖枚举完整性**的架构缺陷 + 3 新发现 | `_bmad-output/审查/codex-review-CARD-G4-9-round6.md` |
| round-6 findings 整改 | **架构级修复 + 6 项**：新增不依赖枚举的**路径层防御**（--out 禁落 transcripts 根内 / 禁等于任一输入 realpath）、QA DB 验证 fd 保持打开至复核完毕、no_token 亦扫描、证据包重生成、ledger 冲突原因自描述、lone surrogate 回退。反例实测：0333 隐藏目录内 transcript 作 --out → exit 2 完好 | 报告 §7g |
| Codex 复审 round-7 | **关键裁定分离**："92 条冻结 ledger **可以采信**；生成器与 UAT 的纯只读安全声明不可验收"——卡面 census 判据已满足，阻断全在工具安全承诺侧。1 BLOCKER（大小写别名根，无需竞态）+ 4 项路径 TOCTOU + 1 MEDIUM（非原子写）+ 2 LOW | `_bmad-output/审查/codex-review-CARD-G4-9-round7.md` |
| round-7 findings 整改 | **架构级第二次修复**：写出改 O_EXCL 临时文件+fsync+os.replace（**全文再无 ftruncate 调用**），五项绕过整类失效；containment 改 inode 逐级比较（normcase 在 POSIX 是恒等函数，我的假设错了）；扫描受阻直接拒绝写出。实测：根外 hardlink 指向根内 transcript 作 --out → 源内容完好 | 报告 §7h |
| Codex 复审 round-8 | 重申裁定分离：**「可验收：92 条冻结 ledger snapshot；不可验收：生成器一般安全性与 UAT 的纯只读声明」**。3 新 BLOCKER（SQLite URI 未转义 #/? / QA DB 仍按 pathname 开可 ABA / 根内末级 symlink 因 rename 不解析而被替换）+ 1 HIGH + 1 MEDIUM | `_bmad-output/审查/codex-review-CARD-G4-9-round8.md` |
| round-8 findings 整改 | **6/6 完成**：QA DB 改「已验证 fd 读字节 → 内存库 deserialize」（URI 转义与 ABA 一并消失，含 #? 路径实测通过）；containment 加父目录语义（POSIX rename 不解析末级 symlink）；扫描受阻去掉 and args.out（stdout 模式亦拒）；replace 纳入 try + fsync 父目录 | 报告 §7i |
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

## 🔧 Codex round-5 复审整改记录（3/8 CLOSED → 9 项全关闭）

round-5 继续深挖，两条新 BLOCKER 与两条 HIGH 都成立：

- **冲突组的候选没进保护集**：token 冲突时我在扫描**之前**就早退了，那些候选从没被看到，`--out` 指向它们照样截断。→ 改成**先扫描后判定**，无论最终是否采信，见到的候选一律进保护集。
- **qa_metrics.db 身份没绑定实际读取**：先按路径 stat、SQLite 稍后按路径重开，中间可换。→ 改 fd 取身份 + 打开后复核身份一致。
- **anomaly 吞掉了"看不见"**：`anomaly→unrecoverable` 排在可见性判断之前，扫描受阻时仍断言"不可恢复"。→ 判定链改为**可见性优先**。
- **`fchmod` 排在碰撞检查之前**：`--out` 指向受保护的只读输入时，会先把它的权限从 644 改成 600 才发现碰撞——字节没丢但输入被改了。→ 碰撞检查前移。
- **其余 5 项**：QA DB 特殊文件门、无 token 归 `unverifiable`、单独换行算 1 空行、strict encode 堵住 lone surrogate 伪造 `full_verified`、`bool` 不再通过长度门。

**一处计数如实变化**：归因冲突 0→3。因为"名字不含 session token"现在被诚实标为"未做归因扫描"，正是那 3 条 callout 记录；它们 inline 全量、不依赖 transcript，仍是可字节级恢复。**三态分布不变**（4/88/0/0）——是标注变诚实，不是结论变化。

round-5 整改后第五次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——五轮整改数字全程未变**。

## 🔧 Codex round-6 复审整改记录（6/9 CLOSED → 架构级修复）

round-6 指出了一个我补丁修不掉的根因：**保护集依赖"能不能枚举到"**。不可列举但可穿越的目录（`0333`）里的 transcript，`os.walk` 看不见，就进不了保护集，`--out` 指向它照样截断；QA DB 的 inode 被 A→B→A 换过也一样。

→ 改为**双层防御**：在 inode 保护集之外，加一层**不依赖枚举**的路径判断——`--out` 的真实路径不得落在 transcripts 根目录内（整个恢复源区域禁写），也不得等于任何输入文件的真实路径。实测：隐藏目录内的 transcript 作 `--out`，inode 保护集根本没看见它，路径层直接拦住，exit 2、文件完好。

另修：QA DB 的验证 fd 改为**保持打开**到复核完毕（堵 ABA）；`no_token` 分支也扫描（原本完全不扫，候选进不了保护集）；证据包每轮重生成（round-6 指出我的 self-attest 停留在 round-4 的旧 SHA，属实）；台账新增冲突原因自描述。

round-6 整改后第六次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变——六轮整改数字全程未变**。

## 🔧 Codex round-7 复审整改记录（关键裁定分离 + 架构级第二次修复）

round-7 把结论分成了两半，这个区分很重要：

> **「现有 92 条冻结 ledger 可以采信；生成器与 UAT 的纯只读安全声明不可验收。」**

也就是说：这张卡要交付的 census 结论（92 条的分类、对账、三态、挂载真相、稳定键、运行零写入）**已经过关**；卡住的是"这个脚本作为工具，其只读承诺是否经得起敌意输入"。

- **一个无需竞态的真实绕过**：大小写不敏感卷上 `/Users/...` 与 `/users/...` 是同一个目录但 realpath 字符串不同，我 round-6 用来防御的 `os.path.normcase` **在 macOS/Linux 上根本是恒等函数**——这是我的知识性错误。改成逐级比较 **inode 身份**，不再依赖任何字符串。
- **五项绕过共用一个根源**：它们都依附于"截断一个已存在的文件"这个动作。改成「新建临时文件 → 写 → fsync → 原子替换」后，脚本**全文再没有任何截断调用**，这一整类绕过连同"崩溃留下半个台账"的风险一起消失。实测：拿一个指向恢复源的 hardlink 当 `--out`，台账正常写出，而**源文件内容一个字节没变**。
- **扫描受阻不再只是标记**：看不全就意味着保护集不完整，现在直接拒绝写出台账。

round-7 整改后第七次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、台账 0600、无临时文件残留——七轮整改数字全程未变**。

## 🔧 Codex round-8 复审整改记录（裁定分离重申 + 3 BLOCKER 全闭）

round-8 把结论说得更清楚了：**「可验收：92 条冻结 ledger snapshot。不可验收：生成器的一般安全性，以及验收单里那句"纯只读、唯一写出口、整类 TOCTOU 已消失"」**。

三条新 BLOCKER 都成立，其中两条有同一个彻底解法：

- **SQLite 打开方式**：`file:路径?mode=ro` 这种写法，路径里只要有个 `#`，`mode=ro` 就掉进 URI 的 fragment 被忽略，SQLite 可能按默认的**读写模式**打开——这直接推翻"唯一写出口"。而且就算持有验证过的文件描述符，SQLite 还是按路径自己去开，中间被换掉也发现不了。→ 改成从**已验证的文件描述符读出全部字节，灌进内存数据库**。SQLite 从此不碰路径，两个问题一起消失。
- **根内的软链接**：POSIX 规定重命名操作**不跟随末级软链接**。所以 `--out` 如果是恢复源目录里的一个软链接（指向外面），我按"它指向哪"判断会放行，但实际被替换的是**目录里那个链接本身**。→ 判定改看**父目录在不在恢复源里**。
- **stdout 模式漏网**：扫描受阻的拒绝条件我写成了"且指定了 --out"，于是省略 `--out` 就能绕过。→ 去掉该条件。

round-8 整改后第八次全量重跑：**92 条、4/88/0/0、89/2/1、6/29、shasum 不变、无 tmp 残留——八轮整改数字全程未变**。

## 📄 交付物清单（全部新增，零业务代码改动）

- `backend/scripts/census_dead_letter_episodes.py` — 唯一代码产物（只读 census 脚本，纯 stdlib）
- `_bmad-output/审查/G4-9-DLQ-census-2026-08-28.md` — census 报告（挂载真相/分类/三态/交接契约）
- `_bmad-output/审查/G4-9-dlq-ledger-2026-08-28.json` — 92 条逐条台账（G4-10 消费）
- `_bmad-output/审查/G4-9-evidence/` — 证据包（shasums ×2、grep 自证、容器 sha 实测、运行日志）
- `_bmad-output/审查/codex-review-CARD-G4-9.md` — Codex 独立审查存档

## 📐 诚实边界（round-9 收敛，替代原先过强的措辞）

九轮对抗审查后，Codex 始终维持一个分层裁定：**「92 条冻结台账可以采信；但生成器的一般安全性、以及验收单里"纯只读、唯一写出口、整类 TOCTOU 已消失"这类绝对化声明不可验收」**。

我接受这个区分，处置是**把声明改准确，而不是假装达标**：

- **可以确证的**：本次运行对全部输入文件（4 份 DLQ + qa_metrics.db）**shasum 前后逐字节不变**，九次重跑均已取证；脚本对 20+ 类误用与攻击路径 fail-closed，19 条回归测试固化。
- **不再声称的**：在共享可写目录、有并发写者、SQLite DB 正被写入等**敌意环境**下具备生产级安全。这类保证需要一致性快照、dirfd 相对发布、单写者锁——是把一次性 census 脚本升级为常驻工具的工作量，不在本卡范围。
- **已登记的**：FU-A~FU-D 四项（报告 §7j），**G4-10 若复用本脚本于活跃 DB 或共享目录，须先补齐**。

## ⏭️ 移交（不在本卡范围）

- **G4-10**：89 条 budget_400 根因修复（16384 context 超限 → 切块或提 budget）+ 按台账重放；3 条 `vault:default` 旧格式重放前需 group 重映射。
- **DeadLetterStore 全量正文开关**：`DEAD_LETTER_STORE_FULL_BODY` live 未启用是 88 条只剩前缀的直接原因——是否开启（隐私 vs 可恢复性权衡）留 G4-10 连根因一并裁。
