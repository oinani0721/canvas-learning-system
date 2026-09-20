> 批次: BATCH-2026-09-18-第十五批 · 车道 P6 · 卡 CARD-HARNESS-TREE-PARSE-R2 · **人审替代轮 v3**
> ⚠️ 非 Codex 轮次（通道断在授权层，见 `codex-channel-diagnosis-20260919T041838.txt`）。
> 形态: 4 维只读查找 + 每条发现 2 个独立镜头证伪（falsify / consequence）
> 审查绑定: `9132586f`（实测 `git diff --stat 9132586f HEAD -- . ':(exclude)_bmad-output'` = 0 行）
> 规模自证（数值来自 workflow 完成通知的 `<usage>` 段，不在 result JSON 里）:
> `agent_count=12  agents_done=12  agents_error=0  agents_skipped=0  agents_empty_result=0`
> `subagent_tokens=1,802,463  tool_uses=313  duration_ms=1,159,742`（≈ 19 分 20 秒）
> 本轮 prompt 把 v2 的 16 条结论（1 已修 + 3 已登记 MEDIUM + 12 已证伪）**全部写入「不要再报」**，
> 并显式要求「没有够 HIGH 的新发现就交空 findings，本轮目的是确认能不能收口，不是凑发现数」。

---

# 结果

原始发现 **4** 条（v2 是 16 ⇒ **收敛**）→ 全部送证伪 → 存活 **1** 条

```
BLOCKER 0   HIGH 1   MEDIUM 0   LOW 0
```

## 存活（已整改）

### [HIGH] 词法否决正则里的 `^` 行首锚无门：删掉它 227 格全绿，而注释掉/散文里提到 `harness_tree:` 的合法 config 从「回退父树」变成硬拒

- **锚**: `def test_g33r2_lexical_veto_does_not_over_match_a_similar_key`

**场景**：

生产 `_lex = re.search(r"^harness_tree[ \t]*:", _raw, re.M)` 有三个承重 token：`^` / `[ \t]*` / 末尾 `:`。本轮整改给后两个各补了一格（`honest_probes_spaced_key` 与 `..._does_not_over_match_a_similar_key`，负控段⑫ 2/2 恰好锁住），**`^` 一个门都没有**。实测（/tmp 副本）：把正则改成 `r"harness_tree[ \t]*:"`（只少一个字符，且「行首锚看着多余」正是清理正则时最常删的一种），227 格**一格不红**。行为反例（同一副本实跑，pristine ↔ mutated 对照）：① `# harness_tree: /old/tree\nvault_id: "v"\n`（用户把键注释掉，SKILL.md docstring 明文承诺「注释掉的 `# harness_tree:` 不顶格 ⇒ 正则不命中, 也照旧回退」）；② `vault_id: "v"   # 想换树就改 harness_tree: 这一项`；③ `note: "改 harness_tree: 就能换树"\nvault_id: "v"`。三份真 PyYAML 都解析成功且顶层无该键，pristine 全部 `ok → 回退父树`，mutated 全部 `SystemExit：解析结果与文件内容不符 (文件第 1 行明文写着 harness_tree 键…)` —— 一份完全正确的 config 被当成「解析器不可信」硬拒，且这三种形态都**不在**卡里列全的那份「已接受误拒面」里（那份只列顶格命中的形态）。

<details><summary>镜头 1（falsify）判词</summary>

场景为真，已在 scratchpad 隔离镜像里双向实证（本树零写入，SKILL.md sha256 仍为 d64d3b8c…，git status 干净）。① 生产 SKILL.md:650 `_lex = re.search(r"^harness_tree[ \t]*:", _raw, re.M)` 三个承重 token 中，`^` 无任何行为门：把它删成 `r"harness_tree[ \t]*:"`（少一个字符）后，在镜像树上跑 test_harness_tree_parse_r2.py 实测 44 passed / 一格不红（基线同为 44 passed）。② 负控存档 negctl-12-lex-regex-both-directions-20260919T055635.txt 自证只跑了两向（`[ \t]*`、末尾冒号），baseline ran=44，`^` 那一向从未跑过。③ 对 ledger 侧做了字面量全扫：两份测试文件里 pristine/mutated 匹配结论不同的字符串只有三类 —— docstring；`_CFG_FORMS["flow"]`/`_TRUNCATING_FORMS["flow_mapping"]`（诚实控制组里 `_doc` 有该键 ⇒ 否决不触发，说谎/截断组死在键级探针层，均先于读 config）；以及含 `"# harness_tree: /a/b"` 的 `_HEADED_LINES`/`_WHOLE_DOCS` 表 —— 后者只被 test_g33r2_harness_tree_no_pyyaml_never_returns_a_tree 消费，而该门 `monkeypatch.setitem(sys.modules, "yaml", None)`，词法否决路径根本到不了。④ 行为反例用与测试同一条 AST 抽取路径 pristine↔mutated 对照实跑：`# harness_tree: /old/tree\nvault_id: "v"\n`、`vault_id: "v"   # 想换树就改 harness_tree: 这一项\n`、`note: "改 harness_tree: 就能换树"\n…`、`outer:\n  harness_tree: /a/b\n` 四份真 PyYAML 解析成功且顶层无该键的合法 config，pristine 全部 `ok → 回退父树`，mutated 全部 `SystemExit：解析结果与文件内容不符 (文件第 N 行明文写着 harness_tree 键…)`。其中第一种正是 SKILL.md 自己 docstring 明文承诺的「注释掉的 `# harness_tree:` 不顶格 ⇒ 正则不命中, 也照旧回退」，四种都不在卡里列全的「已接受误拒面」（那份只列顶格命中形态）内。逐条核过常见证伪原因，均不成立：(a)「更早一道判据拦下」——repo 内确有两道会红的变更检测（check_managed_files 的整文件 sha256，我实测现网文件摘要恰为基线值 d64d3b8c…；以及 check_tmp_blocks 的 B305 块指纹），但本卡验收单 §五⑮ 已自定口径「指纹门只说文件变了，不理解变的是哪条判据 ⇒ 不构成覆盖」，v2 对 `[ \t]*`/`:` 两向定 HIGH 并补门用的正是同一口径，故不证伪，只说明该变异并非全仓不可见；(b)「属已修的 v2 HIGH」——v2 整改只补了两格两 token，验收单 §五⑯ 明确登记同类盲区「未系统清查」，且本轮 prompt 显式邀请报「藏在正则字面量里、无门测量」的具体判据；(c)「路径到不了 / 输入不是同一个东西」——veto 路径在真 PyYAML 下正常可达，四份输入就是 `_harness_tree` 实际读到的 `_raw`。如实登记两点：一是 pristine 代码本身在这四种输入上行为正确，本条是覆盖缺口（门恒绿）而非现存缺陷；二是变异后的失效方向是**可见的 fail-closed 误拒**而非静默绑错树，严格程度低于 `[ \t]*` 那一向——但卡已为对称的另一向（末尾冒号，同样只产生误拒）补了门，且本轮把「门恒绿 + 能说出具体场景」列为 HIGH 门槛，故按 HIGH 呈报。

</details>

<details><summary>镜头 2（consequence）判词</summary>

场景成立（我在 /tmp 副本独立复现，被审树零改动：porcelain 空、HEAD 仍 9132586f、绑定 diff 0 行），但后果落在本卡口径的 MEDIUM 桶，够不上 HIGH。

一、事实两半都实测确认
1) 只改生产那一行 SKILL.md:650 `r"^harness_tree[ \t]*:"` → `r"harness_tree[ \t]*:"`：pristine 副本 `2 failed, 356 passed`（那 2 条是副本环境产物 test_write_point_survey_no_third_implementation / test_r6_schema_declares_identity_key_integrity_owner，与本变异无关），mutated 副本 `2 failed, 356 passed` —— 同样那两条，红格集合 delta = 0。我跑的是两个文件的全部 358 nodeid（比发现里说的 227 格更宽），`^` 确实一个门都没测。
2) 行为反例复现：4 份真 PyYAML 解析成功、顶层无该键的合法 config —— `# harness_tree: /old/tree`、`vault_id: "v"   # …改 harness_tree: 这一项`、`note: "改 harness_tree: 就能换树"`、以及 `nested:\n  harness_tree: /a/b` —— pristine 全部 `ok`（回退父树），mutated 全部 `exit：解析结果与文件内容不符 (文件第 N 行…)`。这四种都不在卡里列出的「已接受误拒面」（那份只列顶格命中形态）。

二、但后果方向与 v2 那条 HIGH 相反，三条 HIGH 判据逐条不成立
- 静默绑错树：不可能。`re.search` 去掉 `^` 是匹配集的**严格超集**，而 `_lex` 只进 `if _lex and (key not in _doc): raise` —— 否决只会**多发**，永不少发。r10 H1 的复活路径要求否决**漏发**，这个 token 结构上到不了。这正是与 `[ \t]*` 的不对称：那一个去掉是**收窄**⇒ 漏发 ⇒ 静默绑错树，所以 v2 判 HIGH；`^` 是**放宽**。
- 写出半态：不成立。`_harness_tree` 在 Step 2.9 预检块 SKILL.md:259 就被调用（`_REPO = _NS["_harness_tree"](VAULT)`，随后 print「可以进 Step 3 写分」），拒在 Step 3 写分**之前**，零写入，拒因还带 `_HALFSTATE` 标记。
- 门恒绿：不成立（按本卡「假门」的语义）。没有任何门**声称**覆盖 `^`；negctl-12 存档如实只列它实际跑的两条变异，验收单 §五⑯ 已明写同类盲区未系统清查。这是**覆盖缺口**，不是「已有门谎报绿」。

三、定级
剩下的是：一条承重 token 无门（覆盖面）+ 一个假想回归，其表现形态是**可见的、指明行号的、零写入的 fail-closed 拒绝**。卡的口径原文：「可见的拒绝（哪怕是误拒）、只影响文案或覆盖面 ⇒ MEDIUM 或 LOW」—— 逐字命中。

不判 refuted，因为它不是「不够完美」：① 卡在 §五⑯ 明确邀请「报具体的某一条藏在正则字面量里、没有门测量的判据」，这条正是；② 生产 docstring（SKILL.md:645 段）**明文承诺**「注释掉的 `# harness_tree:` 不顶格 ⇒ 正则不命中, 也照旧回退」，这是一条零门的行为契约，而注释掉一个键比 `harness_tree_backup:`（本轮反而补了门的那一向）常见得多；③ 本轮整改给同属「放宽」向的末尾冒号补了门，按卡自己的标准 `^` 同向同类。

取 MEDIUM 而非 LOW：触发写法极常见 + 触发后 `/quiz-answer` 对该 vault 整个不可用（砖化直到用户改 config）。但明确低于本轮 HIGH 门槛 —— 若本轮只收 HIGH，这条应当登记不阻断，不进 findings。

另：发现标题里的「227 格」与实测对不上（本文件 44 + ledger 全量 = 358 nodeid；卡文里的 207/209 是 `-k harness_tree` 过滤后的数）。结论不受影响 —— 我跑的是更宽的超集，delta 仍为 0。

</details>

## 被证伪（3 条）

- **[HIGH]** 契约不探 `_vault_id_of`，于是「只发 backend/scripts 的 harness 树」全程绿灯通过预检，Step 3 写完分后 Step 4 在 `_vid` 无条件拒写 = 本卡要消灭的那个半态
  - 证伪要点: 机制属实但**不构成本卡的 HIGH 新发现**，五条各自独立成立：

**① 那条判据不是本卡的面（决定性）**。`_vid = _vault_id_of(Path(EV))` + `raise SystemExit("[quiz-answer] vault 归属无法绑定…")`（SKILL.md:1771-1773）**在本卡 diff 之外**：`git --no-pager diff --no-color a05732c9 HEAD -- canvas-vault/.claude/skills/quiz-answer/SKILL.md | grep -n "vault 归属\|_vault_id_of(Path(EV))"` = **0 命中**（a05732c9 = `0168760e^` = 本卡基线；同一 diff 的 stat 是 +
- **[HIGH]** 键级探针的两个合取项 `a==1` / `b==2` 各自无门：删掉其中一个 token，227 格全绿，而 r10 H1 原样复活（静默绑错树）
  - 证伪要点: 证伪（三条独立理由，任一足以把它挡在 HIGH 之外）：

【1】场景里给的那份输入到不了它声称的后果。finding 的 config 是 `"harness_tree": <目标树>\nnote: docs\nother: x\n` —— 它**没有 `vault_id` 键**。SKILL.md:1771 有一条**无条件**的下游判据 `_vid = _vault_id_of(Path(EV))`，EV = `VAULT/learning_events.jsonl`，`backend/scripts/validate_learning_events.py:1347` 的 `_vault_id_of` 读的正是 `ledger_path.parent/.canvas-config.yaml` = `_harness_tree` 手里那**同一份
- **[LOW]** `never_returns_a_tree` 新增的 13 条 `_WHOLE_DOCS` 对生产零判别力：缺库分支在 `import yaml` 就退出，config 文件从头到尾没被打开过
  - 证伪要点: 证伪。机械事实成立但不构成发现——它正是被审代码自己明写的设计。

1) 代码路径核实：`SKILL.md:510` 只拼路径字符串；`import yaml` + 两道探针在同一个 `try/except Exception` 里（`:527` 起），失败即 `SystemExit`；`open(_cfg_p)` 在 `:623`，确实在其后。所以 `sys.modules["yaml"]=None` 下 config 从头到尾没被打开，73 个参数跑同一条字节相同的路径。这一点发现说对了。

2) 但这不是缺陷，是门**已写明并有意为之**的不变量变更，在同一份被审文件里两处白纸黑字：
   · 测试 docstring（test_g3_2_review_ledger.py:7700）：「旧不变量……在降级解析被整段删除之后**退化成了恒真**…

---

## 主 session 裁定

两个镜头对这条 HIGH 给了**不同定级**：镜头 1 判 HIGH（按本轮「门恒绿 + 能说出具体场景」门槛），
镜头 2 判 **MEDIUM**，理由是结构性的 ——

> `re.search` 去掉 `^` 是匹配集的**严格超集**，而 `_lex` 只进 `if _lex and (key not in _doc): raise`
> ⇒ 否决只会**多发，永不少发**。r10 H1 的复活路径要求否决**漏发**，这个 token 结构上到不了。
> 这与 `[ \t]*` **不对称**：那个删掉是**收窄** ⇒ 漏发 ⇒ 静默绑错树（v2 判 HIGH）；`^` 是**放宽** ⇒ 可见误拒。

⇒ **同一条正则的三个 token，失效方向不同，定级就不同**。「这条判据没有门」不足以定级，
要问**它坏掉时系统往哪个方向坏**。

⚠️ 但主 session **不自判通过**（协议：车道对 HIGH 的驳回要写理由，不能自判通过）。
处置改为**把门补上**：只加一格测试（3 个形态）、不碰生产代码，补完这个正则的三个 token 就完整。
见 `negctl13-three-tokens-and-loadbearing-*.txt`（三向各自「红格集合恰好 == 声称的那一组」）。

⚠️ 镜头 2 还纠正了发现里的数字：标题写「227 格」，实测是 358 个 nodeid（更宽的超集），delta 仍为 0。
**关于证据的断言要自己数一遍** —— 本卡第 N 次撞上这条。
