---
story: "CARD-C1a"
title: "每日复习管道 vault 命名空间化"
status: "review"
version: "1"
date: "2026-08-25"
developer: "Claude Code (Fable 5)"
commit: "card/l1-crossvault 分支（BATCH-2026-08-25-跨vault与收束 / CARD-C1a）"
---

# CARD-C1a 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 CARD-C1a「每日复习管道 vault 命名空间化」的用户验收文档，**给你（非技术）读的版本**。
> 技术档案在 `_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md` 的 CARD-C1a 节（Claude 读的）。

---

## 🎯 这个卡要做到什么

现在的每日复习管道是"全局单例"：推送状态、防重复锁、手机通知的去重编号全共用一份。今天只有一个学科库没事，但将来开第二个库（比如数学库）时会互相覆盖——**一个库早上推送过，另一个库当天就永远不推了**；两个库交替生成还会把对方的缓存打穿。修完后：每个库有自己独立的状态账本、独立的锁、独立的手机通知编号，**今天单库使用零变化**，为"一库一学科"的未来铺好轨。

---

## 📖 用户故事（你的视角）

**作为** 将来会开第二、第三个学科库的学习者，
**我想** 每个库的每日复习推送各自独立记账，
**以便** 每个库每天都能收到自己的那条推送，谁也不覆盖谁、谁也不吞掉谁。

---

## 🖥️ 你会看到的交互（一步一步 · 双库时代的样子）

```
1. 早上 9:05，手机收到两条推送：一条「📚 今日复习 · CS 61B」，
   一条「📚 今日复习 · 数学」——各自独立，不互相顶掉
       ↓
2. 每条推送在 Bark 里归各自的分组（canvas复习·库名）
       ↓
3. 白天任何一个库刷新清单，另一个库完全不受影响
       ↓
4. 今天（单库）：一切和以前一模一样，你感觉不到任何变化
```

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现 `pytest` / `state` / `vault_key` / `dry-run` 等词不算 bug。
> 你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | 裁判命令：`pytest tests/regression/test_daily_review_run.py tests/regression/test_daily_review_pick.py -q` 全绿（24 存量适配 + 12 新增） | ✅ 36 passed |
| 2 | 新增"双 vault 同日各自推送"用例：tmp 库 A/B 各自 push:accepted、两个 state 文件独立、互跑第二轮各自缓存门仍 cached、全天只发 2 条推送 | ✅ 锁定 |
| 3 | 数据格式加性：payload 顶层只新增 `vault_id`，schema_version 保持 3，`notification.id` 的值一字未动（A2 冻结契约，测试锁死）；vault 维度只在发送侧组合 | ✅ 锁定 |
| 4 | 单 vault 生产回归：`daily_review_run.py --vault <worktree canvas-vault> --now 2026-08-26T10:00:00+08:00` 退出 0，落盘 JSON 含 `vault_id`，state 文件名 `daily-review.canvas-vault.state.json`，日志行带 `vault=` 标签 | ✅ exit 0 |
| 5 | 旧状态迁移脚本：`--dry-run` 对真实 backups/ 打印旧→新映射且**零写入**（前后目录快照 diff 为空，含字节码禁写）；实迁在 tmp 环境验证保留 `.bak` 可回滚、重复跑拒绝覆盖、并发决胜原子化、各种中断残局都有显式恢复指引 | ✅ 零写入证明 |
| 6 | 测试 fixture 注入完整性：STATE/LOG 常量函数化后，全部用例改为单点注入 BACKUPS（tmp 路径），逐用例核查无一写真实 backups/ | ✅ 逐用例核过 |
| 7 | 多 vault 循环在 shell 层每库一个进程（wrapper 循环调 push.sh），未引入 Python 进程内循环（decay_beta import 缓存坑规避） | ✅ 结构确认 |
| 8 | 隐藏消费方跟改：memory-health.sh 死人开关改读命名空间 state 文件（多库逐一汇报），旧全局文件迁移前仍可回退读取 | ✅ 已跟改 |
| 9 | Codex 交叉审查（gpt-5.6-sol，ultra 档，只读沙箱）：**九轮对抗攻防**——初轮 6 BLOCKER + 1 HIGH（key 碰撞/锁 ABA/迁移三类硬失败/健康检查假绿等），逐轮修复+复审，期间 Codex 亲测构造反例（locale 漂移、信号继承、symlink 劫持）均被击穿修复，第九轮终裁 **0 BLOCKER / 0 HIGH 可合入**。全程存档 `_bmad-output/审查/codex-review-CARD-C1a*.md`（9 份含处置附录 A-H） | ✅ 九轮清零 |
| 10 | 硬边界遵守：未 push、未碰 live vault 与 ~/Library、未动 review_service.py / fsrs_manager.py / canvas-vault/.claude/skills/ | ✅ diff 自查 |

---

## 👤 你来验（产品使用体验）

> [!info]+ 现在只有一个库，所以你今天验的是"零变化"
> 双库的真实体验要等第二个学科库建好（deploy-vault）后补真机 UAT。

### 第 1 步：单库体验零变化（部署后次日顺手看）

- [ ] 早上 9:05 手机照常收到一条复习推送（一天一条，不多不少）
- [ ] 推送内容和以前一样（板名、待巩固节点数、闲置天数）
- [ ] outputs/今日复习 页面照常生成和刷新

### 主观确认

- [ ] 我知道这张卡是"铺轨"性质：今天看不出变化就是成功

---

## 🚨 wrapper/launchd 重装待用户确认（重要 — 不确认就不会生效）

> [!warning]+ 这次改动只落在仓库副本，你 Mac 上正在跑的定时任务还没动
> 按纪律，Claude 本轮**只改了仓库里的脚本副本**（wrapper / push.sh / runner），**没有**碰 `~/Library/Application Support/CanvasReview/bin/` 里的安装副本，也没有执行任何 `launchctl` 命令。
>
> 所以你 Mac 上的定时任务**现在跑的还是旧版**（全局单 state）。**等你说一句"可以部署 C1a"**，Claude 再按顺序执行（每步贴结果）：
>
> 1. **合并**：把 `card/l1-crossvault` 分支合进 worktree 主车道（launchd 入口固定跑 `feature-obsidian-hybrid-dev` 目录的代码）；
> 2. **迁移状态**：`python3 scripts/migrate_daily_review_state.py --vault canvas-vault --dry-run` 给你看映射 → 确认后去掉 `--dry-run` 实迁（旧文件保留 `.bak` 可回滚）；
> 3. **重装 wrapper**：`cp scripts/launchd/daily-review-wrapper.sh` 到 `~/Library/Application Support/CanvasReview/bin/` 覆盖安装副本；
> 4. **当场验证**：`launchctl kickstart` 手动触发一次，看 boot 日志出现 `vault=` 行、新 state 文件生成、手机推送正常。
>
> 不确认就永远不会动你正在运行的任务。⚠️ 迁移（第 2 步）和重装（第 3 步）必须同一次做完——只做其一会出现「新代码找不到旧账本」或「旧代码不认新账本」的一天期错位。

---

## 📌 已知边界（诚实记录，均不影响日常使用）

1. **中文库名**会得到"slug+哈希"式的内部编号（如 `vault-1a2b3c4d`）用于文件名和通知去重号——手机推送的**标题和分组仍显示中文原名**，内部编号你看不到。
2. **多库清单**目前由 `.env` 的 `DAILY_REVIEW_VAULTS`（逗号分隔目录名）声明，留空 = 只推当前库（今天的行为）。目录名含空格的库暂不支持。
3. **双库端到端**目前只能在临时目录模拟验证（现实只有一个库）；真第二库建好后需补一次真机推送 UAT。
4. **同日迁移窗口**：部署当天如果迁移发生在早推送之后，当天下午的补跑读到的是迁移后的新账本——账本内容原样搬运，不会重复推送。
5. **极小概率的目录调包竞态**（审查 F6，已接受的残余风险）：理论上有程序能在"系统检查库目录合法"与"实际读写"之间的毫秒级窗口里把库目录调包成指向外部的替身。在你这台单人 Mac 上，能做到这件事的程序本来就拥有对全部库数据的完整权限，调包不会让它多得到任何东西——所以记录在案但不修。若将来引入受沙盒限权的第三方 App 共用此机器，需要重新评估这一条。

---

## 🚦 验收结果

**如果所有步骤 ✅**：告诉我 "**CARD-C1a 通过**"，本卡 mark done，车道 1 继续 CARD-C2。

**如果有任何一步 ❌**：在下面批注区写出具体哪一步 + 你看到的实际现象。

---

## 📝 你的批注区

> [!question]+ 你对 CARD-C1a 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）。
