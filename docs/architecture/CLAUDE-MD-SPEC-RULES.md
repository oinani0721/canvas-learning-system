# CLAUDE.md 规范同步规则（复制到 CLAUDE.md）

将以下内容添加到你的 `~/.claude/CLAUDE.md` 文件中：

---

## 🔴 规范文档防腐败规则 (Anti-Stale Spec Rules)

> **问题根源**: 过时的 OpenAPI/Schema 文档导致 AI 产生幻觉，实现与实际 API 不符

### 规范文档时效性检查（强制！）

| 文档类型 | 位置 | 最大有效期 | 超期处理 |
|----------|------|-----------|----------|
| OpenAPI 规范 | `openapi.json` | 7 天 | 🔴 必须重新生成 |
| JSON Schema | `specs/data/*.json` | 30 天 | 🟡 建议验证 |
| Pact 契约 | `pacts/*.json` | 14 天 | 🟡 建议重新运行测试 |

### 🔴 强制检查点（Blocking）

#### 1. 开始开发 Story 前
```bash
# 必须先检查规范时效性
python scripts/spec-tools/verify-sync.py --json

# 如果 age_days > 7，必须先更新：
cd backend && python ../scripts/spec-tools/export-openapi.py
```

**如果跳过此检查：**
- ❌ 可能基于过时的 API 定义开发
- ❌ 导致前后端契约不一致
- ❌ 产生"规范说有但代码没有"的幻觉

#### 2. API 代码变更后（立即！）
```bash
# 任何对以下目录的修改，必须立即更新规范：
# - backend/app/api/**
# - backend/app/models/**
# - backend/app/schemas/**

cd backend && python ../scripts/spec-tools/export-openapi.py --stats
git add ../openapi.json
```

**触发条件：**
- ✅ 新增 API 端点
- ✅ 修改请求/响应结构
- ✅ 更改路径参数
- ✅ 修改状态码
- ✅ 添加/删除字段

#### 3. Story 完成、创建 PR 前
```bash
# 验证同步状态
python scripts/spec-tools/verify-sync.py

# 必须同步率 >= 95%，否则：
# - 找出差异原因
# - 更新规范或代码
```

### 🔴 规范信任规则

#### 规范可信任的条件
```
✅ openapi.json 修改时间 < 7 天
✅ verify-sync.py 同步率 >= 95%
✅ 最近一次 CI 的 Dredd 测试通过
```

#### 规范不可信任时
```
🔴 openapi.json 修改时间 > 7 天
   → 不要相信规范中的 API 定义
   → 必须直接读取 backend/app/api 代码确认

🔴 verify-sync.py 报告差异
   → 差异部分以代码为准
   → 规范中该部分视为过时

🔴 CI 中 Dredd 测试失败
   → 规范与实际 API 不一致
   → 需要调查根因
```

### 🔴 幻觉防护输出格式

当引用规范文档时，必须标注时效性：

```markdown
## API 参考

**规范来源**: openapi.json
**规范年龄**: 3 天 ✅ (< 7 天阈值)
**同步状态**: 98.5% ✅

根据 OpenAPI 规范，`POST /api/v1/memory/search` 接口...
```

如果规范过时：

```markdown
## API 参考

**规范来源**: openapi.json
**规范年龄**: 15 天 🔴 (> 7 天阈值)
**同步状态**: 未知

⚠️ **规范可能过时，以下信息需要代码验证**

根据代码 `backend/app/api/v1/endpoints/memory.py:L45`...
```

### 🔴 BMad 开发流程集成

#### Dev Agent 激活时
```yaml
pre-development-check:
  1. 检查 openapi.json 年龄
  2. 如果 > 7 天:
     - 运行 export-openapi.py
     - 或警告用户规范可能过时
  3. 读取并信任最新规范
```

#### Story 完成时
```yaml
completion-check:
  1. 运行 verify-sync.py
  2. 如果 API 有变更:
     - 必须更新 openapi.json
     - 将更新加入 commit
  3. Debug Log 记录规范变更
```

### 🔴 Git Commit 自动同步

#### 安装 pre-commit hook
```bash
# Windows (在 Git Bash 中运行)
cp scripts/spec-tools/pre-commit-spec-sync.sh .git/hooks/pre-commit

# 或手动创建 .git/hooks/pre-commit
```

#### Hook 行为
```
git commit 触发
    ↓
检测 staged 文件是否包含 API 变更
    ↓
如果有 API 变更:
    ├── 自动运行 export-openapi.py
    ├── 将 openapi.json 加入 commit
    └── 继续 commit
    ↓
如果无 API 变更:
    └── 直接继续 commit
```

### 🔴 规范过时的危险信号

当你看到以下情况，规范很可能已过时：

| 信号 | 含义 | 行动 |
|------|------|------|
| Story 提到的端点在 openapi.json 中不存在 | 规范未更新 | 读取代码确认 |
| 代码中有新的 @router 装饰器 | 规范未更新 | 运行 export |
| Pydantic 模型字段与规范不符 | 规范未更新 | 运行 export |
| CI 报告 Dredd 测试失败 | 契约不一致 | 修复代码或规范 |
| verify-sync.py 报告同步率 < 95% | 存在差异 | 调查并修复 |

### 快速命令参考

```bash
# 检查规范时效性和同步状态
python scripts/spec-tools/verify-sync.py

# 更新 OpenAPI 规范
cd backend && python ../scripts/spec-tools/export-openapi.py --stats

# 比较规范变更
oasdiff diff openapi-old.json openapi.json --format markdown

# 查看规范最后修改时间
git log -1 --format="%ci" -- openapi.json
```

---

## 添加说明

1. 将上面 `---` 之间的内容复制到你的 `~/.claude/CLAUDE.md`
2. 放在 "零幻觉调研规则" 或类似的规则部分附近
3. 确保规则的优先级足够高

这样我在开发时会：
- 自动检查规范时效性
- 在 API 变更后提醒更新规范
- 引用规范时标注时效状态
- 规范过时时以代码为准
