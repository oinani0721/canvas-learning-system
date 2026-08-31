# 多智能体对抗审查存档 — CARD-维护B（数字治理域）

> **形态**: ultracode workflow · 5 路探针（结构 / 数字形态 / 误伤 / 门覆盖 / 名实一致）
> × 三视角独立证伪 · 2026-08-31
> **被审对象**: Codex round-1 整改**之后**的实现（即"整改的整改"）
> **run**: `wf_8cef6e1c-dfa`
>
> ## 为什么在 Codex 之后还要跑这一轮
>
> Codex round-1 判 FAIL（3 BLOCKER / 5 HIGH），我逐条整改并把域从「点名两段」
> 倒转成 default-deny。**域的结构一改，攻击面就换了一批**——单靠"修完自测"
> 无法确认新结构没开新口子。这一轮就是冲着新结构去的。
>
> ## 结果
>
> 第一路（结构面）即交出 **8 条发现 / 4 条 BLOCKER**，全部带四份 live 真报告实测。
> ⛔ 我对每一条都**独立复现**后才动手（下方"我的复现"列），整改后又做了
> 两份真报告 × 17 条构造的双向验证，全部符合期望。
>
> **最该记住的一条**（B-3）：数值池混进了 `scale_gate` 的**源码常量** 30/100/10，
> 于是 100−1=99 恒「有出处」——**卡文与 goal 的旗舰反例「99 个子节点」
> 在四份真报告上全部放行，而我的验收单还写着"拦下"**。
> 池的"出处"语义一旦掺进与板内容无关的常量，整个 D2 就被稀释。
>
> **另一条同样值钱**（B-2）：我为 default-deny 写的那道守卫测试只锁了例外表的
> **字面量**（`entries == ['"数据来源与新鲜度",']`），没锁**匹配语义**——
> 于是子串匹配 + `###` 当段首的组合让「加个标题就逃出治理」原样复活。
> **守卫守错了东西**，比没有守卫更危险。
>
> ## 逐条处置
>
> 见验收单 `UAT-CARD-维护B-数字治理域-2026-08-31.md` §五之三 的对照表。
> 8 条中 7 条已修并固化成门（`test_audit_*`），1 条（H-2 数字/量词仍是字符表）
> **不修、改为如实登记边界**，并把卡文与验收单里那句过度声称一并更正。
>
> ## ⚠️ 本存档的限制（如实）
>
> - 另外 4 路探针在我整改时**尚未返回**，其发现未纳入本次处置；
> - 整改本身**未再过独立复核**；
> - 因此本卡**不宣称「已清零」**。
>
> ---
>
> 以下为探针原始产出（JSON，逐字未删改）。
>
```json
{
 "findings": [
  {
   "title": "HTML 注释剥除不认代码跨度 —— `` `<!--` `` … `` `-->` `` 可让任意**可见**正文对全部 verifier 检查隐身（不止 D2）",
   "kind": "bypass",
   "severity": "BLOCKER",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1522",
   "evidence": "`text = re.sub(r\"<!--.*?-->\", \"\", text_raw, flags=re.S)` 在**原始文本**上无条件剥除，不判断标记是否落在行内代码/围栏跨度内。CommonMark 里 `` `<!--` `` 是 code span（渲染成字面 `<!--`），中间的正文正常渲染给读者，但 verifier 先把它整段删掉；随后 `if \"<!--\" in text` 也因两个标记都被吃掉而不触发。\n实测（`/tmp/recaphunt/`，四份 live fixture + 各自 scan JSON）：\n① 藏无据计数：在 `### ③ 方向` 后插入 `- 注释语法 `<!--` 起，本板共有 987654 个子节点，`-->` 止。【实测】` → cs61b=0 rec=0 eig=0 cs188=0（**四份全 exit 0**）；同一句去掉两个 code span 后为 exit 1（`✗ 数字终核: 『③ 方向』段的计数 987654 …找不到同值来源`）。\n② 不止 D2 —— 藏 HARD-R4 禁词：`- 你的理解偏离了材料主线，其实你当时选择跳过了分治部分。` 裸写 exit 1（`✗ HARD-R4 禁词命中: 偏离`）；包成 `- 语法 `<!--` 起，你的理解偏离了…，`-->` 止。` → **exit 0 VERIFY PASS**。\n即：③段用户主语 / 占位符 / 甩锅词 / fallback「派生」整行白名单 / 动作段白名单 / D2 计数——凡是对 `text` 做字符串或正则判定的检查，全部可被这一个构造整段绕开，而读者在 Obsidian 里看得见那段字。卡文 §0.1 把 E8 登记为「豁免跨度」，但实现是**先于一切检查的删除**且无跨度感知，两者不是一回事。",
   "short_summary": "code-span 包裹的 <!-- --> 删掉可见正文，绕过全部检查"
  },
  {
   "title": "D2 出域表用**子串**匹配任意 `##` 开头行 —— 加一个含「数据来源与新鲜度」的三级标题（甚至围栏里的假标题）即可整段出域",
   "kind": "bypass",
   "severity": "BLOCKER",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1306",
   "evidence": "切段用 `heads = re.finditer(r\"^##[^\\n]*$\", text, re.M)`（`###`/`####` 同样命中），出域判定用 `if any(ex in sec for ex in _D2_EXEMPT_SECTIONS)` —— **子串**包含即出域。而 `_VERIFY_SECTIONS` 的重复段检查用 `_SECTION_RE`（`^## 数据来源与新鲜度(?:[^\\S\\n]*$|（…)`）**前缀锚定**，所以只要把豁免段名放在标题的非开头位置，既不算重复段、又能整段出域。\n实测（四份 live fixture 全部）：\n① 文末追加 `### 数据来源与新鲜度（补充）` + `- 本板共有 987654 个子节点、987654 条批注。【实测】` → cs61b=0 rec=0 eig=0 cs188=0。\n② 文末追加 `## 附录（数据来源与新鲜度）` + 同一行 → cs61b exit 0。\n③ **连可见标题都不需要**：文末放一个围栏\n```\n## 板级数据来源与新鲜度\n```\n再跟 `- 本板共有 987654 个子节点。【实测】` → exit 0。因为 `_verify_prose_counts` 不剥围栏（见另一条 E1 发现），围栏里那行被当成真标题；在 Obsidian 里它渲染成灰底代码，读者根本看不出这是「段落分界」。\n对照：`## 附录`（不含豁免子串）→ exit 1，说明 default-deny 本身是通的，漏的是出域匹配语义。\n这正是 UAT §二 自述被 Codex 推翻过的同一类缺陷（「加一个标题就能逃出治理，那不是域」）换条路复活。测试 `test_recap_scan_signals.py:1913-1925` 只锁了 `_D2_EXEMPT_SECTIONS` 的**条目字面量**（断言 `entries == ['\"数据来源与新鲜度\",']`），没锁**匹配语义**，所以这条守卫守的是错的东西。",
   "short_summary": "出域表子串匹配任意 ## 行，加个三级标题即出域"
  },
  {
   "title": "数值池混入 `scale_gate` 常量 10/30/100 —— 卡文旗舰反例「99 个子节点」在四份真报告上全部 exit 0，UAT §一/§三 仍宣称「拦下」",
   "kind": "claim_mismatch",
   "severity": "BLOCKER",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1291",
   "evidence": "池 = scan 的数值型整数 ∪ 两两和差。实测四份 live scan JSON 的 base 集合分别是 `[0,1,2,3,10,30,100]`(cs61b) / `[0,1,10,30,100]`(rec) / `[0,1,2,3,6,10,30,100]`(eig) / `[0,1,2,3,4,7,8,10,30,100]`(cs188)。其中 10/30/100 与板内容**无关**，来自恒定字段：`.scale_gate.member_threshold=30` / `.scale_gate.annotation_threshold=100` / `.scale_gate.detail_k=10`（即 `MEMBER_THRESHOLD` / `ANNOTATION_THRESHOLD` / `DETAIL_K` 三个源码常量），任何板的 scan JSON 都有。\n⇒ 100−1=99 恒在池内。实测：在 `### ③ 方向` 后插入 `- 本板共有 99 个子节点。` → cs61b=0 rec=0 eig=0 cs188=0（**四份全 VERIFY PASS**）。\n池覆盖度实测：cs188 的池覆盖 1..20 中的 **19 个**、1..200 中的 52 个；cs61b 覆盖 1..20 中的 14 个。即报告里最可能被编造的小整数几乎全部「有出处」。\n口径矛盾（同一份交付物内自相矛盾）：`_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md` §一 表格第 5 行仍写「正文里凭空写『这块板有 **99 个子节点**』… 现在：拦下（并告诉你它在 scan 里找不到同值）」，§三「先红后绿」表仍写「域内裸数字「99 个子节点」｜exit 0（未拦）｜exit 1 ✅」；而同文件 §五之二 第 177 行与 `test_recap_scan_signals.py:1650` 的 docstring 都明说 99 拦不住、门里改用了 987654。用户读的是 §一 那张表。",
   "short_summary": "池含 10/30/100 常量，旗舰反例 99 在四份真报告全放行"
  },
  {
   "title": "E2/E3 豁免跨度挖空的是**渲染可见**内容 —— 数字包进反引号、或写进 wikilink 别名，即可写任意无据计数",
   "kind": "bypass",
   "severity": "BLOCKER",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1309",
   "evidence": "`for rx in (_D2_INLINE_CODE_RE, _D2_WIKILINK_RE, _D2_TIME_RE): body = rx.sub(等长空格)` —— 行内代码的**内容**和 wikilink 的**别名显示文本**都会被整段挖空，但这两者在 Obsidian 里都是读者看得见的正文。\n实测（四份 live fixture 全部 exit 0）：\n① 行内代码：`- 本板共有 `987654` 个子节点。【实测】` → cs61b=0 rec=0 eig=0 cs188=0；去掉反引号同句 exit 1。\n② wikilink 别名：`- 详见 [[节点/x|本板共有 987654 个子节点]]。【实测】` → cs61b=0 rec=0 eig=0 cs188=0。\n③ 数字与量词之间夹一个行内代码跨度也一样：`本板共有 `987654` 个子节点` 挖空后剩 `本板共有         个子节点`。\n这不是「代码示例里的数字不算陈述」——`` `987654` 个子节点 `` 的渲染结果与裸写完全等价地在向读者断言一个计数。live 报告本身大量使用行内代码（`` `1-4 (1=最低)` ``、`` `节点/cs-61b-csm` ``），所以这是 LLM 写报告时**自然会落进去**的形态，不需要刻意攻击。",
   "short_summary": "反引号/wikilink 别名里的数字被挖空但照常渲染"
  },
  {
   "title": "计数识别要求数字与量词**紧邻**（只容 `\\s`）—— 加粗、`<span>`、`&nbsp;`、软换行任一插入即漏检",
   "kind": "bypass",
   "severity": "HIGH",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1219",
   "evidence": "`_D2_COUNT_RE = re.compile(r\"(?<![0-9.])([0-9]+)\\s*(?=[个条块次份处板项篇道张])\")` —— 前瞻只容许空白。任何 Markdown 行内构造插进去就断开；且检查是 `for line in body.splitlines()` 逐行做的，跨软换行也断开。\n实测（每条均在四份 live fixture 上 exit 0，裸写对照 exit 1）：\n① 加粗：`- 本板共有 **987654** 个子节点。【实测】` → cs61b=0 rec=0 eig=0 cs188=0（渲染为「本板共有 **987654** 个子节点」）。\n② HTML：`- 本板共有 <span>987654</span> 个子节点。【实测】` → exit 0。\n③ 实体空格：`- 本板共有 987654&nbsp;个子节点。【实测】` → exit 0。\n④ 软换行（CommonMark 渲染成一个空格，读者看到的是同一句）：`- 本板共有 987654\\n  个子节点。【实测】` → exit 0。\n加粗数字是 LLM 写报告的常见排版，这条同时是绕过面和**静默漏检面**。",
   "short_summary": "加粗/span/nbsp/软换行隔断数字与量词即漏检"
  },
  {
   "title": "「按位置不按字符」只兑现了一半：数字仍是 ASCII 白名单、量词仍是封闭字符表 —— 中文数字/全角/实体/表外量词全部放行",
   "kind": "claim_mismatch",
   "severity": "HIGH",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1219",
   "evidence": "卡文 §0.3 写：「中文数值的拦截改由**位置**承担：D1/D2 域内出现的**任何**未绑定数量表述都 FAIL，而域外不追究——于是「仨/皕/零」这类生僻写法不需要被逐个枚举。」UAT §二 复述为「改由位置承担后，生僻写法不需要被逐个枚举」。\n实现里 D2 的数字仍是 `[0-9]+`、量词仍是 11 字封闭表 `[个条块次份处板项篇道张]`，两头都是字符表。实测（四份 live fixture 全部 exit 0）：\n① 中文数字：`- 本板共有九十八万七千六百五十四个子节点、仨条批注。【实测】` → cs61b=0 rec=0 eig=0 cs188=0。\n② 全角数字：`- 本板共有 ９８７６５４ 个子节点。【实测】` → exit 0。\n③ HTML 实体：`- 本板共有 &#57;&#56;&#55;&#54;&#53;&#52; 个子节点。【实测】` → exit 0（渲染为 987654）。\n④ 表外量词：`- 本板共有 987654 名成员、987654 组关系、987654 段材料。【实测】` → exit 0。\n注意方向：被删掉的 `_has_numeric`（`_EXTRA_QUANTITY_CHARS` 含「一二三…仨俩」+ Nd/Nl/No 全覆盖）本来**认得**①②；新设计对这类写法的覆盖不是「不必枚举」，而是**降为零**。卡文/验收单据此宣称的「生僻写法进不来」与实测相反。",
   "short_summary": "D2 仍是 ASCII 数字表+11 字量词表，中文数字全放行"
  },
  {
   "title": "E1 围栏豁免在 D2 里根本没实现 —— 既造成围栏内合法语料误伤，又是「围栏假标题」出域绕过的成因",
   "kind": "gate_gap",
   "severity": "MEDIUM",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1309",
   "evidence": "卡文 §0.1 与 UAT §二 都把判定顺序画成「先剥豁免跨度（E1 围栏代码块 …）→ 再按段落判域」，E1 排在第一位。但 `_verify_prose_counts` 的挖空只有 `(_D2_INLINE_CODE_RE, _D2_WIKILINK_RE, _D2_TIME_RE)` + 有序列表 + E6b + E7，**从不调用 `_strip_code_blocks`**（该函数只在 `_verify_signal_lines:1048` 被用）。\n双向实测：\n① 误伤方向：`### ③ 方向` 后插入围栏\\n```\\n本板共有 987654 个子节点\\n```\\n→ **exit 1**，`✗ 数字终核: 『③ 方向』段的计数 987654 …找不到同值来源: 本板共有 987654 个子节点`。引用内围栏同样 exit 1。即代码块里的字面文本被当成「报告的陈述」，与 §0.1「代码是字面文本，不是报告的陈述」的写死判据相反。\n② 绕过方向：正因为不剥围栏，围栏里的 `## 板级数据来源与新鲜度` 被 `heads` 正则当成真标题，从而开出一个「出域段」（见出域表那条发现的 ③）。\n同一处缺失同时制造误伤面和绕过面。",
   "short_summary": "D2 从不调用 _strip_code_blocks，E1 只写在文档里"
  },
  {
   "title": "小数形态被 lookbehind 整体跳过 —— `0.987654 个子节点` 可写任意无据计数",
   "kind": "bypass",
   "severity": "MEDIUM",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1219",
   "evidence": "`(?<![0-9.])` 的本意是不切开小数，实际效果是小数点后的整串永不参与匹配。实测：`- 本板共有 0.987654 个子节点。【实测】` → cs61b exit 0 VERIFY PASS（裸写 `987654 个子节点` 为 exit 1）。\nUAT §五之二 裁决点 2 把「mastery 0.3 / 量表 1-4 / 分位值 / 百分比不在内」登记为**已知边界**，方向上诚实；但登记的措辞是「这类带自身形态的量不在内」，读起来像「少校验了一些本来就该放行的值」，实际后果是**任何数字只要前面补一个 `0.` 就退出治理**——这是可写入面，不只是覆盖面。另一并发现：千分位 `987,654 个` 只会被拦到 `654`（exit 1 但点名的数字是错的），错误信息与实际断言不对应。",
   "short_summary": "0.<任意数字> 个 永不参与匹配，可写任意计数"
  }
 ]
}
```

```json
{
 "findings": [
  {
   "title": "同一句合法叙述在 4 块板上判定不一致：2 板 exit 0 / 2 板 exit 1（brief 明列的「明确缺陷」本体仍在）",
   "kind": "false_positive",
   "severity": "BLOCKER",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1322",
   "evidence": "逐字相同的句子 `- 本轮方向叙述只覆盖了材料面，考察侧证据缺口仍有 5 处未被本报告覆盖【推定】。` 插到 4 份 live 真报告的 `### ③ 方向` 段：CS 61B exit=0 / CS188 exit=0 / 特征值 exit=0 / 递归与分治 **exit=1**（`✗ 数字终核: 『三维审查』段的计数 5 在 scan JSON 里找不到同值来源`）。第二组用 CS188 真报告里**原文照抄**的分析句 `- 7 个派生点中仅 2 个带 derived_at，其余 5 个派生时间无据【实测】。`：CS188 exit=0 / 特征值 exit=0 / CS 61B **exit=1** / 递归与分治 **exit=1**（一句报两条）。根因：池 = 本板 scan 数值 ∪ 两两和差，四板的 base 分别是 {0,1,2,3,10}(rec) / {0,1,2,3}(61b) / {0,1,2,3,6}(eig) / {0,1,2,3,4,7,8}(188)，富板 0–18 几乎全覆盖、稀疏板 3–8 大面积缺失。代码注释与 test_domain_allow_range_expression 的 docstring 已把这个现象写成「那是明确误伤」，但只对 `N~M 个` 区间形态做了结构豁免（E7），通用形态未处理。"
  },
  {
   "title": "节点名含「数字+中文量词」→ 整份报告被拒（一处改名触发 5 条 ✗），而节点名是用户自造的自由中文",
   "kind": "false_positive",
   "severity": "BLOCKER",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1233",
   "evidence": "把 递归与分治 板的种子节点 `my-recursion-notes` 在 scan JSON 与报告里同步改名为 `分治法的 6 个步骤`（合法板态，counts 一字未动）→ **exit=1**，5 条 ✗：『你现在可以做的』×2、『台账（种子/派生）』×1、『三维审查』×2，全是 `计数 6 找不到同值来源`。第二块板独立复现：CS188 真报告把派生节点 `规划的分类-1549()` 改名为 `规划的 19 个分类维度` → **exit=1**（`『台账（种子/派生）』段的计数 19 …`）。live 板上现存节点名形如 `反射代理的局限性引出了规划代理-(Planning-Agents)-的需求`、`代理决策分析-0303()`，证明 node_id 就是自由中文长句。卡文 §0.1 的 E3 明写豁免理由是「板名/节点名自带数字（CS 61B、Lecture 14）是原文不是断言」，但 _D2_WIKILINK_RE(:1251) 只在 `[[…]]` 内生效，而 SKILL Step 5 模板的台账行 / 动作句 / 三维审查全部**裸写** node_id。"
  },
  {
   "title": "用户原话被判进域：SKILL 明文允许的「引用行」载体与「」内引语中的数字一律 FAIL，与卡文 D3「引用原文不追究」相反",
   "kind": "false_positive",
   "severity": "HIGH",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1352",
   "evidence": "(a) blockquote 载体（SKILL.md §结构注入防御：『tips/批注原话只能整段放在引用行或行内代码里』）：`> 我只想明白了 5 个步骤里的头两步，后面就断了。` 插入 递归与分治 报告 ①段 → **exit=1**（`『三维审查』段的计数 5 …`）。(b)「」内引语：`- 唯一历史题面的作答里你写的是「我只想明白了 5 个步骤里的头两步」【文件】…` → **exit=1**。(c) 四空格缩进代码块抄录题面 `（数据里共列了 6 个采分点）` → **exit=1**。_verify_prose_counts 的挖空集合只有 _D2_INLINE_CODE_RE / _D2_WIKILINK_RE / _D2_TIME_RE / 有序列表 / E6b / E7，没有任何 blockquote 或引号跨度豁免；卡文 §0.2 D3 写的是「E1-E8 挖空后剩下的**引用原文** → 不追究」。"
  },
  {
   "title": "台账种子行绑值门在 live 4 份里的 2 份形态上静默跳过：谎报「批注 6 条」仍 exit 0",
   "kind": "gate_gap",
   "severity": "HIGH",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1195",
   "evidence": "单变量对照：① 特征值真报告把 `- Fundamentals — 批注 3 条（理解度未闭环 3 条）；已派生 2 点…` 改成 `批注 6 条（理解度未闭环 3 条）；…`（scan 里 tips_count=3）→ **exit=0 VERIFY PASS**。② CS188 真报告 `- lecture 2 — 批注 4 条（未闭环 4 条）；已派生 7 点…` 改成 `批注 3 条（未闭环 4 条）；…`（真值 4）→ **exit=0**。③ 对照组 CS 61B（无全角括号形态）`- cs-61b-csm — 批注 2 条；未派生…` 改成 `批注 3 条；…` → **exit=1**（`台账『种子』行 cs-61b-csm 报批注 3 条, scan JSON 的 tips_count 是 2`）。根因：_SEED_LEDGER_LINE_RE 的 rest 组只接受 `\\s*[；;·]`，数字后紧跟全角 `（` 时整行不匹配 → `continue` 跳过绑定。Codex round-1 BLOCKER-3 的整改只补了 `；`/`·` 两种分隔符，漏了 live 里另一半形态；测试 test_domain_block_seed_count_tamper_on_real_manifest_line 只覆盖了 CS 61B 那份，所以全绿。"
  },
  {
   "title": "SKILL Step 4 强制要求的「闭环 diff / 本段新增」段在结构上不可能通过：previous_recap 在 scan JSON 里没有任何数值字段",
   "kind": "false_positive",
   "severity": "HIGH",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:818",
   "evidence": "给 递归与分治 的 scan JSON 补一个真实形态的 previous_recap（path/date/same_day/actions_section 四个字符串字段，与 _previous_recap() 的实际返回逐字段一致），报告 `## 本段新增（上次回顾 → 现在）` 段写 `上次回顾（2026-08-20）列出的 4 条动作建议，本轮逐条比对后仍有 3 条未见任何变化【文件】。` → **exit=1**，两条 ✗（计数 4、计数 3 均『找不到同值来源』）。根因：_previous_recap 只返回 path/date/same_day/actions_section(str)/selfevals(list[str])，而 _scan_number_pool(:1264) 只收 JSON 的**数值型** → 上一轮的任何计数、以及本轮与上轮的差值，永远不在池里。SKILL.md:205 的「闭环 diff：previous_recap.actions_section 非空 → 本次逐条与上次比对」与 Step 5 模板的 `## 本段新增` 段因此与 verifier 直接冲突。"
  },
  {
   "title": "frontmatter 被算进 D2 preamble 段：board_name 含「数字+量词」→ FAIL，与卡文 D3「frontmatter 非绑定键 = 域外」相反",
   "kind": "claim_mismatch",
   "severity": "HIGH",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1336",
   "evidence": "只改 递归与分治 报告 frontmatter 的 `board_name: \"递归与分治：7 个套路\"`（board_name 不参与任何绑定校验）→ **exit=1**：`✗ 数字终核: 『（规模自陈等前置段）』段的计数 7 …: board_name: \"递归与分治：7 个套路\"`。根因：切段时 parts[0] = text[:heads[0].start()]，而 text 是含 frontmatter 的全文，于是整个 YAML 块进了 D2。卡文 §0.2 D3 行明写域外包含「frontmatter 非绑定键」。"
  },
  {
   "title": "空板（0 成员）的合规报告必被拒两次，其中一条打的是 SKILL 模板逐字常量「manifest（1 次调用）」",
   "kind": "false_positive",
   "severity": "MEDIUM",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1403",
   "evidence": "构造 counts 全 0 / ledger 三组皆空的 manifest 模式 scan JSON + 按 SKILL Step 5 模板逐行渲染的报告 → **exit=1**，两条 ✗：(1) `数字终核: scan JSON 无可用 ledger, 台账『种子』行无法绑定`；(2) `『（规模自陈等前置段）』段的计数 1 找不到同值来源: > 数据面：manifest（1 次调用）/ 无截断`。第二条的 `1` 来自 SKILL.md:228 写死的模板常量（与已登记的「最老 3 条原话」同性质），空板池 base={0,30,100,10} 里没有 1。对照组：把板改成 2 成员/0 批注（ledger 非空 → pick_rank=1 把 1 带进池）→ exit=0，证明这条只在空板触发。_D2_TEMPLATE_CONSTANTS(:1258) 只登记了一条常量。"
  },
  {
   "title": "台账种子行只接受裸 node_id：`node_id（显示名）` 形态被报成「不在 ledger 里」，理由与实况不符",
   "kind": "false_positive",
   "severity": "MEDIUM",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1416",
   "evidence": "把 递归与分治 台账行写成 `- my-recursion-notes（我的递归笔记） — 无批注；未派生（…）`（该节点确实在 ledger 里，写法与报告别处 `节点 csm-tutoring-unit-credit（CSM 辅导学分）` 一致）→ **exit=1**：`✗ 数字终核: 台账『种子』行的节点 'my-recursion-notes（我的递归笔记）' 不在 scan JSON 的 ledger 里 (台账不得列出未扫描到的节点)`。_SEED_LEDGER_LINE_RE 的 node 组吃掉整个「id（显示名）」串后做精确 dict 查表，失败即报「未扫描到的节点」——诊断把「写法不认」说成「数据不存在」，会把作者往错误方向引。"
  },
  {
   "title": "序数引用与报告自指计数一律无出处（「第 4 条动作建议」「以上 4 条建议」「本段以下 3 处判断」）",
   "kind": "false_positive",
   "severity": "MEDIUM",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1376",
   "evidence": "递归与分治 板（该报告 `## 你现在可以做的` 实有 4 个编号项）：(a) ②段 `- 上面第 4 条动作建议依赖的是历史题面摘句【文件】…` → **exit=1**（计数 4）；(b) ②段 `- 本段以下 3 处判断全部只有材料内部证据…` → **exit=1**（计数 3）；(c) 动作段后 `以上 4 条动作建议按材料缺口的紧迫程度排列【推定】。` → **exit=1**（计数 4 + 动作段白名单各一条）。序数（位置）与「报告自身列了几条」都不是板数据，按定义永远进不了 scan 数值池；卡文 E5 只豁免了行首有序列表**标记**本身，没有覆盖对序号/条目数的正文引用。"
  },
  {
   "title": "E7 范围豁免只覆盖一种写法：`4~5 条` 放行，`4 个到 5 个` / `4、5 条` / `4/5 条` 全部 FAIL",
   "kind": "false_positive",
   "severity": "MEDIUM",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1259",
   "evidence": "同一块板（递归与分治）同一段的四种等价写法：`- 预计还需补 4~5 条批注才能闭环【推定】。` → **exit=0**；`- 预计还需补 4 个到 5 个批注点才能闭环【推定】。` → **exit=1**（两条 ✗：计数 4、计数 5）；`- 预计还需补 4、5 条批注才能闭环【推定】。` → **exit=1**（计数 5）；`- 覆盖率 4/5 条批注带来源锚点【推定】。` → **exit=1**（计数 5）。_D2_RANGE_RE 要求「数字 分隔符 数字 量词」紧邻，端点各自带量词、用顿号并列、或写成分数形态都落在豁免之外，而它们与 `4~5 个` 是同一语义。"
  },
  {
   "title": "量词表的任意性直接决定判决：同义的「5 处」FAIL 而「5 点」PASS，「19 个」FAIL 而「19 类」PASS",
   "kind": "false_positive",
   "severity": "MEDIUM",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1232",
   "evidence": "递归与分治 ②段单变量对照：`- 材料面共有 5 处证据缺口【推定】。` → **exit=1**；`- 材料面共有 5 点证据缺口【推定】。` → **exit=0**。CS188 派生节点改名对照：`规划的 19 类划分方式` → **exit=0**；`规划的 19 个分类维度` → **exit=1**。live 报告本身两种都在用（`已派生 7 点` vs `7 个派生点`）。_D2_QUANT 是封闭字符集 `[个条块次份处板项篇道张]`，把「不按字符划分」的裁定又搬回了一张字符表，只是从「哪些汉字算数值」换成了「哪些汉字算量词」；作者改一个字就能翻转判决。"
  },
  {
   "title": "小数计数的诊断会额外错报一条：`1.5 条` 同时报「小数 1.5」和「计数 5 找不到同值」，5 只是小数尾部",
   "kind": "other",
   "severity": "MEDIUM",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1233",
   "evidence": "递归与分治 ②段 `- 全板平均每个成员 1.5 条批注【推定】。` → **exit=1**，两条 ✗：`『三维审查』段出现小数形态的计数 1.5 …` + `『三维审查』段的计数 5 在 scan JSON 里找不到同值来源 …`。_D2_COUNT_RE 的 lookbehind 从 `(?<![0-9.])` 改成 `(?<![0-9])` 之后，小数点后的尾数成了独立 token；_D2_DECIMAL_RE 先命中并不消费它。作者据第二条去找「哪来的 5」时会扑空。同时该行整体不可能通过（scan 计数皆整数），意味着任何合法均值/比率陈述都被硬禁——这是有意设计还是副作用，代码与验收单未登记。"
  },
  {
   "title": "`1)` 形态有序列表与 markdown 链接文本未纳入 E5/E3 豁免",
   "kind": "false_positive",
   "severity": "LOW",
   "anchor": "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py:1252",
   "evidence": "(a) `1) 6 条结构字段全空【实测】。`（`1)` 列表形态）插入 递归与分治 ①段 → **exit=1**（计数 6）；_D2_ORDERED_LIST_RE 只认 `^\\s*\\d+\\.\\s`。(b) `- 分治部分的材料缺口详见 [分治的 7 个标准步骤](节点/divide-conquer.md)【文件】。` → **exit=1**（计数 7）；_D2_WIKILINK_RE 只处理 `[[…]]`，标准 markdown 链接的显示文本没有对应豁免。(c) 相关：`[[节点/x|分治的 7 个标准步骤]]` 的别名段也 **exit=1** —— 这是最新一版把 E3 收窄成「只豁免目标部分」的直接后果，与卡文 E3「wikilink 内部…是原文不是断言」的书面裁定相反。"
  },
  {
   "title": "验收单「一个字都不能误伤」与放行门的证据力：158 全绿的同时 12+ 类合法语料被拒",
   "kind": "claim_mismatch",
   "severity": "LOW",
   "anchor": "_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md:44",
   "evidence": "验收单 §一 标题为「一个字都不能误伤（这一半和上面同等重要）」，放行门表只列了 4 份 live 真报告 + round-5 那几条合成短句 + 日期/wikilink/`Cmd+Shift+D` 三条。实测：在 `pytest tests/regression/test_recap_scan_signals.py -q` 报 **158 passed** 的同一版本上，本次构造的 12 类合法语料全部 exit=1（跨板不一致、节点名、引用原话、闭环 diff、frontmatter、空板、序数/自指、范围写法变体、量词表、markdown 链接、`1)` 列表、小数均值）。§五之二 裁决点 2 只登记了**拦截力弱**的边界（「对常见小数值形同虚设」），没有登记**误伤面**的边界；而误伤恰恰不会让测试变红。另注：被审文件在本次审查期间被并发改动三次（sha256 c8346abf → f3ea2974 → 696e794e，4 分钟内），最后一次实测时 `pytest` 为 2 failed / 171 passed；上列全部 exit code 均锚定在冻结快照 f3ea2974 上复跑确认。"
  }
 ]
}
```
