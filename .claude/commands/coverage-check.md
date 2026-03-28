---
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - mcp__graphiti-canvas__search_memory_facts
  - mcp__graphiti-canvas__add_memory
description: 功能覆盖检查 — 死代码检测 + 利用率审计 + 安全配置扫描
argument-hint: [backend|frontend|all]
---

# /coverage-check — 功能覆盖检查

扫描技术利用率、死代码、禁用功能、安全配置问题。

**用法**: `/coverage-check $ARGUMENTS`（默认 all）

---

## Step 1: 技术栈盘点

1. 读取架构文档: `docs/architecture.md`
2. 扫描依赖文件:
   ```bash
   cat backend/requirements.txt 2>/dev/null
   cat frontend/package.json 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({**d.get('dependencies',{}), **d.get('devDependencies',{})}, indent=2))"
   ```
3. 构建技术清单

## Step 2: 死代码检测

```bash
# 未使用的导入
grep -rn "^import\|^from" backend/app/ --include="*.py" | head -30

# 定义但未调用的函数
grep -rn "^def \|^async def " backend/app/ --include="*.py" | head -30

# 禁用的功能标志
grep -rn "ENABLE_.*=false\|_ENABLED.*=false\|_DISABLED.*=true" backend/ frontend/ 2>/dev/null

# TODO/FIXME 占位
grep -rn "TODO\|FIXME\|HACK\|XXX" backend/app/ frontend/src/ --include="*.py" --include="*.ts" --include="*.tsx" 2>/dev/null | head -20

# 工具定义但未注入
grep -rn "tools.*=\|register_tool\|add_tool" backend/app/ --include="*.py" | head -10
```

## Step 3: 安全配置扫描

```bash
# CSP 配置
grep -rn "CSP\|Content-Security-Policy\|csp" frontend/ backend/ 2>/dev/null | head -5

# CORS 配置
grep -rn "CORS\|cors\|allow_origins" backend/ 2>/dev/null | head -5

# 硬编码密钥
grep -rn "api_key\|API_KEY\|password\|secret" backend/ frontend/ --include="*.py" --include="*.ts" 2>/dev/null | grep -v ".env\|test\|example" | head -5
```

## Step 4: 已知问题对照

读取 `docs/known-gotchas.md`，对照:
- G-FAKE: 假命名函数是否已修复？
- G-PIPE: 管道断裂是否已接线？

## Step 5: 输出报告

```markdown
# 覆盖检查报告
日期: [today]
范围: [backend/frontend/all]

## 摘要
| 指标 | 数值 |
|------|------|
| 技术总数 | N |
| 死代码项 | N |
| 禁用功能 | N |
| 安全问题 | N |
| 已知问题未修 | N |

## 🔴 需立即处理
1. [问题] — [文件] — [修复方式]

## 🟡 建议处理
1. [问题] — [文件]

## 死代码清单
| 文件 | 行 | 类型 | 描述 |
|------|-----|------|------|
```

## Step 6: 记录

```
add_memory("[Coverage-Check] [范围] — [死代码N项] [安全问题N项]", group_id:"canvas-dev")
```
