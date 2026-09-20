# manifest-bindings — 自引用排除规则与非循环绑定层（CARD-G8-7）

> 生成：2026-09-19（P3-C 车道）· 用途：闭合 Codex r2 H-1 / M-2 —— 给出「manifest 自身校验输出」与「被校验的最终对象」之间的**非循环绑定**。

## 1. 为什么需要本文件

`validate_release_manifest.py` 对 manifest 自身跑出的输出（`manifest-red-*.txt` / `manifest-green-*.txt` / `manifest-isolation-v2-*.txt`）**不能**登记进同一 manifest 的 `artifacts[]`：

```
manifest 内容 ──含──> artifacts[].sha256(isolation 文件)
     ▲                          │
     └────── 依赖 ──────────────┘   （isolation 文件的内容又依赖 manifest 内容）
```

登记即形成 SHA-256 循环，任何一侧改动都会让另一侧失真。因此本卡采取**非循环双层**：manifest 只在 `notes` 里**按文件名**引用本文件（不带 SHA）；本文件记录被校验对象的 SHA 与重跑方法。

## 2. 被校验对象与绑定

| 对象 | 路径 | SHA-256 | 校验结果 |
|---|---|---|---|
| 根（卡文字面）manifest | `manifest.json` | `ce05285d0e2f78288a4872950a7a1faba5dc5cb08f74b201ed4dbdefa61ba671` | ❌ `journey_id="G8-7"` 被 schema 模式 `^J(0[1-9]\|10)$` 拒（**恒红，按设计**；用户 2026-09-19 裁定混合方案） |
| 一致性副本（validator 目标） | `b15-g8-7/journeys/J06/manifest.json` | `866983aadbf9b0e0e8a91d1f917358b0058e72d4b1524b351e20344d7be092cf` | ✅ `rc=0` |

**isolation v2 绑定**：`manifest-isolation-v2-20260919T212305.txt` 首行区记录了冻结 SHA `866983aa…`，序列末行复算 `final_sha=866983aa…` 与之一致；副本对象在 [2]/[4] 单变量改动后均按 `restore_sha=866983aa…` 还原。

## 3. isolation v2 序列（单变量对照，均在冻结对象上）

| 步骤 | 单变量 | 期望 | 实测 |
|---|---|---|---|
| [1] before | — | 绿 | ✅ rc=0 |
| [2] red | 仅 `result` → `pass` | 仅红 `S3` | ✅ 仅 `[S3]`，rc=1 |
| [3] restore | — | 绿 | ✅ rc=0，`restore_sha=866983aa…` |
| [4] red | 仅 `signoff.status` → `approved`（缺 `user`/`at`） | 仅红 `signoff` | ✅ 仅 `[schema] signoff`，rc=1 |
| [5] restore | — | 绿 | ✅ rc=0，`final_sha=866983aa…` |

## 4. 早期 isolation / red / green 记录的归属（诚实声明）

`manifest-isolation-20260919T211402.txt`、`manifest-red-20260919T173050.txt`、`manifest-green-20260919T173050.txt` 与 `manifest-red-20260919T173056.txt` 生成于**较早的副本对象**（当时副本 SHA = `e0d39556…`，commands=3 / artifacts=1），**不绑定**当前冻结对象 `866983aa…`。它们保留为历史，判据以本文件的 isolation v2 为准。（Codex r2 H-1 即指出此点。）

## 5. 重跑方法（可复现）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy
M=_bmad-output/审查/evidence-g87-journey/b15-g8-7/journeys/J06/manifest.json
SCR=$(mktemp -d); cp "$M" "$SCR/frozen.json"
backend/.venv/bin/python backend/scripts/validate_release_manifest.py "$M"; echo "rc=$?"      # [1] 绿
backend/.venv/bin/python -c 'import json,sys;m=json.load(open(sys.argv[1]));m["result"]="pass";json.dump(m,open(sys.argv[1],"w"),ensure_ascii=False,indent=2)' "$M"
backend/.venv/bin/python backend/scripts/validate_release_manifest.py "$M"; echo "rc=$?"      # [2] 仅 S3
cp "$SCR/frozen.json" "$M"
backend/.venv/bin/python -c 'import json,sys;m=json.load(open(sys.argv[1]));m["signoff"]={"status":"approved"};json.dump(m,open(sys.argv[1],"w"),ensure_ascii=False,indent=2)' "$M"
backend/.venv/bin/python backend/scripts/validate_release_manifest.py "$M"; echo "rc=$?"      # [4] 仅 signoff
cp "$SCR/frozen.json" "$M"; shasum -a 256 "$M"                                                # 应回 866983aa…
```
