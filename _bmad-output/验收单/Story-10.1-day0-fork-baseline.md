---
story: "10.1"
title: "day0-fork-baseline"
status: "done"
version: "v1.0"
date: "2026-05-06"
developer: "Claude Code (claude-opus-4-7)"
commit: "23a2853 (fork) + worktree-side pending"
---

# Story 10.1 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 10.1 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-10/10-1-day0-fork-baseline.md`（Claude 读的）。

---

## 🎯 这个 Story 要做到什么

把 DeepTutor 这个开源项目"复制一份到我自己 GitHub 账号下"，并锁定起点版本，方便后面 10 天改代码不怕原作者更新。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 拥有一个属于自己的 DeepTutor 副本（fork），并在本地能跑起来，
**以便** 后面 10 天改代码集成 Canvas 五大核心时，原作者改动不会冲突我的工作。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 浏览器打开 GitHub DeepTutor 项目页
       ↓
2. 点击右上角 "Fork" 按钮
       ↓
3. 看到自己账号下多了 oinani0721/DeepTutor 仓库
       ↓
4. 终端 git clone 把它下载到电脑
       ↓
5. 终端 docker compose up -d 启动
       ↓
6. 浏览器打开 :3782 看到 DeepTutor UI ✅
```

---

## ✅ 验收清单（5 步 UAT — 你一步步跑，勾掉每一项）

> [!tip]+ 怎么用这份清单
> 每跑完一步，**点击对应的 `- [ ]` 切换为 `[x]`**（Obsidian 原生支持）。
> 发现不对劲 → **选中那一行 → `Cmd+Shift+A` → 批注问题**。

### 第 0 步：前置（必须做）

- [x] 已经登录 GitHub 账号 oinani0721
- [x] Docker Desktop 已安装在 /Applications/Docker.app
- [x] 终端能跑 git 命令（`git --version` 显示 2.x+）

### 第 1 步：GitHub Fork（你浏览器操作）

- [x] 浏览器打开 https://github.com/HKUDS/DeepTutor
- [x] 看到右上角的 "Fork" 按钮（按钮上有数字 3.1k）
- [x] 点 Fork → 选自己的 oinani0721 账号
- [x] 等 5-10 秒 → 跳到 https://github.com/oinani0721/DeepTutor
- [x] 看到标题显示 "oinani0721/DeepTutor" + 副标题 "forked from HKUDS/DeepTutor"

### 第 2 步：本地 clone

- [x] 终端 `cd ~/Desktop/canvas`
- [x] `git clone https://github.com/oinani0721/DeepTutor.git deeptutor-fork`
- [x] 看到 "Cloning into 'deeptutor-fork'..." 然后完成
- [x] `cd deeptutor-fork && ls` 看到一堆文件（README.md, deeptutor/, web/, docker-compose.yml...）

### 第 3 步：分支 + tag

- [x] `git checkout -b mvp-canvas-integration`（创建 + 切换到新分支）
- [x] `git tag mvp-baseline`（打 tag 锚定起点 commit 9389178）
- [x] `git remote add upstream https://github.com/HKUDS/DeepTutor.git`
- [x] `git tag -l` 看到 `mvp-baseline`

### 第 4 步：启动 Docker

- [x] `open -a Docker`（macOS 启动 Docker Desktop）
- [x] 等 30-60 秒看菜单栏 Docker 鲸鱼图标变实心
- [x] `docker info` 不报错（daemon 已 ready）
- [x] `cp .env.example .env`（占位 LLM key 即可）
- [x] `docker compose up -d --build`（首次 build ~10 min）
- [x] `docker ps` 看到 deeptutor 容器 healthy

### 第 5 步：浏览器验证

- [x] `curl :8001/` 返回 200（DeepTutor 后端 API 通）
- [x] `open http://localhost:3782` 浏览器打开 UI
- [x] 看到 DeepTutor 主界面（左侧 Sidebar + Chat / Books 标签）

### 第 6 步：Canvas 端口让出

- [x] Canvas worktree `backend/.env` 改 `FASTAPI_PORT=8011`（让出 :8001 给 DeepTutor）
- [x] CORS_ORIGINS 加 `:3782 :8001 :5173`
- [x] `cd canvas-worktree && ./integration/scripts/start-integration.sh --canvas-only` 启动 Canvas 在 :8011
- [x] `curl :8011/api/v1/health` 返回 200

---

## 🚦 验收结果

✅ **全部通过**（Day 0 完整收官）

- Fork URL: https://github.com/oinani0721/DeepTutor
- 本地路径: ~/Desktop/canvas/deeptutor-fork/
- baseline tag: mvp-baseline @ 9389178
- 双服务: Canvas :8011 + DeepTutor :8001 + UI :3782 全 healthy

---

## 📝 你的批注区

> [!question]+ 你对 Story 10.1 的批注
>
> 在这里写任何疑问/建议/不满意。或者用 `Cmd+Shift+A` 批注上面任何段落。

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**: `_bmad-output/implementation-artifacts/epic-10/10-1-day0-fork-baseline.md`
- **Round 决策**: Round-22 §八立即行动清单
- **fork 仓库**: https://github.com/oinani0721/DeepTutor
- **Canvas worktree commit**: 待 worktree-side commit

---

## 下一步

→ Story 10.2 Day 1 Wikilink Frontend Pipeline（已 ✅ done）
