# OpenAPI Specification Versions

此目录存储所有OpenAPI规范的历史版本，用于追踪API演进和防止迭代过程中的不一致性。

## 当前版本

- **Agent API**: v1.0.0 (`agent-api.v1.0.0.yml`)
- **Canvas API**: v1.0.0 (`canvas-api.v1.0.0.yml`)

## 版本文件命名规范

```
<api-name>.v<Major>.<Minor>.<Patch>.yml
```

示例:
- `agent-api.v1.0.0.yml` - Agent API的1.0.0版本
- `agent-api.v1.1.0.yml` - Agent API的1.1.0版本（新增功能）
- `agent-api.v2.0.0.yml` - Agent API的2.0.0版本（Breaking Changes）

## 工作副本 vs 版本快照

| 文件类型 | 位置 | 用途 |
|---------|------|------|
| 工作副本 | `specs/api/*.openapi.yml` | Planning Phase迭代时可修改 |
| 版本快照 | `specs/api/versions/*.v*.yml` | 锁定的历史版本，只读 |

## 版本管理工作流

### 1. Planning迭代过程中

工作副本可以自由修改：

```bash
# 修改工作副本
vi specs/api/agent-api.openapi.yml
```

### 2. 完成迭代时

运行`finalize-iteration.py`会自动：

```bash
# 自动执行
cp specs/api/agent-api.openapi.yml specs/api/versions/agent-api.v1.1.0.yml
```

### 3. 回滚到历史版本

```bash
# 恢复到v1.0.0
cp specs/api/versions/agent-api.v1.0.0.yml specs/api/agent-api.openapi.yml
```

## 版本对比

使用diff工具比对两个版本：

```bash
# 使用自定义脚本
python scripts/diff-openapi.py \
  specs/api/versions/agent-api.v1.0.0.yml \
  specs/api/versions/agent-api.v1.1.0.yml

# 或使用标准diff
diff -u specs/api/versions/agent-api.v1.0.0.yml \
       specs/api/versions/agent-api.v1.1.0.yml
```

## 变更历史

详细的变更历史请查看: [CHANGELOG.md](./CHANGELOG.md)

## 文件清单

| 文件 | 版本 | 日期 | 描述 |
|------|------|------|------|
| `agent-api.v1.0.0.yml` | 1.0.0 | 2025-11-19 | 初始版本 |
| `canvas-api.v1.0.0.yml` | 1.0.0 | 2025-11-19 | 初始版本 |

## 相关文档

- [CHANGELOG.md](./CHANGELOG.md) - 变更日志
- [../agent-api.openapi.yml](../agent-api.openapi.yml) - Agent API工作副本
- [../canvas-api.openapi.yml](../canvas-api.openapi.yml) - Canvas API工作副本
