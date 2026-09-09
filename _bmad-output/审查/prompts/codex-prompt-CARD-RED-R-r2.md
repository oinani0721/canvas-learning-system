# 独立复核请求 — CARD-RED-R round-2（整改后复核）

## 一 背景与最小读取面（写死，请只读这些）

本卡是**零代码**定性卡：对 `backend/tests/unit` 红基线（202 条）中被归为「真实现回归」的 26 条，加上 1 条被类级 `@pytest.mark.skip` 掩盖的条目（共 27 条），逐条在独立临时 worktree 里定位 first-bad 并三选一定性。round-1 你给出 BLOCKER 0 / HIGH 3 / MEDIUM 4 / LOW 3；作者逐条实测复核后**认定三条 HIGH 与 MEDIUM-1 全部成立**并已整改。本轮请核对整改是否到位、是否引入新的不实表述。

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance`

请读：

1. 分派表（已整改）：`_bmad-output/审查/evidence-red-r/red-r-triage-20260909.md`
2. 验收单（已整改）：`_bmad-output/验收单/UAT-CARD-RED-R-2026-09-09.md`
3. round-1 复核存档：`_bmad-output/审查/codex-review-CARD-RED-R-r1.md`
4. 本轮新增的三份实测存档：
   - `_bmad-output/审查/evidence-red-r/high1-node-id-filter-detail-20260909T131436.txt`（HIGH-1 用 `-o addopts='' -vv --tb=long --showlocals` 重取）
   - `_bmad-output/审查/evidence-red-r/receiving-card-nameclash-20260909T132057.txt`（MEDIUM-4 台账与 U11-B 核验）
   - `_bmad-output/审查/evidence-red-r/zero-code-gate-20260909T125457.txt`（零代码门）
5. 全部 bisect 存档与探针：`_bmad-output/审查/evidence-red-r/*-bisect.txt`、`probe-*.txt`
6. 需要时用 `git show <sha> -- <path>` 自取（本树内）：`a9304c69` / `836d0986` / `59586af1` / `3d10a02b` / `4236b12e` / `43294c38` / `89d51dc9` / `1768c19d` / `d4823ef9` / `f6a55d3a`

## 二 作者对 round-1 各条的处置（请独立核对，不要采信本节）

- **HIGH-1（第 31 行归因错位）→ 认可并改**。重取 traceback 实测：失败发生在**第一个不带过滤**的断言 `assert len(all_results) == 2`；`--showlocals` 显示 tier1 `relevance_score=0.0` 被地板滤掉、tier2 `relevance_score=0.05` 恰在地板上保留。当前成因已改为 4236b12e 的 `min_relevance=0.05` 地板，生产 file:line 改为 `memory_service.py:2417-2418`。
- **HIGH-2（f6a55d3a 错认为恢复点）→ 认可并改**。实测 `git log --reverse -S 'async def search_error_memories(' 3d10a02b^..8f5f9efc` 只给出 3d10a02b（删）与 d4823ef9（加），且 `f6a55d3a^` 已有该方法。恢复点改为 **d4823ef9**；f6a55d3a 的作用改述为 `_with_status` 状态接口改造。§四 的草案假设 2 相应由「重写点被推翻」改判为「证实」。
- **HIGH-3（三个 HTTP 条目异常链未闭合）→ 认可并改**。实测注入的是 `SessionNotFoundError("not found")`（`app/services/session_manager.py:107` 定义为 `class SessionNotFoundError(Exception)`），已改掉「裸 Exception」的表述，并在这三行与 §三 显式登记「异常链未闭合：未取路由映射与产生 500 的那一层」。
- **MEDIUM-1（生产不可用归因过度）→ 认可并改**。实测 `836d0986^` 上 `app/core/config.py` 同样不存在，该 try 一直恒 ImportError；生产正常路径 `review.py:396` 提前返回。已把「既有降级」与「本次埋下的 NameError」分开登记。
- **MEDIUM-2（红的定义与谓词不一致）→ 认可**，新增 §五之三 显式声明 runner 谓词把 collect error 判 SKIP、而 3 条结论用的「红」是「不再 pass」，并说明为何不改判据重跑。
- **MEDIUM-3（环境等价性 PARTIAL）→ 认可**，保留在验收单「本卡未证明什么」。
- **MEDIUM-4（接收安排未独立确认）→ 认可并补证**，落档台账路径、`grep -c 'CARD-RED-R-FIX'` = 0（rc=1）、`git merge-base --is-ancestor card/u11-red-c main` rc=1（未合入）；并声明未读 U11-B 卡文、未核其接收范围。
- **LOW-1/2/3 → 全部认可并改**：改为 16 条相邻区间 / 11 条宽区间二分；身份变化改为 8 条、候选被推翻改为 6 条；`-r2-checkout-failed.txt` 的描述改为「事后由作者比对存档 `HEAD=` 行识别并作废，脚本当时并未拦下」。

## 三 请按重要性回答的问题

1. 上述整改是否**如实**反映证据？特别是 HIGH-1 的新归因（相关度地板）、HIGH-2 的新恢复点（d4823ef9）、MEDIUM-1 的责任切分，是否有过度或不足。
2. 整改过程中是否**引入了新的不实表述**或与既有存档矛盾之处？
3. 27 行闭合、定性分布（回归 19 / 契约演进 8 / 测试写错 0）、以及 8 条「契约演进」的判定，在整改后是否仍然成立？
4. 还有没有 round-1 未指出、但同类的归因或计数问题？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出：分派表或验收单中的行号（或证据文件名 + 行号）、一句话依据。若某级别为空请显式写「无」。

## 五 边界

- 只读复核。不要修改任何文件，不要连接任何数据库或网络服务。
- 不要评价修复方案该怎么写（那是接收卡的事），只判断本卡的定位、定性与整改是否站得住。
- 若判断需要更多证据，请明确指出「缺哪一份证据、该用什么命令取」。
