结论：**FAIL**。当前 `WT=card/w9-lint`，`HEAD=947ef20683884adff24fb5f09196bd7f54c3dfa6`。**0 BLOCKER，2 HIGH**。`181 passed`、`19/19 KILLED` 与 MANIFEST 全覆盖均真实，但不足以闭合两个生产 false-green。

| round-3 项 | 本轮裁判 |
|---|---|
| H1a + H2 枚举盲区 | PASS |
| H1b realpath 自链排除 | PASS |
| H1c raw-derived 盲区 | **REGRESSED** |
| H1d 越界投影 | PASS |
| H3 等长 code span | **REGRESSED** |
| H4 MANIFEST 覆盖 | PASS |

## BLOCKER

无。

## HIGH

### HIGH-1 — REGRESSED：H1c 只修了 recap 特例，普通 raw-derived 盲区仍假绿

[vault_lint.py:627](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:627) 已收集 G8/G10/G11 到 `blind`，但 [vault_lint.py:642](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:642) 的状态只判断 `findings or recap_blind`；[vault_lint.py:652](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:652) 又对外报告 `blind_spots=len(blind)`。

现有测试 [test_vault_lint.py:456](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:456) 仅锁 `回顾-outside.md`。

生产 CLI 反例：`节点/sub -> vault 外目录`。

```text
vault_lint.py --vault <fixture> --only raw_derived_confusion --json

blind_spots=1
status=ok
cli_rc=0
note="扫描面问题 1 条 ... [G8] 节点/sub"
```

普通 `outputs/ordinary.md -> vault 外文件` 同样得到 `G11 + blind_spots=1 + status=ok + rc=0`。因此“raw_derived 盲区存在 → 至少 warn”的整改声明不成立。指定的 recap fixture 本身已是 `warn/rc=2`，但只是特例闭合。

### HIGH-2 — REGRESSED：H3 的反向引用仍不保证 CommonMark maximal delimiter run

问题位于 [vault_lint.py:367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:367)–371。正则：

```python
r"(`+)[^`]*\1"
```

中的 `+` 可以回溯成较短 opener，`\1` 也能匹配更长 closing run 的前缀。

反例正文：

```text
``[[A]] ` foo``
```

MarkdownIt 实跑确认整个内容是一个双反引号 `code_inline`：

```text
[('code_inline', '[[A]] ` foo', '``')]
```

但生产逻辑输出：

```text
stripped=' [[A]]  `'
{"findings": [], "inbound_targets": 1, "status": "ok"}
```

代码 span 内的 `[[A]]` 泄漏为入链，真孤儿 A 被隐藏。现有 [test_vault_lint.py:968](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:968) 的 fixture 是偶然通过；M16 只能杀退回旧正则的变异，不能证明 maximal-run 语义。

## MEDIUM

1. **M17 未锁“零外部读取”。** 当前 [vault_lint.py:694](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:694) 的守卫确实位于读取前，FIFO/read-sentinel 实测 `corrupt` 且未读取；但 [test_vault_lint.py:943](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:943) 只断言结果。插入“先读、再返回 corrupt”的精准变异后该门仍绿。

2. **M18 未锁指定的 CLI JSON 契约。** 当前 CLI 确实输出 `rc=2/status=warn/blind_spots=1`，但 [test_vault_lint.py:920](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:920) 只检查内部 `CheckResult`；删除 [vault_lint.py:201](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:201) 的 JSON `details` 后相关门仍绿。

3. **UAT 终态陈旧且互相冲突。** [UAT:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:11) 写 181/19，但 :13、:45–58、:86–94、:118–123 仍写 176/15、旧源码 SHA 与 M1–M14，不能作为单一终态验收入口。

## LOW

- `live-sha-command.txt` 未固定 locale；默认/C 与 `en_US.UTF-8` 得到不同聚合 SHA。before/after 相等的零写证据仍成立。
- M13 官方变异过宽、M15 官方变异非最小；额外精准变异均被对应测试杀死，因此不影响其 PASS。

## 已确认通过及实跑

- H1a/H2：目录 symlink 与 `chmod 000` 均进入 `blind_detail`，`--only orphan_nodes --json` 为 `warn/rc=2`。
- H1b：[vault_lint.py:488](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:488) 与 :505 均使用 realpath；目录别名 fixture 中 A 仍报孤儿。
- H1d：越界当天投影为 `fail/corrupt/rc=1`，FIFO 探针未被打开。
- H4：[MANIFEST.txt:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/MANIFEST.txt:4)–8 五个源码/测试 SHA 全匹配；:11–66 恰覆盖 56/56 活跃证据，含 19 份 transcript。
- M11 物理路径锚与 M13 两行锚分别位于 [mutation harness:118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/g82_mutation_negative_controls.sh:118)、[mutation harness:133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/g82_mutation_negative_controls.sh:133)。

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest \
  tests/unit/test_vault_lint.py tests/unit/test_vault_doc_roles.py \
  -q -p no:cacheprovider

collected 181 items
181 passed, 13 warnings in 203.04s
```

隔离 `/tmp` 副本运行现行 mutation harness：

```text
M1-M11, M12a, M12b, M13-M18：19/19 KILLED
ALL-KILLED
restore SHA=9997cdc68748...，cmp_rc=0
```

MANIFEST 独立复算：

```text
源码/测试 5/5 OK
活跃 evidence 56/56 OK
实际集合与清单 comm -3：空
```

审查前后工作树状态指纹均为 `1469d3fb…e0b`；四个关键文件 SHA 未变，无 `.bak-g82` 或 pytest cache 残留。Graphiti `search_memory_facts` 本环境未暴露，未执行。

BLOCKER/HIGH 清零：否（BLOCKER: 0, HIGH: 2）


