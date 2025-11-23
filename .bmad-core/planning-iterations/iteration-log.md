# Planning Phase Iteration Log

此文件记录所有Planning Phase的迭代历史，用于追踪PRD、Architecture、Specs等文件的演进过程。

## 迭代记录格式

每次运行`finalize-iteration.py`时会自动更新此文件。

---

## Iteration History

### Iteration 001 - 初始化 (待添加)

**日期**: YYYY-MM-DD
**PRD版本**: v1.0
**Architecture版本**: v1.0
**OpenAPI Spec版本**: v1.0
**Git Commit**: `待添加`
**Git Tag**: `planning-v1.0`

**变更摘要**:
- 初始PRD创建
- 初始Architecture设计
- 初始OpenAPI Spec定义

**关键决策**:
- （记录重要的架构决策）

**Breaking Changes**:
- 无（初始版本）

---

## 如何使用此文件

### 查看迭代历史
```bash
# 查看所有迭代
cat .bmad-core/planning-iterations/iteration-log.md

# 查看最近3次迭代
tail -n 50 .bmad-core/planning-iterations/iteration-log.md
```

### 比较两次迭代
```bash
# 查看Iteration 3相对于Iteration 2的变化
python scripts/validate-iteration.py \
  --previous .bmad-core/planning-iterations/snapshots/iteration-002.json \
  --current .bmad-core/planning-iterations/snapshots/iteration-003.json
```

### 回滚到某个迭代
```bash
# 回滚到Iteration 2
git checkout planning-v2.0
```

---

## 注意事项

1. ✅ **每次correct course后必须运行finalize-iteration.py**
2. ✅ **Breaking Changes必须明确记录并获得人工确认**
3. ✅ **OpenAPI Spec版本号必须遵循语义化版本规范**
4. ⚠️ **不要手动编辑此文件，使用脚本自动更新**
