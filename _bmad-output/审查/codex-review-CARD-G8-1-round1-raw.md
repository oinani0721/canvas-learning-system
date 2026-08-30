# 总裁定：需整改（FAIL）

绑定最终审查快照：

- HEAD：`cbb20afb572a7b8ce9ebc205082e4be6de076fb8`
- YAML：`b3af310fe95ce567852cbe9ce23efc97be9cdb87846ae035718b661c1867a7fb`
- checker：`8af0ebe0bfe8f3a3e5f6cf18a8c9fd1be09b2ef11edf32f366c55eaa50ec52a9`
- tests：`10a93e5e67a8f086236ae82c70c313d5d8ff3d0fe1c6330bd91f076147104518`

审查期间三件套曾被外部并发改写；以下结论只针对上述最终字节。我未修改仓库或 live vault；测试及反例仅使用经审批的系统临时目录。

## 逐项裁定

| 项目 | 结论 | 复算证据 |
|---|---|---|
| (a) 全覆盖 | **NOT-CLOSED** | live vault 当前 `175 dirs / 324 files / 0 unresolved`，指定派生物均有登记；但 repo tracked Markdown `2428` 个仅匹配 `1460`，遗漏 `968` 个；且现存隔离区文件被错误规则优先级归类。 |
| (b) 每行字段与语义 | **NOT-CLOSED** | vault/root/derived 共 42 行，字段缺失 `[]`；但 repo_docs 被排除于完整契约，[checker:331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:331)，且六个 repo 行没有 `match/frontmatter_type`。多行 role/retention 自相矛盾。 |
| (c) doc_type 白名单 | **NOT-CLOSED** | 六个名字确已登记，但 Dashboard 不是 census 第六行；更严重的是有效 YAML 写法能绕过裁判，生产写侧仍会写入任意 `rogue` 值。 |
| (d) checker 契约 | **NOT-CLOSED** | SHA 先于 YAML 解析为 CLOSED；但“未登记类型”存在漏报，且严格不可写环境下真实入口 exit 1。 |
| (e) 测试及 live 跑通 | **NOT-CLOSED** | 当前独立复跑 `28 passed in 35.35s`，普通临时目录环境下 live checker exit 0、vault SHA 不变；但测试不能先红覆盖 G5/G6/G7、frontmatter 解析旁路和 transitive import 写副作用。 |
| R1 禁止修平业务分歧 | **CLOSED** | 四个敏感文件对 HEAD 的 `git diff --exit-code` 输出为空、exit 0。 |
| R2 DIV-1 如实登记 | **CLOSED**，有 LOW 误述 | 核心 `RAG=true / memory=false / by-design / 只登记不修` 正确。 |
| R3 DIV-2 精确性 | **NOT-CLOSED / HIGH** | patterns 本身精确，但真实 DIV-2 实例仍被 G5 判红，登记无法兑现。 |
| R4 known_gaps | **CLOSED** | 唯一 GAP 的 `finding_codes=[]`；G4–G7 不可豁免。 |
| R5 反软化 | **NOT-CLOSED / HIGH** | `root-loose-md: ["*.md"]` 是根级 Markdown 实质 catch-all。 |
| A 指纹先于解析 | **CLOSED** | [checker:229-249](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:229) 先读 bytes、比 SHA，之后才 import/parse YAML。 |
| B 零写入 | **NOT-CLOSED / HIGH** | live vault 零修改为 CLOSED；“脚本/import 绝对零写入”不成立。 |
| D Dashboard 差异披露 | **CLOSED（仅披露）** | 台账明确承认 census 第六行是空串/自由值，并非 dashboard；不是措辞遮掩。但这不等于两套六值已对齐。 |
| E 先红能力 | **NOT-CLOSED / HIGH** | 有 G1–G4、SHA、字段等负例；无 G5/G6/G7 端到端断言，且当前存在实际漏报反例。 |

## BLOCKER

### 有效 YAML frontmatter 可绕过“未登记类型”裁判

裁判只接受行首严格的 `type:`：

- [_FM_TYPE_RE，checker:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:140)
- [read_frontmatter_type，checker:375-391](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:375)

生产写侧却使用完整 `yaml.safe_load`，随后读取字典键：

- [lancedb_client.py:2142-2172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2142)
- [lancedb_client.py:2738-2758](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2738)

独立解析复算：

```text
'type: rogue'   checker='rogue' writer_yaml='rogue'
'type : rogue'  checker=None    writer_yaml='rogue'
'"type": rogue' checker=None    writer_yaml='rogue'
```

端到端临时 vault 反例：

```text
节点/rogue.md 内容:
---
type : rogue
---

checker_type (none)
entry dir-jiedian
findings []
```

`dir-jiedian` 允许 `(none)`，[YAML:301-317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:301)，因此 G3/G4 均不触发；生产索引器却会写 `doc_type=rogue`。这直接击穿 (c)/(d)。

## HIGH

1. **DIV-2 登记与机械裁判不相容。**  
   Patterns `["**/*.M[Dd]", "**/*.[Mm]D"]` 精确覆盖 `.MD/.Md/.mD`，不覆盖 `.md`，[YAML:160-177](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:160)。但 `节点/FOO.MD` 先按 `dir-jiedian` 声明为 `true/true`，扫描器在 [checker:517-523](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:517) 产生 G5；DIV-2 只在 [checker:525-534](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:525) 抑制 G6。生产入口反例：

   ```text
   divergent ['节点/FOO.MD']
   findings [('G5', '节点/FOO.MD',
     'dir-jiedian 声明 true/true，真实 false(not_markdown)/true(ok)')]
   ```

2. **根级 `*.md` 实质 catch-all。**  
   [YAML:676-705](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:676) 将任何未来无 type 根级 Markdown 归为 `wiki/true/false`；反软化门只禁几个裸字符串，[checker:134-135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:134)。端到端反例：

   ```text
   future-secret.md
   entry ('root-loose-md', 'wiki', True, False)
   divergent ['future-secret.md']
   findings []
   ```

   当前没有 frontmatter 通配符，这一子项 CLOSED；问题是文件 glob 本身把未来新类别吞掉。

3. **解析优先级导致当前隔离文件角色和生命周期错误。**  
   resolver 先执行 `root_files(scope:any_level)`，再执行目录规则，[checker:354-364](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:354)。实算：

   ```text
   .quarantine/UAT-2.5.X-test.md
     => root-uat-scratch / wiki / 可安全删除
   raw/CS188/_misc/junk/未命名.md
     => root-untitled-scratch / wiki / 可安全删除
   ```

   但 `.quarantine` 明确要求 `raw / 保留至人工处置 / 系统绝不清理`，[YAML:489-503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:489)。checker 因双准入布尔值恰好一致而仍然绿。

4. **repo 文档登记不完整，且不受完整 schema 约束。**  
   六个 globs 位于 [YAML:1027-1083](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:1027)。独立匹配：

   ```text
   tracked_md 2428
   covered    1460
   uncovered   968
   ```

   遗漏样例：`.claude/agents/**`、`.claude/commands/**`、`CURRENT_TASK.md`、`PRD.md`、`_bmad/**`、`_decisions/**`。其中 `_decisions` 还是项目明确列出的项目文档，[CLAUDE.md:124-135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/CLAUDE.md:124)。测试只断言 `len(repo_docs)>=5`，[test:139-144](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/tests/unit/test_vault_doc_roles.py:139)。

5. **角色真相源存在内部矛盾。**

   - `note` 唯一定义为 `wiki`，却注册到 `dir-raw`、课程 raw 目录，[YAML:946-952](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:946)。
   - `raw/my-recursion-notes.md`、`CS188/lecture 4/lecture 4.md` 实测均无 type、路径不含 `/videos/`；按 [lancedb_client.py:1771-1777](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:1771) 与 [:2891-2893](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2891) 会写 `doc_type=note`，但台账文件角色是 raw。
   - derived 定义要求 canonical 上游可重放，[YAML:108-112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:108)；`.claudian` 和 `learning_events.jsonl` 却同时声明“无上游、删除不可恢复”，[YAML:475-487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:475)、[YAML:553-570](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:553)。

6. **“绝对零写入”不成立。**  
   constructor 本身仅赋值和构造 Path，[orchestrator:98-123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/app/services/vault_index_orchestrator.py:98)，这一点 CLOSED。但 checker 导入 [app/services/__init__.py:5-29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/app/services/__init__.py:5) 的完整服务图；LanceDB 模块在 import 时调用 `jieba.initialize()`，[lancedb_client.py:75-82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:75)，Jieba 会创建/替换临时缓存。

   严格不可写环境实跑：

   ```text
   LiteLLM 尝试远程 model-cost 请求
   FileNotFoundError: No usable temporary directory
   checker exit=1
   live digest before=after:
   324 2d4a818d...de0ea0c
   ```

   普通可写系统临时目录中则 exit 0。因此“未写 live vault”成立；“脚本/import 零写入”不成立。

7. **测试不能证明 G5/G6/G7 先红。**  
   当前测试构造并断言 G1–G4，[test:235-279](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/tests/unit/test_vault_doc_roles.py:235)；G5 只测试“不允许豁免”，G6 只直接测试 helper，[test:506-520](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/tests/unit/test_vault_doc_roles.py:506)，没有 G7 端到端反例。删除扫描器的 G5/G6/G7 `add()` 分支，现有主要断言仍可能全绿。零写入测试也只正则扫描 checker 自身，[test:389-420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/tests/unit/test_vault_doc_roles.py:389)，不检查 import 图。

## MEDIUM / LOW

- **MEDIUM：LanceDB live 表事实已漂移。** 台账称容器中 `active_vault_*` 与 `canvas_vault_*` 四张表并存，[YAML:852-868](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:852)。只读容器复算：

  ```text
  tables [
    'canvas_vault_file_fingerprints',
    'canvas_vault_vault_notes',
    'file_fingerprints'
  ]
  ```

  实际是三张，没有 `active_vault_*`。

- **MEDIUM：`今日复习.md` consumer 断言不实。** 台账称 `endpoints/review.py` 消费该文件，[YAML:729-742](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:729)；代码只有注释，[review.py:597-599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/app/api/v1/endpoints/review.py:597)。真实生产读取面使用 `今日复习.json`。

- **MEDIUM：`.git` 是机械裁判硬跳过盲区。** 目录和文件循环均直接 `continue`，[checker:452-465](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:452)。当前 live vault 没有 `.git`，故不是当前漏计，但未来出现时不会触发 G1/G2。

- **LOW：DIV-1 其余九个根文件的 reason 误述。** [YAML:157-159](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:157) 称两面都因文件名黑名单拒绝；memory 面在黑名单前就返回 `root_level`，[vault_admission.py:89-115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/app/core/vault_admission.py:89)。布尔结论仍正确。

## C：12 条事实独立复算

| # | 台账事实 | 复算结果 |
|---:|---|---|
| 1 | live 目录/文件 | `175 dirs / 324 files / 214 md / 13 root files` |
| 2 | 当前覆盖 | `uncovered_dirs=[] / uncovered_files=[]` |
| 3 | frontmatter 分布 | `(none)=174, concept=17, exam_board=11, whiteboard=6, recap=4, dashboard=1, mockup=1` |
| 4 | 今日复习 | JSON `1`、Markdown `1` |
| 5 | recap / Excalidraw | recap md `4`、`.recap-scan` `4`、`.recap-manifest` `4`、思维导图 Excalidraw md `3` |
| 6 | 台账结构 | `vault_entries=21, root_files=10, derived=11, repo_docs=6, known_gaps=1`；42 个完整契约行缺字段 `[]` |
| 7 | 分歧行 | 仅 `root-loose-md true/false`，且 `divergence_reason` 非空 |
| 8 | live DIV-1 | checker 实测仅 `chatgpt-adversarial-review-Q1Q2Q3-2026-05-12.md` 一条 |
| 9 | known_gaps | `[('GAP-1','CS188',[])]`，没有 G4–G7 豁免 |
| 10 | 黑名单 | immutable 9 项；文件黑名单 10 项 + root-only `excalibrain.md`，与源码 [lancedb_client.py:427-485](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:427) 一致 |
| 11 | Neo4j/Graphiti | 只读查询得 `12 distinct groups / 35 Episodic`，与 [YAML:876-913](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:876) 一致 |
| 12 | LanceDB | 台账称四张 namespaced 表；实际仅上述三张，**不一致** |

## D：Dashboard 与 census

差异披露本身是 **CLOSED**：

- census 第六行确实是“空串/自由值”，并明确裁定“值域未闭合”，[census:48-57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/_bmad-output/审查/G4-16-doc-type-census-2026-08-28.md:48)。
- 台账明确写出 dashboard 不是 census 第六行、当前没有进入 LanceDB，[YAML:988-1001](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:988)。

所以不是措辞遮掩；但也不能据此声称“两套六取值对齐”。一个是具体 frontmatter 值，另一个是无限自由值面。(c) 仍为 NOT-CLOSED。

## 验证结果汇总

```text
pytest:
28 passed, 10 warnings in 35.35s

普通临时目录环境 live checker:
175 dirs / 324 files
1 divergence
0 findings
exit=0

live vault 聚合 SHA:
before = 324 2d4a818d5bbe682ec38b6b8dd42fae7ee0c084a00e800ee023cb179dfde0ea0c
after  = 324 2d4a818d5bbe682ec38b6b8dd42fae7ee0c084a00e800ee023cb179dfde0ea0c
```

绿测试和当前 live 零 finding 均属实，但不足以覆盖上述 BLOCKER/HIGH。按“任一完成条件不达标即 FAIL”，CARD-G8-1 当前不可验收，需整改。


