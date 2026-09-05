# fsrs_bridge.py 部署到 live vault — 2026-09-05T1052

用户 2026-09-05 授权（AskUserQuestion「授权部署」）。根因：第十批 X7-A e85d4ade 改开发树 fsrs_bridge.py，wrapper 双副本一致性门（daily-review-wrapper.sh:98-106）exit 78，复习链 09-05 09:05/10:05 两档 PREFLIGHT-FAIL。

| 文件 | sha256 |
|---|---|
| live 旧副本（已备份 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/backups/fsrs_bridge.py.pre-deploy-2026-09-05T1052.bak） | 66a755279ad7862603830ac5fa30b7c91837c7b42bc77b58b0d62a574bf3a4de |
| 开发树 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/canvas-vault/.claude/scripts/fsrs_bridge.py @ 868c6668 | 80679678ebf56d53bcbf5f6b5b2b0dbc51e66ea7f8c66977ff2f8d8e7615b35d |
| 部署后 live | 80679678ebf56d53bcbf5f6b5b2b0dbc51e66ea7f8c66977ff2f8d8e7615b35d |

验证：不手动触发；等下一档 launchd（每小时 :05）后看 ~/Library/Logs/canvas-daily-review.boot.log 与 `launchctl list | grep daily-review` 归 0、live outputs/今日复习.json generated_at 更新。

## 验证（2026-09-05 11:08 档）

| 观测 | 值 |
|---|---|
| boot.log | `[2026-09-05 11:08:37] wrapper start` → 无 PREFLIGHT-FAIL 行（门放行） |
| `launchctl list \| grep daily-review` | `-  0  com.canvas.daily-review`（上一档 78 → **0**） |
| live `outputs/今日复习.json` | `generated_at 2026-09-05T11:08:38+08:00`，due_nodes 6，schema 3（09-04 09:05 → 恢复） |

结论：复习链恢复。**规则回写**：合入改 `canvas-vault/.claude/scripts/{fsrs_bridge,decay_beta}.py` 的卡必须同批部署到 live（wrapper 双副本门），否则整条复习链停摆——第十一批 Z2（G3-3）也改 fsrs_bridge.py，合入前须用户再授权一次部署。
