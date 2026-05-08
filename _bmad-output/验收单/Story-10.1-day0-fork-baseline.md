---
story: "10.1"
title: "day0-fork-baseline"
status: "done"
version: "v2.0-double-section"
date: "2026-05-06"
revised: "2026-05-07"
developer: "Claude Code (claude-opus-4-7)"
commit: "deeptutor-fork@9389178 (mvp-baseline tag)"
revision_reason: "5-agent UAT methodology deep explore 收敛后改造为双段结构（DoD-3 D3-A~D3-E）"
---

# Story 10.1 验收单（v2.0 双段重写）

> [!info]+ 这是什么
> Day 0：把 DeepTutor 这个开源项目"复制一份到我自己 GitHub 账号下"，本地能跑起来。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-10/10-1-day0-fork-baseline.md`。
> 本验收单 v2.0 按 DoD-3 双段铁律重写：技术验证全归 🤖 段，你只看 👤 段。

---

## 🎯 这个 Story 要做到什么

把 DeepTutor 复制一份到我的 GitHub 账号下并锁定起点版本，方便后面 10 天改代码。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 拥有一个属于自己的 DeepTutor 副本（fork）并在本地能跑起来，
**以便** 后面 10 天改代码集成 Canvas 五大核心时，原作者改动不会冲突我的工作。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 浏览器在 GitHub 点击 Fork 按钮
       ↓
2. 自己账号下多了一个 DeepTutor 仓库
       ↓
3. (Claude 代你跑 clone + 启动 + 启动 Canvas backend)
       ↓
4. 浏览器打开 localhost 那个网址，看到 DeepTutor 主界面 ✅
```

---

## 🤖 Claude 已代验（你不用跑）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> 出现 `git` / `docker` / `curl` / `port` 等是 Claude 该处理的。你只看右边"结果"列。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | git clone fork repo 到 `~/Desktop/canvas/deeptutor-fork/` | ✅ 9389178 commit 落地 |
| 2 | 创建 `mvp-canvas-integration` 分支 + `mvp-baseline` tag | ✅ tag 锚定起点 |
| 3 | upstream remote 接到 HKUDS/DeepTutor（不会 auto-pull） | ✅ |
| 4 | `docker compose up -d --build` 启动 fork 服务 | ✅ deeptutor 容器 17h healthy |
| 5 | DeepTutor 后端 health endpoint 返回 200 | ✅ `:8001/api/v1/book/health` 200 |
| 6 | DeepTutor 前端 root 路径返回 200 | ✅ `:3782/` 200 |
| 7 | Canvas worktree backend port 让出（FASTAPI_PORT=8011） | ✅ 不和 fork :8001 冲突 |
| 8 | CORS_ORIGINS 加 fork 端口（:3782 / :8001 / :5173） | ✅ 跨域允许 |
| 9 | Canvas backend 启动并 health 200 | ✅ `:8011/api/v1/health` 200 |
| 10 | Neo4j Bolt 端口（:7691）healthy | ✅ Up 37h |

---

## 👤 你来验（产品体验 — 2 步，2 分钟）

> [!warning]+ 这段你只在浏览器里点击、看屏幕。如果哪一步看到英文报错或白屏，截图给 Claude。

### 第 0 步：First 5 seconds（DeepTutor 主界面打开）

- [ ] 我浏览器打开 `http://localhost:3782`，5 秒内看到 DeepTutor 主界面（不是 502 / 不是 connection refused / 不是空白）
- [ ] 第一印象，这看起来是 (a) 严肃学习工具 (b) 还在调试的玩具 (c) 看不出来 — 选: ___
- [ ] 我**感觉**信任这个产品打开速度（不是慢得想关掉）

### 第 1 步：界面元素是熟悉的

- [ ] 我看到主界面有 **Sidebar / Chat / Books** 这几个明显的入口（不是只有空白页）
- [ ] 我**感觉**这是一个学习工具应有的样子（chat + 书 + 笔记是常见组合，符合预期）
- [ ] 中文 UI 元素显示正常（如有），不乱码

### 主观打分（Felt-sense）

- [ ] **流畅度**（1=卡顿到想关 / 5=如丝般顺滑）：___
- [ ] **第一印象**（1=不像专业产品 / 5=像专业学习工具）：___
- [ ] **明天我还会再打开它的可能性**（0-10）：___

---

## 🚦 验收结果

✅ **Day 0 已收官**（fork + baseline + 双服务 healthy 全 ✅）

**最后状态**:
- Fork URL: https://github.com/oinani0721/DeepTutor
- 本地路径: ~/Desktop/canvas/deeptutor-fork/
- baseline tag: mvp-baseline @ 9389178
- 双服务: Canvas :8011 + DeepTutor :8001 + UI :3782 全 healthy

---

## 📝 你的批注区

> [!info]+ v1.0 → v2.0 修复记录（2026-05-07 双段重写）
> **原批注**：用户 2026-05-07 反馈"UAT 只验产品体验，技术验证 Claude 代验"
> **根因**：v1.0 让用户跑 git clone / docker compose / curl / .env 改 port — 100% 是开发任务
> **已修复**：第 0-2 步（fork 操作）+ 第 3-6 步（git/docker/CORS/port）全部移到 🤖 Claude 已代验段；用户段只剩"浏览器打开 + 看主界面"

> [!question]+ 你对 Story 10.1 的批注
>
> （v1.0 已通过，v2.0 是结构重写。如果你跑 👤 段 2 步还有疑问，写在这里）

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **Story spec**: `_bmad-output/implementation-artifacts/epic-10/10-1-day0-fork-baseline.md`
- **Round 决策**: Round-22 §八立即行动清单
- **fork 仓库**: https://github.com/oinani0721/DeepTutor
- **fork commit**: `9389178` (mvp-baseline tag)
- **双服务命令**: `./integration/scripts/start-integration.sh`

---

## 下一步

→ Story 10.2 Day 1 Wikilink Frontend Pipeline（已 ✅ done v2.0 双段）
