---
story_id: "11.4"
epic_id: "11"
prd_id: "canvas-learning-system"
status: "backlog"
priority: "P1"
estimate_hours: 24
depends_on: ["11.3"]
blocks: []
trace: ["FR-DEEP-06"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 19-22"
target_date: "2026-05-25 ~ 2026-05-28"
uat_sheet: "_bmad-output/验收单/Story-11.4-multiplatform-release-autoupdate.md"
---

# Story 11.4: 跨平台发布 + 自动更新

**Status**: backlog（target Day 19-22, 2026-05-25 ~ 2026-05-28）

## Story（用户故事）

As a 学习者, I want to download and install DeepTutor Desktop App once, and then receive automatic update notifications when new versions are released so that I always have the latest features and bug fixes without manual intervention.

> **映射对**: NEG-3（Web/Desktop 双轨并存）+ Round-22 备选 A（Path A 后续投入"月度 release"）

## 通俗化解释（给学习者）

> **一句话说**: 你在 DeepTutor 官网下载一次 Desktop App，之后有新版本时，App 会自动通知你"有更新可用"，点击更新按钮就能升级。就像手机 App 更新一样。

**你会遇到的场景**:
- 首次访问 DeepTutor 官网，看到"Download Desktop App" 按钮
- 选择你的系统（macOS / Windows / Linux）
- 下载对应的安装文件（.dmg / .exe / .AppImage）
- 双击安装，完毕
- 一周后，DeepTutor 发布新版本
- 你启动 Desktop App，弹出"新版本可用"通知
- 点击"立即更新" → 自动下载 → 自动安装 → 重启应用
- 升级完成，享受新功能

**这个功能帮你**:
- 不用手动去官网下载新版本
- 更新无缝进行，不中断你的工作（后台下载，空闲时安装）

**用个比喻**: 📱 就像手机 App Store 自动推送更新——你只管用，app 自己保持最新。

## Acceptance Criteria

### AC #1: 3 平台安装包生成

- **Given** GitHub Actions workflow 配置完成
- **When** 推送 git tag（格式 `v0.2.0`）
- **Then** CI/CD 并行构建 3 个平台：
  - **macOS**: `DeepTutor-0.2.0.dmg` + 代码签名 + notarization
  - **Windows**: `DeepTutor-0.2.0.exe` + 可选代码签名
  - **Linux**: `DeepTutor-0.2.0.AppImage`
- **And** 3 个文件都上传到 GitHub Releases

### AC #2: macOS Apple notarization 完整链

- **Given** macOS .dmg 构建完毕，准备发布
- **When** CI 执行 notarization workflow
- **Then** 自动上传到 Apple notary 服务（via `xcrun notarytool`）
- **And** 等待 Apple 审核（~5-10 min）
- **And** 审核通过后，自动添加 staple 信息
- **And** 最终 .dmg 用户下载后，gatekeeper 验证通过（无警告）

### AC #3: electron-updater 自动检测 + 通知

- **Given** Desktop App 运行中
- **When** 每次应用启动，自动检查更新
- **Then** electron-updater 从 GitHub Releases 拉取最新 release metadata
- **And** 对比当前版本，若有新版本则弹出 dialog：版本号 + Release notes + "立即更新" / "稍后提醒" / "不再提示"

### AC #4: 自动下载 + 安装 + 重启

- **Given** 用户点击"立即更新"
- **When** electron-updater 开始下载新版本
- **Then** UI 显示下载进度条（"下载中... 45%"）
- **And** 下载完毕，自动开始安装（replace old files）
- **And** 安装完毕，弹出"更新成功，立即重启?"或自动重启

### AC #5: 更新降级保护（只升级，不降级）

- **Given** 用户运行 v0.2.0，但本地 Release 包含 v0.1.0
- **When** 检查更新
- **Then** 自动忽略 v0.1.0
- **And** 不会询问用户是否降级

### AC #6: macOS App Sandbox entitlements 完整配置（2026-05-07 5 Agent 调研补全）

> **背景**：Story 11.2 AC #6 + Task 4d 实现 security-scoped bookmarks 是 App Store 发布前提，但 entitlements.mac.plist + electron-builder hardenedRuntime + notarize 的协同配置必须在本 Story 完成。Agent 3 实测：未配置 entitlements 时 App Store 审核会拒绝（"App Sandbox not enabled"），且重启后 bookmark 失效。

- **Given** Story 11.2 已实现 dialog `securityScopedBookmarks: true` + `app.startAccessingSecurityScopedResource(bookmark)`
- **When** Story 11.4 配置 electron-builder mac entitlements
- **Then** 项目根目录创建 `build/entitlements.mac.plist`，含三个关键 key：
  ```xml
  <plist version="1.0"><dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
  </dict></plist>
  ```
  - `com.apple.security.app-sandbox=true` — 启用 App Sandbox（App Store 必需）
  - `com.apple.security.files.user-selected.read-write=true` — 用户通过 dialog 选的文件夹有读写权（搭配 securityScopedBookmarks 持久化）
  - `com.apple.security.network.client=true` — 允许调用 Claude API + Docker localhost（127.0.0.1 也算 client）
- **And** electron-builder.yml 配置：
  ```yaml
  mac:
    entitlements: build/entitlements.mac.plist
    entitlementsInherit: build/entitlements.mac.plist
    hardenedRuntime: true
    gatekeeperAssess: false
    notarize:
      teamId: ${APPLE_TEAM_ID}
  ```
- **And** Mac App Store 发布路径（可选）：另写 `build/entitlements.mas.plist`（含 `com.apple.security.app-sandbox` 必填 + 不含 `com.apple.security.network.server`），electron-builder `mac.target: mas` 触发
- **And** notarize 完成后 `xcrun stapler validate DeepTutor.app` 验证 staple 成功
- **And** 用户首次安装后跑：选 vault → 退出 app → 重启 app → vault **仍可访问**（bookmark restore 成功）；如失败说明 entitlements 配置错

## Tasks / Subtasks

### electron-builder 配置

- [ ] Task 1: 完善 electron-builder.yml
  - [ ] 1.1: 全局配置：`appId`, `productName`, `directories`
  - [ ] 1.2: macOS 配置（`mac:`）：signingIdentity / certificateFile / notarize
  - [ ] 1.3: Windows 配置（`win:`）：certificateFile + signingHashAlgorithms
  - [ ] 1.4: Linux 配置（`linux:`）：target AppImage / category Utility
  - [ ] 1.5: macOS App Sandbox entitlements（AC #6 落地）
    - [ ] 1.5.1: 创建 `build/entitlements.mac.plist`（含 app-sandbox + files.user-selected.read-write + network.client 3 个 key）
    - [ ] 1.5.2: electron-builder.yml `mac.entitlements` 指向 plist 路径 + `mac.entitlementsInherit` 同
    - [ ] 1.5.3: 启用 `mac.hardenedRuntime: true`（notarize 前置）
    - [ ] 1.5.4: 验证 `codesign -d --entitlements - DeepTutor.app/Contents/MacOS/DeepTutor` 输出含 3 个 key
    - [ ] 1.5.5: （可选）创建 `build/entitlements.mas.plist` 用于 Mac App Store 路径（`mac.target: mas`），不含 network.server

- [ ] Task 2: GitHub Secrets 配置
  - [ ] 2.1: macOS Secrets: APPLE_ID / APPLE_ID_PASSWORD / APPLE_TEAM_ID / CSC_LINK / CSC_KEY_PASSWORD
  - [ ] 2.2: Windows Secrets（可选）: WINDOWS_CODE_SIGN_CERT / WINDOWS_CODE_SIGN_PASSWORD

### GitHub Actions Workflow

- [ ] Task 3: 创建 .github/workflows/build-and-release.yml
  - [ ] 3.1: trigger: 推送 git tag（v*.*.*）时触发
  - [ ] 3.2: Jobs:
    - [ ] 3.2.1: **build-mac**: macOS runner 输出 .dmg
    - [ ] 3.2.2: **build-windows**: Windows runner 输出 .exe
    - [ ] 3.2.3: **build-linux**: Ubuntu runner 输出 .AppImage
    - [ ] 3.2.4: **notarize-mac**（depends-on build-mac）: 调用 Apple notary
    - [ ] 3.2.5: **create-release**（depends-on all）: 上传 3 文件到 Releases

- [ ] Task 4: GitHub Actions macOS 签名步骤
  - [ ] 4.1: "Prepare signing certificate": 从 CSC_LINK base64 decode 导入证书
  - [ ] 4.2: "Build Electron app": `npm run electron-build`
  - [ ] 4.3: "Notarize macOS app": `xcrun notarytool submit` + 轮询 + `xcrun stapler staple`

- [ ] Task 5: GitHub Actions Windows 签名步骤（可选）
  - [ ] 5.1: 如果 WINDOWS_CODE_SIGN_CERT 存在: 导入证书 + signtool 自动签名
  - [ ] 5.2: 否则跳过签名

### electron-updater 集成

- [ ] Task 6: 应用代码中集成 electron-updater
  - [ ] 6.1: 在 main.ts 导入 `autoUpdater` 和 `dialog`
  - [ ] 6.2: app ready 时调用 `autoUpdater.checkForUpdatesAndNotify()`
  - [ ] 6.3: 监听 `'update-available'` / `'update-downloaded'` 事件
  - [ ] 6.4: 菜单项"检查更新"手动触发

- [ ] Task 7: electron-updater 配置（package.json）
  - [ ] 7.1: 添加 `"build": { "publish": { "provider": "github", "owner": "oinani0721", "repo": "DeepTutor" } }`
  - [ ] 7.2: 添加 `"homepage": "https://github.com/oinani0721/DeepTutor"`

### Release 工作流

- [ ] Task 8: 版本管理 + Release notes 生成
  - [ ] 8.1: 更新 package.json version 字段（semver 格式）
  - [ ] 8.2: 创建 CHANGELOG.md 条目
  - [ ] 8.3: git commit + push
  - [ ] 8.4: 创建 git tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
  - [ ] 8.5: git push origin v0.2.0（触发 CI）

- [ ] Task 9: 监控 CI 流程
  - [ ] 9.1: 推送 tag 后，GitHub Actions 自动触发
  - [ ] 9.2: 监控 3 个 build job
  - [ ] 9.3: 等待 notarize job 完成（10-15 min）
  - [ ] 9.4: 检查 Releases 页面 3 个文件 + Release notes

### 验收测试

- [ ] Task 10: macOS 验收
  - [ ] 10.1: 下载 .dmg，双击安装
  - [ ] 10.2: 打开应用 → gatekeeper 不显示警告
  - [ ] 10.3: 验证"检查更新"功能

- [ ] Task 11: Windows 验收
  - [ ] 11.1: 下载 .exe，双击运行安装
  - [ ] 11.2: 启动应用，验证"检查更新"功能

- [ ] Task 12: Linux 验收
  - [ ] 12.1: 下载 .AppImage，chmod +x，运行
  - [ ] 12.2: 验证自动更新检查

- [ ] Task 13: 端到端更新测试
  - [ ] 13.1: 安装 v0.1.0
  - [ ] 13.2: CI 构建 v0.2.0，发布到 GitHub Releases
  - [ ] 13.3: 在 v0.1.0 应用中点击"检查更新"
  - [ ] 13.4: 验证检测到 v0.2.0 + 显示 release notes
  - [ ] 13.5: 点击"立即更新"，验证下载 → 安装 → 重启
  - [ ] 13.6: 验证重启后是 v0.2.0

## Dev Notes

### 关键决策
- **Apple notarization 流程**: 必须在 macOS runner 执行（`xcrun` 命令），Win/Linux 无法 notarize
- **Delta updates 优先级**: electron-updater 内置支持，Day 22 基础实现可不启用
- **版本字符串**: package.json 版本 = git tag = GitHub Release 版本
- **App Sandbox 决策（AC #6）**：默认启用（`com.apple.security.app-sandbox=true`），即使非 App Store 路径也启用，理由：(a) 与 Story 11.2 securityScopedBookmarks 一致 (b) 提升用户安全感 (c) 为未来 App Store 发布留余量。代价：DocumentAdder vault_mode 必须严格落实（NEG-2）— Sandbox 模式下不能逃出 user-selected 范围

### 跨平台 Dialog 行为差异（AC #6 落地，Story 11.2 Task 4e 协同）

| 维度 | macOS | Windows | Linux |
|---|---|---|---|
| Native dialog | NSOpenPanel（dialog API 自动调） | IFileDialog（Windows 10+） | GtkFileChooserNative |
| `properties: ['openDirectory']` | ✅ | ✅ | ✅ |
| `createDirectory: true` | ✅ dialog 内可建文件夹 | ❌ Windows 不支持（需引导用户先在 Explorer 建） | ❌ |
| `noResolveAliases: true` | ✅ macOS-only（防 symlink 逃逸） | n/a | n/a |
| `securityScopedBookmarks: true` | ✅ App Sandbox 必需 | n/a（Windows 直接路径访问） | n/a（Linux 直接路径访问） |
| `message` field | ✅ macOS-only（dialog 顶部副标题） | n/a | n/a |
| 默认 path | `~` (用户 home) | `C:\Users\X` | `~` |
| 重启 app 后访问 | 必须 `startAccessingSecurityScopedResource` | 直接 path 仍有效 | 直接 path 仍有效 |
| App 卸载后 bookmark | 自动失效（OS 清理） | n/a | n/a |

### 已知陷阱
1. **Apple Team ID vs Apple ID**: Team ID 是 10 字符码，Apple ID 是 email 地址
2. **App-specific password**: Apple ID 不能直接用密码，需生成 App-specific password
3. **notarytool vs altool**: 新版 macOS 用 notarytool，altool 已弃用
4. **Gatekeeper 缓存**: 首次运行可能仍显示"未识别开发者"，清除 xattr 或重启 Gatekeeper
5. **App Sandbox 启用后 Docker localhost 仍能通**: Docker 通信走 `127.0.0.1:8011/8001/3782/7691` localhost，App Sandbox 不阻止（`com.apple.security.network.client=true` 已开），但**不能 listen 端口**（不需要，Electron 是 client 不是 server）
6. **bookmark stale 的诊断**: 用户重命名 / 移动 vault 文件夹后 bookmark 失效，错误码 `NSURLBookmarkResolutionWithoutUI` 失败 → Story 11.2 Task 4d.5 处理
7. **electron-builder 的 entitlements 双指**: `mac.entitlements` 是 main app，`mac.entitlementsInherit` 是 child processes（如 GPU helper），两者通常一样
8. **Windows 无 entitlements 概念**: AC #6 仅 macOS 路径，Windows / Linux 不需要

### 风险
- **R1 macOS notarization 流程**: Day 19 提前申请开发者账号 + 测试 notarytool 流程
- **R5 Windows Defender 误报**: code signing + timestamp authority
- **R6（新）App Sandbox + Docker 兼容性**: Docker Desktop 在 macOS 启用 Sandbox 后仍能用 localhost socket，但若用户启用 firewall 可能阻断 → CI 验收测试 + 用户文档说明
- **R7（新）bookmark stale 的用户体验**: 用户首次重命名 vault 后 app 启动会黑屏（恢复访问失败）→ Task 4d.5 + UI fallback "Vault not found, please re-select" + Recent vaults 列表保留路径（让用户能直观看到原路径）

## UAT 验收

详见 `_bmad-output/验收单/Story-11.4-multiplatform-release-autoupdate.md`

## References

- Epic-11 _README §"Goals" Goal 3 + AC #5
- Round-22 Desktop 报告 §四（GitHub Actions CI/CD 完整设计）
- Apple Developer Notarization: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
- electron-builder: https://www.electron.build/

## 下一步

→ Day 23+ 用户 UAT 验收 + Round-23 启动
