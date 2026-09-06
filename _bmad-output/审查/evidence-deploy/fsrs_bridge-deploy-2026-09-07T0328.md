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
- 验证（下一个 :05 档后补填）：`launchctl list | grep daily-review` 第二列 / boot.log 无 PREFLIGHT-FAIL / `outputs/今日复习.json` generated_at。
