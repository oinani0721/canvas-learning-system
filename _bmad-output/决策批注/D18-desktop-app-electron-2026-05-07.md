---
decision_ids: ["D18"]
status: "annotated"
date: "2026-05-07"
related_round: "round-22"
related_prd: "_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md"
related_research: "_bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md"
related_epic: "epic-11"
related_stories: ["11.1", "11.2", "11.3", "11.4"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
user_decision: "Path A 后桌面化：Electron + AnythingLLM 模式（59.7k ⭐ 商用先例）+ 12 天交付路线"
---

# D18: Round-22 Desktop App 桌面化决策（Path A 落地）

> **Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
> **Round**: 22（6 报告深度调研：fork MVP / Day 2 vault / Chat vs TutorBot / CLI/SDK/Book Engine / Desktop App / Deep Explore 10 Agent）
> **决策日期**: 2026-05-07
> **Epic 落地**: epic-11（Story 11.1-11.4）
> **关联决策**: D17（Round-22 主决策 - fork + 5 核心嵌入）

---

## 问题回顾：用户批注 Q3 深度探讨

**原问题**（CLI/SDK 深度探索报告 §五，用户 2026-05-07 批注）:
> "这两种 cli 和 sdk 是否可以渲染我们之前提到的 5 个 capability，能否 4 个完整保留出来 ... 那么我们能否使 web 入口实际是改造为本地的 desktop app（就像 claude code desktop 模式：GUI 渲染 + 调 CLI 操作文件）？"

**Round-22 调研答案**: ✅ 100% 可行

---

## 核心决策（D18）：Path A 桌面化路线 = Electron + AnythingLLM 模式

### D18.1 技术栈选定（Tauri vs Electron）

**对比 2 个候选方案**:

| 维度 | Tauri 2.0 | Electron + AnythingLLM 模式 |
|---|---|---|
| **包大小** | 5-10 MB（轻量优势） | 100+ MB（VS Code 200+ MB 参照可接受）|
| **学习曲线** | Rust（陡）| JavaScript/TypeScript（平缓）|
| **社区先例** | 中等（growing）| 高（AnythingLLM 59.7k ⭐ 商用级）|
| **macOS notarization** | 现有坑（签名流程复杂）| 成熟（electron-builder 集成）|
| **Next.js standalone 集成** | 需研究 | 直接（社区案例丰富）|
| **工期** | 1.5 周框架 + ? 跨平台 | 1-2 周框架 + 4 周跨平台发布 |
| **结论** | ❌ 理论最优但工期风险 | ✅ **用户最终选择** |

**理由（4 条）**:

1. **社区验证最强**（Round-22 Desktop 报告 §四）
   - AnythingLLM 59.7k stars，商用级应用
   - 完整跨平台发布案例（macOS/Windows/Linux）
   - electron-builder + electron-updater 生产环保
   - **信心度**: ⭐⭐⭐⭐⭐

2. **工期紧张**（Round-22 Day 11-22 只有 12 天）
   - Electron: 1-2 周已包含 4 周跨平台发布
   - Tauri: 同周期概率 < 50%（Rust 学习 + macOS notarization 坑）
   - **可交付性**: ⭐⭐⭐⭐⭐

3. **包大小可接受**
   - 100 MB 对现代桌面应用（VS Code 200+ MB）可接受
   - GitHub Actions 可自动压缩
   - **实用性**: ⭐⭐⭐⭐

4. **Next.js standalone 零改动**
   - Web 层完全不动（仅 Electron 外包）
   - 万一需要切 Tauri，重新打包可行（Week 3 备选）
   - **技术债**: ✅ 低

---

### D18.2 4 Stories 拆分（Day 11-22）

#### Story 11.1: Electron 外壳（Day 11-12, 12h）
- **决策**: 用 `electron-react-boilerplate` 框架（社区 template）
- **理由**: 省去从头搭框架的 2-3 天，直接继承 Webpack + TS 配置
- **风险**: 框架版本陈旧（Day 12 检查升级）

#### Story 11.2: IPC Bridge + subprocess（Day 13-14, 16h）
- **决策**: spawn FastAPI subprocess（不是后台守护进程）
- **理由**:
  - 1:1 对应 Electron 应用生命周期（应用关闭 → subprocess 自杀）
  - 无需 systemd / launchd 注册
  - 权限管理简单（沙箱用户选定 vault 路径）
- **已知风险**: subprocess 崩溃需 health check（5s heartbeat）→ Story 11.2 Task 2 处理

#### Story 11.3: Vault 深度 + 渲染（Day 15-18, 28h）⭐ 核心
- **决策**: WebView 渲染 = 等于浏览器渲染（WebView 内核 ≈ Chrome）
- **证据**:
  - Round-22 CLI/SDK 报告 Agent B：Visualize CLI/SDK 不渲染，代码字符串需客户端渲染
  - Round-22 Desktop 报告 Agent A：Math Animator MP4 已在 server-side 生成，客户端仅播放
  - **结论**: Desktop App WebView = 完全等价 Web 用户体验
- **关键验证**: Story 11.3 AC #4（5 render_mode 全部支持）+ AC #5（离线渲染）
- **M4 映射对（13 映射中最强）必保留**

#### Story 11.4: 跨平台发布（Day 19-22, 24h）
- **决策**: GitHub Actions + electron-builder（不是本地打包）
- **理由**:
  - macOS 签名 + notarization 必须在 macOS runner
  - CI/CD 自动化可确保版本一致性
  - 3 平台平行构建（加速）
- **关键步骤**:
  1. 提交 tag （v0.2.0）→ GitHub Actions 自动触发
  2. 3 个 platform job 平行构建
  3. macOS job 自动 notarize（10-15 min）
  4. 所有 artifact 上传 Release
  5. electron-updater 检测新 Release，通知用户

---

## 实施路径（Day 11-22 总览）

```
Day 1-10  (Epic-10) : Canvas 5 核心集成 + wikilink/quiz/mastery/exam 全链路
                      ↓ Path A 确认（S1-S5 全 PASS）
Day 11-22 (Epic-11) : Desktop App 增项
  ├─ Day 11-12: Electron 框架搭建 (Story 11.1)
  ├─ Day 13-14: IPC + FastAPI subprocess (Story 11.2)
  ├─ Day 15-18: Vault 深度集成 + Math/Visualize 渲染 (Story 11.3) ⭐ 核心
  ├─ Day 19-22: 3 平台发布 + 自动更新 (Story 11.4)
  └─ Day 23-30: 用户 UAT + 错误修复（D-Batch 收敛）

总工期: ~22 天（Day 1-22 MVP 交付 + Day 23-30 stabilization）
```

---

## 时间窗 + 退出策略

**12 天 Epic-11 MVP**:

| 路径 | 触发条件 | 后续投入 |
|---|---|---|
| **A. 继续 Desktop + Web 双轨**（默认）| 3 平台用户均有人 + 自动更新稳定 | 月度 release（feature + bugfix） |
| **B. 仅保留 macOS Desktop** | 用户主要是 Mac + Win/Linux 装机率 < 10% | 简化 CI 仅 mac runner |
| **C. 退回纯 Web** | Desktop 包过大 / notarization 卡死 / 用户嫌麻烦 | Epic-11 经验作为研究档案 |

---

## 备选方案（D18 已评估并淘汰）

### 备选 A: Tauri 2.0（Week 3 切换可能）
- **触发条件**: Electron 包大 > 200 MB 或 CI/CD 流程反复失败
- **成本**: 重写 main.rs + 适配 IPC（~3-4 天）
- **预案**: Day 22 前保留 Tauri 分支（git branch `feature/tauri-fallback`）

### 备选 B: Web-only（如果 Desktop App 无法在 Day 22 发布）
- **降级方案**: Epic-11 成果仅作为研究报告，正式产品保留 Web（localhost:3782）
- **影响**: M4 映射对（13 映射中最强）仅 Web 端可用
- **概率**: < 10%（Electron 社区成熟度）

---

## 用户主权约束（NEG 反对批注落地）

- **NEG-1（Round-22 派生）**: ❌ 不绕过用户选 vault（首次必须 modal 选择）
- **NEG-2（Round-18 L805）**: ❌ 不上传 vault 文件，仅 IPC 读写本地
- **NEG-3（Round-22）**: ❌ Desktop App 不强制使用，Web 仍可访问 :3782（双轨并存）
- **NEG-4（D17 派生）**: ❌ MVP 期间不 git pull upstream（与 Epic-10 同源）

---

## 关键验证（Story 11.3 AC #4/AC #5 必跑）

### Math Animator MP4 内嵌渲染
- HTML5 `<video src="file://...">` 元素在 WebView 内
- 不弹出系统播放器
- 全屏 / seekbar / 速度调整全部支持

### Visualize 5 render_mode 全部 WebView 渲染
- **SVG**: dangerouslySetInnerHTML（dompurify sanitize）
- **Chart.js**: `<canvas>` + 动态 import
- **Mermaid**: `<div class="mermaid">` + 动态 import
- **HTML**: `<iframe sandbox srcDoc>` 隔离
- **auto**: AI 选定 → 上述分支

### 离线渲染验证
- 断网 → Math/Visualize 仍可用（FastAPI subprocess 本地）
- network monitor 验证无外网请求
- 仅 Claude API 调用时才需网络

---

## D17 ↔ D18 关系

D17 = Round-22 主决策（fork + 5 核心嵌入 - Day 0-10 MVP）
D18 = Round-22 子决策（Path A 后桌面化 - Day 11-22 增项）

两者通过 `related_round: round-22` + `epic` 字段链接：
- D17 落地 = Epic-10（9 stories, Day 0-10）
- D18 落地 = Epic-11（4 stories, Day 11-22）

**Epic-11 启动条件**: Epic-10 Day 10 UAT 5 验证场景 S1-S5 全 PASS（Path A 选定）。

---

## 关键发现（Round-22 调研收敛）

### F1: WebView 渲染 = 完全等价 Web 体验
- WebView 内核 ≈ Chrome（V8 + Blink/WebKit）
- HTML5 video / canvas / SVG / iframe 全部 native 支持
- 不需要复刻 5 capability 的渲染逻辑（Web 层零改动）

### F2: AnythingLLM 是最强参考
- 59.7k stars 商用级 Electron + Next.js 应用
- electron-builder 跨平台 CI/CD 完整模板
- 解决了 Python subprocess + IPC 的最佳实践

### F3: macOS notarization 是最大风险点
- xcrun notarytool 必须在 macOS runner
- Apple Developer Team ID + App-specific password 必备
- 公证审核 10-15 min（不可控）
- **缓解**: Day 19 提前测试流程，留足缓冲

### F4: 包大小不是阻塞
- Electron 100+ MB vs Tauri 5-10 MB
- 但用户期望（VS Code 200+ MB / Slack 200+ MB）已校准
- GitHub Releases delta update 可减少后续更新流量

---

## 关联文档

- **决策报告**: `_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
- **Desktop Deep Explore**: `_bmad-output/research/round-22-desktop-app-rendering-deep-explore-2026-05-07.md`
- **CLI/SDK Deep Explore**: `_bmad-output/research/round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`
- **Epic-11 总览**: `_bmad-output/implementation-artifacts/epic-11/_README.md`
- **Stories**: `_bmad-output/implementation-artifacts/epic-11/11-{1..4}-*.md`
- **UAT 验收单**: `_bmad-output/验收单/Story-11.{1..4}-*.md`
- **关联决策**: `_bmad-output/决策批注/D17-round22-fork-mvp-2026-05-06.md`
- **memory（待写）**: `decision_d18_desktop_app_electron.md`

---

## 签字确认

- **决策者**: 用户（Round-22 产品 owner）
- **技术验证**: Claude Code（5 + 6 Agent Deep Explore，Round-22 6 报告）
- **日期**: 2026-05-07
- **版本**: D18 v1.0

---

*D18 决策已落地为 Epic-11。Epic-11 启动条件 = Epic-10 Day 10 UAT 全 PASS。等用户 Day 10 后回填 Path A/B/C 选择。*
