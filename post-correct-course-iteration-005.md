# Post-Correct-Course Checklist

**目的**: 在完成PM agent的`*correct course`后，验证迭代一致性并正确记录变更。

**使用时机**: 在`@pm *correct course`命令完成后，提交Git commit之前

---

## ✅ 必须完成的验证项

### 1. 文件变更Review

- [ ] 已Review所有被修改的文件：
  ```bash
  git status
  git diff docs/prd.md
  git diff docs/architecture.md
  git diff specs/api/openapi.yml
  ```

- [ ] 确认变更符合本次迭代目标
- [ ] 没有意外的文件被修改

### 2. 版本号更新

- [ ] `docs/prd.md` 头部YAML的version字段已更新
- [ ] `docs/architecture.md` 头部YAML的version字段已更新
- [ ] `specs/api/openapi.yml` 的info.version已更新（如有API变更）
- [ ] 版本号符合语义化版本规范

### 3. 文档一致性检查

- [ ] PRD的Epic列表与实际Epic文件一致
- [ ] Architecture引用的PRD章节仍然存在
- [ ] OpenAPI spec与Architecture的API设计一致
- [ ] 所有FR/NFR都有对应的Epic

### 4. 运行自动化验证

```bash
# 运行迭代验证脚本（使用当前迭代号）
python scripts/validate-iteration.py --iteration {N}

# 或运行最终验证（stricter checks）
python scripts/validate-iteration.py --iteration {N} --final
```

- [ ] 验证脚本运行成功（无错误）
- [ ] 已Review生成的`iteration-{N}-validation-report.md`

### 5. Breaking Changes处理

如果验证报告中有Breaking Changes：

- [ ] 已Review所有Breaking Changes列表
- [ ] 对每个Breaking Change做出决策：
  - [ ] Accept（接受并记录原因）
  - [ ] Reject（回滚修改）
  - [ ] Modify（修改以避免breaking change）

- [ ] 如果接受Breaking Changes：
  - [ ] 更新OpenAPI spec版本号（Major version递增）
  - [ ] 在`specs/api/versions/CHANGELOG.md`中记录
  - [ ] 更新Architecture文档说明影响范围

### 6. 元数据完整性

**自动添加/更新YAML frontmatter**（推荐）：

```bash
# 自动为所有Planning文档添加frontmatter
python scripts/add-frontmatter.py --all

# 或单独处理特定文件
python scripts/add-frontmatter.py --file docs/prd.md --version "1.2.0" --iteration 4
python scripts/add-frontmatter.py --file docs/architecture.md --version "1.2.0" --iteration 4
```

- [ ] 已运行`add-frontmatter.py`自动添加/更新元数据

**手动检查文档头部的YAML frontmatter**：

```yaml
---
version: "X.Y.Z"
last_modified: "YYYY-MM-DD"
iteration: N
compatible_with:
  architecture: "vX.Y"  # PRD需要声明
  prd: "vX.Y"          # Architecture需要声明
  api_spec: "vX.Y"     # Architecture需要声明
api_spec_hash: "sha256:..."  # Architecture需要包含
changes_from_previous:
  - "变更描述1"
  - "⚠️ Breaking: 变更描述2"
---
```

- [ ] PRD的`compatible_with.architecture`正确
- [ ] Architecture的`compatible_with.prd`正确
- [ ] Architecture的`api_spec_hash`与当前OpenAPI spec一致
- [ ] `changes_from_previous`列表完整

### 7. 数据真实性检查

- [ ] 没有引入虚拟数据（mock_*, fake_*, dummy_*）
- [ ] 所有示例数据都是合理的真实场景
- [ ] API响应示例使用真实的数据结构

### 8. Architect Agent同步

如果PRD有重大变更，需要Architect更新Architecture：

- [ ] 运行`@architect`更新architecture.md
- [ ] 要求Architect基于`specs/api/openapi.yml vX.Y`（指定版本）
- [ ] 禁止Architect删除现有组件（只能deprecate）

---

## 🔍 深度验证（可选但推荐）

### Epic依赖关系

- [ ] 使用Mermaid图检查Epic依赖是否有环
- [ ] 所有Epic的prerequisite仍然存在

### API Contract一致性

```bash
# 运行OpenAPI diff
python scripts/diff-openapi.py \
  specs/api/versions/openapi.vX.Y-1.yml \
  specs/api/openapi.yml
```

- [ ] Review所有API变更
- [ ] Breaking changes已明确标记

### Architecture决策记录（ADR）

- [ ] 重要变更已记录到ADR
- [ ] ADR编号和PRD版本关联

---

## 📋 提交准备

### Git Commit Message模板

```
Planning Iteration N: [简短描述]

PRD: vX.Y → vX.Y+1
Architecture: vX.Y → vX.Y+1
API Spec: vX.Y (unchanged) 或 vX.Y → vX.Y+1

Changes:
- 新增FR-XX: [描述]
- 修改NFR-YY: [描述]
- ⚠️ Breaking: [描述]

Validation: ✅ Passed
Snapshot: iteration-NNN.json

Refs: #issue-number (if applicable)
```

- [ ] Commit message已准备好
- [ ] Commit message包含所有关键信息

### Git操作

- [ ] 运行`git add`添加所有变更文件
- [ ] 运行`git commit -m "..."`提交
- [ ] 创建Git Tag: `git tag -a planning-vX.Y -m "PRD vX.Y + Arch vX.Y"`

---

## 🎯 Finalize Iteration

运行完成脚本：

```bash
python scripts/finalize-iteration.py

# 脚本会自动：
# 1. 生成最终snapshot
# 2. 更新iteration-log.md
# 3. 创建Git tag
# 4. 生成迭代总结报告
```

- [ ] Finalize脚本运行成功
- [ ] `iteration-log.md`已更新
- [ ] Snapshot文件已创建

---

## 🚦 Gate Decision

所有验证项完成后：

- ✅ **所有检查项通过 + 无Breaking Changes** → 直接提交
- 🟡 **有Warnings但已Review** → 可以提交，记录Warnings原因
- 🔴 **有未处理的Breaking Changes** → 不能提交，必须先处理

---

## 📝 Iteration Summary

本次迭代总结：

```
迭代编号: ___
目标: _______________________________________________
实际变更: _______________________________________________
Breaking Changes: _______________________________________________
遗留问题: _______________________________________________
下次迭代建议: _______________________________________________
```

---

**验证完成时间**: `_____`
**验证人**: `_____`
**下一步**: 提交Git commit 或 修复问题后重新验证


**Generated for Iteration 5**
**Timestamp**: 2025-11-25 19:36:25
