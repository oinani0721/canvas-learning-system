# CARD-G5-9 worktree vault 全链实测证据（BATCH-2026-08-28-第五批）

> **本目录为 Codex round-3 全部处置后的最终重取版**（写侧从 W4/W5 一路加固到 H5-H8/M4-M7）：
> create = `O_CREAT|O_EXCL|O_NOFOLLOW` 写 tmp + fsync + **`os.link` no-replace** + fsync 父目录，
> 且本次实测**全程带 `--expect-content-sha`**（preview 回执的 sha 原样传入，create 回执 sha 与之全等 = 所见即所写绑定生效）；
> undo 走 fd+(dev,ino) 绑定 + 目的端 `O_EXCL` 写 + fsync 后删源。
> 两组板全链判据依旧全过，`检验白板/` 内 **0 个 `.g59-tmp` 残留**，`undo_hint` 已 shell-quote。
> 组 1 ts=2026-08-28-2000、组 2 ts=2026-08-28-2010（均 UTC）；本次实测另确认 undo_hint 可被 shlex 直接解析（9 参数、零 shell 重定向字符）。

- **时间**: 2026-08-28
- **对象**: worktree vault `canvas-vault/`（live vault 冻结不碰——本卡 live 侧价值验证按 D5 前置顺延 G5-11）
- **快照口径**: `find . -type f -print0 | sort -z | xargs -0 shasum -a 256` → `baseline.txt`（**全 vault 69 文件，含 `.claude/`**）

## 两组真实板全链（preview → create → undo）

### 组 1: 特征值与特征向量 + CS 61B（双板，ts=2026-08-28-2000）

| 步骤 | 证据 | 判定 |
|---|---|---|
| preview（未确认路径） | `g1-preview.json` + `g1-after-preview.txt` | diff baseline 为空 → **未确认零写侧 SHASUM-IDENTICAL** |
| create | `g1-create.json`（回执含 created_path/content_sha256/undo_hint） + `g1-after-create.txt` | diff baseline **恰 1 新增行**（检验白板/特征值与特征向量-2026-08-28-2000.md）；`.g59-tmp` 残留 0 |
| undo | `g1-undo.json` + `g1-after-undo.txt` | diff baseline 为空 → **回字节基线 SHASUM-IDENTICAL**；文件移入 vault 外留痕目录不删除 |

### 组 2: 递归与分治 (Recursion & Divide-Conquer) + 线性代数 + CS 61B（三板，ts=2026-08-28-2010）

同表三步全过（`g2-*.json` / `g2-after-*.txt`）：未确认零写侧 / create 恰 1 新文件 / undo 回字节基线。

## 消费面兼容实测（创建在位时真跑 board_manifest_service.scan_vault）

`g2-manifest-compat.txt`：`parse_errors: 0 | stage-recap 收录: 1 | question_count: 0 | digests 总数: 1`
`baseline-manifest.txt`（undo 后基线对照）：`digests 总数: 1 | parse_errors: 0 | exam_history: 1`

→ **past_question_digests 零新增**（1 == 1，既有的 1 条来自 vault 里 2026-07-05 的旧检验白板，与本卡无关）；
阶段回顾板被 exam_history 正常收录且 question_count=0；全 vault 0 parse_errors。

## quiz-answer done 分支安全停核对（卡片 (b) 条款）

`quiz-answer/SKILL.md` Step 0：`status: done` → A3 增量归纳分支——Grep 答题区疑问批注（本产物无答题区、无
`[!question]`/`[!error]` callout、无 answer sentinel）→ 无新疑问 → 分支 4「停止」，零写侧。
机械前提由 `test_g5_9_recap_exam.py::test_quiz_answer_done_branch_safe_stop_preconditions` 锁定。

## D5 前置诚实登记

D5 前置 1（用户 UAT 反馈）在本卡开发时**未发生**——live 侧价值验证顺延 G5-11，本卡只交 worktree 面 + fixture 证据，不宣称已经真实用户验证。
