# GDR 调研全景报告

**研究主题**: 前端重构技术选型验证 — Tauri 2.0 + React 19 + ReactFlow + shadcn/ui + TailwindCSS + Catppuccin Mocha
**执行 Agent 数**: 16（Wave1×4 + Wave2×10 + Wave3×2）
**Graphiti MCP**: graphiti-canvas | Group ID: canvas-dev
**完成时间**: 2026-03-17

---

## 核心决策状态

| 决策 | 原状态 | 新状态 | 依据 |
|------|--------|--------|------|
| DE-1 Tauri+React+ReactFlow | confirmed(Review PENDING) | **✅ VALIDATED** | 10/10信源验证,零阻塞风险 |
| DE-2 shadcn/ui+TailwindCSS+Catppuccin | confirmed(Review PENDING) | **✅ VALIDATED** | 65k stars+tauri-ui模板+官方Catppuccin port |
| DE-3 后端FastAPI保留 | confirmed(Review PENDING) | **✅ VALIDATED** | FastAPI是AI桌面工具主导后端 |
| DE-4 Tauri Shell管理Docker | confirmed(Review PENDING) | **⚠️ VALIDATED WITH RISKS** | Dockerman验证可行,Windows bug需HTTP IPC备选 |
| DE-5 CSP策略 | confirmed(Review PENDING) | **✅ VALIDATED** | Tauri内置CSP优于Electron,需unsafe-inline配置 |

## 补充决策（P1 用户已确认）

| 编号 | 决策 | 理由 |
|------|------|------|
| GDR-P1-1 | 版本锁定: ReactFlow 12.10.1 + React≥19.2.4 + Vite pin 7.x | RF 12.8.2过时/React CVE/Vite 8未验证 |
| GDR-P1-2 | Zustand 作为状态管理 | ReactFlow内部使用,官方推荐,竞品验证 |
| GDR-P1-3 | DE-4 增加 HTTP IPC 备选 | Windows spawn bug #11513/#4949 |
| GDR-P1-4 | IPC载荷<100KB 硬约束 | Windows IPC 200ms/10MB vs macOS 5ms |

## 冲突发现（共 0 个）

无 P0 级冲突。所有 DE-1~DE-5 决策均获验证。

## 新发现（共 4 个）

1. **ReactFlow ~1000 节点 DOM 天花板** — 50-300节点安全,需React.memo+Zustand+onlyRenderVisibleElements
2. **Windows IPC 性能差距** — 10MB载荷200ms(macOS 5ms),需<100KB+delta更新
3. **版本时效** — ReactFlow 12.10.1/React≥19.2.4/Vite pin 7.x
4. **Zustand 官方推荐** — ReactFlow+Zustand是标配,三层状态管理

## 过期预警（共 1 个）

- ReactFlow 12.8.2 → 需升级 12.10.1（React 19 + Tailwind v4 支持）

## 验证巩固（共 5 个）

- DE-1~DE-5 全部通过 10 个信源维度验证

## 信源覆盖

| Agent | 信源 | 关键证据 |
|-------|------|---------|
| W2-A GitHub | 生产案例 | lencx/ChatGPT(54k), Langflow(100k), Dify(100k+), Dockerman, tauri-ui |
| W2-B 社区 | HN+Reddit | Tauri 10MB vs Electron 100MB, ReactFlow 200-300节点无需优化 |
| W2-C 博客 | 工程复盘 | Firezone/UMLBoard/DoltHub Tauri生产经验, Zustand+ReactFlow最佳实践 |
| W2-D Survey | 综述论文 | Schroeder 2018 g=0.58(n=11,814), 空间学习d=0.79, Mayer多媒体学习 |
| W2-E SOTA | 前沿论文 | BKT鲁棒性(arXiv 2025), FSRS SSP-MMC(KDD 2022), 隐形评估ECD(2024) |
| W2-F 反例 | 失败案例 | 零stack-breaking失败,3个被否决方案均无需重审 |
| W2-G 竞品 | 对标分析 | Langflow≈最近似架构, Spacedrive≈最近似整体, Clash Verge≈最近似壳 |
| W2-H 限制 | 边缘案例 | Windows IPC 200ms, Shell PATH不继承, WebView2差异 |
| W2-I 实现 | Context7+深挖 | nodeTypes外部定义, oklch变量映射, CSP unsafe-inline, fix-path-env-rs |
| W2-J 时效 | 版本核查 | RF 12.10.1, React 19.2.4, Vite pin 7.x, Tauri 2.10.3稳定 |

## 结论

**技术选型通过全域验证，可高成功率稳定实施。**

- 零 P0 冲突，零 stack-breaking 失败案例
- 4 项 P1 补充决策已确认，加固了实施基础
- 最大风险在 Windows 平台（IPC性能+Shell bug），已有明确缓解方案
- 参考架构清晰：Langflow(FastAPI+React+ReactFlow) + Spacedrive(Tauri+React)
