## 结论

**FAIL。0 BLOCKER，4 HIGH，4 MEDIUM。**

当前复核对象为 `card/w9-lint @ 9af18b27`，`vault_lint.py` SHA-256 为 `a5497d91…eb6fd1`。指定的简单整改多数成立，但 symlink、非语义 Markdown、测试判别力和证据绑定仍有可复现 HIGH。

## HIGH

### HIGH-1 — REGRESSED：symlink 防线仍可越界读取并 false green

位置：[vault_lint.py:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:238)、[vault_lint.py:365](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:365)、[vault_lint.py:418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:418)、[vault_lint.py:520](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:520)、[vault_lint.py:540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:540)

普通文件 symlink 已修好，但存在三条旁路：

- `原白板 -> vault 外目录`，外部 `external.md` 含 `[[x]]`：`rc=0/status=ok/findings=[]/inbound_targets=1/blind_spots=0`。原因是扫描根 `is_dir()/rglob()` 跟随 symlink，而后代文件本身 `is_symlink()==False`。
- `节点/lost.md -> 不存在目标`：被 `p.is_file()` 静默过滤，得到 `rc=0/nodes_scanned=0/blind_spots=0`。
- `outputs/回顾-outside.md -> vault 外 type: recap 文件`：G8-1 已记 G11，但 recap 二次循环又直接调用 `read_frontmatter_type()` 跟随读取；最终 `raw_derived_confusion=ok`，同时 `blind_spots=1`，`rc=0`。

指定的 direct-file fixture 确实变为 `warn + 节点/x.md孤儿 + blind_spots=1`，但整改未封闭整个读取边界。

### HIGH-4 — REGRESSED：合法 Markdown 变体仍能隐藏真孤儿

位置：[vault_lint.py:302](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:302)、[sync_board_concepts.py:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/canvas-vault/.claude/scripts/sync_board_concepts.py:52)、[sync_board_concepts.py:463](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/canvas-vault/.claude/scripts/sync_board_concepts.py:463)

简单三反引号、单反引号、闭合 HTML 注释、跨行 wikilink 四组已通过，但：

- 四反引号 fence 内出现三反引号：`:328` 只保存前三字符，提前关闭 fence，`[[x]]` 被算入链，`rc=0/status=ok`。
- 双反引号 code span ``[[x]]``：`:331` 只删除两端空 span，留下 `[[x]]`，结果 `ok`。
- 跨行 code span、未闭合 HTML comment也均得到 `ok/inbound_targets=1`。
- 按真实生成器的 BEGIN（无 `-->`）+ NOTE（以 `-->` 结尾）构造 AUTO/fence 交叉：

  ```text
  <!-- AUTO-GENERATED ...
       NOTE -->
  ```text
  <!-- /AUTO-GENERATED ... -->
  [[x]]
  ```
  ```

  AUTO 状态吞掉 fence opening，END 后仍位于 Markdown fence 内的 `[[x]]` 被计为入链：`rc=0/status=ok/inbound_targets=1`。

反方向交叉还会吞掉 fence closing，把 fence 外真实链接剥到 EOF，造成假孤儿且没有 malformed/blind 提示。

### HIGH-5 — REGRESSED：空 `[[]]` 新测试仍无判别力

位置：[test_vault_lint.py:418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:418)、[test_vault_lint.py:432](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:432)、[test_vault_lint.py:444](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:444)

- “其他文件 frontmatter 指向 A”能杀全文当正文变异：PASS。
- 节点正文入链能杀移除 `NODE_DIR` 变异：PASS。
- 空链用例同时放了 `[[]]`、`[[ ]]` 和有效 `[[A]]`。即使错误实现把空链也映射成 A，A 已经被真实 `[[A]]` 豁免。隔离变异实跑 baseline 与 mutant 均为 `findings=[]`。

因此 [UAT:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:46) 的“空 `[[]]` 不判定”仍是声明比证据宽。

### HIGH（新增）：round-2 存档未绑定当前 exact bytes

位置：[UAT:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:10)、[UAT:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:52)、[referee transcript:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/referee1-pytest-full-round2.txt:1)

- `HEAD == merge-base == 9af18b27`，提交区间为零。
- 实现、测试、UAT、evidence 全部 untracked。
- 存档 pytest 完成于 `07:11:52`，当前 `vault_lint.py` birth/mtime 为 `07:17:00`。
- 存档没有 source/test digest 或 manifest；UAT 的“最终树 git status 干净”也与当前状态冲突。

我已独立对当前 `a5497d91…` 重跑 171 门和 M1–M10，均通过；这重新证明了当前态，但原存档本身不能证明它对应当前字节。

## MEDIUM

1. **MEDIUM-1 REGRESSED/PARTIAL。** [vault_lint.py:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:357) 丢弃路径只保留 basename。`d1/A.md -> [[d2/a]]` 时，A 和目标 a 都归一为同一 key，实际 `findings=[]`；正确结果应仍报告无入链的 `d1/A.md`。对应测试 [test_vault_lint.py:468](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:468) 只断言目标不误报，没有断言来源仍是孤儿。另 [vault_lint.py:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:273) 先去引号再判 null，导致 `source_board: "null"`/`"~"` 被误当 YAML null。plain `none` 当前正确保留为字符串；整改声明中的“none→None”反而不符合 YAML 语义。

2. **MEDIUM-2 REGRESSED/PARTIAL。** 实现 [vault_lint.py:688](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:688) 当前正确，但测试 [test_vault_lint.py:483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:483) 不是环境无关结构门。`TZ=UTC` 时 host-local mutant 返回预期 `2026-08-31` 而存活；`_utcnow().date()` mutant 当前也直接存活。`date.today()` 仅因本轮宿主日期为 09-01 才被杀。

3. **MEDIUM-3 REGRESSED/PARTIAL。** §1、§4-A、§4-B 主体已明确排除 `今日复习.*`；但 [UAT:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:89) 仍据排除后的 SHA 写“live 零写已证”，与 [UAT:135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:135) 的“不证明今日复习文件”矛盾。当前独立运行中，被排除文件也逐个保持相同，但这不能修复历史证据的逻辑洞。

4. **零写声明边界。** 指定 direct `vault_lint.py --help` 已不写 pyc；但无环境变量 `import vault_lint` 会在第 64 行执行前生成 `vault_lint.cpython-314.pyc`。此外 [test_bytecode_guard_is_armed:679](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:679) 检查的是测试文件自己预先设置的全局开关，help 测试也显式设置环境变量；删除生产脚本 guard 后这两门仍可能绿。

## LOW

- [vault_lint.py:33](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:33) 仍说 pycache 由调用方负责，与后文模块兜底声明矛盾；symlink 测试注释称不计入 `nodes_scanned`，实际计入。
- UAT 写 round-2 为 `06:5x`，实际 [live-window-round2.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/live-window-round2.txt:1) 是 `07:06:40 +0800`；仍在 09:05 前，不改变 freshness 结论。

## Round-1 逐条复核

| 项 | 结论 |
|---|---|
| BLOCKER-1 | **PASS（指定 direct CLI）**：`rc=0`，0 pyc；模块 import 边界见 MEDIUM |
| HIGH-1 | **REGRESSED**：直接文件 symlink 修好；目录/祖先、dangling、recap 二次读取未封 |
| HIGH-2 | **PASS（正常生成形态）**：AUTO-only 报孤儿；live 仍 14 节点/0 孤儿；交叉状态缺陷并入 HIGH-4 |
| HIGH-3 | **PASS（指定两例）**：缺目录 `rc=1/fail`；非 UTF-8 `warn/blind=1`；dangling 仍 fail-open |
| HIGH-4 | **REGRESSED**：简单四组通过，合法 Markdown 变体仍 false green |
| HIGH-5 | **REGRESSED**：三门中空链门仍无判别力 |
| HIGH-6 | **PASS**：无参数、非法 `--only` 均 rc3；help rc0；未定义的 `--version` 合理地 rc3 |
| HIGH-7 | **PASS**：判据已收紧；当前 exact bytes 的 M1–M10 全部指定门被杀 |
| MEDIUM-1 | **REGRESSED/PARTIAL**：`.MD`、plain null/~ 通过；子目录同 basename 假阴和 quoted-null 残留 |
| MEDIUM-2 | **REGRESSED/PARTIAL**：实现正确，测试仍依赖宿主时区/日期 |
| MEDIUM-3 | **REGRESSED/PARTIAL**：主要措辞修正，UAT:89 残留过宽结论 |
| MEDIUM-4 | **PASS**：完整 help 39 行，当前输出与存档 `cmp=0`，分级规则完整 |

## 实跑命令与关键输出

```text
$ env -u PYTHONDONTWRITEBYTECODE -u PYTHONPYCACHEPREFIX \
    backend/.venv/bin/python /tmp/card-g82-r2-pyc.VxGuwW/vault_lint.py --help
rc=0; pyc_count=0

$ ... vault_lint.py --vault .../board-dir-link --only orphan_nodes --json
rc=0; status=ok; findings=[]; inbound_targets=1; blind_spots=0

$ ... --vault .../broken-link --only orphan_nodes --json
rc=0; status=ok; nodes_scanned=0; blind_spots=0

$ ... --vault .../recap-link --only raw_derived_confusion --json
rc=0; status=ok; findings=[]; blind_spots=1

$ ... --vault .../inline-double --only orphan_nodes --json
rc=0; status=ok; inbound_targets=1

$ ... --vault /tmp/g82-auto-fence-95_3lb6v/v --only orphan_nodes --json
rc=0; status=ok; findings=[]; inbound_targets=1

$ PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest \
    tests/unit/test_vault_lint.py tests/unit/test_vault_doc_roles.py \
    -q -p no:cacheprovider
171 passed, 13 warnings in 337.40s

$ cd /tmp/g82-current-mutations.frPe7W
$ bash _bmad-output/审查/evidence-g82/g82_mutation_negative_controls.sh
M1–M10: rc=1 + 各自指定 FAILED；ALL-KILLED
恢复后 SHA256=a5497d91…eb6fd1；与工作区 cmp=0
```

Live 当前重跑为 `rc=2`，JSON 为 `ok=2/warn=1/fail=0`，与存档逐字相同；当前前后摘要也相同。用户给定禁改命令 stdout 为空，额外 `git diff/status` 检查五个禁改文件也为空；但因 `HEAD==merge-base`，`git log` 本身是真空证明。

本轮未修改工作区；所有自建 fixture、变异和脚本副本均位于系统临时目录或 `/tmp`。

BLOCKER/HIGH 清零：否


