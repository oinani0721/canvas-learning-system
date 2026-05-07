---
story_id: "10.1"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "done"
priority: "P0"
estimate_hours: 2
depends_on: []
blocks: ["10.2"]
trace: ["FR-DEEP-01"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 0"
ship_commit: "23a2853"
ship_date: "2026-05-06"
fork_baseline_commit: "9389178"
fork_baseline_tag: "mvp-baseline"
uat_sheet: "_bmad-output/验收单/Story-10.1-day0-fork-baseline.md"
---

# Story 10.1: Day 0 Fork & Baseline

**Status**: ✅ DONE (2026-05-06)

## Story（用户故事）

As a developer, I want to fork DeepTutor to a known baseline so that all team members work from a stable starting point with no breaking changes mid-MVP.

> **Round 来源**: Round-22 主报告 §八 立即行动清单（用户必须自己做的 GitHub 操作）

## 通俗化解释（给学习者）

> **一句话说**: 把 DeepTutor 这个开源项目"复制一份到我自己 GitHub 账号下"，并锁定起点版本，方便后面 10 天改代码不怕原作者更新。

**你会遇到的场景**:
- 在浏览器打开 GitHub 上 DeepTutor 项目页
- 点击 "Fork" 按钮把它复制到你的账号
- 在终端用 `git clone` 把这份复制下载到电脑

**这个功能帮你**:
- 拥有完全控制权（自己改代码不影响原作者）
- 锁定版本（30 天内 DeepTutor 上游会发 24 个新版本，我们不跟）

**用个比喻**: 📚 就像图书馆借了一本书，你拿回家在书边写笔记——你的笔记不会影响图书馆原书，将来还书或者复印自己的版本都行。

## Acceptance Criteria

### AC #1: GitHub fork 完成

- **Given** 用户已登录 GitHub 账号 oinani0721
- **When** 浏览器访问 https://github.com/HKUDS/DeepTutor 并点击 Fork
- **Then** fork 仓库创建在 https://github.com/oinani0721/DeepTutor
- **And** clone 到 ~/Desktop/canvas/deeptutor-fork/

### AC #2: Baseline 标记

- **Given** fork 仓库已 clone 到本地
- **When** 在 deeptutor-fork 目录执行 git checkout + tag
- **Then** 创建分支 `mvp-canvas-integration`
- **And** tag commit `9389178` 为 `mvp-baseline`
- **And** `git tag -l | grep mvp-baseline` 返回 mvp-baseline

### AC #3: Baseline 烟雾测试

- **Given** Docker Desktop 已启动 + daemon ready
- **When** 在 fork 目录执行 `docker compose up -d`
- **Then** 容器 `deeptutor` 启动并 healthy（< 2 min）
- **And** `curl http://localhost:8001/` 返回 HTTP 200
- **And** 浏览器 :3782 显示 DeepTutor UI

### AC #4: Canvas worktree 端口迁移

- **Given** Canvas 原本用 :8001（与 DeepTutor 冲突）
- **When** 修改 backend/.env + .env.example 的 FASTAPI_PORT 为 8011
- **Then** Canvas backend 跑在 :8011
- **And** CORS_ORIGINS 加入 :3782 :8001 :5173 让 fork 能访问

## Tasks / Subtasks

- [x] Task 1: 用户 GitHub fork 操作 (AC: #1)
  - [x] 1.1: 浏览器打开 https://github.com/HKUDS/DeepTutor
  - [x] 1.2: 点击右上角 Fork 按钮 → 选择 oinani0721 账号
  - [x] 1.3: 验证 fork 完成（标题显示 oinani0721/DeepTutor）

- [x] Task 2: 本地 clone + 分支 + tag (AC: #2)
  - [x] 2.1: `cd ~/Desktop/canvas`
  - [x] 2.2: `git clone https://github.com/oinani0721/DeepTutor.git deeptutor-fork`
  - [x] 2.3: `cd deeptutor-fork && git checkout -b mvp-canvas-integration`
  - [x] 2.4: `git tag mvp-baseline`
  - [x] 2.5: `git remote add upstream https://github.com/HKUDS/DeepTutor.git`

- [x] Task 3: Baseline smoke test (AC: #3)
  - [x] 3.1: 启动 Docker Desktop（macOS `open -a Docker`）
  - [x] 3.2: `cp .env.example .env`（占位 LLM_API_KEY 即可，MVP 不调 LLM）
  - [x] 3.3: `docker compose up -d --build`（首次 ~10 min build）
  - [x] 3.4: 验证 `curl :8001/` HTTP 200
  - [x] 3.5: 验证 `:3782` 浏览器可见

- [x] Task 4: Canvas 端口迁移 (AC: #4)
  - [x] 4.1: 修改 `backend/.env` `FASTAPI_PORT=8011`
  - [x] 4.2: 修改 `backend/.env.example` 同步
  - [x] 4.3: 加 `:3782 :8001 :5173 :tauri.localhost` 到 CORS_ORIGINS

## Dev Notes

### 关键决策
- 用户必须**自己** 在 GitHub 点 Fork（Claude 不能代登录账号）
- Tag `mvp-baseline` 锚定起点，方便 Day 10 回滚或对比
- Canvas 端口让出 8001 给 DeepTutor → Canvas 改用 8011（Round-22 §八 已确定）

### 已知陷阱（实践捕获）
- DeepTutor `target: production` 镜像 = 源码 COPY 进去，**改代码必须 rebuild**（Day 1 才发现）
- `host.docker.internal:8011` 是 Docker Desktop for Mac 特殊 DNS（Day 1 用到）
- `.env` 在 `.gitignore` 双重防护（`.env` + `*.env`），sk-xxx placeholder 不会泄漏

### 风险红线（NEG-3）
- **MVP 期间禁止 `git pull upstream`** — DeepTutor 30 天 24 release 节奏会冲撞 staging

### 验收证据（Day 0 完成）
- Fork URL: https://github.com/oinani0721/DeepTutor
- Baseline commit: 9389178
- Local path: `~/Desktop/canvas/deeptutor-fork/`
- branch: `mvp-canvas-integration`
- tag: `mvp-baseline` (Day 0) + `mvp-day-1-patches` (Day 1, commit 23a2853)

## UAT 验收

详见 `_bmad-output/验收单/Story-10.1-day0-fork-baseline.md`（非技术用户操作版）

## References

- Round-22 主报告 §八立即行动清单
- Round-22 主报告 §四 Day 0 准备
- CURRENT_TASK.md 前 15 行恢复锚点
- decision_round22_fork_mvp.md (memory)

## 下一步

→ Story 10.2 Day 1 Wikilink Frontend Pipeline
