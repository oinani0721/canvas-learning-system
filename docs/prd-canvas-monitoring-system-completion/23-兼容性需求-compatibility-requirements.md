# 2.3 兼容性需求 (Compatibility Requirements)

## CR1: API兼容性

**要求**：监控系统应保持现有`canvas_utils.py`的API不变。

**具体承诺**：

- ✅ `CanvasJSONOperator`的所有公共方法保持签名不变
- ✅ `CanvasBusinessLogic`的布局算法不修改
- ✅ `CanvasOrchestrator`的Agent调用接口保持不变
- ✅ 新增的回调接口向后兼容（可选参数）

**如果必须修改**：

- 提供弃用警告（deprecation warning）
- 保留旧接口至少2个版本
- 提供迁移指南

**验收标准**：

- ✅ 运行`pytest tests/test_canvas_utils.py`，所有测试通过
- ✅ API文档更新（标注新增/弃用）

---

## CR2: 数据库Schema兼容性

**要求**：SQLite数据库schema应支持版本升级。

**版本管理**：

- 在数据库中存储schema版本号
- 创建迁移脚本：`migrations/v1_to_v2.sql`
- 启动时自动检测并执行迁移

**迁移策略**：

```sql
-- migrations/v1_to_v2.sql

-- 1. 检查当前版本
SELECT version FROM schema_version;

-- 2. 添加新列（如果需要）
ALTER TABLE canvas_changes ADD COLUMN processing_time_ms INTEGER;

-- 3. 更新版本号
UPDATE schema_version SET version = '2.0', updated_at = datetime('now');
```

**验收标准**：

- ✅ v1.0数据库可自动升级到v2.0
- ✅ 迁移过程不丢失数据
- ✅ 迁移失败时回滚（事务保护）

---

## CR3: UI/UX一致性

**要求**：学习报告的格式应与现有Canvas学习系统的文档风格一致。

**格式规范**：

- Markdown格式（支持GitHub Flavored Markdown）
- 使用emoji保持友好性（📊 📈 🎯 ✨）
- 中文为主，英文为辅
- 表格和图表使用文本ASCII艺术

**错误消息规范**：

- 中文错误消息
- 提供具体的解决方案
- 友好的语气（避免"错误"、"失败"等严厉词汇，使用"无法"、"未找到"）

**命令命名规范**：

- 斜杠命令格式：`/xxx-xxx`（小写，连字符分隔）
- 示例：`/monitoring-status`, `/learning-report`, `/stop-monitoring`
- 与现有命令保持一致性

**验收标准**：

- ✅ 报告格式与现有文档风格一致
- ✅ 错误消息友好且有用
- ✅ 命令命名符合规范

---

## CR4: 系统集成兼容性

**要求**：与12个AI Agent和现有系统的集成应通过标准回调协议。

**Agent集成原则**：

- ✅ 不修改Agent定义文件（`.claude/agents/*.md`）
- ✅ 不修改Agent调用协议
- ✅ 监控系统是观察者，不主动触发Agent

**颜色系统兼容**：

- ✅ 使用现有颜色常量（canvas_utils.py中定义）
- ✅ 颜色代码：1=红, 2=绿, 3=紫, 5=蓝, 6=黄
- ✅ 不引入新的颜色代码

**Canvas文件格式兼容**：

- ✅ 不修改.canvas文件格式
- ✅ 只读取，不写入Canvas文件
- ✅ 兼容Obsidian Canvas JSON schema

**验收标准**：

- ✅ 12个Agent在监控运行时正常工作
- ✅ 颜色系统一致（与canvas_utils.py一致）
- ✅ Canvas文件完整性不受影响

---
