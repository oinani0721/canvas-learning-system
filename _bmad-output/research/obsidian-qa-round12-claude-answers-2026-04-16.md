---
title: "Obsidian 翻译问答 Round 12 主答复文件（ChatGPT 审计回应 + Vault 方案修正 + Mode 3 PoC）"
date: 2026-04-16
trigger: "用户在 Round 11 追加 1 条新批注（Line 128: Claudian 自动检测 vault）+ 粘贴 ChatGPT 对抗性审计报告（Lines 612-656: [C1]-[C4]+[I1]-[I4]+[N1]-[N3]+[FINAL]）"
type: "qa-round12-answers"
status: "awaiting-user-audit"
parent_files:
  - "[[obsidian-qa-round11-claude-answers-2026-04-16]]"
related_plan: "OBSIDIAN-QA-ROUND12-2026-04-16"
round: 12
total_sections: 4
round12_character: "诚实承认 Round 11 三个致命缺陷 + 修正为 Claudian 自动检测 vault（零文件编辑 UX）+ 逐条回应 ChatGPT 11 条审计 + Mode 3 PoC 30 行代码"
key_finding: "Round 11 的 .env 方案有 3 个致命问题（restart 不刷新 env / :ro 挡写操作 / 无 vault 隔离），修正为 Claudian 自动检测 vault 路径 → backend runtime API 切换 → vault_id 命名空间隔离。Mode 3（Obsidian Plugin spawn）需要 PoC 验证而非直接否定"
integrity_rules: "IC-1 ~ IC-8（沿用）"
---

# Obsidian 翻译问答 Round 12 主答复文件

> **阅读指引**: 本文件是 [[obsidian-qa-round11-claude-answers-2026-04-16]] 的 Round 12 修正。
>
> Round 11 的 `.env + restart` 方案被 ChatGPT 对抗性审计打了 3 个致命问题 + 用户批注明确否定"修改文件"UX。Round 12 **诚实承认缺陷** + 修正为 **Claudian 自动检测 vault（零文件编辑）** + 逐条回应全部 11 条审计发现。

## Round 12 核心修正（1 分钟版）

| 维度 | Round 11（已否定） | Round 12（修正后） |
|-----|----------------|-----------------|
| **Vault 切换 UX** | 用户编辑 `.env` + Terminal 命令 | **Claudian 自动检测**（用户零操作）|
| **Backend 切换机制** | `docker-compose restart`（不生效 [C1]）| **Runtime API** `POST /vault/switch`（绕过 @lru_cache）|
| **数据隔离** | 无（LanceDB 混用 [C4]）| **vault_id 命名空间**（每 vault 独立索引）|
| **:ro 挂载** | 阻断 CRUD（backend 写 vault）| **移除 :ro** 或**分离读写路径** |
| **Mode 3 判定** | "不可能"（无证据 [C3]）| **做 30 行 PoC 验证** |
| **MCP 安全** | auto-allow（风险 [C2]）| **新增 DEPLOYMENT_TOOLS tier** |

---

## R12-Q1 · 修正后的 Vault 切换方案（Line 128）

### 用户原批注
> "请你看一下这个方案可不可行，在我启动后端的时候，claudian 不是通过 MCP 的方式来调动后端，那么 claudian 在回答我们的问题的时候不就是可以自动检查我们当前的 vault 吗？你这些修改文件的操作，对于非技术用户来说都是不友好的，请您 deep explore 社区成熟的方案来解决。"

### 深度分析

---

#### Part A: Round 11 方案 3 个致命缺陷（诚实承认）

**缺陷 1: `docker-compose restart` 不刷新 env — [C1] 正确**

ChatGPT 审计 100% 正确。Docker 官方文档明确:
> "restart only restarts running containers, it does not reflect compose.yml changes"

Round 11 承诺的 "改 `.env` 一行 + restart 30s" 实际上**不会**把新的 `ACTIVE_VAULT` 注入容器。必须 `docker-compose up -d`（重建容器），但这对非技术用户更不友好。

**缺陷 2: backend 写入 vault 路径 — `:ro` 挂载会阻断 CRUD**

代码审计发现（Round 11 遗漏）:
```python
# canvas_service.py:714 — backend WRITES to vault
canvas_path.parent.mkdir(parents=True, exist_ok=True)
with open(canvas_path, "w", encoding="utf-8") as f:
    json.dump(canvas_data, f, indent=2, ensure_ascii=False)
```

Round 11 的 `"${VAULT_ROOT}:/app/vaults:ro"` 会导致**所有 canvas CRUD 操作 Permission Denied**。

**缺陷 3: LanceDB 无 vault 隔离 — [C4] 正确**

当前 `vault_notes` 表:
- 索引键基于**相对路径**（如 `Lecture1.md`）
- `subject` 写死 `DEFAULT_GROUP_ID`（`config.py:461`: "cs188"）
- 两个 vault 有同名文件 → 去重/删除打到**错误 vault**
- 无 `vault_id` 跟踪

**结论**: Round 11 的 Phase 1 方案**无法安全使用**。需要重新设计。

`★ Insight ─────────────────────────────────────`
- ChatGPT 的 [C1] 审计击中了 Docker Compose 一个**常见误区**——很多开发者以为 `restart` = `up`，但实际上 restart 只 SIGTERM+start 容器进程，不重建容器
- `:ro` 挂载的冲突是**纯代码审计发现**，不在 ChatGPT 审计范围内——说明双重审计（AI + 代码实读）比单一审计更可靠
- LanceDB 的相对路径索引问题根源在于系统从未设计过多 vault——PRD 原文把多 vault 标为 P2（`prd-tauri-original:520`），但代码实现只做了 P1 单 vault
`─────────────────────────────────────────────────`

---

#### Part B: 修正方案 — Claudian 自动检测 vault（零文件编辑 UX）

##### B.1 核心理念

用户批注的关键洞察: **Claudian 已经通过 MCP 连接 backend，它知道用户在哪个 vault 工作 —— 为什么还要用户手动切换？**

修正后的架构:
```
用户打开 Obsidian vault (CS189)
  ↓
用户在 Claudian 里发消息
  ↓
Claudian 读取当前工作目录 / Obsidian vault 路径
  ↓
Claudian 调用 MCP tool: switch_vault(vault_path="/Users/.../CS189")
  ↓
Backend POST /api/v1/vault/switch:
  1. 更新内存中的 active vault（绕过 @lru_cache）
  2. 触发 LanceDB vault_notes 增量索引（带 vault_id）
  3. 更新 Graphiti group_id
  ↓
返回 { status: "switched", vault: "CS189", indexed_notes: 42 }
```

**用户操作: 零**。整个切换由 Claudian 自动完成。

##### B.2 技术实现要点

**1. Claudian 如何知道当前 vault?**
- Claude Code CLI 的 `cwd` 就是用户当前 Obsidian vault 路径
- 或通过 MCP context 获取（Obsidian Plugin 可以传 vault 路径给 Claudian）
- 或 Claudian 主动问用户一次，记住后续自动使用

**2. Backend runtime vault 切换（绕过 @lru_cache）**

```python
# backend/app/api/v1/endpoints/vault.py — 新建
from app.config import get_settings

@router.post("/vault/switch")
async def switch_vault(input: SwitchVaultInput):
    """运行时切换 active vault — 无需重启 backend"""
    settings = get_settings()
    
    # 绕过 @lru_cache: 直接修改 settings 实例属性
    old_vault = settings.CANVAS_BASE_PATH
    settings.CANVAS_BASE_PATH = input.vault_path
    
    # 触发 LanceDB 索引（仅新 vault 的文件）
    from app.services.lancedb_index_service import get_lancedb_index_service
    idx_svc = get_lancedb_index_service()
    result = await idx_svc.schedule_index(
        canvas_base_path=input.vault_path,
        vault_id=input.vault_name,  # NEW: vault 命名空间
    )
    
    # 更新 Graphiti group_id
    settings.DEFAULT_GROUP_ID = input.vault_name.lower().replace(" ", "")
    
    return {
        "status": "switched",
        "old_vault": old_vault,
        "new_vault": input.vault_path,
        "group_id": settings.DEFAULT_GROUP_ID,
    }
```

**技术说明**: Pydantic BaseSettings 实例虽然被 `@lru_cache` 缓存，但**实例属性仍可修改**（`@lru_cache` 缓存的是对象引用，不是冻结对象）。直接改 `settings.CANVAS_BASE_PATH` 会影响所有后续请求。

**3. LanceDB vault_id 隔离**

```python
# 修改 vault indexing: 每条记录带 vault_id
chunk_record = {
    "text": chunk_text,
    "source_file": relative_path,
    "vault_id": vault_name,        # NEW: 命名空间隔离
    "subject_id": subject_id,
    "embedding": embedding_vector,
}
```

查询时自动过滤:
```python
# vault_notes_retriever.py — 激活 group_id Phase 4 placeholder
results = table.search(query_embedding)
    .where(f"vault_id = '{active_vault_id}'")  # NEW: 只搜当前 vault
    .limit(num_results)
```

**4. Docker 挂载修正**

```yaml
# docker-compose.yml — 移除 :ro，允许 canvas CRUD 写操作
volumes:
  - "${VAULT_ROOT}:/app/vaults"       # 不加 :ro
```

`:ro` 被移除因为 `canvas_service.py` 需要写 `.canvas` 文件。安全改由**应用层**控制（不改 vault 外的文件）。

##### B.3 为什么不用 `.env`?

| 维度 | .env 方案（Round 11） | Claudian 自动检测（Round 12） |
|-----|---------------------|---------------------------|
| 用户操作 | 编辑文件 + Terminal 命令 | **零**（Claudian 自动） |
| Docker restart | 必须（且 restart 不够，需 up）| **不需要** |
| 技术用户友好 | 中 | 高 |
| 非技术用户友好 | **低**（编辑 YAML/env 容易出错）| **高**（对话式 + 自动） |
| LanceDB 一致性 | 无保证 | vault_id 隔离保证 |
| 新增 vault | 新建文件夹（好）| 新建文件夹（同样好）|

`★ Insight ─────────────────────────────────────`
- 用户的批注实际上指出了最优解: Claudian **已经是**用户和 backend 之间的中介，让它自动检测 vault 是最自然的路径
- `@lru_cache` 缓存的是 Settings **对象引用**，不是深拷贝。直接修改实例属性是 Python 的标准行为——FastAPI 社区在 `dependency_overrides` 之外也常用此 pattern
- vault_id 命名空间不仅解决 [C4] 跨 vault 污染，还为未来的"多 vault 同时索引"留好了口子
`─────────────────────────────────────────────────`

---

#### Part C: 修正后的启动链路（用户零操作切换）

| 场景 | 用户操作 | 系统行为 |
|-----|-------|--------|
| 首次启动 | `docker-compose up -d` → 打开 Obsidian → 用 Claudian | Claudian 自动调 `/vault/switch`（检测到 cwd = CS188）|
| 切换 vault | 打开另一个 Obsidian vault → 用 Claudian | Claudian 自动调 `/vault/switch`（检测到 cwd = CS189）|
| 新增学科 | 新建 vault 文件夹 → 打开 → 用 Claudian | Claudian 调 `/vault/switch` → backend 自动索引新 vault |
| 日常学习 | 直接用 Claudian | Claudian 检测 vault 不变 → 跳过 switch |

**非技术用户体验**: "打开 Obsidian → 开始学习"。没有 Terminal、没有文件编辑、没有 restart。

---

#### Part D: Round 11 vs Round 12 对比总结

| 维度 | Round 11 | Round 12 |
|-----|---------|---------|
| 核心假设 | 用户手动管理 vault | **Claudian 自动管理** |
| Docker 依赖 | restart 切换（**不生效**）| 初始 up 一次，运行时不再碰 |
| 文件编辑 | 改 .env 一行 | **零** |
| 数据隔离 | 无 | **vault_id 命名空间** |
| :ro 冲突 | 阻断 CRUD | **移除 :ro + 应用层安全** |
| Mode 3 | 判死刑 | **PoC 验证** |
| MCP 安全 | auto-allow | **DEPLOYMENT_TOOLS tier** |

---

## R12-Q2 · ChatGPT Critical [C1]-[C4] 逐条回应

### [C1] restart 不刷新 env — 承认 + 已修正

**ChatGPT 判定**: 正确。`docker-compose restart` 不重建容器，env 变量不更新。

**Claude 回应**: **完全承认**。Round 11 的核心 UX 承诺"改 .env + restart 30s" 是伪命题。

**修正**: 不再依赖 Docker 环境变量切换。改为 **backend runtime API** `POST /vault/switch`，直接修改 Settings 实例属性，**无需重启任何服务**。

Docker 只负责初始挂载（父目录），运行时 vault 切换完全在应用层。

---

### [C2] MCP auto-allow 安全缺口 — 承认 + 提出分层

**ChatGPT 判定**: 正确。MCP backend tools 被 `sidecar.js:297-302` auto-allow，把 Docker 控制放入这个通道有提权风险。

**Claude 回应**: **承认**。项目已有 prompt injection 历史（`UNTRUSTED_*` 包装就是因此加的）。

**修正方案**: 新增 **DEPLOYMENT_TOOLS** 权限 tier:

```javascript
// sidecar.js — 新增第 4 层
const DEPLOYMENT_TOOLS = new Set([
  'check_backend_health',
  'switch_vault',
  'restart_backend',
]);

// canUseTool hook 修改:
if (DEPLOYMENT_TOOLS.has(toolName)) {
  // 需要用户确认（同 HIGH_RISK），但 timeout 更短
  const decision = await requestUserApproval(toolName, input, nodeId, id);
  return decision === 'allow'
    ? { behavior: 'allow', updatedInput: input }
    : { behavior: 'deny' };
}
```

**约束**:
- 不允许自由命令拼接（只固定 allowlist）
- 固定 project root（不能通过参数改）
- 固定服务集合（只 neo4j + backend）
- 每次执行需用户点确认

---

### [C3] Mode 3 判定太急 — 承认 + 附 PoC 代码

**ChatGPT 判定**: 正确。Obsidian 官方文档的 `isDesktopOnly` 明确表示桌面插件可用 Node/Electron API。

**Claude 回应**: **承认过度判定**。Round 10/11 声称"Electron 沙箱硬约束禁止 spawn" 的证据**不够一手**。Smart Connections/Khoj/Copilot 不自动启动可能是**产品选择**而非**技术不可能**。

**PoC 代码**（30 行，用户可直接在 Obsidian 里测试）:

```typescript
// main.ts — Obsidian Plugin PoC: test child_process on desktop
import { Plugin, Platform, Notice } from 'obsidian';

export default class TestSpawnPlugin extends Plugin {
  async onload() {
    if (!Platform.isDesktopApp) {
      console.log('Skipping: not desktop');
      return;
    }

    this.addCommand({
      id: 'test-docker-spawn',
      name: 'PoC: Test Docker spawn from Plugin',
      callback: async () => {
        try {
          // 尝试 require Node.js child_process
          const { exec } = require('child_process');
          
          exec('docker compose version', { timeout: 10000 },
            (err: Error | null, stdout: string, stderr: string) => {
              if (err) {
                new Notice(`❌ exec failed: ${err.message}`);
                console.error('PoC spawn error:', err);
              } else {
                new Notice(`✅ Docker: ${stdout.trim()}`);
                console.log('PoC spawn success:', stdout);
              }
            }
          );
        } catch (e) {
          new Notice(`❌ require('child_process') failed: ${e}`);
          console.error('PoC require error:', e);
        }
      },
    });
  }
}
```

**PoC 测试步骤**:
1. 新建 Obsidian vault 的 `.obsidian/plugins/test-spawn/` 目录
2. 创建 `manifest.json`:
   ```json
   {
     "id": "test-spawn",
     "name": "Test Spawn PoC",
     "version": "0.0.1",
     "minAppVersion": "1.0.0",
     "isDesktopOnly": true
   }
   ```
3. 编译上述 TypeScript 为 `main.js`（或直接手写 JS 版）
4. 在 Obsidian Settings → Community plugins → 启用
5. Cmd+P → "PoC: Test Docker spawn from Plugin"
6. 观察 Notice:
   - `✅ Docker: Docker Compose version v2.x.x` → Mode 3 **可行**
   - `❌ exec failed: ...` → Mode 3 **确实不可行**
   - `❌ require('child_process') failed: ...` → Electron 真的阻断了

**结果决定架构**:
- 如果 ✅ → Mode 3 重新评估（Plugin 可直接管理 Docker）
- 如果 ❌ → Mode 3 正式关闭（Round 10/11 判定有效）

---

### [C4] 跨 vault 污染 — 承认 + vault_id 命名空间

**ChatGPT 判定**: 正确。LanceDB 索引基于相对路径，同名文件跨 vault 会污染。

**Claude 回应**: **完全承认**。当前代码:
- `metadata.py:489` — vault 索引用 `DEFAULT_GROUP_ID`（硬编码 "cs188"）
- `lancedb_index_service.py` — 无 vault 追踪
- `vault_notes_retriever.py:138-152` — `group_id` 参数是 Phase 4 **placeholder**（未激活）

**修正方案**: vault_id 成为一等命名空间

| 层 | 当前 | 修正后 |
|----|-----|------|
| LanceDB `vault_notes` 表 | 无 vault 标识 | 新增 `vault_id` 列 |
| LanceDB `file_fingerprints` | 相对路径做键 | `vault_id + 相对路径` 复合键 |
| Graphiti `group_id` | 硬编码 "cs188" | `{vault_name}:{subject}:{canvas_name}` |
| Dead letter queue | 无 vault 标识 | 新增 `vault_id` 字段 |
| Pending index operations | 无 vault 标识 | 新增 `vault_id` 字段 |

已有基础设施支撑:
- `vault_notes_retriever.py:138` 已有 `group_id` 参数 → 激活它
- `subject_resolver.py:189-240` 已有 4 级 group_id 推导 → 加 vault 层级
- `backend/tests/unit/test_vault_notes_group_filter.py` 已有 5 个 scenario → 扩展

---

## R12-Q3 · ChatGPT Important [I1]-[I4] 逐条回应

### [I1] Health vs Availability 混淆 — 承认 + 统一定义

**ChatGPT 判定**: 正确。3 个健康端点语义不一致。

**当前混乱**:
| 端点 | 检查内容 | 返回 200 条件 |
|-----|--------|------------|
| `GET /api/v1/health` | app status + 组件列表 | 部分组件降级仍 200 |
| `GET /api/v1/system/health` | Neo4j + Ollama + LanceDB | 全部正常才 200 |
| Docker healthcheck | `curl /api/v1/health` | HTTP 200 |

**修正建议**: 统一为 **3 级状态**:

| 状态 | 定义 | Plugin 显示 |
|-----|-----|----------|
| `ready` | 全部组件可用（含 Graphiti） | 🟢 绿灯 |
| `degraded` | 核心可用但部分降级 | 🟡 黄灯 |
| `unavailable` | 核心不可用 | 🔴 红灯 |

统一端点: `GET /api/v1/health` 返回明确的 `readiness` 字段（区分于 `liveness`）。

---

### [I2] External network 依赖 — 承认 + 条件化

**ChatGPT 判定**: 正确。`cliproxyapi_default` 不存在时 Compose 直接报错。

**修正**: 在 `docker-compose.yml` 中将 external network **条件化**:

```yaml
networks:
  canvas-network:
    driver: bridge
  cliproxyapi-network:
    external: true
    name: cliproxyapi_default
    # 非技术用户: 注释掉这 3 行即可
```

或更好的方案: backend 服务只连 `canvas-network`，cliproxyapi 连接由用户显式 opt-in（`--profile proxy`）。

---

### [I3] 配置漂移 — 承认 + 统一源

**ChatGPT 判定**: 正确。Root `.env` + `backend/.env` + Docker env 三处可能冲突。

**修正**: **统一到项目根 `.env`**:
- 删除 `backend/.env` 中与 Docker 环境变量重复的条目
- `backend/app/config.py` 的 `model_config` 指向 `../../.env`（或移除 `load_dotenv`，统一由 Docker 注入）
- 文档化: **唯一改动文件 = 项目根 `.env`**

---

### [I4] Bind mount 路径敏感 — 承认 + 文档化

**ChatGPT 判定**: 正确。路径迁移/Docker Desktop 文件共享配置变化会导致 mount 失败。

**修正**: 创建 **部署预检清单**（`docs/deployment-checklist.md`）:

1. ✅ Docker Desktop 已安装且运行
2. ✅ `VAULT_ROOT` 路径存在且 Docker Desktop File Sharing 包含此路径
3. ✅ Neo4j 端口 7691/7478 未被占用
4. ✅ `backend/.env` 与根 `.env` 的 `NEO4J_PASSWORD` 一致
5. ✅ Ollama native 已安装（Mac: `brew install ollama && ollama serve`）
6. ✅ cliproxyapi 已启动（或 docker-compose.yml 已注释 external network）

---

## R12-Q4 · ChatGPT Nice-to-have [N1]-[N3] 回应

### [N1] vault_id 一等命名空间 — 纳入修正方案

**ChatGPT 建议**: vault 不应只是 env var，应成为一等命名空间。

**Claude 回应**: **完全采纳**。已在 R12-Q2 [C4] 修正方案中实现:
- LanceDB 表带 `vault_id` 列
- `file_fingerprints` 用 `vault_id + 相对路径` 复合键
- Graphiti group_id 格式: `{vault_name}:{subject}:{canvas_name}`
- Dead letter / pending operations 带 vault_id

这是修正方案的**核心组成部分**，不是 nice-to-have。

---

### [N2] 部署工具不走 auto-allow — 新增 DEPLOYMENT_TOOLS tier

**ChatGPT 建议**: 基础设施控制不应 auto-allow。

**Claude 回应**: **完全采纳**。已在 R12-Q2 [C2] 修正方案中设计:
- 新增 `DEPLOYMENT_TOOLS` Set（`switch_vault`, `check_backend_health`, `restart_backend`）
- 每次执行需用户审批（permission card）
- 不允许自由命令拼接

---

### [N3] Mode 3 PoC — 30 行代码已给出

**ChatGPT 建议**: 做最小 PoC 验证 Obsidian Plugin child_process。

**Claude 回应**: **完全采纳**。PoC 代码已在 R12-Q2 [C3] 给出:
- `main.ts` 30 行
- `manifest.json` 7 行
- 测试步骤 6 步
- 结果决定架构（✅ → Mode 3 可行 / ❌ → 正式关闭）

---

## Round 12 总结

### 对 ChatGPT [FINAL] 判定的回应

ChatGPT [FINAL]:
> "方案方向可以成立，但当前版本最大的风险不是 Neo4j 或 Docker 本身，而是你们把一个'实际上不会生效的 vault 切换流程'和一个'未经充分验证就被判死刑的插件自动启动假设'写成了架构前提"

**Claude 回应**: **完全同意**。Round 11 的两个错误前提:
1. "restart 能刷新 env" → **错**（Docker 文档明确否定）
2. "Plugin 不可能 spawn" → **未验证**（官方文档指向相反方向）

Round 12 已修正:
1. 不再依赖 Docker 环境变量 → **backend runtime API**
2. 不再凭印象判死 Mode 3 → **30 行 PoC 验证**

### 核心答案总结

| 发现 | 承认/否认 | 修正措施 |
|-----|---------|--------|
| [C1] restart 不刷新 | ✅ 完全承认 | Runtime API /vault/switch |
| [C2] MCP auto-allow | ✅ 承认风险 | DEPLOYMENT_TOOLS tier |
| [C3] Mode 3 过度否定 | ✅ 承认 | 30 行 PoC 代码 |
| [C4] 跨 vault 污染 | ✅ 完全承认 | vault_id 命名空间 |
| [I1] Health 混淆 | ✅ 承认 | 统一 3 级状态 |
| [I2] External network | ✅ 承认 | 条件化/opt-in |
| [I3] 配置漂移 | ✅ 承认 | 统一到根 .env |
| [I4] 路径敏感 | ✅ 承认 | 部署预检清单 |
| [N1] vault_id 命名空间 | ✅ 采纳 | 核心修正部分 |
| [N2] 部署工具安全 | ✅ 采纳 | 新权限 tier |
| [N3] Mode 3 PoC | ✅ 采纳 | 代码已给出 |

### 下一步期待

1. 用户测试 Mode 3 PoC（在 Obsidian 里跑 30 行代码）→ 结果决定最终架构
2. 用户确认 Claudian 自动检测方案 → 启动实施 Story
3. 如 Mode 3 PoC ✅ → 可能还需重新评估 3 种模式的优先级

### Obsidian 可导航引用

- `canvas_service.py:704-720` — backend 写 vault（`:ro` 冲突来源）
- `config.py:789-802` — `@lru_cache` + `get_settings()`（runtime 修改可行性）
- `vault_notes_retriever.py:126-231` — group_id Phase 4 placeholder + common-note 降级
- `subject_resolver.py:159-241` — 4 级 group_id 推导（vault 层级待加）
- `metadata.py:445-599` — 3 个 vault indexing API
- `sidecar.js:52-66,297-302` — 权限模型（auto-allow MCP 证据）
- `episode_worker.py:44-60` — EpisodeTask group_id 字段
- Obsidian Plugin API: `isDesktopOnly` 文档（ChatGPT [C3] 引用）

---

**下一轮触发条件**: 用户跑完 Mode 3 PoC → 结果（✅/❌）→ Round 13 最终架构定稿
