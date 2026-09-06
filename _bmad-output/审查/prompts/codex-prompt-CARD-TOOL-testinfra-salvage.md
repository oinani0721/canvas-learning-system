# 复核任务：CARD-TOOL-testinfra-salvage（定点抽取 + 管道退出码穿透 + 基线对账）

你是独立复核者。工作树根目录：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool`

只读复核，不要修改任何文件。请按下面的顺序读材料、然后逐条回答问题。

## 一 背景（一句话）

分支 `fix/test-infra-paralysis` 上有 4 个 commit，其中 3 个（`f19dcff6` / `7f495eda` /
`0fd6d398`）是要抽取的内容，第 4 个 `66d6a835` 是一次 merge origin/main（57 文件
+7830/-114），把它带进来会把主干上四张已合入的卡改回旧版。本卡要求逐个
`git cherry-pick --no-commit` 前三个、显式排除第四个，并修掉主干上仍存在的
「管道吞掉退出码」问题。

## 二 读取面

1. 代码改动全貌（这是复核的主体）：
   ```
   git diff 16b9e337 HEAD -- . ':(exclude)_bmad-output'
   ```
   `16b9e337` 是本车道上一张卡的收尾 commit，`HEAD` = `aae845f8`。共 13 个文件。

2. 四个 commit 的消息与逐个内容：
   ```
   git log --format='%H%n%s%n%b%n---' 16b9e337..HEAD
   git show 33fd106d -- lefthook.yml .claude/hooks/
   git show aae845f8
   ```

3. 冲突解法的对照物（分支上的原始 hunk，**不是**要落地的字面）：
   ```
   git show f19dcff6 -- lefthook.yml
   git show 16b9e337:lefthook.yml   # 解冲突时用作底版
   ```

4. 裁判与证据 transcript（全部在 `_bmad-output/审查/evidence-testinfra/`）：
   - `judge-c-*.txt`、`judge-c4f-*.txt`、`judge-78-*.txt`、`judge-7c-rewrite-*.txt` — 静态判据
   - `canary-d-*.txt`、`canary-d-extra*.txt` — wrapper 行为探测
   - `unit-pre-*.txt`（开工基线）、`unit-post2-*.txt`（收工基线）、`skip-detail-*.txt`
   - 红基线对照文件在另一棵树：
     `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b12/unit-red-baseline-03ac8bf8.txt`
     （247 个 nodeid；口径写在该文件头部 5 行）

5. 验收单（含逐命令判定表与三列对账表）：
   `_bmad-output/验收单/UAT-CARD-TOOL-testinfra-salvage-2026-09-06.md`

## 三 lefthook.yml 的解法说明（供你判断是否只做了该做的变换）

`f19dcff6` 对 `lefthook.yml` 只有一个 hunk，覆盖 pre-push 的两个命令。它的字面是
2026-04 的状态：`frontend-test` 用 glob `frontend/src/**` + `npx vitest`，
`backend-smoke` 跑 `tests/unit/` 全目录并用 `command -v python`。主干这两处都已被后续
的卡改过（glob 指向 `frontend/obsidian-plugin`、runner 换成 `npm test`；backend-smoke
收窄成 A11 两文件并用 `.venv/bin/python`）。

本卡的做法：以 `16b9e337:lefthook.yml` 为底，只把「管道 → wrapper」这一个变换落到现行
命令体上。`frontend-test` 取变换；`backend-smoke` 判定为不需要改（它已经用
`TEST_EXIT=$?` 显式捕获退出码、本来就没有管道），二者不并存。

## 四 请回答的问题（按重要性排序，逐条给结论 + 证据行号）

1. **lefthook.yml 的手工解法是否只做了「管道 → wrapper」这一个变换？**
   有没有夹带任何把主干配置改回旧版的内容（glob、runner、测试目标、解释器路径）？
   `backend/tests/unit/` 全目录、`command -v python` 这些旧字面有没有以任何形式回来？
   `backend-smoke` 块是否与 `16b9e337` 版逐字节相同？

2. **`scripts/run_cmd_capture.sh` 会不会在某条路径上改写被包裹命令的退出码？**
   请把每一条 return / exit 路径列出来，并说明它返回什么。特别注意：
   - `"$@" &> "$LOGFILE"` 之后 `RC=$?` 的取值是否可能被中间语句污染；
   - 参数解析分支（`--cwd` / `--tail` / 未知 flag / 缺少 `--`）各自的退出码；
   - `set -u` 在参数缺失时的行为，以及它产生的退出码是否与「被包裹命令失败」混淆；
   - 验收单里已登记了三条 wrapper 本体的瑕疵，请判断这三条的定级是否恰当，以及是否
     还有第四条。

3. **基线对账是否把「被 skip 掩盖」与「真的修好」分开了？**
   验收单三列表的分类是否与 transcript 里的实际数字一致？有没有把 skip 记成修复？
   `test_memory_service_write_retry.py` 那 18 条的处置说明是否准确？
   另外：验收单声称 6 个文件共 47 条 SKIPPED、而红基线里只有 43 条 —— 这个差额 4 条
   的解释（原本是绿的测试被类/模块级 skip 顺带关掉）是否成立？请自己数一遍。

4. **`.claude/hooks/stop-test-runner.js` 的 Stop hook 协议（失败时 exit 2）是否保住？**
   主干版有 2 处 `process.exit(2)`，现在只有 1 处。减掉的那一处原来负责什么？
   这个变化会让哪些情况从「阻断」变成「放行」？验收单对此的声明是否如实？

5. **`aae845f8` 修的那 2 条断言，是修复还是迁就实现？**
   请自己去 `backend/app/services/episode_worker.py` 核对生产行为，判断新断言是否
   反映了真实契约。特别看：期望值是写死的字面量还是调用生产函数求出来的（后者会随
   实现一起漂移）；补的那条「原始 task.group_id 不被改写」是否是独立的不变量。

6. **有没有本卡改动引入的、验收单没有登记的新问题？**
   包括但不限于：`ruff format` 那一批改动里有没有语义变化（验收单声称纯格式）；
   13 个文件的改动面有没有超出三个 commit 应有的范围；有没有碰到卡文禁改的文件
   （`backend/tests/conftest.py`、`backend/tests/support/live_port_guard.py`、
   `backend/tests/unit/conftest.py`）。

## 五 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级列出发现，每条给：结论、证据（文件:行号或命令
输出）、以及你认为的处置建议。没有发现的级别写「无」。最后给一段总体判断。

请不要输出「PASS」或「FAIL」这类总评字样——分级发现清单本身就是结论。
