# CURRENT_TASK: DeepTutor Fork MVP 集成（Round-22）

> **前 15 行是 Clear Context 后的恢复锚点 — 必须自包含**

**当前状态**：
- Day 1 ✅ wikilink 集成完整收官（fork `23a2853` + tag `mvp-day-1-patches`）
- Day 2 ✅ Story 10.3 Phase A ship（CalloutBlock + vault mount + client.py path param，commit `2fe058d`）
- **Day 3 ✅ Story 10.4 Phase A 端到端 ship**（2026-05-07）：adapter 6 文件 + dry-run + Pydantic 验证 + cli endpoint prefix 修复（`/api/v1/book`）+ POST 创建 book `bk_a87d2cdff1` + confirm-spine 注入 5 chapters + LLM cost = $0（fork ideation fallback 到 stub）+ 验收单 v0.2-phase-a 重写为"Claude 代验/用户验"双段结构

**下一步**（用户只看产品体验，3 步）：
1. `open http://localhost:3782` — 看 fork UI 打开 + 中文不乱码
2. Books 列表找到 `bk_a87d2cdff1`（title 可能是 "Untitled Book"）→ 点进去
3. 看到 5 chapter 列表（本书导览 / 特征值 / 线性代数 / CS 61B / 递归）→ 点不报错

通过 → Claude commit worktree + fork repo + 启 Day 4 Phase B（CalloutAnnotationParser P1 + 真实 insert-block 注入）
不通过 → 截图给 Claude → correct-course

**关键路径**：
- 本 worktree：`~/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-deeptutor-canvas-mvp/`
- DeepTutor fork：`~/Desktop/canvas/deeptutor-fork/`（adapter 在 `adapter/`）
- Round-22 决策报告：`_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
- 最新决策批注：`_bmad-output/决策批注/D19-desktop-db-stack-2026-05-07.md`

**端口约定**：Canvas :8011 / DeepTutor :8001 / Neo4j Bolt :7691 / DeepTutor UI :3782

**一键启动**：`./integration/scripts/start-integration.sh --canvas-only`（仅 Canvas）或 `./integration/scripts/start-integration.sh`（双服务）

---

## Round-22 用户决策（2026-05-06）

> "我是想要舍弃 obsidian，直接把我们 Canvas learning systeam 思想在 deeptutor 实现，我的批注有列出来哪些 deeptutor 和我们 Canvas learning systeam 的思想和功能相对应，缺少功能我们就参考我们的 Canvas learning systeam 的源码集成。**我先试一下集成的效果先**"

**核心**：
- ⛔ Fork DeepTutor + 嵌入 Canvas 5 大核心
- ⛔ 舍弃 Obsidian
- ⛔ MVP 验证（不是 production）
- ⛔ 工程量：10 天

## 已完成（Day 0）

- [x] Canvas worktree `feature-deeptutor-canvas-mvp` 创建（基于 `worktree-feature-obsidian-hybrid-dev`）
- [x] Canvas backend 端口 8011（让出 8001 给 DeepTutor）
  - `.env` API_PORT=8011
  - `backend/.env` FASTAPI_PORT=8011
  - `backend/.env.example` FASTAPI_PORT=8011
- [x] CORS 加 DeepTutor 端口（:3782, :8001）
- [x] Staging 文件 cp 到 `integration/deeptutor-patches/`
  - backend/{canvas_client,wikilink_proxy_router,exam_proxy_router}.py
  - frontend/{wikilink-parser,remark-wikilink-plugin}.ts
  - frontend/BLOCK_TYPE_PATCH.md
  - docker/docker-compose.canvas.yml
- [x] 3 个 shell 脚本就位：
  - `integration/scripts/start-integration.sh`
  - `integration/scripts/health-check.sh`
  - `integration/scripts/apply-staging-patches.sh`
- [x] Round-22 决策报告：`_bmad-output/research/round-22-deeptutor-fork-mvp-2026-05-06.md`
- [x] Memory 决策：`decision_round22_fork_mvp.md`

## 用户必须自己做（GitHub 操作）

```bash
# 1. 浏览器 fork
open https://github.com/HKUDS/DeepTutor

# 2. clone 到 deeptutor-fork（不是 .references！.references 保留参考）
cd ~/Desktop/canvas
git clone https://github.com/oinani0721/DeepTutor.git deeptutor-fork
cd deeptutor-fork
git checkout -b mvp-canvas-integration
git tag mvp-baseline
git remote add upstream https://github.com/HKUDS/DeepTutor.git

# 3. baseline smoke test（不改代码）
docker compose up -d
curl http://localhost:8001/api/v1/health  # 期望 200
open http://localhost:3782                  # 期望看到 DeepTutor UI
```

## Day 1 路线（用户 fork 完成后立即开始）

| 步 | 内容 | 工具 |
|---|---|---|
| 1 | cp staging frontend → fork | `./integration/scripts/apply-staging-patches.sh --dry-run` 然后真应用 |
| 2 | 改 fork web/components/common/RichMarkdownRenderer.tsx:624-628 注入 remarkWikilink | 手动 Edit |
| 3 | 验证 `[[recursion]]` 渲染（浏览器 :3782） | DevTools 看 `<a class="wikilink">` |
| 4 | cp staging backend → fork | apply-staging-patches.sh |
| 5 | 注册 wikilink_proxy router 到 fork main.py | 手动 Edit |
| 6 | curl `:8001/api/v1/wikilink/build` 端到端 | 验证 DeepTutor → Canvas HTTP 链路 |

## 5 个验证场景（Day 10 全过 = MVP 成功）

| # | 场景 | Pass 标准 |
|---|---|---|
| **S1** | DeepTutor 写 `[[recursion]]` → 自动跳转 | < 1s |
| **S2** | 右键 callout → Canvas ACP 出题 | DeepTutor quiz 块渲染 |
| **S3** | 答题 → mastery 更新 → UI 显示 | mastery.value 改变 |
| **S4** | Graph View tab 显示节点 + 边 | ≥ 10 节点 |
| **S5** | 答错 → Day 0/3/7 推送 console | `[REVIEW DUE] T+0/3/7` |

## 风险红线

🚫 不 `git pull upstream`（DeepTutor 30 天 24 release）
🚫 不跑 DeepTutor 完整测试（Enum patch 会破坏部分单测）
🚫 vault md 单一源（DeepTutor 只 read-only mount）
🚫 不在本 worktree 跑 Canvas 业务开发

## 退出策略

Day 6 / Day 10 弃集成：`rm -rf ~/Desktop/canvas/deeptutor-fork && git worktree remove .claude/worktrees/feature-deeptutor-canvas-mvp`。Canvas 主线零影响。
