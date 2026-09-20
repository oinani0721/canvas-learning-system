> 批次: BATCH-2026-09-18-第十五批 · 车道 P6 · 卡 CARD-HARNESS-TREE-PARSE-R2 · **人审替代轮 v4（收口轮）**
> ⚠️ 非 Codex 轮次（通道断在授权层，见 `codex-channel-diagnosis-20260919T041838.txt`）。
> 形态: 4 维只读查找 + 每条发现 2 个独立镜头证伪（falsify / consequence）
> 审查绑定: `43bea775` = **最终代码**（实测 `git diff --stat 43bea775 HEAD -- . ':(exclude)_bmad-output'` = 0 行）
> 规模自证（数值来自 workflow 完成通知的 `<usage>` 段，不在 result JSON 里）:
> `agent_count=6  agents_done=6  agents_error=0  agents_skipped=0  agents_empty_result=0`
> `subagent_tokens=903,677  tool_uses=152  duration_ms=567,552`（≈ 9 分 28 秒）
> 本轮 prompt 把 v2 的 16 条 + v3 的 4 条结论**全部写入「不要再报」**，并明写：
> 「这条正则的三个承重 token 现已全部有门，这条线已闭合」「没有够 HIGH 的新发现就交空 findings ——
> 交一条勉强的 MEDIUM 不会让任何人更安全，只会再触发一轮整改、再让绑定失效一次」。

---

# 结果

原始发现 **1** 条 → 存活 **0** 条

```
BLOCKER 0   HIGH 0   MEDIUM 0   LOW 0
```

⇒ ✅ **满足卡文收口条件**：绑最终 HEAD 的一轮 BLOCKER = 0、HIGH = 0。

## 收敛轨迹

| 轮次 | 绑定 | 原始 → 存活 | 存活的是什么 |
|---|---|---|---|
| v2 | `31dfd0de` | 16 → 4 | 词法正则 token ①`[ \t]*` ②末尾`:` + 3 条 MEDIUM |
| v3 | `9132586f` | 4 → 1 | 同一正则 token ③`^` |
| **v4** | **`43bea775`** | **1 → 0** | — |

三轮存活的 HIGH 全部落在**同一条正则的三个 token** 上 —— 一条有限、可穷尽的线，
补齐即闭合。v4 的 `parse_layers` 维度专门核过「有没有第四个结构元素」：
键名字面量由 `_LYING_CASES` 全体覆盖、`re.M` 与 `re.search`→`re.match` 由 `honest_probes_*` 覆盖，
**没有第四个无门的结构元素**。

## 唯一发现（LOW，已证伪；按协议登记不阻断，**不修**）

**[LOW]** skill_portability_lint 新注释里的行号/位移算错（写 `:267`/+62，实际登记且正确的是 `:281`/+76），下一个重算基线的人会照它算出错值

<details><summary>镜头 1 证伪理由</summary>

Facts check out but the harm scenario cannot occur. (a) The numbers were correct when written: at the card's first commit 0168760e the `**4b · 用 Write 工具写 payload**` line really was at 267 (+62); it moved to 275 at 4b671eb7 and 281 at af6e2626 — I walked all 7 SKILL.md commits. So it is a stale round-log entry, and the sibling TMP_BLOCK_BASELINE comment has exactly the same property (narrates `:229`→`:299` and "round-1 后仍是 :291" while registering `B305`), i.e. layered stale intermediates are this file's established comment convention, not something this change introduces. (b) The mis-derivation cannot survive: check_opaque_tmp (skill_portability_lint.py:3076-3085) fails with `期望={want} 实测={actual} (新增=… 缺失=…)` printing the full `行号:指纹` list, and check_tmp_block (:3007-3009) does the same. A maintainer who derived 267 from the comment, or "fixed" 281 back to 267, gets an immediate red gate whose message hands them `281:44b7655dd97c27b7`. The recompute protocol is "run the lint and take 实测", not arithmetic from a comment. (c) Verified the registered value is right: line 281 is the 4b prose hashing to 44b7655dd97c27b7; line 267 is `` `Edit` **检验白板 md** frontmatter： `` (bd640602afb8d2c3). No input makes the code do anything wrong, no silent wrong state is reachable, and no gate is weakened — the comment is documentation drift whose only failure mode is a loud, self-correcting test failure.

</details>

<details><summary>镜头 2 证伪理由</summary>

事实成立但后果够不上「做错事」。实测：SKILL.md 第 281 行指纹 = 44b7655dd97c27b7，与登记值一致；第 267 行是 `` `Edit` **检验白板 md** frontmatter： ``、指纹 bd640602afb8d2c3。所以那条注释里的「`:205` → `:267`，+62 行」确实写错、也确实与同批 `TMP_BLOCK_BASELINE` 的「S205 → S281，+70/+8/+6 = +76」自相矛盾（+76 才对，205+76=281）。但代码登记值是对的，`pytest -k "opaque_tmp_lines_match_baseline or tmp_block"` 3 passed。关键在消费端：`check_opaque_tmp()`（skill_portability_lint.py:3055）对 `行号:sha16` 做**精确集合相等**，不等就打印「期望=… 实测=…（新增/缺失）」——且登记项自带内容指纹（r11 HIGH-3 的产物），所以写错行号既不可能静默命中别的行、也不可能变成塞真实债的槽。假设场景成立时的实际路径是：后人照注释算出 267 或把 281「修」回 267 ⇒ 下一次 tests/skills 立刻红、且报文直接指名正确行号 ⇒ 一次运行内自纠。既不是静默绑错树、不是半态、也不是门恒绿，而是可见的、带定位信息的失败。属纯文案陈旧，判 refuted。

</details>

> ⛔ **为什么不修**：协议对 LOW 是**登记**不是修。这条注释的登记值本身是对的
> （SKILL.md:281 指纹 = `44b7655dd97c27b7`，与 `OPAQUE_TMP_BASELINE` 一致），
> 错的只是叙述里的中间行号（写 `:267`/+62，实际 `:281`/+76 —— 267 是卡的**首个** commit
> `0168760e` 时的真实行号，后续 commit 把它推到 275、281，属**陈旧的轮次记录**）。
> 消费端 `check_opaque_tmp` 做 `行号:指纹` **精确集合相等**，报错直接打印
> `期望=… 实测=…（新增/缺失）`，照注释误推会在**一次运行内**红并自纠。
> ⇒ 修它 = 亲手打破刚拿到的终审绑定、再触发一轮。**登记，不修。**

---

## 本轮的 checked_but_clean（4 维共 40+ 条只读核查，摘要）

### parse_layers（12 条）

- 【核心问题·无解】找不到「具体 config 文本 + 非敌意坏解析器 ⇒ 静默绑父树」的组合。静默回退的充要条件是：两道探针都过 ∧ 读/解析无异常 ∧（原文无 `^harness_tree[ \t]*:` 顶格命中 ∨ 解析结果含该键）∧ 取到的值为 None/空。要走通第一个析取支，config 必须用非顶格的合法写法（带引号键 / flow mapping / 整体缩进 / BOM 开头），同时解析器必须「对探针诚实、只对这种写法说谎」。而键级探针要求 `a: 1→int 1`、`b: 2→int 2`、末行裸键→精确哨兵串——任何朴素 split/正则式解析器都死在 int 标量解析
- 【honest PyYAML 实测·7 形态】在 PyYAML 6.0.3 上逐条对照「人眼读到的」vs「生产会做的」：BOM 开头（`﻿harness_tree: /a/b`）PyYAML 会剥 BOM ⇒ 顶层有键 ⇒ 正常采用（不是漏洞）；整体缩进的顶层 mapping ⇒ 顶层有键 ⇒ 采用；CRLF ⇒ `open()` 通用换行已归一，`_raw` 与解析器看的是同一串 ⇒ 正常；`---` 文档头 ⇒ 正常；block literal `note: |` 内含该串 ⇒ 缩进故正则不命中、顶层无键 ⇒ 正确回退；anchor/merge 嵌套 ⇒ 顶层无键 ⇒ 正确回退；`harn
- 【tab 过匹配·无害】正则 `[ \t]*` 允许 `harness_tree\t:`，而真 PyYAML 对该文本抛 ScannerError（tab 不能起 token）⇒ 落进 `except Exception` ⇒ 可见 SystemExit。过匹配方向只会多发否决，不会漏发。
- 【`_raw` 与解析输入同一性】r10 H1 的修法（先 `_cf.read()` 再 `safe_load(_raw)`）确实消灭了「词法看的文本 ≠ 解析器看的文本」这条缝：两者是同一个 str 对象，编码/换行归一都发生在 read 一侧。没有第二条读取路径能让两者分叉。
- 【拒绝路径零写·函数内】`_harness_tree` 内唯一 IO 是 `open(_cfg_p, encoding='utf-8')`（只读模式），全部四条拒因（缺库 / 打开后读解析失败 / 词法否决 / 树不存在）之前没有任何 `open(...,'w')` / `makedirs` / `os.open(O_CREAT)` / subprocess。三条 fail-closed 出口都在导入任何 harness 树代码**之前**，所以 `_harness_tree` 自身的拒绝态对磁盘零副作用（`.locks` 是主块更早的既有写入，已登记为 v2 证伪项，不重报）。
- 【异常归类·两个 try 的分界】`import yaml` + 两道探针在一个 try（`except Exception → SystemExit 缺库`），`open()` 单独一个 try（`except OSError → _cf=None`），读/解析在第三个 try（`except Exception → SystemExit`）。逐个试了会打乱归类的路径：`yaml.safe_load` 不存在（AttributeError）、探针自身抛、config 非 UTF-8（UnicodeDecodeError 发生在 `read()` 而非 `open()`，故落在第三个 try）
- 【正则第四结构元素·未找到】除已闭合的三个 token（`^` / `[ \t]*` / 末尾 `:`）外，逐一检查了余下结构元素的门覆盖：键名字面量 `harness_tree` 由 `_LYING_CASES` 全体覆盖（改一字则否决不发、静默回退 ⇒ 那些格全红）；`re.M` 由 `honest_probes_*`（键写在第 2 行）覆盖；`re.search` 改成 `re.match` 同样被 `honest_probes_*` 打红（它们的键不在 pos 0）。没有第四个无门的结构元素。
- 【新增 3 格自身】`_NON_ANCHORED_FORMS` 三个形态的前提断言（真 PyYAML 顶层无该键 / 文本含该串 / 不顶格命中）都是行动前的裸 assert，不会被吞；`indented_nested` 在 PyYAML 6.0.3 实测确为 `{'nested': {...}, 'vault_id': 'v'}`，顶层无该键，断言成立。前提里的正则是**硬编码副本**而非引用生产对象，所以「删掉 `^`」这个目标变异不会连带把前提一起放过——变异仍由 `_got[0]=='ok'` 抓住。与 `_VALUE_NEST_FORMS`（那串字确以顶格出现、期望 exit）取值面
- 【veto 条件的两个析取支】`not isinstance(_doc, dict) or 'harness_tree' not in _doc` 当前写法行为正确：非 dict（list/str/None）一律否决，dict 缺键一律否决。注意 `honest_probes_list` 其实靠第二个析取支就红了（`'harness_tree' not in ['not','a','dict']` 为真），所以第一个析取支缺专门的门——但**代码本身没有做错事**（需要它的场景是「解析器返回含该串子串的字符串」，现写法此时正确否决），属门覆盖缺口而非缺陷，按本轮定级门槛不足以成 HIGH，如实
- 【预检与主块用同一份实现】Step 2.9 的 `_NS` 只 exec `_CUT` 之前的顶层 import，实测该范围含 `json/re/os/sys/…/math`，故 `_harness_tree` 拒因里用到的 `sys.executable` 与词法用到的 `re` 在预检命名空间里都在（不会把 SystemExit 降级成 NameError）。预检与主块是 AST 逐字同一份函数，不存在「预检按旧口径判绿」的漂移面。
- 【VAULT 推导】主块 `VAULT = dirname(dirname(abspath(NODE)))` 与预检的同式。节点多一层嵌套时 VAULT 指偏 ⇒ 找不到 config ⇒ 回退父目录 ⇒ 但随后 `_harness_contract` 导入必败 ⇒ 可见拒绝，不构成静默绑错树。
- 【重复键 / BaseLoader 型解析器】config 顶格写两遍 `harness_tree:` 时 PyYAML 静默取最后一个——绑到的仍是用户自己写过的路径，且下游 `_vault_id_of` 用同一语义读同一文件，不构成本卡意义上的「绑到用户没写过的树」；全标量返字符串型（BaseLoader 语义）的模块会死在 `_kprobe.get('a') == 1` 上 ⇒ 可见误拒，方向安全。两者均不足以成 finding。

### contract（15 条）

- 【终审绑定自证】`git --no-pager diff --stat --no-color 43bea775 HEAD -- . ':(exclude)_bmad-object'` 口径按协议写成 `':(exclude)_bmad-output'`，输出为空 ⇒ 本轮所读代码树即 43bea775。全程只读：未改本树任何文件、未跑变异、未 git 写；唯一执行的对照实验写在 scratchpad（/private/tmp/.../probe_contract.py），从 SKILL.md 逐字抽 `_harness_contract` 后在临时目录造假树调用，零写入本树。
- 【契约 11 格不是恒绿 —— 实测证明底本能过】scratchpad 里用与 `_VALIDATOR_STUB_OK` 逐字相同的占位 validator 造树后调 `_harness_contract`，实得 `OK len=7 types=['function','function','Pattern','function','function','function','Pattern']`。⇒ `_CONTRACT_CASES` 的 11 格每格确实是「只拆一项才红」，不存在「底本本来就被拒、11 格全为同一个无关理由绿」的假门。（这正面补上了 v2 已证伪那条「11 格不钉拒在哪一层
- 【返回元组的位置解包有门，且最危险的那一次交换被钉住】`_HARNESS_NAMES` 索引 6 = `_TS_RE`，`accepts_real_tree` 断言 `_names[6] is _vle._TS_RE`；把常量表里 `_WHOLE_SECOND_RE`(idx2) 与 `_TS_RE`(idx6) 对调会当场红。我另外追了「只改调用点解包顺序、不改常量表」这条常量表外的路径：它会让 `_WHOLE_SECOND_RE` 绑到宽松的 `_TS_RE` 上，`_durable_instant` 的整秒字面门失效 ⇒ 小数秒 durable 行被消费（R2 BLOCKER 复活）——
- 【契约四层每一条判据逐条找门，无裸奔项】① 影子门 `_from != abspath(_scripts)`：`refuses_shadowed_module`（拒）+ `accepts_real_tree`（symlink 真树必须过 = 同时守住「没写成 realpath」）两向都有格；去掉 `os.path.dirname` 会让 `_from` 恒为文件路径 ⇒ 控制组红。② 版本两条判据分别由 `event_version_2` / `version_bool` 钉。③ 形状三层：缺名字 `missing_name`、callable `vault_id_of_not_callabl
- 【`_HARNESS_NAMES` 与调用点解包的名字/顺序逐字比对】常量表 `(classify_card_state, _vault_id_of, _WHOLE_SECOND_RE, _looks_like_review_ext, validate_record_full, _golden_manifest, _TS_RE)` 与 SKILL.md:820 的 7 元解包逐词一致；`return tuple(getattr(_vle,_n) for _n in _HARNESS_NAMES)` 按同一表生成 ⇒ 无错位。
- 【影子门 abspath 而非 realpath：找过「symlink 不合法」的布局，没找到构成新缺陷的】能构造的最坏布局是「树 B 的 backend/scripts（或其中的 validator）是指向旧树 A 的 symlink，用户以为 B 是新 checkout」。abspath 放行、realpath 会拒。但这只覆盖到**已声明接受**的那一类（旧树 `b85a168a` 同名同形状、纯函数探针全对，realpath 对「A 物理上自带 validator」的同类完全无效）⇒ realpath 只多堵住该类的 symlink 子形态，不改变结论。且顺带确认了自洽性：valida
- 【「不探 `_vault_id_of` / `_golden_manifest`」的理由核过，站得住】我本来要报「读文件不违反纯读零写，所以这个理由是伪的」。实际核了两棵树的实现：新旧两版 `_vault_id_of` 对不存在的 `.canvas-config.yaml` **都**返回 None（旧版 b85a168a:412-414 与新版 1347+ 同形），⇒ 零 IO 的探针区分不了新旧；要区分必须现造一份 config 文件 = 真落盘，与预检块「不落任何文件」的自我承诺冲突。`_golden_manifest()` 同理（只读树内 manifest，异树给不出判别力）。⇒ 该处
- 【探针在异常输入上会抛而不是 fail-closed —— 定级 LOW，不入表】实测：`_TS_RE = re.compile(rb"...")`（bytes 模式）能过形状层的 `isinstance(..., re.Pattern)`，随后 `fullmatch("2026-...")` 抛未捕获的 `TypeError: cannot use a bytes pattern on a string-like object`（scratchpad 实测原文）。同族还有「`validate_record_full` 签名无默认值 ⇒ 探针 TypeError」。后果是 traceback 
- 【`EVENT_VERSION` 的等值判据边界】`isinstance(_ver, bool) or _ver != 1` 对 `1.0` / `Decimal(1)` 放行。属「配置注入」同族但比 `True` 远为牵强（没有现实分发会把它写成浮点），且真放行后写点仍按 v1 消费、与树侧一致 ⇒ 不构成做错事。LOW，不报。
- 【preflight 与 Step 4 的契约是否可能「预检过、主块拒」（半态）】逐条排过三条可能的分叉：① `sys.modules` 污染 —— 主块在 `_harness_contract` 之前只 import 了 `fsrs_bridge`，实测 `canvas-vault/.claude/scripts/fsrs_bridge.py` 的 import 清单里**没有** `validate_learning_events`（也没有 sys.path 操作），不会先占坑触发影子门；② `sys.path` 面 —— 主块比预检**多**一条 `<vault>/.claude/scr
- 【`_harness_contract` 之后主块不再二次 import validator】grep 全文 `validate_learning_events` 只在 :813/:815/:820 出现（两条注释 + 解包），主块后续无重复 import、无从该树导入第 8 个名字 ⇒ 契约覆盖面与实际消费面一致。
- 【`_golden_manifest()` / `_vault_id_of()` 的失败形态核过，不会把「契约过了」变成 Step 4 崩】真树里两者都是全捕获降级返 None（`_golden_manifest` 捕 OSError/ValueError/RecursionError + 非 dict/畸形值一律 None；`_vault_id_of` 捕 Exception）⇒ 契约不探它们不会让 Step 4 出现 traceback 型半态。
- 【本轮新增那 3 个形态（`_NON_ANCHORED_FORMS`）自身】三条前提断言都是真断言、不会被吞（`_outcome` 只接 `SystemExit`，别的异常照样冒泡）：真 PyYAML 顶层无该键 ✓、文本确含 `harness_tree:` ✓、`^harness_tree[ \t]*:` 与 `re.M` 下不命中 ✓（`indented_nested` 的键有两格缩进，实测不命中）。与「已接受误拒面」三格期望相反但前提互斥（那三格顶格命中），不冲突。三格都真正区分 `^`：去掉行首锚后三者都从 ok 变 exit。冗余但无害。
- 【整套 47 格实跑】`backend/.venv/bin/pytest tests/skills/test_harness_tree_parse_r2.py -q` ⇒ `47 passed`，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0)`，无偷连。
- 【lint 基线位移核过】`TMP_BLOCK_BASELINE["quiz-answer"]` 的 `B305` 与 SKILL.md 实际块首行 305 对上；`S281` / `98` 两条散文条目对应的 :281（`/tmp/quiz-answer-payload.json`）与 :98（`/tmp/quiz-answer-incr.json`）实见。唯一不一致是 `OPAQUE_TMP_BASELINE` 上方注释写「`:205` → `:267`（+62 行）」而实际值是 281（+76，round-2/3 又 +8/+6 后的终值）—— 注释是上一轮的中途数、值本身正确，纯 LO

### preflight（14 条）

- 先拒后写的顺序：Step 1（定位+提取答案）与 Step 2（Read 节点正文评分）在 2.9 之前是纯读，SKILL.md 里这两步没有任何写侧动作 ⇒ 预检之前零落盘；顺序本身由 test_g33r2_step29_precedes_step3（标题）+ test_g33r2_preflight_block_precedes_step3（fence 自身位置）+ ..._is_the_second_pyeof_block_and_main_stays_single（块序）三面钉住，实测 8 格 pass（PYTHONDONTWRITEBYTECODE=1 -p no:cacheprov
- 「拒绝了却已落盘」：在 /tmp 沙箱按真实用户环境（显式不设 PYTHONDONTWRITEBYTECODE）逐字真跑预检块，控制组一路走到 import validate_learning_events，全树 __pycache__ = 0、rc=0。sys.dont_write_bytecode = True 排在 import ast, os, re 之前，之前只有 import sys（解释器启动时已载入，不新增落盘面）。
- 预检 import 的目标模块零 import-期副作用：对 backend/scripts/validate_learning_events.py 做 AST 顶层普查，body 只有 Import/ImportFrom/Assign/AnnAssign/FunctionDef/ClassDef/docstring 与一个 if __name__ == '__main__'，没有顶层调用、没有文件/目录创建 ⇒ 预检导它既不落盘也不改状态。
- 「抽取失败 ⇒ 恒绿」不成立（沙箱实测两种坏法）：① 把 def _harness_contract( 改名 ⇒ rc=1 + 一句话拒因『应各恰 1 处, 实见 [_harness_tree]』；② 构造两个 def _harness_tree( 且零 _harness_contract（刻意绕过 len(_FNS) != len(_WANT) 这条只数总数、不查身份的判据）⇒ 仍 rc=1（_NS['_harness_contract'] KeyError traceback）。名实不符（错误文案说「各恰 1」而判据是总数）确实存在，但两条路都 fail-closed，够不上 HIGH。
- 自指风险已闭合：预检自己的 fence 行 QUIZ_ANSWER_NODE='节点/<concept>.md' python3 - <<'PYEOF' 含 _FENCE 子串、会被 re.findall 命中，但 _ANCHOR（'def ' + '_harness_tree' + '('，预检块内无该字面量）把它滤掉；_FENCE 串内无正则元字符（p y t h o n 3 空格 - 空格 < < ' P Y E O F '），不需要 re.escape。
- 「顶层 import 取漏 ⇒ 恒绿」不成立：漏了名字只会在函数调用时 NameError（rc≠0）。逐条核过 _CUT 之前的顶层 import（json/re/os/sys/subprocess/unicodedata/decimal/hashlib/fcntl/time + datetime 三名 + Path + math）覆盖了两个被抽函数实际用到的全部自由名（os/re/sys；yaml 与 shlex 是函数体内 import）；from decay_beta import …（:1723）在 _CUT 之后被正确跳过，这正是 docstring 声称的那条口径。
- 「抽到旧定义」的可达性：NODE 在 prose 里是相对路径 节点/<concept>.md，abspath 按 cwd 解析 ⇒ VAULT 恒 = cwd ⇒ 预检读的 <VAULT>/.claude/skills/quiz-answer/SKILL.md 与 Claude 加载的那一份是同一文件。cwd 不在 vault 时（例如在 repo 根跑），_SK 打不开 ⇒ 预检先红（『vault 不是标准布局』），Step 4 随后也会在 fsrs_bridge 上红 —— 方向安全，不是绿。
- 预检与主写点是同一份实现、同一条 VAULT 公式：两处都是 os.path.dirname(os.path.dirname(os.path.abspath(NODE)))，唯一差别是 NODE 来源（env QUIZ_ANSWER_NODE vs payload['node']），同 cwd 下同值；函数体由 AST 逐字抽取，不存在第二份手抄。
- sys.path 形态等价：Step 4 是先插 <VAULT>/.claude/scripts 再由 _harness_contract 插 <REPO>/backend/scripts（后者落 index 0），预检只有后者；影子门比的是 abspath(_scripts)，两边同结论。实查 canvas-vault/.claude/scripts/fsrs_bridge.py 与 decay_beta.py 顶层 import 里没有 validate_learning_events ⇒ 「Step 4 先 import fsrs_bridge 把 sys.modules 污染、影子门在
- REPO 遮蔽 vault 脚本的风险不成立：_harness_contract 把 <REPO>/backend/scripts 顶到 index 0 之后，主块在 :1723 紧邻 from decay_beta import 之前又插了一次 <VAULT>/.claude/scripts（本卡之前就有），且实查 backend/scripts/ 下无 decay_beta.py / fsrs_bridge.py。
- 续跑路径不构成「预检被绕过」：Step 0 的 scored_pending_node_update / in_progress+score≠null 两支跳过 Step 1-3（含 2.9），但此时白板**已在**半态，Step 4 再失败不新增半态，且主块每条拒因都自带 _HALFSTATE 文案（分数保留、不回滚、可续写）。
- _harness_tree 的三层 except 逐条读过、无吞异常：except Exception 不接 SystemExit（BaseException）；_cf is None 只在 open() 自己失败时成立，打开后的读/解析失败一律 fail-closed；值为 False/0/非 str 时 str() 后交给路径存在性判据 ⇒ 拒；''/null/无键 ⇒ 回退，与 docstring 三条分界逐字一致。.canvas-config.yaml 是目录时走 IsADirectoryError ⊂ OSError ⇒ 回退，与 v2 已证伪的 EACCES 同族（下游 _vaul
- rc 语义三路一致（沙箱实测）：SystemExit 拒因 / 契约 _refuse / 未捕获异常都给 rc=1；控制组 rc=0 且 stdout 打印出选中的那棵树的 realpath。
- 【登记不报，供台账参考】skill_portability_lint.py 新增的两段基线注释里位移算术是陈旧的：OPAQUE_TMP_BASELINE 处写『:205 → :267 纯行号位移（+62 行）』、TMP_BLOCK_BASELINE 处写『共 +70 行 … 又 +8 … 又 +6』，而实际位移是 +76（old:205 = new:281，B229 → B305 同为 +76）。**登记的值本身是对的**（我逐行核过 new:281 = 老的 4b 那行 payload 散文、new:267 是 Step 3 的 Edit 行；lint 门绿也佐证），错的只是注释里的加减法。

### tests（13 条）

- `_WHOLE_DOCS` 13 条「真值」逐条实测对得上：用 AST `literal_eval` 从测试文件里把表原样取出来（不手抄），在本车道共享 venv（Python 3.14.4 / PyYAML 6.0.3）上逐条重跑 `yaml.safe_load` 并用门里那套 `dict_with_key` / `dict_no_key` / `not_a_dict` / `raises:<Name>` 归类，13/13 与表一致，0 mismatch。
- v4 新加的 3 个形态前提断言确实成立：`commented_out` / `inline_comment` / `indented_nested` 在真 PyYAML 下顶层都没有 `harness_tree`；特别核了任务点名的 `indented_nested`——真 PyYAML 给的是 `{'nested': {'harness_tree': '/a/b'}, 'vault_id': 'v'}`，顶层确实无该键，断言没说错。三格的 `harness_tree:` 都不在任何行首，`re.search(r"^harness_tree[ \t]*:", raw, re.M)` 恒 No
- 两个文件零 skip / 零 xfail：`tests/skills/test_harness_tree_parse_r2.py` 47 passed；`tests/regression/test_g3_2_review_ledger.py -k g33r2` 183 passed；目录级 `tests/skills` 607 passed（协议 §3 要求的那一面）。没有任何格靠 skip 把「前提不成立」吞成绿色。
- 顺序无关：`pytest-randomly` 打开跑 3 遍，47 passed ×3。autouse 夹具 `_no_validator_leak` 确实把 `sys.modules['validate_learning_events']` 与整份 `sys.path` 前后各还原一次（生产 `_harness_contract` 的 `sys.path.insert` 与 import 都不回滚，靠这个夹具兜）。
- 缺陷态复活会响亮地红：在 /tmp 的副本里把两层判据同时换成 `if False:`（键级探针的 `if not (isinstance(_kprobe, dict) and …)` + 词法否决的 `if _lex and (…)`），47 格里 13 格红（constant_bare / constant_quoted_key / honest_probes_list / truncating ×3 / tail_only 等）。主干树一个字节未动。
- 对「不是 if 语句、也不是那条正则的三个 token」的判据做了 14 组独立变异（全部在 /tmp 副本上）。已被门覆盖的：去掉 `re.M` → 6 红（与卡文声称一致）；影子门 `abspath`→`realpath` → 2 红；`realpath(strict=True)`→`normpath` → 1 红（`truthful_parser_still_binds_alt_tree`，靠 macOS `/var`→`/private/var` 分叉抓到）；第一道探针字面量 `"a: 1"`→`"a: 1\n"` → 4 红；`isinstance(_ver, bool)` 排除去掉
- 专门核了「有没有第四个承重结构元素」这个方向：`[ \t]*` 字符类里的 `\t` 成员确实没有任何一格覆盖（现有 `spaced_before_colon` 用的是空格），把它删成 `[ ]*` 后 47 格全绿。但它**不承重**——PyYAML 6.0.3 对 `harness_tree\t: v` 抛 ScannerError（`found character '\t' that cannot start any token`），这类文本根本不是合法 config，生产会在 `except Exception as _ye` 那条「打开后读取/解析失败」里先拒，`_lex` 永远不会
- 变异后仍全绿、但判据在本卡 diff 之外（`git diff a05732c9 HEAD -- SKILL.md` 里那几行是上下文行、未改）且终局 fail-closed 的四项，按 v3 对 `_vid` 那条的同一口径不计为本卡发现：`os.path.expanduser`（ledger 侧 `broken_is_fail_closed[~/definitely-missing…]` 有专门一格钉「拒因里不得还带未展开的 ~」）；`sys.path.insert(0,…)`→`append`（影子门照样拒，可见）；`isdir(<tree>/backend/scripts)` 去掉（`
- 契约表 13 格逐格追到它真正触发的那条生产判据：5 条 v2 新增格（`ts_re_accepts_bare_date` / `whole_second_re_*` 两向 / `classify_says_review_…` / `looks_like_returns_zero_not_false`）各落在自己声称的那一层，`_WHOLE_SECOND_RE` 两向都有格。`_VALIDATOR_STUB_WRAPPED_RE` 的三次链式 `.replace()` 若有任一锚漂了会产生语法错 ⇒ import 失败 ⇒ 拒因变成「G3-2 依赖不可达」（不含「不是编译正则」）⇒ 最后一条断
- 前提断言的求值顺序全部正确、没有被更早的断言吞掉：`_LYING_CASES` / `_TRUNCATING_FORMS` / `_NON_ANCHORED_FORMS` / `_VALUE_NEST_FORMS` 每一格都在 `monkeypatch.setitem(sys.modules, "yaml", …)` **之前**用真 PyYAML 算前提；ledger 的 whole-mode 控制组同样排在 `sys.modules['yaml']=None` 之前，并且用 `assert` 而不是 `pytest.skip`（注释里明写为什么不许 skip）。
- 测试侧手抄的那份正则 `r"^harness_tree[ \t]*:"` 在 4 处前提里出现，没有像 `_KPROBE_DOC` 那样做 AST 反向抽取防漂移。核过后认为不构成假门：生产正则一改，行为断言会先红，手抄副本只会让「红在哪一行」的说法不准，不会让格变绿。
- lint 基线三项实数核对：`MANAGED_FILE_DIGESTS['skills/quiz-answer/SKILL.md']` = `d64d3b8c…` 与 `shasum -a 256` 当前文件逐字节相同；`B305` 对应 SKILL.md:305 的 ```python3 - <<'PYEOF'``` fence；`98` / `281` 对应两条裸 `/tmp/` 散文行。
- `never_returns_a_tree` 的拒绝半边其实与 config 内容无关（生产在 `import yaml` 就拒，根本没走到 `open(_cfg_p)`），73 个参数跑的是同一条路径 —— 这是门 docstring 自己声明过的设计（表的职责已从「两侧比值」改成「给重新加回降级解析制造阻力」），whole-mode 控制组的价值是把 PyYAML 的实际结局钉死给那个未来用。不按假门计。

