---
story: "11.2"
title: "ipc-bridge-fastapi-subprocess"
status: "backlog"
version: "v1.0"
date: "2026-05-07"
developer: "TBD（Day 13 启动）"
commit: "TBD"
---

# Story 11.2 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 11.2 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-11/11-2-ipc-bridge-fastapi-subprocess.md`。

> [!warning]+ 此 Story 处于 backlog
> 前置：Story 11.1 完成。Day 13 启动。

---

## 🎯 这个 Story 要做到什么

应用可以自动启动 AI 引擎，并通过内部通道和它通信，读写你的笔记文件。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 应用启动时自动准备好 AI 引擎 + 让我选择笔记本位置，
**以便** 之后所有操作都在我的本地文件夹进行（不上传云端）。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 打开应用
       ↓
2. 弹出"选择笔记本位置"对话框
       ↓
3. 点击"浏览文件夹"按钮
       ↓
4. 在文件系统选择一个文件夹（含 .md 文件）
       ↓
5. 点击"确定"
       ↓
6. 对话框关闭
       ↓
7. 应用正常加载（UI 显示）
       ↓
8. 在应用中编辑笔记 → 本地文件自动更新
```

---

## ✅ 验收清单（13 步 UAT）

> [!tip]+ 怎么用
> 每跑完一步打勾。问题用 `Cmd+Shift+A` 批注。

### 第 0 步：前置

- [ ] Story 11.1 已通过（Desktop App 可启动）
- [ ] 准备一个测试 vault 文件夹（含至少 3 个 .md 文件）

### 第 1 步：首次启动 + Vault 选择

- [ ] 打开应用，弹出"选择笔记本"对话框
- [ ] 对话框有清晰的说明文字
- [ ] 有"浏览文件夹"按钮和"取消"按钮
- [ ] 点击"浏览文件夹" → 弹出系统文件选择对话框

### 第 2 步：选定 Vault 后行为

- [ ] 选择一个文件夹后，对话框关闭
- [ ] 应用 UI 正常加载（导航栏 + 内容区可见）
- [ ] 应用记住这个 vault 路径（关闭重开仍记得）

### 第 3 步：AI 引擎运行验证

- [ ] 任务管理器查看：除了 Electron 主进程，还有一个 Python 进程（AI 引擎）
- [ ] 应用界面响应灵敏（说明 IPC 通信正常）
- [ ] 没有报错弹窗

### 第 4 步：读取笔记

- [ ] 在 vault 中找到一个已有的 .md 文件
- [ ] 在应用中打开它（通过 wikilink 跳转或文件浏览）
- [ ] 内容显示正确（与 Obsidian 中看到的一致）

### 第 5 步：写入笔记

- [ ] 在应用中编辑一个 .md 文件，加一段文字
- [ ] 保存
- [ ] 用 Finder / 文件管理器检查本地 .md 文件 → 内容已更新

### 第 6 步：实时同步

- [ ] 在 Obsidian / VS Code 中修改同一个 .md 文件
- [ ] 不到 1 秒，应用内的内容自动刷新
- [ ] 不需要手动刷新页面

### 第 7 步：网络隔离测试

- [ ] 关闭 WiFi / 拔网线
- [ ] 应用仍能读写笔记（FastAPI subprocess 本地）
- [ ] 用网络监控工具确认无外网请求

### 第 8 步：AI 引擎崩溃恢复

- [ ] 如果 Python 进程意外崩溃（手动 kill 测试）
- [ ] 应用界面弹出 toast 提示"Backend recovering..."
- [ ] 几秒后弹出 "Backend online"
- [ ] 功能恢复正常

### 第 9 步：关闭应用

- [ ] 关闭应用 → AI 引擎进程也自动退出
- [ ] 任务管理器检查 → 没有僵尸 Python 进程

### 第 10 步：边界测试

- [ ] 选择空文件夹（无 .md）→ 提示"vault 必须含 markdown 文件"
- [ ] 选择只读文件夹 → 提示无写入权限
- [ ] vault 路径含中文/空格 → 正常工作

---

## 🚦 验收结果

**如果所有步骤 ✅**：说 "**Story 11.2 通过**"。

**如果有 ❌**：批注区写明问题。

---

## 📝 你的批注区

> [!question]+ 你对 Story 11.2 的批注
>
> （空）

### 已知的已批注问题（历史追溯）

（空）

---

## 🔗 技术 spec 参考

- **Story spec**: `_bmad-output/implementation-artifacts/epic-11/11-2-ipc-bridge-fastapi-subprocess.md`
- **关联 Story**: `epic-10/10-3-day2-cleanup-vault-mount.md`（Phase B vault 直读）
- **决策批注**: `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md`
- **调研报告**: `_bmad-output/research/round-22-day2-vault-access-design-2026-05-06.md`
- **源代码**:
  - Electron main: `desktop/src/main/main.ts`（subprocess spawner）
  - Renderer IPC: `desktop/src/renderer/ipc-client.ts`
  - FastAPI router: `deeptutor/api/routers/vault_ops.py`
- **Git commit**: TBD
- **AC → 代码对应**:
  - AC #1 → `main.ts` `spawnFastAPIServer()`
  - AC #2 → `main.ts` `startHealthCheck()`
  - AC #3 → `VaultSelectorModal.tsx`
  - AC #4 → `ipc-client.ts` 5 functions + `vault_ops.py` 4 endpoints
  - AC #5 → 网络监控 + tcpdump 验证

---

## 下一步

1. **通过** → Story 11.3（Vault 深度集成 + 渲染验证 — Math Animator + Visualize 内嵌）
2. **不通过** → correct-course
