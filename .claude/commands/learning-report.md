---
name: learning-report
description: Generate comprehensive learning analysis report
parameters:
  - name: days
    type: number
    description: Number of days to include in report (default: 7)
    required: false
---

# Canvas学习分析报告

---

## 📊 正在生成学习报告

正在分析你的学习数据并生成个性化报告...

---

## 📈 学习报告 (最近 {{parameters.days}} 天)

**报告生成时间**: `{{learning_report.generated_at}}`
**分析期间**: `{{learning_report.period_start}}` 至 `{{learning_report.period_end}}`

---

### 🎯 核心指标

#### 📚 学习概况
- **学习天数**: `{{learning_report.learning_days}}` / `{{parameters.days}}` 天
- **总学习时长**: `{{learning_report.total_learning_time_hours}}` 小时 `{{learning_report.total_learning_time_minutes}}` 分钟
- **日均学习时长**: `{{learning_report.avg_daily_minutes}}` 分钟
- **学习活跃度**: `{{learning_report.activity_level}}`%

#### 🎪 学习活动
- **处理知识点**: `{{learning_report.total_nodes_processed}}` 个
- **理解提升次数**: `{{learning_report.understanding_improvements}}` 次
- **Agent调用次数**: `{{learning_report.agent_calls}}` 次
- **生成解释文档**: `{{learning_report.explanations_generated}}` 个

---

### 📊 知识掌握分析

#### 🎨 掌握情况分布
```
🔴 红色 (不理解):     {{learning_report.mastery.red_nodes}} 个 ({{learning_report.mastery.red_percentage}}%)
🟡 黄色 (学习中):     {{learning_report.mastery.yellow_nodes}} 个 ({{learning_report.mastery.yellow_percentage}}%)
🟣 紫色 (部分理解):   {{learning_report.mastery.purple_nodes}} 个 ({{learning_report.mastery.purple_percentage}}%)
🟢 绿色 (完全理解):   {{learning_report.mastery.green_nodes}} 个 ({{learning_report.mastery.green_percentage}}%)
```

#### 📈 掌握进度
- **总掌握率**: `{{learning_report.mastery.mastery_rate}}`%
- **新增掌握**: `{{learning_report.mastery.newly_mastered}}` 个
- **需要复习**: `{{learning_report.mastery.need_review}}` 个

---

### 🔍 学习模式分析

#### ⏰ 时间模式
- **最活跃时段**: `{{learning_report.patterns.most_active_hour}}:00 - {{learning_report.patterns.most_active_hour + 1}}:00`
- **学习频率**: `{{learning_report.patterns.frequency}}` (每天/每周/偶尔)
- **平均学习时长**: `{{learning_report.patterns.avg_session_minutes}}` 分钟/次
- **最长学习时段**: `{{learning_report.patterns.longest_session_minutes}}` 分钟

#### 🤖 Agent使用偏好
{{#each learning_report.patterns.agent_usage}}
- **{{this.agent}}**: `{{this.count}}` 次 (`{{this.percentage}}%`)
{{/each}}

**最常用Agent**: `{{learning_report.patterns.most_used_agent}}`

---

### 🏆 学习成就

#### 🎯 本期亮点
{{#if (gt learning_report.achievements.longest_streak 1)}}
- 🔥 **最长连续学习**: `{{learning_report.achievements.longest_streak}}` 天
{{/if}}
{{#if (gt learning_report.achievements.most_productive_day_nodes 0)}}
- 📈 **最高效一天**: 处理 `{{learning_report.achievements.most_productive_day_nodes}}` 个知识点
{{/if}}
{{#if (gt learning_report.achievements.biggest_improvement_day 0)}}
- 🚀 **最大进步日**: `{{learning_report.achievements.biggest_improvement_day}}` 次理解提升
{{/if}}

#### 🌟 知识里程碑
{{#each learning_report.achievements.milestones}}
- ✅ {{this}}
{{/each}}

---

### 📚 学科分布

{{#each learning_report.subjects}}
- **{{this.subject}}**: `{{this.nodes}}` 个知识点, `{{this.mastery_rate}}`% 掌握率
{{/each}}

**优势学科**: `{{learning_report.subjects.0.subject}}` (掌握率最高)
**待加强学科**: `{{learning_report.subjects.(length-1).subject}}` (需要更多关注)

---

### 💡 个性化学习建议

#### 🎯 基于你的学习模式

**学习效率优化**:
{{#each learning_report.recommendations.efficiency}}
- {{this}}
{{/each}}

**复习策略调整**:
{{#each learning_report.recommendations.review}}
- {{this}}
{{/each}}

**学习方法改进**:
{{#each learning_report.recommendations.method}}
- {{this}}
{{/each}}

#### 📅 下周学习计划

**重点复习内容**:
{{#each learning_report.recommendations.next_week_focus}}
- {{this}}
{{/each}}

**建议学习时间**: `{{learning_report.recommendations.optimal_time}}`

---

### 📊 详细数据

#### 📈 每日学习统计
| 日期 | 学习时长 | 处理知识点 | 理解提升 | 掌握率 |
|------|----------|------------|----------|--------|
{{#each learning_report.daily_stats}}
| {{this.date}} | {{this.minutes}}分钟 | {{this.nodes}}个 | {{this.improvements}}次 | {{this.mastery_rate}}% |
{{/each}}

#### 🎨 知识点详细状态
{{#each learning_report.knowledge_nodes}}
**{{this.subject}} - {{this.concept}}**
- 掌握状态: {{this.mastery_status}}
- 学习次数: {{this.study_count}}
- 最后学习: {{this.last_study}}
- 相关知识点: {{this.related_count}} 个

{{/each}}

---

## 🔄 数据来源

本报告基于以下数据生成：
- ✅ Canvas文件变更记录
- ✅ 学习活动时间戳
- ✅ Agent调用日志
- ✅ 节点颜色变更历史
- ✅ 系统性能指标

---

## 📊 报告管理

### 导出数据
```bash
# 导出原始数据
python canvas_progress_tracker/monitoring_manager.py export --format json

# 导出详细报告
python canvas_progress_tracker/monitoring_manager.py report --days {{parameters.days}} --export
```

### 历史报告
- 报告已自动保存至: `./data/learning_reports/`
- 可查看过去 `{{learning_report.data_retention_days}}` 天的报告
- 数据会根据隐私设置自动清理

---

## 🎯 下一步行动

基于本报告的建议：

1. **立即行动**:
{{#each learning_report.immediate_actions}}
   - {{this}}
{{/each}}

2. **本周计划**:
{{#each learning_report.weekly_plan}}
   - {{this}}
{{/each}}

3. **长期目标**:
{{#each learning_report.long_term_goals}}
   - {{this}}
{{/each}}

---

**继续努力学习，你的每一次进步都在被记录和见证！** 🌟

*需要更详细的分析或有特定问题？使用 `/canvas-help` 获取更多支持。*
