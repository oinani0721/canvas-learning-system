结论：**FAIL**。当前 `WT=card/w9-lint`，`HEAD=947ef20683884adff24fb5f09196bd7f54c3dfa6`；裁判对象为脏工作树当前字节。**0 BLOCKER / 2 HIGH / 3 MEDIUM / 0 LOW**。

| round-4 项 | round-5 裁判 |
|---|---|
| HIGH-1 G8/G10/G11 盲区状态 | PASS，非 REGRESSED |
| HIGH-2 maximal backtick run | **REGRESSED** |
| M17 守卫先于读取 | PASS |
| M18-2 CLI JSON 契约 | PASS |
| UAT 终态统一 | FAIL，MEDIUM |

## BLOCKER

无。

## HIGH

### HIGH-1 — REGRESSED：inline code 错把“更长 run”当作 closer

实现于 [vault_lint.py:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:341)–344 跳过 `< opener` 后，无条件接受首个 `>= opener` 的 run。CommonMark inline code 的 closing backtick string 必须与 opener **等长**；“至少同长”是 fenced code block 的规则，不是 code span 规则。[CommonMark 0.31.2 §6.1](https://spec.commonmark.org/0.31.2/#code-spans)

生产反例：

```text
节点/A.md
原白板正文：`x``[[A]]`
```

MarkdownIt：

```text
[('code_inline', 'x``[[A]]', '`')]
```

因此 `[[A]]` 在 code span 内，不应算入链；A 应报孤儿。当前实跑：

```text
strip='[[A]]`'
targets=['a']
cli_rc=0
status=ok
findings=[]
inbound_targets=1
```

命令：

```text
PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python \
  backend/scripts/vault_lint.py \
  --vault <tmp>/vault --only orphan_nodes \
  --now 2026-09-01T12:00:00+08:00 --json
```

结果仍是“真孤儿被隐藏”的生产 false-green，因此 round-4 HIGH-2 整改不成立，标 **REGRESSED**。现有新门 [test_vault_lint.py:1004](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:1004)–1013 只覆盖 2/1/2 run，未覆盖 1/2/1。

### HIGH-2 — 整改引入新面：删除 span 后拼接出不存在的 wikilink

[vault_lint.py:348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:348)–354 用空串删除 span，再直接 `join` 两侧文本。

反例：

```text
[`x`[A]]
```

原文 token 是：

```text
text '[' + code_inline 'x' + text '[A]]'
```

原文没有连续 `[[A]]`，但当前输出：

```text
stripped='[[A]]'
targets=['a']
cli_rc=0 status=ok findings=[] inbound_targets=1
```

旧逻辑用空格替换会得到 `[ [A]]`；本次无占位拼接实际制造伪入链，同样隐藏真孤儿 A。

## MEDIUM

1. **M16 删除理由不成立。** [mutation harness:133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/g82_mutation_negative_controls.sh:133)–134 与 [UAT:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:121) 声称 M13/M16 均被 M20 更强覆盖。精准 M16 变异实跑结果：

   ```text
   test_code_span_equal_length_runs: KILLED
   test_code_span_commonmark_maximal_run: SURVIVED
   ```

   M13 的 no-strip 语义确会被 M20 门杀死，但 M16 等长语义不会。故“19 个活跃 mutant 全杀”数量真实，语义覆盖声明为 PARTIAL。

2. **UAT 仍不是统一的 round-5 终态。** [UAT:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:13) 仍写 15 份 transcript；[UAT:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:46)–51 的正式结论仍称“三轮、终轮未清零”；:104、:132、:150 仍把 round-3 09:33 称为最终 live；:197–209 仍将 round-3 停轮移交写成现行处置。

3. **`--help` 未同步 HIGH-1 状态契约。** 实现 [vault_lint.py:670](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:670)–684 已让 `recap_blind`、G8/G10/G11 blind 触发 WARN，但 [vault_lint.py:848](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:848)–850 仍只写“有混淆 finding”才 warn。实跑 `--help | cmp help-full.txt` 得 `rc=0`，说明当前帮助和绑定证据一起陈旧；UAT 所称“分级规则全语义完整”不成立。

## 已确认通过

- HIGH-1：G8、G10、G11 三类真实 CLI fixture 均为 `status=warn / blind_spots=1 / JSON exit_code=2 / OS rc=2`；[测试:983](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:983)–1001 的内部、JSON、rc 门均通过。
- M17：守卫位于 [vault_lint.py:725](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:725)–730；精准“先读再返回 corrupt”变异被新门杀死。
- 完整测试亲跑：

  ```text
  184 passed, 13 warnings in 196.89s
  ```

- 隔离 `/tmp` 副本重放当前 mutation harness：

  ```text
  19/19 KILLED
  ALL-KILLED
  ```

- [MANIFEST](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/MANIFEST.txt:4)：源码/测试 `5/5`、活跃 evidence `62/62` 哈希匹配，实际集合与清单 `comm -3` 为空。
- live round-5 存档内部一致：before/after 均为 `a82e3af0…`，stored rc 与 JSON 均为 0。未重读工作区外的 raw live vault，因此这里只判证据包内部一致。
- 禁改门为空；测试与隔离变异后源码 SHA 仍为 `a8234c15…c47f`，工作树外 `.venv` 无新增 pytest/pyc/bak 残留。
- `graphiti-canvas` MCP 本环境未暴露，故本轮无法执行其 memory-facts 检索。

BLOCKER/HIGH 清零：否（BLOCKER: 0, HIGH: 2）


