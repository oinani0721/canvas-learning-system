# CARD-G8-1 第三轮复核

总裁定：**需整改**。原冻结版本存在 2 个 BLOCKER，不能验收。

## 冻结完整性警报

开跑时三项 SHA-256 完全匹配，因此未触发“开头声明并停止”条件：

```text
$ shasum -a 256 backend/scripts/vault_doc_roles.yaml \
  backend/scripts/check_vault_doc_roles.py \
  backend/tests/unit/test_vault_doc_roles.py

a919ccad8542890646d62d762a1e6d9556ece648aa026667390b177c13d1369e  YAML
a8c2b1703765a18c30597a1119b30979cabb76f829871caeda935763ffc4a8fb  checker
991643012fb8f7e49b4f817c091b48a832520a15a186545c59d7fb3d7a31035b  tests
rc=0
```

但收尾重算时，三文件在 `2026-08-30 15:16:38 +0800` 同时发生漂移：

```text
cb5f9c230c52d8a1980862b4c8011958b7432a256d31ac4e65c087c50a0ae7f1  YAML
f6e8f08330f887ac4a25a3659682685a551b5ba2d741ffa8af6b593a1e75d088  checker
d48ee8e4d4ddc75e93d45cc805900b98b3329fe7ca9247fde61f329b0ead2962  tests
```

原字节与现字节的 `--numstat` 分别为：

```text
YAML     +2/-0
checker +17/-1
tests    +9/-0
```

因此：

- 以下所有结论**只绑定用户指定的原三 SHA**。
- 漂移发生后已停止新增探针；当前新字节未经本轮复核，不能继承本报告结论。
- 原字节仍保存在 [YAML 冻结副本](/tmp/card-g8-mutation-a.UyQEuz/backend/scripts/vault_doc_roles.yaml:1)、[checker 冻结副本](/tmp/card-g8-main-tests2/pytest/test_fingerprint_contract0/tamper/check_vault_doc_roles.py:1)、[tests 冻结副本](/tmp/card-g8-mutation-a.UyQEuz/backend/tests/unit/test_vault_doc_roles.py:1)。

## 逐项结论

| 项目 | 结论 | 核心原因 |
|---|---|---|
| 1 | NOT-CLOSED | 指定 symlink 已修，但目录 symlink 后代完全漏扫 |
| 2 | NOT-CLOSED | frontmatter 仍与真实写侧不等价，可绕过 G3/G4 |
| 3 | NOT-CLOSED | 四个指定结构对照已关；范围数字及其他空结构门不实 |
| 4 | NOT-CLOSED | role 归类自洽；“事件可重放当前态”不成立 |
| 5 | CLOSED | deny-file-write 下惰性 import 正确归入 ConfigError/rc=2 |
| 6 | NOT-CLOSED | 其余门已关，但根级 `*.md` 会静默误登记角色 |
| 7 | NOT-CLOSED | degraded 门已关；多 pattern 并集仍可形成 catch-all |
| 8 | CLOSED | 63 项基线通过；四个指定反向变异全部转红 |
| 9 | CLOSED | 无业务代码 delta；DIV-1、DIV-2 均保留 |

### 1) 路径解析稳定性：NOT-CLOSED / BLOCKER

指定场景已正确判红：

```text
$ backend/.venv/bin/python backend/scripts/check_vault_doc_roles.py \
    --enforce --vault /tmp/card-g8-runtime-fGN7TF/xrole

rc=1
双准入面实测分歧: 检验白板/alias-into-node.MD
G5 should_index=False(not_markdown) / check_vault_path=True(ok)
G6 不属任何已登记的 by_design_divergences
```

普通稳定路径仍保留 DIV-2：

```text
$ ...check_vault_doc_roles.py \
    --enforce --vault /tmp/card-g8-runtime-fGN7TF/plain

rc=0
双准入面实测分歧: 节点/PLAIN.MD
info: 命中已登记分歧类
✓ 无 finding
```

但存在第三类未判红情形：目录 symlink 后代不被 `Path.rglob` 递归。

```text
fixture:
检验白板/alias-node-dir -> ../节点
节点/PLAIN.MD

$ ...check_vault_doc_roles.py \
    --enforce --vault /tmp/card-g8-runtime-fGN7TF/dir-symlink

DIRLINK_CLI_RC=0
vault ... (4 目录 / 2 文件)
✓ 无 finding
```

真实函数与枚举对照：

```text
alias_child_exists True
rglob_contains_alias_child False
resolution_stable False
rag (False, 'not_markdown')
mem (True, 'ok')
```

该路径不是生产不可达：显式刷新接口会直接把请求路径交给 orchestrator，见 [index.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/app/api/v1/endpoints/index.py:125)。

另外，原冻结 YAML 实际没有声明所称的两个 `requires_resolution_stable: true`：

```text
$ rg -n requires_resolution_stable <冻结 YAML> <冻结 checker> <冻结 tests>

<冻结 checker>:849:
if div.get("requires_resolution_stable", True) and not resolution_stable:
```

```text
DIV-1-root-level-md explicit_key=False effective_default=True
DIV-2-md-suffix-case explicit_key=False effective_default=True
```

行为靠默认值暂时安全，但“显式声明”和配置结构门均未闭合，另计 MEDIUM。

### 2) frontmatter 对齐：NOT-CLOSED / BLOCKER

以真实 `LanceDBClient._parse_frontmatter` 与冻结 checker 同文件对照：

```text
file                    checker      writer effective
type : rogue            rogue        rogue
"type": x               x            x
type: Concept           concept      concept
TYPE: x                 (none)       note
bad YAML                (none)       note
CRLF delimiter          rogue_crlf   rogue_crlf
opening "---   "        (none)       rogue_open_space
closing "---   "        (none)       rogue_close_space
closing "..."           rogue_dot    note
missing closing marker  rogue_no_end note
type after line 400     (none)       rogue_after_400
```

对应 CLI：

```text
$ ...check_vault_doc_roles.py \
    --enforce --vault /tmp/card-g8-runtime-fGN7TF/frontmatter

FM_CLI_RC=1
G3/G4 只捕获:
  a-type-space.md
  b-quoted.md
  h-dot-end.md
  i-no-close.md
```

结论：

- (a) `type : rogue`、`"type": x`、`type: Concept`：CLOSED。
- (b) `TYPE: x` 不读取，与写侧一致：CLOSED。
- (c) 坏 YAML 回 `(none)`/默认 note：CLOSED。
- (d) 仍有真实漏判：首分隔符尾空白、结束分隔符尾空白、合法 frontmatter 超过 400 行。
- `...` 与缺少结束符则产生反向假阳性。

生产写侧见 [lancedb_client.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2142)。这些反例在允许 `(none)` 的 RAG 条目下会同时绕过 G3/G4。

### 3) H3 与 repo_docs：NOT-CLOSED

四个指定内存对照全部正确拒绝：

```text
$ python -B -c '<deepcopy load_rules; mutate; _verify_contract>'

drop_identifier|ConfigError|必须有 identifier
identifier_scalar|ConfigError|必须有 identifier
path_glob_empty|ConfigError|path_glob 必须是非空字符串列表
rag_index_string|ConfigError|rag_index 必须是 bool, 实际 "false"
rc=0
```

这四项局部门为 CLOSED。

“选定文档面、非 repo 全量普查”的定性范围是诚实的：卡片只要求覆盖 vault 现存目录/派生物并扫 live vault，见 [总账](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:367)。

但 YAML 的数量声明不实。按冻结 checker 自身 `glob_match` 复算：

```text
$ python3 -B -c '<git ls-files -z *.md; apply every repo_docs.path_glob>'

tracked_md=2428
repo_glob_covered=1460
uncovered=968
```

原声明是“约 1000 覆盖、1400+ 未覆盖”。

另有结构门缺口：

```text
$ python3 -B -c '<分别令 required 字段为空结构后调用 _verify_contract>'

owner None       ACCEPT
provenance []    ACCEPT
retention {}     ACCEPT
```

原因是这些字段仍以 `str(value).strip()` 验 truthiness，`None/[]/{}` 字符串化后非空。

### 4) H4 角色：NOT-CLOSED

角色集合机械复算：

```text
dir-claudian-sessions role=raw
  globs=['.claudian/sessions', '.claudian/sessions/**']

dir-claudian-config role=schema
  globs=['.claudian']

root-learning-events role=raw
  globs=['learning_events.jsonl']
```

`.claudian` 的会话实例为 raw、配置为 schema；`learning_events.jsonl` 是事件实例流而非 schema 定义，归 raw。两处与台账 roles 定义自洽，局部门 CLOSED。

但同段“frontmatter 可由事件流重放推导”不成立：

```text
$ nl -ba canvas-vault/.claude/skills/quiz-answer/SKILL.md | sed -n '285,355p'

316-319 先原子写节点 frontmatter
322-343 后追加 event；失败明确“不影响评分”
333-338 payload 仅含 grade_norm/exam_board/attempt_count
```

```text
$ nl -ba backend/app/services/learning_event_log.py | sed -n '59,105p'

68  append_event 永不抛异常
100 open(path, "a")
103-105 append 失败返回 False，主链不受影响
```

事件可在 frontmatter 已提交后丢失，payload 也没有 `mastery_a/mastery_b/fsrs_*` 最终态。因此：

- “两个真相源不是同一个对象”：成立。
- “事件流可重建 FSRS 当前态”：不成立，HIGH。

### 5) 严格只读预热：CLOSED

宿主 deny-file-write 沙箱实测全量 probe：

```text
$ sandbox-exec \
  -p '(version 1)(allow default)(deny file-write*)' \
  env PYTHONDONTWRITEBYTECODE=1 \
  backend/.venv/bin/python backend/scripts/check_vault_doc_roles.py \
  --enforce --vault /tmp/card-g8-runtime-fGN7TF/plain

[配置/环境错误] 真实准入函数首次调用失败
  No usable temporary directory ...
  严格只读环境请用 --no-probe --allow-degraded...
DENY_FULL_PROBE_RC=2
```

惰性 import 已在扫描前被预热调用捕获并转换为 ConfigError；不再中途以普通 `rc=1` 退出。

### 6) 其余处置：NOT-CLOSED

根级 `*.md` 论证不成立于“角色台账”维度：

```text
$ python3 -B -c '<resolve machine-generated-report.md and test DIV-1>'

is_catch_all(*.md)=False
resolved_id=root-loose-md
role=wiki
owner=用户 (根级散落笔记 / 审查记录)
none_allowed=True
div1_covers_true_false=True
```

因此一个新的无 type `machine-generated-report.md` 会：

- 不触发 G2/G3；
- 双准入分歧被 DIV-1 吞掉；
- 被静默登记为“用户 wiki、不可重建”。

“镜像真实 admission”只能证明 RAG 行为，不足以把所有未来根级 Markdown 的 owner/role/retention 泛化为用户 wiki。此子项 NOT-CLOSED / HIGH。

其余四项均 CLOSED：

```text
$ python3 -B -c '<resolve .quarantine/UAT-2.5.X-test.md>'

resolve_file_entry.id=root-uat-scratch
governance_scope=root_only
container.id=dir-quarantine
container.retention=保留至人工处置; 系统绝不自动清理或回收
```

扫描期 INFO 也明确深层实例治理以 `dir-quarantine` 为准，不再被解释为“可安全删除”。

```text
$ python3 -B -c '<recompute each doc_type roles from registered_by>'

note             declared=['raw','wiki']    recomputed=['raw','wiki']
whiteboard       declared=['raw']           recomputed=['raw']
exam_board       declared=['wiki']          recomputed=['wiki']
video_transcript declared=['raw']           recomputed=['raw']
concept          declared=['schema','wiki'] recomputed=['schema','wiki']
dashboard        declared=['derived']       recomputed=['derived']
contract=accepted
```

把 `dir-jiedian.role` 改为 `schema`：

```text
ConfigError: doc_type note ... 实际角色集 ['raw','schema','wiki'] 不符
```

冻结 YAML 还明确登记：

```text
git_dir_note: 校验脚本在目录与文件两个循环都无条件跳过 .git/
今日复习.md: review.py:599 只是注释；真实消费方读取今日复习.json
```

### 7) degraded 与 catch-all：NOT-CLOSED

降级门 CLOSED：

```text
$ ...check_vault_doc_roles.py --enforce --no-probe \
    --vault /tmp/card-g8-runtime-fGN7TF/plain

[拒绝执行] 会跳过 G5/G6/G7
REFUSE_RC=2
```

```text
$ ... --enforce --no-probe --allow-degraded --json ...

rc=0
"probe_skipped": true
"checks_run": ["G1","G2","G3","G4"]
```

人类输出也改为：

```text
⚠ 已跳过 G5/G6/G7
✓ 登记面无 finding（双列与真实函数是否一致：本次未验证）
```

单 pattern 语义门 CLOSED：

```text
?*     → ConfigError, rc=2
**/?*  → ConfigError, rc=2
```

但多 pattern 并集仍能绕过：

```text
$ python3 -B -c '<evaluate patterns over CATCH_ALL_PROBES>'

per_pattern [('**/.*', False), ('**/[!.]*', False)]
union_hits_all_probes True
_verify_contract ACCEPT
```

真实 CLI 对照：

```text
冻结配置，mystery/.secret 四目录:
FROZEN_CONTROL_RC=1
G1 4 条

将同一 dir_glob 改为 ["**/.*", "**/[!.]*"]:
UNION_MUTANT_RC=0
✓ 登记面无 finding
```

当前门只逐 pattern 判定，没有判断整个列表的 OR 并集，故整体 NOT-CLOSED / HIGH。

### 8) 测试有效性：CLOSED

冻结基线：

```text
$ PYTHONDONTWRITEBYTECODE=1 \
  TMPDIR=/tmp/card-g8-main-tests2 \
  backend/.venv/bin/pytest backend/tests/unit/test_vault_doc_roles.py \
  -q -p no:cacheprovider \
  --basetemp /tmp/card-g8-main-tests2/pytest

collected 63 items
63 passed, 13 warnings in 126.43s
rc=0
```

四项对照修改均令对应门转红：

```text
(a) 去掉 requires_resolution_stable 判断
test_cross_role_symlink_is_not_covered_by_registered_divergence
→ 1 failed, rc=1

(b) 改回严格 ^type: 正则
-k 'frontmatter_reader_matches_writer or rogue_type_variant_is_caught_by_scan'
→ 4 failed, 6 passed, rc=1

(c) 去掉 --allow-degraded 前置拒绝
test_degraded_gate_cannot_masquerade_as_full_pass
→ 1 failed: assert 0 == 2, rc=1

(d) is_catch_all 改回字面集合
test_catch_all_detection_is_semantic
→ 2 failed (?*、**/?*), 15 passed, rc=1
```

四个指定门都有效，因此本项 CLOSED；但这些测试未覆盖第 1、2、7 项的新反例。

计数文案有 LOW 偏差：

```text
$ python -B -c '<AST count top-level test_ functions>'

top_level_test_functions=24
```

实际是 24 个函数、20 个编号语义组、参数化后 63 个 item；文件头仍写“本文件 11 个”。

### 9) 业务代码与分歧保留：CLOSED

```text
$ git rev-parse HEAD cbb20afb

cbb20afb572a7b8ce9ebc205082e4be6de076fb8
cbb20afb572a7b8ce9ebc205082e4be6de076fb8
```

```text
$ git diff cbb20afb --stat
<empty>
rc=0
```

定向业务路径：

```text
$ git diff cbb20afb -- \
  backend/app/core/vault_admission.py \
  backend/app/services/vault_index_orchestrator.py \
  backend/lib/agentic_rag/clients/lancedb_client.py

<empty>
rc=0
```

`git status --short --branch` 显示交付物及审查文档均为 untracked；没有 `backend/app/`、`backend/lib/` 或前端业务文件：

```text
## card/t4-roles
?? _bmad-output/审查/...
?? _bmad-output/验收单/...
?? backend/scripts/check_vault_doc_roles.py
?? backend/scripts/vault_doc_roles.yaml
?? backend/tests/unit/test_vault_doc_roles.py
```

冻结台账仍含：

```text
count=2
DIV-1-root-level-md  rag_index=True  memory_write=False
DIV-2-md-suffix-case rag_index=False memory_write=True
```

因此没有把双准入面分歧当 bug 修改，也没有从台账删除。

## 新发现分级

BLOCKER：

1. 解析稳定性不是全局 fail-closed 不变量：目录 symlink 后代生产可达、真实 G5/G6 分歧，但 scanner `rc=0`。
2. frontmatter checker 与写侧仍不等价：尾空白分隔符及 400 行上限可令真实 rogue type 绕过 G3/G4。

HIGH：

1. 多个非 catch-all pattern 的并集可成为 catch-all，使 G1 恒绿。
2. 根级 `*.md` 可把新机器派生文档静默误归为用户 wiki。
3. `learning_events.jsonl` 可重放 FSRS 当前态的声明没有代码保证。

MEDIUM：

1. 原冻结 YAML 未显式声明 `requires_resolution_stable`，契约也接受缺失/软化。
2. repo_docs 数量声明错误；其他 required 字段仍接受 `None/[]/{}`。
3. YAML 声明 ID 全局唯一，但复制一个相同 ID 后 `_verify_contract` 仍 `ACCEPT`：

```text
duplicate_id=dir-chunks count=2 contract=ACCEPT
```

LOW：

1. 实际 24 个测试函数、20 个语义组，文件头仍写 11 个。
2. `read_frontmatter_type` docstring 仍称“解析失败回退正则”，实现实际返回 `(none)`。

本轮按生产入口、反例和 exact-byte 证据裁定；绿测只作索引。所有审计 fixture/变异均位于 `/tmp`。`graphiti-canvas` 本轮未暴露可调用工具，未进行 Graphiti 读写；这不影响上述文件级及生产函数复核。


