# CARD-G4-13 r14 独立复核（只读 · 绑 `12d61f9a`，父 `fe8952de`）

**绑定/方法**：HEAD=`12d61f9a`，工作树两源文件与该 commit 逐字一致（`git diff` 空、porcelain 干净）；未跟踪仅任务前已存在的 r14 review/prompt 两文件，我未改任何文件。r13（`git show fe8952de:` 载入）与 r14 两版 `gold_set_manifest_tool.py` **同进程**、同一批 fixture 直调 `verify_gold_set_file()`；runner 侧只调真纯函数（`norm_text`/`grade_of`，无 HTTP/无库/无落盘）；四真金集走真 verify + 独立 `shasum`；12 判分函数对 `9c4e7e82` 独立 AST 复算；83 条×10 键独立重算。承重门沙箱外实跑一次（`-B -p no:cacheprovider`，跑后 `git status` 复核仓库零写入）。未连 7691/7687/8011，未跑任何 runner（含 shadow）。

## ① 逐条复算（r13 源码 vs r14 源码，同 fixture）

| 项 | 结果 | 判定 |
|---|---|---|
| LOW-1 `_grade_ok` 名实 | docstring/测试串已同步；全表：`3/0/2.0/"2"` 两版 T；`"２"/"+5"/" 5 "` r13 F→r14 T；`11/"11"/"2000"/"²"/nan/2.5/bool` 两版 F | **真关闭**（函数/测试面） |
| LOW-2 契约过严 | `contains:5`、缺 `max_in_top_k`、`grade` int() 串均 r13 F→r14 T；正向对照在同 fixture 下 r13=False→r14=True（真 True） | **真关闭**；残余见 **LOW-1（falsy contains）** |
| LOW-3 空白 id | `""/" "/"\t"/"\u00a0"` r13 T→r14 F（group_id、vault_id 各 4 形态）；`null`/缺省仍 T；`num5` 两版 F | **真关闭** |
| LOW-4 内部键消息 | r13 文案「…（环境/输入错）」→r14「…（空表会让该门恒空；str 会被逐字符迭代）」，contamination/forbidden 两处实测 | **真关闭** |
| LOW-5 红运行注记 | `r13-gate-green-…161522` 末尾已加「中间态红运行…以同 glob 最新 80 passed 为准」（同 glob `161539` 确为 80 绿） | **真关闭** |

## ②③ 放宽后的新 fail-open / 新「守卫 T 但 runner 失配」路径

- **LOW-1（本轮唯一新 fail-open）**：`_contains_ok` 接受 falsy 标量并放行——`backend/scripts/gold_set_manifest_tool.py:403-407`（`str(0)="0"` 非空白⇒T）、`:546` 使用点；但 vault runner 两处都是**先判真值再 `str()`**（`run_vault_retrieval_regression.py:132`、`:280`），`0/0.0` 短路**静默跳过 contains 检查**。真函数复算：`grade_of(snippet 无"0", [{file:"f",contains:0,grade:5}])→5`，而 `contains:"0"`→`2`（应有的 min(grade,2) 封顶丢失）。复现：fixture 写 `contains: 0`（无引号）→ verify=True；同条目带引号则 runner 行为不同。r13 会拒该输入（本卡 LOW-2 的放宽只应覆盖真值标量），方向为 fail-open（仅 nDCG 面、幅度有界；现存金集 8 处 contains 全带引号，含两处 `"0"`，无现状影响）。附：`contains: .nan` 也 T，runner 按字面 `"nan"` 确定性匹配，非静默丢弃但意图可疑。
- **LOW-2（名实残留，新引入）**：`tool:553` 报错文案仍写「file/contains 须非空 str、grade 须 0..10」，而 `:546` 已接受非 str 标量——与 r13 LOW-1 同一缺陷类别，换到了消息面。复现：对任一被拒的 vault 条目看 detail 文案与 `_contains_ok(5)=True` 自相矛盾。
- **grade 全角串语义**：与 runner `int()` 真实接受面一致（`"２"/"+5"/" 5 "/"1_0"/"٣"/"-0"/"+10"` 均 int() 可解析；`"²"/"＋5"` 双方均拒——后者 runner 侧会经 `:505-507` 兜底成 rc=2，不会落 rc=1）。**max_in_top_k 缺省=0 确为 runner 真行为**（`:303 int(nh.get("max_in_top_k", 0))`，零容忍=最严，非 fail-open）。
- **除 LOW-1 外，未发现新的「守卫 T→runner rc=1/崩溃/fail-open」路径**（新接受的标量均 JSON 可序列化、int()/str() 可消费）。
- **四真金集仍全 T 无误拒**：真 verify rc=0（75/28/2/0），四 sha 独立重算与 manifest 及 `r14-shas` 证据逐字同。

## ④ 测试判别力与数字自洽

- **未发现空转**：新正向对照 fixture 在 r13 源码上为 False（detail 点名 `expect_hit 形态不对`）⇒ 断言必红；`_grade_ok` 新 assert（`"２"/"+5"/" 5 "`）在 r13 亦必红。改动无删断言（diff 仅 +）。
- **gate 81**：我沙箱外复跑 `test_gold_set_manifest_g413.py`=collected 81 / **81 passed**（2.28s），与 `r14-gate-green-…163010.txt` 一致；目录级 1994 自洽：r13 collected 2000→r14 2001、passed 1993→1994、`1994+6+1=2001`、FAILED 行 0；+1 与 gate +1 同源（该 commit 只动此一个测试文件）。
- **immutability 独立复算**：12 函数 vs `9c4e7e82` AST 全 `same=True`；83 条×10 冻结键 diffs=0——与 `r14-immutability` 逐条一致（明细可见性已达标）。

## ⑤ UAT §二十一 / §21.3 诚实性

- §21.1 五行与代码实测一一对应（唯 LOW-2 行未披露 falsy 标量缺口，见 LOW-1）；§21.2 各计数我复现了 gate 81 / named 47（与 r11–r13 持平）/ immutability / verify / shas / 目录 1994；§21.3 残余可溯源到本单既有登记（`UAT:646-647`、`:628-629`，LOW-4=runner 报表层、LOW-5=确定性重放），**非 overclaim**（注意其 LOW-4/5 编号是 UAT 自己的登记表，与 r13 复核对同编号的用语不同，易混读但不失实）；§21.4 三条「未证明」如实。
- **LOW-3（证据卫生，r13 LOW-5 同类轻量复发）**：`r14-gate-green-*` glob 含两个文件——`…162952.txt`（尾行 **80 passed**，新测试尚未加入的中间态，未注记）与 `…163010.txt`（81 passed）；`UAT:719` 仅引「81 passed」。两文件皆绿、非误导红绿，但同 glob 计数不一致且中间态无注记。复现：`ls r14-gate-green-* && tail -1` 两个不同计数。

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

**未被拦下的输入**：`contains: 0/0.0`（LOW-1，守卫 T 但 runner 静默跳过）；`contains: .nan`（T，字面 "nan" 匹配）；`vault_id: null`（vault 类守卫 T，runner `str(None)→"None"→sanitize→"none"`，即查 `vault:none` 而非默认——**旧口径非本轮新增**，预期全零落入 rc=2 哨兵 `runner:508-516`，非静默通过）；`max_in_top_k ∈ [10,10⁶]` 与 10⁴⁰⁰ 在 runner 内 top10 等价（r12 已明示的注解自由度）。
**对照输入**：四真金集真 verify rc=0 + sha 逐字；`contains:"0"`（现存金集形态）↔ runner 仍封顶 min(g,2)；`contains:5`、缺 `max_in_top_k`、`"２"/"+5"/" 5 "` 全 T 且 runner int()/str() 实测同语义；`group_id/vault_id` 的 null/缺省/非空串 T、空白族 F；r13 侧同 fixture 全量对照（上表）。
**负控输入**：新正向对照在 r13 源码=False（判别力成立）；falsy-contains fixture r13=False→r14=True（本轮打开方向可复现）；runner 真函数 `grade_of` 对 `contains=0` 给声明 grade、对 `"0"` 给 min(grade,2)（语义分叉实证，非纸面推断）。
**门未覆盖的路径**：`group_id/vault_id` 空白拒收**无专属 case**（将来改回 `isinstance` 检查测试仍绿）；`contains` 的 falsy/nan 无 case；`grade` 仅覆盖全角/正号/空白三例（`"1_0"/"٣"/"+10"` 无 case）；`vault_id:null→none` 语义无 case；目录级 1994 未重跑（artifact + 算术核对，同 r13 先例）。

## 本轮总评

- **BLOCKER**：未发现
- **HIGH**：未发现
- **MEDIUM**：未发现
- **LOW-1**：`_contains_ok` 放行 falsy 标量 → runner 静默跳过 contains 检查（`tool:403-407,546` × `runner:132,280`；复现：`contains: 0` fixture verify=True，`grade_of` 返回声明 grade）
- **LOW-2**：expect_hit 报错文案「contains 须非空 str」与实际接收面不符（`tool:553`；复现：`_contains_ok(5)`=True vs 文案）
- **LOW-3**：`r14-gate-green-*` glob 内 80 passed 中间态未注记，UAT `:719` 只引 81（复现：两文件尾行 80/81 不一致）

**本轮总评：B=0 / H=0 / M=0 / L=3** —— r13 的 5 条 LOW 全部真关闭（名实/契约/空白 id/消息理由/证据注记逐条实测），四真金集零误拒、gate 81 与目录 1994 自洽、immutability 独立复算全同；新残三低：falsy `contains` 的窄口径 fail-open、报错文案名实、证据计数卫生。
