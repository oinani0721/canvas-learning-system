export const meta = {
  name: 'rv-d-review',
  description: 'CARD-RV-D：Z6-A 七条整改逐条定性 + 对抗验证 + 完备性批判（审面钉死 514cff3c..e22ad10a）',
  phases: [
    { title: 'Assess', detail: '8 个维度各自独立定性（6 条自述 + 2 个特别判）' },
    { title: 'Refute', detail: '每条结论派 2 个不同视角的反驳者' },
    { title: 'Gaps', detail: '完备性批判：什么没查' },
  ],
}

const E = '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene/_bmad-output/审查/evidence-rv-d'

const BOUNDARY = `
## 读取面（硬边界）

先读 ${E}/审查上下文.md —— 它有审面定义、作者六条自述原文、关键代码位置。

你的读取面**就是这两份 diff 文件**：
- P1: ${E}/rv-d-p1.diff  （g32ccr1 负控 + validator + schema doc，+348/-3）
- P2: ${E}/rv-d-p2.diff  （回归测试门 + g32cb 变异 harness，+508/-6）

⛔ 审面是 commit \`514cff3c..e22ad10a\`，**不是 HEAD**。HEAD 上同族文件在
e22ad10a 之后又被 Z6-B/Z6-C 改了 +169/-11，读 HEAD 会把后两卡的改动算进结论。
⛔ 此刻工作树上有变异 harness 正在运行，\`canvas-vault/.claude/skills/quiz-answer/SKILL.md\`
与 \`backend/scripts/validate_learning_events.py\` 可能处于**被临时改写**的状态 ——
不要读它们的工作树版本。需要上下文时可以读，但**结论只能引用 diff 内的行**。
⛔ 只读。不改任何文件，不连任何数据库端口。
⛔ 行号一律写成 \`e22ad10a:<文件>:<行>\`。判不了的写「未验证」，不要猜。

## 措辞

描述负控时用：「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
`

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    item: { type: 'string', description: '被定性的条目，如 "(a) 不扩表裁定"' },
    verdict: { type: 'string', enum: ['成立', '部分成立', '不成立', '整改引入新问题', '未验证'] },
    one_line: { type: 'string', description: '一句话结论' },
    evidence: { type: 'array', items: { type: 'string' }, description: 'e22ad10a:文件:行 形式的具体依据，至少 1 条' },
    reasoning: { type: 'string', description: '推演过程，要能被人复算' },
    new_problems: { type: 'array', items: { type: 'string' }, description: '整改本身引入的新问题（没有就空数组）' },
    unverifiable: { type: 'string', description: '这一条里你无法只读判定的部分' },
  },
  required: ['item', 'verdict', 'one_line', 'evidence', 'reasoning', 'new_problems', 'unverifiable'],
}

const REFUTE_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean', description: '该结论是否被推翻' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    why: { type: 'string' },
    counter_evidence: { type: 'array', items: { type: 'string' } },
    corrected_verdict: { type: 'string', description: '若推翻，正确的定性应该是什么；否则空串' },
  },
  required: ['refuted', 'confidence', 'why', 'counter_evidence', 'corrected_verdict'],
}

const DIMENSIONS = [
  {
    key: 'a-no-expand',
    title: '(a) 不扩表裁定',
    prompt: `定性作者自述 (a)：receipt 14 键与严格表差集 = {question_id, self_confidence_raw}，裁定**不扩表**，依据收窄为「当前写点不写、复放不读」。

重点核：
1. 这个收窄后的依据在 diff 里有没有落地（代码注释 / docstring / schema §6.1 的措辞）？措辞是否比证据宽？
2. 作者说「扩表后四回归只有 2 道表声明门变红，无行为门变化」—— diff 里有没有能支持这个对照实证的东西？还是纯自述？
3. 「枚举表零改动」在 P1 的 validator diff 里能否证实？`,
  },
  {
    key: 'b-unreachable',
    title: '(b) 差集字段写得进读不回不可达',
    prompt: `定性作者自述 (b)：差集字段「写得进读不回」不可达，靠 q_() 往返自证（负控 E4）+ _TS_RE 词法门（负控 E8）兜住。

重点核：
1. E4 与 E8 这两条负控在 P1 diff 里的实现，是否真的各自只拆掉**被测的那道防线**、而没有连带拆掉别的（拆多了会导致「被更早的防线喂饱」式的假杀）？
2. 作者说原版 E8 被 review_time 那道门喂饱、现已「拆成单字段用例并核对拒因」—— diff 里能否看到「核对拒因」这一步？还是只断言了 rc？
3. self_confidence_norm 那条 HIGH：diff 里除了 xfail 锚，有没有任何**实际约束**被加上？（作者说没有，请独立确认）`,
  },
  {
    key: 'c-nondict',
    title: '(c) 非 dict 分支不可达 + AST 三处收紧',
    prompt: `定性作者自述 (c)：value_charset_problems 非 dict 分支不可达；AST 判据收紧三处（任何 Store 上下文的 record / 守卫与调用同为顶层语句且守卫在前 / 守卫须比 dict 且立即 return），负控 E5/E10。

重点核：
1. 这三处收紧在 P1 diff 里逐条对得上吗？有没有哪一处是自述有、代码没有？
2. E5（在 validate_record_full 里重绑 record）与 E10（用海象重绑）是**两个不同的**对照输入吗，还是同一形态的两种写法（若是后者，它们不构成独立覆盖）？
3. 「不可达」的推理依赖哪些前提？这些前提在 diff 内可证，还是要读 HEAD 全文才能证（后者请标「未验证」）？`,
  },
  {
    key: 'd-emitter',
    title: '(d) emitter 判据改造【特别判】',
    prompt: `**这是本卡的重点判项，请逐字推演，不要采信自述。**

作者自述 (d)：emitter 门原判据是**子串包含**，对「行复制」「行位移」双盲（E1/E2 实测 SURVIVED）。新判据改为「整条按边界逐字节 + 出现次数 = 1 + 紧跟 calibration_log:」+ 第三阶段补 rc==0。

**核心问题：新判据是否真能区分这两种情况？**
- E1 = A 行被**复制到别处**（原位置还在，别处多了一份）
- E2 = A 行**位移**（键序重排，行文本逐字节不变，位置变了）

请在 P2 diff 里找到新判据的实现代码，**逐字推演**它对 E1 和 E2 分别会得到什么结果：
- 「出现次数 = 1」能抓 E1 吗？（复制 ⇒ 出现 2 次 ⇒ 应该能抓）
- 「紧跟 calibration_log:」能抓 E2 吗？（位移后 A 行还紧跟着 calibration_log 吗？取决于位移到哪）
- 有没有一种位移方式能同时满足「出现 1 次」和「紧跟 calibration_log:」但仍然是真实的行序破坏？
- 「整条按边界逐字节」中的「边界」具体怎么切的？切法是否会漏掉行尾空白/换行差异？

另外核：第三阶段补的 rc==0 判据，加在哪一步？它防的是什么？`,
  },
  {
    key: 'e-anchor',
    title: '(e) g32cb 锚点自检提前 + --list',
    prompt: `定性作者自述 (e)：g32cb 锚点自检提前 + 兑现未实现的 --list；并**如实登记**「锚漂 ⇒ 8/8 假绿」这个前提不成立（因为原本就有 ANCHOR-ERROR 分支），以及注释诱饵/缩进漂移的盲区。

重点核：
1. 「锚点自检提前」在 P2 的 g32cb diff（61/1 行）里具体是怎么实现的？提前到了哪一步之前？
2. 作者主动承认「锚漂 ⇒ 假绿」前提不成立 —— 这个自我更正在 diff 的注释里落地了吗？还是只写在 commit message 里？（只写在 message 里 = 后人读代码看不到）
3. 「注释诱饵 / 缩进漂移」这两个盲区，新的锚点自检能不能挡住？请按实现推演。
4. --list 的实现是只打印，还是同时做了锚点校验？（若只打印，它对「锚漂」没有防御价值）`,
  },
  {
    key: 'f-ast',
    title: '(f) 一致性门 AST 化 + 严格表钉死 + tuple',
    prompt: `定性作者自述 (f)：一致性门提取器从正则改 **AST**（注释诱饵/改名/双引号 f-string 都会暴露）+ 严格表逐项钉死（堵住空表空真），负控 E9；容器门补 tuple 样本（E11）。

重点核：
1. AST 提取器在 P1/P2 diff 里的实现：它到底提取什么？「注释诱饵」为什么 AST 能挡而正则不能——请按实现说清机制，不要复述自述。
2. 「严格表逐项钉死」是把期望值**写死成字面量**，还是**从实现读取**？后者会让变异同时改掉门的期望值（门看不见变异）——这是已知的经典陷阱，请重点确认。
3. E9（把严格字段表清空）会被新门抓到吗？E11（删掉 tuple 支持）呢？请分别推演。`,
  },
  {
    key: 'p1-killed-judge',
    title: '【特别判】g32ccr1 的 KILLED 判据是否有假杀面',
    prompt: `**这是本卡要给下一张卡（Y1-B）的定向输入，请给出可执行的结论。**

g32ccr1_negative_controls.py 的 KILLED 判据（主干 :277）是：

    killed = rc == 1 and gate in out and "failed" in out

g32cb_mutation_gates.py:383 同型（多一个 "1 failed" in out or "failed" in out）。

它**不解析失败集合、不绑定断言身份**。这与已知的「Z2 M15 假杀」是同一族缺陷：
**红在别的断言上，也会被算成 KILLED。**

请在 P1 diff 里找到这个判据的实现（它是本次新增的 306 行的一部分），然后回答：

1. 在「变异确实生效，但让门在**另一条**断言上变红」这种输入下，判据会报 KILLED 吗？
   （如果会 ⇒ 假杀：击杀被归给了错误的原因）
2. 在「变异体**语法错误 / 未编译 / import 失败**」这种输入下呢？
   （pytest 会 rc≠0 且输出含 "failed"/"error"，判据可能仍报 KILLED ⇒ 假杀）
3. 判据里的 \`gate in out\` 起了多少作用？它是在匹配 gate 的**名字字符串**吗？
   若门名出现在 pytest 的收集行/摘要行里（而不是失败行里），这个条件是否恒真？
4. 要修成「绑定失败身份」，最小改动是什么？（给出可执行建议，供下一张卡采纳）

这 11 条负控里，有哪几条的击杀**可能**是靠这个宽判据成立的（即：换成严格判据后可能变 SURVIVED）？`,
  },
  {
    key: 'xfail-anchor',
    title: '【归口】self_confidence_norm HIGH 的 xfail 交接锚',
    prompt: `**这是卡文 (d) 要求的归口分析。**

交接锚在 \`test_g3_2_review_ledger.py:6294-6333\`（P2 diff 里应能找到它的新增）：

    @pytest.mark.xfail(strict=True, reason=…)
    def test_g32ccr1_self_confidence_norm_must_not_forge_receipt_identity

测试体逻辑：
- 以 \`self_confidence_norm='0.5\\n    event_id: "quiz:injected"'\` 跑写点
- \`if r.returncode != 0:\` → 断言账本零写后 **return**（**拒绝也算通过**）
- 否则 → 断言 \`calibration_log[-1]["event_id"] == "quiz:板戊#q1"\` 且原样重跑 \`rc==0\`

请对**三种未来的缺陷修法**分别推演这个锚会怎样反应：

① 写点**拒绝**（rc≠0 且零写）→ 测试通过 → XPASS(strict) 变红 ✅ 锚有效
② 写点**转义/规范化后照写**，receipt 身份不变且重跑 rc==0 → 测试通过 → 红 ✅ 锚有效
③ 写点**拒绝但非零写**（先落账再拒）→ \`assert len(_ledger_lines)==0\` 失败 → 仍 xfail → **锚静默**

请核对这三条推演是否正确（按 diff 里的实际测试体，不是按我的复述），并回答：
- 还有没有**第四种**修法会让锚静默？
- 是否需要把锚改成两段（一段管拒绝路径、一段管写入路径）？给出具体建议。
- \`strict=True\` 在这里是否用对了？（strict=False 会让 XPASS 安静通过 = 锚失效）`,
  },
]

const REFUTE_LENSES = [
  { key: 'evidence', ask: '证据是否支持这个结论 —— 有没有把「自述」当成「已验证」、把「没看到」当成「不存在」、或者引用了审面之外（HEAD 上）的行？' },
  { key: 'mechanism', ask: '机制推演是否成立 —— 判据/门/负控的实际行为，是否真如结论所说？找一个能让结论翻转的具体输入或场景。' },
]

phase('Assess')
log(`审面 514cff3c..e22ad10a（+856/-9），${DIMENSIONS.length} 个维度并行定性，每条 2 个视角反驳`)

const results = await pipeline(
  DIMENSIONS,
  (dim) => agent(
    `你在复核一个**已经合并的整改 commit**，任务是独立定性它的一条自述是否成立。\n${BOUNDARY}\n\n---\n\n# 你负责的条目：${dim.title}\n\n${dim.prompt}\n\n---\n\n给出 verdict（成立 / 部分成立 / 不成立 / 整改引入新问题 / 未验证）+ 至少一条 \`e22ad10a:文件:行\` 形式的具体依据 + 可被人复算的推演过程。\n**宁可写「未验证」，也不要给没有依据的结论。**`,
    { label: `assess:${dim.key}`, phase: 'Assess', schema: VERDICT_SCHEMA }
  ),
  (verdict, dim) => {
    if (!verdict) return null
    return parallel(REFUTE_LENSES.map((lens) => () => agent(
      `你是对抗性复核者。下面是另一位复核者对整改 commit \`e22ad10a\` 的一条定性结论，**你的任务是尽力推翻它**。\n${BOUNDARY}\n\n---\n\n# 被审的结论\n\n条目：${verdict.item}\n定性：**${verdict.verdict}**\n一句话：${verdict.one_line}\n依据：${JSON.stringify(verdict.evidence, null, 2)}\n推演：${verdict.reasoning}\n新问题：${JSON.stringify(verdict.new_problems)}\n自称未验证的部分：${verdict.unverifiable}\n\n---\n\n# 你的审视角度\n\n${lens.ask}\n\n---\n\n去 diff 里核对它引用的每一行是否真的存在、是否真的支持它的说法。\n**不确定时默认 refuted=true** —— 宁可错杀一个站不住的结论，也不要放过它。\n若你推翻了它，在 corrected_verdict 里写出正确的定性。`,
      { label: `refute:${dim.key}:${lens.key}`, phase: 'Refute', schema: REFUTE_SCHEMA }
    ))).then((votes) => ({
      dim: dim.key,
      title: dim.title,
      verdict,
      refutations: (votes || []).filter(Boolean),
    }))
  }
)

const assessed = results.filter(Boolean)
const survived = assessed.filter((r) => r.refutations.filter((v) => v.refuted).length < 2)
const contested = assessed.filter((r) => r.refutations.filter((v) => v.refuted).length >= 2)
log(`定性完成：${assessed.length} 条；未被多数推翻 ${survived.length} 条，被推翻/争议 ${contested.length} 条`)

phase('Gaps')
const gaps = await agent(
  `你是完备性批判者。下面是一次复审的全部结论。你的任务只有一个：**指出什么没被查**。\n${BOUNDARY}\n\n---\n\n# 已完成的定性\n\n${JSON.stringify(assessed.map((r) => ({
    条目: r.title,
    定性: r.verdict.verdict,
    一句话: r.verdict.one_line,
    自称未验证: r.verdict.unverifiable,
    被推翻票数: r.refutations.filter((v) => v.refuted).length,
    反驳要点: r.refutations.map((v) => v.why),
  })), null, 2)}\n\n---\n\n请回答：\n1. 这次复审有哪些**审面内**的东西没人看？（两份 diff 里有哪些 hunk 没被任何一条定性覆盖到）\n2. 有哪些结论是靠「作者说」而不是「diff 里能看到」成立的？\n3. 856 行新增里，有没有**看起来是测试/门、实际上会改变生产行为**的改动被漏掉？\n4. 有没有哪条定性的「未验证」其实是可以在 diff 内验证的（即：不该放弃）？\n\n只列真问题，每条给出具体的文件/hunk 定位。没有就说没有。`,
  { label: 'gaps:completeness', phase: 'Gaps' }
)

return {
  审面: '514cff3c..e22ad10a (+856/-9, 5 files)',
  定性条数: assessed.length,
  未被多数推翻: survived.map((r) => ({ 条目: r.title, 定性: r.verdict.verdict, 一句话: r.verdict.one_line })),
  被推翻或争议: contested.map((r) => ({
    条目: r.title,
    原定性: r.verdict.verdict,
    推翻理由: r.refutations.filter((v) => v.refuted).map((v) => ({ why: v.why, 更正为: v.corrected_verdict })),
  })),
  全部明细: assessed,
  完备性批判: gaps,
}