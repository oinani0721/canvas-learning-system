# CARD-G5-9 — codex round-1 发现处置对照表

> **上游**: `codex-review-CARD-G5-9.md`（首轮，0 BLOCKER / 4 HIGH / 8 MEDIUM / 2 LOW，裁决「需再一轮」）
> **处置卡**: BATCH-2026-08-29-第六批 / CARD-收口A ③
> **停轮规则**（本批，写在验收单头部）: **BLOCKER 或 HIGH > 0 → 再一轮；MEDIUM / LOW → 一律登记结案，不再开轮。**
> **处置口径**: 4 条 HIGH **全部整改 + 逐条负验证**；MEDIUM/LOW 按规则**登记结案**，
> 其中 3 条「文档/回执与实现不符」因与本次改动同域且属名实一致问题，一并修掉（逐条注明）。

---

## 一、HIGH（4/4 已整改，8 变体负验证全承重）

| # | 发现 | 整改 | 负验证变体 |
|---|---|---|---|
| HIGH-1 | **空 SHA 绕过用户确认字节绑定**。`required=True` 只保证 flag 出现；`--expect-content-sha ''` 因 falsy 短路跳过比较，复核者隔离实测 `created: true`、写出 1092 bytes | 新增 `_SHA256_RE`（64 位小写 hex）形状白名单，**先于**比较；比较本身改为**无条件**。同型约束施于 undo 的 `--expect-sha` | **A**（回退 falsy 短路）→ 7 红<br>**B**（去掉 undo 形状白名单）→ 1 红 |
| HIGH-2 | (a) create 只核 inode 不核**发布字节**：并发者原地改写同一 tmp inode 时核对照过，回执 SHA 与目标实际字节分叉（`e51ca99e…` vs `43cb09e0…`，而返回 `err=None`）<br>(b) 失败回滚**按 pathname unlink**，会删掉并发者刚创建的文件（返回失败时文件已丢失） | (a) 发布后用新 fd **重读目标字节**并与待写 content 做 sha 全等，inode + 字节两条都过才算成功<br>(b) inode 不符 = target 已不是我们的文件 ⇒ **绝不删**，只如实回报；仅 inode 仍是我们的（纯字节被原地改写）才撤销自己的发布 | **E**（只比 dev,ino 不回读）→ 1 红<br>**F**（回退为按路径 unlink）→ 1 红 |
| HIGH-3 | (1) 最终重读校验后先 `close(fd)` 再按路径 unlink，窗口内换入的新文件被误删（注入 `USER-NEW-BYTES` 实测新 inode 被删、留痕只有旧版本、回执仍报 `undone: true`）<br>(2) 留痕写入 + fsync 后**从不回读**：原地改写留痕 inode ⇒ 源已删、回执 retained SHA 说谎（`765bf07e…` vs 实际 `3710644e…`） | (1) 紧贴 unlink 前**再 lstat 一次**核 identity，把窗口压到相邻两个系统调用之间（POSIX 无「按 inode 删除」原语，残留窗口已如实写进代码注释）<br>(2) 删源之前把留痕**重新打开读回**，size + sha 全等才继续；任一不符 → 绝不删源 | **H**（去掉 unlink 前复核）→ 1 红<br>**G**（去掉留痕回读）→ 1 红 |
| HIGH-4 | **五类关键变异 4 类 survivor**（O_EXCL/no-replace、父目录 symlink 守卫、wikilink 集去 `|`、undo dev/inode 比较，弱化后完整套件仍 33 passed）；且 7/33 为非承重或假门 | 新增 20 条承重门（33 → 53）。**假门修复**：复核者点名的三条 create 拒绝测试都**没传 `--expect-content-sha`**，在 argparse 阶段就 exit 2、从未触达被测防御 ⇒ 新增同场景但**带合法 sha** 的版本；wikilink 由整体门改为**逐字符参数化**（5 例） | **C**（只删 `\|`）→ 1 红<br>**D**（同时禁纵深两层 symlink 防御）→ 1 红 |

**负验证**: `g5-9-evidence/round1-high-negverify.py`（⛔ 必须串行）+ `…-negverify.txt`
**结果**: 8/8 变体如期变红；还原后字节与备份**逐字相同**（sha `4e99f06b…`）；还原后完整套件 53 passed。

### 负验证过程中抓到的两个方法论问题（如实记录，值钱的部分）

1. **变体 D 首跑报「命中 2 处」**——目录 symlink 守卫在 `_prepare` 与 `cmd_undo` 各有一份同文实现。
   更重要的是：这里是**纵深防御**（`_prepare` 守卫 + `_symlink_probe` 两层），只禁一层测试仍绿。
   若照此收工，会得出「该门非承重」的**错误**结论。修法 = 变体同时禁掉所有层，证明测试锁的是**性质**而非某一行。
2. **变体 H 首跑报「弱化后仍全绿」——是测试锁错了门，不是实现有问题。**
   第一版注入点选在 `_fsync_dir(undo_dir)`，被更早的 cfd 重读校验抓住。
   根因是一个隐蔽陷阱：`mod.os` **就是全局 `os` 模块**，patch `mod.os.lstat` 会拦下**进程内所有** `os.lstat`
   （含 `pathlib` 内部），所以「对 target 的第 2 次调用」根本不是 unlink 前那次。
   修法 = 按调用帧定位（`f_code.co_name == "cmd_undo"` 且 `st_dest` 已在局部变量里 ⇒ 留痕回读已完成），
   并在断言里**点名拒绝理由必须来自「删除前一刻」那道**，防止再次锁错门。

---

## 二、一并修掉的 3 条（名实一致，与本次改动同域）

停轮规则说 MEDIUM/LOW 登记结案。下面 3 条例外处理，理由统一为：
**它们是「文档/回执声称的行为 ≠ 实现的实际行为」，且恰好落在本次改动的同一段代码上**——
在动过这段代码之后仍留着已知为假的声明，比不改更糟（DD-13 名实一致）。每条都带门。

| # | 发现 | 处置 |
|---|---|---|
| MEDIUM-1 | SKILL.md:379-381 称「preview 之后 vault 若有**任何**变化均拒绝」；实际绑定的是**拟写入全文字节**，vault 改动若不影响产物字节（改节点正文但角色/计数不变）则 sha 不变、旧 sha 仍可创建 | SKILL.md 改写为「绑定的是拟写入的那份全文字节」+ 显式**诚实边界**段落：保证是「输出字节未变时所见即所写」，不是「vault 任何变化都拒绝」；同时补写 `--expect-content-sha` 的形状要求 |
| MEDIUM-7 | `undo_hint` 以 `undo …` 开头，缺 `python3 <脚本>` 前缀；SKILL.md 却称「可直接复制执行」——普通 shell 里 `undo: command not found` | 回执补 `sys.executable` + 脚本绝对路径（均 `shlex.quote`）。新增门 `test_undo_hint_is_actually_executable`：把 hint **原样跑一遍**（只替换 `--undo-dir` 占位符），必须真的完成回退 |
| LOW-2 | 实现拒绝 `# \| ^ [ ]` **5** 个字符，SKILL.md 只列 3 个；且这些字符走 `{"error":...}` + exit 2，不是文档说的 `refusal_reason` | SKILL.md 两处改为 5 字符全列 + 说明返回形态是 exit 2 而非 `refusal_reason`（安全行为**强于**旧文档描述）。逐字符门已由 HIGH-4 的参数化测试覆盖 |

---

## 三、登记结案（按停轮规则不再开轮，移交后续卡）

| # | 发现 | 结案理由 / 移交去向 |
|---|---|---|
| MEDIUM-2 | create/undo 不是完整失败原子事务：tmp 清理异常被吞、`_fsync_dir` 对 open/fsync 失败全静默仍返回成功、undo 无 journal/restart reconciliation | 属**耐久性纵深**，非产品行为错误；当前所有失败分支都不会两头皆空（留痕先于删源）。要做完整需引入 journal，是独立设计题 ⇒ 移交 |
| MEDIUM-3 | symlink 防御只覆盖瞬时、直接路径；vault 根/祖先与**中段**没有 dirfd 锚定；undo 的 `resolve()` 先行会让后面的 `O_NOFOLLOW` 看不到原 final symlink | 该路径**有留痕可恢复**（复核者据此定 MEDIUM）。彻底修需全链 `openat(dirfd)` 重写路径层 ⇒ 移交 |
| MEDIUM-4 | 跨板只对**汇总数字**去重，链接清单未全局去重（两板共享 `Shared` 时 totals=1 但 `[[节点/Shared]]` 出现 2 次） | 产物**语义正确**（成员确实同时属于两板），只是可读性；且 `duplicate_members` 已显式申报 ⇒ 移交为体验改进 |
| MEDIUM-5 | **`recap_kind` 没有被所有消费方读取**：`board_manifest_service` 完全不看它，把阶段回顾板计入 `exam_board_count`；API/Snapshot 模型无该字段。实测 `exam_history 1→2`、锚板 `exam_board_count 0→1` | ⚠️ **本条最值得后续跟**。但修它要动 `board_manifest_service` + API/Snapshot 模型，属**后端消费面**改动，明显超出「补 codex 存档」的卡范围 ⇒ **移交**，建议与 G5-11 或 board_manifest 系卡合并 |
| MEDIUM-6 | 消费面证据多为必要前提/静态文本，非端到端执行证据（start-exam-board / quiz-answer 未真实驱动；Dashboard 未在 Dataview 运行时执行） | 需真实 LLM/Obsidian 运行时 ⇒ 与 D5 前置（用户 UAT）同域，顺延 G5-11 |
| MEDIUM-8 | C1/C2/C3 触发与范围解析未闭合：SKILL CRITICAL TRIGGER 仍只有 `/board-recap`，`skill_trigger_matrix.yaml` 三条仍 `trigger_today:false`；C1/C2 无板名而脚本强制 `--boards` | 触发面归 **G5-1 触发矩阵**车道，本卡硬边界外 ⇒ 移交 |
| LOW-1 | UAT 写 31 tests，目标 commit 实际收集 **33** | 低估非假绿。本卡整改后已是 **53**，验收单按新数字更新 |

---

## 四、判据（本地实跑）

| 项 | 结果 |
|---|---:|
| `tests/skills/test_g5_9_recap_exam.py` | 33 → **53 passed** |
| S6 完整裁判 `test_recap_scan_signals.py` + `test_g5_9_recap_exam.py` | **158 passed**（裁定书基线 138） |
| 负验证 8 变体 | **8/8 如期变红**；还原后字节逐字相同 |
| `ruff check`（被测脚本 + 测试） | All checks passed |
