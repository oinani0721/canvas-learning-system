# Codex 冻结审查 · CARD-维护B-R3（中文数词与计数绑定的提取/判据面）

你是对抗复核者。历史：round-1 FAIL(3B/5H/3M)；round-2/round-4 两次被你侧 cyber
过滤器截断无终裁；round-3 FAIL(2B/4H) 已整改；**round-5 判 A ✅PASS / B ✅PASS /
C ⚠️HIGH**。`c754b043` 是对 C 的整改但无独立终审。

**本轮范围**：只审「中文数词 / 计数的**提取面与判据面**」这一条线（C 面）。
A/B 已 PASS，不重开。

工作树: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix
基线 commit: `c754b043`（round-5 整改，本轮审查起点）。

## ⛔ 规则（请逐条遵守）

1. **不读 `fixtures/` 下任何 `.md`/`.json` 正文；不访问 live vault。**
2. 需要时**可以**在 `/tmp` 下构造合成 fixture 并运行只读探针（车道已提供全部
   实测数据，你也可以自行复算）。**不要**写入本工作树。
3. **新问题不限于"本轮直接引入"** —— C 面上任何可复现的缺陷都请报，并如实标注
   它是"本卡引入"还是"存量未闭合"。上一轮的范围限定被车道自查判为**结构性
   导向 PASS**，本轮已移除。
4. **报告第一行**：「BLOCKER/HIGH 清零：是/否（就 C 面而言）」。

## 时间线（车道如实交代，含自己踩的洞）

### round-5 对 C 的判词（属实）

> 提取字符集与 `_CJK_NUM`/`_CJK_UNIT` 完全相同 ⇒「解析失败 fail-closed」分支
> **静态不可达**；连续数字字仅反复覆盖 `digit`，可能只保留末位并对**错误的
> 小值查池**；若发生池碰撞，同类允许式仍可通过。

### R3 第一刀：判据统一（`c754b043` 只封了两个消费面中的一个）

车道在开工 HEAD 的字节上实测：`_verify_prose_counts`（D2 叙述段）**仍在调**多位
解析器 `_cjk_to_int`，`- 本板共有一零个子节点。【实测】` **exit 0 放行**
（`_cjk_to_int("一零")==0`，0 恒在池内 `abs(a-a)`）。
⇒ 删 `_cjk_to_int`，两处共用 `_cjk_single_to_int`（只认单字）。
红证据 `_bmad-output/审查/evidence-maintb-r3/b-prefix-red-repro.txt`。

### R3 第二刀：提取面（车道自查 1 BLOCKER + 4 HIGH，**存量**，第一刀没关上）

第一刀之后，车道用 5 个独立镜头做对抗自查，收敛到同一根因并实测复现：

> `- 本板共有九十八万**五**个子节点。【实测】`（Markdown 粗体，**渲染出来就是
> 「本板共有九十八万五个子节点」**）→ **rc=0 / VERIFY PASS / 零诊断**。
> 机制：提取式只有右侧量词前瞻，数串在 `**` 处断开，匹配重锚到尾片 `五`，
> `_cjk_single_to_int("五")==5` ∈ pool ⇒ 放行。ASCII 侧同形：`980 005个` 只查
> 到 `005`；`98765**4**个` 只查到 `4`。

⚠️ 归因如实：该性质在 `c754b043` 上**同样存在**（`git show` 重放实证），
**不是 R3 引入的回归**；但 R3 的门与 docstring 宣称「多字中文数词一律
fail-closed」，被一个 `**` 击穿 = **声明比证据宽**，故必须闭合。

⇒ 数串**跨连接字符整体抓取**，剥掉连接字符后再交判据：
- `_D2_NOISE_ONE`(:1355) / `_INVISIBLE_ONE`(:1366) / `_D2_JOIN_ONE`(:1367)
- `_join_free()`(:1371) —— 还原读者**看到**的那个数
- `_D2_COUNT_RE`(:1388) ASCII 侧同样跨连接字符
- `_CJK_NUM_RUN_PAT`(:1508) / `_CJK_NUM_RUN_RE`(:1509)

### 修复过程中车道自己踩出的洞（已闭合，请一并复核）

行级「前导零归一化」与「跨连接字符抓取」相冲：`本板共有1 000个子节点`
（渲染 = 1000，SI 千分位）先被剥成 `1 0`，再拼成 `10` 落进池内 ⇒ 放行。
⇒ 删除行级剥零（`int("000123")` 本就按十进制解析），归一化改由 `int(tok)` 承担。

### 车道明确**未**闭合并如实登记的残余（请判断登记是否诚实、是否有被低估的）

- 连接集是**封闭表**。表外字符仍能切断数串：`九十八万x五个` / `九十八万、五个` /
  `[[目标|]]` 空别名残留的 `|]]`。车道判词：这些断点**渲染后可见**，读者不会读成
  一个连续的数；表外的**不可见**载体（如超长 HTML 注释 >22 字符）是真残余。
- D2 的适用口径是「数字**紧邻**中文量词」的计数形态。`本板共有节点九十八万，
  其中种子五个。` 中的 `九十八万` 无量词 ⇒ 不进检查面（ASCII 同形同样不进）。
  这是 `_verify_prose_counts` docstring 已声明的边界，本卡不改。
- 中文数词表封闭在 17 字：大写/金融数字（壹貳參…）、廿/卅/仨/俩 不在提取面内。
- `recap_scan.py:1311/1319` 的⑦⑧允许式里另有**两份手抄**的中文数词字符类字面量，
  未随 `_CJK_NUM_CHARS` 机械派生（当前字符集相同，将来会漂移）。
- R3 收紧带来的**新误伤**：`本板共有一两个/三五个/十来个子节点` 现在硬 FAIL
  （旧实现按 `_cjk_to_int` 得 2/5/10，多在池内而放行）。按卡文 §3 默认裁决
  「多字、非法或无法确定语法的中文数词一律 fail-closed」执行，代价已登记。

## 你的复核动作

1. **读实现**（`canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py`）：
   - 连接语义：`:1355-1383`（`_D2_NOISE_ONE` / `_INVISIBLE_ONE` / `_D2_JOIN_ONE`
     / `_join_free`）与 `:1388-1391`（`_D2_COUNT_RE`）；
   - 判据与提取面：`:1481-1536`（`_CJK_NUM` / `_CJK_UNIT` / `_CJK_NUM_CHARS` /
     `_CJK_NUM_RUN_PAT` / `_cjk_single_to_int` **实现体**）；
   - D2 消费点：`:1650-1680`（CJK finditer + ASCII finditer + 前导零口径注释）；
   - fallback 消费点：`:1915-1935`。
   重点问：**还有没有别的路径能让"进池比对的值"≠"读者看到的数"**？
   连接集/量词表/数词表三张封闭表的边界，车道登记得诚实吗？有没有被低估的？
   possessive `*+` 有没有改变匹配语义（而不只是性能）？
2. **读测试**（`backend/tests/regression/test_recap_scan_signals.py`）：
   `:3124` 判据契约（注意：期望值已改为**独立写死**，因为原版
   `for ch, want in _CJK_NUM.items()` 是自抄期望、把映射改成 7 也全绿）、
   `:3184` fallback 合成 scan 单元门、`:3216` 池碰撞 CLI 门、
   `:3251` D2 多字 CLI 门、`:3288` **切断矩阵 CLI 门（本轮新增，含放行面）**、
   `:3364` D2 合成 scan 单元门，以及既有 `:3088`。
   重点问：有无空洞断言（不改实现也恒真）？有无比实现宽的措辞？
   `assert "九十八万五" in r.stdout` 这类"诊断还原完整数串"的断言够不够强？
3. **跑裁判 1**：`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest
   tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`
   （开工基线 249 → 现 **255**，新增 6 门）。
4. **跑裁判 2**：`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python
   tests/regression/recap_domain_negverify.py`（10 既有 + R3 新增
   survivor-11/12/13/14 共 **14** 条，须全部如期变红）。
   重点问：survivor-13（数串不再跨连接字符）与 survivor-14（`_join_free` 变恒等）
   是否**真的**是该性质的全部防线，还是被别处纵深兜住而误判承重？

## 输出格式

- **第一行**：「BLOCKER/HIGH 清零：是/否（就 C 面而言）」。
- 逐项 ✅/⚠️/❌ + `file:line` 判词；新问题按 severity 列出并标注「本卡引入 /
  存量未闭合」。
- 明确写出：本报告绑定的 commit（请自行 `git rev-parse HEAD`，工作树应为 clean），
  与你实际跑出的两条裁判命令结果。
- 报告一次给出；先写正文再补过程。
