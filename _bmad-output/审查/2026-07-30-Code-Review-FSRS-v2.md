---
type: code-review
plan_id: FSRS-V2-2026-07-30
date: 2026-07-30
reviewer: 独立 general-purpose Agent（对抗性，含沙盘实测复现）
graphiti_note: graphiti MCP 未挂载，[Code-Review] 以本文件代记录
---

# 代码审查报告 — FSRS v2（真实到期调度）

## 统计与处置

| 严重性 | 发现 | 处置 |
|---|---|---|
| CRITICAL | 0 | - |
| HIGH | 2 | 全部修复：H1 桥 venv 路径改「相对仓库根优先 + 硬编码兜底」+ wrapper cmp 守卫扩到 fsrs_bridge.py；H2 桥失败时不再删旧 fsrs_* 行（只有产出新块才删——一次临时故障不再清零调度历史，评审员已实测复现该病理） |
| MEDIUM | 2 | 全部修复：M1 降级消息改为无视退出码先读 stdout 诚实报错；M2 picker 对非规范 fsrs_due 格式 fail-open 视同到期 + stderr 记录（防 Obsidian Properties 重序列化造成「永不到期」静默消失） |
| LOW | 4 | 全部修复：L1 review.py 3 个死导入删除；L2 补真降级路径测试（REEXEC 守卫 + exit 3）；L3 Dashboard 口径对齐 Decision-FSRS-2（新卡计入到期）+ 两处 Story 5/6 陈旧文案清除；L4 统计口径备注 |

修复后回归：38/38 绿（bridge 9 + picker 10 + decay 18 + 退役回归 1）。评级从「需修复」升为**可复用**。

## 评审员实测过硬的部分（引用）

管道真实性（含空格路径 vault 全链路 e2e + 毕业到 Review 态回读）、subprocess 注入面、re-exec 递归守卫、跨时区 --now 三态比较、YAML 合法性（fsrs_step 空省略）、退役清扫零残留（/review/schedule、open-review-queue、DUE_THRESHOLD 全库无存活调用方）。

附注：test_dependencies.py 的 TestGetReviewService 3 个失败为既有测试债（本批未触碰），不在本批账上。
