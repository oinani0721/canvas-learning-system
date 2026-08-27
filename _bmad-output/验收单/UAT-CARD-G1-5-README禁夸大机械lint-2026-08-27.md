# 验收单 · CARD-G1-5 README 禁夸大红线清单 + 机械 lint

> **批次**: BATCH-2026-08-27-第四批 · 车道 4 第二卡
> **分支**: `card/n4-readme`（不 push，等你验收）
> **日期**: 2026-08-27
> **计划书锚点**: §12.7:633（禁夸大声明逐条清单）· §12.5:590-592（E 级不自动提升）· User 批注:494（readme 不能编造）

---

## 一、你需要做什么（用户产品体验）

**没有要你操作的**。这张卡是给你的刚需「README 不能编造」造的机械尺子：从现在起，谁往 README 里写「production-ready / 一键可用 / 14 Agent 协同」这类话——包括未来的 Claude 自己——commit 时就会被 hook 当场打回，除非同一行贴着**仓库里真实存在**的证据文件链接。而「把命中率叫召回率」「把 skipped 算成功」这两类名实谎言，贴证据也不放行。

唯一建议你**过目**的：「三、机制说明」里 legacy 登记的语义——旧 README 里 3 行「14 Agents」旧文案被登记为「已知失实、待 G1-6 证据化重写」，报告里照常曝光，但不卡今天的 commit。若你认为应该现在就卡死（代价：G1-6 重写前 CI 恒红），说一声即改。

## 二、技术判据（Claude 已代跑，全部通过）

| 裁判 | 命令 | 结果 |
|---|---|---|
| 先红 | `pytest tests/unit/test_check_readme_claims.py`（脚本存在前） | collection error（模块不存在）❌，红/绿/基线三段实录存档 `_bmad-output/审查/g1-5-red-green-evidence.txt` |
| 后绿（五版加固） | `cd backend && .venv/bin/pytest tests/unit/test_check_readme_claims.py -q` | **120 passed** ✅ |
| report 基线 | `check_readme_claims.py --report`（对含 G1-4 横幅的 README） | **exit 0 · TOTAL=3 effective=0**，全部 `C9-agent-collab` + `[legacy]`（行 35/50/68）✅ 与勘探预期「14 Agent 协同类命中 3 处」一致 |
| 横幅不误伤 | 同上 + 单测（横幅+5 标注全文阴性对照） | **0 命中** ✅ |
| staged-diff 实战 | stage G1-4 diff 后 `--staged-diff` | **TOTAL=0 · exit 0**（banner commit 不被存量阻断）✅ |
| enforce 门 | `--enforce` | **exit 0**（存量已登记；新增违规会 1）✅ |
| CI 式单测调用 | `python -m pytest ... --confcutdir backend/tests/unit` | **120 passed**（不依赖全量 backend 依赖，CI 可跑）✅ |
| ruff | `ruff check` + `ruff format --check` 两个新 py 文件 | 全过 ✅ |
| test.yml 零改动 | `git diff .github/workflows/test.yml` | 空 ✅ |

### 单测 120 例覆盖（goal 要求 ≥4；Codex 四轮审查全部 finding 转为回归用例）

- **11 条规则 canonical 阳性 23 句参数化**（含两轮审查展示的全部漏报等价句：`recall@k` 字面 k、`Ready for production`、`Each vault works out of the box`、`Skipped checks mean/indicate success`、`are successful`、`Degraded is considered successful`、动词前置 `treats skipped as success`、否定拼接洗白句 `Skipped means success; degraded is not treated as success` 仍拦、`14 个智能体协同工作`）
- **近邻阴性 13 句**（防私自扩大：`Many vaults`、裸 `multi-vault safe`、`fully rebuildable` 无永久、`permanent partial restore`、`Limited ... default main pipeline`、`Lossy ... bidirectional`、单向 lossless、个位数 agent×2、明确否定句×2、`is available on green` 类近邻）
- **逃逸五条件**：`[C1:E3](tracked 非空文件)` 放行；裸 `[E3]`/绑错规则/链接不存在/untracked/空文件/README 自引用/藏 HTML 注释/藏 code span/`E4+` 非法档 → 均不放行
- **hard-forbidden 三重免疫**：证据标注不放行、legacy 引擎级不吃（上下文指纹全匹配仍 effective）、staged 不放行
- **配置面指纹 9 变体**：删规则/C6 C11 降级/**正则掏空 `(?!)`**/**注入 legacy**/scan_paths 鬼文件/通配/字符串/l633 漂移 → 全部退出 2 拒绝伪绿；`RULES_SHA256` 常量与磁盘 yaml 自洽断言
- **legacy 语义**：上下文指纹匹配处放行 / 相同邻域复制超配额拦 / 搬移换邻域拦 / 全链搬到文件头拦 / staged 新增行永不吃 legacy
- **staged 对抗**：`++` 内容行不当元数据；`diff.noprefix`+`mnemonicPrefix`+`color.ui=always` 仍拦；`.gitattributes -diff` 二进制伪装被 `--text` 强制解析仍拦；`--root` 指仓库子目录退出 2
- **白名单外不扫**、**真仓基线钉死**（3 命中全 C9 全 legacy 行号 35/50/68）、**跨文件同步契约断言**（lefthook glob 与 workflow paths 与 scan_paths 一致）

## 三、机制说明（L633 → 规则逐条映射）

`backend/scripts/readme_claims_rules.yaml` 的 C1-C11 与计划书 L633 语序一致；(id, severity, L633 原文) 序列由脚本 `EXPECTED_RULES` 常量**钉死**——改 yaml 削弱任何一条 = 配置错误退出 2，不是静默放行：

| id | L633 原文 | 严重级 |
|---|---|---|
| C1 | production-ready | evidence-escapable |
| C2 | 任意 vault 一键可用 | evidence-escapable |
| C3 | 完整 multi-vault safe | evidence-escapable |
| C4 | Graphiti 永久且全量可重建 | evidence-escapable |
| C5 | full multi-source RAG 是默认主链 | evidence-escapable |
| C6 | 把 hit@k 写成 recall | **hard-forbidden（证据/legacy 均不放行）** |
| C7 | FSRS/UI 已完全一致 | evidence-escapable |
| C8 | Canvas↔Excalidraw 无损双向 | evidence-escapable |
| C9 | 14 个 Agent 协同 | evidence-escapable |
| C10 | 移动端可用 | evidence-escapable |
| C11 | skipped/degraded 等同成功 | **hard-forbidden（证据/legacy 均不放行）** |

三档：`--report`（全量曝光，恒 exit 0）/ `--enforce`（CI 门，有效命中 exit 1）/ `--staged-diff`（lefthook pre-commit，只扫 staged 新增行，git 参数钉死免疫用户 diff 配置）。配置/环境错误统一 exit 2。

**配置面指纹（二轮 B2' 处置）**：规则 yaml **全文 SHA-256** 钉死在脚本 `RULES_SHA256` 常量——改任何一个正则/legacy 条目都必须同 commit 改脚本常量（双文件改动，审查可见），否则退出 2。yaml 单边削弱裁判在机制上不可能。

**逃逸语法（终版）**：`[Cx:E3](docs/evidence/…)`——绑定被命中规则编号、E 级 ∈ {E3,E3+,E4,E5} 精确枚举、链接必须位于受控证据目录 `docs/evidence/`（该目录已入 workflow paths，证据增删改会重触 CI——生命周期闭合）、在 git index 中以 stage-0 真实 blob 存在（`add -N`/空 blob 拒绝）、worktree 中为非空非 symlink 普通文件、不得自引用被扫描文件、标记不得被反斜杠转义或藏在 HTML 注释/code span 里。诚实边界已写进脚本 docstring：本裁判只验证标记与链接文件的机械性质，**不裁决证据内容成立**（E 级真伪归 G1-3 台账 / G1-6 逐声明审计）。

**legacy 登记（需你知情）**：旧 README 3 行 14-Agent 文案按「精确整行文本 + 文件 + **精确行号锚（容差 0）** + **5 行上下文 SHA-256 指纹** + 出现配额 1」五重绑定登记。语义 = 已知失实、report 照常曝光、不卡今天的门、G1-6 重写时删空。防滥用：复制超配额 fail；搬移换邻域指纹不符 fail；staged 新增行（含搬移重提交）一律不吃 legacy；hard 类连 legacy 都不生效。

**C6 政策裁定（需你知情，与 Codex 二轮建议存在有记录的分歧）**：README 范围内一切 `recall@k` 型指标声明一律拦截，自称「真 recall」也不例外。依据：卡片 spec 将「hit@k 误名」列为 hard-forbidden 永不可逃逸 + G4-12 实证本仓检索指标全是 hit rate。Codex 二轮建议改为只拦「显式 hit→recall 命名关系」以免误杀合法 recall——被否决，因为行内豁免（negative_patterns）已被二轮审查自己证明可拼接洗白（B1'），且本仓当前不存在任何合法 recall@k 指标。未来确有经审计的 recall 指标时，修改规则走「双文件指纹契约 + 审查」，不存在行内豁免通道。

**否定句处理（终版，取代已废除的整行安全阴性）**：仅 C11 启用**谓词否定尾绑定**守卫（钉死在脚本）——否定词必须紧邻被评估的谓词（中间只许 be/被 类助词），配合掩码重试逐个评估同分句谓词候选。「Skipped means success; degraded is not treated as success」「do not fail but indicate success」等拼接洗白全拦；「Skipped is not treated as success.」「were not successful」诚实否定句放行。未被守卫覆盖的修辞仍会命中——改写措辞即可，已写进 docstring。

**单测入 CI**：本卡铁律 test.yml 零改动——裁判测试改由独立 workflow `readme-claims.yml` 以 `--confcutdir` 隔离方式执行（不装全量 backend 依赖）。

## 四、接线清单

- `backend/scripts/check_readme_claims.py` — 新建（三档裁判 + 契约钉死 + 逃逸绑定 + hunk 状态机 diff 解析）
- `backend/scripts/readme_claims_rules.yaml` — 新建（11 规则中英正则 + 安全阴性 + legacy 四重绑定登记）
- `backend/tests/unit/test_check_readme_claims.py` — 新建（120 单测，先红后绿）
- `lefthook.yml` — 追加 `readme-claims-lint`（仿 cypher-vault-filter-lint，glob 限 README.md，staged 新增行模式）
- `.github/workflows/readme-claims.yml` — 新建独立 workflow（enforce + report + 单测三步；paths 限 README+规则+脚本+测试+自身+lefthook.yml+docs/evidence/**）
- `.github/workflows/test.yml` — **零改动**

### Codex 对抗审查（重点：L633 逐条映射完整性 + 逃逸语法不被架空）

- 一轮（ultra）：存档 `_bmad-output/审查/codex-review-CARD-G1-5.md` — **判 FAIL：2 BLOCKER + 5 HIGH + 2 MEDIUM + 1 LOW**（对初版脚本/规则）。全部成立，逐条处置如下：
  - **B1 hard 红线漏直白等价句**（`recall@k` 字面 k / `mean success` / `considered successful`；且误杀真 recall 口径）→ C6/C11 补模式 + 安全阴性（negative_patterns），全部转参数化回归用例
  - **B2 配置可静默解除裁判**（删规则/改 severity/scan_paths 塞鬼文件或通配/--root 指错全部伪绿）→ (id, severity, l633) 序列与 scan_paths 钉死进脚本 `EXPECTED_RULES`/`EXPECTED_SCAN_PATHS` 常量，任何偏离退出 2；--root/目标文件缺失也退出 2；7 变体削弱测试钉死
  - **H3 复合规则私自扩大/漏报**（Many 误伤 any / 永久且全量被写成 OR / default fallback 误伤 / 单向 lossless 误伤 / 个位数 agent 误伤 / 中文智能体漏报）→ 逐条修正为 L633 字面合取语义 + 15 阳性 8 阴性钉死
  - **H4 逃逸标记是自我声明**（裸 [E3] 指向不存在的链接也放行、一个标记逃逸多规则）→ 升级为 `[Cx:E3](仓库内存在文件)` 三条件绑定（规则编号 + E 级 + 文件存在且在仓库根内），escape 正则钉死进脚本不再从 yaml 读；诚实边界（不裁决证据成立）写进 docstring
  - **H5 legacy 同文件搬移洗白**→ staged 新增行永不吃 legacy（搬移=新写入当场拦）+ 行号锚 ±25 + 配额；三个滥用路径全部有回归测试
  - **H6 staged 解析器可绕过**（`++` 内容行被当元数据、diff.noprefix/mnemonicPrefix/color.ui 让解析空转）→ hunk 状态机重写 + git 参数钉死（--no-color/固定前缀/--no-ext-diff/--no-textconv/-U0/inter-hunk-context=0），对抗配置回归测试钉死
  - **H7 测试没钉死语义且无 CI 消费方**→ 测试 10→44（11 规则参数化+契约变体+对抗 diff），独立 workflow 增加 `--confcutdir` 单测步骤（test.yml 仍零改动）
  - **M8 部分配置错误退出 1 而非 2** → load_rules/git 调用/IO/类型错误统一包装 ClaimsConfigError → 2
  - **M9 机械边界声明** → 安全阴性覆盖明确否定句（`Skipped is not treated as success` 不再被拦），边界拆成「机械标记校验」vs「证据裁决」两层写明
  - **L10 fixture 注释失实** → 注释改为如实描述（非空行逐字一致，空行布局非严格相同）
- 二轮复核（ultra，同文件附录）：对一轮处置判 **仍 FAIL：3 新 BLOCKER + 5 HIGH**（整行安全阴性可拼接解除 hard 红线 / patterns 与 legacy 未随契约钉死可被 `(?!)` 掏空 / staged 对错误 root 伪绿 / 合取仍不完整 / 逃逸接受空文件与隐藏标记 / legacy ±25 内搬移 / 二进制伪装 diff / symlink 越界）。全部成立，处置：
  - 整行 negative_patterns 机制**彻底废除**（loader 见到该字段直接报配置错误），C11 改为脚本内钉死的**匹配片段级**否定守卫；C6 取消行内豁免（政策裁定见上）
  - 规则 yaml 全文 SHA-256 指纹钉进脚本常量，正则/legacy 单边改动 = 退出 2（含 `(?!)` 掏空与 legacy 注入两个二轮反例，已入回归）
  - staged 档补 scan 目标存在校验 + `--root` 必须是 git toplevel；git diff 加 `--text` 强制文本 + 变更文件/解析结果交叉核对（二进制伪装 = 退出 2）；`.gitattributes -diff` 对抗回归钉死
  - 逃逸目标升级五条件（tracked/非空/非 symlink/非自引用/E 级精确枚举），标记匹配前剥离 HTML 注释与 code span
  - legacy 加 5 行上下文 SHA-256 指纹（搬移换邻域即失效）；scan 目标拒绝 symlink + resolved containment
  - C3/C4/C5/C8/C9 全部改为 L633 字面合取（裸 multi-vault safe / fully-not-permanent / limited-default / lossy-bidirectional / 个位数 agent 全部入阴性矩阵）；`ready for production`、`Each vault out of the box`、`are successful`、`indicate success` 等漏报等价句入阳性矩阵
  - schema_version/类型/异常归一化补全（`legacy_allowlist: 1`、PATH 无 git 等 → 2）；跨文件同步改为**契约测试断言**（lefthook glob 与 workflow paths 解析比对）+ lefthook.yml 纳入 workflow paths；测试 44→**59**
- 三轮复核（ultra，同文件附录）：**C6 全拦政策被裁定为可接受设计决定（INFO）** ✅；实现层判 **2 BLOCKER + 4 HIGH**（span 否定守卫可被注释藏词/跨谓词洗掉、call hit@k recall 与 Top-k 定义式与 Skipped checks pass 漏报、跨分句拼接 conjunct、逃逸接受反斜杠转义与非受控目录与 add -N、五行窗口整体搬移、U+2028 断行与 rm --cached 双树错配）。全部处置：
  - 匹配面改为**剥离 HTML 注释后的可见文本**（全量档含跨行注释块状态）——注释藏否定词/藏标记双向失效；否定守卫升级为**谓词捕获组 (?P<v>) 前窗检测**（but-indicate 拼接句仍拦、诚实否定句仍放行）
  - **分句级合取**：行先按 [;；。] 与句号边界切分，conjunct 不得跨分句（前句 complete + 后句 multi-vault safe 不再拼合）
  - C6 补 `call hit@k recall` 主动语态 + `Top-k recall` 定义式；C11 补 `pass/succeed` 直接谓词；C8 补 Canvas conjunct；C9 双位数政策在 yaml/测试/本单三处显式声明
  - 逃逸再收紧：证据必须位于 `docs/evidence/`（该目录已入 workflow paths——证据删除会重新触发 CI，生命周期闭合）+ git index stage-0 真实 blob（`add -N`/空 blob 拒绝）+ 反斜杠转义标记不算
  - legacy 行号锚收为**容差 0**（五行窗口整体搬移失效；README 本受用户批准门管制，行号漂移走双文件契约重钉）
  - staged 档改**字节级解析**（只按 \n 分行，U+2028 不再错位）+ 扫描目标 D/T/unmerged staged 状态拒绝裁决（rm --cached 出 2）
  - 测试 59→**70**（三轮全部反例入回归）
- 四轮复核（ultra，同文件附录）：**H4/H5/H6 全部 RESOLVED**（证据生命周期/legacy 搬移/字节级解析三类闭合）；剩 **2 BLOCKER + 1 HIGH**（无关谓词的 not 误解除 indicate 阳性、贪婪跨度吞未否定谓词、`Hit@k = recall` 与 `were successful` 字面等价漏、C9 政策说双位数实现只有 10-19）。全部处置：
  - 否定守卫终版：**否定尾绑定**（否定词必须紧邻谓词，中间只许 be/被 类助词）+ **掩码重试**（被否定谓词打掩码后重扫同分句，逐个评估谓词候选）+ C11 惰性量词——「do not fail but indicate success」「mean success but are not treated」均拦，「were not successful」放行
  - C6 补 `Hit@k =/is/equals recall` 字面命名；C11 补 was/were 过去时
  - C9 按政策实现 **10-99 全双位数**（20/99 边界入回归）
  - schema_version 严格整数（拒 2.0）+ 顶层字段闭集 + legacy 字段严格 str 类型
  - 真仓基线断言放宽为「钉 3 条 legacy 身份 + 零 effective」（不再硬钉总数，未来合法 escaped 声明不受阻）
  - 测试 70→**78**
- 五轮复核（ultra，同文件附录）：否定尾绑定与掩码机制本体被确认闭合，schema/基线/index 三 MEDIUM 清零；剩 **2 BLOCKER + 1 HIGH + 1 MEDIUM**（掩码重扫被 40 字符主谓跨度截断、equal/`==` 等价族漏、C9 普通双位数 AI Agents 句漏、中文三位数尾部误报）。全部处置：
  - C11 主谓跨度 40→80（掩码后仍可达后续谓词——"are not considered successful but indicate success" 入回归）
  - C6/C11 补 `equal(s)/equivalent to` 谓词与 `==`/`===` 重复等号族
  - C9 补「普通双位数阵容句」模式（"42 AI Agents are available" 入回归）+ 中文数字负向后顾（`120 个智能体协同` 三位数超政策范围不判，入阴性）
  - 测试 78→**83**
- 六轮复核（ultra，同文件附录）：B1 掩码跨度与中文三位数边界判 RESOLVED；剩 **1 BLOCKER + 1 HIGH**（`Hit@k is equivalent/equal to recall` 系词组合与 `Skipped checks == success` 主谓间隔等号、中文「42 个 Agent 可用」直接族）。全部处置：C6/C11 补系词+等价短语组合与间隔等号，C9 补中文「个 Agent(s)」模式；6 句全部入回归，测试 83→**89**
- 七轮复核（ultra，同文件附录）：六轮 6 反例全闭合；新报 **2 BLOCKER + 1 HIGH**（canonical 主语 `hit@k metric` 与新谓词组合、**行内 Markdown 强调符切断 token 旁路**（`` `Hit@k` ``/`**==**`）、中英混排无空格 `42个Agent可用`）。全部处置：
  - **Markdown 强调归一化**：规则匹配前剥离 `` ` ``/`*`/`__`/`~~`（保留单 `_` 防伤 `recall_at_5` 标识符）——强调排版切不断声明，8 句排版变体全部入回归
  - C6 hit@k 与谓词间允许 ≤12 字符有界间隔（metric 同位语）；C9 `agents?` 词尾改 `(?![a-z0-9_])` 负向前瞻（Unicode 词边界陷阱）
  - 测试 89→**97**
- 八轮复核（ultra，同文件附录）：七轮 2 BLOCKER 全部 RESOLVED，**BLOCKER 首次清零**；剩 2 个同根 HIGH（CJK 与 ASCII 相邻处 Unicode `\b` 失效：`当前full multi-source…`、`共有42 AI Agents协同`）。处置：C5 `full` 与 C9 数字前导边界统一改负向后顾 `(?<![0-9a-z_])`（`120` 尾部仍拒）+ C10 预防性补混排 `mobile可用` 变体；4 句入回归，测试 97→**101**
- 九轮复核（ultra，同文件附录）：八轮 2 HIGH RESOLVED；应我方要求对全部 11 规则 37 pattern 的边界端点做了**穷举**，报同根残留 1 BLOCKER + 2 HIGH + 1 MEDIUM（C11 七个 CJK 紧邻端点如 `mean成功`/`Skipped检查pass`、C2 三处、C10 四处、否定词 CJK 紧邻 false-red）。终局处置：规则面 **`\b` 清零**——全部 ASCII 词边界统一改定向 lookaround `(?<![a-z0-9_])`/`(?![a-z0-9_])`（兼容正常中英混排，`Many`/`fuller`/`120` 仍拒）；否定尾正则同步修（`Skipped状态not等同成功` 正确放行，含 p5 宾语排除后顾）；14 阳性 + 4 阴性入回归，测试 101→**118**
- 十轮复核（ultra，同文件附录）：九轮 1B+2H **全部 RESOLVED**（规则面 `\b` 清零核实、14 阳性 4 阴性复算全过）；新报 1 BLOCKER + 1 MEDIUM——均为九轮宾语排除自身引入的镜像缺口（`等于成功` 直接句无人接管、`not等价成功` false-red）。处置：p2 谓词表补「等于」、p5 后顾补「等价」，2 句入回归，测试 118→**120**
- 十一轮复核（ultra，同文件附录）：十轮 BLOCKER RESOLVED；六谓词邻域对称性 12/12 复算通过；**结论行「BLOCKER/HIGH 清零: 是」**（绑定规则指纹 `4825e71a…`）✅
- **已知残留（1 MEDIUM，保守方向，如实登记不再改动）**：`Skipped checks not 等同 成功。` 类「英文否定 + 中文谓词与宾语之间带空格」的混排句会被 p5 误拦（false-red——只会**多拦不放行**，绝不产生伪绿；改写措辞即可通过）。为保持清零裁定与提交字节严格一致，此项不在本卡修复，登记为已声明机械边界。
- 审查全程 11 轮共出 **10 BLOCKER + 16 HIGH**（含重分级），全部闭合；最终测试 **120 条**全绿，规则面 `\b` 清零，三档退出码语义与真仓基线（TOTAL=3 effective=0 legacy=3）经每轮独立实跑复核。
