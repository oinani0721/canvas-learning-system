---
story_id: "10.3"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 12  # Phase A 2-3h + Phase B 6-9h（Round-22 二轮 F4 修订重估，2026-05-07 对抗性审查 L1 同步）
depends_on: ["10.2"]
blocks: ["10.4"]
trace: ["FR-DEEP-03", "M11", "UX-1"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 2"
target_date: "2026-05-08"
uat_sheet: "_bmad-output/验收单/Story-10.3-day2-cleanup-vault-mount.md"
---

# Story 10.3: Day 2 Cleanup + Vault Mount

**Status**: ready-for-dev (target Day 2, 2026-05-08)

## Story（用户故事）

As a 学习者, I want my Canvas vault md files to be readable by DeepTutor + my callouts to render `[[wikilinks]]` so that all my existing notes work seamlessly without copying or syncing.

> **映射对**: M11（vault 不上传文件，知识库直接访问，Round-18 L805）+ UX-1（批注是核心操作单位）

## 通俗化解释（给学习者）

> **一句话说**: 让 DeepTutor 直接读你已有的 vault md 文件夹（不用上传不用同步），并且 callout 里写的 `[[xxx]]` 也能渲染成蓝链。

**你会遇到的场景**:
- 在 Obsidian 写了 `> [!question]+ 这个 [[递归]] 重要`
- 在 DeepTutor 打开同一笔记
- 期望 callout 内的 `[[递归]]` 显示为蓝色链接

**这个功能帮你**:
- vault 不用复制粘贴，DeepTutor 直接读你本地文件
- callout（`[!question]+ [!error]+`）内的双链也生效

**用个比喻**: 📁 就像 Mac 的"映射网络硬盘"——本地文件夹直接挂到 DeepTutor 容器里，DeepTutor 看到的就是你 Obsidian 里的实时内容。

## Acceptance Criteria

### AC #1: CalloutBlock wikilink 渲染（1 行修）

- **Given** fork `web/components/blocks/CalloutBlock.tsx` 当前 body 是 `<div>{body}</div>` 纯文本
- **When** 替换为 `<MarkdownRenderer content={body} variant="compact" />`
- **Then** `> [!question]+ See [[sorting]]` 中 `[[sorting]]` 渲染为蓝链
- **And** TimelineBlock/FlashCardsBlock/DeepDiveBlock 同理修复（顺手 4 个 block）

### AC #2: Canvas vault 路径挂载到 fork 容器

- **Given** Canvas vault 在 `~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp/canvas-vault/`
- **When** 修改 fork 的 `docker-compose.canvas.yml` bind mount path
- **Then** fork 容器内 `/vault` 指向真实 vault 路径
- **And** Canvas backend `:8011/api/v1/wikilink/build` 返回 `total_nodes > 0`

### AC #3: wikilink_neighbors path param 修复

- **Given** Canvas backend 路由 `/neighbors/{note_path:path}`（path param）
- **When** 修改 fork `deeptutor/services/canvas/client.py:65`
- **Then** `wikilink_neighbors(note_path, hop)` 调用 `GET /api/v1/wikilink/neighbors/{note_path}?hop={hop}`（不是 query param `?note_path=`）
- **And** 调用 `client.wikilink_neighbors("subjects/algorithms/recursion.md")` 返回邻居列表

### AC #4: docker-compose.canvas.yml 路径修正

- **Given** staging cp 进 fork 的 `docker-compose.canvas.yml` 路径写死指向旧 worktree
- **When** 改为参数化 `${CANVAS_WORKTREE_PATH}` 或当前 worktree 真实路径
- **Then** Day 3 时双服务 compose `docker compose -f docker-compose.yml -f docker-compose.canvas.yml up -d` 不报路径错误

## Tasks / Subtasks

- [ ] Task 1: CalloutBlock 1 行修 (AC: #1)
  - [ ] 1.1: Edit `~/Desktop/canvas/deeptutor-fork/web/app/(workspace)/book/components/blocks/CalloutBlock.tsx`
  - [ ] 1.2: 加 import `import MarkdownRenderer from "@/components/common/MarkdownRenderer"`
  - [ ] 1.3: 替换 `<div>{body}</div>` → `<MarkdownRenderer content={body} variant="compact" />`
  - [ ] 1.4: 同改 TimelineBlock.tsx + FlashCardsBlock.tsx + DeepDiveBlock.tsx（payload 字段不同，但逻辑同）

- [ ] Task 2: 修复 client.py path param (AC: #3)
  - [ ] 2.1: Edit `deeptutor/services/canvas/client.py:65`
  - [ ] 2.2: 改为 `return await self._request("GET", f"/api/v1/wikilink/neighbors/{note_path}", params={"hop": hop})`
  - [ ] 2.3: 注意 note_path URL encode（FastAPI `:path` 接受未编码 `/`）

- [ ] Task 3: vault 路径挂载 (AC: #2, #4)
  - [ ] 3.1: 修改 `docker-compose.canvas.yml` 把 `feature-obsidian-hybrid-dev` 路径替换为当前 worktree
  - [ ] 3.2: 或参数化 `${CANVAS_WORKTREE_PATH:-/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp}`
  - [ ] 3.3: Canvas worktree compose 加 vault bind mount: `./canvas-vault:/vault:rw`

- [ ] Task 4: vault 结构验证 (AC: #2)
  - [ ] 4.1: 确认 `canvas-vault/` 目录存在
  - [ ] 4.2: 确认 `.obsidian/` 子目录或建最小假目录
  - [ ] 4.3: `curl -X POST :8011/api/v1/wikilink/build` 返回 `total_nodes > 0`

- [ ] Task 5: rebuild + 验证
  - [ ] 5.1: `docker compose up -d --build deeptutor`（Story 10.3 改了 frontend 必须 rebuild）
  - [ ] 5.2: 浏览器验证 callout 内 `[[xxx]]` 渲染为蓝链
  - [ ] 5.3: `curl :8001/api/v1/wikilink/neighbors/some-real-note?hop=2` 返回邻居

## Dev Notes

### 修复来源
- **CalloutBlock**: Agent 2.3 发现"9/14 blocks 自动支持 wikilink"，CalloutBlock 是其中"低垂果实"，1 行修
- **path param**: Agent 1.1 + 主线对照发现 client query param 与 backend path param 不匹配
- **docker-compose.canvas.yml 路径**: Agent 2.4 发现路径硬编码指向旧 worktree

### 复用 Canvas 后端（零改动）
- `backend/app/api/v1/endpoints/wikilink.py` 已支持 `vault_path` 参数（无需改）
- `backend/app/services/wikilink_graph_service.py` `build_graph()` 期望 obsidiantools 布局

### 风险
- **R4 obsidiantools vault 布局期望**: 若 canvas-vault 结构不标准 → 建假 `.obsidian/config.json` 或 fork 服务放宽检查
- **R7 CalloutBlock 修复**: 1 行改动，但 4 个 block 同模式，必须一起修（避免遗漏）

## UAT 验收

详见 `_bmad-output/验收单/Story-10.3-day2-cleanup-vault-mount.md`

## References

- Round-22 主报告 §三 + §九（Canvas backend wikilink endpoints）
- Deep Explore §2.3 14 BlockType 渲染对照（CalloutBlock 漏网之鱼）
- Deep Explore §3.3 Day 2 路线
- Story 10.2 Dev Notes 已知陷阱

---

## Round-22 修订（2026-05-07 — Day 2 vault 设计深度调研）

> **修订源**: `_bmad-output/research/round-22-day2-vault-access-design-2026-05-06.md`（5 Agent 深度调研）+ `round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`

### 关键发现

**F1 manager.py:438 沙箱默认开（Phase A 0 改动验证）**

调研发现 DeepTutor `manager.py:438` 已硬编码 `restrict_to_workspace=False`，TutorBot ReadFileTool 默认开沙箱。**Day 2 Phase A 不需修改源码即可让 TutorBot 读 vault md**。

**F2 工作量翻倍（4h → 1.5-2d）**

原 Story spec estimate_hours=4 严重低估。实际可拆为 Phase A（2-3h，立即可做）+ Phase B（6-9h，可选升级）。

**F3 VaultMonitor 守护进程必要性**

DeepTutor 的 DocumentAdder 默认上传 vault → 内部存储 → 失去用户主权（NEG-2）。需 VaultMonitor daemon 监听 vault 文件变化 + 调用 vault_mode 参数避免上传。

**F4 file lock + atomic rename**

vault md 写入要防 Obsidian 打开同一文件冲突。用 `flock` 文件锁 + `os.rename` 原子写（写到临时文件再 rename）。

### 修订后任务清单

#### Phase A：核心修复（2-3h，已含原 5 Tasks）

保持原 Tasks 1-5 不变（CalloutBlock + path param + vault 挂载 + 验证）。

#### Phase B：Vault 直读升级（可选 6-9h，Day 2 下午或 Day 3 morning 弹性）

- [ ] Task 6: VaultMonitor daemon 搭建（vault 直读路径）
  - [ ] 6.1: 创建 `deeptutor/services/canvas/vault_monitor.py`（~120 行）
  - [ ] 6.2: 用 `watchdog` 库监听 vault 目录 fs events（macOS FSEvents）
  - [ ] 6.3: debounce 500ms（避免 Obsidian 多次写触发抖动）
  - [ ] 6.4: 文件变化时调 Canvas backend `:8011/api/v1/wikilink/build`（增量）

- [ ] Task 7: DocumentAdder vault_mode 参数注入
  - [ ] 7.1: Edit `deeptutor/services/document_adder.py`（fork 现有代码）
  - [ ] 7.2: 加 `vault_mode: bool = False` 参数
  - [ ] 7.3: `vault_mode=True` 时跳过 upload，仅记录 vault 路径
  - [ ] 7.4: API endpoint 加 `?vault_mode=true` query param

- [ ] Task 8: file lock + atomic rename（vault md 写入安全）
  - [ ] 8.1: 创建 `deeptutor/services/canvas/vault_writer.py`
  - [ ] 8.2: 用 `fcntl.flock(LOCK_EX)` 文件锁
  - [ ] 8.3: 写入 `<filename>.tmp` 然后 `os.rename` 到目标（原子）
  - [ ] 8.4: 写入失败时 cleanup tmp 文件

- [ ] Task 9: Phase B 端到端测试
  - [ ] 9.1: 启动 VaultMonitor daemon
  - [ ] 9.2: 在 Obsidian 编辑 `节点/recursion.md` 加 `[[base-case]]`
  - [ ] 9.3: ≤ 1s 内 Canvas backend 增量更新 wikilink_graph
  - [ ] 9.4: DeepTutor TutorBot ReadFileTool 直接读 vault md（无 upload）
  - [ ] 9.5: TutorBot 写笔记 → vault md 文件更新 → Obsidian 自动 reload

### 推荐路径（Chat vs TutorBot 双轨澄清）

| Canvas 核心 | 推荐 capability | Why |
|---|---|---|
| OriginWhiteboard wikilink 操作 | TutorBot ReadFileTool（沙箱内 vault 读写） | 用户主权（vault 不上传） + 长程伴学 |
| 即时问答（callout 内 wikilink 跳转） | Chat capability（Math Animator 后续叠加） | 瞬时问题，无需会话状态 |

### 修订后估算

- **Phase A only**（保留原 spec）: 2-3h，Day 2 morning 完成 → S1 wikilink 全链路
- **Phase A + Phase B**（推荐）: 1.5-2 day（Day 2 全天 + Day 3 morning），完整 vault 直读 + 主权
- **AC 不变**（保持向后兼容）：原 4 个 AC 仍是验收基准；Phase B 提供"加分项"

### 新增 AC（Phase B 推荐项）

#### AC #5: VaultMonitor 增量更新（Phase B，可选）

- **Given** VaultMonitor daemon 启动 + Obsidian 编辑 vault md 加 wikilink
- **When** 文件保存事件触发
- **Then** ≤ 1s 内 Canvas backend `:8011/api/v1/wikilink/graph` 反映新 wikilink
- **And** DeepTutor frontend 显示新邻居（无需 fork rebuild）

#### AC #6: TutorBot 不上传 vault 文件（Phase B，可选）

- **Given** vault_mode=True 注入 DocumentAdder
- **When** TutorBot 触发"读 vault md"
- **Then** 文件路径用本地 file:// 引用（不进 DeepTutor 内部 upload）
- **And** vault md 修改时间戳不变（read-only 验证）

---

## 下一步

→ Story 10.4 Day 3-4 CanvasVaultAdapter（路径 B：vault → Spine JSON 注入）
