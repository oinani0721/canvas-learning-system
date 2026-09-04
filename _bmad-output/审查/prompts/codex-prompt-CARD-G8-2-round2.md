# CARD-G8-2 独立对抗审查（round-2 · 整改复核）

你是独立审查者。round-1 你判 FAIL（1 BLOCKER + 7 HIGH + 4 MEDIUM，存档
`_bmad-output/审查/codex-review-CARD-G8-2.md`）。本轮复核整改后的车道
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。

工作目录 = 上述车道根。**只读审查，不要修改任何文件。**

## 一、round-1 逐条整改声明（请逐条对抗验证，证伪优先）

| # | round-1 发现 | 声明的整改 | 验证要点 |
|---|---|---|---|
| BLOCKER-1 | 无 PYTHONDONTWRITEBYTECODE 时 `--help` 也写 .pyc | vault_lint.py 顶部 `sys.dont_write_bytecode = True` 先于一切 import | 请在 /tmp 隔离副本上用 `env -u PYTHONDONTWRITEBYTECODE -u PYTHONPYCACHEPREFIX` 复跑你 round-1 的实验，确认 0 个 .pyc 产生 |
| HIGH-1 | 文件 symlink 跟随 vault 外 | `_read_text` 拒读 symlink；`_iter_md` 保留 symlink 在列（记盲区）；有盲区时检查 ≥warn | 你的 external.md fixture 应变为：孤儿仍报 + blind_spots=1 + status=warn |
| HIGH-2 | AUTO-GENERATED 哨兵段当入链 | `_strip_nonsemantic` 段级剥离（BEGIN→END 整段含成员列表） | 你的 AUTO fixture 应报孤儿；live 复算应仍 0 孤儿（3 节点改由 source_board 豁免） |
| HIGH-3 | `节点/` 不存在 → ok；不可读节点 → ok（fail-open） | 缺目录=FAIL+finding；盲区去重（set）+ ≥warn | 你的空目录 fixture 应 rc=1；非 UTF-8 节点 fixture 应 warn + 盲区恰 1 |
| HIGH-4 | 围栏/行内 code/HTML 注释/跨行伪链豁免真孤儿 | 四级剥离 + wikilink 正则禁跨行 | 你的四组 fixture 全部应报孤儿 |
| HIGH-5 | frontmatter 排除门无判别力；`[[]]` 用例不字面；缺节点互链正向用例 | 新增 `test_orphan_frontmatter_of_other_files_has_no_power`（B.frontmatter up→A，A 必报）/ `test_orphan_empty_wikilink_literal`（字面 `[[]]`）/ `test_orphan_node_to_node_body_link_counts`（变异对照=删 NODE_DIR 入链源） | 三个新用例请各自评估判别力（能否杀死它们声称能杀死的变异） |
| HIGH-6 | argparse 用法错误 rc=2 撞「有 warn」 | 自定义 `_LintArgumentParser.error()` 退 3 | 无参数与 `--only no_such_check` 都应 rc=3 |
| HIGH-7 | 变异判据 rc∈{2,3,4} 都算 KILLED；无 transcript | 判据=rc==1 且输出含指定门 FAILED 行；`evidence-g82/mutation-transcripts/` 存档；M1-M10 重跑 | 请抽查 transcript 与判定行的一致性；评估 M7-M10 四个新变异的锚与门对应关系 |
| MEDIUM-1 | `.MD` 未剥 / `source_board: null` 豁免 / 子目录跨链误杀自链 | 三处口径修（`\.md\Z` IGNORECASE / null,~,none → None / 自链仅限顶层文件） | 你的三组 fixture 应全绿（不误报不豁免） |
| MEDIUM-2 | resolve_today 默认分支未被门锁 | 提取 `_utcnow()` 时钟缝 + patch `_TZ_SHANGHAI` 为 UTC 的结构断言 | 评估该结构断言能否杀死 date.today()/宿主本地 变异 |
| MEDIUM-3 | UAT「全树 sha」与排除矛盾 | 结论区与 4-B 措辞改「排除 今日复习.* 后的全树」 | 查验收单 §1/§4-A/4-B |
| MEDIUM-4 | help 存档截断；分级规则不在 --help | help-full.txt 完整存档；分级规则写进 epilog；测试断言扩展 | 查 help-full.txt 与测试 |

## 二、整改引入的**新面**（重点对抗——整改本身可能引入新缺陷）

1. `_strip_nonsemantic` 的行级状态机：AUTO 段与围栏嵌套时的行为（AUTO 段内出现 ``` 会怎样？
   围栏内出现 AUTO BEGIN 行会怎样？未闭合时剥到哪）？会不会**过度剥离**把真入链剥掉（新假阴）？
   对照 sync_board_concepts.py 的实际写入形态（BEGIN 行无 `-->`、NOTE 行以 `-->` 结尾）验证
   正则是否逐字匹配。
2. symlink 保留在 `_iter_md` 后：`nodes_scanned` 计数会含 symlink（诚实化设计）；但
   `节点/` 下的 symlink 节点现在会**两处**记盲区吗（入链源循环 + 节点循环）？去重是否真的生效？
3. `source_board` 的 null 语义扩展（null/~/**none** → None）：YAML 里 `source_board: none`
   的合法语义是字符串 "none" 吗？会不会误伤？
4. `_LintArgumentParser.error()` 退 3：`--help` 与 `--version` 类正常退出路径有没有被误伤？
5. 新退出码语义（3=配置/环境/用法错误）与 --help 文案是否自洽；`test_bytecode_guard_is_armed`
   等既有测试有没有被整改破坏。
6. 裁判复跑实况：referee1-pytest-full-round2.txt = 171 passed（52+119）；变异 10/10 KILLED
   （transcripts/）；live round-2 sha 逐字相同 + rc=2 与 summary 一致。

## 三、范围与边界（同 round-1）

禁改面核实命令：
```
git log --format= --name-only $(git merge-base HEAD worktree-feature-obsidian-hybrid-dev)..HEAD -- \
  backend/scripts/check_vault_doc_roles.py backend/scripts/vault_doc_roles.yaml \
  canvas-vault/.claude/scripts/sync_board_concepts.py \
  backend/app/api/v1/endpoints/review_overview.py backend/app/services/board_manifest_service.py | sort -u
```
期望空。审查对象仍以 round-1 提示词的四类重点（orphan 假阴阳面 / 同源锁真绑定 / 零写侧 /
退出码自洽）为准绳；「声明比证据宽」与代码缺陷同级。

## 四、输出格式

同 round-1：BLOCKER/HIGH/MEDIUM/LOW 分级、file:line、具体失败场景（什么输入 → 什么错误输出）、
你实际跑过的命令与输出。round-1 各条若整改不成立请直接标 REGRESSED。
最后一行必须是：`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`。
