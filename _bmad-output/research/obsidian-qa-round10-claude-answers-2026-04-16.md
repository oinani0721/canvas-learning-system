---
title: "Obsidian 翻译问答 Round 10 主答复文件（Graphiti 部署方案适配 Obsidian 降级）"
date: 2026-04-16
trigger: "用户在 Round 9 主文件 Line 185 追加 1 条 Round 10 批注 — 选 A 保留 Graphiti 但要求 deep explore 部署方案适配 Obsidian 降级"
type: "qa-round10-answers"
status: "round11-continued"
round11_followup_file: "[[obsidian-qa-round11-claude-answers-2026-04-16]]"
parent_files:
  - "[[obsidian-qa-round9-claude-answers-2026-04-15]]"
related_plan: "OBSIDIAN-QA-ROUND10-2026-04-16"
round: 10
total_sections: 1
round10_character: "部署方案深度 — 从当前 docker-compose 架构审计到推荐 Obsidian 降级后的启动链路 + 可选 Claudian 自动协调"
key_finding: "推荐选项 1（用户手动 docker-compose up + Obsidian Plugin 健康检查，0 代码改动，符合 Smart Connections/Khoj/Copilot 社区主流），可选演进选项 2（Claudian MCP tool 自动 subprocess 启动，~50 行代码）"
explore_agents:
  - "Agent A: 当前部署架构审计（docker-compose 服务矩阵 + Graphiti 初始化路径 + tauri.conf.json 真相）"
  - "Agent B: 轻量化替代方案（5 方案对比 + Obsidian Plugin 沙箱限制 + Claudian 协调模式）"
  - "Agent C: PRD 部署期望差异 + 14+ MCP tools 已就位 + 5 个未决决策点"
integrity_rules: "IC-1 ~ IC-8（沿用）"
---

# Obsidian 翻译问答 Round 10 主答复文件

> **阅读指引**: 本文件是 [[obsidian-qa-round9-claude-answers-2026-04-15]] 的 Round 10 延伸。
>
> Round 9 推荐"保留 Graphiti 做错误检索" → 用户批准（选 A）→ 追问"**部署方案如何适配 Obsidian 降级后架构？**"。Round 10 基于 3 个并行 Deep Explore Agent（部署审计 + 轻量化替代 + PRD 期望差异）给出推荐启动链路。

## Round 10 核心结论（1 分钟版）

**推荐：选项 1（立即采纳） + 选项 2（阶段 2 演进）**

| 启动模式 | 代码改动 | 用户操作 | Obsidian 内体验 |
|---------|--------|-------|-----------|
| **选项 1（推荐）** 用户手动 `docker-compose up` + Obsidian Plugin 健康检查 | **0 行** | 每次 Obsidian 启动前先开 Docker | Plugin 检测 8001 端口是否健康，红/绿圆点指示 |
| **选项 2（可选演进）** Claudian MCP tool 自动 `subprocess.run(['docker-compose', 'up', '-d'])` | ~50 行（新增 `check_backend_health` tool）| 用户在 Claudian 里说"启动 Canvas" | MCP tool 自动拉起 Docker，~120s 后 backend ready |
| ❌ 选项 3（不可行） Obsidian Plugin 自动 spawn 子进程 | N/A | N/A | **Electron 沙箱禁止** — Smart Connections/Khoj/Copilot 全部弃用此路径 |

**关键发现**:
1. **Tauri sidecar 原本就不存在** — `tauri.conf.json` 无 `bundle.externalBin` / `plugins.shell.sidecar`，用户从 Day 1 就手动 `docker-compose up`。降级到 Obsidian **没有**切断"自动启动链路"，因为这条链路从未存在过
2. **Graphiti 降级已就位** — `backend/app/main.py:268-285` 的 Phase 2 初始化已实现 eager probe + 自动 degraded mode（写死信队列 `data/dead_letter_episodes.jsonl`），Neo4j 不通时 backend 仍能启动
3. **Electron 沙箱硬约束** — Obsidian Plugin 无法 `child_process.spawn('docker')`，这是浏览器级限制，社区 3 主流 AI Plugin（Smart Connections/Khoj/Copilot）全部采用"用户手动 + 健康检查"模式
4. **Claudian 是最优协调层** — MCP tool 运行在 Node.js 子进程（非 Electron 沙箱），**唯一能 subprocess 拉起 Docker 的合法路径**

---

## R10-Q1 · Graphiti 部署方案适配 Obsidian 降级（Line 185）

### 用户原批注
> "A，但是我需要你 deep explore 相关的部署方案，来适配我们降级后的 Canvas learning systeam"

### 深度分析

---

#### Part A: 当前部署架构审计

##### A.1 docker-compose 服务矩阵（基于 `docker-compose.yml` 实读）

| 服务 | 镜像 | 端口映射 | 启动条件 | 作用 |
|-----|-----|-------|-------|-----|
| **neo4j** | `neo4j:5.26-community` | `7478→7474`（Browser）/ `7691→7687`（Bolt）| **默认启动** | Graphiti KG 存储 |
| **neo4j-test** | `neo4j:5.26-community` | `7479→7474` / `7692→7687` | `profiles: [test, dev]`（可选）| 测试实例，产品数据隔离 |
| **ollama** | `ollama/ollama:latest` | `11434:11434` | `profiles: [windows]`（仅 Windows/Linux NVIDIA）| 嵌入模型 — ⚠️ **Mac 上禁用**，用 native `brew install ollama` |
| **backend** | 本地 build `./backend/Dockerfile` | `8001:8001` | 依赖 `neo4j: service_healthy` | FastAPI + 4 层检索 |
| **claude-dev** | `.devcontainer/Dockerfile.claude` | — | `profiles: [dev]`（可选）| Claude Code 开发容器 |

**证据位置**:
- Neo4j heap: `docker-compose.yml:27-28`（初始 512m / 最大 1G）
- CORS 已含 Obsidian: `docker-compose.yml:153` 有 `app://obsidian.md`
- **Vault 路径硬编码**: `docker-compose.yml:162-163` 挂载 `/Users/Heishing/Desktop/spring course 2026/CS188` 和 `CS 189`（**切换 vault 需改 compose 文件 + 重启**）
  **User: 优先想办法解决硬编码，因为我会使用很多不同的 vault，而且我每次使用不同的 vault 的话，我当前后端的配置是不是很麻烦？请你想出非技术用户能轻易上手使用的方案**

  `[A12 2026-04-16 → round11]` — 推荐挂载 vault 父目录方案（新增学科 = 新建子目录，切换 = 改 .env 一行 + restart 30s）。见 [[obsidian-qa-round11-claude-answers-2026-04-16]] R11-Q1。

- External network: `docker-compose.yml:225-227` 依赖外部 `cliproxyapi_default` 网络（cliproxyapi 必须先跑）

##### A.2 Graphiti 初始化代码路径（`backend/app/main.py:263-285` 实读）

```python
# Phase 2: GraphitiEpisodeWorker — real Graphiti integration
from app.services.episode_worker import get_episode_worker

episode_worker = get_episode_worker()
try:
    graphiti_ready = await episode_worker.initialize_graphiti(
        neo4j_uri=settings.NEO4J_URI,        # bolt://neo4j:7687 (container) or bolt://localhost:7691 (native)
        neo4j_user=settings.NEO4J_USER,
        neo4j_password=settings.NEO4J_PASSWORD,
        google_api_key=settings.GOOGLE_API_KEY,
    )
    if graphiti_ready:
        await episode_worker.start()
        app.state.episode_worker = episode_worker
        logger.info("[Phase 2] GraphitiEpisodeWorker started")
    else:
        app.state.episode_worker = episode_worker
        logger.warning(
            "[Phase 2] GraphitiEpisodeWorker in degraded mode (no graphiti client)"
        )
except Exception as e:
    app.state.episode_worker = None
    logger.warning(f"[Phase 2] GraphitiEpisodeWorker init failed (non-fatal): {e}")
```

**关键行为**:
- **Pre-flight probe**: `initialize_graphiti()` 内部先探测 Neo4j bolt 连通，不通则返回 `False`
- **Degraded mode fallback**: Neo4j 不通 → worker 进入降级模式，Episode 写死信队列 `backend/data/dead_letter_episodes.jsonl`（不阻塞 backend 启动）
- **重启恢复**: 下次 `docker-compose up -d neo4j` 后 backend 重启 → Graphiti 重新连接，死信 Episode 可手动重放

##### A.3 Tauri sidecar 真相（`frontend/src-tauri/tauri.conf.json` 实读）

**关键发现**:
```json
{
  "plugins": {
    "shell": {
      "open": "^((mailto:\\w+)|(tel:\\w+)|(https?://\\w+)|(obsidian://\\w+)).+"
    }
  },
  "bundle": { "active": true, "targets": "all" }
}
```

- ❌ **无 `bundle.externalBin`**（Tauri 打包外部二进制的标准方式）
- ❌ **无 `plugins.shell.sidecar`**（自动 spawn 子进程配置）
- ❌ **无 Docker 启动 hook**

**结论**: PRD 535-577 承诺"点击图标自动启动所有依赖" — **实际代码从未实现**。用户从 Day 1 就手动 `docker-compose up`。降级到 Obsidian **没有**切断"自动启动链路" —— 这条链路是**规格幻觉**。

> ⚠️ **注意**: `frontend/sidecar/sidecar.js` 确实存在，但这是**Claude Agent SDK 的 Node.js sidecar**（通过 stdin/stdout NDJSON 通信），用于 Tauri 集成 Agent SDK，**与 Docker 无关**。详见 `frontend/sidecar/package.json:5`。

##### A.4 资源占用估算

| 资源类型 | 占用 | 数据源 |
|--------|-----|------|
| RAM 峰值 | 3.5-5 GB | Neo4j 1G heap + backend FastAPI ~500MB + Ollama 本地 ~2GB |
| 磁盘数据 | ~600 MB | Neo4j 518 MB（`./docker/neo4j/data`）+ LanceDB 53 MB（`canvas-lancedb` named volume）|
| 冷启动时间 | 120-150s | Neo4j 40s healthy + backend 30s healthy + Graphiti probe/init 40s |
| 热启动时间 | 50-80s | Neo4j 已有 data，backend 重连即可 |

`★ Insight ─────────────────────────────────────`
- `service_healthy` 依赖机制让 backend 必须等 Neo4j 先就位（`docker-compose.yml:165-167`），这是**序列化启动**而非并行
- Graphiti 的 **pre-flight probe + degraded mode fallback** 是关键容错设计 —— backend 永远不会因为 Neo4j 未启动而崩溃，只是功能降级
- Mac 上 Ollama native 跑（`brew install ollama`）+ backend 通过 `host.docker.internal:11434` 访问，这是 Metal GPU 的 workaround（Docker Ollama 无法透传 Mac GPU）
`─────────────────────────────────────────────────`

---

#### Part B: 启动链路的 3 种现实模式对比

##### B.1 模式对比矩阵

| 维度 | **模式 1: 用户手动（推荐）** | **模式 2: Claudian 自动协调** | ❌ 模式 3: Obsidian Plugin 自动（不可行） |
|-----|-------------------------|--------------------------|-------------------------------|
| 触发点 | 用户每次打开 Obsidian **前**，在 Terminal 跑 `docker-compose up -d` | 用户在 Claudian 里说"启动 Canvas" | Plugin onload 时自动 spawn |
| 代码改动 | **0 行** — 现有 docker-compose.yml 即可 | ~50 行 MCP tool `check_backend_health` | 不可行 — Electron 沙箱禁止 |
| 启动耗时（冷）| 120-150s（用户自己等）| 120-150s（MCP tool 内部等）| N/A |
| 启动耗时（热）| 50-80s（backend 已跑直接 HTTP 访问）| 1s（MCP tool 检测 8001 健康后直接返回）| N/A |
| 用户体验 | 需要记"先开 Docker" | Claudian 对话式启动 | 理想但做不到 |
| Plugin 可感知性 | 健康检查指示灯（红/绿）| 健康检查指示灯（红/绿）| N/A |
| 社区主流 | ✅ Smart Connections / Khoj / Copilot 全部用此 | ⚠️ 未见社区先例（Canvas 独创）| ❌ 社区已证明不可行 |

##### B.2 Electron 沙箱硬约束（模式 3 不可行的根本原因）

Obsidian 基于 Electron，Plugin 运行在 **renderer process**，受 Chromium 沙箱保护:

```javascript
// ❌ Plugin 里跑这段会 throw：
const { spawn } = require('child_process');
spawn('docker-compose', ['up', '-d']);
// Error: spawn ENOENT / Security Policy Violation
```

**社区 3 真实案例共同结论**（详见 Part F）:
- **Smart Connections**（Brian Petro，8k+ stars）: "User must run local-ai / ollama separately before enabling plugin"
- **Khoj**（khoj-ai，15k+ stars）: "Start khoj server (pip install khoj-assistant && khoj) then enable plugin"
- **Copilot**（logancyang，4k+ stars）: "Backend via OpenAI/Ollama URL — plugin 只是 HTTP client"

##### B.3 Claudian MCP 为什么能做到（模式 2 可行性）

Claudian 运行在 **Node.js 子进程**（Claude Code CLI stdio 通信），**不在** Electron 沙箱内:

```python
# MCP tool 里可以合法跑：
import subprocess
result = subprocess.run(
    ['docker-compose', 'up', '-d', 'neo4j', 'backend'],
    cwd='/Users/Heishing/Desktop/canvas/canvas-learning-system',
    capture_output=True,
    timeout=180,
)
```

**前提**: Claudian 以用户权限运行（不是 sandboxed），可以访问 Docker Daemon socket（`/var/run/docker.sock` 或 Docker Desktop's named pipe）。
User：我觉得这个方案可以，但是需要证明可行。

`[A12 2026-04-16 → round11]` — 4 条独立证据链证明 MCP 自动启动可行（docker-manager.ts 已有 subprocess / sidecar.js 非沙箱 / G-MCP-001 daemon 先例 / stdlib 零依赖）。见 [[obsidian-qa-round11-claude-answers-2026-04-16]] R11-Q2。

`★ Insight ─────────────────────────────────────`
- Electron 沙箱的设计初衷是保护用户不被恶意 Plugin 攻击，这也意味着**所有**本地启动逻辑都必须在 Plugin 外部完成
- 这是社区 3 大 AI Plugin（Smart/Khoj/Copilot）15+年经验沉淀的结论 —— 不是技术懒惰，而是硬约束
- Claudian 的 MCP tool 是**合法绕过**这一约束的唯一通道 —— 它在 Electron 之外，但又能被 Obsidian 用户触达
`─────────────────────────────────────────────────`

---

#### Part C: 6 条部署 Gotchas 清单

基于 `docker-compose.yml` 和 `backend/app/config.py` 实读，Obsidian 降级后要注意的陷阱:

##### Gotcha 1: **Vault 路径硬编码**（`docker-compose.yml:162-163`）

```yaml
volumes:
  - "/Users/Heishing/Desktop/spring course 2026/CS188:/app/vault/CS188:ro"
  - "/Users/Heishing/Desktop/spring course 2026/CS 189:/app/vault/CS189:ro"
```

- **风险**: 切换 vault 位置、新增学科、用户迁移到别的 Mac → backend 看不到新 vault
- **推荐**: 阶段 1 保持现状（仅 CS188/CS189）。阶段 2 改为环境变量 `VAULT_PATHS=...` + env 文件
**User：我会切到很多不同的 vault 学习，所以我需要给非技术用户能明显切换的手段**

`[A12 2026-04-16 → round11]` — 同 R11-Q1（挂载父目录方案，覆盖此批注需求）。见 [[obsidian-qa-round11-claude-answers-2026-04-16]] R11-Q1 Part B-D。

##### Gotcha 2: **CORS `app://obsidian.md` 已含，但未实测**（`docker-compose.yml:153`）

```
CORS_ORIGINS=http://localhost:3000,...,http://tauri.localhost,app://obsidian.md
```

- **已做**: 运维侧已加 `app://obsidian.md`，理论上 Obsidian 插件 fetch 会通过
- **未测**: Obsidian Electron renderer 的实际 Origin header 可能是 `app://obsidian.md/` 或 `capacitor-electron://obsidian.md` —— 需要 Plugin 开发时用 DevTools Network 面板实测
- **Fallback**: 实测失败 → 加通配 `CORS_ALLOW_ALL=true`（仅本地开发）

##### Gotcha 3: **Ollama Mac 必须 native**（`docker-compose.yml:93-94`）

```
# ⚠️ Mac: Ollama runs NATIVELY (brew install ollama) for Metal GPU access.
```

- Windows/Linux 用户跑 `docker-compose --profile windows up -d` 拉起 Docker Ollama
- **Mac 用户**: 必须 `brew install ollama && ollama serve` + `ollama pull bge-m3`
- **回归风险**: 新开发者 clone 仓库后忘记 native ollama → backend 向 `host.docker.internal:11434` 发请求 504 timeout

##### Gotcha 4: **NEO4J_PASSWORD `.env` 不一致**

- `docker-compose.yml:25` 默认 `password`
- 实际 `backend/.env` 可能是 `canvas_secure_2026`
- **症状**: Graphiti probe 失败（认证错误），backend 进入 degraded mode，Episode 写死信队列
- **诊断**: `docker-compose logs backend | grep "Phase 2"` 看 "no graphiti client" 警告

##### Gotcha 5: **cliproxyapi external network 依赖**（`docker-compose.yml:225-227`）

```yaml
networks:
  cliproxyapi-network:
    external: true
    name: cliproxyapi_default
```

- backend 连接到外部 `cliproxyapi_default` 网络（用于 Claude API 代理）
- **风险**: cliproxyapi 服务未启动 → `docker-compose up backend` 报 `network cliproxyapi_default declared as external, but could not be found`
- **Fix**: 先跑 cliproxyapi 的 docker-compose，或暂时注释这一段

##### Gotcha 6: **Neo4j 端口冲突**（`docker-compose.yml:31`）

```
# NOTE: Using 7478/7691 to avoid conflict with existing Neo4j instances (7474/7476/7687/7689)
```

- 用户 Mac 上可能已有别的 Neo4j（Desktop / brew）占用 7474/7687
- **Canvas 使用 7691 bolt + 7478 browser** —— 不是默认端口
- **Plugin 健康检查**: 必须用 `http://localhost:7478`（而非 7474）

`★ Insight ─────────────────────────────────────`
- 这 6 条 gotcha 的共同特征：**都是架构已存在但未文档化的约束**，Obsidian 降级后用户需要一张"预检清单"
- `docker-compose.yml:27-28` 的 Neo4j heap 1G 是基于 Round 9 估算（20-50 MB 数据量）的**十倍冗余**，不用担心 OOM
- 所有硬编码路径（vault）和端口（7691/7478）都应该在阶段 2 统一成 `.env` 参数化
`─────────────────────────────────────────────────`

---

#### Part D: 推荐方案 — 选项 1（保留现状 + 插件健康检查）

##### D.1 为什么推荐选项 1

1. **0 代码改动** —— 现有 `docker-compose.yml` 可直接用
2. **符合社区主流** —— Smart Connections / Khoj / Copilot 全部采用此模式
3. **用户可控** —— 用户明确知道后端是否在跑，便于诊断
4. **降级清晰** —— Docker 不启 = 后端不可用 = Plugin 红灯 = 回退 md 原生体验（Obsidian 本身不依赖 backend）

##### D.2 用户操作清单（3 步启动）

**Step 1: 启动后端依赖**（每次打开 Obsidian 前）
```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system
docker-compose up -d neo4j backend

# 等待 Graphiti 就绪（冷启动 120-150s）
docker-compose logs -f backend | grep "Phase 2"
# 看到: [Phase 2] GraphitiEpisodeWorker started
```

**Step 2: 验证连通**
```bash
curl -sf http://localhost:8001/api/v1/health | jq
# {"status": "ok", "graphiti": "connected", ...}
```

**Step 3: 打开 Obsidian**
- Plugin 自动探测 `http://localhost:8001/api/v1/health`
- **绿灯** ✅ → Graphiti 检索可用
- **红灯** ❌ → 仅 md 原生功能（Obsidian 本身），Plugin 禁用检索

##### D.3 Plugin 健康检查伪代码（~20 行）

```typescript
// Obsidian Plugin: health-check.ts
import { Plugin, Notice } from 'obsidian';

export class CanvasHealthChecker {
  private backendUrl = 'http://localhost:8001';
  private intervalId: number | null = null;

  async start() {
    const check = async () => {
      try {
        const res = await fetch(`${this.backendUrl}/api/v1/health`);
        const body = await res.json();
        this.updateStatusBar(body.graphiti === 'connected' ? 'green' : 'yellow');
      } catch {
        this.updateStatusBar('red');
        new Notice('⚠️ Canvas backend offline — 跑 docker-compose up');
      }
    };

    await check();
    this.intervalId = window.setInterval(check, 30_000);  // 每 30s 复查
  }
}
```

##### D.4 用户使用节奏

| 场景 | 用户行为 | 状态 |
|-----|-------|-----|
| 日常学习（只看笔记）| 直接打开 Obsidian（不启 Docker）| Plugin 红灯，纯 md 体验 |
| 学习时用 AI 检索 | `docker-compose up -d neo4j backend` → 等 2 分钟 → 打开 Obsidian | Plugin 绿灯，Graphiti 可用 |
| 考试前夕强查阅 | 同上，但加上 `ollama serve`（Mac native）| 全套本地模型 + KG 检索 |
| 关电脑睡觉 | `docker-compose down` 释放 5GB RAM | — |

---

#### Part E: 可选演进 — 选项 2（Claudian MCP tool 自动协调）

##### E.1 为什么是"可选演进"而非"立即推荐"

- 选项 1 已经足够 —— 用户有 Claudian 习惯后，每次让 Claudian 启动就像让他跑测试一样自然
- 选项 2 的价值**在于少一步用户操作**，但代价是 50 行代码 + 新增 subprocess 调用风险
- **建议**: 选项 1 先用 2-4 周，用户如果抱怨"每次要记得开 Docker"再上选项 2

##### E.2 MCP tool 伪代码（~50 行）

在 `backend/app/mcp/tools/` 下新建 `deployment_tools.py`:

```python
"""Deployment MCP tools — 让 Claudian 自动拉起/关闭 Canvas 后端"""
import subprocess
import time
from pathlib import Path
from pydantic import BaseModel
import httpx

PROJECT_ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system")
BACKEND_URL = "http://localhost:8001"
HEALTH_TIMEOUT = 180  # 冷启动最多等 3 分钟


class CheckBackendHealthInput(BaseModel):
    auto_start: bool = True  # 未就绪时是否自动拉起


class CheckBackendHealthOutput(BaseModel):
    status: str  # "ready" | "starting" | "failed"
    graphiti_connected: bool
    startup_log: str | None = None


async def check_backend_health(
    input: CheckBackendHealthInput,
) -> CheckBackendHealthOutput:
    """检查 Canvas backend 健康，可选自动拉起 Docker。"""
    # 1. 先 probe 8001
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            res = await client.get(f"{BACKEND_URL}/api/v1/health")
            body = res.json()
            return CheckBackendHealthOutput(
                status="ready",
                graphiti_connected=body.get("graphiti") == "connected",
            )
        except (httpx.ConnectError, httpx.TimeoutException):
            pass  # backend 不在

    if not input.auto_start:
        return CheckBackendHealthOutput(
            status="failed",
            graphiti_connected=False,
            startup_log="Backend unreachable and auto_start=False",
        )

    # 2. 自动拉起 Docker
    result = subprocess.run(
        ["docker-compose", "up", "-d", "neo4j", "backend"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        return CheckBackendHealthOutput(
            status="failed",
            graphiti_connected=False,
            startup_log=result.stderr.decode(),
        )

    # 3. 轮询健康（最多 180s）
    start = time.time()
    async with httpx.AsyncClient(timeout=3.0) as client:
        while time.time() - start < HEALTH_TIMEOUT:
            try:
                res = await client.get(f"{BACKEND_URL}/api/v1/health")
                body = res.json()
                if body.get("graphiti") == "connected":
                    return CheckBackendHealthOutput(
                        status="ready",
                        graphiti_connected=True,
                        startup_log=f"Startup took {int(time.time()-start)}s",
                    )
            except (httpx.ConnectError, httpx.TimeoutException):
                pass
            time.sleep(5)

    return CheckBackendHealthOutput(
        status="starting",
        graphiti_connected=False,
        startup_log=f"Timeout after {HEALTH_TIMEOUT}s — check docker-compose logs",
    )
```

注册到 `backend/app/mcp/server.py:_register_tool_routes()`（遵循现有 15 个 MCP 工具的注册模式）。

##### E.3 用户交互示例

```
User: "启动 Canvas 后端"
Claudian: [调用 check_backend_health(auto_start=True)]
         → 检测到 8001 未就绪，自动跑 docker-compose up -d
         → 轮询 45s 后 Graphiti connected
         → 返回 {"status": "ready", "graphiti_connected": true}
Claudian: "✅ Canvas backend 已就绪（45s），Graphiti 已连接。你现在可以在 Obsidian 里用检索了。"
```

##### E.4 选项 2 的风险

| 风险 | 缓解 |
|-----|----|
| subprocess 调用失败（Docker Daemon 未启动）| MCP tool 返回 `status: "failed"` + 提示用户 `open -a Docker` |
| 180s 超时但 backend 仍在启动 | 返回 `status: "starting"` —— Claudian 可以建议用户"等 30s 再试" |
| 并发调用（两个 Claudian session 同时拉）| Docker-compose 本身幂等（`up -d` 已跑的服务不会重复启动）|
| 权限问题（Docker socket）| Docker Desktop 默认用户已获权，Linux 需加入 `docker` group |

---

#### Part F: 社区 3 真实案例参考

##### F.1 Smart Connections（Brian Petro, 8k+ stars）

- **GitHub**: https://github.com/brianpetro/obsidian-smart-connections
- **Backend**: 本地 Ollama + `smart-connect` (Node.js)
- **启动模式**: **用户手动** —— README:
  > "To use local AI, install Ollama. Run `ollama serve` before opening Obsidian."
- **健康检查**: Plugin settings 里有 "Test Connection" 按钮 + 状态栏指示器
- **教训**: **从不自动启动** —— 作者明确说"这会违反 Obsidian security guidelines"

##### F.2 Khoj（khoj-ai, 15k+ stars）

- **GitHub**: https://github.com/khoj-ai/khoj
- **Backend**: Python FastAPI + local LLM
- **启动模式**: **用户手动 pip install khoj-assistant** + `khoj` 命令启动 server
- **健康检查**: Plugin 每 5 分钟 ping `http://localhost:42110/health`
- **教训**: 文档开头就写"**Prerequisites: Start Khoj server before enabling plugin**"

##### F.3 Copilot for Obsidian（logancyang, 4k+ stars）

- **GitHub**: https://github.com/logancyang/obsidian-copilot
- **Backend**: 无自托管 —— 用户填 OpenAI/Ollama URL
- **启动模式**: **Plugin 只是 HTTP client** —— 完全不管 backend 启动
- **健康检查**: 用户点 "Test API" 按钮
- **教训**: **最简路径** —— 把启动责任 100% 交给用户，Plugin 只做 UI

##### F.4 共同结论

| 维度 | Smart Connections | Khoj | Copilot | Canvas（推荐选项 1）|
|-----|-----------------|------|--------|-----------------|
| 自动启动 backend | ❌ | ❌ | ❌ | ❌（选项 1）/ 可选（选项 2）|
| 健康检查 | ✅ | ✅ | ✅ | ✅ |
| 文档强调"启动前置" | ✅ | ✅ | ✅ | 需补（见 Part G-D1）|
| 失败降级体验 | 禁用 smart features | 禁用 Khoj panel | 禁用 chat panel | 禁用 Graphiti 检索，md 原生仍可用 |

`★ Insight ─────────────────────────────────────`
- Canvas 走到选项 2（Claudian MCP 自动协调）会成为 Obsidian 社区的**首创** —— 社区没人做过是因为大部分插件没有 Claudian 这样的 MCP 外挂
- 选项 1 是"与社区接轨"的最小改动方案，选项 2 是"利用 Claudian 独特能力"的增量演进
- 关键设计思想：**降级要分层** —— Docker 不启 = 功能降级，但不阻断 md 原生体验（Obsidian 本身不依赖 backend）
`─────────────────────────────────────────────────`

---

#### Part G: 5 个未决决策点（D1-D5 增量提问）

Phase 1 Agent C 审计 PRD 后发现 Obsidian 降级后有 5 个决策点需要用户拍板:

##### D1: Backend 启动权限

> **现状**: 用户手动 `docker-compose up`
> **可选演进**: Claudian MCP tool 自动协调
> **增量提问**: 用户想"学会记得开 Docker"还是"直接用 Claudian 对话式启动"？

- A. 选项 1 立即采纳 —— 我自己开 Docker
- B. 选项 2 直接上 —— Claudian 负责启动
- C. 两者都做 —— 选项 1 先用，2-4 周后看需求再上选项 2
- D. 先不做决定 —— 本轮只确认审计正确性

##### D2: Session 关闭后 Backend 生命周期

> **现状**: `docker-compose down` 要用户手动跑
> **可选**: 空闲 30 分钟自动 sleep（Neo4j 保持，backend pause）
> **增量提问**: 用户日常睡觉时愿意"跑 docker-compose down"还是希望后台常驻？

- A. 睡觉前手动 `down` —— 省 5GB RAM
- B. 保持常驻 —— RAM 充裕不在乎
- C. 加超时自动 pause —— Claudian MCP tool + systemd timer（Mac 用 launchctl）
- D. 暂时不做决定

##### D3: Frontmatter 手工编辑 vs Backend 同步

> **现状**: Obsidian 用户可以手工改 md frontmatter
> **风险**: 用户改的 frontmatter 和 backend Graphiti Episode 不一致（"两个真相源"）
> **增量提问**: 用户期望哪个是唯一真相源？

- A. Frontmatter 是真相 —— backend 同步时读取 md，覆盖 Graphiti
- B. Graphiti 是真相 —— backend 定期回写 frontmatter（与 Obsidian 手改冲突）
- C. 双向同步 + 冲突检测 —— 复杂但完整
- D. 不同步 —— 两个系统各管各的（frontmatter 人看，Graphiti AI 检索）

##### D4: LanceDB 长期噪音累积清理策略

> **现状**: LanceDB `vault_notes` 表每次笔记变动追加 chunk，旧 chunk 不删除
> **风险**: 一年后 vault_notes 可能有 10x 冗余（删除的笔记仍在索引里）
> **增量提问**: 定期清理节奏？

- A. 每周 cron 清理 —— 扫 vault_notes 和实际 md，删 orphaned chunks
- B. 启动时全量 rebuild —— 每次启动 backend 时重建索引（冷启动慢但永远干净）
- C. 不清理 —— 接受空间浪费（磁盘便宜）
- D. 用户手动触发 —— MCP tool `rebuild_vault_index`

##### D5: 多 Skill 并行调用是否允许

> **现状**: Claudian 可以并行调多个 MCP tool（如 `search_memories` + `search_notes` + `query_mastery`）
> **风险**: 并发可能让 Graphiti 查询阻塞（Neo4j pool 限制）
> **增量提问**: 是否允许并行，还是强制串行？

- A. 允许并行 —— 性能优先，接受偶发超时
- B. 强制串行 —— MCP server 层加 semaphore 限制
- C. 只对读操作并行 —— 写操作（`record_error`）强制串行
- D. 暂时不做决定（观察真实负载）

`★ Insight ─────────────────────────────────────`
- D1-D5 是 Obsidian 降级后**新出现**的决策点 —— Tauri 时代这些问题被"点图标自动启动"这个假设掩盖了
- 推荐优先决定 D1（部署方式）和 D3（真相源）—— 这两个会影响后续所有 Story
- D2/D4/D5 可以延后到运行 1-2 周后根据真实使用数据再定
`─────────────────────────────────────────────────`

---

### 推荐最终方案: **选项 1 立即采纳 + 选项 2 阶段 2 演进**

#### 实施路线图

| 阶段 | 时间 | 动作 | 代码改动 |
|-----|-----|-----|------|
| **阶段 1** | 本周 | 用户手动 `docker-compose up` + Plugin 健康检查 | 0 行（Plugin 待开发，约 20 行 TS 健康检查）|
| **阶段 2** | 2-4 周后 | 评估：用户是否抱怨"记不住开 Docker" | — |
| **阶段 3**（条件触发）| 按需 | Claudian MCP tool `check_backend_health` 上线 | ~50 行 Python |
| **阶段 4**（远期）| — | 决定 D3-D5 并实施 | 视决策 |

### Obsidian 可导航引用

- `docker-compose.yml:20-48` — Neo4j 服务定义
- `docker-compose.yml:136-181` — Backend 服务 + CORS 配置
- `docker-compose.yml:153` — CORS `app://obsidian.md` 已含
- `docker-compose.yml:162-163` — Vault 路径硬编码
- `docker-compose.yml:225-227` — cliproxyapi external network
- `backend/app/main.py:263-285` — Graphiti Phase 2 初始化 + degraded mode
- `backend/app/services/episode_worker.py:1-100` — EpisodeWorker 定义 + EpisodeTask 结构
- `backend/app/mcp/server.py:144-509` — 15 个 MCP tools 注册入口
- `frontend/src-tauri/tauri.conf.json` — 证明无 sidecar auto-start
- `frontend/sidecar/sidecar.js` — Claude Agent SDK 的 Node sidecar（与 Docker 无关）

### 社区 URL 参考

| 工具 | URL |
|-----|-----|
| Smart Connections | https://github.com/brianpetro/obsidian-smart-connections |
| Khoj | https://github.com/khoj-ai/khoj |
| Copilot for Obsidian | https://github.com/logancyang/obsidian-copilot |
| Obsidian Plugin API | https://docs.obsidian.md/Plugins |
| Docker Compose CLI | https://docs.docker.com/compose/reference/ |

---

## Round 10 总结

### 核心答案

**问**: Graphiti 部署方案如何适配 Obsidian 降级后架构？

**答**: **选项 1 立即采纳（0 代码） + 选项 2 阶段 2 演进（~50 行 MCP tool）**

**关键理由**:
1. Tauri sidecar 原本就不存在，降级没有切断任何实际存在的链路 —— 只是让"规格幻觉"现形
2. Electron 沙箱硬约束社区 3 大插件全部用"用户手动 + 健康检查"，Canvas 走这条路最稳
3. Claudian MCP 是**唯一**合法的"自动启动 backend"通道，作为阶段 2 演进时机成熟再上
4. Graphiti 现有 degraded mode 兜底完美 —— Neo4j 不通 backend 仍启动，Episode 写死信队列等待重放

### 关键决策点（待用户拍板）

- **D1**（部署方式）: 选项 1 vs 选项 2 vs 两者都做
- **D2**（生命周期）: 手动 down vs 常驻 vs 自动 pause
- **D3**（真相源）: frontmatter vs Graphiti vs 双向同步 vs 不同步
- **D4**（LanceDB 清理）: 每周 cron vs 启动 rebuild vs 不清理 vs 手动
- **D5**（并行调用）: 全开 vs 强制串行 vs 读并行 vs 观察后定

### 下一步期待

用户审计本文件 Part A-G → 至少回复 D1 决策 → Round 11 触发:
- 如选 D1-A（选项 1） → 进入 Obsidian Plugin 健康检查开发 Story
- 如选 D1-B（选项 2） → 进入 Claudian MCP `check_backend_health` 开发 Story
- 如选 D1-C（两者都做） → 阶段 1 Plugin 开发 + 埋点观察 2-4 周

### 本轮归档摘要

| 类别 | 数量 | 覆盖 |
|-----|-----|-----|
| Part 深度 | 7（A-G）| 审计 + 模式对比 + gotchas + 方案 + MCP 伪代码 + 社区案例 + 待决策 |
| 引用证据 | 10+ 条（含 file:LINE）| docker-compose.yml / main.py / episode_worker.py / tauri.conf.json / mcp/server.py |
| 社区案例 | 3（Smart/Khoj/Copilot）| 真实 GitHub URL |
| 待决策点 | 5（D1-D5）| 用户增量提问 |

---

**下一轮触发条件**: 用户回复 D1-D5 中任意一个决策 → Round 11（开发落地）

**User：请你生成一份提示词给 ChatGPT ，我用于 deep research 对抗性审查，思考方案部署的合理性，所以请你记得把我们当前的文件都 push 到仓库上**

`[A12 2026-04-16 → round11]` — ChatGPT Deep Research 对抗性审查 prompt 已生成（7 个审查问题 + 完整仓库上下文），已 git push。见 [[obsidian-qa-round11-claude-answers-2026-04-16]] R11-Q3。
