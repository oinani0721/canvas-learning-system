审计结论：FAIL。当前存在 2 个 BLOCKER、5 个 HIGH。

审计绑定末态 `HEAD=0204d2eb161e2d9111ce2d13cc98102c862c050a`；脚本 SHA-256 `78f17a4b…`，规则 SHA-256 `db63f763…`，测试 SHA-256 `519e821c…`。审计期间 HEAD 前移为 G1-4 commit，但脚本与规则字节未变化，所有基线已在末态重跑。

## Findings

1. **BLOCKER — 两条 hard-forbidden 红线可被直白等价句完全漏过**

   位置：[readme_claims_rules.yaml:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:74)、[readme_claims_rules.yaml:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:112)

   隔离环境调用 production `--enforce`：

   | 输入 | 应判 | 实际 |
   |---|---:|---:|
   | `The hit@k metric is labeled recall@k.` | C6 hard | 0 命中，exit 0 |
   | `Skipped checks mean success.` | C11 hard | 0 命中，exit 0 |
   | `Degraded is considered successful.` | C11 hard | 0 命中，exit 0 |
   | `Measured true recall@5 over a labeled relevance corpus.` | 不应命中 | C6 hard，无法逃逸 |

   C6 既漏掉真相源字面 `k`，又把合法 Recall 指标一概当成“hit@k 误名”。

   建议：C6 检测“hit 被命名为 recall”的关系，而非禁用所有 Recall；覆盖 `k|\d+`。C11 增加 `means/considered/regarded/reported as/green` 等明确等同语法，并为合法指标和非成功降级描述建立阴性集。

2. **BLOCKER — 配置可静默解除整个裁判，C6/C11 的 hard 身份也未钉死**

   位置：[check_readme_claims.py:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:100)、[check_readme_claims.py:109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:109)、[check_readme_claims.py:169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:169)

   以下配置面对含 `production-ready` 的 README 均实测 `TOTAL=0 / exit 0`：

   - `scan_paths: [DOES-NOT-EXIST.md]`
   - `scan_paths: README.md`，字符串被拆成字符 tuple
   - `scan_paths: [README*.md]`
   - 删除 C1、只保留 C9
   - 把 C6 severity 改成 `evidence-escapable`

   直接指定不存在的 `--root` 时，report/enforce 也伪绿；绝对 `scan_paths` 还能越出 root 读取文件。若扩展 `scan_paths`，硬编码的 [lefthook.yml:146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/lefthook.yml:146) 和 [readme-claims.yml:9](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.github/workflows/readme-claims.yml:9) 又不会随之触发。

   建议：严格钉死有序且唯一的 C1–C11、对应 `l633`、C6/C11 hard、`scan_paths == ["README.md"]`；校验类型、存在性、root containment、无 glob/`..`/绝对路径。未来扩面时用契约测试同步 YAML、Hook glob、workflow paths。

3. **HIGH — 其余规则名义齐全，但复合语义存在私自扩大和漏报**

   位置：[readme_claims_rules.yaml:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:39)

   抽查实测：

   | 句子 | 实际问题 |
   |---|---|
   | `Many vaults offer one-click import.` | C2 把 `Many` 中的 `any` 当“任意” |
   | `Every vault works with one click.` | C2 漏报 |
   | `Graphiti supports permanent partial restore checkpoints.` | C4 命中；“永久且全量”被实现为 OR |
   | `Limited multi-source RAG is the default fallback.` | C5 命中；未要求 full、主链 |
   | `One-way export into Excalidraw is lossless.` | C8 命中；未要求 Canvas、双向 |
   | `3 specialized AI Agents for a prototype.` | C9 命中；未要求 14 或协同 |
   | `14 个智能体协同工作。` | C9 漏报 |

   建议：复合项明确钉死 subject 和 AND 条件；每类至少加入语义等价阳性、近邻安全阴性、中文和英文变体。

4. **HIGH — evidence escape 是未经验证的自我声明**

   位置：[readme_claims_rules.yaml:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:20)、[check_readme_claims.py:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:151)

   `production-ready [E3](x)` 实测 exit 0；链接无需存在、无需 committed evidence、无需绑定 rule 或 RC SHA。同一行一个标记还能同时逃逸 C1 和 C10。

   建议：至少使用 `[C1:E3](repo-relative-path)` 形式并验证目标存在；真正的 E3/E4/E5 仍需绑定 manifest、RC SHA 和证据等级的独立裁判。否则应明确这里只验证 Markdown 标记，不代表证据成立。

5. **HIGH — legacy_allowlist 可通过同一 README 内搬移洗白**

   位置：[check_readme_claims.py:137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:137)、[readme_claims_rules.yaml:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:24)

   - 保留原行再复制第二份：staged-diff 放行，但 enforce 报 1，CI 兜底成功。
   - 删除原位置、把同一行新增到 README 另一位置：staged-diff 和 enforce 都 exit 0。
   - 移到另一个已扫描文件：`file` 限制有效，不继承 legacy。

   建议：staged 新增行永远不能享受 legacy；全量档把 legacy 绑定到冻结基线 commit 和 occurrence/context fingerprint。

6. **HIGH — staged-diff 解析器可被内容和常见 Git 配置绕过**

   位置：[check_readme_claims.py:181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:181)

   - 暂存 `++ production-ready`：patch 内容行以 `+++` 开头，被当元数据跳过；staged `TOTAL=0`，同一文件 enforce 报 C1。
   - `diff.noprefix=true`、`diff.mnemonicPrefix=true`、`color.ui=always` 均让当前 19 条 staged 新增行被解析成 0 条。
   - `diff.interHunkContext` 可导致命中行号错误。

   建议：强制稳定 diff 参数，如 `--no-color --default-prefix --no-ext-diff --no-textconv --inter-hunk-context=0`；用显式 hunk 状态机，在 hunk 内把所有 `+` 行，包括 `+++...`，当作内容。

7. **HIGH — 10 个测试既未钉死 11 类语义，也没有任何 CI 消费方**

   位置：[test_check_readme_claims.py:83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:83)、[readme-claims.yml:29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.github/workflows/readme-claims.yml:29)、[test.yml:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.github/workflows/test.yml:100)

   测试只实际覆盖 C1/C6/C9/C11。变异实测删除 C2–C5、C7–C8、C10 后仍 `10 passed`；把 hard 改成可吃 legacy，现有测试也不红。独立 workflow 只运行 enforce/report，既有 test.yml 又是显式文件清单，不含本测试。

   建议：增加 C1–C11 参数化阳性/阴性、精确 ID/顺序/severity、字面 `[E3+]`、hard+legacy、配置削弱、Git hostile diff 测试，并在独立 workflow 真正执行。

8. **MEDIUM — 部分配置错误退出 1，而非约定的 2**

   位置：[check_readme_claims.py:86](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:86)、[check_readme_claims.py:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:238)

   非法 `evidence_escape.pattern: "("` 会 traceback、exit 1。非法 `max_occurrences`、非 mapping entry、I/O/解码错误等也未统一包装。缺失规则文件正确返回 2。

   建议：完整 schema 验证，并将正则、整数、I/O、Unicode、subprocess 启动异常统一转换为 `ClaimsConfigError`。

9. **MEDIUM — “不做否定语义分析”声明准确，但确实掩盖不了实质缺陷**

   位置：[check_readme_claims.py:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:21)

   它诚实解释了 `not production-ready` 类误报；但无法解释上述 hard 漏报、合法 Recall 误杀、错误合取、假 evidence 和配置伪绿。`Skipped is not treated as success` 还会被 hard 阻断，反而妨碍 README 诚实说明降级语义。

   建议：至少支持明确否定/限制句的安全阴性形式，并把机械能力边界和证据裁判边界分开声明。

10. **LOW — G1-4 fixture 并非注释所称的严格“19 行逐字副本”**

    位置：[test_check_readme_claims.py:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:42)

    19 行数量相同且 16 条非空内容一致，但空行位置不完全相同。当前逐行 matcher 不受影响。

    建议：修正注释，或加入与冻结新增行快照的 exact-sequence 断言。

## 逐项通过证据

1. L633 名义映射：**部分通过**。当前 YAML 恰好 11 个唯一 ID，顺序和 `l633` 文本与[计划书 L633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:633)一致；11 条 canonical 句各命中一次。正则语义因 findings 1、3 不通过。

2. hard/escape/legacy：**部分通过**。当前 severity 不被改写时，C6/C11 对 evidence escape 和 legacy 都不放行；复制旧行由 enforce 兜底。假 evidence、配置降级和同文件搬移不通过。

3. 三档与退出码：**正常路径通过**。有效配置下 report 恒 0；阳性 enforce/staged 为 1；缺失规则为 2。异常配置覆盖因 finding 8 不通过。

4. lefthook：**配置形态通过**。`glob: README.md` 与当前唯一 scan path 一致，调用 production `--staged-diff`，`lefthook validate` 为 `All good`。G1-4 在暂存态实测 `TOTAL=0`；解析器本身因 finding 6 不通过。

5. CI：**静态编排通过**。workflow 是独立文件；PR/push paths 仅 README、规则、脚本和 workflow 自身；enforce 后以 `if: always()` 输出 report；`.github/workflows/test.yml` 相对基线零改动。未实际触发 GitHub hosted runner，且本机无 actionlint。

6. 最低测试要求：**通过**。阳性、逃逸、hard 不可逃逸、白名单外不扫均有有效断言；末态实跑 `10 passed`。完整语义保证因 finding 7 不通过。

7. 基线：**通过**。用户指定命令末态实际输出：

   `TOTAL=3 effective=0 escaped=0 legacy=3`

   三条均为 `C9-agent-collab`，位置 README 35/50/68，全部 `[legacy]`。`--enforce` exit 0。当前 G1-4 commit 为严格 `19 insertions / 0 deletions`，新增横幅 0 误伤。

8. 机械边界声明：**声明本身通过，能力充分性不通过**，详见 finding 9。

限制：审计只读，未修改 worktree；隔离反例仅写系统临时目录。环境未暴露 `graphiti-canvas`，但本卡结论完全来自当前 Git/file/production CLI，不依赖 Graphiti。

BLOCKER/HIGH 清零: 否



---

## 附录：二轮复核（一轮 2B+5H 处置对抗重验，ultra 档）

结论：二轮复核仍为 **FAIL**。44 项测试及两个基线命令均通过，但 production 入口仍存在 hard 红线、配置、legacy 和 staged-diff 的可复现旁路。审计绑定 `HEAD=0204d2eb161e2d9111ce2d13cc98102c862c050a`；全程只读，目标文件仍未提交。

## 一轮 finding 状态表

| # | 一轮 finding | 状态 | 二轮验证依据 |
|---|---|---|---|
| 1 | BLOCKER — 两条 hard-forbidden 红线漏等价句 | `PARTIALLY-RESOLVED` | 原反例已覆盖，但 `[scan_lines:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:266)` 的整行阴性会抹掉阳性。实跑 `Degraded is successful.`、`Skipped checks indicate success.` 均 `NO_HIT`；显式 C6/C11 阳性后附安全阴性词也 `NO_HIT`。 |
| 2 | BLOCKER — 配置可静默解除裁判 | `PARTIALLY-RESOLVED` | ID/severity/L633/scan_paths 已在 `[常量:58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:58)` 钉死；但 patterns、negative_patterns、legacy 未钉死。变异实跑：所有 pattern=`(?!)`、所有 negative=`.*`、注入 C1 legacy 均 `exit 0`。 |
| 3 | HIGH — 复合语义私自扩大和漏报 | `PARTIALLY-RESOLVED` | 一轮列出的固定样例已修，但 C3/C4/C5/C8/C9 仍未满足全部合取，见 `[rules:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:63)`、`[rules:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:70)`、`[rules:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:78)`、`[rules:105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:105)`、`[rules:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:113)`。 |
| 4 | HIGH — evidence escape 是未经验证的自我声明 | `PARTIALLY-RESOLVED` | 规则编号、root containment、目标存在已实现于 `[escape:225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:225)`；但空的 tracked `.gitkeep`、README 自引用、HTML comment/code 中的 marker 均可放行，且 `[ESCAPE_RE:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:78)` 错误接受 E4+/E5+。 |
| 5 | HIGH — legacy 可通过同一 README 搬移洗白 | `PARTIALLY-RESOLVED` | staged 新增行不吃 legacy、配额已实现；但 `[锚判定:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:275)` 为 `<=25`：锚 68 搬到 43/93 仍 legacy，42/94 才阻断。CI 只跑 full enforce，绕过本地 hook 后窗口内搬移仍绿。 |
| 6 | HIGH — staged diff 解析可绕过 | `PARTIALLY-RESOLVED` | 原 `+++` 内容及 noprefix/mnemonic/color/inter-hunk 问题已修；但 `[git diff 参数:324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:324)` 未强制文本 diff。隔离实跑 binary/`.gitattributes -diff`：staged `TOTAL=0 exit 0`，同态 enforce `exit 1`。 |
| 7 | HIGH — 测试未钉语义且无 CI 消费方 | `PARTIALLY-RESOLVED` | 现已收集 44 项且 workflow 会运行，见 `[tests:112](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:112)`、`[workflow:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.github/workflows/readme-claims.yml:39)`；但上述 production 反例、pattern/negative/legacy 变异、±25 边界和跨文件同步均无回归。 |
| 8 | MEDIUM — 配置错误未统一退出 2 | `PARTIALLY-RESOLVED` | regex/YAML/I/O/git 主路径已包装；但 `legacy_allowlist: 1` 在 `[script:205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:205)` 抛 TypeError、exit 1；PATH 中无 git 时 `[script:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:415)` traceback、exit 1；schema_version 未校验。 |
| 9 | MEDIUM — 否定语义能力不足 | `PARTIALLY-RESOLVED` | 已新增安全阴性并声明边界，但阴性是整行无作用域匹配，既可解除 hard 阳性，又仍误杀 `not production-ready`、`must not be treated as success` 等诚实说明。 |
| 10 | LOW — G1-4 fixture 注释不准确 | `RESOLVED` | `[test:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:48)` 已准确写明“非空行逐字一致、空行布局非严格相同”。 |

## 新发现问题

### BLOCKER

- **整行 negative_patterns 可解除 hard 红线。** `[script:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:266)`、`[C6 negatives:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:95)`、`[C11 negatives:141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:141)`。`hit@k ... labeled recall@k; labeled relevance corpus` 和 `Skipped means success; degraded is not treated as success` 均 0 hit。建议按同一 clause、subject、predicate 绑定否定；显式 hit→recall 命名阳性不得被其他片段覆盖。

- **运行语义与 legacy 仍可由 YAML 静默改写。** `[load_rules:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:188)` 只钉 metadata；legacy 从 `[script:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:204)` 任意加载。隔离变异中，替换一个 C9 基线句并增加同锚 legacy 后，enforce 仍 `effective=0`，原 44 项测试仍全过。建议冻结 pattern/negative/legacy 的规范化契约；legacy 绑定 rule、基线 blob/context digest，并由受保护的外部 review/required check 授权变更。

- **staged 模式仍会对错误 root/缺扫描目标伪绿。** `[main:420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:420)` 未经过 `[目标存在校验:296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:296)`。实跑 `--staged-diff --root backend` 在 `backend/README.md` 不存在时得到 `TOTAL=0 / exit 0`；同 root enforce 正确 exit 2。建议在模式分支前验证 root 是 Git toplevel、全部 scan target 存在且为受控普通文件。

### HIGH

- **L633 合取与明显等价句仍不完整。** 实跑误命中：`multi-vault-safe` 但不完整、Graphiti fully rebuildable 但不永久、Limited multi-source RAG default main pipeline、lossy Excalidraw bidirectional sync、3 Agents collaborate。反向又漏掉 `ready for production`、`Each vault works out of the box`、`Skipped checks are successful`。建议每条规则绑定 subject 和所有必要 conjunct，并为“缺任一 conjunct”建立阴性矩阵；自由文本正则不能宣称完整语义裁判。

- **evidence marker 仍非可信 Markdown 证据且生命周期断链。** 空文件、README 自引用、HTML comment/code/反斜杠转义 marker 可逃逸；目录正确拒绝。workflow paths `[10-22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.github/workflows/readme-claims.yml:10)` 和 hook `[147-151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/lefthook.yml:147)` 又不会在证据文件单独删除/改名时重验旧 README。建议使用 Markdown AST，仅接受可渲染链接；精确枚举 E3/E3+/E4/E5；限制到 tracked、非空、指定 evidence 目录并将其纳入 CI/hook 触发。

- **legacy 的 ±25 容差仍可绕过 hosted CI。** 锚 68 搬到 93：full enforce 放行，staged-diff 才阻断；但 workflow 不运行 PR-base 新增行裁判。建议在 CI 增加 base→head diff 模式，或用冻结 context/blob fingerprint 取代宽行号容差。

- **binary diff 可绕过本地 hook。** `[staged parser:315](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:315)` 对 Git 的 `Binary files ... differ` 无 hunk即返回空。建议添加 `--text`，并比较 changed-name 集与成功解析集；扫描目标有 staged 变化却无可解析 hunk时 exit 2。

- **scan target 未做 resolved containment。** `[scan_scan_paths:300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:300)` 直接 `is_file/read_text`。README symlink 指向 root 外文件时会读取并可能打印外部内容。建议拒绝 symlink，并对 resolved target 执行 `relative_to(root.resolve())`。

### MEDIUM

- **schema/异常归一化仍不完整。** 显式校验 `schema_version == 2`、legacy 必须为 list、行号/配额必须为严格正整数；包装默认 root 的 git 启动及 subprocess decode 错误，统一 exit 2。

- **scan_paths/hook/workflow 同步目前正确，但仅靠注释。** 当前三者都是 `README.md`，`lefthook validate` 为 `All good`；测试没有解析 hook/workflow 做等值断言，workflow paths 也不含 `lefthook.yml`。建议增加跨文件契约测试并把 `lefthook.yml` 纳入触发路径。

## 安全阴性边界评估

等级：**BLOCKER，必须收窄**。

- `true recall`/`labeled relevance` 不能作为整行豁免词。它们可被附到明确的 hit→recall 误名句后直接解除 C6；同时 `Recall@5 uses all labeled relevant items as denominator` 这类合法口径仍被误杀。建议移除“所有 recall@k 默认 hard”的宽模式，优先只拦显式 hit→recall 命名关系；真正 recall 只按局部指标定义/分母关系判断。

- `not treated` 同样必须绑定 `skipped/degraded + 否定词 + success/pass/green` 的同一谓词，覆盖 `must not`、`does not mean`、`cannot`、`不应/不得/不视为` 等，而不是任意位置出现即整规则豁免。

- Markdown comment/code 内容不应提供 negative 或 evidence escape。否则隐藏文本即可控制裁判结果。

## 实跑证据

- `cd backend && .venv/bin/pytest tests/unit/test_check_readme_claims.py -q`：**44 passed, 10 warnings，exit 0**。
- `python3 backend/scripts/check_readme_claims.py --report --root <worktree>`：`TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0。
- `python3 backend/scripts/check_readme_claims.py --enforce --root <worktree>`：同一计数，`OK`，exit 0。
- `lefthook validate`：`All good`；`.github/workflows/test.yml`：零 diff。
- 环境未暴露 `graphiti-canvas`；本结论完全绑定当前文件字节及 production CLI 实跑，不依赖模型自报或 Graphiti。未修改工作树。

BLOCKER/HIGH 清零: 否
一轮处置复核: 不通过

---

## 附录：三轮复核（二轮 3B+5H 处置重验 + C6 政策分歧裁定，ultra 档）

结论：第三轮仍不通过。当前残余为 **2 BLOCKER + 4 HIGH + 2 MEDIUM**。审计绑定 `card/n4-readme@0204d2eb161e2d9111ce2d13cc98102c862c050a`；全程只读，反例仅使用系统临时目录。

## 二轮 finding 状态表

| 二轮 finding | 状态 | 三轮验证依据 |
|---|---|---|
| B1′ 整行阴性解除 hard | `PARTIALLY-RESOLVED` | `negative_patterns` 已废除，原拼接句现会命中；但新的 span 守卫仍可被 HTML 隐藏词或无关谓词中的 `not` 洗掉，见 [script:101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:101)、[script:337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:337)。 |
| B2′ patterns/legacy 未钉死 | `RESOLVED` | YAML 原始字节全文 SHA 在 [script:195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:195) 校验；pattern 掏空、legacy 注入等单边变化均 exit 2。它是 review-coupling，不是外部授权封印，但符合声明的设计。 |
| B3′ staged 错误 root/缺目标 | `PARTIALLY-RESOLVED` | 错误 root、缺 README 已 exit 2；但 [target validation:404](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:404) 检查 worktree，而提交对象来自 index，D/T/R 状态仍可伪绿。 |
| H1′ L633 合取不完整 | `PARTIALLY-RESOLVED` | 二轮列出的固定样例已修；但 C8 不要求 Canvas，C9 扩成 10–19 Agent 且部分模式不要求协同；全行 lookahead 还会跨分句拼合 conjunct，见 [rules:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:74)、[rules:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:113)。 |
| H2′ 五条件 evidence escape | `PARTIALLY-RESOLVED` | tracked、非空、非 symlink、编号/E级、自引用检查已实现；但反斜杠、跨行 HTML、双反引号及 prospective index/lifecycle 仍可绕过，见 [script:292](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:292)。 |
| H3′ legacy ±25 搬移 | `PARTIALLY-RESOLVED` | 单行换邻域会失效；完整五行窗口整体搬移时 digest 保持不变，full enforce 仍放行，见 [digest:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:161)、[legacy check:374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:374)。 |
| H4′ 二进制/staged 解析 | `PARTIALLY-RESOLVED` | `--text`、changed/parsed 交叉核对及原二进制反例已修；但 `text=True` + `splitlines()` 会在 CR/VT/U+2028 后丢失 diff 的 `+` 归属，见 [staged parser:477](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:477)。 |
| H5′ symlink/containment | `RESOLVED` | full-mode 直接、broken、越界 symlink 均拒绝，resolved containment 已在 [script:404](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:404) 闭合。index/worktree 分叉另计 B3/H4。 |
| M1 schema/异常统一 | `PARTIALLY-RESOLVED` | 主路径改善，但深层 YAML 可在 SHA 比较前抛 `RecursionError`、混合类型未知键仍 TypeError、无 git 时 default root 会退回 cwd 并 exit 0。 |
| M2 跨文件同步 | `PARTIALLY-RESOLVED` | 当前 hook/workflow 路径一致且含 `lefthook.yml`；但 [同步测试:455](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:455) 只检查 `EXPECTED_SCAN_PATHS[0]`，第二扫描路径可漏同步。 |

## 分歧裁定

**等级：INFO / ACCEPTED DESIGN DECISION，不构成缺陷。**

C6 在 README 范围广拦所有 `recall@k` 是明确、保守、fail-closed 的产品政策，且脚本、YAML、测试均一致声明。未来合法 recall 必须通过双文件契约审查，属于可接受的治理选择。

但“政策可接受”不等于“实现已正确”：下面 `We call hit@k recall.`、Top-5 hit-rate 定义式等漏判仍是 BLOCKER。

## 新发现问题

1. **BLOCKER — C11 的 span 否定守卫仍能洗掉 hard-positive。**

   - `Skipped <!-- not --> means success.` → full `--enforce TOTAL=0`、exit 0。
   - `Skipped checks do not mean failure but indicate success.` →同样伪绿。
   - 原因：[_rule_fires](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:337) 在原始 Markdown 上查找 span 内任意 negator，并未把否定绑定到“等同成功”谓词。
   - 建议：先按 Markdown 可见文本归一化，再做谓词级否定绑定；上述输入加入 production CLI 回归。

2. **BLOCKER — C6/C11 仍漏直白 hard 等价句。**

   - `We call hit@k recall.` → exit 0。
   - `Top-5 recall is the fraction of queries with at least one relevant hit.` → exit 0。
   - `Skipped checks pass.` → exit 0。
   - 位置：[C6 patterns:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:97)、[C11 patterns:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:139)。
   - 建议：覆盖主动语态命名、prefix Top-k 定义式、直接 `pass/succeed` 谓词。

3. **HIGH — 复合规则仍跨主体、跨分句或扩大数字范围。**

   - `Excalidraw provides lossless bidirectional SVG conversion.` 缺 Canvas，却命中 C8、exit 1。
   - `19 specialized AI Agents available independently.` 非 14 且无协同，却命中 C9。
   - `This manual is complete; the storage layer is multi-vault safe.` 会跨分句拼成 C3。
   - 建议：约束同一 clause/subject；C8 显式要求 Canvas；C9 严格绑定 14+协同，或另行声明扩大政策。

4. **HIGH — escape 仍不证明“可渲染证据链接”，生命周期也未闭合。**

   - `production-ready \[C1:E3](docs/evidence.md)` 被判 `escaped=1`、exit 0。
   - 跨行 HTML comment、双反引号 code span、`<code>` marker 同样可放行。
   - `git add -N proof.md` 会被 `git ls-files` 视为 tracked，但 prospective tree 中没有该文件。
   - 证据文件单独删除不会触发 [hook:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/lefthook.yml:147) 或 [workflow paths:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.github/workflows/readme-claims.yml:8)。
   - 建议：用 Markdown AST 接受真实 link node；staged 模式验证 index blob；证据限制到受控目录并纳入 hook/workflow。

5. **HIGH — 五行 legacy 窗口可整体搬移。**

   - 真实 README L66–70 整块搬移，目标 L68→L78：digest 不变，full enforce 仍 `TOTAL=3 effective=0 legacy=3`、exit 0。
   - 当前 workflow 的精确行号测试会额外拦住该具体变更，因此不是“现行整套 CI 绿”；但 `--enforce` 自身及任何仅消费它的入口仍伪绿。
   - 建议：CI 基于 merge-base/index 判定 legacy 行未被新增，或取消 ±25 容差。

6. **HIGH — staged diff 仍有 hard 声明漏判及 index/worktree 双树错配。**

   - 新增 `prefix<U+2028>recall@5 reached 0.9`：staged `TOTAL=0`、exit 0；full enforce 命中 C6、exit 1。
   - `git rm --cached README.md` 后保留 worktree 副本：staged exit 0，但 `git write-tree` 中 README 已不存在。
   - 建议：diff 捕获 bytes、仅按 `b"\n"` 分割；用 `git ls-files --stage`/prospective tree 验证 stage-0 普通 blob，并显式拒绝 D/T/unmerged。

7. **MEDIUM — schema 和异常契约仍不严格。**

   - [load_rules:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:203) 先解析再验 SHA，超深 YAML 可 traceback exit 1。
   - `schema_version: 2.0`、未知顶层字段、非字符串 legacy `line/reason` 在同步 SHA 后可被接受。
   - PATH 无 git时，本仓默认 enforce 实测 exit 0，而非摘要声称的 exit 2。
   - 建议：先验 raw hash，再解析；闭集顶层 schema；严格 `type(...)`；git 定位失败 fail closed。

8. **MEDIUM — CI 基线测试反向阻断合法 escape。**

   - [test_real_repo_baseline_three_legacy_c9](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:435) 断言总 hit 必须恰为 3。
   - 新增完全合法、tracked、非空证据支持的 escaped 声明时，production enforce 通过，但 workflow pytest 因 `len(hits) == 3` 失败。
   - 建议：只断言三条指定 legacy 的身份与状态，不应禁止额外合法 escaped hit。

## 实跑证据

| 核对项 | 结果 |
|---|---|
| `cd backend && .venv/bin/pytest tests/unit/test_check_readme_claims.py -q` | `59 passed, 10 warnings`，exit 0 |
| `--report` | `TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0 |
| `--enforce` | 同一计数，`OK`，exit 0 |
| `--print-rules-sha` | `7025b80e28e71092807569fdfb74796d0422c312bad9c489fd44999cd9cfc2b8` |
| 磁盘 SHA / 脚本常量 | 与上述完全一致 |
| 当前 `--staged-diff` | `TOTAL=0`，exit 0 |
| `lefthook validate` | `All good` |
| worktree | 五个被审文件未被修改；既有未提交状态保持不变 |

未实际触发 hosted GitHub Actions，因此不能把本地 59 项 PASS 表述为整套 CI PASS；Graphiti 工具未暴露，本结论完全绑定当前文件字节和 production CLI 结果。

BLOCKER/HIGH 清零: 否  
二轮处置复核: 不通过



---

## 附录：四轮复核（三轮 2B+4H 处置重验，收敛轮，ultra 档）

结论：四轮复核不通过。当前仍有 **2 BLOCKER + 1 HIGH**；H4/H5/H6 已闭合，但 B1、B2、H3 仍存在 staged、enforce、CI 共用的可复现漏判。

## 三轮 finding 状态表

| 三轮 finding | 状态 | 四轮验证依据 |
|---|---|---|
| B1 — HTML 注释/跨谓词否定洗白 | `PARTIALLY-RESOLVED` | 三轮原反例均已修；但 [谓词前窗实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:421) 仍把无关 `not` 当成后续谓词的否定。`Skipped checks do not fail but indicate success.` 在 staged/enforce 均 `TOTAL=0`、exit 0。 |
| B2 — C6/C11 漏直白等价句 | `PARTIALLY-RESOLVED` | `We call hit@k recall.`、Top-k 定义式、`Skipped checks pass.` 已拦；但 [C6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:101) 漏 `Hit@k = recall.`，[C11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:147) 漏 `Skipped checks were successful.`，两档均 exit 0。 |
| H3 — 跨主体/分句/C8/C9 | `PARTIALLY-RESOLVED` | 分句隔离和 C8 Canvas conjunct 已修；但 C9 三处声明“所有双位数阵容”，生产正则却全部为 `1[0-9]`，见 [rules:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:127)。20/99 Agents 均漏判。 |
| H4 — evidence escape/lifecycle | `RESOLVED` | 受控目录、stage-0、ITA/空文件、反斜杠、E 级枚举均实跑正确，见 [escape 实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:360)。push/PR paths 均含 `docs/evidence/**`，见 [workflow](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/.github/workflows/readme-claims.yml:8)。 |
| H5 — 五行 legacy 整体搬移 | `RESOLVED` | [行号容差为 0](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:126)。保持五行 digest、L68→L73 后 `effective=1`、exit 1。 |
| H6 — U+2028/双树错配 | `RESOLVED` | [字节级 diff 解析及 D/T/U 拒绝](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:540)有效：U+2028 exit 1；D/T/U 各 exit 2；index 有 hard 声明而 worktree 恢复诚实文本时仍 exit 1。 |

## 新发现问题

### BLOCKER

1. **C11 前窗仍可跨谓词洗白。**

   - `Skipped checks do not fail but indicate success.`：`indicate` 的前窗为 `"do not fail but "`，`not` 实际修饰 `fail`，却在 [line 435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:435) 解除阳性。
   - `Skipped checks mean success but are not treated as success.`：贪婪 span 只捕获后面的被否定谓词，吞掉较早的未否定 `mean success`。
   - 这直接违反脚本 docstring 所称“同分句其他未否定谓词照常计”，不是 DOCUMENTED-LIMIT。
   - 建议：逐个检查谓词候选、避免贪婪跨度，并把否定绑定到谓词的局部语法结构。

2. **C6/C11 仍漏基本字面等价。**

   - `Hit@k = recall.`、`Hit@k is recall.`、`Skipped checks were successful.`：staged/enforce 均 `TOTAL=0`、exit 0。
   - 等号、基本系词和过去时属于 L633 的直接表达，不是开放式语义释义。
   - 建议：C6 补 `=|≈|is|equals`；C11 补 `was|were` 等基本形态，并增加生产 CLI 回归。

### HIGH

3. **C9 “双位数”政策只实现 10–19。**

   - 政策见 [脚本:45](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:45)、[YAML:131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:131)；三条正则均使用 `1[0-9]`。
   - 10/19 Agents 命中；20/42/99 Agents 在 staged/enforce 均 exit 0。测试只覆盖 19，见 [test:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:125)。
   - 建议：若政策确为双位数，覆盖 10–99 并锁 10/19/20/99 边界；否则把四处政策文字明确收窄为“10–19”。

### MEDIUM

- [schema loader](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:277) 仍接受 `schema_version: 2.0`、未知顶层字段及数字型 legacy `line/reason`（被 `str()` 转换）。建议严格类型和顶层闭集。
- [真仓基线测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:464) 强制 `len(hits)==3`，会反向阻断新增的合法 escaped 声明。建议只钉三条 legacy 身份并断言无 effective hit。
- [index 解析](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:360) 未用 `git cat-file` 证明对象确为非空 blob。畸形 index 可让本地 staged/enforce 伪绿，但 `git fsck`、fresh checkout 会失败，因此不升 HIGH。

### LOW

无独立新增。

### DOCUMENTED-LIMIT

- 同一分句内不解析不同主体、跨物理行不拼接；属于已声明的逐行正则边界。
- evidence 只验证机械链接性质，不判断内容真伪或完整 Markdown/HTML 渲染语义；由用户 diff 批准门和 G1-6 逐声明审计补偿。
- C6 对 README 全拦 recall@k 继续按已裁定的 INFO/accepted design decision 处理。

## 实跑证据

- checkout：`card/n4-readme@0204d2eb161e2d9111ce2d13cc98102c862c050a`
- 指定测试：`70 passed, 10 warnings in 3.22s`，exit 0。
- `--report`：`TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0。
- `--enforce`：同一计数，`OK`，exit 0。
- `--print-rules-sha`、磁盘 SHA、脚本常量均为 `27912ef0a2f65fdd3996f072f1df77db511676cc33d8dca2e3125477b951ebfe`。
- 当前 `--staged-diff`：`TOTAL=0`，exit 0；`lefthook validate`：`All good`。
- 未实际触发 hosted GitHub Actions，不能表述为整套 CI PASS。
- Graphiti 工具本轮未暴露；记忆仅用于审计流程，所有实质结论均在当前 checkout 重验。
- 审阅后 `git status --short` 与起始状态一致，未修改 worktree。

BLOCKER/HIGH 清零: 否  
三轮处置复核: 不通过



---

## 附录：五轮复核（四轮 2B+1H 处置重验，ultra 档）

结论：不通过。虽然 78 项测试与真仓基线均通过，但生产入口仍有 **2 BLOCKER + 1 HIGH** 的可复现漏判。

审计绑定当前工作树字节，`HEAD=0204d2eb161e2d9111ce2d13cc98102c862c050a`；目标文件尚未提交。全程只读，反例仅写入并自动清理 `/tmp`。

## 四轮 finding 状态表

| 四轮 finding | 五轮状态 | 验证依据 |
|---|---|---|
| B1 — C11 前窗跨谓词洗白 | `PARTIALLY-RESOLVED`，残余 BLOCKER | 点名两句已修；但掩码重试仍受 C11 `{0,40}` 主体—谓词跨度限制。[规则:155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:155)、[重试实现:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:445)。`Skipped checks are not considered successful but indicate success.` 在掩码 `considered` 后无法再抵达 `indicate`，full/staged 均 `TOTAL=0`、exit 0。这违反“逐个评估同分句谓词”的声明，不是 DOCUMENTED-LIMIT。 |
| B2 — C6/C11 字面等价漏判 | `PARTIALLY-RESOLVED`，残余 BLOCKER | `Hit@k =/is recall`、`were successful` 已拦；但 [C11 patterns:153](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:153) 未覆盖 `equal/equivalent`。`Skipped checks equal success.` full/staged 均 `TOTAL=0`、exit 0；C6 的 `Hit@k == recall.` 同样漏判。二者均是 [L633“等同/写成”](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:633) 的直接表达。 |
| H3 — C9 双位数范围 | `PARTIALLY-RESOLVED`，残余 HIGH | 三条正则已改为 `[1-9][0-9]`，20/99 点名样例闭合；但规则仍要求 `specialized AI` 或“协同”。`42 AI Agents are available.` full/staged 均 `TOTAL=0`、exit 0，违反脚本“不要求协同”的双位数阵容政策。[政策:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:46)、[patterns:136](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:136)。 |
| MEDIUM — schema 严格性 | `RESOLVED` | [loader:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:283) 严格要求 `type(schema_version) is int` 并关闭未知顶层字段；[legacy:343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:343) 严格校验 file/line/reason。同步规则 SHA 后独立变异，`2.0`、未知字段及三种数字类型均 exit 2。 |
| MEDIUM — 真仓基线硬钉总数 | `RESOLVED` | [测试:474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:474) 只钉 L35/L50/L68 三条 legacy 身份和零 effective，不再断言总命中恰为 3。 |
| MEDIUM — index 缺少 `cat-file` 深验 | `PARTIALLY-RESOLVED`，DOCUMENTED-LIMIT | [index 解析:373](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:373) 仍只信 mode/stage/SHA。畸形 index 可令 checker `escaped=1`，但 `git cat-file`、`git fsck`、`git write-tree` 均失败，无法形成提交或 fresh checkout；维持四轮既定 DOCUMENTED-LIMIT，不升 HIGH。 |

## 否定尾绑定与掩码完整性

已确认闭合：

- `do not fail but indicate success`、`mean success but are not treated as success`：full/staged 均 `TOTAL=1`、exit 1。
- `were not successful`、`must not be treated as success`：full/staged 均 `TOTAL=0`、exit 0。
- 短距离连续谓词能逐个掩码：首个否定、后续未否定时能命中；全部否定时放行。

未闭合的是上述 `{0,40}` 重扫截断，而非 `_NEG_TAIL_RE` 尾绑定本身。

以下维持 [docstring 已声明边界](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:55)：

- `不能再被视为成功`、`must not ever be treated as success` 会被保守误报，因为中间只允许一个助词。
- `not unsuccessful` 等双重否定需要完整语义推断，属于 DOCUMENTED-LIMIT。

## 新发现分级

- **BLOCKER**：B1 的 40 字符掩码重扫截断。
- **BLOCKER**：B2 的 `equal/equivalent` 与常见重复等号直接等价族漏判。
- **HIGH**：C9 普通双位数 `AI Agents` 阵容句漏判。
- **MEDIUM**：C9 中文第二条正则缺数字边界；`120/199/999 个…智能体协同` 会从三位数尾部取两位误报。[规则:137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:137)。
- **LOW**：78 项测试未直接锁 schema 同步-SHA拒绝路径；C9 的 20/99 回归只覆盖第一条英文模式。[现有边界用例:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:139)。

## 实跑证据

- `backend/` 下执行 `.venv/bin/pytest tests/unit/test_check_readme_claims.py -q -p no:cacheprovider`
  - `78 passed, 10 warnings in 3.27s`，exit 0。
- `--report`
  - README L35/L50/L68，均为 C9 `[legacy]`
  - `TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0。
- `--enforce`
  - 同一计数，`OK`，exit 0。
- 规则文件 SHA、脚本常量、`--print-rules-sha`：
  - `82605964c22e1516ca479601104a685e2919bbb90ec2d3b67a941760140c0160`
- `lefthook validate`：`All good`。
- 未实际触发 hosted GitHub Actions，不能表述为整套 CI PASS。
- 审计前后 `git status --short` 完全一致。Graphiti 本轮未暴露；历史记忆仅用于选择审计方法，所有结论均在当前 checkout 重验。

BLOCKER/HIGH 清零: 否  
四轮处置复核: 不通过



---

## 附录：六轮复核（五轮 2B+1H+1M 处置重验，ultra 档）

六轮复核结论：**不通过**。点名反例虽已修复，但仍复现 **1 个 BLOCKER + 1 个 HIGH** 的生产入口伪绿。

### 五轮 finding 状态表

| 五轮 finding | 六轮状态 | 验证依据 |
|---|---|---|
| B1 — C11 掩码重扫跨度截断 | `RESOLVED` | 主体→谓词已扩至 80、谓词→成功词扩至 40，[规则:158](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:158)；生产代码会掩码否定谓词后继续重扫，[实现:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:445)。原反例 full/staged 均 `TOTAL=1`、exit 1；全部谓词均否定的对照句保持 `TOTAL=0`、exit 0。 |
| B2 — equal/equivalent/重复等号族 | `PARTIALLY-RESOLVED`，残余 **BLOCKER** | 点名的 `Skipped checks equal success.`、`Hit@k == recall.` 已拦，[回归:149](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:149)。但 [C6:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:114) 把 `is`、`equivalent to`、`equals` 列为互斥单项，漏掉标准语法 `is equivalent to`/`is equal to`；[C11:156](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:156) 又只接受紧邻 `skipped/degraded` 的等号。见下方反例。 |
| H3 — C9 普通双位数阵容 | `PARTIALLY-RESOLVED`，残余 **HIGH** | `42 AI Agents are available.` 已拦；但政策明确“不要求协同”，[脚本:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:46)。[规则:137-141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:137) 中 `个 Agent` 路径仍要求协同，无协同路径只接受“智能体”。 |
| MEDIUM — 中文三位数尾两位误报 | `RESOLVED` | 两条中文模式已有 `(?<![0-9])`，[规则:137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:137)、[规则:141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:141)；`120/199/999 个智能体…` full/staged 均 `TOTAL=0`、exit 0，阴性回归见 [测试:173](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:173)。 |

### 新发现分级

- **BLOCKER — B2 直接等价族仍漏判**

  - `Hit@k is equivalent to recall.`
  - `Hit@k is equal to recall.`
  - `Skipped checks == success.`
  - `Degraded mode === success.`

  四句在真实 `--enforce` 和 `--staged-diff` 均为 `TOTAL=0`、exit 0。它们只增加标准系词或既有 canonical 主语名词，直接属于 [L633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:633)，不是开放式同义词链。

- **HIGH — C9 中文原词直接族仍漏判**

  - `42 个 Agent 可用。`
  - `42 个 AI Agents 可用。`

  两句 full/staged 均 `TOTAL=0`、exit 0。它们使用 L633 原词“个 Agent”，且只省略了政策明确不要求的“协同”，不属于 DOCUMENTED-LIMIT。

- **DOCUMENTED-LIMIT，不阻断定级**：超过 80/40 的远距改写、任意形容词链及保守误报（例如 `unequal` 被其中的 `equal` 命中）属于 [docstring:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:55) 已声明的逐行正则边界，不升 BLOCKER/HIGH。

### 实跑证据

- `HEAD=0204d2eb161e2d9111ce2d13cc98102c862c050a`，分支 `card/n4-readme`。
- 从 `backend/` 使用 `.venv/bin/pytest`：`83 passed, 6 warnings in 9.83s`，exit 0。
- `--report`：README L35/L50/L68，均为 C9 legacy；`TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0。
- `--enforce`：同一计数，输出 `OK`，exit 0。
- 规则文件 SHA 与脚本常量一致：`dcbad1c575a811b5d323b9ec6a00e714b4c1941e5998493955ebfd73a97f8d10`。
- 反例仅在 `/tmp` 隔离 Git fixture 中执行并自动清理；审阅前后 worktree 状态一致。
- 目标脚本、规则、测试和 workflow 当前仍未提交，因此结果绑定当前 working-tree bytes，不代表 HEAD 或 hosted CI 已包含它们。历史记忆仅用于审阅方法，所有结论均在当前 checkout 重验。

BLOCKER/HIGH 清零: 否  
五轮处置复核: 不通过



---

## 附录：七轮复核（六轮 1B+1H 处置重验，ultra 档）

结论：七轮复核仍不通过。六轮点名的 6 个反例均已修复，但同一直接表达族仍复现 **2 BLOCKER + 1 HIGH** 伪绿。

### 六轮 finding 状态表

| 六轮 finding | 七轮状态 | 验证依据 |
|---|---|---|
| B2 — C6/C11 equal/equivalent/重复等号族 | `PARTIALLY-RESOLVED` | 原四句 full/staged 均 `TOTAL=1 effective=1`、exit 1，并已入[回归](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:154)。但既有 canonical 主语 `hit@k metric` 与新谓词组合仍漏判，见下方 BLOCKER。 |
| H3 — C9 中文双位数 Agent 直接族 | `PARTIALLY-RESOLVED` | 原两句 full/staged 均命中 C9、exit 1，并已入[回归](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:158)。但仅移除中英混排空格即伪绿，见下方 HIGH。 |

### 新发现分级

1. **BLOCKER — C6 既有 canonical 主语与等价谓词无法组合**

   - `The hit@k metric is equivalent to recall.`
   - `Hit@k metric == recall.`

   两句在真实 `--enforce`、`--staged-diff` 均为 `TOTAL=0 effective=0`、exit 0。`metric` 已由[现有 canonical 用例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:115)纳入直接主语族，不是新增同义词或形容词链。根因是 [C6 等价模式](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:114)只允许 `hit@k` 后以 `\s*` 紧接谓词。

2. **BLOCKER — 行内 Markdown 可切断 hard-forbidden 直接句**

   以下原词、原语序句仅增加 code/emphasis 排版，两档均 `TOTAL=0`、exit 0：

   ```text
   `Hit@k` is equivalent to recall.
   Hit@k is **equivalent to** recall.
   Skipped checks **==** success.
   Skipped checks == **success**.
   ```

   脚本明确声明 code span 对读者可见且仍属声明面，[契约](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:20)与实际不符；[_rule_fires](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:434)直接对含 Markdown 分隔符的文本跑正则。整句整体加粗或整体 code span 的对照能命中，定位为 token 内部分隔旁路。

3. **HIGH — C9 Unicode 词边界导致中文紧邻写法伪绿**

   - `42个Agent可用。`
   - `42个AI Agents可用。`

   full/staged 均 `TOTAL=0`、exit 0。它们与六轮点名句只差混排空格，仍是 L633 原词直接族。根因是 [C9 模式](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:142)末尾 `agents?\b`：`Agent` 后紧接中文 `可` 时，Python Unicode 正则不存在词边界。

### 实跑证据

- `backend/`：`89 passed, 10 warnings in 3.14s`，exit 0。
- `--report`：README L35/L50/L68 均为 C9 legacy；`TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0。
- `--enforce`：同一计数，输出 `OK`，exit 0。
- 规则文件 SHA 与脚本常量一致：`4bda09016efcef80167c058d06e65f249625bb7eb6489ce660cecbd4cd407b94`。
- 绑定 `card/n4-readme@0204d2eb161e2d9111ce2d13cc98102c862c050a` 的当前 working-tree bytes；目标文件仍未提交，不能外推为 HEAD/hosted CI 已包含。
- 反例仅在系统临时目录运行并自动清理；审阅前后工作树状态一致。未将远距改写、开放同义词或形容词链升级定级。

BLOCKER/HIGH 清零: 否  
六轮处置复核: 不通过



---

## 附录：八轮复核（七轮 2B+1H 处置重验，ultra 档）

结论：第八轮仍未收敛。两个七轮 BLOCKER 已解决，但 C9 残留 HIGH，另发现 C5 同根 HIGH；没有剩余 BLOCKER。

## 七轮 finding 状态表

| 七轮 finding | 八轮状态 | 验证依据 |
|---|---|---|
| BLOCKER — C6 `hit@k metric` 主语组合漏判 | `RESOLVED` | [C6 正则](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:114)加入 `[^.。]{0,12}?`；两句回归位于[测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:161)。真实 `--enforce`/`--staged-diff` 均命中 C6，`TOTAL=1 effective=1`、exit 1。 |
| BLOCKER — 行内 Markdown 强调符切断 token | `RESOLVED` | [_match_surface](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:374)剥离反引号、`*`、`**`、`__`、`~~`，并由[生产扫描路径](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:502)统一调用。四句回归位于[测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:163)；两档均命中正确 C6/C11、exit 1。 |
| HIGH — C9 中文紧邻 Unicode 词边界 | `PARTIALLY-RESOLVED` | 七轮两句已由[C9 词尾负向前瞻](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:142)修复，并进入[回归](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:167)；两档均命中 C9、exit 1。但数字前的 Unicode `\b` 仍产生同族伪绿，见下表。 |

## 新发现分级

| 等级 | 可复现伪绿 | 两档结果与根因 |
|---|---|---|
| HIGH — C5 Unicode 前导边界 | `当前full multi-source RAG 是默认主链。` | `--enforce`/`--staged-diff` 均 `TOTAL=0 effective=0`、exit 0；加空格的对照 `当前 full…` 均命中 C5、exit 1。[规则第 98 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:98)的 `\bfull\b` 在中文与 ASCII 字母之间不存在 Unicode 词边界。句子逐字保留 [L633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:633) 原词，仅增加正常中文前缀。 |
| HIGH — C9 残余前导边界 | `共有42 AI Agents协同。`、`现有14 Agents协同。` | 两档均 `TOTAL=0 effective=0`、exit 0；`共有 42 AI Agents可用。` 或 `共有42个Agent可用。` 对照均命中、exit 1。C9 英文路径在[规则第 136/138/140 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:136)仍以 `\b[1-9][0-9]` 起始；这违反脚本已声明的[双位数 Agent 直接族政策](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:47)。 |

这两项属于正常中英混排的原词直接表达，不属于已排除的 HTML/零宽/全角、单下划线、跨行、完整渲染器或语义推断边界。未发现新 BLOCKER。

## 实跑证据

- `backend/`：`.venv/bin/pytest tests/unit/test_check_readme_claims.py -q -p no:cacheprovider`
  - `collected 97 items`
  - `97 passed, 10 warnings in 3.19s`
  - exit 0
- 七轮全部 8 句确实位于[参数化回归表](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:160)；参数测试验证正确规则、enforce exit 1、report exit 0。另以临时 Git fixture 手工验证了全部 8 句的 staged 入口。
- 本仓 `--report`：README L35/L50/L68 三条 C9 `[legacy]`，`TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0。
- 本仓 `--enforce`：相同计数，输出 `OK`，exit 0。
- 规则实际 SHA、`--print-rules-sha` 和[脚本常量](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:103)一致：`08c5fb08358c7cd1f97b41f1219dacddd696678d2087d99549a4504c8cbbf743`。
- 证据绑定 `card/n4-readme@0204d2eb161e2d9111ce2d13cc98102c862c050a` 的当前 working-tree bytes；目标文件仍未跟踪，不能外推为 HEAD 或 hosted CI 已通过。
- 审阅前后工作树状态一致；所有反例 fixture 均已从 `/tmp` 清理。当前会话未提供 `graphiti-canvas`，未执行其记忆搜索。

BLOCKER/HIGH 清零: 否  
七轮处置复核: 不通过



---

## 附录：九轮复核（八轮 2 HIGH 处置重验，ultra 档）

结论：第八轮点名的 2 个 HIGH 均已 `RESOLVED`，但九轮仍发现同根 Unicode 边界残留：**1 个 BLOCKER、2 个 HIGH、1 个 MEDIUM**，因此尚未收敛。

### 八轮 finding 状态表

| 八轮 finding | 九轮状态 | 验证依据 |
|---|---|---|
| C5：`当前full multi-source RAG 是默认主链。` | `RESOLVED` | 八轮原问题见[审查报告:583](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/_bmad-output/审查/codex-review-CARD-G1-5.md:583)。[规则:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:98) 已改用 ASCII 定向 `(?<![a-z0-9_])full(?![a-z0-9_])`。真实 `--enforce`、`--staged-diff` 均命中 C5，`TOTAL=1 effective=1`、exit 1；`当前fuller…` 对照保持 `TOTAL=0`、exit 0。 |
| C9：`共有42 AI Agents协同。`、`现有14 Agents协同。` | `RESOLVED` | 八轮原问题见[审查报告:584](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/_bmad-output/审查/codex-review-CARD-G1-5.md:584)。英文/混排入口在[规则:136](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:136)、[规则:138](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:138)、[规则:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:140) 使用负向后顾。两句两档均命中 C9、exit 1；`共有120 个智能体协同。`、`共有120 AI Agents协同。` 均 `TOTAL=0`、exit 0。 |

八轮四个新增回归位于[测试:169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:169)，由[参数入口:200](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:200)验证正确规则及 enforce/report 退出语义。

### 新发现分级

已穷举当前 11 条规则、37 个 pattern。规则级 `\b` 只存在于 [C2:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:74)、[C10:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:150)、[C10:151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:151)、[C11:160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:160)、[C11:164](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:164)、[C11:166](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:166)。

1. **BLOCKER — C11 hard-forbidden 直接族仍可伪绿**

   共残留 7 个边界端点：`mean/indicate/equal` 词尾、系词前、成功词尾、直接谓词前及词尾。代表反例：

   ```text
   Skipped checks mean成功。
   Skipped checks indicate成功。
   Skipped checks equal成功。
   Skipped状态is success。
   Skipped is 成功了。
   Skipped检查pass。
   Skipped checks pass了。
   ```

   每句在真实 `--enforce`、`--staged-diff` 均为 `TOTAL=0 effective=0`、exit 0；加正常空格的对照均命中 C11、exit 1。C11 是不可由 evidence/legacy 放行的 hard-forbidden，故沿用既定分级为 BLOCKER。

2. **HIGH — C2 三处 Unicode 边界残留**

   [规则:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:74) 的量词前、量词后、`vault` 后共三个 `\b`：

   ```text
   当前any vault 一键可用。
   any类 vault 一键可用。
   当前 any vault一键可用。
   ```

   两档均 `TOTAL=0`、exit 0；`当前 any vault 一键可用。` 对照命中 C2、exit 1。

3. **HIGH — C10 四处 Unicode 边界残留**

   ```text
   当前available on mobile。
   available on mobile端。
   当前mobile is available。
   mobile is ready了。
   ```

   两档均 `TOTAL=0`、exit 0。[新增 fallback:152](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:152) 能拦 `当前mobile可用。`，但未覆盖上述四个既有英文 direct-family 边界。

4. **MEDIUM — C11 英文否定词 CJK 前邻产生 false-red**

   [否定守卫:123](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:123) 的英文 negator 前导 `\b` 使 `Skipped状态not等同成功。` 被错误阻断；增加空格后正确放行。它不会造成伪绿，按本轮纪律不升 BLOCKER/HIGH。

静态勘误：开发者说明称 C9“全部”改为 `(?<![0-9a-z_])`，但当前 [规则:137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:137)、[规则:141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:141)、[规则:142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:142) 仍是 `(?<![0-9])`。这不影响本轮点名句及三位数尾部行为，记为 INFO，不重开 C9 HIGH。

以上反例均为单行可见文本、正常空格或正常中英混排；未使用 HTML 实体、零宽/全角混淆、单下划线、跨行、开放同义改写或渲染/语义推断形态。

### 实跑证据

在 `backend/` 执行：

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit/test_check_readme_claims.py -q -p no:cacheprovider
```

结果：`collected 101 items`，`101 passed, 10 warnings in 3.29s`，exit 0。

本仓生产入口：

- `--report`：README L35/L50/L68 三条 C9 均为 `[legacy]`；`TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0。
- `--enforce`：相同计数，输出 `OK`，exit 0。
- 规则磁盘 SHA、`--print-rules-sha`、脚本常量一致：`84c56cc6963e5ee98ea457666a44548b6a1a38692f546d6ced60fe10dc606150`。
- 反例均在系统临时 Git fixture 通过 [full/staged 生产分支](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:705)重放。
- 证据绑定 `card/n4-readme@0204d2eb161e2d9111ce2d13cc98102c862c050a` 当前 working-tree bytes；审阅前后 `git status --short` 一致。目标脚本、规则、测试仍未跟踪，不能外推为 HEAD 或 hosted CI。
- 当前会话未提供 Graphiti 工具；所有实质结论均由当前 checkout 静态检查和真实入口重验得出。

BLOCKER/HIGH 清零: 否  
八轮处置复核: 不通过



---

## 附录：十轮复核（九轮穷举残留处置终验，ultra 档）

结论：终验不通过。九轮 14 个点名漏判均已修复，但 C11 新增后顾制造了新的 hard-forbidden 伪绿，仍有 1 个 BLOCKER。

### 九轮 finding 状态

| 九轮 finding | 十轮状态 | 验证依据 |
|---|---|---|
| BLOCKER — C11 七个 Unicode 端点 | `RESOLVED` | [C11 patterns](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:158) 已使用 ASCII 定向 lookaround；七句在 enforce/staged 均命中 C11、exit 1。 |
| HIGH — C2 三个端点 | `RESOLVED` | [C2 pattern](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:74) 已覆盖量词前后及 vault 词尾；三句均拦截，`Many...` 保持零命中。 |
| HIGH — C10 四个端点 | `RESOLVED` | [C10 patterns](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:150) 已改定向边界；四句均拦截。 |
| MEDIUM — CJK 前邻英文 negator false-red | `PARTIALLY-RESOLVED` | [_NEG_TAIL_RE](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:122) 已修，点名句 `Skipped状态not等同成功。` 正确放行；但 p5 仍会重新误判其他已枚举谓词，见下。 |

[回归集](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:175)包含全部 14 个阳性；[参数入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:219)验证正确规则、enforce=1、report=0。临时 Git fixture 复算结果：14/14 阳性在 enforce/staged 均拦截；四类阴性对照（120 类含中英两句，共五行）全部放行。

### 新发现

- `BLOCKER` — C11 宾语排除引入直接等同句伪绿。

  反例：`Skipped checks 等于成功。`

  full report、enforce、staged-diff 均为 `TOTAL=0 effective=0`、exit 0。根因是 [p5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:166) 用 `(?<!等于)` 排除了“成功”，但 [p2 谓词表](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:160) 没有 `等于` 接管。这是单行、正常空格和中英混排的 [L633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:633) 直接等同表达，不是 DOCUMENTED-LIMIT。

- `MEDIUM` — p5 否定宾语排除仍不完整。

  `Skipped状态not等价成功。` 在 report 中 `TOTAL=1 effective=1`，enforce/staged 均 exit 1。`等价` 已在 p2 明确枚举，不属于开放式同义扩面。

未发现新的 HIGH；既定 DOCUMENTED-LIMIT 未重开。

### 实跑证据

- 指定 pytest：`118 passed, 10 warnings in 6.63s`，exit 0。
- 本仓 `--report`：`TOTAL=3 effective=0 escaped=0 legacy=3`，exit 0。
- 本仓 `--enforce`：同计数并输出 `OK`，exit 0。
- 11 rules / 37 patterns；规则文件 `\b` 数量为 0。
- 磁盘、`--print-rules-sha`、[脚本常量](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:103)一致：`64e472ab48d2755eaeb9d105a03c4a7f941ace568516d2c50e6a7c322f4b78aa`。
- 证据绑定当前 dirty worktree bytes：`card/n4-readme@0204d2e`；审阅前后状态一致，未修改仓库。

BLOCKER/HIGH 清零: 否  
九轮处置复核: 不通过



---

## 附录：十一轮复核（十轮 1B+1M 处置终验，ultra 档）

### 十轮 finding 状态

| Finding | 状态 | 验证依据 |
|---|---|---|
| BLOCKER — `Skipped checks 等于成功。` 伪绿 | `RESOLVED` | p2 已纳入“等于”：[规则:160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:160)；回归见[测试:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:190)。生产 CLI 实跑：report `TOTAL=1 effective=1`、exit 0；enforce 同计数、exit 1。 |
| MEDIUM — p5 否定宾语排除不完整 | `PARTIALLY-RESOLVED` | 点名句 `Skipped状态not等价成功。` 已正确零命中；p5 已补 `(?<!等价)`：[规则:166](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:166)，回归见[测试:216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/tests/unit/test_check_readme_claims.py:216)。但正常空格形态仍有同根 false-red。 |

### 六谓词邻域

`P ∈ {等同、等价、等于、视为、算作、当作}`：

| 形态 | 生产 CLI 结果 |
|---|---|
| `Skipped checks P成功。` | 6/6 拦截 |
| `Skipped checks P 成功。` | 6/6 拦截 |
| `Skipped状态notP成功。` | 6/6 正确放行 |
| `Skipped checks not P 成功。` | 0/6 放行，六句全部 false-red |

新发现：`MEDIUM`。谓词与“成功”之间加入一个普通 ASCII 空格后，p5 的立即后顾无法识别谓词，宾语“成功”被重新当作直接谓词。否定掩码逻辑见[脚本:453](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:453)，六个固定后顾见[规则:166](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/readme_claims_rules.yaml:166)。这是 false-red，不是漏判或伪绿，按既定纪律不升 BLOCKER/HIGH。

### 实跑证据

从 `backend/` 执行：

- `.venv/bin/pytest tests/unit/test_check_readme_claims.py -p no:cacheprovider -q`：exit 0，`120 passed, 10 warnings in 2.73s`。
- `--report --root ..`：exit 0，README L35/L50/L68 三条 C9 legacy；`TOTAL=3 effective=0 escaped=0 legacy=3`。
- `--enforce --root ..`：exit 0，同一计数并输出 `OK`。
- `--print-rules-sha`、磁盘 SHA-256、[脚本常量:103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n4-readme/backend/scripts/check_readme_claims.py:103)一致：`4825e71a58e2bc8ce7167815bb58085278a8f422065e21a22fbcc4f48881aded`。
- 反例仅写入系统临时目录；未修改 worktree。

BLOCKER/HIGH 清零: 是  
十轮处置复核: 不通过
