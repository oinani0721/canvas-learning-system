终裁：`HEAD=e013102fedb87a4ed4ae238f1f33c81c236f53f7` 已确认。第十三轮点名的三项整改本身成立，但发现新的可复现绕过：

- CARD-G3-1：`STILL-OPEN / 需十五轮`
- CARD-G3-4：原 `CONFIRMED-CLOSED` 被新发现推翻，`STILL-OPEN / 需十五轮`
- BLOCKER：0

## 一、CARD-G3-1

### 1. 原 HIGH 的层级作用域：CONFIRMED-CLOSED（窄义）

Schema 已明确尾部约束只施于最外层 proof；递归 ancestor 固定不施加。[schema:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:197) [verifier:444](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:444) [verifier:482](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:482)

正常两层链通过、反序分层链被跨层门拒绝。该特定歧义已闭合。

### 2. HIGH / NEW-FINDING：参考 verifier 可接受明显违规 proof

Schema 明定表中字段缺一即不可证明，并要求算法身份、完整配置、reducer、账本 prefix、事件身份和 genesis 真锚。[schema:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:204) [schema:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:208) [schema:243](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:243)

实现却只检查若干字段为非空字符串，既不复算 prefix，也不绑定 event_id、genesis 原文/hash 或最早行。[verifier:427](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:427) [verifier:455](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:455) [verifier:530](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:530)

最小反例实测返回 `[]`：

```python
proof = {
    "vault_id": "v", "node_id": "n", "event_id": "e2",
    "review_time": t2, "cursor_line": 2,
    "ledger_prefix_sha256": "x", "result_hash": "x",
    "origin": {
        "kind": "new_card",
        "genesis_evidence": {
            "node_frontmatter_hash": "not-a-sha256",
            "node_frontmatter_text": "fsrs_state: 2\n",
            "first_event_line": 2,
        },
    },
}
verify_degraded_proof(proof, [(1, t1), (2, t2)])  # []
```

它同时缺少 `fsrs_library_version`、`fsrs_params_hash`、`scheduler_config`、`reducer`，genesis 原文还明确含 FSRS 状态。

`applicable` 信任边界也不足：

```text
完整 [(1,t1),(2,t2)]  -> 报尾部未覆盖
截断为 [(1,t1)]       -> []
显式 is_top_level=False -> []
```

函数仅称该列表“由调用方抽取”，未声明完整性、事件身份、payload、prefix bytes 均未自行核验。[verifier:409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:409) CLI 入口也没有调用 proof verifier。[validator:968](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:968)

### 3. 逐门对照

| 判据 | 结论 |
|---|---|
| 左开右闭、按行号升序 | `CONFIRMED-CLOSED`，实现于 [508-514](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:508) |
| 层内/跨层严格单调 | `CONFIRMED-CLOSED`，前提是调用方给出的 `applicable` 完整可信 |
| 三等式 | `PARTIAL`：等式 1/2 正确；等式 3 错用原字符串比较 |
| 链递减/自引用 | `PARTIAL`：递减有效，但额外引入未成文的 64 层上限 |
| genesis 锚 | `FAIL`：只查非空，不验 hash、原文无 `fsrs_*`、最早行 |
| prefix/LF | `FAIL`：不复算 bytes；不能判断何时必须写/省略 `prefix_ends_without_lf` |
| 状态键集和值类型 | `PARTIAL`：键集/int/bool/float/finite 正确；时间只验正则 |
| 算法身份/config/reducer | `FAIL`：甚至不要求字段存在 |

### 4. 其他 verifier 缺陷

- `MEDIUM`：Schema 要求所有 `W/review_time` 相等比较按绝对瞬间。[schema:138](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:138) 实现却直接比较字符串。[verifier:489](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:489)

  ```text
  ancestor.review_time = 2026-01-01T18:00:00+08:00
  state.fsrs_last_review = 2026-01-01T10:00:00Z
  实测：['等式3失败...']
  ```

  两者为同一瞬间，属于合法 proof 假阳性。

- `MEDIUM`：canonical 时间仅由正则检查。[verifier:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:341) `2026-99-99T99:99:99Z` 和末尾带真实换行的 `...Z\n` 均得到 canonical bytes/hash 且 `problems=[]`。

- `LOW`：Schema 只要求严格递减并最终终止，没有 64 层限制。[schema:248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:248) 实测 65 层通过、66 层因 `_depth > 64` 被拒。[verifier:418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:418)

- `left is None`、空 interval、`ancestor_end is None` 均至少留下违规，不会空通过。自引用对象会被深度门抓住；但混合 naive/aware 的不可信 `applicable` 可在跨层比较处抛 `TypeError`。

### 5. 14 条测试及负验证

- 精确选中并实跑：`14 passed, 56 deselected`。
- 三等式等负例均查具体 marker，不是真空的“只要有违规”。
- 但正例 helper 本身缺四个 schema 必填字段并使用非 SHA `result_hash`，却要求 `[]`。[test:1075](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1075) [test:1119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1119)
- Hash 门同源循环：`_layered()` 用被测 `state_hash()` 生成 oracle，稳定性测试也只比较同一函数两次。[test:1096](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1096) [test:1195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1195) 将 `state_hash` 内存替换为恒返回 `"0"*64` 后，14/14 仍通过。正确已知 digest 应为 `4f26831a0f4e60998f463ca6ed5091831e5ad7cba9e242789ad23acccc1e3b57`。

负验证存档当前内容与三道门的实际行为一致，但脚本不是可靠的机械门：

- 只有 `set -uo pipefail`，没有 `-e`；[script:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:11)
- Perl 替换不检查命中次数；
- `run()` 只 grep 输出，不断言必须失败及失败门名。[script:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:20)

令三个替换模式失配时，A/B/C 全绿，脚本最终仍 `exit 0`。正常退出时 backup、逐变体 `cp` 和 `EXIT` trap 能恢复当前 bytes；SIGKILL/掉电不保证。为遵守只读，本工作树未原地执行该脚本。

### 6. 范围声明：PARTIAL

Schema 与函数前置注释都明确“不复算 FSRS”“空违规不等于 proof 成立”。[schema:201](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:201) [validator:329](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:329)

但真正的函数 docstring 没有这一限制，反写“空 = 结构上可证明”。[verifier:407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:407) 而且“空违规”现在连完整结构成立也不能表示。对 reducer 的限制声明足够；对 `applicable`、账本 bytes 和 genesis 信任边界不够。

## 二、CARD-G3-4

### 正向锚点：全部确认

- `e013102f^..e013102f` 未触碰 generator、manifest、vectors、golden test 或两份 requirements。
- `generate()` 内存输出与仓库 JSON 逐字节相同：
  - manifest SHA-256 `82eaaffa2a064064140916a272e8b4d4256fe4bd58cdb4914c4793646af3cb09`
  - vectors SHA-256 `df60dbc6192c499ad21da6533f35ed2e0e316f5d4bc52fb45b711d4cae6f49a3`
- `params_hash=7b28ae29ac876981a7fca1424772214c7a4d9884439efd678ecb60e615b00342`
- 20 vectors、20 唯一 ID、3 个 retrievability 点。
- 两份 requirements 仍为 `fsrs==6.3.1`：[root requirements:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/requirements.txt:68) [backend requirements:131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/requirements.txt:131)
- 当前两份 JSON 经严格重复键扫描均正常，枚举值当前也确为 int。

### HIGH / NEW-FINDING：重复 JSON 键可绕过全部 13 门

Golden 测试用默认 `json.loads`，重复键在结构门运行前已被 last-wins 抹掉。[golden test:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:53)

在 manifest 开头插入：

```json
"library_version": "999.0.0",
```

同时保留后面的真实 `6.3.1`：

```text
raw SHA: 82eaaffa… -> 4b5cbd6…
Python last-wins: 6.3.1，解析对象与原对象完全相同
first-wins verifier: 999.0.0
strict verifier: duplicate:library_version
当前 13 个 test_*：全部通过
```

这不是空白或键顺序变化，而是不同合理解析器得到相反结果，违反“manifest 全字段 + 结构锁”的声明。[G3-4 UAT:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:19)

### MEDIUM / NEW-FINDING：枚举 JSON 类型未锁

`rating_values.again: 1` 改成 `true` 后，因 Python `True == 1`，[golden test:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:175) 的字典比较及全部 13 门仍通过；`state_values` 同类。与 UAT 的“Rating&State 枚举值域锁”不符。[G3-4 UAT:29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:29)

因此，“本提交未触碰且当前 baseline 正确”成立，但“防漂移门已闭合”不成立。

## 三、回归与一致性

- 契约：`69 passed, 1 skipped`
- 契约 + golden + 既有账本：`88 passed, 1 skipped`
- Golden：`13 passed`
- `test_learning_event_log.py`：`6 passed`
- `tests/unit/test_fsrs_manager.py`：`37 passed`
- 均有 10 个既有依赖弃用类 warning；以上是定向测试，不代表整套 CI。

现网仓根账本：

- 23 行；
- validator `exit 0`，仅输出 `RESULT: PASS`；
- 前后 SHA 均为 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`。

锁定 blob 正确：

- `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
- `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`

验收单的 `69+1 / 88+1` 及历史“恰六键”注释均已修正。[UAT:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:32) [UAT:198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:198)

`CURRENT_TASK` 数字正确，但仍写“十四轮整改待提交/下一步提交”，与当前已提交的 `e013102f` 不符。[CURRENT_TASK:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:7) [CURRENT_TASK:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/CURRENT_TASK.md:24)

## 残留清单

- BLOCKER：0
- HIGH ×2
  - CARD-G3-1：参考 verifier 对多项 schema 必填/真实绑定违规返回空
  - CARD-G3-4：重复 JSON 键可保持 13/13 全绿并产生解析器分歧
- MEDIUM ×5
  - CARD-G3-1：等式 3 对合法 offset 假阳性
  - CARD-G3-1：canonical 状态接受非法日期/尾换行
  - CARD-G3-1：hash 测试同源，恒定 hash 仍 14/14
  - CARD-G3-1：负验证脚本不机械断言 mutation 与预期红门
  - CARD-G3-4：Rating/State 枚举 bool 类型漂移全绿
- LOW ×3
  - CARD-G3-1：未成文的 64 层上限误拒有限链
  - CARD-G3-1：UAT 所称限制“写入 docstring”不准确
  - CARD-G3-1：`CURRENT_TASK` 仍声称第十四笔待提交

最终：

- CARD-G3-1：需十五轮
- CARD-G3-4：需十五轮

全程未读取既有未跟踪 round14 审查稿，未修改任何文件；最终工作树仍仅有该既有未跟踪文件。`graphiti-canvas` 本会话未提供，因此该搜索步骤为 `UNVERIFIABLE`。


