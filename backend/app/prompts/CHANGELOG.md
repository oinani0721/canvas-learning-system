# Prompt 版本变更记录

> 每次 Prompt 版本变更必须在此记录。格式：日期 | 模板 | 版本 | 变更说明 | 影响范围

---

## 变更记录

### 2026-03-16

| 模板 | 版本 | 操作 | 说明 | 影响范围 |
|------|------|------|------|---------|
| autoscore | v1 | 创建 | AutoSCORE 两阶段评分初始版本（证据提取 + 4 维 4 分制 SOLO 锚定） | services/autoscore.py |
| question_gen | v1 | 创建 | 出题 Prompt 5 层结构初始版本（角色-模式-ACP-规则-评分预设） | services/question_generator.py |
| context_extract | v1 | 创建 | 对话结构化提取初始版本（错误 4 类/Tips/关键问答） | services/conversation_archive.py |

---

## 回滚记录格式

如需回滚，按以下格式记录：

| 日期 | 模板 | 回滚操作 | 原因 | 回归测试结果 |
|------|------|---------|------|-------------|
| YYYY-MM-DD | template_name | vN -> vM | 回滚原因描述 | 回归测试通过/未通过 |
