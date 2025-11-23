# Planning Phase Iteration Validation - End-to-End Test Guide

**Date**: 2025-11-19
**Version**: 1.0.0
**Status**: Test Guide

---

## 目录

1. [测试目标](#测试目标)
2. [前置条件](#前置条件)
3. [完整测试流程](#完整测试流程)
4. [测试场景](#测试场景)
5. [预期结果](#预期结果)
6. [故障排除](#故障排除)

---

## 测试目标

验证Planning Phase迭代管理系统的所有核心功能：
- ✅ 迭代初始化 (init-iteration.py)
- ✅ 快照创建 (snapshot-planning.py)
- ✅ 迭代验证 (validate-iteration.py)
- ✅ Breaking changes检测
- ✅ 虚拟数据检测
- ✅ 版本一致性检查
- ✅ 迭代完成 (finalize-iteration.py)
- ✅ Git pre-commit hook集成

---

## 前置条件

### 1. Git仓库初始化

```bash
cd "C:\Users\ROG\托福\Canvas"

# 初始化Git（如果尚未初始化）
git init

# 配置Git用户信息
git config user.name "Canvas Developer"
git config user.email "dev@canvas-learning.local"

# 配置CRLF处理（Windows）
git config core.autocrlf true
git config core.safecrlf false

# 创建.gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class

# BMad Core temporary files
.bmad-core/planning-iterations/snapshots/temp-*.json
EOF

# 创建初始commit
git add .
git commit -m "Initial commit: Canvas Learning System with Planning Phase Iteration Management"
```

### 2. Python环境检查

```bash
python --version  # 需要 Python 3.9+
python -c "import yaml; import hashlib; print('Dependencies OK')"
```

### 3. 验证脚本可用性

```bash
ls scripts/*.py
# 应该看到：
# - scripts/lib/planning_utils.py
# - scripts/snapshot-planning.py
# - scripts/validate-iteration.py
# - scripts/init-iteration.py
# - scripts/finalize-iteration.py
# - scripts/diff-openapi.py
# - scripts/setup-git-hooks.py
# - scripts/add-frontmatter.py
```

---

## 完整测试流程

### 测试场景1: 完整的迭代周期（Happy Path）

#### Step 1: 初始化迭代1

```bash
python scripts/init-iteration.py
```

**预期输出**:
```
============================================================
🔧 Initialize Planning Phase Iteration
============================================================

✅ Git working directory is clean
⏳ Creating baseline snapshot...
   Snapshot saved: .bmad-core/planning-iterations/snapshots/iteration-001.json
✅ OpenAPI specs backed up to specs/api/versions/
✅ Pre-checklist generated: .bmad-core/checklists/pre-correct-course-iteration-001.md

📋 Pre-Iteration Checklist:
1. [ ] Define iteration goal
2. [ ] Review current PRD version
3. [ ] Identify affected Epics
4. [ ] Backup current state (✅ Done automatically)

Iteration 1 initialized successfully!
```

#### Step 2: 模拟Planning Phase修改

创建测试修改来模拟 `@pm *correct course` 的效果：

```bash
# 创建新的Epic文档
cat > docs/epics/epic-test-001.md << 'EOF'
# Epic Test 001: Test Epic for Iteration Validation

**Version**: 1.0.0
**Status**: Planning
**Created**: 2025-11-19

## Description
This is a test Epic for validating the iteration management system.

## User Stories
- Story 1: Test story description
- Story 2: Another test story
EOF

# 修改PRD（增加Epic引用）
# (实际场景中由PM agent自动修改)
```

#### Step 3: 创建快照

```bash
python scripts/snapshot-planning.py --iteration 2 --verbose
```

**预期输出**:
```
============================================================
📸 Create Planning Phase Snapshot
============================================================

⏳ Scanning Planning Phase files...

Found files:
- PRD: 3 file(s)
- Architecture: 5 file(s)
- Epics: 14 file(s)  ← 包含新创建的epic-test-001.md
- Stories: 45 file(s)
- API Specs: 2 file(s)
- Data Models: 8 file(s)

⏳ Computing file hashes...
⏳ Extracting metadata...
⏳ Saving snapshot...

✅ Snapshot created: .bmad-core/planning-iterations/snapshots/iteration-002.json

Statistics:
- Total files: 77
- Git commit: abc12345
- Timestamp: 2025-11-19T12:00:00Z
```

#### Step 4: 验证迭代（对比Iteration 1 vs 2）

```bash
python scripts/validate-iteration.py --previous 1 --current 2 --output validation-report.md
```

**预期输出**:
```
============================================================
🔍 Validate Planning Phase Iteration
============================================================

⏳ Loading snapshots...
   Previous: iteration-001.json
   Current: iteration-002.json

⏳ Running validation checks...
   ✅ PRD validation
   ✅ Architecture validation
   ✅ Epic validation
   ✅ OpenAPI validation
   ✅ Mock data detection

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validation Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Validation Status: PASSED (0 breaking changes)
⚠️  Warnings: 1

Warnings:
1. ⚠️  New Epic added: epic-test-001.md
   Recommendation: Ensure Epic is traced to FR in PRD

Informational:
1. ℹ️  Files modified: 1
2. ℹ️  Files added: 1

Report saved to: validation-report.md
```

#### Step 5: 查看验证报告

```bash
cat validation-report.md
```

**预期内容**:
```markdown
# Planning Phase Iteration Validation Report

**生成时间**: 2025-11-19 12:00:00
**Previous Iteration**: 1
**Current Iteration**: 2
**Git Commit**: abc12345

---

## Summary

**Validation Status**: ✅ PASSED
**Breaking Changes**: 0
**Warnings**: 1
**Informational**: 2

---

## ⚠️ Warnings

### New Epic Added
⚠️ **docs/epics/epic-test-001.md** was added

**Details**:
- Epic ID: epic-test-001
- Status: Planning
- Stories: 2

**Recommendation**: Ensure this Epic is traced to a Functional Requirement in PRD

---

## ℹ️ Informational Changes

### Files Modified
- docs/epics/epic-test-001.md (new file)

---

## Version Compatibility Matrix

| Document | Previous | Current | Status |
|----------|----------|---------|--------|
| PRD | v1.0.0 | v1.0.0 | ⚠️  No increment |
| Architecture | v1.3.0 | v1.3.0 | ✅ Current |
| Agent API | v1.0.0 | v1.0.0 | ✅ Current |

---

## Recommendations

1. ✅ No breaking changes - safe to proceed
2. ⚠️  Consider incrementing PRD version to v1.1.0
3. ✅ Validation passed

Exit code: 0
```

#### Step 6: 完成迭代

```bash
python scripts/finalize-iteration.py
```

**预期输出**:
```
============================================================
🏁 Finalize Planning Phase Iteration
============================================================

⏳ Creating final snapshot...
✅ Snapshot created: iteration-002.json

⏳ Running final validation...
✅ Validation passed (0 breaking changes, 1 warning)

⏳ Updating iteration log...
✅ Entry added to .bmad-core/planning-iterations/iteration-log.md

⏳ Generating post-checklist...
✅ Post-checklist saved: .bmad-core/checklists/post-correct-course-iteration-002.md

🏷️  Creating Git tag: planning-v2
✅ Git tag created

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Iteration 2 Finalized Successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
- Files modified: 1
- Files added: 1
- PRD: v1.0.0 (no change)
- Architecture: v1.3.0 (no change)
- Git tag: planning-v2

Next steps:
1. Review post-checklist
2. Commit changes: git commit -m "Iteration 2: Add test Epic"
3. Push to remote (optional)
```

---

### 测试场景2: Breaking Changes检测

#### Step 1: 创建Breaking Change

模拟删除API endpoint（这是breaking change）：

```bash
# 备份当前API spec
cp specs/api/agent-api.openapi.yml specs/api/agent-api.openapi.yml.bak

# 删除一个endpoint（模拟breaking change）
# (实际操作：手动编辑 agent-api.openapi.yml，删除一个endpoint)
```

#### Step 2: 运行验证

```bash
python scripts/validate-iteration.py --previous 2 --current 3
```

**预期输出**:
```
============================================================
🔍 Validate Planning Phase Iteration
============================================================

⏳ Running validation...

❌ Breaking Changes Detected!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validation Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Validation Status: FAILED
🔴 Breaking Changes: 2

Breaking Changes:
1. 🔴 **Endpoint Deleted**: DELETE /api/analyze/{node_id}
   Impact: Existing clients will break
   Recommendation: Deprecate instead of deleting, or increment MAJOR version

2. 🔴 **OpenAPI spec hash changed without version increment**
   Previous: 7f8a9b3c...
   Current: 4d5e6f7a...
   Version: v1.0.0 (no change)
   Recommendation: Increment API version to v2.0.0

Report saved to: validation-report.md
Exit code: 1
```

#### Step 3: 尝试Finalize（应该被阻止）

```bash
python scripts/finalize-iteration.py
```

**预期输出**:
```
============================================================
🏁 Finalize Planning Phase Iteration
============================================================

⏳ Running final validation...

❌ Breaking changes detected! Cannot finalize iteration.

Options:
  A. Fix breaking changes and retry
  B. Accept breaking changes: python scripts/finalize-iteration.py --breaking
  C. Rollback: git checkout previous-tag

Details: 2 breaking changes detected
Review: validation-report.md

Exit code: 1
```

#### Step 4: 使用--breaking标志强制接受

```bash
python scripts/finalize-iteration.py --breaking
```

**预期输出**:
```
⚠️  WARNING: Accepting breaking changes!

This will:
- Increment API version to v2.0.0 (MAJOR)
- Require migration guide for consumers
- Create tag: planning-v3-BREAKING

Continue? [yes/no]: yes

✅ Breaking changes accepted
⏳ Finalizing with BREAKING flag...
   API version: v1.0.0 → v2.0.0
   Updated CHANGELOG.md
   Created tag: planning-v3-BREAKING

⚠️  IMPORTANT NEXT STEPS:
1. Document migration path in specs/api/versions/CHANGELOG.md
2. Notify all stakeholders
3. Update consumer applications

Iteration 3 finalized.
```

---

### 测试场景3: 虚拟数据检测

#### Step 1: 引入虚拟数据

```bash
# 修改Epic文档，添加mock数据
cat > docs/epics/epic-test-002.md << 'EOF'
# Epic Test 002: Mock Data Test

## Test Data
- user_id: "mock_user_123"
- email: "fake_email@example.com"
- data: "dummy_data_for_testing"
EOF
```

#### Step 2: 运行验证

```bash
python scripts/validate-iteration.py --previous 3 --current 4
```

**预期输出**:
```
⚠️  Mock Data Detected!

Details:
1. ⚠️  **docs/epics/epic-test-002.md** contains mock data patterns
   Patterns found:
   - "mock_user_123" (line 5)
   - "fake_email@example.com" (line 6)
   - "dummy_data_for_testing" (line 7)

   Recommendation: Replace with real data or placeholder descriptions

Warnings: 1
Exit code: 0 (warning only, not blocking)
```

---

### 测试场景4: Git Pre-Commit Hook测试

#### Step 1: 安装Hook

```bash
python scripts/setup-git-hooks.py
```

**预期输出**:
```
============================================================
🔧 Git Hooks Setup for Planning Phase
============================================================

⏳ Installing pre-commit hook...
✅ Hook installed: .git/hooks/pre-commit
✅ Hook is executable

⏳ Testing hook...
✅ Hook test passed

✅ Git hooks setup complete!
```

#### Step 2: 尝试Commit（有Breaking Change）

```bash
# 修改API spec（breaking change）
# ... (手动修改)

git add specs/api/agent-api.openapi.yml
git commit -m "Update API spec"
```

**预期输出**:
```
🔍 Pre-commit: Validating Planning Phase changes...

⏳ Creating temporary snapshot...
⏳ Running validation...

❌ Breaking Changes Detected!

Details:
- Endpoint deleted: POST /api/nodes
- Required field removed: node.title

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Commit blocked by validation hook!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To proceed:
1. Fix breaking changes
2. Run: git commit  (hook will re-validate)

Or bypass validation:
git commit --no-verify  (NOT recommended)
```

---

## 预期结果

### 成功标准

1. **迭代初始化**
   - ✅ Baseline snapshot创建成功
   - ✅ OpenAPI specs备份到versions/
   - ✅ Pre-checklist生成

2. **快照创建**
   - ✅ 所有Planning文件被扫描
   - ✅ 文件hash正确计算
   - ✅ Metadata正确提取
   - ✅ JSON格式valid

3. **迭代验证**
   - ✅ Breaking changes正确检测（endpoint删除、schema变更）
   - ✅ 虚拟数据正确检测（mock_, fake_, dummy_）
   - ✅ 版本一致性检查通过
   - ✅ 报告格式正确（Markdown）

4. **迭代完成**
   - ✅ Iteration log正确更新
   - ✅ Git tag正确创建
   - ✅ Post-checklist生成

5. **Git Hook**
   - ✅ Hook安装成功
   - ✅ Breaking changes被阻止
   - ✅ 清洁commit允许通过

### 性能标准

- Snapshot创建: < 10s (for ~100 files)
- Validation: < 5s (for iteration comparison)
- Hook执行: < 8s (for commit validation)

---

## 故障排除

### 问题1: "Python not found"

**解决**:
```bash
# Windows
python --version
# 如果不工作，尝试：
py --version
```

### 问题2: "Git not clean"

**解决**:
```bash
git status
git add .
git commit -m "Save current work"
```

### 问题3: "Snapshot not found"

**解决**:
```bash
# 重新创建baseline
python scripts/init-iteration.py --force
```

### 问题4: "Module 'yaml' not found"

**解决**:
```bash
pip install pyyaml
```

### 问题5: "Permission denied: pre-commit hook"

**解决** (Windows):
```bash
icacls .git/hooks/pre-commit /grant Everyone:F
```

**解决** (Linux/Mac):
```bash
chmod +x .git/hooks/pre-commit
```

---

## 附录A: 测试数据清理

测试完成后，清理测试数据：

```bash
# 删除测试Epic
rm docs/epics/epic-test-*.md

# 恢复API spec
mv specs/api/agent-api.openapi.yml.bak specs/api/agent-api.openapi.yml

# 重置Git到初始状态（可选）
git reset --hard HEAD~N  # N = 测试commits数量
```

---

## 附录B: 完整测试脚本

创建自动化测试脚本：

```bash
#!/bin/bash
# test-iteration-workflow.sh

set -e  # Exit on error

echo "🧪 Starting Iteration Validation System Test"
echo "=============================================="

# Step 1: Init
echo "Step 1: Initialize iteration..."
python scripts/init-iteration.py

# Step 2: Modify
echo "Step 2: Creating test modifications..."
cat > docs/epics/epic-test-auto.md << 'EOF'
# Epic Test Auto

**Version**: 1.0.0
**Status**: Testing
EOF

# Step 3: Snapshot
echo "Step 3: Creating snapshot..."
python scripts/snapshot-planning.py --iteration 2

# Step 4: Validate
echo "Step 4: Validating changes..."
python scripts/validate-iteration.py --previous 1 --current 2

# Step 5: Finalize
echo "Step 5: Finalizing iteration..."
python scripts/finalize-iteration.py

echo "✅ Test completed successfully!"
```

---

**Last Updated**: 2025-11-19
**Test Status**: ✅ Ready for Execution
**Estimated Time**: 30-45 minutes (manual testing)
