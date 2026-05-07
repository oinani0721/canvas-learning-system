---
story: "11.4"
title: "multiplatform-release-autoupdate"
status: "backlog"
version: "v1.0"
date: "2026-05-07"
developer: "TBD（Day 19 启动）"
commit: "TBD"
---

# Story 11.4 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 11.4 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-11/11-4-multiplatform-release-autoupdate.md`。

> [!warning]+ 此 Story 处于 backlog
> 前置：Story 11.3 完成。Day 19-22 执行。**Epic-11 收官 Story**。

---

## 🎯 这个 Story 要做到什么

在官网下载应用安装一次，之后有新版本时自动通知和更新。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 安装一次 DeepTutor Desktop App 后自动收到新版本更新通知，
**以便** 不用手动去官网下载新版本（像手机 App 一样）。

---

## 🖥️ 你会看到的交互（一步一步）

**初次安装**：
```
1. 访问 DeepTutor 官网（GitHub Releases 页）
       ↓
2. 看到下载选项：macOS / Windows / Linux
       ↓
3. 选择你的系统，下载对应文件（.dmg / .exe / .AppImage）
       ↓
4. 双击安装，完毕
```

**自动更新**：
```
1. 一周后，发布新版本 v0.2.0
       ↓
2. 打开应用
       ↓
3. 弹出对话框：
   "新版本可用: v0.2.0
    当前版本: v0.1.0
    [立即更新] [稍后提醒] [不再提示]"
       ↓
4. 点击"立即更新"
       ↓
5. UI 显示下载进度（"下载中... 45%"）
       ↓
6. 下载完毕，自动安装
       ↓
7. 提示"更新完成"或自动重启
       ↓
8. 应用重启，看到新版本号
```

---

## ✅ 验收清单（17 步 UAT — 跨平台 + 自动更新）

### 第 0 步：前置

- [ ] Story 11.1 + 11.2 + 11.3 已通过
- [ ] GitHub 仓库 oinani0721/DeepTutor 已配置 Secrets
- [ ] Apple Developer Team ID + 证书已就绪

### 第 1 步：CI/CD 触发

- [ ] 推送 git tag `v0.2.0`（开发者操作）
- [ ] GitHub Actions 自动触发 build workflow
- [ ] 3 个 build job（mac / windows / linux）平行启动

### 第 2 步：macOS 构建 + 签名 + Notarization

- [ ] mac job 完成（输出 DeepTutor-0.2.0.dmg）
- [ ] notarize job 自动跑（10-15 min）
- [ ] notarytool history 显示 "Accepted"
- [ ] staple 凭证添加成功

### 第 3 步：Windows 构建

- [ ] windows job 完成（输出 DeepTutor-0.2.0.exe）
- [ ] 代码签名（如有证书）

### 第 4 步：Linux 构建

- [ ] linux job 完成（输出 DeepTutor-0.2.0.AppImage）

### 第 5 步：GitHub Release 创建

- [ ] Releases 页面看到 v0.2.0 release
- [ ] 包含 3 个文件（dmg / exe / AppImage）
- [ ] Release notes 自动生成

### 第 6 步：macOS 安装验收

- [ ] 下载 .dmg
- [ ] 双击 .dmg 打开
- [ ] 拖到 Applications 文件夹
- [ ] **关键**: gatekeeper 校验通过（**无**"未识别开发者"警告）
- [ ] 应用启动正常

### 第 7 步：Windows 安装验收

- [ ] 下载 .exe
- [ ] 双击运行 → 安装向导
- [ ] 完成安装，应用启动
- [ ] Windows Defender 不报警（如有签名）

### 第 8 步：Linux 安装验收

- [ ] 下载 .AppImage
- [ ] `chmod +x DeepTutor-*.AppImage`
- [ ] `./DeepTutor-*.AppImage` 启动
- [ ] 应用正常

### 第 9 步：自动更新检查（首次）

- [ ] 安装 v0.1.0（旧版本）
- [ ] 启动应用
- [ ] 自动检查更新（应用内）
- [ ] 弹出 "新版本可用 v0.2.0" 对话框
- [ ] 显示当前版本 + 新版本 + Release notes

### 第 10 步：手动检查更新

- [ ] 菜单 → 关于 / Help → "检查更新"
- [ ] 立即触发检查
- [ ] 显示结果（有/无新版本）

### 第 11 步：下载更新

- [ ] 点击"立即更新"按钮
- [ ] UI 显示下载进度条
- [ ] 进度从 0% → 100%
- [ ] 下载速度合理（不卡）

### 第 12 步：安装 + 重启

- [ ] 下载完毕，自动开始安装
- [ ] 安装完毕，弹出"立即重启"或自动重启
- [ ] 应用重启
- [ ] 关于菜单显示新版本号 v0.2.0

### 第 13 步：稍后提醒

- [ ] 收到更新通知后点击"稍后提醒"
- [ ] 对话框关闭，应用正常使用
- [ ] 下次启动时再次提醒

### 第 14 步：不再提示

- [ ] 点击"不再提示"
- [ ] 当前版本不再弹通知（直到更新版本发布）

### 第 15 步：降级保护

- [ ] 安装 v0.2.0
- [ ] 假设 GitHub Releases 仍有旧 v0.1.0
- [ ] 应用不会建议降级到 v0.1.0

### 第 16 步：边界

- [ ] 网络断开时检查更新 → 友好错误提示
- [ ] 下载中断（关闭应用）→ 下次启动重新下载
- [ ] 多平台版本号一致（macOS / Windows / Linux 同步）

---

## 🚦 验收结果

**全部 ✅** → 说 "**Story 11.4 通过**" → Epic-11 完成 → 进入 Day 23+ 用户 UAT

**有 ❌** → 批注区记录

---

## 📝 你的批注区

> [!question]+ 你对 Story 11.4 的批注
>
> （空）

### 已知的已批注问题

（空）

---

## 🔗 技术 spec 参考

- **Story spec**: `_bmad-output/implementation-artifacts/epic-11/11-4-multiplatform-release-autoupdate.md`
- **决策批注**: `_bmad-output/决策批注/D18-desktop-app-electron-2026-05-07.md`
- **调研报告**: `_bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md` §四
- **CI/CD**: `.github/workflows/build-and-release.yml`
- **electron-builder 配置**: `desktop/electron-builder.yml`
- **Releases 页**: https://github.com/oinani0721/DeepTutor/releases
- **Apple Notarization**: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
- **Git commit**: TBD
- **AC → 代码对应**:
  - AC #1 → `.github/workflows/build-and-release.yml` (3 jobs)
  - AC #2 → workflow `notarize-mac` step
  - AC #3 → `desktop/src/main/main.ts` (autoUpdater integration)
  - AC #4 → electron-updater 内置 + UI dialog
  - AC #5 → electron-updater 默认行为

---

## 下一步

1. **通过** → Epic-11 完成，进入 Day 23+ 用户 UAT 验收 + Round-23 启动
2. **不通过** → correct-course
