# Story 6.7: 认知负荷控制与休息提醒

Status: ready-for-dev

## Story

As a 用户,
I want 持续考察一段时间后系统提醒我休息，
so that 不会过度考察导致疲劳。

## Acceptance Criteria

1. **AC-1: 15/25/35/45 分钟递进提醒（FR-EXAM-08）**
   - **Given** 用户持续在检验白板中考察
   - **When** 考察持续时间达到以下阈值
   - **Then** 按递进级别触发休息提醒：
     - **15 分钟**：轻量提醒——"你已经考察了 15 分钟，可以休息一下"（对话内嵌入）
     - **25 分钟**：中等提醒——"连续考察 25 分钟了，建议休息 5 分钟"
     - **35 分钟**：较强提醒——"已持续 35 分钟，大脑需要休息才能更好吸收"
     - **45 分钟**：强烈提醒——"连续 45 分钟了，强烈建议休息。休息后回来效果更好"
   - **And** 每个阈值只触发一次（不重复提醒）
   - **And** 45 分钟后不再有新的时间阈值提醒
   - **And** 计时从考察开始时起算（exam-state.startTime）

2. **AC-2: 休息提醒以对话消息呈现**
   - **Given** 到达时间阈值触发提醒
   - **When** 提醒显示
   - **Then** 提醒以特殊样式的对话消息插入 ChatPanel 中（RestReminder 组件）
   - **And** 不弹出模态框、不打断当前对话
   - **And** 消息样式区别于普通对话：使用柔和的背景色 + 图标
   - **And** 消息语气温和正面（"建议休息"而非"必须停止"）

3. **AC-3: 用户选择"继续"或"休息"**
   - **Given** 休息提醒消息显示
   - **When** 用户看到提醒
   - **Then** 提供两个操作选项：
     - **"继续考察"**：关闭提醒消息，继续考察（对话不中断）
     - **"休息"**：正常结束考察，保存所有数据
   - **And** 不回应提醒 = 继续考察（提醒不阻塞操作）
   - **And** 选择"休息"后触发考察结束流程（Story 6.8 考察记录保存）

4. **AC-4: CognitiveLoadTimer Svelte 组件**
   - **Given** 检验白板考察进行中
   - **When** ExamCanvas 渲染
   - **Then** CognitiveLoadTimer 组件在检验白板顶部状态栏显示考察时长
   - **And** 时长格式："考察 MM:SS"
   - **And** 接近提醒阈值时（前 2 分钟）时长文字颜色从默认变为黄色
   - **And** CSS 使用 `cl-exam-timer-*` 前缀

5. **AC-5: RestReminder Svelte 组件**
   - **Given** 到达时间阈值
   - **When** 提醒触发
   - **Then** RestReminder 组件渲染为对话流中的特殊消息
   - **And** 包含：提醒图标 + 提醒文字 + "继续考察"按钮 + "休息"按钮
   - **And** "继续考察"为次操作样式（边框按钮），"休息"为文字操作样式
   - **And** CSS 使用 `cl-exam-rest-*` 前缀，适配 Light/Dark 主题

6. **AC-6: 考察暂停与恢复**
   - **Given** 用户点击"休息"
   - **When** 考察暂停
   - **Then** exam-state.examStatus 更新为 `paused`
   - **And** 考察计时暂停
   - **And** 当前对话上下文保留（不清空 session）
   - **And** 后端 `PATCH /api/v1/exam/{exam_id}/status` 更新为 paused
   - **And** 用户可从 Dashboard 重新进入该检验白板继续考察（resume）

7. **AC-7: 计时不计算非活跃时间**
   - **Given** 考察进行中
   - **When** 用户切换到其他 Obsidian 页面或最小化窗口
   - **Then** 计时器暂停（不计非活跃时间）
   - **And** 用户回到检验白板时计时恢复
   - **And** 使用 `document.hidden` / `visibilitychange` API 检测活跃状态

## Tasks / Subtasks

- [ ] **Task 1: CognitiveLoadTimer 组件** (AC: #4)
  - [ ] 1.1 创建 `src/components/exam/CognitiveLoadTimer.svelte`
  - [ ] 1.2 实现考察时长计时器（每秒更新）
  - [ ] 1.3 实现接近阈值时颜色变化（黄色预警）
  - [ ] 1.4 实现 visibilitychange 检测暂停/恢复计时
  - [ ] 1.5 集成到 ExamCanvas 顶部状态栏

- [ ] **Task 2: RestReminder 组件** (AC: #2, #5)
  - [ ] 2.1 创建 `src/components/exam/RestReminder.svelte`
  - [ ] 2.2 实现特殊对话消息样式（区别于普通消息）
  - [ ] 2.3 实现"继续考察" / "休息"两个按钮
  - [ ] 2.4 CSS cl-exam-rest-* 前缀 + Light/Dark 适配

- [ ] **Task 3: 递进提醒逻辑** (AC: #1)
  - [ ] 3.1 在 exam-state 中实现阈值检测逻辑（15/25/35/45 分钟）
  - [ ] 3.2 每个阈值只触发一次（已触发阈值列表）
  - [ ] 3.3 到达阈值时向 ChatPanel 插入 RestReminder 消息
  - [ ] 3.4 不同级别的提醒文案差异化

- [ ] **Task 4: 休息/继续交互** (AC: #3, #6)
  - [ ] 4.1 "继续考察"：关闭提醒消息，继续计时
  - [ ] 4.2 "休息"：exam-state 更新为 paused → 触发考察暂停
  - [ ] 4.3 后端更新 exam_session 状态为 paused
  - [ ] 4.4 实现从 Dashboard 恢复暂停的考察（resume）

- [ ] **Task 5: 非活跃时间处理** (AC: #7)
  - [ ] 5.1 实现 visibilitychange 事件监听
  - [ ] 5.2 页面隐藏时暂停计时器
  - [ ] 5.3 页面显示时恢复计时器
  - [ ] 5.4 只统计活跃考察时间

## Dev Notes

### 架构定位

本 Story 是检验白板的用户体验保障层——认知负荷控制。防止用户过度考察导致疲劳，是 PRD 中应对"递归考察打击信心"风险的关键缓解措施。

### 依赖关系

- **依赖 Story 6.1**：ExamCanvas + exam-state 基础框架（startTime）
- **被 Story 6.8 依赖**："休息"结束考察时触发考察记录保存

### 认知负荷控制设计理据

PRD 风险矩阵明确标注"递归考察打击学习信心"风险，缓解策略为认知负荷控制（15/25/35/45 分钟提醒）。

时间阈值选择依据：
- 15 分钟：番茄工作法最短工作周期
- 25 分钟：标准番茄周期
- 35 分钟：超出标准周期
- 45 分钟：接近一节课时长，强烈建议休息

### 非打断式提醒设计

UX 设计原则"右侧面板即上下文"——提醒不弹窗、不覆盖白板，而是融入对话流。用户可以自然地在对话中看到提醒，无需切换注意力。

### Project Structure Notes

- CognitiveLoadTimer / RestReminder 在 `src/components/exam/` 目录（B 组）
- CSS 类名前缀 `cl-exam-timer-*` / `cl-exam-rest-*`
- 计时器状态在 exam-state 中管理

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story6.7] — AC 原文
- [Source: _bmad-output/planning-artifacts/prd.md#能力域4] — FR-EXAM-08
- [Source: _bmad-output/planning-artifacts/prd.md#过度考察风险] — 15/25/35/45 分钟递进提醒
- [Source: _bmad-output/planning-artifacts/prd.md#Layer3创新] — 递归考察风险缓解
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy] — B 组 CognitiveLoadTimer / RestReminder
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#反馈模式] — 休息提醒：对话内特殊消息
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#情感设计原则] — "用户掌控节奏"
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Pencil范式覆盖] — 场景 14 认知负荷休息提醒

## Dev Agent Record

### Agent Model Used

(待开发时填写)

### Debug Log References

(待开发时填写)

### Completion Notes List

(待开发时填写)

### File List

- `src/components/exam/CognitiveLoadTimer.svelte` — 新建
- `src/components/exam/RestReminder.svelte` — 新建
- `src/stores/exam-state.svelte.ts` — 修改（添加计时器逻辑 + 已触发阈值列表）
- `src/components/exam/ExamCanvas.svelte` — 修改（集成 CognitiveLoadTimer）
