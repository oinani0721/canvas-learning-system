# Phase 1: 启动验证 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Canvas Learning System 在 Windows 上完整启动，验证基本功能可用，修复已知 Bug。

**Architecture:** 纯配置修复 + Bug 修复 + 手动验证。不涉及新功能开发。Docker Compose 管理 3 个服务（Neo4j + Ollama + FastAPI），Tauri+React 前端通过 `npm run tauri dev` 启动。

**Tech Stack:** Docker Compose, Neo4j 5.26, Ollama (bge-m3), FastAPI, Tauri 2, React 19, TypeScript

**Review Checklist Reference:** `docs/superpowers/specs/2026-03-25-review-checklist.md` — Phase 1 相关条目

---

## File Structure

| 操作 | 文件 | 职责 |
|------|------|------|
| Modify | `backend/.env` | Neo4j 端口修复 7688→7691 |
| Modify | `backend/.env.example` | 同步 .env 模板 |
| Modify | `frontend/src-tauri/tauri.conf.json` | CSP 开发配置 |
| Delete | `frontend/src/components/exam/CognitiveLoadTimer.tsx` | 移除已抛弃的计时组件 |
| Modify | `frontend/src/components/exam/ExamCanvas.tsx` | 移除 CognitiveLoadTimer import 和渲染 |
| Modify | `frontend/src/components/exam/ExamSummary.tsx` | 移除总用时显示 |
| Verify+Fix | `frontend/src/services/` 中评分相关文件 | 验证并修复 ×2.5 溢出 Bug |
| Verify+Fix | `backend/app/services/agent_service.py` | 验证并修复 score×100 Bug |

---

### Task 1: 环境配置修复

**Files:**
- Modify: `backend/.env` (NEO4J_URI 行)
- Modify: `backend/.env.example` (NEO4J_URI 行)

- [ ] **Step 1: 修改 backend/.env**

将 `NEO4J_URI=bolt://localhost:7688` 改为 `NEO4J_URI=bolt://localhost:7691`

- [ ] **Step 2: 同步 backend/.env.example**

将 `NEO4J_URI=bolt://localhost:7688` 改为 `NEO4J_URI=bolt://localhost:7691`

- [ ] **Step 3: 验证 CSP 配置**

读取 `frontend/src-tauri/tauri.conf.json`，确认 `security.csp` 字段。如果不是 `null`，改为 `null`（开发阶段不限制）。

User："C:\Users\Heishing\Pictures\Screenshots\屏幕截图 2026-03-26 074640.png" start exam 测试失败，完全不符合我们的预期使用模式；/命令也是没有一个注册成功的；然后检验白板下也没有返回dashboard 的按钮了
User2：  问题 2: Start Exam 不符合预期

  从截图看，考试确实启动了（顶栏显示 EXAM Mixed / 2 examined / Hint 0/4 / Skip / End Exam），但显示的是旧的对话历史（3月24日的 A* 搜索内容）。

  这说明：
  - ExamCanvas + ChatPanel 加载正常 ✅
  - 但对话内容来自 Dexie 缓存的旧 session，不是新考察 ✅ → 需要 Phase 3 打通 sidecar → MCP generate_question 管道
（那么我现在是否需要进行继续测试 检验白板的相关功能）
User3：  │ Exam History（考试历史） │ 你之前做过的所有检验白板考察记录             │
  ├──────────────────────────┼──────────────────────────────────────────────┤
  │ Review（复习）           │ 根据遗忘曲线提醒你该复习哪些知识点           │
（"C:\Users\Heishing\Pictures\Screenshots\屏幕截图 2026-03-26 075928.png"，"C:\Users\Heishing\Pictures\Screenshots\屏幕截图 2026-03-26 075954.png"；这两个功能完全没有打通，这里都是假的实现）
User4："C:\Users\Heishing\Pictures\Screenshots\屏幕截图 2026-03-26 080422.png" 这里标记tips 只能看到文本高亮，点击完全看不到tips 的详细内容； 原白板创建/连线 暂时没有看到问题；拉出节点 正常也是可以拉出来；

- [ ] **Step 4: Commit**

```bash
git add backend/.env backend/.env.example frontend/src-tauri/tauri.conf.json
git commit -m "fix: Neo4j port 7688→7691 (docker container) + CSP dev config"
```

**验收（review-checklist 二级）**:
- [ ] .env.example NEO4J_URI 已更新为 7691
- [ ] CSP 配置 = null（开发阶段）

---

### Task 2: Docker 服务启动验证

**Files:** 无代码修改（纯验证）

- [ ] **Step 1: 启动 Docker 服务**

```bash
cd /c/Users/Heishing/Desktop/canvas/canvas-learning-system
docker-compose up -d
```

等待 ~90 秒，直到所有服务 healthy。

- [ ] **Step 2: 检查服务状态**

```bash
docker-compose ps
```

Expected: 3 个容器全部 `healthy`:
- `canvas-learning-system-neo4j` — healthy
- `canvas-learning-system-ollama` — healthy
- `canvas-learning-system-backend` — healthy

- [ ] **Step 3: 拉取 Ollama 模型（首次）**

```bash
docker exec canvas-learning-system-ollama ollama pull bge-m3
```

Expected: 模型下载完成（~1.3GB，首次需要几分钟）

- [ ] **Step 4: 验证后端健康**

```bash
curl http://localhost:8001/api/v1/health
```

Expected: 返回 200 + JSON（含 neo4j/lancedb/ollama 组件状态）

- [ ] **Step 5: 验证 Neo4j 连接**

```bash
curl -u neo4j:cs188study http://localhost:7478/
```

Expected: Neo4j Browser 页面（HTTP 200）

- [ ] **Step 6: 验证 Ollama bge-m3 已加载**

```bash
curl http://localhost:11434/api/tags
```

Expected: JSON 中包含 `bge-m3` 模型

---

### Task 3: 移除 CognitiveLoadTimer（决策 GDA-5）

**Files:**
- Delete: `frontend/src/components/exam/CognitiveLoadTimer.tsx`
- Modify: `frontend/src/components/exam/ExamCanvas.tsx:37,249`
- Modify: `frontend/src/components/exam/ExamSummary.tsx`

- [ ] **Step 1: 读取 ExamCanvas.tsx 确认 import 位置**

读取 `frontend/src/components/exam/ExamCanvas.tsx`，找到 import 行（约 line 37）和渲染行（约 line 249）。

- [ ] **Step 2: 移除 ExamCanvas.tsx 中的 CognitiveLoadTimer**

删除 import 行:
```typescript
import { CognitiveLoadTimer } from './CognitiveLoadTimer';
```

删除渲染行:
```typescript
{startTime && <CognitiveLoadTimer startTime={startTime} />}
```

- [ ] **Step 3: 读取 ExamSummary.tsx 确认 elapsedTime 相关代码**

读取 `frontend/src/components/exam/ExamSummary.tsx`，找到 `elapsedTime`/`computeElapsedTime` 相关代码。

- [ ] **Step 4: 移除 ExamSummary.tsx 中的总用时显示**

移除 `computeElapsedTime` 函数和所有引用 `elapsedTime` 的 JSX 渲染代码。保留其他统计（examined nodes、average score、hints used）。

- [ ] **Step 5: 删除 CognitiveLoadTimer.tsx 文件**

```bash
rm frontend/src/components/exam/CognitiveLoadTimer.tsx
```

- [ ] **Step 6: 验证 TypeScript 编译**

```bash
cd frontend && npx tsc --noEmit
```

Expected: 无错误（CognitiveLoadTimer 的所有引用已清理）

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: remove CognitiveLoadTimer (decision GDA-5, timing feature abandoned)"
```

---

### Task 4: 评分 Bug 验证与修复（决策 GDA-8）

**Files:**
- Verify+Fix: 前端评分显示文件（搜索 `* 2.5` 或 score 乘法逻辑）
- Verify+Fix: `backend/app/services/agent_service.py`（搜索 `* 100` 或 score 归一化逻辑）

- [ ] **Step 1: 搜索前端评分 ×2.5 Bug**

```bash
cd frontend/src
grep -rn "2\.5\|score.*\*\|multiply" --include="*.ts" --include="*.tsx" | grep -i "score\|point\|grade"
```

如果找到 `score * 2.5` 或类似乘法 → 进入 Step 2 修复。如果未找到（可能已在 S18 BMAD 审查中修复）→ 记录"Bug 1 已修复"跳到 Step 3。

- [ ] **Step 2: 修复前端 ×2.5 Bug（如果存在）**

移除旧的 40 分制 → 100 分制转换逻辑。AutoSCORE 返回 0-12 分（4维×3分），前端应直接显示此分数，不做缩放。

- [ ] **Step 3: 搜索后端 score×100 Bug**

```bash
grep -n "score.*\* 100\|score.*100\|<= 1\.0.*100" backend/app/services/agent_service.py
```

如果找到将 ≤1.0 分数乘 100 的逻辑 → 进入 Step 4 修复。如果未找到 → 记录"Bug 2 已修复"。

- [ ] **Step 4: 修复后端 score×100 Bug（如果存在）**

移除 `if score <= 1.0: score = score * 100` 逻辑。AutoSCORE 4D 返回的是 0-12 绝对分数。

- [ ] **Step 5: Commit（如有修改）**

```bash
git add -A
git commit -m "fix: scoring display bugs - remove legacy scale conversion (decision GDA-8)"
```

---

### Task 5: 前端启动验证

**Files:** 无代码修改（纯验证）

- [ ] **Step 1: 安装前端依赖**

```bash
cd frontend && npm install
```

- [ ] **Step 2: 启动 Tauri 开发服务器**

```bash
npm run tauri dev
```

Expected: Tauri 窗口打开，React 应用加载无白屏。

- [ ] **Step 3: 验证 #1 原白板**

操作: 创建白板 → 添加 3 个节点 → 连线
Expected: 节点/边在画布可见，刷新后仍在

- [ ] **Step 4: 验证 #2 检验白板**

操作: 选白板 → Generate Exam → 选模式
Expected: ExamCanvas 打开，ChatPanel 显示

- [ ] **Step 5: 验证 #2+ 检验白板 Tips**

操作: 在考察对话中选中文本 → 打 Tip 标注
Expected: InlineAnnotation 浮窗出现，Tips 保存成功

- [ ] **Step 6: 验证 #7 Dashboard**

操作: 切换到 Dashboard 视图
Expected: 三个选项卡（白板/考试/复习）可见

- [ ] **Step 7: 验证 #4 节点对话**

操作: 右键节点 → Chat
Expected: ChatPanel 打开，能输入消息（sidecar 或 fallback）

- [ ] **Step 8: 验证 #13 /命令**

操作: 在 ChatPanel 输入 `/`
Expected: SkillSelector 浮窗弹出

- [ ] **Step 9: 验证 #14 拉出节点**

操作: 在 ChatPanel 选中文本
Expected: SelectionToolbar 出现

- [ ] **Step 10: 记录验证结果**

将每项验证结果（通过/失败/问题描述）记录到设计文档的验证清单中。发现的小问题（<50 行）直接修复并 commit。

---

### Task 6: Phase 1 完成确认

- [ ] **Step 1: 运行最终验证**

确认所有 Phase 1 验收标志：
```
□ docker-compose ps → 3 服务 healthy
□ curl /api/v1/health → 200
□ CSP 配置不阻塞前端加载
□ Tauri 窗口打开无崩溃
□ 能创建白板 + 添加节点 + 连线
□ CognitiveLoadTimer 已移除
□ 评分 Bug 已验证/修复
□ 检验白板中能打 Tips
```

- [ ] **Step 2: 最终 Commit + Push**

```bash
git add -A
git commit -m "milestone: Phase 1 startup validation complete"
```

Post-commit hook 自动 push 到 backup 远程。
