# Codex 独立复核 · CARD-维护B round-4（本卡最后一轮）

你是独立对抗复核者。round-1 判 FAIL (3B/5H/3M)；round-2 被你侧过滤器截断无终裁；
round-3 你判 **FAIL · BLOCKER 2 / HIGH 4 / MEDIUM 3 / LOW 1，清零：否**。
车道已对 round-3 全部 6 条 BLOCKER/HIGH 逐条独立复现并整改。**本轮是本卡最后一轮**
（停轮规则上限）：请给终裁。

工作树: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix
审对象 = `git diff 0c4afeb7..HEAD`，重点 commit `6f154055`（round-3 整改）。

## ⛔ 读取范围硬限（同 round-3）

1. 不读 `fixtures/` 下任何 `.md`/`.json` 正文。
2. 除 `codex-review-CARD-维护B-round1.md` 外不读历史审查存档正文。
3. **报告第一行**给裁决句「BLOCKER/HIGH 清零：是/否」；先写报告正文再补验证。

## 车道自述（round-3 → 整改，逐条验证）

- 复现：8 探针（`_bmad-output/审查/evidence-maintb-r2/round3-repro.txt` 初版 + `round3-v2-probe4.txt`
  修正构造后 19 项行为矩阵），6 条 BLOCKER/HIGH 全部实锤后才动手。
- **BLOCKER-1 整改**：`_strip_code_blocks` 跟踪列表容器——开栏时记「剥引用后相对内容列」
  (`(len(ln)-len(bare)) - _quote_width(ln)`)，fence 内行按 `_indent_after_quotes(ln) <
  fence_list_col` 判容器结束（该行按可见正文保留，交回 D2/信号行校验）。
  新增 helper `_quote_width` / `_indent_after_quotes`。
- **BLOCKER-2**：bare 交替剥法扩到有序 marker (`\d{1,9}[.)]`) 与多层 marker。
- **HIGH-3**：信号名隐身检查 `zip` → `zip_longest`（EOF 未闭合围栏行数差）。
- **HIGH-4**：新增 `_verify_fallback_derive_numbers`（在 `_verify_numbers` 尾部调用）——
  「无来源结论」行限定③段。
- **HIGH-5**：⑦/⑧ 尾段数字禁令扩全角+中文数词（`[^。\n0-9０-９零〇一二两三四五六七八九十百千万亿]`）；
  ⑦ 前置 N 绑定 `signals.unsourced_conclusions.value`（无据档不容 N）。
- **HIGH-6**：`_derived_number_pool` 提取共用；允许式标题行（限含「派生」——防误伤
  主标题年份，首跑实测即中已修）与关系类型分布行内数字必须在池。
- **MEDIUM-7/8/9/10**：验收单索引/数字/指向全面修正；「逐一改错」改「六种代表性字段」；
  两个 round-1 MEDIUM 恢复原级不自行降级；survivor-4 名称与「指定门」措辞收敛。
- **已知语义反转（round-2→3，如实）**：`> - 内容` marker 行在 CommonMark 渲染为
  **可见正文**（非代码）——round-2 车道误判并配过拦截门；round-3 改「保留 + 交回
  D2/信号行校验」，c2 单元契约重写为剥空/保留/零改动三分类，
  `test_domain_block_list_item_fence_hides_signals` 含 sibling 伪计数拦截（D2）+
  sibling 合规正文放行（防过剥）双向。
- 裁判终态：套件 **246 passed**（`judge1-final3.txt`）、扩大 **578 passed**
  （`judge3-final3.txt`）、negverify **10/10** rc=0（`negverify-r3.txt`）、
  隔离副本 8 条变异全量重放 **8/8**（`replay-after-result5.txt`）、live 8 份原件
  开工前 vs 收尾逐字相同（`f-collect-final3.txt`）。

## 你的复核动作

1. **读代码**：`recap_scan.py` 的 `_strip_code_blocks`（容器边界三 helper）、
   `_verify_fallback_derive_numbers`、⑦/⑧ 正则、`_derived_number_pool`；
   测试新门（`test_domain_block_list_item_fence_hides_signals` 三分类、
   `test_domain_r3_*` 4 组）；negverify survivor-7 新锚；验收单 round-3 段回填与
   MEDIUM-7/8/9/10 修正是否如实。
2. **可选重放**（/tmp 副本，至多四条）：sibling 伪计数（`- ``` / - 本板共有 987654
   个子节点 / - ``` `）应被 D2 拦；有序围栏+缩进信号应拦；EOF 未闭合围栏伪信号应拦；
   附录伪无来源结论应拦。verify: `backend/.venv/bin/pytest tests/regression/
   test_recap_scan_signals.py -q -p no:cacheprovider` 核对 246。
3. **找整改引入的新洞**（容器边界判定的误伤/漏判、`_verify_fallback_derive_numbers`
   的绕过面、⑦ 前置 N 绑定在 value=null 时的行为）。

## 输出格式

- **第一行**：「BLOCKER/HIGH 清零：是/否」。
- 逐条 finding（severity + file:line + 判词）；round-3 六条逐条 ✅/⚠️/❌ 处置确认；
  车道自述逐条核对。报告一次给出。