总裁定：**需整改，不可验收**。

绑定最终稳定快照：

```text
HEAD    cbb20afb572a7b8ce9ebc205082e4be6de076fb8
checker 78917021cbdf1f2e812d5988b920efa384e9b3c7c65ba7e1ddbec60162d9fe85
YAML    05ef82794c143b7cd9a27339df9d72852e354cb3c830f2ee2b4aaa191fffafcc
tests   5480e4808befa8c20c286fb72ca84c52db1a13f2c878d7b5f8a1447ef1434f84
```

审查期间三件未跟踪交付物曾被外部并发改写；以下结论只绑定上述最终字节。工作区未被我修改，fixture/变异均在 `/tmp`。

## 逐项裁定

| 项目 | 结论 |
|---|---|
| BLOCKER-1 | **NOT-CLOSED**：FOO 正例修好了、普通 G5 反例也能抓，但豁免仍可被跨角色 symlink 误命中 |
| BLOCKER-2 | **NOT-CLOSED**：round-1 两个反例已判 G6，但发现新的 G6 绕过 |
| H1 `.claude/cache` | **CLOSED** |
| H2 `dir-excalidraw` | **CLOSED** |
| H3 identifier / repo_docs 契约 | **NOT-CLOSED / HIGH** |
| H4 `.claudian` / learning events 角色 | **NOT-CLOSED / HIGH** |
| H5 零写入/只读退出 | **NOT-CLOSED / HIGH** |
| §4 五项事实 | **全部一致 / CLOSED** |
| 测试面 E 三项指定变异 | **CLOSED：全部 KILLED，无 survivor** |
| 业务代码与分歧台账改动面 | **CLOSED** |

### BLOCKER-1 / BLOCKER-2

生产入口统一复跑：

```bash
TMPDIR=/tmp/card-g8-r2-blockers.xaVhqH/runtime \
PYTHONDONTWRITEBYTECODE=1 \
backend/.venv/bin/python backend/scripts/check_vault_doc_roles.py \
  --enforce --json --vault /tmp/card-g8-r2-blockers.xaVhqH/<fixture>
```

| fixture | 真实 `scan()` | CLI |
|---|---|---|
| `div2-vault/节点/FOO.MD` | entry=`T/T`；actual=`F(not_markdown)/T(ok)`；`probe_divergent` 含 FOO；`findings=[]`；INFO 如实写“偏离常态、命中已登记分歧类” | `rc=0` |
| `g5-vault/节点/alias-to-blacklisted.md -> 检验白板/plain.md` | entry=`T/T`；actual=`T(ok)/F(blacklisted_dir)`；`covered=False`；`G5+G6` | `rc=1` |
| `alias-vault/alias-text.md` | `G6`，reason=`ok/not_markdown` | `rc=1` |
| `alias-vault/alias-blacklisted.md` | `G6`，reason=`ok/blacklisted_dir`，另有无关 G3 | `rc=1` |
| `bypass-vault/检验白板/alias-into-node.MD -> 节点/plain.md` | entry=`F/F`；actual=`F(not_markdown)/T(ok)`；`covered=True`；`findings=[]`，仅 INFO | **`rc=0`** |

最后一行是阻断反例：它与 DIV-2 的 pattern、scope、布尔对、reason 对全部相等，但原因包含“symlink 解析后跨角色目录”。当前覆盖函数没有绑定 lexical entry/baseline 或 symlink 身份，[覆盖判定](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:687) 将其误认成 DIV-2；随后 [G5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:620) 和 [G6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:641) 同时放过。

所以：

- B1 的三个指定检查本身通过，但“豁免没有开过大”不成立。
- B2 的两个旧反例已修复，但仍存在真实 G6 绕过。

## HIGH-1 至 HIGH-5

### H1 — CLOSED

```bash
find canvas-vault/.claude/cache -type f
```

输出：

```text
board-manifest/manifest-v3.json                         1
rag-s2.6-concepts-backup/*.md.bak                       6
合计                                                     7
```

独立解析结果：

```text
manifest  -> art-board-manifest-cache / derived /
             board_manifest_service / 可重建
6 backups -> art-rag-s26-board-backup / raw /
             Story RAG-S2.6 / 不可重建
```

`cmp` 六组备份与当前原白板均为 `same_bytes=False`；`run_skill_navigation_probe.py` 的 `BAK_DIR`/读取点在 40、75–78 行。台账拆分见 [backup](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:858) 与 [manifest](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:881)，owner、角色和可重建性自洽。

### H2 — CLOSED

```bash
find canvas-vault -path '*/Excalidraw/*.excalidraw.md' -type f
rg -n '^source_board:' canvas-vault/raw/CS188/Excalidraw -g '*.excalidraw.md'
rg -l '^source_board:' canvas-vault/outputs -g '*.excalidraw.md'
```

输出：

```text
raw 手绘文件：1
raw source_board：无，rg rc=1
outputs 系统导出：3，三份均命中 source_board
```

原始手绘 frontmatter 仅有 `excalidraw-plugin`、`tags`。因此 [dir-excalidraw=raw](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:223) 与系统导出 derived 分行成立。

### H3 — NOT-CLOSED / HIGH

存在性检查确实加上了，但契约只验 truthiness/字符串化，未验结构和可核身份。

内存变异直接调用生产 `_verify_contract()`：

```text
drop_identifier          ConfigError
scalar_identifier='x'    PASS
drop_repo_rag_retrieval  ConfigError
empty_repo_path_glob=[]  PASS
rag_index='false'        PASS
```

对应薄弱点在 [checker:340–363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:340)。

按 checker 自己的 glob 语义复算 repo 文档：

```text
tracked=2428 covered=1021 uncovered=1407
uncovered samples:
.claude/agents/basic-decomposition.md
.claude/commands/auto-epic.md
CURRENT_TASK.md
PRD.md
_bmad/_memory/storyteller-sidecar/stories-told.md
_decisions/ADR-001-dialogue-engine.md
```

因此 repo_docs 仍没有 live repo census 门，空 glob/伪布尔也能恢复为“绿”。

### H4 — NOT-CLOSED / HIGH

```bash
find canvas-vault/.claudian -type f
```

输出：

```text
sessions=30
claudian-settings.json=1
```

只打印 settings 顶层键，得到 `model`、`providerConfigs`、`permissionMode`、`systemPrompt` 等应用配置字段。台账自己的 schema 定义明确包含“工具/应用定义、应用配置”，但 [dir-claudian](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:496) 用一个 `.claudian/**` glob 全标 raw。正确方向应至少拆为 sessions/raw 与 settings/schema。

事件账复算：

```bash
wc -l canvas-vault/learning_events.jsonl
rg -n 'append_event|open\(path, "a"|review event ledger|复习事件契约' \
  backend/app/services/learning_event_log.py \
  _bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md
```

输出：

```text
22 learning_events.jsonl
learning_event_log.py:59 append_event
learning_event_log.py:100 open(path, "a", ...)
计划书:186 schema = “复习事件契约”
计划书:200 review event ledger 与 schema 并列
```

[台账](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:577) 把“事件契约”偷换为“22 条事件实例账本”，而且同时写“frontmatter 才是真相源”“无上游不可恢复”“它自己是 canonical”，不自洽。

### H5 — NOT-CLOSED / HIGH

严格 deny-all-writes 实测：

```bash
sandbox-exec -p '(version 1)(allow default)(deny file-write*)' \
  env PYTHONDONTWRITEBYTECODE=1 \
  backend/.venv/bin/python backend/scripts/check_vault_doc_roles.py \
  --no-probe --allow-degraded --enforce --json
```

输出：

```text
rc=0
probe_skipped=true
checks_run=["G1","G2","G3","G4"]
dirs=175 files=324 findings=[]
```

说明 `--no-probe` 本身确实没有 import 写副作用；且当前未加 `--allow-degraded` 会正确 `rc=2` 拒绝伪装成全量门。

但同一严格环境跑全量 probe：

```text
rc=1
Traceback ...
FileNotFoundError: No usable temporary directory
scan:603 -> should_index:174 -> lazy import lancedb_client/jieba
```

异常发生在首次调用真实函数，不在 `load_admission_fns()` 的初始 import 捕获范围内。因此 docstring 所称“严格只读失败优雅 exit 2”仍为假。

## §4 五项事实

| 事实 | 独立命令与输出 | 结论 |
|---|---|---|
| 根级 Markdown reason | production 两函数遍历 10 个根级 md：9 个=`F(blacklisted_file)/F(root_level)`；唯一 `chatgpt-adversarial…md`=`T(ok)/F(root_level)` | 一致 |
| LanceDB | `docker exec backend printenv LANCEDB_DATA_PATH` → `/lancedb`；`ls /lancedb` → `canvas_vault_file_fingerprints.lance`、`canvas_vault_vault_notes.lance`、`file_fingerprints.lance` | 一致，三表 |
| Neo4j 标签组合 | `MATCH (n) RETURN labels(n),count(*)` → Entity 99；Episodic 35；Entity+LearningConcept 27；CanvasNode 21；EntityNode 3；User 2；Concept 1；VaultIdentity 1 | 一致，含次标签 27 |
| `.claude/cache` | `find ... -type f` → manifest 1 + backup 6 | 一致 |
| node_modules | `find ... -path '*/node_modules/*' -type f` → `35`，其中 UI 25、`raw/CS188/exams` 10 | 一致 |

`CALL db.labels()` 还返回五个零实例标签：CanvasBoard、Community、EpisodicNode、Node、Saga；台账也已如实区分。

## 测试面 E

绑定临时副本 `/tmp/card-g8-finalmut.jVZoZf`，未改工作区。

基线：

```bash
CANVAS_BASE_PATH=/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault \
PYTHONDONTWRITEBYTECODE=1 \
backend/.venv/bin/python -m pytest -p no:cacheprovider -vv \
  test_vault_doc_roles.py::{用例12,用例13,用例14,用例15}
```

输出：

```text
4 passed
```

完整文件：

```text
49 passed, 10 warnings in 66.13s
```

指定 mutation 结果：

```text
撤销 B1 G5 豁免：
  用例13 FAILED
  FOO.MD offending=[G5]

删除 B2 reason 比对：
  用例14 FAILED
  g6=set()
  findings 只剩无关 G3

dir-jiedian frontmatter_type 增加 dashboard，
并同步刷新 checker 指纹：
  用例12 FAILED
  declared=['(none)','concept','dashboard']
  observed=['(none)','concept']
  extra=dashboard
```

因此三项指定 mutation 全部 **KILLED**，没有用户定义的 mutation-survivor BLOCKER。用例 15 内置的删除 identifier、删除 repo `rag_retrieval`、删除 divergence reason 三项也都收到 `ConfigError`。

但新增两个测试质量问题：

- **MEDIUM**：用例 14 的 CLI `rc=1` 被无关 G3 污染。reason mutant 下 CLI 没有任何 G6，仍因 G3 退出 1；只有 in-process `g6` 集合断言能杀当前 mutant。应断言 CLI 输出含两条 G6，或让 fixture 没有其他 finding。
- **MEDIUM**：用例 12 在 live vault 不可达时直接 `SKIPPED`，pytest 总退出 0。当前本机能杀 mutant，但 CI/隔离环境是 fail-open。

## 改动面

```bash
git rev-parse HEAD
git rev-parse cbb20afb
git diff --exit-code --stat cbb20afb
git status --short --untracked-files=all
```

输出：

```text
HEAD = cbb20afb572a7b8ce9ebc205082e4be6de076fb8
base = cbb20afb572a7b8ce9ebc205082e4be6de076fb8
git diff --stat：空，rc=0
status：16 个 ??，均为三件交付物、审查/UAT/证据文件
backend/app、backend/lib、frontend、frontend/sidecar：0 改动
```

台账仍保留 [DIV-1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:144) 和 [DIV-2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:169)。结论：**没有为变绿修改业务代码，也没有抹掉分歧**。不过所有交付物均是 untracked，故空 `git diff` 本身不能证明其内容；最终 SHA 是必要绑定。

## 原始逐字稿的遗漏残留

整改 §2/§3 的“2 BLOCKER + 5 HIGH”重排漏掉了 round‑1 raw 中数项原始 finding：

- **BLOCKER / NOT-CLOSED**：有效 YAML `type : rogue` 仍绕过裁判。[checker regex](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:205) 只认严格 `type:`。

  ```text
  PyYAML type = rogue
  checker type = (none)
  scan findings = []
  CLI --enforce rc=0
  ```

- **HIGH / NOT-CLOSED**：根级 `*.md` 仍是实质兜底。当前解析：

  ```text
  future-secret.md => root-loose-md | wiki | rag=true | memory=false
  ```

- **HIGH / NOT-CLOSED**：resolver 仍先匹配 any-level root_files，再匹配目录角色：

  ```text
  .quarantine/UAT-2.5.X-test.md
    => root-uat-scratch | wiki | 可安全删除
  raw/CS188/_misc/junk/未命名.md
    => root-untitled-scratch | wiki | 可安全删除
  ```

  与隔离区/raw 的生命周期规则冲突，根因见 [resolver 顺序](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:451)。

- **HIGH / NOT-CLOSED**：`doc_type=note` 的角色仍声明为 wiki，却明确 `registered_by` 包含 `dir-raw`、根级课程 raw；生产默认无 type 的 raw 文档写 `note`。角色映射仍不唯一。

- **MEDIUM / NOT-CLOSED**：台账仍称 `endpoints/review.py` 消费 `outputs/今日复习.md`；代码唯一命中只是注释，真实链使用 JSON。
- **MEDIUM / NOT-CLOSED**：checker 仍在目录和文件循环中无条件跳过 `.git`。
- round‑1 的 LanceDB 三表漂移和 DIV-1 分侧 reason 误述则已由本轮 §4 复算确认 **CLOSED**。

## 新发现分级

- **BLOCKER**：DIV-2 coverage 未绑定 lexical entry、resolved target 或 symlink 身份；同 pattern/reason 的跨角色 symlink 可同时绕过 G5/G6。
- **HIGH**：H3 契约允许 scalar identifier、空 path_glob、字符串伪布尔，并漏 1407 个 tracked Markdown。
- **HIGH**：`.claudian` 需要按 sessions/settings 拆角色；事件账实例不能由“事件契约”直接推成 schema。
- **HIGH**：严格只读全量 probe 的 lazy import 异常仍为未捕获 `rc=1`。
- **MEDIUM**：用例 14 CLI 断言被 G3 伪绿；用例 12 无 live vault 时 skip/fail-open。
- **LOW**：无新增。

因此，即使 H1/H2、五项事实、三项指定 mutation 和业务改动面均通过，仍有可复现的生产入口 BLOCKER，最终裁定只能是：**需整改**。


