# CARD-G8-1 证据包

| 文件 | 内容 |
|---|---|
| `live-vault-shasum-BEFORE.txt` / `-AFTER.txt` | live vault 全量 324 文件 SHA-256，校验脚本真跑前后各一份；两份逐字节相同 = 零写入实证 |
| `check-live-enforce-stdout.txt` | `--enforce` 对 live vault 的输出（exit 0，0 finding） |
| `check-live-report.json` | `--report --json` 机器可读档（dirs 175 / files 324 / findings 0 / divergent 1） |
| `pytest-119-passed.txt` | `pytest tests/unit/test_vault_doc_roles.py -q` 完整 stdout（119 passed） |
| `check-live-degraded.txt` / `-refused.txt` | 降级门两态：显式 `--allow-degraded` 可跑 / 未声明则 exit 2 拒绝执行 |

复跑（绝对路径，无占位符）：

```
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles
LIVE=/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault
(cd "$LIVE" && find . -type f -not -path "./.git/*" -print0 | sort -z | xargs -0 shasum -a 256) > /tmp/before.txt
backend/.venv/bin/python backend/scripts/check_vault_doc_roles.py --enforce --vault "$LIVE"
(cd "$LIVE" && find . -type f -not -path "./.git/*" -print0 | sort -z | xargs -0 shasum -a 256) > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
cd backend && .venv/bin/pytest tests/unit/test_vault_doc_roles.py -q
```
