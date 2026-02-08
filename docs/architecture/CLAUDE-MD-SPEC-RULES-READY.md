# 直接复制到 CLAUDE.md 的规则块

**插入位置**: 在 "零幻觉调研规则" 之后，或 "Sequential Thinking MCP 强制使用规则" 之前

---

## 🔴🔴🔴 规范文档防腐败规则 (BLOCKING) 🔴🔴🔴

> **解决问题**: 过时的 OpenAPI/Schema 导致 AI 幻觉，实现与实际 API 不符

### 规范时效性阈值

| 文档类型 | 位置 | 新鲜期 | 过时期 | 腐败期 |
|----------|------|--------|--------|--------|
| OpenAPI 规范 | `openapi.json` | 🟢 < 3天 | 🟡 3-7天 | 🔴 > 7天 |
| JSON Schema | `specs/data/*.json` | 🟢 < 14天 | 🟡 14-30天 | 🔴 > 30天 |
| Pact 契约 | `pacts/*.json` | 🟢 < 7天 | 🟡 7-14天 | 🔴 > 14天 |

### ⛔ 禁止行为
- ❌ 信任 > 7 天的 OpenAPI 规范而不验证代码
- ❌ 引用规范内容时不标注时效性
- ❌ API 代码变更后不更新规范
- ❌ 跳过 `verify-sync.py` 检查直接开发
- ❌ Story 完成后不将规范变更加入 commit

### 🔴 强制检查点 (Canvas 项目)

#### 检查点 1: BMad Dev Agent 激活时
```bash
# 必须检查规范时效性
python scripts/spec-tools/verify-sync.py --json
```

**如果规范过时 (> 7 天):**
```
⚠️ OpenAPI 规范已过时 (最后更新: X 天前)

行动选项:
1. 运行更新: cd backend && python ../scripts/spec-tools/export-openapi.py
2. 继续但以代码为准 (规范内容视为 [未验证])

请确认如何处理？
```

#### 检查点 2: API 代码变更后 (立即触发!)
```
触发条件 (任一文件被修改):
- backend/app/api/**/*.py
- backend/app/models/**/*.py
- backend/app/schemas/**/*.py

强制行动:
cd backend && python ../scripts/spec-tools/export-openapi.py --stats
git add ../openapi.json
```

#### 检查点 3: Story 完成、PR 前
```bash
python scripts/spec-tools/verify-sync.py

# 同步率必须 >= 95%，否则 HALT
```

### 🔴 规范引用输出格式

**规范新鲜时 (可信任):**
```markdown
**规范来源**: openapi.json (2 天前更新) ✅
根据 OpenAPI 规范，`POST /api/v1/memory/search` 接受...
```

**规范过时时 (不可信任):**
```markdown
**规范来源**: openapi.json (15 天前更新) 🔴 过时
⚠️ 以下信息来自代码验证，规范仅供参考

根据代码 `backend/app/api/v1/endpoints/memory.py:L45`:
@router.post("/search", response_model=SearchResponse)
```

### 🔴 Git Commit 自动同步

**已配置 pre-commit hook:**
```
git commit 触发
    ↓
检测是否有 API 文件变更
    ↓
如果有: 自动运行 export-openapi.py → 加入 commit
如果无: 直接 commit
```

**安装 hook (如未安装):**
```bash
cp scripts/spec-tools/pre-commit-spec-sync.sh .git/hooks/pre-commit
```

### 🔴 代码优先原则 (SSOT)

> **核心原则**: 代码是唯一的事实来源（Single Source of Truth）！！！！
> 规范应该从代码自动提取，而不是反过来。

**验证链:**
```
Pydantic Models (SSOT) → OpenAPI Spec → JSON Schema
       ↓                      ↓              ↓
  [代码定义]           [自动生成]      [自动生成]
```

### 🔴 检查点 4: 规范一致性验证 (BMad Story 创建前)

```bash
# 交叉验证 OpenAPI、Pydantic、JSON Schema 一致性
python scripts/spec-tools/validate-spec-consistency.py

# 如果发现幻觉（规范有但代码没有的属性）→ BLOCKING
# 必须先修复再继续
```

**幻觉检测输出示例:**
```
CRITICAL ISSUES (must fix):
  ! [schema_hallucination]
    OpenAPI has properties not in Pydantic model (幻觉!): {'customData'}
    代码位置: app/models/schemas.py
```

### 快速命令

| 场景 | 命令 |
|------|------|
| 检查规范状态 | `python scripts/spec-tools/verify-sync.py` |
| 更新 OpenAPI | `cd backend && python ../scripts/spec-tools/export-openapi.py` |
| 导出 JSON Schema | `python scripts/spec-tools/export-json-schemas.py --compare` |
| **一致性验证** | `python scripts/spec-tools/validate-spec-consistency.py` |
| 比较 OpenAPI 变更 | `python scripts/spec-tools/diff-openapi.py old.json openapi.json` |
| 验证 ADR 哈希 | `python scripts/spec-tools/validate-hash.py` |
| 迭代完成同步 | `python scripts/spec-tools/finalize-iteration.py --story X.X` |
| 查看规范年龄 | `git log -1 --format="%cr" -- openapi.json` |

### 工具链总览

```
scripts/spec-tools/
├── export-openapi.py           # FastAPI → OpenAPI JSON
├── export-json-schemas.py      # Pydantic → JSON Schema (NEW!)
├── validate-spec-consistency.py # 交叉验证一致性 (NEW!)
├── verify-sync.py              # OpenAPI vs 代码同步率
├── diff-openapi.py             # 破坏性变更检测
├── validate-hash.py            # ADR 哈希验证
└── finalize-iteration.py       # Story 完成自动化
```

### BMad 工作流集成

```
┌─────────────────────────────────────────────────────────────────┐
│  BMad Story 开发流程 (带规范验证门控)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  /po → /dev 之前                                                 │
│  ├── python scripts/spec-tools/verify-sync.py                   │
│  └── 规范 > 7天? → 先更新规范                                    │
│                                                                 │
│  /dev → 代码变更后                                               │
│  ├── cd backend && python ../scripts/spec-tools/export-openapi.py│
│  └── python scripts/spec-tools/validate-spec-consistency.py     │
│                                                                 │
│  /qa → PR 前                                                     │
│  ├── python scripts/spec-tools/finalize-iteration.py --story X.X│
│  └── 一致性检查 + 契约测试                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

**复制说明结束**
