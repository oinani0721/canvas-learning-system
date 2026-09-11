# fsrs_bridge.py live 部署证据（第十二批 Y1-A 合入当天）

- 时间：2026-09-07 03:28:05（授权：用户于 2026-09-06 晚 AskUserQuestion 选「授权部署并合并」）
- 触发：主干 ff-only `65cfd8ff → ba998a60`（第十二批 23 卡 squash + 4 集成 commit），Y1-A（CARD-G3-3-R1，含 Z2 原 777e8f97）带入 `canvas-vault/.claude/scripts/fsrs_bridge.py` +69/−0
- wrapper 门：`~/Library/Application Support/CanvasReview/bin/daily-review-wrapper.sh:99-105` 对 `$WT=feature-obsidian-hybrid-dev` 与 live 逐字节 cmp `decay_beta.py` / `fsrs_bridge.py`

| 文件 | sha256 |
|---|---|
| live 旧副本（部署前） | `80679678ebf56d53bcbf5f6b5b2b0dbc51e66ea7f8c66977ff2f8d8e7615b35d` |
| 备份 `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/backups/fsrs_bridge.py.pre-deploy-2026-09-07T0328.bak` | `80679678ebf56d53bcbf5f6b5b2b0dbc51e66ea7f8c66977ff2f8d8e7615b35d` |
| 主干 ba998a60 版本 | `a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0` |
| live 部署后 | `a766fbcc28e3ff917e740843c633e800aa8a75e949295f83efc90f55105f90f0` |
| decay_beta.py | 未动，cmp SAME |

- 只部署 `fsrs_bridge.py`；**未部署** quiz-answer / start-exam-board 的 SKILL.md（live SKILL 旧版只 subprocess 调 bridge，新 bridge 纯加法 cas_* 符号，加性兼容）。
- launchd 日程：`com.canvas.daily-review` 只在 09:05–20:05 每小时一档（plist StartCalendarInterval Hour 9..20），夜间无档；部署时刻 03:28 到首档 09:05 之间 wrapper 不会跑，因此**不存在停摆窗口**。首档 09:05 后核：`launchctl list` 第二列（部署前 0）、boot.log 无 `fsrs_bridge.py_version_skew` / `PREFLIGHT-FAIL`、`outputs/今日复习.json` generated_at 更新为 2026-09-07。
- 验证（09:05 档后补填）：`launchctl list | grep daily-review` 第二列 / boot.log 无 PREFLIGHT-FAIL / `outputs/今日复习.json` generated_at。
- **验证回填（2026-09-11 09:05 档实测，主 session 波 0）**：`launchctl list | grep daily-review` → `-	0	com.canvas.daily-review`（第二列退出码 **0**）；launchd StandardOutPath `~/Library/Logs/canvas-daily-review.log` mtime `2026-09-11 09:05`，末三行 `[runner] generate:cached push:skip-done fallback:-` / `bark accepted http=200 code=200` / `[runner] generate:new push:accepted fallback:-`；`canvas-vault/outputs/今日复习.json` generated_at **`2026-09-11T09:05:05+08:00`**（date 2026-09-11）；`~/Library/Logs/canvas-daily-review.err.log` 无 09-11 条目（mtime 08-01）。⚠️ 台账 §三.14(f) 写的 `canvas-vault/backups/daily-review.log` **不存在**——真实日志路径以 `~/Library/LaunchAgents/com.canvas.daily-review.plist` 的 `StandardOutPath` 为准；「04:05 档」不存在（日程只有 09:05–20:05 每小时一档）。本次未部署任何文件（第十四批无部署卡；`fsrs_bridge.py` / `decay_beta.py` 零写者）。

