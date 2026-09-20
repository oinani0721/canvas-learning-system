> 批次: BATCH-2026-09-18-第十五批 · 车道 P6 · 卡 CARD-HARNESS-TREE-PARSE-R2 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-R2.md)"`
> 审查绑定: `0168760e`（送审时的 HEAD；**本轮之后车道按其发现整改，HEAD 已前进到 `09f190a3`，故本轮不绑最终 HEAD**）
> 会话头自证（抄 `.stderr` 中的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 4 行） / `model: gpt-6-astra`（第 7 行） / `reasoning effort: ultra`（第 11 行）

---

# ⚠️ 本文件是**车道记录**，不是 Codex 的输出

**Codex 本轮的 stdout 是 0 字节**（`wc -c` 实测 0）。原因写在 `.stderr` 末尾：

```
ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage
to purchase more credits or try again at Sep 24th, 2026 2:05 AM.
```

`tokens used: 56,616`。按协议「0 字节存档不入 commit」，那个 0 字节的
`codex-review-CARD-HARNESS-TREE-PARSE-R2.md` **未入库**（已就地清理）。

**配额已复测**（协议教训「外部服务的重置时间是一次观测不是不变量」，不继承结论）：
2026-09-18 20:20 用一个最小 prompt（「只回答两个字：可用」）重发 → 同样 `rc=1` + 同一条
usage limit。⇒ 本次是**真耗尽**，不是一次误判的观测。

按协议：「0 字节存档重发一次，再 0 字节 → 主 session 人审替代，不等配额」。

---

## 但本轮**实质审查已经发生**，且留下了可核的硬数据

`.stderr` 里有完整的推理轨迹与**一次它自己跑的实测**。轨迹标题（⚠️ 标题不是裁定，
仅用于说明它审到了哪一步）：

```
Locating relevant context → Reviewing scoped changes → Checking the preflight segment
→ Verifying PyYAML setup → Preparing shellQuote helper → Testing AST negative controls
→ Reading source records → Checking option scope → Checking worktree hashes
→ Digesting likely mismatch → Verifying root hashes → Preparing in-memory harness
→ Building virtual tree cases → **Refining finding severity** → **Assessing preflight tests**
```

它在 `Building virtual tree cases` 那一步**真的执行了一段只读 python**（`exec ... succeeded in 0ms`），
把当时的 `_harness_tree` 从 SKILL.md 抽出来，对 4 种 config 文本 × 2 种解析器跑了一遍。
**原样输出**（从 `.stderr` 逐字抄录）：

```
bare real            OK   /Users/…/card-p6-skills-w
bare constant_a1     EXIT [quiz-answer] .canvas-config.yaml 解析结果与文件内容不符 (文件第 1 行明文写着 harness_tree 键, 解析器却没有给出它; 它给出的是 dict)
quoted real          OK   /Users/…/card-p6-skills-w
quoted constant_a1   OK   /in-memory-parent
flow real            OK   /Users/…/card-p6-skills-w
flow constant_a1     OK   /in-memory-parent
false_refusal real   EXIT [quiz-answer] .canvas-config.yaml 解析结果与文件内容不符 (文件第 2 行明文写着 harness_tree 键, 解析器却没有给出它; 它给出的是 dict)
false_refusal constant_a1 EXIT （同上）
```

三条**未被拦下的输入 / 门未覆盖的路径**由此显形：

| # | 形态 | 当时的行为 | 性质 |
|---|---|---|---|
| 1 | `"harness_tree": v`（**带引号的键**）+ 恒返 `{"a":1}` 的假模块 | `OK /in-memory-parent` = **静默回退父树** | r10 H1 在这种写法下**依然成立** |
| 2 | `{harness_tree: v}`（**整份 flow mapping**）+ 同上 | `OK /in-memory-parent` = **静默回退父树** | 同上 |
| 3 | `note: "open<换行>harness_tree: /a/b"` + **真 PyYAML** | `EXIT` = **误拒一份合法文档** | 词法否决的误拒面 |

⇒ 车道第一版的词法否决 `^harness_tree[ \t]*:` 问的是「文件里有没有**顶格裸键**」，
那依赖用户的**书写形式**；而形态 1/2 是生产**明确支持**的另外两种合法写法（既有门
`..._noncanonical_key_form_is_honored` 与 `..._no_pyyaml_refuses_whole_flow_document`
就在测它们），行首都不是 `harness_tree`，正则一条都不命中。

---

## 车道的处置（**不采信，全部独立复现后再改**）

**① 独立复现**：`evidence-harness-tree-r2/verify-codex-r1-findings.py`（入档）+
`verify-codex-r1-20260918T195846.txt`。用本卡测试同法（AST 从 SKILL.md 逐字抽取、
`tmp_path` 派生、零 live）重跑，并**带三个对照输入**：

```
A 引号键 + 恒返{'a':1}              OK    ⛔ 回退父树（config 指着 target-tree）
B flow mapping + 恒返{'a':1}        OK    ⛔ 回退父树
C 值内跨行文本 + 真 PyYAML           EXIT  （误拒）
D 裸键 + 恒返{'a':1}（对照：应被拒）    EXIT  ✓ 第一版在这一种写法下有效
E 引号键 + 真 PyYAML（对照：应采用）    OK    ✓ 采用了 config 指的那棵树
F flow + 真 PyYAML（对照：应采用）     OK    ✓ 同上
```

E / F 两个对照证明 A / B 的失败**不是因为 config 写错了** —— 三条发现全部**如实成立**。

**② 整改**（commit `09f190a3`，详见该 commit message 与验收单 §二）：

- **键级探针**（主力，与书写形式无关、零误拒）：`safe_load("harness_tree: __quiz_answer_key_probe__")`
  必须给出该键。它**不看用户的文件**，所以恒返 `{"a":1}` / 恒返 `{}` / 返列表的模块
  **无论用户怎么写**都被拦。
- **词法否决补「值内文本」豁免**：只在命中文本不落在任何已解析值内时才否决 ⇒ 修掉形态 3。
- docstring 的威胁模型段按实测更正（第一版「探测 7 形态零误拒面」的结论**是错的**，已留档）。

**③ 整改后重跑**（全部在 `09f190a3`）：

- 新文件 19 → **22 passed**（lying_parser 重构成两层 + 新增误拒控制组）
- `test_g3_2_review_ledger.py` 整文件 **314 passed**（其假模块同批放行第二道探针，
  否则 `parse_oserror` / `parse_valueerror` 两格会从「解析这一步坏了」静默掉回
  「拿不到 PyYAML」—— 已实测并加 `assert _KEY_PROBE_DOC in CODE` 防手抄漂移）
- `tests/skills` 目录级 **582 passed**
- 负控**四段**（见 `negctl-{1,2,3,4}-*.txt`），其中段① 与段④ 互为**对角线**：

  | 段 | 拆掉的那一层 | 红 | 绿 |
  |---|---|---|---|
  | ① | 词法否决 | `honest_probes_{empty_mapping,list}` | `constant_*` 三格 + 两控制组 |
  | ④ | 键级探针 | `constant_{quoted_key,flow_mapping}`（红在「返回了一棵树」）+ `constant_bare`（红在「拒因落错层」） | `honest_probes_*` + 控制组 |

  ⇒ 两层**有重叠但不等价**：裸键写法两层都拦得住，而引号键 / flow mapping
  **只有键级探针拦得住** —— 这正是本轮发现的那两条路径。

---

## ⛔ 移交主 session（协议 §1 / D-15）

**本卡状态：一轮实质审查（发现 3 条，全部已复现并整改）+ 整改后未再审。**

D-15 要求「审后再改代码 ⇒ 必再送一轮，且末轮绑最终 HEAD」。本轮整改后需要的那一轮
**因配额耗尽发不出去**（已按协议重发并复测）。协议对此的口径是「再 0 字节 → 主 session
人审替代，不等配额」。

请主 session 裁定：
1. 以人审替代整改后的那一轮（本文件 + `verify-codex-r1-*` + 负控四段是可核的输入面）；
2. 或排入配额恢复后的补审（存档名预留 `codex-review-CARD-HARNESS-TREE-PARSE-R2-r2.md`，
   ⚠️ 轮次后缀一律小写 `-rN`，因为本卡卡号已含 `-R2`，而 T7-A 的 `-r2` 在大小写不敏感
   文件系统上会撞 —— 已 `ls | grep -ixF` 核过零冲突）。

**车道未自判通过**：本轮 Codex 未给出 BLOCKER/HIGH/MEDIUM/LOW 分级输出，
所以「BLOCKER = 0、HIGH = 0」这个条件**本卡无法自证**，按未完成登记。
