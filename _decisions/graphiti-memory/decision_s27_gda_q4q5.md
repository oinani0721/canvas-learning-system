---
name: S27 GDA Q4/Q5 用户批注确认
description: CognitiveLoadTimer确认移除 + Node Profile优先级：跳转最高→疑惑节点=选文本创建→考察记录/错误历史延后（2026-03-25）
type: project
---

## [Decision] S27 GDA Q4/Q5 — 用户批注确认

Session: S27 | 日期: 2026-03-25

### Q4: CognitiveLoadTimer 确认移除
- 用户说"先进行移除"
- 删除 CognitiveLoadTimer.tsx + ExamCanvas 中的引用
- ExamSummary 中的总用时显示也应移除

### Q5: Node Profile 4项功能优先级
用户确认的优先级排序：

1. **最高优先级：d. 点击跳转到当时的对话/白板**
   - 用户明确说"我觉得最优先级创建的是点击跳转"

2. **c. 疑惑→新节点手动创建**
   - 用户澄清交互方式："你检测出来然后问我是否需要单独讨论，这时候我可以和原白板一样选择相关的文本来创建节点"
   - 即：AI 识别疑惑 → 提示用户 → 用户选择文本 → 创建新节点（复用原白板的文本选择创建节点机制）

3. **a. 考察记录列表 + b. 错误历史**
   - 用户未提及优先级，隐含为较低优先级
   - 等管道打通后再做

**Why:** 跳转功能让用户能追溯学习历程（"点击错误→看到当时对话"），是学习闭环的核心体验
**How to apply:** Phase 3 优先实现跳转功能，疑惑节点复用 usePullToNode hook

**决策状态: [Decision-Review] PENDING — 待验证: 跳转需要 source_session_id + source_canvas_id 记录完整性**
