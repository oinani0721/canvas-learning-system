---
title: "Obsidian 翻译问答 Round 11 主答复文件（Vault 动态切换 + Claudian MCP 可行性证明 + ChatGPT 对抗性审查提示词）"
date: 2026-04-16
trigger: "用户在 Round 10 主文件追加 4 条 Round 11 批注（vault 动态切换方案 ×2 + MCP 可行性证明 + ChatGPT 对抗性审查提示词 + git push）"
type: "qa-round11-answers"
status: "awaiting-user-audit"
parent_files:
  - "[[obsidian-qa-round10-claude-answers-2026-04-16]]"
related_plan: "OBSIDIAN-QA-ROUND11-2026-04-16"
round: 11
total_sections: 3
round11_character: "Vault 动态切换 UX + Claudian MCP 可行性证据链 + ChatGPT Deep Research 对抗性审查提示词"
key_finding: "推荐挂载 vault 父目录（而非单独 vault），新增学科 = 新建子目录（零配置改动），切换 = 改 .env 一行 + restart 30s。MCP 可行性有 4 条独立证据（docker-manager.ts 已有 subprocess / sidecar.js 非沙箱 / G-MCP-001 daemon 先例 / stdlib 零依赖）"
explore_agents:
  - "Agent A: Round 10 新批注定位（4 条: Line 70/192/215/654）"
  - "Agent B: Frontend+Backend 代码深度审计（34 组件 + 22 服务 + 15 MCP tools + sidecar 权限模型）"
  - "Agent C: Recovered 规划文档 + PRD 部署期望 + 社区模式（3 recovered files + 原 PRD 5-step wizard spec vs 现实 gap）"
integrity_rules: "IC-1 ~ IC-8（沿用）"
---

# Obsidian 翻译问答 Round 11 主答复文件

> **阅读指引**: 本文件是 [[obsidian-qa-round10-claude-answers-2026-04-16]] 的 Round 11 延伸。
>
> Round 10 部署审计后，用户在 4 处追加批注。Round 11 基于 3 个并行 Deep Explore Agent（批注定位 + 前后端代码审计 + 规划文档/社区案例）给出 3 个 section 的深度答复。

## Round 11 核心结论（1 分钟版）

| Section | 核心答案 | 用户操作 |
|---------|--------|--------|
| **R11-Q1 Vault 切换** | 挂载**父目录** `/spring course 2026/` 而非单独 vault，新增学科 = 新建子目录 | 切 vault = 改 `.env` 一行 + `docker-compose restart backend`（30s）|
| **R11-Q2 MCP 可行性** | 4 条独立证据全部指向"可行" | 用户确认后另开 Story 实现 |
| **R11-Q3 ChatGPT 审计** | 完整 `copy-to-deep-research` 块已生成 | Cmd+V 粘贴给 ChatGPT Deep Research |

---

## R11-Q1 · Vault 动态切换方案（Line 70 + 215）

### 用户原批注
> **Line 70**: "优先想办法解决硬编码，因为我会使用很多不同的 vault，而且我每次使用不同的 vault 的话，我当前后端的配置是不是很麻烦？请你想出非技术用户能轻易上手使用的方案"
>
> **Line 215**: "我会切到很多不同的 vault 学习，所以我需要给非技术用户能明显切换的手段"

### 深度分析

---

#### Part A: 痛点分析 — 3 步才能切 vault

**当前切 vault 需要 3 步 + 编辑 2 个文件**:

| 步骤 | 操作 | 难度 | 文件 |
|-----|-----|-----|-----|
| 1 | 编辑 `docker-compose.yml:162-163`，手动加一行 volume mount | 高（YAML 缩进敏感）| `docker-compose.yml` |
| 2 | 编辑 `backend/.env`，修改 `CANVAS_BASE_PATH` | 中 | `backend/.env` |
| 3 | 运行 `docker-compose down && docker-compose up -d` | 低（Terminal 命令）| — |

**为什么这么麻烦？3 个硬编码根源**:

1. **Docker volume mount 是静态的**（`docker-compose.yml:162-163`）:
   ```yaml
   # 每个 vault 单独写死一行 — 新增学科必须改这里
   - "/Users/Heishing/Desktop/spring course 2026/CS188:/app/vault/CS188:ro"
   - "/Users/Heishing/Desktop/spring course 2026/CS 189:/app/vault/CS189:ro"
   ```
   改 volume 必须 `docker-compose down && up`（不是 restart 能解决的）。

2. **CANVAS_BASE_PATH 是单路径**（`backend/app/config.py:138-139`）:
   ```python
   CANVAS_BASE_PATH: str = Field(
       default=os.path.join(_PROJECT_ROOT, "笔记库"),
   )
   ```
   Docker 环境用 `CANVAS_BASE_PATH=/app/vault`（`docker-compose.yml:150`）— 单一路径，无法一次对多个 vault 索引。

3. **`@lru_cache` 冻结设置**（`backend/app/config.py` `get_settings()` 被 `@lru_cache` 包裹）:
   改 env var 后必须重启 backend 才能生效（runtime 无法热更新设置）。

**非技术用户的噩梦**: 编辑 YAML 文件（缩进错一格整个 Docker 起不来）+ 记住两个文件路径 + 区分 `down` vs `restart` 语义。

`★ Insight ─────────────────────────────────────`
- Docker Compose 的 volume mount 是**容器创建时**绑定的，不是运行时——这是 Docker 的设计限制，不是代码 bug
- `@lru_cache` 冻结 settings 是 FastAPI 的推荐模式（Pydantic BaseSettings 文档），但代价是失去热更新能力
- 现有 `backend/app/api/v1/endpoints/metadata.py` 已实现 vault indexing API（`POST /index/vault` / `POST /index/vault/incremental`），只是没有 vault **切换** API
`─────────────────────────────────────────────────`

---

#### Part B: 关键洞察 — 挂载父目录，新增 vault = 新建子目录

**核心发现**: 当前 2 个 vault（CS188 / CS 189）都在**同一个父目录**下:
```
/Users/Heishing/Desktop/spring course 2026/
├── CS188/           ← vault 1
├── CS 189/          ← vault 2
├── (未来新学科)/     ← vault 3, 4, 5...
```

**洞察**: 如果挂载**父目录**而非单独 vault:
- Docker volume mount 只写一次，永不再改
- 新增学科 = 在 Finder 里新建文件夹（零配置改动）
- 切换 = 改 `.env` 里的 `ACTIVE_VAULT=CS189`（一行）+ restart 30s

**对比**:

| 维度 | 当前（每 vault 单独挂载） | 推荐（挂载父目录） |
|-----|------------------------|--------------------|
| 新增 vault | 改 compose YAML + down/up | **新建文件夹**（零改动）|
| 切 vault | 改 2 文件 + down/up | **改 .env 一行 + restart** |
| Docker restart | 必须 down/up（volume 变了）| **只 restart**（volume 不变）|
| 非技术用户难度 | 高（YAML 编辑）| **低（改一行文本文件）** |
| 多 vault 并存 | ✅（全挂载了） | ✅（父目录下全可见）|

---

#### Part C: 4 方案对比

| # | 方案 | 新增 vault | 切换 vault | 代码改动 | 推荐度 |
|---|-----|---------|----------|--------|------|
| **1** | **父目录挂载 + .env ACTIVE_VAULT** | 新建文件夹（0 配置）| 改 .env 一行 + restart 30s | 改 compose 2 行 + 新建 .env | ✅ **Phase 1 推荐** |
| 2 | vaults.yaml + backend API | 编辑 YAML（比 compose 简单）| API 调用（0 重启）| ~100 行新代码 | 🟡 Phase 2 演进 |
| 3 | Claudian MCP tool `switch_vault` | 对话式（最自然）| 说"切到 CS189"（0 文件编辑）| ~150 行（API + MCP tool）| 🟡 Phase 3 |
| 4 | 符号链接 `/active → /CS188` | 改 symlink 指向 | 改 symlink + restart | 0 代码改动 | ❌ macOS Docker VM 边界不稳定 |

---

#### Part D: 推荐 Phase 1 — .env 父目录挂载 + ACTIVE_VAULT

##### D.1 具体改动（共 3 个文件，5 行变更）

**文件 1: 新建项目根目录 `.env`**
```bash
# Canvas Learning System — Vault 配置
# 切换 vault: 改 ACTIVE_VAULT 的值 → docker-compose restart backend

# Vault 父目录（包含所有学科文件夹的上级目录）
VAULT_ROOT=/Users/Heishing/Desktop/spring course 2026

# 当前激活的 vault（= VAULT_ROOT 下的子目录名）
ACTIVE_VAULT=CS188

# Neo4j（已有，从 backend/.env 统一过来）
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

**文件 2: 修改 `docker-compose.yml`**（2 行变更）

```yaml
# 旧（162-163）:
- "/Users/Heishing/Desktop/spring course 2026/CS188:/app/vault/CS188:ro"
- "/Users/Heishing/Desktop/spring course 2026/CS 189:/app/vault/CS189:ro"

# 新:
- "${VAULT_ROOT}:/app/vaults:ro"
```

```yaml
# 旧（150）:
- CANVAS_BASE_PATH=/app/vault

# 新:
- CANVAS_BASE_PATH=/app/vaults/${ACTIVE_VAULT}
```

**文件 3: 修改 `backend/app/config.py:138-139`**（兼容性调整）

```python
# 旧:
CANVAS_BASE_PATH: str = Field(
    default=os.path.join(_PROJECT_ROOT, "笔记库"),
)

# 新:
CANVAS_BASE_PATH: str = Field(
    default=os.path.join(_PROJECT_ROOT, "笔记库"),
    description="Absolute path to active vault directory. "
                "In Docker: /app/vaults/${ACTIVE_VAULT}. "
                "Native: defaults to _PROJECT_ROOT/笔记库.",
)
```

##### D.2 用户切 vault 操作（2 步，非技术用户友好）

**Step 1**: 打开项目根目录的 `.env` 文件，改一行:
```
ACTIVE_VAULT=CS 189
```

**Step 2**: 在 Terminal 运行:
```bash
docker-compose restart backend
```

等 30 秒，done。

##### D.3 用户新增 vault 操作（1 步）

在 Finder 里把新学科的 Obsidian vault 文件夹**放到** `VAULT_ROOT` 目录下:
```
/Users/Heishing/Desktop/spring course 2026/
├── CS188/
├── CS 189/
└── MATH101/   ← 新增！直接放进去
```

然后切 vault（上面的 2 步）。不需要改任何配置文件，也不需要 `docker-compose down`。

`★ Insight ─────────────────────────────────────`
- Docker Compose 的 `${VAR}` 插值从 `.env` 文件读取是**原生特性**（不需要 dotenv 库）——`docker-compose.yml:25` 已用此模式处理 `NEO4J_USER`
- `restart` vs `down+up` 的区别: restart 只重启进程（保留容器 + volume mount），`down+up` 销毁并重建容器。**父目录挂载方案让 restart 够用**，因为 volume mount 不变，只有 env var 变了
- 未来 Phase 2（vaults.yaml + API）可以做到**零重启切换**——但需要绕过 `@lru_cache`，技术复杂度更高
`─────────────────────────────────────────────────`

---

#### Part E: Phase 2 演进 — vaults.yaml + backend API + MCP tool

**Phase 2（2-4 周后，按需启动）**:

```yaml
# backend/config/vaults.yaml — 新建
vaults:
  - name: CS188
    path: /app/vaults/CS188
    group_id: cs188
    display_name: "CS 188 - Introduction to AI"
  - name: CS189
    path: /app/vaults/CS 189
    group_id: cs189
    display_name: "CS 189 - Machine Learning"

active_vault: CS188
```

```python
# backend/app/api/v1/endpoints/vault.py — 新建
@router.post("/vault/switch")
async def switch_vault(input: SwitchVaultInput):
    """运行时切换 active vault — 无需重启 backend"""
    # 1. 更新内存中的 active vault
    # 2. 触发 LanceDB vault_notes 增量重索引
    # 3. 更新 Graphiti group_id
    # 4. 返回新 vault 的索引状态
```

```python
# backend/app/mcp/tools/vault_tools.py — 新建 MCP tool
async def switch_vault(input: SwitchVaultInput) -> SwitchVaultOutput:
    """Claudian 对话式切换 vault — 用户说"切到 CS189" 即可"""
```

**Phase 2 依赖 Phase 1 完成**（父目录已挂载，vault 都可见），是**增量演进**而非推倒重来。

---

## R11-Q2 · Claudian MCP 自动启动可行性证明（Line 192）

### 用户原批注
> "我觉得这个方案可以，但是需要证明可行。"

### 深度分析

---

#### Part A: 4 条独立证据链

##### 证据 1: `docker-manager.ts` — 项目已有 Docker subprocess 调用

**文件**: `frontend/src/services/docker-manager.ts:281-291`
```typescript
private async execCommand(
  commandName: string,
  args: string[],
): Promise<CommandResult> {
  try {
    const output = await Command.create(commandName, args).execute();
    return {
      success: output.code === 0,
      stdout: output.stdout,
      stderr: output.stderr,
      code: output.code,
    };
  }
}
```

**分析**:
- `Command.create('docker', ['compose', '-f', composeFile, 'up', '-d'])` — Tauri Shell plugin 的 subprocess API
- 这是**项目已有代码**——不是理论可行性，而是**已经在跑的代码**
- Claudian MCP tool 的 `subprocess.run(['docker-compose', 'up', '-d'])` 在技术层面**完全等价**，只是调用方从 Tauri 变成 Python/Node.js

##### 证据 2: `sidecar.js` — Claudian 运行在 Electron 沙箱外

**文件**: `frontend/sidecar/sidecar.js:62-66`
```javascript
const HIGH_RISK_SDK_TOOLS = new Set([
  'WebFetch', 'WebSearch',
  'Bash', 'Shell', 'Exec',        // ← 注意: 包含 Bash
  'Write', 'Edit', 'MultiEdit', 'NotebookEdit',
  // ...
]);
```

**分析**:
- Claudian sidecar 是独立 Node.js 进程（`#!/usr/bin/env node`），**不在** Obsidian Electron renderer 里
- HIGH_RISK_SDK_TOOLS 包含 `Bash` / `Shell` / `Exec` —— 说明 SDK 本身**支持**执行系统命令
- 这些工具需要用户审批（permission card），但**技术上可执行**
- MCP tool 的 `subprocess.run()` 权限层级**低于** Bash tool（MCP tool 是后端代码，不是 Shell 命令）

##### 证据 3: G-MCP-001 — 项目已有 daemon 进程先例

**文件**: `docs/known-gotchas.md:97`
```
G-MCP-001 | graphiti-canvas stdio spawn ~30-45s 超时被 SIGKILL
          | ✅ 2026-04-06 改用 launchd HTTP daemon
          | (com.canvas.graphiti-mcp.plist + ~/bin/graphiti-canvas-daemon.sh)
          | binds 127.0.0.1:8765
```

**分析**:
- 项目已经将 MCP server 从"Claude Code spawn"迁移到"launchd 长驻 HTTP daemon"
- 这是**更复杂**的 subprocess 管理模式（daemon = 后台常驻进程）
- `check_backend_health` MCP tool 做的只是一次性 `subprocess.run()`（执行完就返回）—— 比 daemon 管理**简单得多**
- 已验证路径: 项目知道怎么在 macOS 上管理 subprocess

##### 证据 4: Python `subprocess.run` — 标准库，0 新依赖

```python
import subprocess  # Python 标准库
result = subprocess.run(
    ['docker', 'compose', 'up', '-d', 'neo4j', 'backend'],
    cwd='/Users/Heishing/Desktop/canvas/canvas-learning-system',
    capture_output=True,
    timeout=30,
)
# result.returncode == 0 → 成功
# result.stderr → 错误信息
```

**分析**:
- `subprocess` 是 Python 标准库（**0 新依赖**）
- `docker compose up -d` 是**幂等**操作（已跑的服务不会重复启动）
- `timeout=30` 保证不会卡死（30s 内 Docker Compose 返回或超时）

##### 证据链总结

| # | 证据 | 证明了什么 | 文件引用 |
|---|------|---------|--------|
| 1 | docker-manager.ts | 项目已有 Docker subprocess 代码（Tauri Shell → 完全等价 Python subprocess）| `frontend/src/services/docker-manager.ts:286` |
| 2 | sidecar.js | Claudian 在 Electron 沙箱外，SDK 支持 Bash/Shell/Exec | `frontend/sidecar/sidecar.js:62-66` |
| 3 | G-MCP-001 | 项目已有 daemon 进程管理先例（launchd HTTP daemon）| `docs/known-gotchas.md:97` |
| 4 | subprocess.run | 标准库，0 依赖，幂等，30s 超时保护 | Python 3.12 stdlib |

**结论**: 4 条证据全部独立指向"可行"。没有技术阻断点。

---

#### Part B: MCP tool 运行位置分析

**关键问题**: `check_backend_health` MCP tool 应该跑在**哪里**？

| 位置 | 可行性 | 优势 | 风险 |
|-----|------|-----|-----|
| **Option A: Backend 容器内** | ⚠️ 需要 Docker-in-Docker | 和其他 14 MCP tools 同位 | 需 mount `/var/run/docker.sock`（安全面增大）|
| **Option B: Host（Claudian sidecar）** | ✅ 原生 Docker CLI 可用 | 最简单，0 额外配置 | 需要 Claudian 在线才能启动 |
| **Option C: 独立 MCP server（launchd）** | ✅ 类似 G-MCP-001 | Backend 不在线也能启 | 新增 daemon 管理复杂度 |

**推荐**: **Option B**（Host/Claudian sidecar）—— 用户启动 Claudian → 说"启动 Canvas" → sidecar 跑 `subprocess.run(['docker', 'compose', 'up', '-d'])` → 等待 health check → 返回 ready。

**Option A 的 Docker-in-Docker 问题**: Backend 容器（`docker-compose.yml:136-181`）默认不 mount Docker socket。要让容器内跑 `docker compose up` 需要额外配置:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock  # 安全风险
```
社区共识是避免 Docker-in-Docker 除非必要。Canvas 场景**不需要**——Claudian 在 host 上。

---

#### Part C: PoC 命令 + 预期行为

**完整 PoC 流程**（可在 Terminal 验证）:

```bash
# 1. 模拟 MCP tool 的 subprocess 调用
python3 -c "
import subprocess, time, httpx

# Step 1: 启动 Docker
result = subprocess.run(
    ['docker', 'compose', 'up', '-d', 'neo4j', 'backend'],
    cwd='/Users/Heishing/Desktop/canvas/canvas-learning-system',
    capture_output=True, timeout=30
)
print(f'docker-compose returncode: {result.returncode}')

# Step 2: 轮询 health
for i in range(36):  # 最多 180s
    try:
        r = httpx.get('http://localhost:8001/api/v1/health', timeout=3)
        print(f'health: {r.json()}')
        break
    except:
        print(f'waiting... ({i*5}s)')
        time.sleep(5)
"
```

**预期输出**:
```
docker-compose returncode: 0
waiting... (0s)
waiting... (5s)
...
health: {"status": "healthy", "components": {"neo4j": "ok", "fsrs": "ok", ...}}
```

`★ Insight ─────────────────────────────────────`
- `docker compose up -d` 的**幂等性**是关键安全特性——多次调用不会创建多个容器，只是确保服务在跑
- 运行位置选择（Container vs Host）不是技术问题而是**安全架构决策**——Docker socket mount 把容器内进程提升到和 host root 等价的 Docker 控制权
- PoC 用 `httpx`（已在 `backend/requirements.txt`）而非 `requests`，和项目技术栈一致
`─────────────────────────────────────────────────`

---

## R11-Q3 · ChatGPT 对抗性审查提示词（Line 654）

### 用户原批注
> "请你生成一份提示词给 ChatGPT ，我用于 deep research 对抗性审查，思考方案部署的合理性，所以请你记得把我们当前的文件都 push 到仓库上"

### 深度分析

---

#### Part A: copy-to-deep-research 块

> 以下块已由 `stop-deep-research-clipboard.js` hook 自动 pbcopy 到剪贴板。直接 Cmd+V 粘贴到 ChatGPT Deep Research。

```copy-to-deep-research
## 审查任务

我需要你对一个桌面学习应用的**部署架构方案**进行**对抗性审查**（adversarial review）。请扮演一个怀疑论者（devil's advocate），找出方案中的漏洞、遗漏的失败模式、和不合理的假设。

## 项目背景

**Canvas Learning System** — 个人桌面学习应用（非 SaaS），正在从 Tauri 2 桌面 App 降级到 **Obsidian + Claude Code CLI** 架构。

- **GitHub 仓库**: https://github.com/oinani0721/canvas-learning-system (main branch)
- **技术栈**: Tauri 2 + React + TypeScript (前端) / Python FastAPI + Neo4j 5.26 + LanceDB + Graphiti (后端) / Docker Compose
- **部署模型**: 用户本地 Mac（M5 Max 128GB），Docker Desktop，非云端

## 已完成的部署审计（Round 10 — 请审查）

### 当前 docker-compose 服务矩阵

| 服务 | 镜像 | 端口 | 说明 |
|-----|-----|-----|-----|
| neo4j | neo4j:5.26-community | 7478(Browser) / 7691(Bolt) | Graphiti KG 存储（非默认端口，避免冲突）|
| neo4j-test | neo4j:5.26-community | 7479 / 7692 | 测试隔离（profiles: test/dev）|
| ollama | ollama/ollama:latest | 11434 | **仅 Windows/Linux**，Mac 用 native brew |
| backend | 本地 Dockerfile | 8001 | FastAPI + 15 MCP tools + 4 层检索 |
| claude-dev | .devcontainer/ | — | 开发容器（profiles: dev）|

**关键文件**: `docker-compose.yml`, `backend/app/main.py:263-285` (Graphiti 初始化)

### 关键发现（Round 10 审计）

1. **Tauri sidecar 从未存在** — `tauri.conf.json` 无 `bundle.externalBin` / `plugins.shell.sidecar`。PRD 承诺"自动启动所有依赖"是规格幻觉，用户一直手动 `docker-compose up`
2. **Graphiti 降级模式已就位** — Neo4j 不通 → `GraphitiEpisodeWorker` 进入 degraded mode，Episode 写死信队列 `data/dead_letter_episodes.jsonl`，不阻塞启动
3. **Electron 沙箱硬约束** — Obsidian Plugin 无法 `child_process.spawn('docker')`，Smart Connections (8k stars) / Khoj (15k stars) / Copilot (4k stars) 全部用"用户手动 + 健康检查"
4. **CORS 已含 Obsidian** — `docker-compose.yml:153` 有 `app://obsidian.md`，但未实测
5. **资源占用** — 峰值 RAM 3.5-5GB，磁盘 ~600MB，冷启动 120-150s

### 部署方案推荐（3 启动模式）

| 模式 | 代码改动 | 用户操作 | 社区先例 |
|-----|--------|-------|--------|
| **模式 1（推荐）** 用户手动 `docker-compose up` + Plugin 健康检查 | 0 行 | 每次打开 Obsidian 前开 Docker | Smart Connections / Khoj / Copilot |
| **模式 2（可选演进）** Claudian MCP tool 自动 subprocess 启动 | ~50 行 | 在 Claudian 里说"启动 Canvas" | 无社区先例（Canvas 独创）|
| 模式 3（不可行）Obsidian Plugin 自动 spawn | N/A | N/A | Electron 沙箱禁止 |

### Vault 动态切换方案（Round 11 — 请审查）

**当前痛点**: vault 路径硬编码在 `docker-compose.yml:162-163`，切 vault 需改 2 文件 + 重启。

**推荐**: 挂载 vault **父目录**（`/Users/.../spring course 2026/`）而非单独 vault:
```yaml
volumes:
  - "${VAULT_ROOT}:/app/vaults:ro"
environment:
  - CANVAS_BASE_PATH=/app/vaults/${ACTIVE_VAULT}
```
切 vault = 改 `.env` 里 `ACTIVE_VAULT=CS189` + `docker-compose restart backend`（30s）。
新增学科 = 在父目录下新建文件夹（零配置改动）。

### 5 个未决决策点（D1-D5）

| ID | 决策 | 选项 |
|----|-----|-----|
| D1 | Backend 启动权限 | 用户手动 vs Claudian MCP 自动 vs 两者都做 |
| D2 | Session 关闭后 Backend 生命周期 | 手动 down vs 常驻 vs 自动 pause |
| D3 | Frontmatter vs Graphiti 真相源 | Frontmatter 主 vs Graphiti 主 vs 双向同步 vs 不同步 |
| D4 | LanceDB 长期噪音清理 | 每周 cron vs 启动 rebuild vs 不清理 vs 手动 |
| D5 | MCP 并行调用 | 全开 vs 串行 vs 读并行写串行 vs 观察后定 |

## 我希望你审查的具体问题

### 必答（Critical）

1. **Vault 父目录挂载方案的失败模式**:
   - Docker Desktop 对带空格路径的 volume mount 行为（当前有 `CS 189`）？
   - `:ro` (read-only) mount 下 backend 需要写临时文件怎么办？
   - VAULT_ROOT 变更后旧索引数据（LanceDB）的一致性？

2. **MCP 自动启动的安全风险**:
   - Claudian sidecar 以用户权限执行 `subprocess.run(['docker', 'compose', 'up'])`——是否有提权风险？
   - 恶意 prompt 注入能否触发 Docker 命令？（sidecar 有 3 tier 权限模型但 MCP backend tools 是 auto-allow）
   - Docker Compose 的幂等性在哪些边界条件下失效？

3. **Neo4j 端口冲突方案**:
   - 当前用 7691/7478 避免默认端口冲突——如果用户安装 Neo4j Desktop 呢？
   - Graphiti 连接配置是否正确指向非默认端口？

### 期望（Important）

4. **降级模式的完整性**:
   - Docker 不启 → backend 不可用 → Obsidian Plugin 红灯。这条链路有断裂风险吗？
   - 死信队列（`dead_letter_episodes.jsonl`）重放机制是否有数据丢失风险？

5. **社区模式对比**:
   - 我们参考 Smart Connections / Khoj / Copilot 的"用户手动 + 健康检查"模式。这 3 个插件有没有后来演进到自动启动的？我们是否遗漏了其他社区实践？

6. **`@lru_cache` 冻结 settings 的影响**:
   - Phase 1（.env + restart）不受影响。但 Phase 2（runtime API switch vault）需要绕过 `@lru_cache`。这样做的副作用？FastAPI 社区有推荐模式吗？

### 可选（Nice-to-have）

7. **跨平台兼容**:
   - 方案以 macOS M-series 为主设计。如果用户迁移到 Windows/Linux，哪些环节会断？

8. **长期演进**:
   - 这个架构（Docker Compose + native Ollama + MCP tools）在 2-3 年后还合理吗？有没有更轻量的替代路径？

## 项目约束（请在审查时考虑）

- **个人桌面应用**，非 SaaS（无多用户 / 无云端部署）
- **Mac M5 Max 128GB**（RAM 不是瓶颈，但 Docker 桌面的 VM overhead 是）
- **Obsidian 生态**（Plugin 受 Electron 沙箱限制）
- **Claude Code CLI + MCP** 是主要 AI 交互通道（不是 Obsidian 内置 UI）
- 用户是**非技术用户**（Python/React 代码由 AI 编写，用户不直接写代码）
- 项目用 **OpenSpec 管理需求变更** + **Graphiti 知识图谱**记录决策

## 你的审查回复格式

请按以下结构回复：

### Critical 发现（必须修复才能上线）
- [C1] ...
- [C2] ...

### Important 发现（建议修复但不阻断）
- [I1] ...
- [I2] ...

### Nice-to-have 发现（远期考虑）
- [N1] ...

### 对方案的总体评价
[FINAL] 一句话总结：这个方案是否合理，最大风险是什么？
```

#### Part B: Git Push

用户明确要求"把文件都 push 到仓库上"。Round 11 文件创建完成后，将执行全量 `git add` + `git commit` + `git push`，确保 ChatGPT Deep Research 可以通过 GitHub URL 访问最新代码。

---

## Round 11 总结

### 核心答案

**Q1（Vault 切换）**: 挂载父目录，新增 vault = 新建子目录，切换 = 改 `.env` 一行 + restart 30s

**Q2（MCP 可行性）**: 4 条独立证据全部指向"可行" — 项目已有 Docker subprocess 代码 + sidecar 在沙箱外 + daemon 先例 + stdlib 零依赖

**Q3（ChatGPT 审计）**: `copy-to-deep-research` 块已生成，7 个对抗性问题覆盖: vault 路径空格 / MCP 安全 / Neo4j 冲突 / 降级完整性 / 社区演进 / @lru_cache 副作用 / 跨平台

### 下一步期待

1. 用户将 `copy-to-deep-research` 块粘贴给 ChatGPT Deep Research → 收到 [C1]/[I1]/[N1] 对抗性审计
2. 用户将 ChatGPT 审计结果粘回 Claude → Round 12 回应审计发现
3. 基于审计结果 + 用户决策 D1-D5 → 启动实施 Story

### Obsidian 可导航引用

- `docker-compose.yml:150,162-163` — vault 挂载 + CANVAS_BASE_PATH
- `backend/app/config.py:138-139,632-634` — CANVAS_BASE_PATH 设置 + @lru_cache
- `backend/app/api/v1/endpoints/metadata.py` — vault 索引 API（index/incremental/status）
- `frontend/src/services/docker-manager.ts:281-291` — 已有 Docker subprocess 代码
- `frontend/sidecar/sidecar.js:52-66` — 3 tier 权限模型（SAFE_READONLY / HIGH_RISK / MCP）
- `docs/known-gotchas.md:97` — G-MCP-001 launchd daemon 先例
- `backend/app/main.py:263-285` — Graphiti Phase 2 初始化 + degraded mode

---

**下一轮触发条件**: 用户粘回 ChatGPT Deep Research 的对抗性审计结果 → Round 12 回应
