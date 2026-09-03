# CARD-G8-2 独立对抗审查（round-7 · 用户授权定向续轮第四轮）

你是独立审查者。round-1..6 存档于 codex-review-CARD-G8-2*.md；round-6 你判
0 BLOCKER + 2 HIGH + 4 MEDIUM。本轮复核 round-6 全部发现的整改。工作目录 =
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、核心整改声明：「先剥除再扫描」→ **区间盲区法**（结构性重构）

round-6 的两个 HIGH（`` [[A`x`]] `` 空格占位仍造伪链 / "[<!--x-->[A]]" 注释拼接造伪链）
与你两条 MEDIUM（escaped backtick 误剥真链 / span 跨空行误剥真链）同根因：**先剥除非语义
内容再扫描 wikilink**，任何占位策略都可能改写文本。

整改：删除 `_strip_nonsemantic` / `_strip_code_spans`，新增
- `_semantic_blind_intervals(body)`：返回非语义区间的**字符偏移**（AUTO 哨兵段、fenced
  code 行区间、code span、HTML 注释；区间取并集——round-2 登记的 AUTO-fence 交叉缝隙由此闭合）；
- `_code_span_intervals(text)`：CommonMark 算法——maximal run、closer **严格等长**
  （round-5 H1 语义保留）、**转义**反引号（奇数反斜杠前缀）不是 delimiter（r6 M1）、
  opener/closer 之间含空行不配对（r6 M2，span 不跨段落）；
- `_wikilink_targets`：在**原始文本**上 `_WIKILINK.finditer`，起点落在任一盲区间的匹配丢弃。

结构保证：扫描对象是原文，**不可能**制造原文不存在的伪链（H1/H2 类缺陷被结构性消灭）；
原文真实存在的 wikilink 只要不落在盲区间就被采纳（escaped/跨段类误剥被消灭）。

## 二、四个新判别用例（fixture 逐字取自你的 round-6 反例与 CommonMark 规则）

| 用例 | 输入 | 期望 |
|---|---|---|
| test_code_span_inside_wikilink_does_not_create_link | `[[A\`x\`]]` | A 报孤儿（伪链不得制造） |
| test_html_comment_inside_bracket_does_not_create_link | `[<!--x-->[A]]` | A 报孤儿 |
| test_escaped_backtick_is_not_delimiter | `` \`x [[A]]\` `` | A **不**报（真入链保留） |
| test_code_span_does_not_span_blank_line | `` `x `` + 空行 + `` [[A]]` `` | A **不**报 |

## 三、新增/重锚变异 M7/M20/M21/M22（区间法形态）

M7 盲区间检查拆除（杀 nonsemantic 组）/ M20 code span 区间源拆除（杀 maximal 组）/
M21 转义识别拆除（杀 escaped 用例）/ M22 跨空行配对拆除（杀 blank-line 用例）。
harness 转换器新增 `\Q` 转义（锚含源码字面 `\n` 时不再被换行转换吞掉——本教训见
MEMORY「argv 里的 \n 是字面两字符」的补全）。

## 四、其余顺带整改（round-6 M3/M4 与 LOW）

- UAT 全文统一 round-7 终态（190 passed / 22 mutant / SHA aa2eca15…）；历史段标注时点快照；
  附 C 增补 r4/r5 对照、附 D 级别的轮次史在 §6.10。
- live sha 门覆盖面收窄声明（§6.11）：`-not -name` 按 basename 排除任意目录同名文件、
  shasum 不覆盖 symlink 指向——「排除后全树普通文件内容零写」已证，其余不在承诺内。
- `test_help` 的盲区断言精确到 raw_derived 专属 G8/G10/G11 句（r6 LOW 判别力修正）；
  harness 头注改 round-6；live-window-round7.txt 带 before/after 标签。

## 五、终态裁判（当前字节，MANIFEST 绑定）

referee1-pytest-full-round7.txt = **190 passed**（71 本卡 + G8-1 119 零回归）+
22/22 mutant KILLED + live 第七轮 sha `a82e3af0…` 前后逐字相同 rc=0 + 禁改门空。

## 六、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
round-6 各条若整改不成立标 REGRESSED；区间法重构引入的新面请重点对抗（区间并集/偏移
对齐/keepends/转义计数/空行判定），并跑你自己的对抗 fixture。
最后一行：`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
