## 终轮结论

**FAIL。WT=`card/w9-lint`，HEAD=`9af18b27092c46f5c0a41989f7ccd1e4b3a9c56f`。0 BLOCKER，4 HIGH。**

`176 passed`、当前 live `rc=0`、隔离副本全部变异被杀都真实成立，但生产入口仍有普通可达的 false-green/越界场景，且证据清单没有绑定核心 transcript。按停轮条款：**终轮到顶未清零，当前不可合并，须显著登记并留台账。**

## HIGH

### HIGH-1 — REGRESSED：统一 symlink/盲区边界仍未封闭

位置：[vault_lint.py:240](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:240>)、[vault_lint.py:402](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:402>)、[vault_lint.py:623](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:623>)、[vault_lint.py:674](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:674>)、[test_vault_lint.py:454](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:454>)

生产 CLI 临时 fixture 实测：

| 场景 | 实际结果 |
|---|---|
| `节点/sub -> vault 外目录(A.md)` | `rc=0,status=ok,nodes=0,blind_spots=0`；嵌套目录 symlink 被 `rglob` 静默吞掉 |
| `原白板 -> 节点/`，A 只有自链 `[[A]]` | 同一物理文件以别名贡献入链；`rc=0,status=ok,inbound_targets=1` |
| `回顾-outside.md -> vault 外` | 已拒读并记录 `recap_blind`，但仍 `raw_derived_confusion=ok,rc=0`；测试甚至明确锁定 `status == OK` |
| `outputs -> vault 外目录`，外部 JSON 为当天 | freshness 实际读取 vault 外文件并返回 `projection_status=ok,rc=0` |

指定的“扫描根直接指 vault 外”、直接文件 symlink、dangling 文件 fixture 已通过；但整改声明的“统一边界守卫”仅部分成立。

### HIGH-2 — REGRESSED/PARTIAL：不可读子树仍假绿

位置：[vault_lint.py:413](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:413>)、[vault_lint.py:445](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:445>)、[check_vault_doc_roles.py:1120](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/check_vault_doc_roles.py:1120>)

`节点/locked/A.md` 创建后将 `locked` 设为 `chmod 000`：

```text
rc=0
status=ok
summary=0 个节点, 0 个孤儿
blind_spots=0
```

现有逻辑只能处理“已枚举、但文件读不出”；不可读目录整棵消失。round-1 HIGH-3 的缺目录和非 UTF-8 单文件已修，但广义不可读扫描面仍 `REGRESSED/PARTIAL`。

### HIGH-3 — REGRESSED：合法 code-span 仍能隐藏孤儿

位置：[vault_lint.py:327](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:327>)、[vault_lint.py:370](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:370>)、[test_vault_lint.py:355](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:355>)

Code span 的开闭 backtick run 必须等长，但正则 `` `+[^`]*`+ `` 没有此约束：

```text
``foo` [[A]]``
```

单 backtick 被误当成双 backtick closer；实际：

```text
STRIPPED='  [[A]] '
rc=0 status=ok findings=[] inbound_targets=1
```

这不是 §6.1 已登记的 AUTO-fence 手工交叉，而是普通合法 Markdown，因此 round-2 HIGH-4 仍为 `REGRESSED`。

### HIGH-4 — REGRESSED：MANIFEST 未绑定核心证据 exact bytes

位置：[MANIFEST.txt:9](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/MANIFEST.txt:9>)、[MANIFEST.txt:37](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/MANIFEST.txt:37>)、[UAT:53](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:53>)

- MANIFEST 已列的四个源码/测试对象及 25 个根级证据：`29/29 OK`。
- 但当前 `mutation-transcripts/` 的 **15 份 transcript 全部未列入**。
- 裁判 1 的 `backend/tests/unit/test_vault_doc_roles.py` 也未绑定；当前 SHA 为 `6617b17b…a39f114`。
- 忽略旧备份目录，活跃证据实际为 40 文件、MANIFEST 仅列 25；包括 `.old-transcripts-*` 时目录实际有 95 文件。

失败场景：替换任一 KILLED transcript 或 G8-1 测试文件，MANIFEST 校验仍全部 `OK`。因此 round-2 “全部证据当前字节绑定”整改不成立。

## MEDIUM

1. **MEDIUM-1 REGRESSED/PARTIAL。** [vault_lint.py:284](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:284>)、[vault_lint.py:374](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:374>)

   - `source_board: null # 尚无来源` 在剥注释前判 null、剥完不再判，最终 `_fm_scalar == "null"`，孤儿假绿 `rc=0`。
   - `d1/A.md`、`d2/a.md`、由第三文件链接 `[[d2/a]]`：路径被压成 basename，实得 `3 个节点/0 孤儿`；`d1/A.md` 应仍报。
   - 用户指定的 `d1/A -> d2/a` 自贡献场景和 `"null"` 引号字符串场景本身均通过。

2. **MEDIUM-2 REGRESSED。** [test_vault_lint.py:578](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:578>)

   `TZ=UTC` 时基线测试绿，但固定钟选在 `2026-08-31T23:00Z`，UTC 与 New York 仍是同一天：

   ```text
   expected_NY=2026-08-31
   host_local_mutant=2026-08-31
   utc_date_mutant=2026-08-31
   ```

   因此它杀不死注释声称要杀的两个时区变异；“环境无关结构判别”声明不成立。

3. **MEDIUM-4 REGRESSED/PARTIAL。** [vault_lint.py:813](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:813>)

   CLI 无环境变量写 0 pyc 的行为门真实有效；docstring/UAT 也写了 import-as-library 边界。但 `--help` 仍笼统称“不依赖调用方环境变量”，未披露库 import 自身 pyc 例外。

4. **MEDIUM：变异计数不精确。** [UAT:83](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:83>) 称“14/14”，脚本实际执行 15 个 mutant：M1–M11、M12a、M12b、M13、M14。准确表述应为“14 个编号组、15 个 mutant/transcript”。

5. **MEDIUM：人话版仍是旧终态。** [UAT:15](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:15>) 已称 09:33 `rc=0`，但 [UAT:119](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:119>) 仍称“现在是凌晨、昨天数据、1 条提示”。

## LOW / 登记结案评估

- **AUTO-fence 交叉可作为显式风险接受。** [sync_board_concepts.py:463](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/canvas-vault/.claude/scripts/sync_board_concepts.py:463>) 的真实生成器只产 BEGIN/NOTE/member/END，不产 fence，且 [line 53](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/canvas-vault/.claude/scripts/sync_board_concepts.py:53>) 明写“请勿手改”。建议降为 LOW/登记结案；这是风险接受，不是技术修复。
- [vault_lint.py:432](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:432>) 和 UAT §3 仍称自链规则“仅顶层适用”，但实现 line 485–489 已统一排除所有节点自身来源。
- `live-sha-command.txt` 未固定 locale；当前 `C` 得 `f63bb258…`，`en_US.UTF-8` 才得存档 `a82e3af0…`。前后相等证据仍成立，但跨环境命令不确定。

## 独立实跑

```bash
cd backend
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest \
  tests/unit/test_vault_lint.py tests/unit/test_vault_doc_roles.py \
  -q -p no:cacheprovider
```

```text
collected 176 items
176 passed, 13 warnings in 236.31s
```

隔离 `/tmp` 副本运行原变异脚本：

```text
M1–M11, M12a, M12b, M13, M14:
rc=1 + 指定门 FAILED
ALL-KILLED
temp source restore SHA=37127d8f…a020a6719
```

重复测试名负控：

```text
baseline duplicate_names=[]
追加第二个 test_orphan_symlink_never_read:
rc=1
AssertionError ... ['test_orphan_symlink_never_read']
```

空链隔离变异：

```text
baseline_findings=['节点/A.md']
empty_maps_to_A_mutant_findings=[]
gate_would_fail=True
```

Live 当前复跑：

```text
rc=0
status_counts={ok:3,warn:0,fail:0}
orphan=14/0
raw_derived=324 files/0 confusion
projection_status=ok
排除 今日复习.* 后 SHA before/after=a82e3af0…a380
```

工作树始末状态相同，无新增 pyc、pytest cache 或 `*.bak-g82`。Graphiti 工具本轮未暴露，因此未执行 `search_memory_facts`；全仓 CI 也不在用户指定裁判范围内。

## Round-1/2 逐条状态

| 历史项 | 终轮状态 |
|---|---|
| BLOCKER-1 CLI pyc | PASS |
| HIGH-1 symlink | **REGRESSED** |
| HIGH-2 正常 AUTO 哨兵 | PASS |
| HIGH-3 缺目录/不可读 | **REGRESSED/PARTIAL** |
| HIGH-4 非语义 Markdown | **REGRESSED** |
| HIGH-5 判别力/空链 | PASS |
| HIGH-6 argparse rc | PASS |
| HIGH-7 指定门变异 | PASS；实际 15/15，证据绑定另见 HIGH-4 |
| round-2 新 HIGH：exact-byte binding | **REGRESSED** |
| MEDIUM-1 basename/null | **REGRESSED/PARTIAL** |
| MEDIUM-2 时钟测试 | **REGRESSED** |
| MEDIUM-3 今日复习排除措辞 | PASS |
| round-1 MEDIUM-4 help 分级规则 | PASS |
| round-2 MEDIUM-4 import/pyc 边界 | **REGRESSED/PARTIAL** |
| 自查：重复同名测试门 | PASS，有判别力 |

AUTO-fence 交叉属于可登记结案类；上述 4 个剩余 HIGH 均不是构造性前提，而是普通文件系统、合法 Markdown 或证据绑定场景，不能登记后合并。

BLOCKER-COUNT: 0; HIGH-COUNT: 4；结论：终轮未清零，须再修，当前不可合并，并按卡文显著声明、留台账。


