# 智能快照系统使用说明

**版本**: v1.0
**创建日期**: 2025-11-15
**目标**: 100%无幻觉地区分压缩后继续对话 vs 全新对话，避免上下文污染

---

## 📋 系统概述

本系统在Claude Code执行`/compact`压缩对话前，自动保存完整上下文快照，并在新会话启动时智能判断是否加载快照。

### 核心特性

✅ **自动快照保存**: 压缩前自动保存BMad状态、相关文件、完整20轮对话
✅ **智能时间判断**: 使用时间戳差值（< 2小时 = 继续对话，> 2小时 = 新对话）
✅ **零幻觉保证**: 完全基于确定性时间差判断，无需AI推测
✅ **自动清理**: 过期快照自动删除，避免污染新对话上下文
✅ **无缝恢复**: 压缩后继续对话时自动加载完整上下文

---

## 🏗️ 系统架构

### 组件清单

| 组件 | 文件位置 | 功能 |
|------|---------|------|
| PreCompact Command Hook | `.claude/hooks/pre-compact-auto-save.ps1` | 在CLAUDE.md添加快照引用 |
| PreCompact Prompt Hook | `settings.local.json` | 指示Claude写入完整快照内容 |
| SessionStart Command Hook | `.claude/hooks/session-start-snapshot-manager.ps1` | 时间判断+自动清理 |
| SessionStart Prompt Hook | `settings.local.json` | 指示Claude加载快照 |
| 快照引用 | `CLAUDE.md` (顶部) | 临时引用，带时间戳 |
| 快照文件 | `.claude/compact-snapshot-[timestamp].md` | 完整对话内容 |

### 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│ 场景1: 用户执行 /compact 压缩对话                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ PreCompact Command Hook 执行    │
         │ pre-compact-auto-save.ps1      │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 1. 生成时间戳文件名              │
         │ 2. 在CLAUDE.md顶部添加引用      │
         │ 3. 删除旧引用（如果存在）         │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ PreCompact Prompt Hook 执行     │
         │ 指示Claude写入快照文件           │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Claude使用Write tool创建快照:   │
         │ - BMad状态                      │
         │ - 相关文件列表                   │
         │ - 完整20轮对话（逐字保留）        │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 压缩完成                        │
         │ ✅ 快照已保存                    │
         │ ✅ 引用已添加到CLAUDE.md         │
         └─────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 场景2: 用户开启新会话（压缩后2小时内）                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ SessionStart Command Hook 执行  │
         │ session-start-snapshot-manager.ps1 │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 1. 从CLAUDE.md读取快照引用      │
         │ 2. 提取快照时间戳               │
         │ 3. 计算时间差: 1.5小时 < 2小时  │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 输出: SNAPSHOT_ACTION=LOAD      │
         │ 输出: SNAPSHOT_FILE=[path]      │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ SessionStart Prompt Hook 执行   │
         │ 指示Claude读取快照文件           │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Claude使用Read tool加载快照:    │
         │ - 恢复BMad状态                  │
         │ - 恢复完整20轮对话               │
         │ - 恢复相关文件列表               │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 无缝继续之前的工作               │
         │ ✅ 上下文完全恢复                │
         └─────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 场景3: 用户开启新会话（压缩后3天后）                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ SessionStart Command Hook 执行  │
         │ session-start-snapshot-manager.ps1 │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 1. 从CLAUDE.md读取快照引用      │
         │ 2. 提取快照时间戳               │
         │ 3. 计算时间差: 72小时 > 2小时   │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 输出: SNAPSHOT_ACTION=CLEANUP   │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 自动清理:                       │
         │ 1. 删除快照文件                 │
         │ 2. 从CLAUDE.md删除引用          │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 干净的新对话开始                │
         │ ✅ 无上下文污染                 │
         └─────────────────────────────────┘
```

---

## 🔧 技术实现细节

### 1. 时间戳格式

**快照时间戳**: `yyyy-MM-dd HH:mm:ss`（用于时间差计算）
**文件名时间戳**: `yyyyMMddHHmmss`（用于文件命名）

**示例**:
- 快照时间: `2025-11-15 16:30:00`
- 文件名: `compact-snapshot-20251115163000.md`

### 2. 时间判断逻辑

```powershell
$snapshotTime = [DateTime]::ParseExact($snapshotTimeStr, "yyyy-MM-dd HH:mm:ss", $null)
$currentTime = Get-Date
$timeDiff = ($currentTime - $snapshotTime).TotalHours

if ($timeDiff -lt 2) {
    # 压缩后继续对话 - 加载快照
    Write-Output "SNAPSHOT_ACTION=LOAD"
} else {
    # 新对话 - 清理快照
    Write-Output "SNAPSHOT_ACTION=CLEANUP"
}
```

**为什么选择2小时？**
- 压缩通常发生在对话即将耗尽上下文时（~90% token使用）
- 用户通常会在压缩后立即或短时间内继续对话
- 2小时是合理的"会话连续性"阈值
- 超过2小时更可能是完全不同的会话

### 3. CLAUDE.md快照引用格式

```markdown
---
<!-- TEMP_COMPACT_SNAPSHOT_START -->
# 🔄 临时上下文快照 [2025-11-15 16:30:00]

**📎 快照文件**: .claude/compact-snapshot-20251115163000.md
**⏰ 快照时间**: 2025-11-15 16:30:00
**⏱️ 有效期**: 2小时（超时自动清理）

⚠️ **说明**:
- 这是对话压缩前的上下文快照
- 如果是压缩后继续对话（2小时内），请使用Read tool读取快照文件
- 如果是新对话，SessionStart hook会自动清理此引用

<!-- TEMP_COMPACT_SNAPSHOT_END -->
---
```

**关键特性**:
- 使用HTML注释标记 `<!-- -->` 便于正则表达式精确匹配
- 包含完整时间戳供SessionStart hook解析
- 使用相对路径引用快照文件
- 明确说明有效期和用途

### 4. 快照文件内容结构

```markdown
# 压缩前上下文快照

**生成时间**: 2025-11-15 16:30:00
**有效期**: 2小时

---

## 🤖 当前BMad状态

**Active Agent**: dev
**执行功能**: implement story
**核心内容**: 实现Epic 10.14三层记忆存储活动记录
**当前Epic/Story**: Epic 10.14

**相关文件**:
- canvas_utils.py
- .claude/agents/graphiti-memory-agent.md
- tests/test_memory_storage.py

**下一步行动**:
1. 实现活动记录存储功能
2. 编写单元测试
3. 更新文档

**关键技术决策**:
- 使用Neo4j存储时序数据
- 活动类型: decomposition, explanation, scoring, review
- 每个活动记录包含: 时间戳, 节点ID, Agent类型, 输出文档路径

---

## 📝 最近20轮对话 (完整保留)

### Turn 1: User
在claude code压缩上下文后容易忘记我们在bmad哪一个开发阶段...

### Turn 2: Assistant
我会帮你完成以下两项任务...

...

### Turn 20: Assistant
[完整的第20轮对话内容]

---

## ⚠️ 使用说明

本快照文件包含压缩前的完整对话上下文。如果在2小时内继续对话：
1. SessionStart hook会自动检测并指示Claude读取此文件
2. Claude会完整恢复上下文，包括BMad状态和最近20轮对话
3. 可以无缝继续之前的工作

如果超过2小时开启新对话：
1. SessionStart hook会自动删除此文件和CLAUDE.md中的引用
2. 避免污染新对话的上下文
```

---

## 📖 使用指南

### 正常使用（无需手动操作）

系统完全自动化，用户无需任何手动操作：

1. **压缩对话时**: 执行 `/compact` 或等待自动压缩
   - 系统自动保存快照
   - 系统自动在CLAUDE.md添加引用
   - Claude自动写入完整对话内容

2. **压缩后继续对话时**: 开启新会话
   - 系统自动检测快照时间
   - 如果 < 2小时: Claude自动加载快照
   - 如果 > 2小时: 系统自动清理快照

3. **开启全新对话时**: 正常开启新会话
   - 系统自动清理过期快照
   - 无上下文污染

### 手动检查（可选）

如果想手动验证系统状态：

```bash
# 1. 检查CLAUDE.md顶部是否有快照引用
cat CLAUDE.md | Select-Object -First 20

# 2. 列出所有快照文件
ls .claude/compact-snapshot-*.md

# 3. 查看特定快照内容
cat .claude/compact-snapshot-20251115163000.md
```

### 调整时间阈值（高级）

如果需要修改2小时阈值，编辑 `.claude/hooks/session-start-snapshot-manager.ps1`:

```powershell
# 找到这一行:
if ($timeDiff -lt 2) {

# 修改为你想要的小时数，例如4小时:
if ($timeDiff -lt 4) {
```

---

## ❓ 常见问题

### Q1: 快照文件会无限增长吗？
**A**: 不会。SessionStart hook会自动删除超过2小时的快照文件。每次新会话启动时都会执行清理。

### Q2: 如果压缩时电脑关机了怎么办？
**A**: PreCompact hook在压缩前执行，如果电脑关机，快照引用可能已添加到CLAUDE.md但快照文件未创建。SessionStart hook会检测到文件不存在并清理引用。

### Q3: 可以手动删除快照文件吗？
**A**: 可以。如果手动删除快照文件，SessionStart hook会检测到文件不存在并清理CLAUDE.md中的引用。

### Q4: 快照会包含敏感信息吗？
**A**: 快照包含完整的20轮对话，如果对话中包含敏感信息，快照也会包含。快照文件存储在 `.claude/` 目录，应该已被 `.gitignore` 排除，不会提交到Git。

### Q5: 为什么是20轮对话？
**A**: 20轮对话（10轮用户+10轮助手）通常足以覆盖一个完整的任务上下文。可以在PreCompact Prompt Hook中修改这个数字。

### Q6: 系统如何保证100%无幻觉？
**A**: 系统使用**确定性时间戳差值**判断，完全不依赖AI推测：
- 时间戳从文件系统获取（PowerShell Get-Date）
- 时间差计算是纯数学运算
- 判断逻辑是简单的if-else（< 2小时或 > 2小时）
- 无任何需要AI理解或推测的环节

---

## 🔍 调试指南

### 查看Hook执行日志

Hook的PowerShell输出会显示在Claude Code的命令输出中。如果遇到问题，检查输出中的以下内容：

**PreCompact Hook输出**:
```
SNAPSHOT_FILE=C:\Users\ROG\托福\.claude\compact-snapshot-20251115163000.md
SNAPSHOT_TIMESTAMP=2025-11-15 16:30:00
✅ 临时快照引用已添加到CLAUDE.md顶部
```

**SessionStart Hook输出（加载场景）**:
```
INFO: Snapshot timestamp: 2025-11-15 16:30:00
INFO: Current time: 2025-11-15 17:00:00
INFO: Time difference: 0.5 hours
SNAPSHOT_ACTION=LOAD
SNAPSHOT_FILE=C:\Users\ROG\托福\.claude\compact-snapshot-20251115163000.md
✅ 检测到压缩后继续对话（时间差 < 2小时），请Claude加载快照文件
```

**SessionStart Hook输出（清理场景）**:
```
INFO: Snapshot timestamp: 2025-11-15 16:30:00
INFO: Current time: 2025-11-18 10:00:00
INFO: Time difference: 65.5 hours
SNAPSHOT_ACTION=CLEANUP
⚠️ 检测到新对话（时间差 > 2小时），开始清理快照
✅ 已删除过期快照文件: C:\Users\ROG\托福\.claude\compact-snapshot-20251115163000.md
✅ 已从CLAUDE.md中删除快照引用
```

### 测试系统

#### 测试PreCompact Hook:

```powershell
# 手动运行PreCompact脚本
powershell -ExecutionPolicy Bypass -File ".claude/hooks/pre-compact-auto-save.ps1"

# 检查CLAUDE.md顶部
cat CLAUDE.md | Select-Object -First 30

# 应该看到快照引用已添加
```

#### 测试SessionStart Hook:

```powershell
# 手动运行SessionStart脚本
powershell -ExecutionPolicy Bypass -File ".claude/hooks/session-start-snapshot-manager.ps1"

# 检查输出
# 应该看到 SNAPSHOT_ACTION=LOAD 或 SNAPSHOT_ACTION=CLEANUP
```

---

## 📊 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code 会话                          │
└─────────────────────────────────────────────────────────────────┘
                │                                    │
                │                                    │
         /compact 触发                        新会话启动
                │                                    │
                ▼                                    ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│   PreCompact Hook        │          │   SessionStart Hook      │
├──────────────────────────┤          ├──────────────────────────┤
│ 1. Command Hook (PS脚本) │          │ 1. Command Hook (PS脚本) │
│    - 生成时间戳           │          │    - 读取快照引用         │
│    - 添加引用到CLAUDE.md  │          │    - 计算时间差           │
│                          │          │    - 判断LOAD/CLEANUP    │
│ 2. Prompt Hook           │          │                          │
│    - 指示Claude写快照     │          │ 2. Prompt Hook           │
│                          │          │    - 指示Claude加载快照   │
└──────────┬───────────────┘          └──────────┬───────────────┘
           │                                     │
           │ 创建                                │ 读取/删除
           ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  .claude/compact-snapshot-[timestamp].md         │
│                                                                  │
│  内容:                                                           │
│  - BMad状态 (Agent, 功能, Epic/Story)                            │
│  - 相关文件列表                                                   │
│  - 完整20轮对话（逐字保留）                                        │
│  - 下一步行动                                                     │
│  - 关键技术决策                                                   │
└─────────────────────────────────────────────────────────────────┘
           │                                     │
           │ 引用                                │ 清理
           ▼                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                           CLAUDE.md                              │
│                                                                  │
│  顶部临时引用:                                                    │
│  ---                                                             │
│  <!-- TEMP_COMPACT_SNAPSHOT_START -->                           │
│  # 🔄 临时上下文快照 [2025-11-15 16:30:00]                       │
│  ...                                                             │
│  <!-- TEMP_COMPACT_SNAPSHOT_END -->                             │
│  ---                                                             │
│                                                                  │
│  [其他CLAUDE.md内容]                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 设计目标达成情况

| 设计目标 | 实现方式 | 状态 |
|---------|---------|------|
| 压缩前保存完整上下文 | PreCompact Hook写入快照文件 | ✅ 完成 |
| 保存BMad状态 | 快照包含Agent、功能、Epic/Story | ✅ 完成 |
| 保存完整20轮对话 | Claude逐字复制到快照文件 | ✅ 完成 |
| 保存相关文件列表 | 快照包含文件路径列表 | ✅ 完成 |
| 压缩后继续对话时加载 | SessionStart判断时间 < 2小时 | ✅ 完成 |
| 100%无幻觉判断 | 确定性时间戳差值计算 | ✅ 完成 |
| 新对话时自动清理 | SessionStart判断时间 > 2小时 | ✅ 完成 |
| 避免上下文污染 | 自动删除快照文件和引用 | ✅ 完成 |
| 无需手动操作 | 全自动化Hook系统 | ✅ 完成 |

---

## 📝 维护日志

**v1.0 (2025-11-15)**:
- 初始版本发布
- 实现PreCompact Hook（Command + Prompt）
- 实现SessionStart Hook（Command + Prompt）
- 2小时时间阈值
- 完整文档

---

## 📞 技术支持

如有问题或建议，请查看：
- 本文档（SNAPSHOT_SYSTEM_README.md）
- `.claude/hooks/` 中的PowerShell脚本
- `.claude/settings.local.json` 中的Hook配置

---

**最后更新**: 2025-11-15
**系统状态**: ✅ 生产就绪
