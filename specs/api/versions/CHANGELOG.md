# OpenAPI Specification Changelog

此文件记录所有API规范的版本变更历史。

---

## [Unreleased]

### 待添加到下一个版本

---

## [1.0.0] - YYYY-MM-DD (待添加)

### Added
- 初始API定义
- `/api/v1/canvas` endpoints
- `/api/v1/learning` endpoints
- `/api/v1/memory` endpoints

### Changed
- N/A (初始版本)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

---

## Changelog格式说明

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 规范和 [Semantic Versioning](https://semver.org/lang/zh-CN/) 版本号规则。

### 版本号规则

- **Major (X.0.0)**: Breaking Changes (不兼容的API修改)
- **Minor (x.Y.0)**: 新增功能 (向后兼容)
- **Patch (x.y.Z)**: Bug修复 (向后兼容)

### 变更类型

- **Added**: 新增功能
- **Changed**: 现有功能的变更
- **Deprecated**: 即将移除的功能
- **Removed**: 已移除的功能 (Breaking Change)
- **Fixed**: Bug修复
- **Security**: 安全性修复

### Breaking Changes标记

任何Breaking Change必须：
1. 在此CHANGELOG中明确标记为`[BREAKING]`
2. 递增Major版本号
3. 在PRD和Architecture中记录影响范围

### 示例

```markdown
## [2.0.0] - 2025-11-20

### Added
- 新增`/api/v1/export`端点用于数据导出

### Changed
- [BREAKING] `/api/v1/canvas` 返回格式从数组改为分页对象
- 优化了`/api/v1/learning/start`的响应时间

### Deprecated
- `/api/v1/legacy/canvas` - 将在v3.0.0中移除

### Removed
- [BREAKING] 移除了已废弃的`/api/v1/old-memory`端点
```

---

## 版本文件管理

每个版本的OpenAPI spec会保存在此目录：

```
specs/api/versions/
├── openapi.v1.0.0.yml  # 锁定的v1.0.0版本
├── openapi.v1.1.0.yml  # 锁定的v1.1.0版本
├── openapi.v2.0.0.yml  # 锁定的v2.0.0版本
└── CHANGELOG.md        # 本文件
```

### 工作副本

`specs/api/openapi.yml` 是当前工作副本，每次Planning迭代时可能会修改。

### 版本锁定

运行`finalize-iteration.py`时会自动：
1. 复制`openapi.yml` → `versions/openapi.vX.Y.Z.yml`
2. 更新此CHANGELOG
3. 计算hash并记录到Architecture文档

---

## 如何查看变更

### 比对两个版本

```bash
# 使用diff-openapi.py脚本
python scripts/diff-openapi.py \
  specs/api/versions/openapi.v1.0.0.yml \
  specs/api/versions/openapi.v2.0.0.yml
```

### 检查Breaking Changes

```bash
# 验证迭代会自动检测Breaking Changes
python scripts/validate-iteration.py
```

---

## 相关文档

- [OpenAPI Specification](../../openapi.yml) - 当前工作副本
- [Architecture文档](../../../docs/architecture.md) - API架构设计
- [PRD文档](../../../docs/prd.md) - 功能需求
