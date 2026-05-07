---
story_id: "10.2"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "done"
priority: "P0"
estimate_hours: 8
depends_on: ["10.1"]
blocks: ["10.3"]
trace: ["FR-DEEP-02", "M9"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 1"
ship_commit: "23a2853"
ship_date: "2026-05-06"
fork_tag: "mvp-day-1-patches"
uat_sheet: "_bmad-output/验收单/Story-10.2-day1-wikilink-frontend.md"
---

# Story 10.2: Day 1 Wikilink Frontend Pipeline

**Status**: ✅ DONE (2026-05-06)

## Story（用户故事）

As a 学习者, I want to write `[[recursion]]` in my notes and see it auto-render as a clickable blue link so that knowledge graph navigation becomes immediate inside DeepTutor — and clicking jumps to the target note, just like Obsidian.

> **映射对**: M9（拆分点 + 批注 + 双链 → Graphiti 推导过程，Round-17 L703）

## 通俗化解释（给学习者）

> **一句话说**: 在 DeepTutor 里写 `[[递归]]` 这种双方括号，会自动变成蓝色链接，点击就跳到"递归"那篇笔记。

**你会遇到的场景**:
- 在 Co-Writer 写笔记时，输入 `[[`
- 期望看到自动补全 / 至少 `[[xxx]]` 渲染成蓝色链接
- 点击链接立即跳转

**这个功能帮你**:
- 不用记每个概念的 URL，写名字就行
- 笔记之间互相关联，知识网络自动形成

**用个比喻**: 🔗 就像维基百科里加方括号自动出现蓝链——但 DeepTutor 的链接还能跨整个 vault 网络。

## Acceptance Criteria

### AC #1: Wikilink 渲染覆盖 9/14 BlockType

- **Given** DeepTutor book 或 Co-Writer 内容含 `[[concept]]`
- **When** 渲染该 markdown
- **Then** `[[concept]]` 转为 `<a class="wikilink" href="/notes/concept" data-target="concept">concept</a>`
- **And** 自动支持的 9 个 block: TextBlock / SectionBlock / QuizBlock / UserNoteBlock / CodeBlock / FigureBlock / InteractiveBlock / AnimationBlock / ConceptGraphBlock
- **And** 5 个不支持的 block 留待 Day 2 修（CalloutBlock, TimelineBlock, FlashCardsBlock, DeepDiveBlock, PlaceholderBlock）

### AC #2: RichMarkdownRenderer 注入 plugin

- **Given** fork 内 `web/components/common/RichMarkdownRenderer.tsx`
- **When** 修改第 624-628 行 remarkPlugins useMemo
- **Then** `[remarkGfm, remarkWikilink]` 双 plugin 注入
- **And** import 行加 `import { remarkWikilink } from "@/lib/wikilink/remark-wikilink-plugin"`
- **And** Next.js build 通过（无 TypeScript 错误）

### AC #3: Backend wikilink_proxy 注册

- **Given** fork backend `deeptutor/api/main.py`
- **When** 在 multi-import block 加 `wikilink_proxy` + 在 include_router 块加 `app.include_router(wikilink_proxy.router, tags=["wikilink"])`
- **Then** `POST :8001/api/v1/wikilink/build` 返回 HTTP 200
- **And** 调用链 fork :8001 → CanvasClient → host.docker.internal:8011 → Canvas backend
- **And** 响应 JSON 含 `{total_nodes, total_edges, build_time_ms}`

### AC #4: 端到端视觉验证（S1 通过）

- **Given** Canvas backend (:8011 healthy) + DeepTutor fork (:3782 + :8001 healthy)
- **When** 用户在 Co-Writer 写 `[[到我了旗舰店]]`
- **Then** Preview 区显示橘红色链接（`<a class="wikilink">`）
- **And** DevTools Elements 显示完整 `<a href="/notes/到我了旗舰店">` 结构
- **And** S1 验证通过（点击 404 是预期，因 `/notes/[slug]` 路由 Day 2 才做）

## Tasks / Subtasks

### Frontend (DeepTutor fork)

- [x] Task 1: Wikilink parser + plugin (AC: #1, #2)
  - [x] 1.1: cp staging `wikilink-parser.ts` → `web/lib/wikilink/parser.ts`
  - [x] 1.2: cp staging `remark-wikilink-plugin.ts` → `web/lib/wikilink/remark-wikilink-plugin.ts`
  - [x] 1.3: 修复 unist-util-visit v5 named export bug：`import { visit, SKIP }` + `return [SKIP, ...]`（不是 `visit.SKIP`）

- [x] Task 2: RichMarkdownRenderer 注入 (AC: #2)
  - [x] 2.1: `Edit web/components/common/RichMarkdownRenderer.tsx` 加 import line
  - [x] 2.2: 修改 line 624-628：`const p: Array<any> = [remarkGfm, remarkWikilink]`
  - [x] 2.3: 验证依赖数组保持 `[plugins.remarkMath]`（不加 remarkWikilink，它是模块级 const）

### Backend (DeepTutor fork)

- [x] Task 3: services/canvas package (AC: #3)
  - [x] 3.1: `mkdir -p deeptutor/services/canvas/`
  - [x] 3.2: cp staging `canvas_client.py` → `deeptutor/services/canvas/client.py`
  - [x] 3.3: 写 `deeptutor/services/canvas/__init__.py` re-export 公共符号

- [x] Task 4: wikilink_proxy router (AC: #3)
  - [x] 4.1: cp staging `wikilink_proxy_router.py` → `deeptutor/api/routers/wikilink_proxy.py`
  - [x] 4.2: 修 import：`from app.clients.canvas_client import` → `from deeptutor.services.canvas import`
  - [x] 4.3: 同 cp staging `exam_proxy_router.py` → `deeptutor/api/routers/exam_proxy.py`（Day 4 用，import 留待 Day 4 修）

- [x] Task 5: main.py register router (AC: #3)
  - [x] 5.1: 在 line 220 alphabetical 位置加 `wikilink_proxy` 到 multi-import block
  - [x] 5.2: 在 line 244 (attachments) 后加 `app.include_router(wikilink_proxy.router, tags=["wikilink"])` （**不**加 prefix，wikilink_proxy 内部已声明）
  - [x] 5.3: 保留 `# Unified WebSocket endpoint` 注释组完整

### Environment + Build

- [x] Task 6: .env 配置 CANVAS_BASE_URL (AC: #3)
  - [x] 6.1: 在 fork 的 `.env` 追加 `CANVAS_BASE_URL=http://host.docker.internal:8011`
  - [x] 6.2: 追加 `CANVAS_TIMEOUT_SECONDS=30`

- [x] Task 7: docker compose rebuild (AC: #4)
  - [x] 7.1: `docker compose up -d --build deeptutor`
  - [x] 7.2: 等待容器 healthy（~5 min incremental cached）
  - [x] 7.3: 验证 `curl -X POST :8001/api/v1/wikilink/build` 返回 200 + JSON

### Verification (S1)

- [x] Task 8: 浏览器视觉验证 (AC: #4)
  - [x] 8.1: 打开 :3782 → Co-Writer
  - [x] 8.2: 写 `[[到我了旗舰店]]`
  - [x] 8.3: Preview 显示橘红 wikilink ✅

- [x] Task 9: 端到端 curl (AC: #3, #4)
  - [x] 9.1: `curl -X POST :8001/api/v1/wikilink/build` HTTP 200
  - [x] 9.2: `docker exec deeptutor curl :8011/api/v1/health` HTTP 200（容器→host 通）

## Dev Notes

### 关键决策
- 用 ReactFlow 替换 Mermaid 是 Day 5 的事（Cytoscape v3.33.1 已装但保留），Day 1 仅做 wikilink **渲染**
- staging 文件 cp 后必须修 import 路径（NEG-2 落地）：staging 默认 `from app.clients.canvas_client`，fork 真实是 `from deeptutor.services.canvas`
- `confirm-spine` API 留待 Day 3-4 用（Agent 2.4 发现，路径 B 核心）

### 已知陷阱（实战捕获）
1. **`visit.SKIP` 不是属性是命名导出**: unist-util-visit v5 必须 `import { visit, SKIP }`，否则 Next.js TS build 失败
2. **MAPPINGS 路径假设错误**: staging 默认 `web/src/lib/...`，fork 实际 `web/lib/...`（无 src 子目录）；backend 默认 `backend/app/`，fork 实际 `deeptutor/`。Day 0 staging 写错了，Day 1 修了 apply-staging-patches.sh 的 MAPPINGS
3. **`docker compose up -d` ≠ reload 源码**: production target 镜像 COPY 源码进 layer，必须 `--build`
4. **`host.docker.internal` 是 Docker Desktop Mac 特殊 DNS**: 容器内访问宿主机服务用这个

### 验收证据（Day 1 完成）
- Commit: `oinani0721/DeepTutor@23a2853`
- Tag: `mvp-day-1-patches`
- 9 files changed, +519 -1 lines
- POST `:8001/api/v1/wikilink/build` → HTTP 200 + `{"data":{"total_nodes":0,"total_edges":0,"build_time_ms":1.5}}`
- 浏览器 Co-Writer 渲染 `[[到我了旗舰店]]` 为橘红 wikilink ✅

### Round-22 引用
- 主报告 §三 Wikilink 在 DeepTutor 实装
- 主报告 §四 Day 1-2: Wikilink 前端 + 后端 bridge
- Deep Explore §3.3 Day 1 修订路线

## UAT 验收

详见 `_bmad-output/验收单/Story-10.2-day1-wikilink-frontend.md`

## References

- fork commit `oinani0721/DeepTutor@23a2853`
- Canvas worktree commit (待 Day 1 worktree-side commit)
- staging files 在 `integration/deeptutor-patches/`

## 下一步

→ Story 10.3 Day 2 Cleanup + Vault Mount（CalloutBlock 1 行修 + path param + vault 数据布线）
