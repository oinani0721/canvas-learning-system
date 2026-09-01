# Codex 定向复核 · CARD-维护B round-5（仅审 round-4 三缝隙整改）

你是对抗复核者。历史：round-1 FAIL(3B/5H/3M)；round-2/round-4 两次被你侧 cyber
过滤器截断无终裁；round-3 FAIL(2B/4H) 已全部整改并经你 round-3 报告点名。
**本轮范围极窄**：只复核 round-4 从你 stderr 抢救出的三条缝隙（A/B/C）的整改。
不要扩展到其它面——其它面 round-1~3 已覆盖并有存档。

工作树: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix
相关 commit: `ff946d8c`（round-4 整改）。

## ⛔ 硬限（保证本轮不触发你侧过滤器）

1. **不要构造、不要运行任何变异/探针命令**——车道已提供先红与整改后的完整实测
   （见下），你只做**静态审读 + 跑既有套件**。
2. 不读 `fixtures/` 下任何 `.md`/`.json` 正文。
3. **报告第一行**：「BLOCKER/HIGH 清零：是/否（就 A/B/C 三缝隙及其整改而言）」。

## 三条缝隙与整改（你 round-4 stderr 的探针实测 → 车道整改）

| # | 你 round-4 的实测（stderr :4551-4554） | 整改（`ff946d8c`） | 整改后实测 |
|---|---|---|---|
| A | ` > - ``` `（引用标记前带前导空格）围栏藏信号 rc=0 | `_quote_width`/`_indent_after_quotes` 重写为**绝对内容列**口径（前导空白计入引用系；fence_list_col = 本行剥掉的前缀长度；容器终止判定 = `_quote_width(ln)+_indent_after_quotes(ln) < fence_list_col`） | rc=1 拦 |
| B | manifest 模式附录伪无来源结论 rc=0 | `_verify_fallback_derive_numbers` 的③段限定移出 data_mode 条件（manifest 同样生效） | rc=1 拦 |
| C | 允许式标题行中文数词（`九十八万`）rc=0 | 数字提取加 `[零〇一二两三四五六七八九十百千万亿]+` 序列，`_cjk_to_int` 可解析入池比对、解析失败 fail-closed 报「无法验证」 | rc=1 拦 |

车道证据（`_bmad-output/审查/evidence-maintb-r2/`）：
`round4-repro.txt`（先红，A/B/C 全 exit 0）、`round4-after3.txt`（整改后 A/B/C 全拦 +
round-3 全矩阵 19/19 无回归）、`judge1-final5.txt`（套件 249 passed）、
`judge3-final5.txt`（扩大 581 passed）、`negverify-final5.txt`（10/10 rc=0）、
`f-collect-final5.txt`（live 8 份开工前 vs 收尾逐字相同）。

## 你的复核动作（只有三步）

1. **读代码**（`canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py`）：
   - `_quote_width` / `_indent_after_quotes`（≈:1000-1030）与 `_strip_code_blocks`
     内的容器终止判定（≈:1050-1075）——口径是否自洽（绝对列 vs 相对列混用即洞）；
     `fence_list_col` 的设置条件（marker 检测）；
   - `_verify_fallback_derive_numbers`（≈:1791 起）——③段限定位置（data_mode
     return 之前）与 fallback 段的边界；
   - HIGH-6 数字提取段（≈:1852 起）——中文数词提取与 `_cjk_to_int` 失败分支。
2. **读测试**（`backend/tests/regression/test_recap_scan_signals.py`）：
   `test_domain_r4_leading_space_blockquote_list_fence` /
   `test_domain_r4_manifest_appendix_signal_in_section3_only` /
   `test_domain_r4_derive_allow_cjk_numbers_in_pool` 三门的断言是否与实现一致、
   `test_domain_strip_code_blocks_unit_contract` 的三分类用例是否被新口径推翻。
3. **跑一遍套件核对 249**：`cd backend && .venv/bin/pytest
   tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`。

## 输出格式

- **第一行**：「BLOCKER/HIGH 清零：是/否（就 A/B/C 三缝隙及其整改而言）」。
- 三条逐条 ✅/⚠️/❌ + `file:line` 判词；发现的新问题按 severity 列出（仅限本轮
  整改直接引入的）。
- 报告一次给出；先写正文再补过程。