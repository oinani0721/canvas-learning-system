# EPIC 1 非技术用户验收指南

> **版本**: 1.1 | **日期**: 2026-04-17 | **覆盖**: 13/13 Stories
>
> 本文档面向**非技术用户**。你只需要：一个浏览器 + Obsidian + 终端（运行脚本时）。
> 每个测试步骤都写成"你做什么 → 你应该看到什么"的格式。
>
> 每个 Story 标题旁的 `[[链接]]` 可在 Obsidian 中直接点击跳转到对应的 BMAD spec 文件。

---

## 验收用 Vault — 打开哪个？

你需要在 Obsidian 中打开 **`canvas-vault`** 这个 vault 来进行验收。

| 项目 | 值 |
|------|---|
| **Vault 名称** | `canvas-vault` |
| **磁盘路径** | `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault` |
| **Obsidian 打开方式** | Obsidian → 左下角 vault 名称 → Open another vault → Open folder → 选择上述路径 |
| **URI 快捷方式** | `obsidian://open?vault=canvas-vault` （浏览器地址栏粘贴即可打开） |

> **注意**: 如果你要测试 vault 切换（Story 1.8/1.9），需要**至少 2 个 vault**。可以在同级目录创建第二个 vault：
> ```bash
> mkdir -p /Users/Heishing/Desktop/canvas/canvas-learning-system/test-vault/.obsidian
> ```
> 这样你就有 `canvas-vault` 和 `test-vault` 两个可以互相切换。

### 阅读本文档的方式

本文档本身也在一个 Obsidian vault 中（`_bmad-output/` 目录）。你可以：
1. 在 Obsidian 中打开 `_bmad-output` 文件夹作为 vault
2. 点击文中的 `[[双链]]` 直接跳转到对应的 Story spec 原文

---

## 前置准备

在开始验收前，确保以下环境就绪：

1. **Docker 已启动**: 打开 Docker Desktop，确认状态栏显示绿色
2. **后端已运行**: 终端运行 `docker compose up -d`，等待 30 秒
3. **Obsidian 已打开**: 打开 `canvas-vault`（路径见上方）

**快速检查**: 浏览器打开 `http://localhost:8001/api/v1/system/health` — 如果看到 JSON 数据，说明后端正常运行。

---

## 验收清单总览

| Story | Spec 链接 | 功能 | 测试数 | 状态 |
|-------|-----------|------|--------|------|
| 1.1 | [[1-1-vault-init-templates]] | Vault 初始化 + 模板 | 4 | [ ] |
| 1.2 | [[1-2-wikilink-graph-build]] | Wikilink 图构建 | 4 | [ ] |
| 1.3 | [[1-3-wikilink-context-assembly]] | Wikilink MCP 工具 | 2 | [ ] |
| 1.4 | [[1-4-hotkey-binding-config]] | 快捷键绑定 | 4 | [ ] |
| 1.5 | [[1-5-hotkey-conflict-detection]] | 快捷键冲突检测 | 3 | [ ] |
| 1.6 | [[1-6-git-backup-kg-health]] | Git 备份 + KG 健康 | 3 | [ ] |
| 1.7 | [[1-7-root-env-docker-compose]] | 环境变量统一 | 3 | [ ] |
| 1.8 | [[1-8-vault-switch-runtime-api]] | Vault 运行时切换 | 4 | [ ] |
| 1.9 | [[1-9-lancedb-vault-id-isolation]] | LanceDB 数据隔离 | 3 | [ ] |
| 1.10 | [[1-10-health-endpoint-unification]] | 健康仪表盘 | 3 | [ ] |
| 1.11 | [[1-11-config-unification]] | 配置漂移检测 | 2 | [ ] |
| 1.12 | [[1-12-mcp-infra-tools-deployment-tier]] | MCP 基础设施工具 | 2 | [ ] |
| 1.13 | [[1-13-deployment-checklist-external-net]] | 部署预检脚本 | 2 | [ ] |

---

## [[1-1-vault-init-templates|Story 1.1]]: Vault 初始化

> **一句话**: 第一次打开时，系统自动帮你搭好笔记库的文件夹结构和模板。

### 测试 1: 文件夹结构

- [ ] **你做什么**: 在 Obsidian 的文件浏览器中查看 `canvas-vault` 根目录
- [ ] **你应该看到**:
  - `raw/` 文件夹（存放原始导入笔记）
  - `wiki/concepts/` 文件夹（存放概念笔记）
  - `wiki/canvases/` 文件夹（存放 Canvas 画布）
  - `outputs/exam_boards/` 文件夹（存放考察板）
  - `CLAUDE.md` 文件（系统说明文档）
- [ ] **如果不对**: 记录"[[1-1-vault-init-templates|Story 1.1]] — 缺少文件夹: ___"

### 测试 2: 概念笔记模板

- [ ] **你做什么**: 在 `wiki/concepts/` 中用 Templater 创建一篇新笔记
- [ ] **你应该看到**: 笔记顶部自动包含这些字段：
  ```
  mastery_score: 0
  bkt_p_mastery: 0.30
  nextReview: [日期]
  lastReview: [今天]
  relationships: []
  ```
- [ ] **如果不对**: 记录"[[1-1-vault-init-templates|Story 1.1]] — 模板字段缺失: ___"

### 测试 3: 插件检查

- [ ] **你做什么**: 浏览器打开 `http://localhost:8001/api/v1/system/startup-check`
- [ ] **你应该看到**: 每个组件显示 "healthy"：neo4j / ollama / fastapi / mcp
- [ ] **如果不对**: 记录哪个组件显示 "unhealthy" 以及错误信息

### 测试 4: 启动速度

- [ ] **你做什么**: 查看上面 startup-check 返回的 `latency_ms` 字段
- [ ] **你应该看到**: 每个组件都小于 3000（3 秒）
- [ ] **如果不对**: 记录"[[1-1-vault-init-templates|Story 1.1]] — 启动慢: ___ ms"

---

## [[1-2-wikilink-graph-build|Story 1.2]]: Wikilink 图

> **一句话**: 系统自动读取你笔记中的 `[[双链]]`，构建概念关联地图，AI 用它来找相关笔记。

### 测试 1: 图构建

- [ ] **你做什么**: 浏览器打开 `http://localhost:8001/api/v1/wikilink/stats`
- [ ] **你应该看到**:
  ```json
  { "data": { "is_built": true, "total_nodes": [>0], "total_edges": [>0] } }
  ```
  如果 `is_built` 是 false，先用 curl 触发构建：
  ```bash
  curl -X POST http://localhost:8001/api/v1/wikilink/build
  ```
- [ ] **如果不对**: 记录"[[1-2-wikilink-graph-build|Story 1.2]] — 图未构建"

### 测试 2: 邻居查询

- [ ] **你做什么**: 浏览器打开 `http://localhost:8001/api/v1/wikilink/neighbors/[你的某篇笔记名]`
- [ ] **你应该看到**: 返回相关概念列表，每个包含 `title`、`hop_distance`（1=直接链接）、`frontmatter`
- [ ] **如果不对**: 记录"[[1-2-wikilink-graph-build|Story 1.2]] — 邻居查询返回空或报错"

### 测试 3: 没有重复

- [ ] **你做什么**: 找一组互相引用的笔记（A→B→C→A），查询 A 的邻居
- [ ] **你应该看到**: B 和 C 各只出现一次（循环链接不会导致重复）
- [ ] **如果不对**: 记录"[[1-2-wikilink-graph-build|Story 1.2]] — 出现重复概念"

### 测试 4: 不存在的笔记

- [ ] **你做什么**: 查询一个不存在的笔记名
- [ ] **你应该看到**: 返回空列表 `"neighbors": []`，**不报错**
- [ ] **如果不对**: 记录"[[1-2-wikilink-graph-build|Story 1.2]] — 查询不存在的笔记时报错"

---

## [[1-3-wikilink-context-assembly|Story 1.3]]: Wikilink MCP 工具

> **一句话**: Claude 可以主动调用"查邻居"和"读笔记"工具来理解你的知识结构。

### 测试 1: get_neighbors 工具

- [ ] **你做什么**: 在 Claude Code 中问"我的 [某个概念] 有哪些相关笔记？"
- [ ] **你应该看到**: Claude 调用 `get_neighbors` 工具，返回相关概念列表
- [ ] **如果不对**: 记录"[[1-3-wikilink-context-assembly|Story 1.3]] — Claude 没有调用 wikilink 工具"

### 测试 2: read_note 工具

- [ ] **你做什么**: 问"帮我读一下 [某篇笔记名] 的内容"
- [ ] **你应该看到**: Claude 调用 `read_note` 工具，展示笔记全文
- [ ] **如果不对**: 记录"[[1-3-wikilink-context-assembly|Story 1.3]] — read_note 工具未被调用"

---

## [[1-4-hotkey-binding-config|Story 1.4]]: 快捷键绑定

> **一句话**: 在 Obsidian 设置中可以给 6 个学习命令绑定自定义快捷键。

### 测试 1: 命令注册

- [ ] **你做什么**: Obsidian → Settings（齿轮图标）→ Hotkeys → 搜索 "Canvas"
- [ ] **你应该看到** 6 个命令：
  - [ ] 启动学习对话
  - [ ] 启动考察
  - [ ] 提取概念
  - [ ] 批注考察
  - [ ] 打开仪表盘
  - [ ] 打开复习队列
- [ ] **如果不对**: 记录"[[1-4-hotkey-binding-config|Story 1.4]] — 命令缺失: ___"

### 测试 2: 绑定快捷键

- [ ] **你做什么**: 点击"启动学习对话"旁的 + 按钮 → 按 `Cmd+Shift+L` → 回到编辑器按该快捷键
- [ ] **你应该看到**: 对话启动，或看到后端响应
- [ ] **如果不对**: 记录"[[1-4-hotkey-binding-config|Story 1.4]] — 快捷键不响应"

### 测试 3: 默认无绑定

- [ ] **你做什么**: 首次安装后查看 Hotkeys 设置
- [ ] **你应该看到**: 所有 6 个命令旁边都是空的 + 按钮（没有预设快捷键）
- [ ] **如果不对**: 记录"[[1-4-hotkey-binding-config|Story 1.4]] — 有预设快捷键"

### 测试 4: 后端断连时

- [ ] **你做什么**: 停止后端（`docker compose down`），按已绑定的快捷键
- [ ] **你应该看到**: 右上角弹出提示"后端未连接，请先启动 Canvas 后端"（8 秒后消失）
- [ ] **如果不对**: 记录"[[1-4-hotkey-binding-config|Story 1.4]] — 后端断连时崩溃或无提示"

---

## [[1-5-hotkey-conflict-detection|Story 1.5]]: 快捷键冲突检测

> **一句话**: 如果你不小心把两个命令绑到同一个快捷键，系统会提醒你。

### 测试 1: 检测冲突

- [ ] **你做什么**: 把"启动学习对话"和"启动考察"都绑到 `Cmd+Shift+L` → 重启 Obsidian
- [ ] **你应该看到**: 黄色通知"Canvas 快捷键冲突: Cmd+Shift+L 同时绑定了 '启动学习对话' 和 '启动考察'"
- [ ] **如果不对**: 记录"[[1-5-hotkey-conflict-detection|Story 1.5]] — 冲突未被检测"

### 测试 2: 无冲突时静默

- [ ] **你做什么**: 确保每个命令绑定不同的快捷键（或不绑定）→ 重启 Obsidian
- [ ] **你应该看到**: 没有任何冲突警告
- [ ] **如果不对**: 记录"[[1-5-hotkey-conflict-detection|Story 1.5]] — 无冲突时误报"

### 测试 3: 修饰键顺序

- [ ] **你做什么**: 一个命令绑 `Cmd+Shift+C`，另一个绑 `Shift+Cmd+C` → 重启
- [ ] **你应该看到**: 检测到冲突（两者是同一个快捷键）
- [ ] **如果不对**: 记录"[[1-5-hotkey-conflict-detection|Story 1.5]] — 修饰键顺序不同未被视为冲突"

---

## [[1-6-git-backup-kg-health|Story 1.6]]: Git 备份 + 知识图谱健康

> **一句话**: 帮你设置好备份忽略规则 + 一个 URL 查看知识图谱的健康状况。

### 测试 1: .gitignore 自动生成

- [ ] **你做什么**: 在 `canvas-vault` 根目录查看 `.gitignore` 文件
- [ ] **你应该看到** 文件包含：`data/lancedb/`、`data/neo4j/`、`.obsidian/workspace.json`
- [ ] **如果不对**: 记录"[[1-6-git-backup-kg-health|Story 1.6]] — .gitignore 缺失或内容不全"

### 测试 2: KG 健康报告

- [ ] **你做什么**: 浏览器打开 `http://localhost:8001/api/v1/kg/health`
- [ ] **你应该看到**: `total_nodes`、`total_relationships`、`orphaned_count`、`neo4j_available: true`
- [ ] **如果不对**: 记录返回的错误信息

### 测试 3: Neo4j 断连时

- [ ] **你做什么**: 停止 Neo4j（`docker compose stop neo4j`），再访问 `/kg/health`
- [ ] **你应该看到**: `"neo4j_available": false` + 错误提示含"Neo4j 未连接"+ 修复命令
- [ ] **如果不对**: 记录"[[1-6-git-backup-kg-health|Story 1.6]] — Neo4j 断连时崩溃"

---

## [[1-7-root-env-docker-compose|Story 1.7]]: 环境变量统一

> **一句话**: 所有配置集中在一个 `.env` 文件，改一处就行。

### 测试 1: .env.example 存在

- [ ] **你做什么**: 在项目根目录查看 `.env.example` 文件
- [ ] **你应该看到**: 包含 `NEO4J_USER`、`NEO4J_PASSWORD`、`VAULTS_ROOT`、`ACTIVE_VAULT`、`CANVAS_BASE_PATH` 等变量，每个都有中文注释
- [ ] **如果不对**: 记录"[[1-7-root-env-docker-compose|Story 1.7]] — .env.example 缺失"

### 测试 2: 一键启动

- [ ] **你做什么**: `cp .env.example .env` → 编辑 `.env` 填入密码和路径 → `docker compose up -d`
- [ ] **你应该看到**: 所有服务正常启动，无报错
- [ ] **如果不对**: 记录"[[1-7-root-env-docker-compose|Story 1.7]] — 启动报错: ___"

### 测试 3: 不需要改 docker-compose.yml

- [ ] **你做什么**: 只修改 `.env` 中的端口（如 `API_PORT=9001`），重新 `docker compose up -d`
- [ ] **你应该看到**: 后端在新端口启动，无需编辑 `docker-compose.yml`
- [ ] **如果不对**: 记录"[[1-7-root-env-docker-compose|Story 1.7]] — 改 .env 没生效"

---

## [[1-8-vault-switch-runtime-api|Story 1.8]]: Vault 切换

> **一句话**: 在不同课程 vault（如 canvas-vault → test-vault）之间切换，不需要重启。

### 测试 1: 查看当前 Vault

- [ ] **你做什么**: 浏览器打开 `http://localhost:8001/api/v1/vault/current`
- [ ] **你应该看到**:
  ```json
  {
    "vault_path": "/Users/Heishing/.../canvas-vault",
    "vault_name": "canvas-vault",
    "vault_id": "canvas_vault",
    "vaults_root": "/Users/Heishing/.../canvas-learning-system"
  }
  ```
- [ ] **如果不对**: 记录返回的内容

### 测试 2: 切换 Vault

- [ ] **你做什么**: 终端运行（替换为你的实际路径）：
  ```bash
  curl -X POST http://localhost:8001/api/v1/vault/switch \
    -H "Content-Type: application/json" \
    -d '{"vault_path": "/Users/Heishing/.../test-vault"}'
  ```
- [ ] **你应该看到**: 返回新 vault 信息，包含 `"vault_name": "test-vault"` 和 `"previous_vault": "canvas-vault"`
- [ ] **如果不对**: 记录返回的错误信息

### 测试 3: 切换后确认

- [ ] **你做什么**: 再次访问 `/vault/current`
- [ ] **你应该看到**: `vault_name` 已变为 `test-vault`
- [ ] **如果不对**: 记录"[[1-8-vault-switch-runtime-api|Story 1.8]] — 切换后 /current 未更新"

### 测试 4: 非法路径拒绝

- [ ] **你做什么**: 尝试切换到不存在的路径 或 没有 `.obsidian/` 的普通文件夹
- [ ] **你应该看到**: 400 错误 + "Directory does not exist" 或 "Not an Obsidian vault (missing .obsidian/)"
- [ ] **如果不对**: 记录"[[1-8-vault-switch-runtime-api|Story 1.8]] — 非法路径未被拒绝"

---

## [[1-9-lancedb-vault-id-isolation|Story 1.9]]: 数据隔离

> **一句话**: 在 vault A 搜东西不会出现 vault B 的内容，反之亦然。

### 测试 1: 搜索隔离

- [ ] **你做什么**:
  1. 在当前 vault 搜索某个概念 → 记录结果
  2. 切换到另一个 vault（[[1-8-vault-switch-runtime-api|用 Story 1.8 的切换 API]]）
  3. 搜索相同概念
- [ ] **你应该看到**: 第二个 vault 的搜索结果中**不包含**第一个 vault 的内容
- [ ] **如果不对**: 记录"[[1-9-lancedb-vault-id-isolation|Story 1.9]] — 搜索结果跨 vault 泄漏"

### 测试 2: 索引统计

- [ ] **你做什么**: 浏览器打开 `http://localhost:8001/api/v1/index/stats`
- [ ] **你应该看到**: 按 vault_id 分组的统计：`{"canvas_vault": {"tables": N, "rows": N}, ...}`
- [ ] **如果不对**: 记录返回的内容

### 测试 3: 独立删除

- [ ] **你做什么**: `curl -X DELETE http://localhost:8001/api/v1/index/canvas_vault`，然后检查另一个 vault 是否仍能搜索
- [ ] **你应该看到**: 被删除的 vault 索引清空，其他 vault 不受影响
- [ ] **如果不对**: 记录"[[1-9-lancedb-vault-id-isolation|Story 1.9]] — 删除一个 vault 影响了其他"

---

## [[1-10-health-endpoint-unification|Story 1.10]]: 健康仪表盘

> **一句话**: 一个 URL 看所有组件的状态灯——绿灯正常、黄灯勉强、红灯挂了，还告诉你怎么修。

### 测试 1: 查看详细状态

- [ ] **你做什么**: 浏览器打开 `http://localhost:8001/api/v1/system/health/detailed`
- [ ] **你应该看到**: 5 个组件各自的状态：
  | 组件 | 预期状态 | 含义 |
  |------|---------|------|
  | neo4j | ready | 数据库正常 |
  | ollama | ready | AI 模型正常 |
  | lancedb | ready / degraded | 搜索引擎（首次可能未创建） |
  | fastapi | ready | 后端正常 |
  | mcp | ready | Claude 工具正常 |
- [ ] **如果不对**: 记录哪个组件异常

### 测试 2: 修复提示

- [ ] **你做什么**: 如果某个组件显示 "unavailable"，查看它的 `fix_hint` 字段
- [ ] **你应该看到**: 具体的修复命令，如：
  - Neo4j: "确认 Neo4j 容器运行中: docker compose up -d neo4j"
  - Ollama: "确保 Ollama 正在运行: ollama serve"
- [ ] **如果不对**: 记录"[[1-10-health-endpoint-unification|Story 1.10]] — fix_hint 为空或不准确"

### 测试 3: 总体状态码

- [ ] **你做什么**: 注意响应的 HTTP 状态码
- [ ] **你应该看到**:
  - 所有 ready → **200**
  - 有 degraded → **200**
  - Neo4j unavailable → **503**
- [ ] **如果不对**: 记录"[[1-10-health-endpoint-unification|Story 1.10]] — 状态码不正确"

---

## [[1-11-config-unification|Story 1.11]]: 配置漂移检测

> **一句话**: 系统帮你检查 root `.env` 和 backend `.env` 是否一致。

### 测试 1: 检查一致性

- [ ] **你做什么**: 浏览器打开 `http://localhost:8001/api/v1/system/config-check`
- [ ] **你应该看到**: `"drifts": []`（空 = 一致）+ `"synced": ["NEO4J_USER", "DEBUG", ...]`
- [ ] **如果不对**: 记录 drifts 的内容

### 测试 2: 检测不一致

- [ ] **你做什么**: 故意修改 `backend/.env` 中的 `DEBUG` 为不同值 → 再访问 `/system/config-check`
- [ ] **你应该看到**: `drifts` 中出现 `{"key": "DEBUG", "root": "true", "backend": "false"}`
- [ ] **如果不对**: 记录"[[1-11-config-unification|Story 1.11]] — 漂移未被检测"

---

## [[1-12-mcp-infra-tools-deployment-tier|Story 1.12]]: MCP 基础设施工具

> **一句话**: Claude 可以帮你检查后端状态、切换 vault，不需要你手动输入 URL。

### 测试 1: 健康检查工具

- [ ] **你做什么**: 在 Claude Code 中说"检查后端健康状态"
- [ ] **你应该看到**: Claude 调用 `check_backend_health` 工具，返回各组件状态报告
- [ ] **如果不对**: 记录"[[1-12-mcp-infra-tools-deployment-tier|Story 1.12]] — Claude 没有调用健康检查工具"

### 测试 2: Vault 切换工具

- [ ] **你做什么**: 在 Claude Code 中说"帮我切换到 test-vault"
- [ ] **你应该看到**: Claude 调用 `switch_vault` 工具 → 需要你确认（DEPLOYMENT_TOOLS 权限层）→ 确认后切换成功
- [ ] **如果不对**: 记录"[[1-12-mcp-infra-tools-deployment-tier|Story 1.12]] — 切换工具未被调用或未要求确认"

---

## [[1-13-deployment-checklist-external-net|Story 1.13]]: 部署预检

> **一句话**: 启动前自动检查所有前置条件，逐项打勾或报错。

### 测试 1: 运行预检脚本

- [ ] **你做什么**: 在终端运行（从项目根目录）：
  ```bash
  ./scripts/pre-deploy-check.sh
  ```
- [ ] **你应该看到**: 逐项检查结果：
  ```
  ✅ PASS Docker Desktop is running
  ✅ PASS .env exists with required variables
  ✅ PASS Port 7478 (Neo4j HTTP) available
  ✅ PASS Port 7691 (Neo4j Bolt) available
  ✅ PASS Port 8001 (Backend API) available
  ✅ PASS Ollama is running
  ✅ PASS Ollama bge-m3 model available
  ✅ PASS CORS config includes app://obsidian.md
  ✅ PASS Vault path exists
  ═══════════════════════════════════════════════
    All checks passed! Run: docker compose up -d
  ═══════════════════════════════════════════════
  ```
- [ ] **如果不对**: 记录哪些项显示 ❌ FAIL

### 测试 2: 失败时的修复提示

- [ ] **你做什么**: 停止 Ollama（`pkill ollama`），再运行预检脚本
- [ ] **你应该看到**: Ollama 项显示 `❌ FAIL` + 修复命令 `Fix: ollama serve`
- [ ] **如果不对**: 记录"[[1-13-deployment-checklist-external-net|Story 1.13]] — 没有修复提示"

---

## 发现问题如何记录

请按以下格式记录，方便开发者复现：

```
[[Story spec 链接]] — [简短描述]
- 我做了什么: [操作步骤]
- 我期望看到: [文档说的]
- 我实际看到: [实际情况]
- 错误信息: [完整复制]
- 时间: [年-月-日 时:分]
- vault: [哪个 vault]
```

**示例**:
```
[[1-8-vault-switch-runtime-api|Story 1.8]] — Vault 切换报错
- 我做了什么: curl 发送 POST /vault/switch，vault_path 指向 test-vault
- 我期望看到: 返回新 vault 信息
- 我实际看到: 400 错误 "Not an Obsidian vault"
- 错误信息: {"error":"vault_not_found","message":"Not an Obsidian vault (missing .obsidian/)"}
- 时间: 2026-04-17 15:30
- vault: test-vault
```

---

## 所有 API 端点速查

**基础 URL**: `http://localhost:8001/api/v1`

| 端点 | 方法 | Story Spec | 说明 |
|------|------|------------|------|
| `/system/health` | GET | [[1-1-vault-init-templates]] | 基础健康检查 |
| `/system/health/detailed` | GET | [[1-10-health-endpoint-unification]] | 详细三级状态 |
| `/system/startup-check` | GET | [[1-1-vault-init-templates]] | 启动依赖检查 |
| `/system/config-check` | GET | [[1-11-config-unification]] | 配置漂移检查 |
| `/system/setup-wizard` | POST | [[1-1-vault-init-templates]] | 初始化向导 |
| `/vault/current` | GET | [[1-8-vault-switch-runtime-api]] | 当前 vault 信息 |
| `/vault/switch` | POST | [[1-8-vault-switch-runtime-api]] | 切换 vault |
| `/wikilink/build` | POST | [[1-2-wikilink-graph-build]] | 构建 wikilink 图 |
| `/wikilink/stats` | GET | [[1-2-wikilink-graph-build]] | 图统计信息 |
| `/wikilink/neighbors/{path}` | GET | [[1-2-wikilink-graph-build]] | N-hop 邻居查询 |
| `/wikilink/refresh` | POST | [[1-2-wikilink-graph-build]] | 热更新图 |
| `/kg/health` | GET | [[1-6-git-backup-kg-health]] | 知识图谱健康 |
| `/index/stats` | GET | [[1-9-lancedb-vault-id-isolation]] | 索引统计 |
| `/index/{vault_id}` | DELETE | [[1-9-lancedb-vault-id-isolation]] | 删除 vault 索引 |
