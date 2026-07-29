---
type: code-review
plan_id: DAILY-REVIEW-PUSH-2026-07-29
date: 2026-07-29
reviewer: 独立 general-purpose Agent（对抗性，非本体自审）
scope: 每日复习推送 MVP 全部 10 个新增/修改文件
graphiti_note: 本 session graphiti MCP 未挂载，[Code-Review] 以本文件代记录
---

# 代码审查报告 — 每日复习手机推送 MVP

## 统计

| 严重性 | 发现 | 已修复 | 进 backlog | 有理由保留 |
|---|---|---|---|---|
| CRITICAL | 0 | - | - | - |
| HIGH | 2 | 1（H1 无 key 静默） | 1（H2 memory-health 宿主迁移） | - |
| MEDIUM | 6 | 5（M1/M2/M3/M4/M5） | 1（M6 部分：picker 测试已补，runner 单测靠 12 场景矩阵） | - |
| LOW | 7 | 6（L1/L3/L4/L5/L6/L7） | - | 1（L2） |

评审员评级「需修复」→ 修复后回归全绿，升级为**可复用**。

## 修复清单（全部已验证）

| # | 问题 | 修复 | 验证 |
|---|---|---|---|
| H1 | 无 key 时一切静默且日志全绿 | skip-nokey 也发每日一条本地提醒「Bark 未配置，仅本地提醒」 | 实测 `push:skip-nokey fallback:ok` |
| M1 | 死人开关 9:00 跑在 9:05 生成前 → 天天误报 ❌ | 判据改昨日界（48h 内活着 = ✅） | 实测 `复习推送:生成:✅` |
| M2 | 病理 last_examined（0001 年）→ 0.99^d 下溢 → 除零崩全轮 | effective() 加 `f=max(f,1e-150)` 同比下限（μ 不变契约不破）+ picker try 扩到 pick_score | 新测试 ×2 + fixture 实测 |
| M3 | 无 source_board 节点系统性失明（live 命中 4 个） | md 点名列出未归板节点；回填进 backlog | 新测试 + md 实查 |
| M4 | runner import 主仓 untracked 手工拷贝，忘 cp = 静默漂移 | wrapper 预检加 `cmp` 双副本一致性，不一致 fail | wrapper 重装 |
| M5 | 断电/SIGKILL 残留锁 → 永久静默跳过 | mtime>6h 陈旧锁夺回 | 代码审读 |
| M6 | 三个新脚本零自动化测试 | 新增 test_daily_review_pick.py 7 用例（病理日期/wikilink/占位/tie-break/负值/BOM/未归板） | 26/26 绿 |
| L1 | osascript 兜底无去重，窗内每次触发都弹 | `last_local_notify_date != today` 门 | 实测同日二跑 `fallback:-` |
| L3 | payload_sha256 死字段 | cached 分支校验 sha，不一致重生成 | 实测 cached 命中 |
| L4 | key 文件贴裸域名 → 误导性 net= 重试 | key 格式校验（字符集+长度），不合法按未配置退 2 | 实测人话提示 |
| L5 | 负数 mastery 静默降级 + BOM 不容忍 | `_fm_num` 容负号（进 corrupt 分支）+ frontmatter 容 BOM | 新测试 ×2 |
| L6 | --now 裸时间两入口语义差 8 小时 | picker 与 runner 统一「裸时间=本地时区」 | 代码对齐 |
| L7 | 手工把 a/b 改 0 → 评分段裸 traceback | 写分前 `max(A,1e-4)` 容错钳制 | 部署双副本 |

## Backlog（转入吸收文档 §五 加固清单）

- **H2**: memory-health.sh 的 launchd 宿主仍指向 worktree 且 TCC 拦截（上次退出 126）——需同款迁移到 `~/Library/Application Support/CanvasReview/bin/` wrapper + TCC 预检。监控者自身无监控，是既有基建债，非本 MVP 范围。
- **M3 后半**: 4 个未归板节点（考察-Fundamentals-2026-07-16 / cs-61b-csm / csm-tutoring-unit-credit / my-recursion-notes）的 source_board 回填（从原白板 ## Concepts 反查）。
- **M6 后半**: runner 状态机单测化（当前由 12 场景运行时矩阵覆盖）。

## 有理由保留（对审查意见的 pushback）

- **L2（board_last_recommended 在生成时记账而非推送成功时）**：刻意保留。无 key / 纯 md 用户也应获得轮转推荐——md 落盘即「已推荐」的产品语义；若改成推送成功才记账，无 key 用户的 tie-break 永不轮转。

## 审查亮点（评审员独立复现的证据）

- underflow 崩溃用 python 实测复现（days=74000 → ZeroDivisionError）
- key 永不进 argv/URL/日志：POST body only 实核
- 管道全链静态连通 + 21:23 手动运行四重落盘证据
- 发现 launchd 运行态双断点（TCC 78 + 无 key）并确认 wrapper 预检有效
