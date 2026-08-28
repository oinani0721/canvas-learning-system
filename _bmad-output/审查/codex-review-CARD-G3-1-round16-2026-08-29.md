## 终裁

- **CARD-G3-1：需再一轮。** 十五轮给出的具体反例均已被处理，但门整体仍有 **4 项 HIGH** 可复现绕过。
- **CARD-G3-4：仍保持可验收。** generator/manifest/vectors 零改动，全部指定回归通过。
- HEAD 精确为 `b6f11fb984ac2e4bca369f0bdbade2c49bcc4015`。
- 全程只读。审阅前后工作树均只有既存未跟踪 round16 审查稿，无 tracked 改动。

## 1. 十五轮三组 HIGH 重放

| 项目 | 独立重放结果 | 终裁 |
|---|---|---|
| 算法身份四输入 | `library_version="garbage"` 被报与 manifest 不同源；`params_hash="degraded:x"` 被拒；`scheduler_config={}` 被报非空对象违规；`reducer={}` 同时报缺 `id`、`precision`。[校验器:750](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:750) | 具体输入 **CONFIRMED-CLOSED**；门整体 **STILL-OPEN** |
| genesis 引号键 | frontmatter 为 `"fsrs_state": 2` 时，报顶层 FSRS 键违规；block scalar 内同文字不误报；空 frontmatter 合法。[校验器:566](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:566) | 具体输入 **CONFIRMED-CLOSED**；门整体 **STILL-OPEN** |
| genesis 历史行 | L1 无扩展 `answer_scored`、L2 为 `review/1`、`first_event_line=2`，同时报历史不完整及实际最早行为 1。[校验器:851](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:851) | **CONFIRMED-CLOSED** |
| 两次读取追加竞态 | `Path.read_bytes` 设为依次返回 `L1`、`L1+L2`，实际只调用 1 次，第二份未消费；若首份已含 L2，则正常触发尾部违规。递归 proof 也是 `read_count=1, scan_count=1`。[校验器:997](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:997) | **CONFIRMED-CLOSED** |

因此，十五轮 **HIGH 3 单快照已完全闭合**；HIGH 1、HIGH 2 的原反例闭合，但相应安全门仍有其他缺口。

## 2. proof 逐门更新

| proof 门 | 结论 |
|---|---|
| 12 个顶层必填字段 | **CONFIRMED-CLOSED** |
| cursor/E/event_id/review_time 绑定；时间语法、域、整秒 | **CONFIRMED-CLOSED** |
| node_id 与链上身份 | **CONFIRMED-CLOSED** |
| vault_id 与事件绑定 | **STILL-OPEN**：混合 vault、缺失 vault 可绕过 |
| prefix 精确 bytes、LF 规则 | **CONFIRMED-CLOSED**，且基于同一快照 |
| algorithm/version/hash/config | **STILL-OPEN**：JSON 类型等值和 manifest 不可达分支 |
| reducer `id`/`precision` | **CONFIRMED-CLOSED** |
| result/state canonical hash | **CONFIRMED-CLOSED**，仅指所附状态的自洽 hash；按声明不复算 FSRS 折叠 |
| 状态键集、类型、数值域 | **CONFIRMED-CLOSED** |
| snapshot 三等式 | **CONFIRMED-CLOSED** |
| 区间、行序、层内/跨层单调 | 核心比较 **CONFIRMED-CLOSED**；端到端因扫描器可隐藏行而 **STILL-OPEN** |
| 链终止、身份一致、cursor 递减、防循环/深度 | **CONFIRMED-CLOSED** |
| genesis | **STILL-OPEN**：无 PyYAML 时可漏键，且 `unextended_lines` 误拒非复习事件 |
| top-level 尾部覆盖 | 比较逻辑 **CONFIRMED-CLOSED**；端到端因 `out_of_order:false` 可被隐藏而 **STILL-OPEN** |
| 区间 degraded 哨兵 | **CONFIRMED-CLOSED**；双哨兵会重复记录同一行号，仅属诊断瑕疵 |

## 3. 新规范偏差与绕过

### NEW-FINDING / HIGH — 算法身份仍非严格 JSON 同源

实现用 Python dict equality：[校验器:793](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:793)。

具体输入：

```json
"enable_fuzzing": 0
```

manifest 中为 JSON `false`，[manifest:23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/fsrs_golden_manifest.json:23)。Python 判 `0 == False`，完整 proof 返回 `[]`。`learning_steps_minutes=[true,10]` 对 `[1,10]` 同样可过。

manifest 不可达时更严重：使用合法形状版本、任意 64-hex hash，并让六个必要配置键全部取 `0`，即可返回 `[]`；实现只查键存在。[校验器:764](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:764)

这与 §6.2“须与 G3-4 manifest 同源”不一致。[schema:219](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:219)

关于旧版本：manifest 可达时 `6.2.0` 会被拒。按当前 schema，这不是实现过严；当前规范本身只接受当前 G3-4 manifest。若需要历史版本重建，应在 schema 中增加不可变 manifest digest/版本寻址，而不是简单放宽比较。

### NEW-FINDING / HIGH — `out_of_order:false` 隐藏尾部事件

扫描器判断的是“键是否存在”，不是值是否严格为 `true`：[校验器:510](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:510)。

复现：

- L1：正常 `review/1`
- L2：同节点正常 `review/1`，但 `payload.out_of_order=false`
- proof cursor 指向 L1

结果：L2 被扫描器排除，公开 ledger 模式返回 `[]`，尾部逃逸。主体文件校验器会拒绝 `false`，但 proof 入口没有先执行完整记录语义校验。

### NEW-FINDING / HIGH — vault 绑定只做集合成员关系

[校验器:641](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:641) 只要求 proof vault 存在于扫描所得集合。

两个反例均返回 `[]`：

- L1 `vault=A`、L2 `vault=B`，cursor 指向 L2，但 proof 仍写 `vault=A`。
- 适用行全部缺 `vault_id`，proof 可填任意 `claimed`。

应按 proof 的 vault 过滤事件，或要求扫描集合严格等于 `{proof.vault_id}`。

### NEW-FINDING / HIGH — 无 PyYAML fallback 漏检合法转义键

强制 PyYAML 不可用，frontmatter 为：

```yaml
"fsrs_\u0073tate": 2
```

YAML 语义键为 `fsrs_state`；PyYAML 路径能识别，第 0 列正则 fallback 返回空键集，完整 proof 返回 `[]`。[校验器:573](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:573)

schema 没有授权依赖不可达时削弱 genesis 门。该路径应 fail-closed，或把 PyYAML 明确列为 proof 必需依赖。

### NEW-FINDING / MEDIUM — `unextended_lines` 误拒合法非复习事件

实现把同节点的任何非 `review/1` 事件都列为历史不完整：[校验器:503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:503)。

复现：

- L1：合法同节点 `callout_ingested`，普通 payload
- L2：合法 `answer_scored review/1`
- `first_event_line=1`

两条记录分别通过主体校验，但 new-card proof 被拒。§6.2 要求的是“全部**复习事件**都带 `review/1`”，不是全部节点事件。[schema:250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:250)

### NEW-FINDING / MEDIUM — `bad_lines` 口径不完整

无法解析的行会全局阻断，即使文本看似属于另一节点。这是保守的 fail-closed：坏行无法可信确定节点，且全局账本本身已不合法。

但范围存在两处缺口：

- 空行在 scanner 中直接跳过，主体校验器却判违规。
- 可解析但语义非法的记录不会进入 `bad_lines`。

因此当前只能声称“无法解析的行全局 fail-closed”，不能声称“所有坏账本行都 fail-closed”。§6.2 还应明确 proof 是否以前置“账本已通过完整 schema 校验”为条件。

## 4. 单快照完整性

当前实现本身 **CONFIRMED-CLOSED**：

- 全文件唯一实际 `read_bytes()` 位于 [_ledger_bytes:537](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:537)。
- 公开入口只读一次并把同一 `ledger_raw` 交给 scan 和 prefix。
- `ledger_prefix(raw, n)` 消费该 bytes，不重新打开路径。
- snapshot 递归复用同一 `scan` 与 `ledger_raw`。[递归:900](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:900)

不过现有测试只做源码字符串 `count("read_bytes()")==1`，不能防两次 `.open().read()`，也没有递归 scan 复用行为门；实现正确，但回归保护不足。

## 5. 测试有效性

实跑结果：

- contract：`130 passed, 1 skipped`
- golden：`19 passed`
- 既有 `test_learning_event_log.py`：`6 passed`
- 三文件同进程合跑：`155 passed, 1 skipped`
- `tests/unit/test_fsrs_manager.py`：`37 passed`
- G3-4 UAT 明列的 11 个 FSRS 文件：`191 passed`

第十七笔 contract 展开约 30 个 case。未发现纯恒真断言；golden bool/NaN 门会真实调用主门，独立钉死 digest 也不是从被测实现生成。弱点是 [mixed naive/aware 测试:1639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1639) 只写 `assert problems`，未锁错误原因。

A–G 七个声明分支的进程内等价 mutation 均只让预期项变红。但另有五个关键 survivor：

| 破坏 | 结果 |
|---|---|
| earliest 退回最早适用行，不用 `node_event_lines` | contract 仍 `130+1` 全绿 |
| 改为两次 `.open().read()` | 单快照测试仍绿 |
| snapshot 递归丢弃共享 scan/raw | contract 仍全绿 |
| 删除 stability 上界 | 域测试仍全绿 |
| 区间扫描不查 params-hash 哨兵 |相关 9 个测试仍全绿 |

因此测试结论是 **PARTIAL**，不能证明所有新增分支承重。缺少的关键行为门正好覆盖本轮发现的 config 类型、manifest 不可达、`out_of_order:false`、无 PyYAML escape、非复习历史行、mixed/missing vault、递归复用、stability 上界及 params 哨兵。

## 6. 负验证脚本

按只读要求，未执行会原地修改 tracked 文件的脚本；仅做静态审阅及进程内等价 mutation。

- A–G 七个 Perl 模式在当前实现中均恰好命中 1 处。
- 等价 mutation 结果分别为 `A 1F/1P、B 1F/1P、C 1F、D 1F、E 1F/2P、F 1F/1P、G 1F/7P`，当前确实命中预期门。
- `expect_red` 已检查 exit code、collection 数与预期 FAILED 行，但不拒绝额外 FAILED/ERROR，因此可能把连带失败误判为“恰好对应门承重”。[脚本:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:48)
- `mutate()` 只比较修改前后 SHA，不验证命中次数；未来模式命中两处仍会通过。[脚本:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:34)
- `mktemp`、初始备份及逐次 `cp` 未检查返回码，脚本也未启用 `set -e`。
- 末尾还原检查在工程上有效，但机制是 SHA-256 相等，不是 `cmp` 式逐字比较；并且依赖最初备份成功。[脚本:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:143)

结论：七变体当前有效，但脚本的“三重判据”和“逐字相同”声明仍略强于其机械保证。

## 7. 范围声明与文档一致性

- schema §6.2 与函数 docstring 当前都列出四项限制：不复算 FSRS、不从折叠结果复算 `result_hash`、不绑定真实节点文件、快照后追加不在判定内。[schema:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:203)、[docstring:981](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:981)
- **NEW-FINDING / LOW**：schema 仍记录已经不存在的公开 `is_top_level=True` 签名。[schema:201](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:201)
- **NEW-FINDING / LOW**：模块级范围注释仍只有三条，并称传 `ledger_path` 即“消除信任边界”；鉴于扫描器并不做完整记录语义校验，该措辞过强。[校验器:327](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:327)
- G3-1 UAT 的历史范围段仍只写“结构与分层”，与后文“已扩成四条”内部不一致。[G3-1 UAT:267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:267)
- G3-4 UAT 没有对 proof verifier 作扩大声明，其 golden 覆盖范围表述本身诚实。

## 8. 回归、对象与账本一致性

- `425f8564..HEAD` 对 generator/manifest/vectors 的 name-status diff 为空。
- Git blob：

  - generator `9d6ab4f63b326dc3f604cb794ce9fd9e42de792e`
  - manifest `b59f331d9a1f57e5778fd82399ef12b61eb0c967`
  - vectors `33c601995d5274f7702a4d0ce501d2b81311d688`

- manifest SHA-256 `82eaaffa2a064064140916a272e8b4d4256fe4bd58cdb4914c4793646af3cb09`；vectors SHA-256 `df60dbc6192c499ad21da6533f35ed2e0e316f5d4bc52fb45b711d4cae6f49a3`。`generate()` 内存序列化与仓库两份 JSON 字节相同。
- 锁定 blob 精确匹配：

  - [learning_event_log.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/services/learning_event_log.py) `28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
  - [fsrs_manager.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/lib/memory/temporal/fsrs_manager.py) `980b3758758b1d78d6795451c76270c10713cc60`

- 现网账本实际在主 checkout，共 23 行；公开 CLI exit 0、`RESULT: PASS`。前后 SHA 均为 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`。
- G3-1 UAT 的 `130+1 / 6 / 155+1` 正确。
- **NEW-FINDING / LOW**：G3-4 UAT 顶部列出的 191 正确，但末尾写 179；CURRENT_TASK 同样写 179。[G3-4 UAT:26](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:26)、[G3-4 UAT:157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:157)
- **NEW-FINDING / LOW**：CURRENT_TASK 仍称“第十七笔待提交”，但 HEAD 本身就是第十七笔。[CURRENT_TASK:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:5)
- G3-1 UAT 的“git diff 只含新增文件……”缺少基线，且对 `425f8564..HEAD` 不成立。[G3-1 UAT:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:40)

## 残留清单

- **BLOCKER：0**
- **HIGH：4**

  1. 算法身份 JSON 类型碰撞及 manifest 不可达时任意身份。
  2. `out_of_order:false`/语义坏行可从 proof 扫描中隐藏，绕过尾部。
  3. 无 PyYAML fallback 可漏掉 YAML escaped FSRS 键。
  4. mixed/missing vault 不能与 cursor 事件唯一绑定。

- **MEDIUM：4**

  1. 非复习事件被 `unextended_lines` 误拒。
  2. proof 对“完整合法账本”的前置条件及 `bad_lines` 口径未冻结。
  3. 五个关键实现破坏可在现有 contract 测试下存活。
  4. 负验证脚本不保证唯一命中、唯一失败，备份/恢复返回码保护不足。

- **LOW：4**

  1. schema 仍记录旧 `is_top_level` 公共签名。
  2. 模块注释、G3-1 UAT 与函数 docstring 的范围声明不一致。
  3. G3-4 UAT/CURRENT_TASK 的 179/191 数字及提交时态过期。
  4. 双 degraded 字段会重复报告同一行号。

最终结论：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。**

附带环境限制：当前会话未暴露 `graphiti-canvas` MCP，因此无法执行 AGENTS.md 要求的 Graphiti memory search；代码、对象、测试及账本结论均已直接从当前 checkout 重新复算。


