总裁定：需整改。

8 条窄声明本轮均属实，且三项冻结对象开跑、收尾无漂移；但开放审查发现 HIGH 级台账—生产语义偏差及 checker 契约缺口，不能仅凭 `105 passed` 和 live `0 finding` 验收。

### 冻结校验

开跑与收尾输出完全一致：

```text
72e1d7617dfcfd4ce76b9459415d6ac8fdc9414eb249e01b6234936bfe87fd90  backend/scripts/vault_doc_roles.yaml
6cf028b0dbab65b6cae9cd3fc1ce7f527694a1394f40ae05a91f98ed15386c4b  backend/scripts/check_vault_doc_roles.py
86666ddbacd5f5444e78895d77a5d2aa170af7bf2c635aa8b8db9adc06c04a5e  backend/tests/unit/test_vault_doc_roles.py
```

Checkout：`card/t4-roles@cbb20afb572a7b8ce9ebc205082e4be6de076fb8`。

### 8 条逐项裁定

1. 属实

```text
$ cd backend && .venv/bin/pytest tests/unit/test_vault_doc_roles.py -q
collected 105 items
================= 105 passed, 10 warnings in 91.40s ==================
exit 0
```

首次在强制只读沙箱内因无可写临时目录而未完成收集；在允许依赖使用系统临时目录后原命令重跑得到上述结果。

2. 属实

执行 argv 与声明一致；仅设置 `PYTHONDONTWRITEBYTECODE=1` 防止写入工作树 pyc：

```text
$ env PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python \
    backend/scripts/check_vault_doc_roles.py --enforce \
    --vault /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault

vault .../canvas-vault  (175 目录 / 324 文件, 只读)
双准入面实测分歧 1 条: chatgpt-adversarial-review-Q1Q2Q3-2026-05-12.md
✓ 无 finding —— live vault 全部类型已登记, 且台账双列与真实函数一致
exit 0
```

stderr 仅含 Python/langchain/jieba 警告及初始化信息。

3. 属实

```text
$ backend/.venv/bin/python backend/scripts/check_vault_doc_roles.py \
    --enforce --vault /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault \
    --no-probe

[拒绝执行] --enforce 与 --no-probe 同用会跳过 G5/G6/G7 ...
  确需在严格只读环境跑降级门, 请显式加 --allow-degraded。
exit 2
```

4. 属实

同一进程内生成前清单、运行声明 2 的 checker、再生成后清单。每项为排序后的 `(原始字节相对路径、size、文件 SHA-256)`，并直接比较完整列表：

```text
INVENTORY_BEFORE regular_files=324 visited_dirs_including_root=176
canonical_sha256=34fd04dfdc1cd8edacd20e0347026463057adf676a5f3c26a8e49db81ea4f092
COMMAND_EXIT=0
INVENTORY_AFTER  regular_files=324 visited_dirs_including_root=176
canonical_sha256=34fd04dfdc1cd8edacd20e0347026463057adf676a5f3c26a8e49db81ea4f092
INVENTORY_EXACT_EQUAL=True
DIRECTORY_VISIT_COUNT_EQUAL=True
symlinks=0
other_nonregular=0
```

因此不仅整体摘要相同，324 项清单对象也逐项完全相等。

5. 属实，但不表示全仓干净

```text
$ git diff cbb20afb --stat
<空>

$ git status --porcelain -uall -- backend/app backend/lib frontend
<空>
```

全量 status 并非空，包含：

```text
?? backend/scripts/check_vault_doc_roles.py
?? backend/scripts/vault_doc_roles.yaml
?? backend/tests/unit/test_vault_doc_roles.py
?? _bmad-output/...
```

所以“指定三处业务代码零条目”属实；“整个工作树干净”不成立，也不是本声明内容。

6. 属实

```text
$ rg -n '以下分歧是 by-design|id: DIV-[12]|属设计分歧而非缺陷|不是修复对象' \
    backend/scripts/vault_doc_roles.yaml

144:  # ⛔ 以下分歧是 by-design 登记对象, 不是修复对象。
148:    - id: DIV-1-root-level-md
163:        ...属设计分歧而非缺陷。
174:    - id: DIV-2-md-suffix-case
```

当前冻结字节中没有把二者改写为“已修复”。因文件未跟踪，Git 历史不能独立证明更早版本的时间序列。

7. 属实

```text
$ rg -n '^ROLES_SHA256 = ' backend/scripts/check_vault_doc_roles.py
100:ROLES_SHA256 = "72e1d761...fd90"
```

临时副本只改第 11 byte：

```text
$ cmp -l 原YAML 篡改副本
11 61 62

篡改 SHA = 6c5eb59e452470df7c1274510c1c8343266ed983c9c5744c67479e5b441d9562
```

用未改 checker 副本执行：

```text
[配置/环境错误] 台账指纹不匹配 (双文件契约)
  期望: 72e1d761...fd90
  实际: 6c5eb59e...9562
exit 2
```

8. 属实

测试头声明见 [test_vault_doc_roles.py:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/tests/unit/test_vault_doc_roles.py:4)：

```text
38 个 test 函数 / 27 个编号语义组
```

实测：

```text
$ grep -c '^def test_' backend/tests/unit/test_vault_doc_roles.py
38

$ grep -oE '^# [0-9]+\. ' backend/tests/unit/test_vault_doc_roles.py | sort -u | wc -l
27
```

105 是参数化展开后的 pytest item 数，不是函数数。

### 开放项

BLOCKER：无。

HIGH

- 台账对生产支持的节点考题路径给出错误检索角色。[台账 `dir-jiedian`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:331)统一声明 `rag_retrieval: included`；真实写侧却会将 `节点/**` 下“无 `type`、含 `exam_question_id`”的文档推断为 `exam_board`，见 [lancedb_client.py:2740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2740)，随后被检索排除。真实代码探针：

  ```text
  ledger_entry= dir-jiedian
  ledger_rag_retrieval= included
  ledger_allowed_frontmatter= ['concept', '(none)']
  actual_chunk_doc_types= ['exam_board']
  ```

  checker 只看到允许的 `(none)`，不会发现最终 `doc_type` 推断造成的 retrieval 偏差。

- 声称的行级 schema 没有被生产 checker 完整执行。YAML [39–42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:39)声明 ID 全局唯一/kebab-case、`match` 结构必填、缺项即红；实际 `_verify_contract/_verify_entry` 未完整校验。内存变异结果：

  ```text
  duplicate_id=ACCEPTED
  empty_match=ACCEPTED
  governance_any_level=ACCEPTED
  ```

  即使同步刷新复制 checker 的 SHA，重复 ID 副本仍可在 `--enforce --no-probe --allow-degraded` 下得到 `0 finding / exit 0`。当前冻结 YAML 自身没有重复 ID；问题是生产契约弱于文字声明。

- `by_design_divergences.scope` 未校验。`scope="typo_scope"` 被接受，并在匹配代码中按任意层级处理：

  ```text
  divergence_scope_typo=ACCEPTED
  ```

  拼写错误会静默扩大分歧豁免范围。

MEDIUM

- `derived` 使用了两套冲突判据。YAML [108–112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:108)规定必须存在可重放 canonical 上游；Graphiti/Neo4j 行又保持 `derived`，同时承认部分 Episodic 历史内容不可恢复；思维导图行也承认用户批注无法重放。需明确“按产物族枚举”还是“按实例可重放性”分类，或拆分混合对象。

- JSON `checks_run` 与实际路径不符。代码实际在 no-probe 下仍执行 G8/G9/G10/G11，但 JSON 只报告 G1–G4：

  ```text
  actual_findings=[('G10', 'dangling.md')]
  json_checks_run=['G1', 'G2', 'G3', 'G4']
  ```

- `--no-probe` 的“全程零 import 副作用”不成立。`scan()` 无条件调用 `_writer_frontmatter_parser()`，后者尝试导入 `lancedb_client`，其模块初始化会运行 `jieba.initialize()` 并可能写系统临时缓存。未带 `--allow-degraded` 的声明 3 会提前退出，因此不受此问题影响。

- YAML 声称显式 frontmatter `type` 优先于视频路径推断；实际显式 `type: note` 仍会被视频路径覆盖：

  ```text
  frontmatter_chunk_doc_type= note
  is_video_transcript= True
  index_write_doc_type= video_transcript
  ```

LOW

- checker 称“七类 finding”，实际为 G1–G11 共 11 类。
- checker 零写入说明仍写 `rglob`，当前实现明确使用 `os.walk`。
- checker glob 文档称 DIV-2 使用 `*.[Mm][Dd]`，但 YAML 明确声明刻意不用该宽模式，实际为两个较窄 pattern。
- 测试头“语义钉死点”概览只列 1–24，正文另有 25–27；且写“九个必填字段”，实际 `REQUIRED_ENTRY_FIELDS` 为 10。计数声明本身仍属实。

结论：八条声明全部通过，但核心台账对生产 `doc_type/rag_retrieval` 路径存在错误事实，且 standalone checker 可接受违反其自述的 schema/豁免变异。因此本轮总裁定为需整改。全程未修改工作树或 live vault；生产依赖仅使用了系统临时缓存和 `/tmp` 副本。


