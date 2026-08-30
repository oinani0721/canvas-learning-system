# Codex 审查 · CARD-G5-3（第 3 轮）

## 裁决

**不通过**——完整测试与双 manifest 当前全绿，但二轮发现中仍有 **3 项 PARTIAL**：严格整数类型可被 JSON 布尔值绕过、dangling symlink 会在拒绝路径被误删、四态演示双产物未被“全部产物”清单绑定。

本轮未发现 BLOCKER 或新的 HIGH；新增/新确认 **3 MEDIUM / 2 LOW**。

## 二轮发现逐条复核

| 编号 | 状态 | 实跑验证 |
|---|---|---|
| HIGH-1 注释内 RA 吞正文 | **RESOLVED** | 注释 RA 后正文 A→B：指纹改变，diff=`changed=1`。真实 RA 日志 A→B：候选均为 1、伪候选未进入、指纹相同、diff=`unchanged=1`。AUTO 尾段也独立验证为候选 1→1、指纹不变。 |
| HIGH-2 schema fail-open | **PARTIAL** | 系统变异 166 组，158 组拒绝；但 8 组仍 `rc=0` 并生成 JSON+MD：`index=true/false`、`ambiguous_group_size=true`、`occurrence=true`、`line_start=true/false`、`line_end=true/false`。根因是 [split_preview.py:1133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1133) 等处用 `isinstance(v, int)`，Python 将 `bool` 视为 `int`，不符合契约“字段类型不对即拒绝”。 |
| HIGH-3 证据包自洽 | **PARTIAL** | `engine-and-products.sha256` **9/9 OK**；`judge-and-contract.sha256` **3/3 OK**；实跑 **100 passed**，确为稳定 ID 66 + 存量 34。候选 27/1、live diff unchanged 27/1、四态汇总也与文档一致。但输出目录实际有 10 个产物，所谓“全部产物”清单只绑定 8 个，漏掉 `split-diff-CS188 lecture 2-四态演示.{json,md}`；其当前哈希 `d349b38b…` / `997cbf66…` 无 manifest 条目。与 [README:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/README.md:96) 及审查记录“全部产物”声明不符。 |
| MEDIUM-1 第二产物拒写 | **PARTIAL** | MD 预置为有效 symlink、硬链接、`0444` 文件时，均 `rc=1`、JSON 不存在、预置目标内容不变。但 dangling symlink 会被删除：拒绝前 `lexists=true`，拒绝后 `false`。原因是 [split_preview.py:1658](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1658) 用 `not path.exists()` 判断“本次新建”；dangling symlink 的 `exists()` 为 false，随后回滚将其误删。 |
| MEDIUM-2 NFC/NFD basis | **RESOLVED** | raw 文件名确实不同的 NFC/NFD 等价路径：`rc=0`、正常输出；改成真正不同的路径：`rc=1`，诊断点名 `stable_id_basis`，out-dir 不存在。 |
| MEDIUM-3 `--max-units` | **RESOLVED** | `-1`→rc1、`0`→rc1、`1.5`→argparse rc2，均零输出；`+1`→rc0 作为正向对照。 |
| LOW-1 YAML 漏 `basis` | **RESOLVED** | 契约 §7.1 示例 [contract:328](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:328) 已包含 `basis: seed-note-section`。 |
| LOW-2 裸 NUL 分隔碰撞 | **RESOLVED** | 4 组专门构造的 NUL/冒号/路径分段反例全部得到不同 ID；另枚举 4,680 个长度前缀段序列，未发现载荷碰撞。长度字段按精确字符数确定段边界，段内冒号与 NUL 不会产生新分段歧义；剩余只有契约已声明的 64-bit SHA 截断概率碰撞面。 |

补充 schema 穷举边界：还有 13 类“类型正确但语义损坏”的输入可 `rc=0`，包括负 `index`、非正或倒置行号、空路径、错误 ID/指纹格式，以及顶层 namespace/basis/source anchor 与 `stable_id_basis` 不一致。§8.2 当前未声明格式校验、stable ID 自复算或内部字段交叉绑定；若目标是验证外部可编辑 JSON 的完整性，这仍是明确残余边界。

## 本轮新发现

### MEDIUM · 严格整数校验仍可被布尔绕过

直接违反 [契约 §8.2:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:445)。“10 组参数化”没有覆盖 JSON `true/false` 的 Python 类型陷阱。

### MEDIUM · 拒绝路径会删除既存 dangling symlink

这不是“零产物”问题，而是对既存输出目录项的破坏；与契约“只删本次创建的空文件”相反。有效链接测试无法覆盖它，因为 `Path.exists()` 对 dangling link 的语义不同。

### MEDIUM · “全部产物绑定”不完整

[engine-and-products.sha256](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/engine-and-products.sha256:1) 仅有引擎 + 8 个 live 产物，四态演示双产物没有 exact-bytes 绑定。两份清单自身全绿，但不能证明“全部产物”。

### LOW · 19 个变异体结论真实，但覆盖声明过宽

19/19 实跑确实全部变红；抽查 RA、vault fingerprint、回滚、长度前缀四条，失败原因均与撤修直接对应。不过 [mutate_engine.py:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/mutate_engine.py:134) 所谓“退回存在性检查”实际只关闭 `vault_fingerprint` 单点守卫，不能证明 HIGH-2 的全部字段类型门，更没有覆盖本轮 bool-as-int 缺口。截断前身份自检无行为门则已在脚本中如实声明，并非隐藏遗漏。

### LOW · 文档仍有轻微漂移

- [UAT:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/验收单/UAT-CARD-G5-3-拆分稳定ID与diff契约-2026-08-30.md:15) 称 outputs “有三份文件”，实际为 10 个文件（5 JSON + 5 MD）。
- 引擎模块摘要 [split_preview.py:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:20) 和测试文件摘要仍在 L1 公式里漏写 `basis`，尽管正式契约与实现正确。
- 测试矩阵注释 [test_split_stable_id.py:615](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/backend/tests/skills/test_split_stable_id.py:615) 仍写 §4.1 为 8 条、§4.2 为 7 条；正式契约实际各 10 条。

契约专项结论：§3.1 指纹覆盖面、§4.1/§4.2 行为边界、§4.4 歧义三处红旗均与生产入口行为一致；§8.2 因严格整数漏洞只能判 **PARTIAL**。

## 我实际跑了什么

- 用户指定完整测试命令：**100 passed / 10 warnings / rc0**。
- 两份 `shasum -a 256 -c`：分别 **9/9 OK**、**3/3 OK**。
- `pytest --collect-only`：稳定 ID 66 + 存量 34。
- `/private/tmp/codex-g53-r3.lJhDNK/audit_round3.py`：RA、166 组 schema、NFC/NFD、四种目标文件、`max-units`、长度前缀。
- `/private/tmp/codex-g53-r3.lJhDNK/contract_supplement.py`：AUTO 指纹及行内标题注释边界。初版正文未过 60 字内容门，排除该无效结果；加长正文后重跑通过。
- 直接运行 `mutate_engine.py`：**19/19 变异体变红，rc0**；另以 `pytest -vv` 抽查四条失败栈。
- 审查前后 `git status --short` 一致；未编辑仓库文件，未写真实 vault。
