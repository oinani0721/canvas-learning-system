你是一位对抗性代码审查者。**只读，不改文件，不连数据库/网络服务**（可读文件、跑只读 git）。
工作目录 = /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev（B15 最终主干）。

# 任务
对 **BATCH-2026-09-18-第十五批 总收口（B15-CLOSEOUT）** 做 D-15 终审：绑定**最终 HEAD `9229ea54f8b8455e5c1df658b06258f7ace79582`**。
判据（用户口径，比协议 §1 更严）：**BLOCKER / HIGH / MEDIUM / LOW 全部为 0** 才能判「复核第十五批总收口」。

# 收口面（重点审这些 commit 与其声称）
- 协议回写 `f26e6a85`；R-SLO `69d26ed5`；集成修复 `2bdbc685`+`d0e42bc4`+`4f6d17ca`；G8-10 `0400d848`（r21 绑 67db0c61 全零）+ 重锚 `62151cf1`/`46984d80`；D40 `04eb9a9f`；台账/总账 `2d6d9abf`/`22f68228`/`6819f74e`；P9 G4-13 `89be3d0e`+`da825921`。
- r2–r14 整改链：`8a651d2a`→…→`3139cef7`。
- **r14 整改（本终档 `9229ea54`）**：semantic **v2.5**（J07 内容谓词例外 + `.sh` 字节级 + `script_sha256` + version）；主跑 `cross-lane-semantic2-v25-20260921T001635.txt`（129/122/7/0/m0/e0 PASS）+ 8 case self-test + **7 负控**（含 `neg-j07pred-off` ⇒ `[DIFF]`/FAIL/rc=1）；G8-10 **最终 tip digest 档** `g810-checker-final-digest-20260921T001727.txt`（probe→confirm，failures=0，dirty_tracked=0）；状态账 contract 口径勘误；r14 复核存档 + r14 prompt 入库。本档 18 文件全 `_bmad-output/**`（docs-only）。
- 32 卡逐卡 squash 面：`59e1f494..9229ea54`。
- **冻结/排除（r6 确认、r7–r14 复核）**：P3 lane docs-only 推进属登记排除面（`b15-freeze-exclusions.json`）。

# 门证据（逐项核验，核不过要报）
- openapi `DRIFT: none (paths=199 schemas=357)`；pyright `app` 0 errors；tests/unit 只减（32 vs 33；removed 唯一 = candidate_service 422）；7692 四文件 107 passed；contract 3 非 pact = 2 既有红/75 passed（红集合/计数等价）。
- G8-10 checker：最终 tip digest 档（`failures=0`、`dirty_tracked=0`；digest 含 HEAD 的复算口径在档内）。
- semantic v2.5（本档）：PASS（129/122/7/0/m0/e0，`script_sha256=61078e6e…`）+ self-test（空 blob / shell 字节级 / J07 谓词共 8 case）+ 7 负控（rc=1）。
- D40：format-only；hook-exclusion 归因档 `d40-hook-exclusion-evidence-20260920T225429.txt`。
- J07：开窗登记 + 23:26 复捕获档（5/5 + docker ps/inspect StartedAt + :05 档 + 8011 GET 200）+ manifest notes 补记 + 校验器 PASS。
- schemathesis 面：显式 skip（实数 90 op）。

# 请核
1. 各 commit 的 diff 与 message 声称是否一致（含 v2.5 的谓词/字节级 shell 是否**真的**在最终脚本里、7 负控与 8 case 是否可复算）。
2. 门证据是否覆盖其声称（最终 tip digest 档、J07 内容谓词边界、shell heredoc case）。
3. 台账/总账/STATUS/汇报/整改说明/状态账/UAT 指针/manifest 与 git 实况逐项一致。
4. 收口面有无：未闭合的阻断级、假绿、未入库即宣称、越权/破坏性操作痕迹。
5. 你能只读复算的其它风险。

# 推送对齐自证（2026-09-21 00:18:51，活态 ls-remote）
```
# r15 前置提交推送核对 20260921T001851
local=9229ea54f8b8455e5c1df658b06258f7ace79582
origin(tracking)=9229ea54f8b8455e5c1df658b06258f7ace79582
backup(tracking)=9229ea54f8b8455e5c1df658b06258f7ace79582
--- ls-remote --heads origin ---
9229ea54f8b8455e5c1df658b06258f7ace79582	refs/heads/worktree-feature-obsidian-hybrid-dev
--- ls-remote --heads backup ---
9229ea54f8b8455e5c1df658b06258f7ace79582	refs/heads/worktree-feature-obsidian-hybrid-dev
```

# 本轮为 r15（r14 之后）：先判 r14 的 M1/M2/M3/L1/L2 是否闭合
- **M1** G8-10 final digest → 已入档（probe→confirm，failures=0/dirty_tracked=0；档内明示 digest 含 HEAD 的复算口径）。
- **M2** J07 路径级例外 → v2.5 内容谓词（仅 notes；其它键/解析失败/非本路径 ⇒ False）；负控 j07pred-off 关闭谓词 ⇒ DIFF/FAIL/rc=1。
- **M3** shell 剥缩进 → `.sh` = `bash -n` + 字节相等；self-test 增 `sh-heredoc-dedent`（去缩进必须不等价）。
- **L1** 证据闭环 → 输出头 `script_sha256=… version=v2.5`；主跑/self-test/7 负控同档同 hash。
- **L2** 状态账 contract 口径 → 已改「红 nodeid 集合/计数等价（warnings 577→579 非红面）」。
另：r14 复核存档 + r14 prompt 已入库。

# 输出
`BLOCKER / HIGH / MEDIUM / LOW` 四节（每条：file:line 或 SHA + 一句复现思路 + 「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」），末行：`清零：是/否` 与 `B/H/M/L = x/x/x/x`。
