# Canvas Learning System - Claude Code Instructions

## 🚨 部署关键路径 (必读)

### Obsidian 插件部署

**构建输出**: `canvas-progress-tracker/obsidian-plugin/main.js`

| 位置 | 路径 | 状态 |
|------|------|------|
| **正确目标** | `C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\` | ✅ 使用此路径 |
| **错误位置** | `C:\Users\ROG\托福\笔记库\.obsidian\plugins\canvas-review-system\` | ❌ 旧版本，勿用 |

### 部署检查清单

```powershell
# 1. 构建插件
cd canvas-progress-tracker/obsidian-plugin && npm run build

# 2. 复制到正确位置 (注意路径!)
Copy-Item main.js "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\" -Force
Copy-Item manifest.json "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\" -Force

# 3. 验证部署 (main.js 应 >= 520KB)
Get-Item "C:\Users\ROG\托福\Canvas\笔记库\.obsidian\plugins\canvas-review-system\main.js"

# 4. 重启 Obsidian 加载新插件
```

### 后端服务

- **位置**: `backend/app/services/`
- **启动**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **端口**: **8000** (统一配置，前后端一致)

---

## 项目结构

```
C:\Users\ROG\托福\
├── Canvas/                              # 主项目 Git仓库
│   ├── backend/                         # FastAPI后端
│   │   └── app/services/                # 所有服务实现
│   ├── canvas-progress-tracker/         # Obsidian插件源码
│   │   └── obsidian-plugin/
│   │       └── main.js                  # 构建输出 (部署源)
│   ├── 笔记库/                          # ✅ 正确的Obsidian Vault
│   │   └── .obsidian/plugins/
│   │       └── canvas-review-system/    # 插件部署目标
│   └── CLAUDE.md                        # 本文件
│
└── 笔记库/                              # ❌ 旧的Vault (勿用)
    └── .obsidian/plugins/
        └── canvas-review-system/        # 过期插件
```

---

## Context Snapshot System

<!-- TEMP_COMPACT_SNAPSHOT_START -->
# Context Snapshot [2025-12-15 04:03:30]

**Snapshot File**: .claude/compact-snapshot-20251215040330.md
**Snapshot Time**: 2025-12-15 04:03:30
**Valid For**: 2 hours (auto-cleanup after expiration)

**Note**:
- This is a context snapshot before conversation compression
- Snapshot was automatically filled by PreCompact hook (PowerShell transcript parsing)
- If continuing conversation after compression (within 2 hours), use Read tool to load snapshot file
- If starting new conversation, SessionStart hook will automatically clean up this reference

<!-- TEMP_COMPACT_SNAPSHOT_END -->
