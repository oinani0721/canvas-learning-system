# Session D 前端重构 — Brainstorming 总结

> 汇总日期：2026-03-14
> 涵盖：Session D 全部 brainstorming + demo 构建 + Pencil 设计 + 代码审查 + bug 修复
> 状态：Brainstorming 完成，待集成到 Obsidian 插件

---

## 一、Session D 演进时间线

| 日期 | 阶段 | 产出 |
|------|------|------|
| 03-11 | Brainstorming Phase 1-2 | 竞品调研(17款)、框架选型(Svelte)、核心概念设计(Canvas 知识图谱学习界面)、学习科学评估(8/10) |
| 03-12 | Pencil 设计 V1 | 完整 UI 原型(Canvas UI.pen)、10+ frame 覆盖所有交互流程 |
| 03-13 | Demo V1 构建 | 交互 HTML demo(demo/index.html)、2541 行、Catppuccin Mocha 主题 |
| 03-13 | Demo V2 迭代 | Obsidian Canvas 风格重设计、文本卡片节点、文字选取拉出节点 |
| 03-14 | Pencil 设计 V2 | Canvas v2 frame + Connection Interaction Flow frame |
| 03-14 | Bug 修复 | 移除自动连线、XSS 修复、手动连线系统、conn-dot 事件修复 |
| 03-14 | 方向调整 | 用户决定：demo 应在 Obsidian 插件内运行，非浏览器独立页面 |

---

## 二、核心设计决策

### 2.1 产品定位（已确认）
**Canvas 知识图谱学习界面** — 不是传统卡片管理 UI，而是：
- 节点 = 知识单元（含实际文本内容，非仅标题标签）
- 点击节点 → 右侧面板 AI 对话
- 节点间有学习关系图（typed edges：分解为、解释了、追问自等）
- 从 AI 对话中选取文字 → 拖出为新节点

### 2.2 两大差异化功能（竞品调研结论）
1. **节点级 Dashboard** — 每个知识节点有独立精通度、学习进度、FSRS 复习调度
2. **类型化学习关系图** — 不是通用 graph，边有语义标签描述学习关系

### 2.3 设计风格（已确认）
- **Obsidian Canvas 原生风格** — 暗色卡片(#181825) + 彩色左边框（非填充色）
- **Catppuccin Mocha 色系** — 6 种节点状态颜色
- **手动连线** — 遵循 Obsidian Canvas 交互原则，连线完全由用户控制（hover 圆点 → 拖拽 → 松开创建）

### 2.4 技术框架（已确认）
- **Svelte** 作为前端框架（1.6KB bundle、内置 CSS 隔离、状态管理）
- 80% 现有代码基础设施可复用
- 前后端分离架构

---

## 三、Demo 现状（demo/index.html）

### 已实现功能
| 功能 | 状态 | 说明 |
|------|------|------|
| 5 个静态知识节点 | ✅ 完成 | Obsidian Canvas 风格暗色卡片 + 彩色左边框 |
| 节点拖拽 | ✅ 完成 | header/footer 拖拽，body 文字选取 |
| 预设连线 + 标签药丸 | ✅ 完成 | 贝塞尔曲线 + 中点标签 |
| 手动连线系统 | ✅ 完成 | hover 圆点 → 拖拽 → hit-test → prompt 输入标签 |
| 连线删除 | ✅ 完成 | 点击 edge label 删除 |
| 文字选取 → 拉出节点 | ✅ 完成 | 选中 AI 回复文字 → "放到白板" → 创建新节点 |
| 右侧面板 | ✅ 完成 | 对话/笔记/考察 tab + AI 聊天线程 + 输入框 |
| 自我评估 | ✅ 完成 | 4 级评分 → FSRS 更新 → 精通度变化 |
| 底部工具栏 | ✅ 完成 | 选择/节点/连线/考察/Skills |
| 颜色图例 | ✅ 完成 | 7 种节点状态说明 |
| 画布缩放/平移 | ✅ 完成 | 鼠标滚轮缩放 + 空白区域拖拽平移 |
| 粘贴创建节点 | ✅ 完成 | Ctrl+V → 选择类型 → 创建节点 |

### 已修复 Bug
| Bug | 修复方案 |
|-----|---------|
| 自动连线（doPlaceOnCanvas/createNodeFromPaste 无条件 connections.push） | 移除自动连线代码 |
| XSS（用户文本直接插入 innerHTML） | 使用 escapeHtml() 处理 |
| conn-dot 事件拦截（opacity:0 元素仍捕获事件） | pointer-events:none 默认，hover 时启用 |
| overflow:hidden 裁剪 conn-dot | overflow 移到 .node-body |
| selOverlay 文字选取范围受限 | 事件委托覆盖 .selectable + .node-body |
| 拖拽与选取冲突 | node-body 跳过拖拽逻辑 |

---

## 四、Pencil 设计文件（Canvas UI.pen）

### 已完成 Frame
| Frame | ID | 内容 |
|-------|-----|------|
| Canvas v2 — Obsidian Canvas Style | VvxVL | 主界面：5 节点 + 4 连线 + 圆点 + 工具栏 + 图例 + 右侧面板(header/tabs/chat/input) |
| Connection Interaction Flow | Lwifu | 4 步连线流程图：悬停→拖拽→松开→编辑 |
| Canvas Learning System (V1) | rSIY3 | 旧版彩色填充风格（已弃用） |
| 其他 10+ frames | — | Interaction Flow、Skill Manager、Dashboard 等 |

---

## 五、学习科学评估

### 理论支撑（8/10）
- 精细加工编码（Elaborative Encoding）— 节点扩展对话
- 间隔重复（Spaced Repetition）— FSRS 调度
- 主动回忆（Active Recall）— 考察模式
- 知识图谱化（Knowledge Graph）— 可视化关系
- 元认知监控（Metacognition）— 自我评估

### Karpicke 陷阱风险（需缓解）
> "学习 ≠ 解释，学习 = 检索练习" — Harvard RCT (d=0.73-1.3)

当前 7/8 个 Agent 模式属于解释型，需要增加检索练习比重：
1. 强制先提问再解释（inverted tutoring）
2. 定期自动触发考察
3. 解释生成中嵌入测试题
4. 精通度仅通过考察表现提升（非阅读）
5. 复习时先回忆再查看

---

## 六、关键方向变更（2026-03-14）

### ⛔ Demo 不应在浏览器运行，应集成到 Obsidian 插件

**用户明确要求**：
- 插件前后端分离，demo 必须在 Obsidian 环境验证
- 不直接编译修改覆盖当前插件，先备份
- 已完成 git push (commit b2a4461)

**待定工作**：
- 需要 deep explore 现有插件前端架构
- 制定安全的集成方案（新分支隔离开发）
- 验证 Obsidian Canvas API 是否支持 demo 中的交互模式

---

## 七、与其他 Session 的依赖关系

```
Phase 0 (基础修复)
  S1 死代码清理 → S4a Config → S2 Retriever → S3 Pipeline
                                                    ↓
Phase 1 (核心升级)
  P0 分块+bge-m3 → S7/A2 Reranking+CRAG → S4 Config统一
                                                    ↓
Phase 2 (新功能)
  A3 检索范围 → A5 多模态 → Memory System 2
                                                    ↓
Phase 3 (前端重构) ← 可部分并行
  Session D Canvas 知识图谱 UI + Karpicke 缓解 + FSRS 对接
```

**Session D 独立于后端**：前端 UI 可独立开发，但完整体验需要后端 RAG 管道就绪。

---

## 八、19 个 PENDING Decision-Reviews（全项目）

Session D 相关：
- [Decision-Review] Demo 集成到 Obsidian 插件的方案 — PENDING

全项目（来自 Session A 子任务）：
- A1 分块管道（DR-1~4）— 4 个 PENDING
- A2 重排序+CRAG（DR-5~8）— 4 个 PENDING（2 个已被 S6 review 修正）
- A3 新功能（DR-9~14）— 6 个 PENDING
- A4 索引管道（DR-15~18）— 4 个 PENDING
- A5 多模态（DR-19）— 1 个 PENDING

---

## 九、下一步建议

1. **Session C（Golden Test Set）** — 所有验收测试的前置条件，尚未实施
2. **Phase 0 实施** — S1 死代码清理 → S4a Config → S3 激活 reranker
3. **Session D 集成调研** — deep explore 插件前端架构，制定 demo → Obsidian 插件迁移方案
4. **Pencil ↔ Claude Code 修复** — 验证旧 session 备份后是否恢复正常
