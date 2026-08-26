结论：**第三轮仍为 BLOCKED。当前剩余 1 个 BLOCKER、4 个 HIGH。** 审查快照：`card/l1-crossvault @ 9fff98c2d3c9`。

## F1–F7 裁定

| 项目 | 裁定 | 关键证据 |
|---|---|---|
| F1 锁参数同源、fail-hard | **关闭** | [push.sh:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:13) 仅接受完整 `--vault`，并与 [runner:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_run.py:193) 的 `allow_abbrev=False` 一致；实跑 `--v` 得 rc=2，未进入业务。[push.sh:29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:29) 使用同一解释器/`vault_key`，失败或空结果于 37–40 行退出 78，basename fallback 已删除。 |
| F2 mv 决胜、代际校验、信号退出 | **维持 BLOCKER** | [push.sh:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:75) 的目标含各自 PID，不阻止晚到回收者按旧判断搬走新一代活锁；代际检查发生在锁名已空缺之后。实测第三进程可趁隙夺锁；而 [line 86](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:86) 的恢复 `mv graveyard LOCK` 在目标目录已存在时会嵌套并返回 0，结果同时留下两个 live owner。INT/TERM 显式退出子项已关闭。 |
| F3 迁移状态机、决胜点 | **维持 HIGH** | [migrate:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:106) 只解决两个 migrator 抢同一 `old`，未与 runner 共锁，也无 `new↔bak` 代际证明。真实入口复现：内容不同的 `new + bak` 被 [lines 63–72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:63) 判为“迁移已完成”，rc=0；旧 `last_push_accepted_date` 可仅存于 `.bak`，导致重复推送。 |
| F4 O_EXCL | **关闭原缺陷** | [migrate:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:114) 的 `"x"` 确实独占创建且不跟随悬空 symlink，原“覆写 symlink 目标”反例消失。但该修法引入下述新 HIGH。 |
| F5 wrapper 退出码 | **关闭** | [wrapper:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:102) 裸调用后立即读取 `$?`，并保留首个非零；不再取得 `!` 后的 0。 |
| F6 containment | **维持 HIGH** | [wrapper:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:67) 验证 `REAL_VAULT`，但后续 [line 81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:81) 和 [line 102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:102) 仍使用可变的字面 `$VAULT`。实测 alias 检查时指向 root 内并 PASS，检查后换向 root 外，child 随即解析到外部目录。 |
| F7 日期解析 | **维持 HIGH** | [memory-health:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/memory-health.sh:93) 先 `str(v)[:10]` 再解析，且 [line 108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/memory-health.sh:108) 只有下界、没有 `<= today`。`"9999-12-31junk"`、有效未来日期及整数 `20991231` 均可继续永久假绿；仅原 `"zzzz"` 子例关闭。 |

## 处置引入的新 HIGH

- **N1 — HIGH：迁移最终路径半写可见。** [migrate:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:114) 直接在最终 `new` 路径创建后写内容，丢失原来的“完整临时文件→原子发布”。若 runner 在写完前读取，会由 [runner:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_run.py:76) 将空/半截文件隔离；migrator 仍向已改名 inode 写完并返回成功，最终 `new` 可能不存在或被默认新账本替代。

## MEDIUM 简记

- additive 精确契约：**维持**；[测试:242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_pick.py:242) 仍未锁 notification 精确键集合及 title/body 原值。
- 空清单：**维持**；纯 TAB 或 `,\t,` 可通过只删除空格的守卫，循环零次后退出 0。
- 迁移嵌套结构：**维持（部分修复）**；旧输入已校验，但 `new+bak` 恢复态仍只验根 `dict`。
- health 拆分/身份：**维持（部分修复）**；health 拆 CR/FF/VT，wrapper 默认 IFS 不拆，CRLF 配置仍漂移。
- 日期逐字段异常隔离：**关闭窄项**；但严格性由 F7 HIGH 阻断。
- PID 写失败回滚：**维持**；写失败可能留下空 `pid`，随后仅 `rmdir` 无法清理。
- PID 复用：**维持**；只是注释登记，长寿命无关进程可让锁长期误判为活。
- dry-run pycache 防线：**关闭**。

验证：指定 pytest **36 passed、10 warnings**；`bash -n ×3`、`git diff --check` 通过。绿色测试不覆盖上述锁竞态、迁移/runner 交错、containment TOCTOU 或 health 敌对日期。未真实调用 Bark/launchctl、未跑全量 CI；Graphiti MCP 本轮未暴露；未读取 backups 或 vault output 内容，工作树未修改。

**合入结论：BLOCKED——BLOCKER/HIGH 未清零（1 BLOCKER、4 HIGH），不可合入。**



---

# 附录 C — 第三轮处置记录（Claude, 2026-08-25）

## BLOCKER

- **F2 残余竞态 + mv 恢复嵌套 bug → 已修（方案更换）**。放弃 mv 搬锁（其恢复分支在目标已存在时确会嵌套返 0——实锤）。定稿方案：主锁永不被搬动；回收者先 mkdir 抢唯一「回收权」`$LOCK.reclaim`，持权下重读代际（pid token 与判定时一致才拆）——此后无人能改该锁（acquire 需 mkdir 必失败、回收需抢权必失败），拆除绝无误伤；权柄自身死留 >6h 才被代清。ownership token 升级为 "pid + 进程启动时刻"（ps -o lstart=），pid 复用不再误判活锁（沙盒实测：活 pid + lstart 不符 + 陈旧 → 正确回收）。

## HIGH

- **F3 → 已修**。①迁移与 push.sh/runner 共锁：实迁前 mkdir 同名 per-vault 锁（抢不到 rc1 退出），finally 释放；dry-run 走无锁纯只读路径（字面零写含锁目录）。②完成态判据升级为 new/bak 逐字节相等——内容不同一律 rc1 报"人工核对后重迁"，不再有"旧账本仅存 .bak 却判完成"的重复推送通道。
- **N1 → 已修**。发布改 mkstemp（随机名独占创建）+ os.replace 原子换名：终点路径无半写可见窗口；rename 只替换链接名，预置悬空 symlink 不能把内容引到别处（测试改按新语义断言：rc0、劫持目标不存在、终点为常规文件）。
- **F6 → 已修**。containment 校验通过后 VAULT=物理路径——后续 cmp/push 全用物理路径，校验后换向 alias 不再影响本轮。
- **F7 → 已修**。日期解析去截断（"2026-08-25junk" 整串解析失败）、拒非 str（整数 20991231 → None）、加上界（健康窗 [昨天, 明天]，"9999-12-31" 不再假绿）。敌对日期合成实测：生成:❌ 推送:-；正常今日：生成:✅ 推送:✅。

## MEDIUM

- additive 契约 → notification 键集合恒等 + id/group/title/body 四值全部精确锁定。
- 空清单 → 守卫改 tr -d '[:space:]'（纯 TAB 也拦）。
- CRLF → wrapper 与 memory-health 的 .env 提取管道统一去 \r。
- pid 写失败 → acquire 失败分支先清 pid 再收目录（不留非空锁）。
- 迁移嵌套结构恢复态 → 已被字节相等判据取代（不等即 rc1）。

## 复验

36 passed；bash -n ×3、ruff 全绿；锁沙盒四分支（正常/活 token skip/pid 复用回收/死锁回收）通过；memory-health 敌对与正常日期实测；生产回归 exit 0。
