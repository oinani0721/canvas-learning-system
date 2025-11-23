# Sprint变更提案 (SCP-003)
## Canvas备份文件夹组织规范补全

**文档编号**: SCP-003
**创建日期**: 2025-11-12
**PRD版本**: v1.1.6
**变更类型**: 设计细节补充
**优先级**: P1 (影响用户体验)
**状态**: ✅ **已批准并实施**

---

## 1. 变更分析总结

### 1.1 触发原因

**问题陈述**:
Canvas备份文件与原Canvas文件存放在同一文件夹，导致Obsidian文件浏览器显示凌乱，影响用户体验和文件管理。

**发现方式**:
用户在PRD审查阶段提出的实际使用场景问题。

**问题类型**:
新发现的需求（Newly Discovered Requirement）- 备份文件组织策略缺失

### 1.2 影响范围

**Epic影响**:
- ✅ Epic 12（Story 12.1）- 需要扩展验收标准
- ✅ Epic 13（Story 13.2）- 需要确保Plugin兼容性
- ✅ 其他Epic - 无影响

**文档影响**:
- ⚠️ NFR2 可靠性要求 - 需要补充详细规范
- ⚠️ Section 3.6.6 回滚机制 - 需要补充备份文件组织说明
- ⚠️ Epic 12, Story 12.1 - 需要扩展验收标准

**当前状态诊断**:
- ✅ PRD中已有`.canvas_backups/`路径（Line 3449）
- ❌ 但仅出现在代码示例中，未作为正式需求定义
- ❌ 缺少：备份文件夹位置、命名规则、清理策略

### 1.3 选择的路径

**推荐方案**: **选项1 - 直接调整/集成**

**理由**:
1. 这是设计细节补充，非架构变更
2. 备份路径已在PRD中存在，仅需规范化
3. 不影响Epic结构、Story序列、项目时间线
4. 工作量最小（1-2小时文档更新）

---

## 2. 具体实施编辑

### ✅ 编辑 #1: NFR2 可靠性要求扩展

**文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
**位置**: Line 1350
**编辑类型**: 扩展现有内容
**状态**: ✅ 已完成

**变更内容**:
将简单的"所有Canvas操作前自动备份"扩展为包含以下详细规范：
- 备份文件夹: `{Vault根目录}/.canvas_backups/`
- 备份命名规则: `{canvas_name}_{checkpoint_id}.canvas`
- 备份触发时机: 每次LangGraph创建checkpoint时
- 备份清理策略: 保留最近50个，超过自动删除最旧的
- 手动保护机制: 用户标记的备份永不删除

---

### ✅ 编辑 #2: Section 3.6.6 备份文件组织规范补充

**文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
**位置**: Line 3489之后（Section 3.6.6内部）
**编辑类型**: 新增小节
**状态**: ✅ 已完成

**新增内容**:
完整的"备份文件组织规范"小节，包括：

1. **问题背景说明**
2. **备份根目录获取方法** (`get_vault_root()`)
3. **备份文件路径计算** (`get_backup_path()`)
4. **LangGraph Checkpointer集成** (`CanvasBackupCheckpointer`类)
5. **备份清理策略** (`cleanup_old_backups()`)
6. **手动保护机制** (`is_protected_backup()`)
7. **Obsidian Plugin隐藏配置** (TypeScript代码)
8. **用户手动保护备份UI** (右键菜单)
9. **验收标准**
10. **性能影响评估**

总计约170行代码和说明。

---

### ✅ 编辑 #3: Story 12.1验收标准扩展

**文件**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
**位置**: Epic 12, Story 12.1的验收标准（Line 3871）
**编辑类型**: 追加验收标准
**状态**: ✅ 已完成

**新增验收标准** (标注为[SCP-003新增]):
- ✅ 备份文件夹`.canvas_backups/`在Vault根目录正确创建
- ✅ 备份文件按规范命名：`{canvas_name}_{checkpoint_id}.canvas`
- ✅ 每次checkpoint创建时自动生成对应备份文件
- ✅ 备份清理机制正常工作：超过50个自动删除最旧的（跳过受保护的）
- ✅ 备份文件夹在Obsidian文件浏览器中默认隐藏（需Story 13.1配合）
- ✅ 回滚功能正确：`rollback_to_checkpoint()`能找到并恢复备份
- ✅ 性能达标：备份创建+清理总耗时 <100ms

---

## 3. MVP影响评估

**MVP功能范围**: ✅ 无变化
**MVP时间线**: ✅ 无变化
**MVP核心目标**: ✅ 无影响

**说明**:
此变更为设计细节补充，不影响系统功能或用户价值主张，仅优化文件组织和用户体验。

---

## 4. 技术实现要点

### 4.1 核心设计原则

1. **统一存储**: 所有Canvas备份统一存放在Vault根目录的`.canvas_backups/`文件夹
2. **自动隐藏**: 备份文件夹在Obsidian文件浏览器中默认隐藏，不干扰日常使用
3. **智能清理**: 自动清理旧备份（保留最近50个），同时支持手动保护重要备份
4. **性能优先**: 备份操作总耗时<100ms，不影响用户体验

### 4.2 关键函数

| 函数名 | 功能 | 实施位置 |
|--------|------|---------|
| `get_vault_root()` | 从Canvas路径获取Vault根目录 | Story 12.1 |
| `get_backup_path()` | 计算备份文件完整路径 | Story 12.1 |
| `CanvasBackupCheckpointer` | 扩展的Checkpointer，同步创建备份 | Story 12.1 |
| `cleanup_old_backups()` | 清理旧备份文件 | Story 12.1 |
| `is_protected_backup()` | 检查备份是否被保护 | Story 12.1 |

### 4.3 Obsidian Plugin集成

| 功能 | 实施位置 | 说明 |
|------|---------|------|
| 备份文件夹隐藏 | Story 13.1 | 在文件浏览器中隐藏`.canvas_backups/` |
| 右键菜单"保护备份" | Story 13.5 | 允许用户手动标记重要备份 |

---

## 5. 验收检查清单

### 5.1 Story 12.1实施时检查

- [ ] `get_vault_root()`函数正确实现并测试
- [ ] `get_backup_path()`函数正确实现并测试
- [ ] `CanvasBackupCheckpointer`类正确扩展PostgresSaver
- [ ] 每次checkpoint创建时自动生成备份文件
- [ ] 备份文件命名符合规范：`{canvas_name}_{checkpoint_id}.canvas`
- [ ] 备份清理机制测试通过（超过50个时自动删除）
- [ ] 手动保护机制测试通过（受保护的备份不被删除）
- [ ] 性能测试：备份创建+清理 <100ms

### 5.2 Story 13.1实施时检查

- [ ] `.canvas_backups/`文件夹在Obsidian中默认隐藏
- [ ] 用户可通过设置查看隐藏文件夹（如需要）

### 5.3 Story 13.5实施时检查

- [ ] 右键菜单显示"保护此备份 🔒"选项
- [ ] 点击后正确创建`.protected`标记文件
- [ ] 显示确认通知

---

## 6. 高级行动计划

### ✅ 已完成行动

1. ✅ 获得用户批准此变更提案
2. ✅ 更新PRD文档（编辑#1, #2, #3）
3. ✅ 保存Sprint变更提案文档到`docs/`

### 📋 Story 12.1实施时行动

1. 实现`get_vault_root()`和`get_backup_path()`函数
2. 实现`CanvasBackupCheckpointer`（扩展PostgresSaver）
3. 实现`cleanup_old_backups()`清理机制
4. 实现`is_protected_backup()`保护检查
5. 编写单元测试和集成测试
6. 执行扩展的验收标准

### 📋 Epic 13实施时行动

1. **Story 13.1**: 在Obsidian Plugin中配置`.canvas_backups/`为隐藏文件夹
2. **Story 13.5**: 实现右键菜单"保护此备份"功能
3. 测试备份文件夹在Obsidian中的可见性

---

## 7. Agent移交计划

**移交对象**: SM Agent（Scrum Master）

**移交内容**:
1. ✅ PRD已更新，Story 12.1验收标准已扩展
2. ✅ 技术实现规范已详细记录在Section 3.6.6
3. ✅ 验收检查清单已准备好

**SM Agent后续工作**:
- 在Story 12.1开发时引用Section 3.6.6的技术规范
- 确保Dev Agent实施所有7条新的验收标准
- 在Story 13.1和13.5开发时确保Obsidian Plugin集成

**无需移交**:
- Architect Agent: 无架构变更
- Design Architect Agent: 无前端设计变更
- PM Agent: 已完成所有PM职责

---

## 8. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 | 状态 |
|------|-------|------|---------|------|
| 备份文件过多占用磁盘空间 | 中 | 低 | 默认保留50个，定期自动清理 | ✅ 已缓解 |
| 用户误删`.canvas_backups/`文件夹 | 低 | 中 | 文件夹隐藏+文档说明 | ✅ 已缓解 |
| 备份操作影响性能 | 低 | 低 | 要求<100ms，异步清理 | ✅ 已缓解 |
| 跨平台路径兼容性问题 | 低 | 中 | 使用pathlib.Path，多平台测试 | ✅ 已规避 |

---

## 9. 变更提案批准

**提案人**: Sarah (PM Agent)
**审批人**: 用户
**批准日期**: 2025-11-12
**批准状态**: ✅ **已批准并实施**

**实施记录**:
- ✅ 2025-11-12: 编辑 #1 完成（NFR2扩展）
- ✅ 2025-11-12: 编辑 #2 完成（Section 3.6.6新增小节）
- ✅ 2025-11-12: 编辑 #3 完成（Story 12.1验收标准扩展）
- ✅ 2025-11-12: Sprint变更提案文档保存

---

## 10. 参考文档

- **PRD主文档**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
- **NFR2位置**: Line 1348-1365
- **Section 3.6.6**: Line 3415-3665
- **Epic 12定义**: Line 3847+
- **Story 12.1定义**: Line 3850-3878

---

## 11. 课程修正流程总结

本次课程修正遵循了完整的BMad方法论流程：

### 📋 完成的Checklist项

**Section 1: 理解触发点和背景** ✅
- [x] 触发Story识别：PRD实施前发现的设计不足
- [x] 问题类型：新发现的需求
- [x] 核心问题：备份文件组织策略缺失
- [x] 证据收集：PRD Line 3449分析

**Section 2: Epic影响评估** ✅
- [x] 当前Epic分析：Epic 12需要修改
- [x] 未来Epic分析：Epic 13需要配合
- [x] Epic影响总结：无需新增/删除Epic

**Section 3: 文档冲突和影响分析** ✅
- [x] PRD审查：识别3处需要更新的位置
- [x] 架构文档审查：无需修改
- [x] 文档影响总结：仅PRD需要更新

**Section 4: 前进路径评估** ✅
- [x] 选项1（直接调整）：✅ 推荐
- [x] 选项2（回滚）：❌ 不适用
- [x] 选项3（重新范围界定）：❌ 不必要
- [x] 路径选择：选项1

**Section 5: Sprint变更提案生成** ✅
- [x] 问题识别总结
- [x] Epic影响总结
- [x] 文档调整需求
- [x] 推荐路径和理由
- [x] MVP影响评估
- [x] 高级行动计划
- [x] Agent移交计划

**Section 6: 最终审查和批准** ✅
- [x] 提案审查完成
- [x] 用户批准获得
- [x] PRD更新确认
- [x] 下一步行动确认

### 🎯 关键成果

1. **分析深度**: 系统性地分析了问题根源、影响范围、解决方案
2. **文档质量**: 生成了详细的技术规范和实施指南
3. **风险管理**: 识别并缓解了所有潜在风险
4. **协作流程**: 清晰的Agent移交和后续行动计划
5. **用户价值**: 直接解决用户痛点，提升文件管理体验

---

**文档结束**

**变更提案状态**: ✅ **已批准并完全实施**
**下一步**: SM Agent在Story 12.1开发时引用本提案和PRD Section 3.6.6
