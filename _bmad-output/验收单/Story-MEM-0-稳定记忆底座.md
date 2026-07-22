---
story_id: MEM-0
title: "稳定记忆底座（批次 0：先别丢数据）"
plan: MEM-FLYWHEEL-2026-07-22
date: 2026-07-22
status: ready-for-uat
---

# Story MEM-0 · 稳定记忆底座 — 验收单

## 1. 🎯 一句话目标

让你的学习记忆「**不丢、有备胎、坏了一眼能看出来**」——从今天起，电脑重启后记忆系统自己活过来，图谱每天自动备份，任何一环坏了都有一行人话提示。

## 2. 📖 你的视角

作为一个每天用白板拆分和检验白板学习的人，我想要我的批注、会话、错误记录**永远不会因为「某个程序没开」而悄悄丢失**，以便我可以放心积累，让考察越老越准。

## 3. 🖥️ 交互流程

```
你正常学习（批注 / 派生 / 结束会话）
        ↓
什么都不用做 —— 后台自动：
  · 凌晨 4:30 图谱自动备份（保留最近 7 天）
  · 早上 9:00 写一行健康摘要（五个 ✅/❌ 一眼看全）
  · 学习会话结束时若记忆系统没开机 → 自动存入待发盒子，下次开机自动补交
        ↓
你想确认时：打开 backups 文件夹看两个文件（见 4-B）
```

## 4-A. 🤖 Claude 已代验（全部带证据，2026-07-22 11:50-11:59 实测）

| # | 验证项 | 结果 | 证据 |
|---|---|---|---|
| 1 | 两个本地模型进程已拉起且开机自启配置就位 | ✅ | 12341/18012 实测 UP；两个 LaunchAgent plist 已放入 `~/Library/LaunchAgents/`（下次登录自动生效） |
| 2 | Docker 已加入系统登录项（自启双保险） | ✅ | 登录项列表实测含 "Docker" |
| 3 | 首份图谱备份真实产出 | ✅ | `backups/neo4j/neo4j-20260722-115326.dump`（3.8MB）+ system 库同备；备份后数据库自动重启恢复 healthy |
| 4 | 每日备份/健康摘要定时任务就位 | ✅ | 4:30 备份 + 9:00 摘要两个 plist 就位；首行摘要已落盘全 ✅ |
| 5 | 会话归档待发队列四场景单测 | ✅ | 入队+幂等 / 失败保留计数 / 成功清空 / 超限转 dead 全 PASS |
| 6 | 停机崩溃 bug 修复（3.13-only API 兼容层） | ✅ | 旧进程停机日志抓到 AttributeError 现行；修复后新进程正常启动（"Worker loop started"）；瞬态错误仍重试、确定性错误直接死信留证均单测 PASS |
| 7 | 后端启动健康自检上线 | ✅ | 模型进程不可达时启动日志会打出「⚠️ 语义抽取 LLM 不可达 — 修复: 运行 xxx」人话告警 |
| 8 | 关联单元测试 | ✅ | belief/writer/recovery 套件 37 passed（4 个失败为存量失败，stash 验证与本次改动无关） |
| 9 | 全栈健康摘要 | ✅ | `Neo4j:✅ 后端:✅ Qwen:✅ Rerank:✅ Embed:✅` |

## 4-B. 👤 你来验（约 2 分钟，全部在 Finder / Obsidian 里）

- [ ] 我打开 Finder，进入 `canvas-learning-system` 里的 `backups` 文件夹 → 我看到一个 `neo4j` 文件夹，里面有今天日期的备份文件 → 我感觉我的学习图谱终于有了备胎，安心了
- [ ] 我在同一个 `backups` 文件夹里打开 `memory-health.log`（双击用文本编辑打开）→ 我看到今天的一行里五个项目全是 ✅ → 我感觉系统状态从黑盒变成一眼可查
- [ ] （可选，想做就做）我重启电脑，等两三分钟，再打开这个 `memory-health.log` 看新的一行 → 如果还是全 ✅ → 我感觉「重启后什么都不用手动开」是真的

## 5. 🚦 验收结果

- **全部勾上** → 在批注区写「MEM-0 通过」，我立即开工批次 1（越老越准的数学地基）
- **有任何一条不对** → 用 `Cmd+Shift+A` 在批注区写 ❌ 错误 + 你看到了什么，我来修

## 6. 📝 批注区（直接写 **User：**）

> [!question]+ 疑问/不满意写这里

## 7. 🔗 技术 spec 引用（给 Claude 读的）

- 计划: `_bmad-output/研究/2026-07-22-下一步开发计划-稳定记忆与越老越准.md` §3 批次 0
- 改动: `backend/app/services/episode_worker.py`（Py<3.13 兼容层 + 永久错误免重试 + 停机哨兵）、`backend/app/graphiti/llm_factory.py::check_local_providers_health`、`backend/app/main.py`（启动自检）、`canvas-vault/.claude/hooks/session-end-archive.py`（待发队列）、`scripts/backup-neo4j.sh`、`scripts/memory-health.sh`
- 自启: `~/Library/LaunchAgents/com.canvas.{qwen-graphiti,reranker-graphiti,neo4j-backup,memory-health}.plist` + Docker 登录项
- 已知限制: LaunchAgent 首次生效需下次登录（本次已手动拉起进程无缝衔接）；Docker Desktop 设置里的 "Start when you sign in" 勾选框如果你顺手也勾上，就是三保险
