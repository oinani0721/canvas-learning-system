---
story_id: "1.13"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 4
depends_on: ["1.7"]
blocks: []
trace:
  - "FR-DEPLOY-03"
  - "FR-OPS-03"
---

# Story 1.13: 部署预检清单 + External Network 条件化

Status: ready-for-dev

## Story

As a 开发者/新用户,
I want 一个自动化的部署预检脚本能在 `docker-compose up` 之前检查所有前提条件，并且 external network 只在需要时创建,
So that 我不会因为端口冲突、缺少模型、网络不存在等可预防的错误浪费时间排查。

## 通俗化解释（给学习者）

> **一句话说**: 起飞前先做安全检查，别飞到半空才发现没油。

**你会遇到的场景**:
- 你运行 `docker-compose up`，等了 2 分钟报错"network cliproxyapi_default not found"，原来是因为另一个项目的 Docker 网络没创建
- Neo4j 端口 7691 被别的进程占了，启动失败，错误信息是一堆 Docker 日志看不懂
- 你同学第一次跑项目，Ollama 没装 bge-m3 模型，后端启动后向量索引一直失败
- 你不知道 Ollama 只能跑在 Mac 原生环境（不是 Docker），折腾了半天 Docker 里跑 Ollama

**这个功能帮你**:
- 运行一个预检脚本，2 秒内告诉你所有前提条件是否满足
- 每项检查给出清晰的"通过/未通过 + 修复命令"
- `cliproxyapi-network` 不存在时自动创建或跳过（不报错终止）

**用个比喻**: 就像飞行员起飞前的 checklist — 油量 ✅ / 引擎 ✅ / 通信 ✅ / 跑道 ✅。有一项不过就不起飞，告诉你具体哪里要修。

## Acceptance Criteria

1. **Given** 用户准备部署
   **When** 运行 `scripts/pre-deploy-check.sh`
   **Then** 按顺序检查以下项目：
   - Docker Desktop 运行中
   - `.env` 文件存在且必需变量已设置
   - 端口 7478/7691/8001 未被占用
   - Ollama 原生安装且运行中（非 Docker）
   - Ollama bge-m3 模型已下载
   - CORS 配置包含 `app://obsidian.md`
   **And** 每项输出 `✅ PASS` 或 `❌ FAIL: [修复命令]`

2. **Given** `cliproxyapi-network` Docker external network
   **When** 该网络不存在
   **Then** docker-compose 不因此报错终止
   **And** 通过 docker-compose profiles 或条件化配置实现可选依赖

3. **Given** docker-compose.yml 中 external network 配置
   **When** `ENABLE_CLIPROXY=true`（默认 false）
   **Then** backend 服务加入 `cliproxyapi-network`
   **When** `ENABLE_CLIPROXY` 未设置或为 false
   **Then** backend 服务只加入 `canvas-network`

4. **Given** bind mount 路径配置
   **When** `CANVAS_BASE_PATH` 指向的目录不存在
   **Then** 预检脚本检测并报错：`❌ FAIL: vault 路径 /path/to/vault 不存在`
   **And** 提示修正 `.env` 中的 `CANVAS_BASE_PATH`

5. **Given** Neo4j 使用非默认端口
   **When** 用户查看文档
   **Then** 预检脚本和 `.env.example` 都注明：HTTP=7478（非默认 7474），Bolt=7691（非默认 7687）
   **And** 说明原因：避免与现有 Neo4j 实例（7474/7687）和 Graphiti（7689）冲突

6. **Given** Mode 3 PoC（R12 [N3]）
   **When** 用户想验证 cliproxyapi 集成
   **Then** 文档提供一键验证脚本 `scripts/test-cliproxy.sh`
   **And** 脚本检查 cliproxyapi 容器运行 + 网络连通 + 后端可通过代理访问

7. **Given** 预检脚本运行完成
   **When** 所有检查通过
   **Then** 输出 `🚀 All checks passed. Run: docker-compose up -d`
   **When** 有失败项
   **Then** 输出失败总结 + 不自动启动 Docker

## Tasks / Subtasks

- [ ] Task 1: 预检脚本 (AC: #1, #4, #7)
  - [ ] 1.1: 创建 `scripts/pre-deploy-check.sh`
  - [ ] 1.2: Docker Desktop 检测（`docker info` 是否成功）
  - [ ] 1.3: `.env` 存在 + 必需变量检查（复用 `validate-env.sh` 逻辑）
  - [ ] 1.4: 端口占用检测（`lsof -i :7478 -i :7691 -i :8001`）
  - [ ] 1.5: Ollama 检测（`which ollama` + `ollama list | grep bge-m3`）
  - [ ] 1.6: CORS 配置检查（`.env` 中 CORS_ORIGINS 包含 `app://obsidian.md`）
  - [ ] 1.7: Vault 路径存在性检查
  - [ ] 1.8: 总结输出 + 退出码（0 = 全部通过，1 = 有失败）

- [ ] Task 2: External Network 条件化 (AC: #2, #3)
  - [ ] 2.1: 修改 `docker-compose.yml`，将 `cliproxyapi-network` 从 `external: true` 改为条件化
  - [ ] 2.2: 方案 A（推荐）：使用 Docker Compose profiles，`ENABLE_CLIPROXY=true` 时才创建网络
  - [ ] 2.3: 方案 B（备选）：使用 `docker-compose.override.yml` 分离 cliproxy 配置
  - [ ] 2.4: 默认配置下 `docker-compose up` 不依赖任何 external network

- [ ] Task 3: 文档化 (AC: #5, #6)
  - [ ] 3.1: 在 `.env.example` 中注明 Neo4j 非默认端口及原因
  - [ ] 3.2: 创建 `docs/deployment-guide.md`，包含预检流程 + 故障排除
  - [ ] 3.3: 添加 Ollama Mac native 说明（不能 Docker 化的原因：GPU 直通）
  - [ ] 3.4: 创建 `scripts/test-cliproxy.sh`，Mode 3 PoC 验证脚本

- [ ] Task 4: 测试 (AC: #1, #2)
  - [ ] 4.1: 在 CI 环境中运行预检脚本（模拟各种缺失场景）
  - [ ] 4.2: 验证无 cliproxyapi-network 时 docker-compose config 仍合法
  - [ ] 4.3: 验证有 cliproxyapi-network 时 backend 正确加入双网络

## Dev Notes

- **6 Gotchas（R10）**: Round 10 发现的 6 个部署陷阱，本 Story 全部覆盖：
  1. Vault 路径硬编码 → Story 1.7 已解决，本 Story 预检脚本验证
  2. CORS `app://obsidian.md` 未测 → 预检脚本检查
  3. Ollama Mac native only → 文档 + 预检脚本
  4. NEO4J_PASSWORD 不一致 → Story 1.11 + 预检脚本
  5. cliproxyapi external network → 本 Story 条件化
  6. Neo4j 非默认端口 → 文档 + 预检脚本
- **docker-compose.yml:225-227**: `cliproxyapi-network` 当前声明为 `external: true`，如果网络不存在会导致 `docker-compose up` 失败
- **Docker Compose profiles**: v2.4+ 支持 `profiles` 字段，可用于条件化启用服务/网络
- **R12 [N3] Mode 3 PoC**: R12 给出了 cliproxyapi 集成的概念验证代码，本 Story 将其固化为测试脚本
- **R12 [I2] External network 依赖**: 承认 external network 导致首次部署失败的问题
- **R12 [I4] Bind mount 路径敏感**: 路径不存在时 Docker 会自动创建空目录而非报错，需要预检捕获
- **QA 来源**: R10 6 Gotchas + R12 [I2]（external network）+ R12 [I4]（bind mount）+ R12 [N3]（Mode 3 PoC）

### Project Structure Notes

- 新建文件: `scripts/pre-deploy-check.sh`
- 新建文件: `scripts/test-cliproxy.sh`
- 新建文件: `docs/deployment-guide.md`
- 修改文件: `docker-compose.yml`（cliproxyapi-network 条件化）
- 修改文件: `.env.example`（端口说明注释）

### References

- [Source: docker-compose.yml:225-227] — cliproxyapi-network external 声明
- [Source: docs/known-gotchas.md] — 已知部署陷阱
- [Source: _bmad-output/research/obsidian-qa-round13-claude-answers-2026-04-16.md] — R10 6 Gotchas, R12 [I2][I4][N3]

## UAT Script

> 非技术用户验收脚本

1. **验证预检脚本** (AC: #1, #7)
   - 运行 `scripts/pre-deploy-check.sh`
   - 应看到每项检查的结果（绿色 ✅ 或红色 ❌）
   - 所有通过时显示"可以启动"提示

2. **验证缺失检测** (AC: #1, #4)
   - 故意把 `.env` 中的 vault 路径改成不存在的目录
   - 重新运行预检脚本，应看到红色提示 + 修复建议
   - 修正后再跑，应全部通过

3. **验证无 cliproxy 启动** (AC: #2, #3)
   - 确保 `ENABLE_CLIPROXY` 未设置或为 false
   - 运行 `docker-compose up -d`，不应因 cliproxyapi 网络不存在而报错
   - 服务正常启动

4. **验证端口说明** (AC: #5)
   - 查看 `.env.example`，应看到 Neo4j 端口 7478/7691 的说明
   - 查看 `docs/deployment-guide.md`，应有完整的部署指南

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.13.1 | shellcheck | `shellcheck scripts/pre-deploy-check.sh` | exit 0 |
| CP-1.13.2 | shellcheck | `shellcheck scripts/test-cliproxy.sh` | exit 0 |
| CP-1.13.3 | docker | `docker-compose config --quiet` | exit 0（无 external network 也合法）|
| CP-1.13.4 | grep | `grep -c 'ENABLE_CLIPROXY' docker-compose.yml` | ≥ 1 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**QA 来源追溯**:
1. **R10 6 Gotchas**: 全部 6 个部署陷阱都在预检脚本覆盖范围内
2. **R12 [I2]**: 承认 external network 导致首次部署失败 — 改为条件化可选
3. **R12 [I4]**: 承认 bind mount 路径敏感 — 预检脚本验证路径存在
4. **R12 [N3]**: 采纳 Mode 3 PoC — 固化为 test-cliproxy.sh 验证脚本

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
