# UAT-CARD-G8-2 — 统一 /lint 骨架 + 首批三检查（orphan / raw-derived 混淆 / 投影 freshness）

> 批次 [BATCH-2026-09-01-第八批 / CARD-G8-2] · 车道 card/w9-lint（9af18b27 切）· 2026-09-01
> 锚点: 计划书 §3.7 L189（lint 缺口）+ §G8 L344（统一 /lint）+ 总账 v2 G8-2 档案

---

## ⛔⛔⛔ 终态裁定（先读这一段 · round-12 终版 · 本段为唯一权威入口）

**Codex 审查共 11 轮**（r1 1B+7H → r2-r11 每轮 0-5B / 2-5H 递进，各轮存档 codex-review-CARD-G8-2-round*.md）。
经用户六次授权定向续轮、三轮结构性重构（正则反向引用 → 区间盲区法 → **markdown-it-py token 流**），
round-11 的 3 HIGH 中两项（BEGIN/END 词边界）已修、一项（AUTO 段内 fence 交互）与 H3（同名碰撞）登记为
**构造性深水区口径边界**（详见下方登记表）。

**round-12 终态（当前字节，MANIFEST 绑定 vault_lint.py SHA `c800665c…`）**：
- 裁判 1 = **208 passed**（89 本卡 + G8-1 119 零回归），含 17 组 freshness 同源锁（referee1-pytest-full-round12.txt）
- 变异负验证 **22 个锚位全杀**（21 个唯一 mutant + M22 拆双；transcripts/ 存档；判定 = 指定门 FAILED 行）
- live 取证十三轮 sha `a82e3af0…` 前后逐字相同（rc 随取证时刻 stale/ok 切换 = 结构性窗口实证）
- 禁改门空；MANIFEST 全覆盖（时序：生成于全部证据落定之后）

**登记的构造性前提 / 口径边界**（不修理由 = 真实生成器形态不可达 或 需 orphan 权威口径用户裁决）：
| # | 前提 | 登记理由 |
|---|---|---|
| B1 | AUTO 段内 fence 开合交互（info 反引号 / 容器前缀哨兵 / fence 内 END） | 真实生成器固定四段结构（probe-F 实测 6 板同构）永不产出；段内 fence 标记行/异常已显式记 anomalies 披露 |
| B2 | 同 token 内 code span 真链与转义/实体假链同名碰撞 | mdit text token 无字符级 srcmap，decoded 已消费转义/实体，位置级绑定结构性不可达；orphan 权威口径（mdit 渲染 vs 生产图 vs Obsidian）需用户裁决 |
| B3 | 三连以上反斜杠的奇偶残面 | fail-closed 方向（多报孤儿），人工核真伪 |

**§6.11 live sha 门覆盖面（r11 M3 收窄声明）**：`-not -name '今日复习.*'` 按 basename 排除**任意目录**
下的同名文件（不止 outputs/），且 `-type f` + shasum 不覆盖 symlink 对象——「排除后全树普通文件内容
零写」已证；symlink 替换与深层同名文件不在承诺内。

**最终清零状态以 codex-review-CARD-G8-2-round12.md 末行为准**；合并须主 session 复核 + 用户验收。
历史轮次（r1-r11）的判定与数字为**时点快照**，保留于 §4-A / 附 A/B/C。

---

## 1. 结论

见顶部「终态裁定」——round-12 当前字节：208 passed / 22 锚位全杀 / live 十三轮 sha 一致 / 禁改门空。
完成条件 (a)(b)(c)(d) 达成明细见 §2；审查轮次史与登记项见 §6。

## 2. 完成条件对照

| 条件 | 要求 | 实况 |
|---|---|---|
| (a) | `backend/scripts/vault_lint.py` 单命令 `--vault/--json/--now/--only`，三检查独立函数，退出码 0/2/1，--json 与文本同源 | ✅ 全部落地；**另扩展退出码 3 = 配置/环境错误**（含参数用法错误）；理由与待裁决见 §5① |
| (b) | 先红后绿 fixture 反例 ×3 + 干净全 ok + 退出码一致 + 同源门 + orphan ≥5 类形态 | ✅ 反例 3+；干净 rc=0；orphan 形态判定 10 形态 / 不判定 5 形态（§3 表，19 行） |
| (c) | pytest 全绿（119 不回归 + 同源锁 ≥6）+ --help 门 + live 只读取证 + 禁改门空 | ✅ 208 passed；live 十三轮取证 §4-A；禁改门空 |
| (d) | 变异串行 ≥4，还原逐字节比对，各杀指定门 | ✅ **19 个 mutant 全 KILLED**，判据=指定门 FAILED 行，transcript 存档；M8/M12a/M12b 首跑 SURVIVED 暴露重复定义后已修并全部转 KILLED；M18 首跑 SURVIVED 暴露枚举冗余后已消除结构冗余 |

## 3. orphan 形态表（验收单「不比什么」的数据源）

| 形态 | 判定 | 依据（测试用例） |
|---|---|---|
| `[[x]]` 基本形 | 判定为入链 | `test_orphan_link_forms` |
| `[[x|别名]]` | 判定为入链 | 同上 |
| `[[节点/x]]` 子路径 | 判定为入链 | 同上 |
| `![[x]]` embed | 判定为入链（`!` 在捕获组外） | 同上 |
| `[[x#小节]]` / `[[x#^块]]` | 判定为入链 | 同上 |
| `[[x.md]]`（含 `[[x.MD]]` 大写） | 判定为入链 | 同上 + `test_orphan_uppercase_md_link_and_null_source_board` |
| NFC 文件名 ↔ NFD 存盘 | 判定为入链（归一后匹配） | `test_orphan_nfc_nfd_and_casefold`；live 实测 14/14 全 NFC 存储 |
| 大小写差异（`[[Agent]]` ↔ `agent.md`） | 判定为入链（casefold；Obsidian/APFS 均不敏感） | 同上 |
| 节点正文互链（节点→节点） | 判定为入链 | `test_orphan_node_to_node_body_link_counts` |
| 子目录节点跨链（`d1/A` 链 `[[d2/a]]`） | 判定为入链（对 d2/a；不是 A 的自链） | `test_orphan_subdir_node_crosslink_not_selfchain` |
| 检验白板正文链 | 判定为入链（⚠️ live 零正样本，见 §6） | `test_orphan_exclusions` 的 exam 用例 |
| 围栏 code（```dataviewjs 等） | **不判定**（round-1 HIGH-4 整改） | `test_orphan_ignores_nonsemantic_wikilinks` |
| 行内 code（`` `[[x]]` ``） | **不判定** | 同上 |
| HTML 注释（含跨行） | **不判定** | 同上 |
| AUTO-GENERATED 哨兵段（BEGIN→END 整段含成员列表） | **不判定**（round-1 HIGH-2 整改；live 复算去掉 AUTO 后 3 节点无其他入链） | 同上 |
| 跨行 `[[\nx\n]]` 伪链 | **不判定**（Obsidian wikilink 不跨行） | 同上 |
| 空 `[[]]` / 链向别处 | 不判定 | `test_orphan_link_forms` + `test_orphan_empty_wikilink_literal` |
| frontmatter 里的 wikilink（含**别的文件**的 frontmatter 指向本节点） | **不判定**（有意；判别力用例 `test_orphan_frontmatter_of_other_files_has_no_power`） | `test_orphan_exclusions` + HIGH-5 判别力用例 |
| 自链（**顶层**节点正文 `[[自己]]`） | **不判定**（子目录文件不适用——方向=少误杀入链） | `test_orphan_exclusions` |

## 4-A. 裁判输出存档（技术段）

**⛔ 证据绑定**：以下全部证据生成于**当前字节**（round-7 终版：vault_lint.py sha256
`aa2eca15…`、test_vault_lint.py 见 MANIFEST；全清单含 mutation-transcripts/ 22 份与
test_vault_doc_roles.py，见 `evidence-g82/MANIFEST.txt`）——源码任何字节变更后这些证据自动失效，
须复跑。终版证据 = referee1-pytest-full-round7.txt（190 passed）+ live-lint-round7.json（rc=0，sha
`a82e3af0…` 前后逐字相同）+ mutation-transcripts/（22/22 KILLED）。

- 裁判 1（终版，evidence-g82/referee1-pytest-full-round7.txt，round-7 字节）：
  `PYTHONDONTWRITEBYTECODE=1 caffeinate -i .venv/bin/pytest tests/unit/test_vault_lint.py tests/unit/test_vault_doc_roles.py -q -p no:cacheprovider`
  → **190 passed**（71 本卡 + 119 G8-1 实数，0 failed）。
  freshness 同源锁 = 17 组参数化用例（FRESHNESS_MATRIX，要求 ≥6），每组**活 oracle 比对**：
  同一 fixture 同时喂真实 `review_overview._vault_entry`（spec_from_file_location 直载，
  probe-B 实测 0.95s/557 模块/审计事件 0；包路由 import 实测 29.4s + import 期出站 HTTP，禁用）
  与 `vault_lint._projection_status`，断言 status 逐字相等；另附实测快照锚防 oracle 静默漂移。
  覆盖 4 种机制：DATE_COMPARE / REGEX_REJECT / ASTIMEZONE_RAISE(OverflowError)（h2/h3 唯二触达
  oracle :856 except 的用例）/ SUMMARIZE_TYPE_REJECT（int 20260831 → corrupt，非 stale——
  本卡实现曾在此与 oracle 分叉，已修并对齐）。
- 裁判 2（**三轮**取证，均在安全窗口、三步连续执行）：
  - 前/后 sha（十三轮全同）：`a82e3af0a5a8d8e05511175bf3442773d600b4be2451d59e30254767db748380`
    （**覆盖面收窄声明见 §6.11**：按 basename 排除任意目录同名文件 + symlink 不覆盖，
    命令存 live-sha-command.txt）
  - round-1（05:44）与 round-2（07:06）取证 → **rc=2**（freshness stale——每日 00:00→09:05 的
    结构性窗口）；round-3（09:33，09:05 首推档已过、距下一档 10:05 尚远）→ **rc=0 全 ok**
    （投影已被 launchd 刷新）——三轮 rc 演化本身就是「stale 是结构性现象、09:05 自愈」的实测实证。
  - 各轮 rc 与 JSON summary 一致（round-3：`exit_code:0, ok:3 warn:0 fail:0`）✓
  - findings 逐条核真伪（round-1/2 各 1 条 stale finding，判定见下；round-3 零 finding）：
    | finding | 真伪 |
    |---|---|
    | freshness stale：`generated_at=2026-08-31T09:05:05+08:00` ≠ today 2026-09-01 | **真**。launchd 实测 12 档 Hour 9-20 每小时 :05 刷新——每日 00:00→09:05 之间投影必然是"昨天"，属结构性窗口，09:05 自愈（round-3 实测自愈），非缺陷 |
  - orphan：14 节点 / 0 孤儿（round-2 剥离 AUTO 哨兵段后仍 0——3 个节点改由 source_board 豁免，
    与 Codex live 复算一致）；raw_derived：324 文件 / 175 目录 / 0 条混淆——与 probe-F
    独立普查（另一实现）数字互证。
- 裁判 3：`--help` 列出三检查名 + 退出码 0/2/1/3 语义 + 各检查分级规则（完整输出存 help-full.txt，
  与当前字节 `cmp=0`）。
- 变异（evidence-g82/g82_mutation_negative_controls.sh，串行；transcript 存 mutation-transcripts/）：
  **19/19 全 KILLED**（token 流法下可变异面收敛：M7 text 过滤 / M20 AUTO 段跳过为
  本卡自有决策点；M16/M21/M22 的 Markdown 库语义不可变异，由集成测试锁定）。判据 = rc==1 且指定门 FAILED 行在 transcript。round-2 新增 M11 自身贡献
  排除 / M12a symlink 层 / M12b 越界层 / M13 跨行 span / M14 裸 null。⛔ M8/M12a/M12b 首跑
  SURVIVED——真凶是本卡测试文件**同名测试函数重复定义**（:385 新版被 :466 旧版后定义覆盖，pytest
  只执行无判别力版本），已删旧版 + 加 `test_no_duplicate_test_names` 防回归门 + 每层防线配专属
  原因断言/直达单测（纵深防御不再吞判别力）。还原后 cmp 逐字节相同 + 复跑 76 passed。
- 禁改门：`git log --format= --name-only $(git merge-base HEAD
  worktree-feature-obsidian-hybrid-dev)..HEAD -- <五文件> | sort -u` → **空** ✓
  （另有 Codex 独立 `git diff` 六文件复核，含 .gitignore）

### ⛔ 零写铁律的如实陈述（round-1 BLOCKER-1 整改后）

- **live vault**：三轮取证全树 sha（**排除 `outputs/今日复习.*`**）逐字相同——排除后的全树零写已证；
  被排除的 `今日复习.*` 本身**不在承诺内**（launchd 与按需刷新是它的合法写者），§6 第 4 条如实声明。
- **LANE 工作区**：vault_lint.py 以模块级 `sys.dont_write_bytecode = True`（先于一切 import）兜底，
  无环境变量时 CLI 直跑（`--help` 等）0 个 .pyc（Codex 两轮独立实测；行为门
  `test_cli_help_writes_no_pyc_without_env` 锁定）。**残余边界**：本模块被当作库 `import` 时
  自身的 .pyc 由 Python 在模块执行**前**落盘，模块级开关管不到自己——该场景只有调用方的
  `PYTHONDONTWRITEBYTECODE=1` 能挡（Python 机制边界，--help 门与 docstring 已如实声明）。
- **如实登记一次已发生的违例**：勘探期（probe-B，本卡实现之前）的 import 副作用实验曾在
  LANE 的 backend/app、app/core、app/utils 下写出 8 个 .pyc，事后已 mv 清除——**恢复不等于
  从未写**，如实记录在案。该实验产物不属提交内容；当前工作树对本卡的 git 状态 = 全部为
  untracked 新文件（本卡尚未 commit，"干净"仅指无 pyc 残留与无禁改文件改动）。
- conftest 措辞修正：本卡**未新建** conftest；但 pytest 会自动加载父级 conftest 链（与本仓
  全部单测相同），故测试进程 warnings 里有 jieba/graphiti 的 import 副作用——那是裁判环境的
  固有行为，非本卡测试文件引入。

## 4-B. 人话版结果（给你勾真伪用）

本次检查读了学习库里的全部笔记，**只看不动**（跑前跑后逐字节核对——除了系统每小时自动更新的
"今日复习"推送文件不算在内，其余一个字都没改）。最终一轮（2026-09-01 上午 9:33）结果：

1. **孤儿卡片：0 个。** 「节点」文件夹里 14 张学习卡片，每一张都能查到出处（要么挂在某块白板上，
   要么笔记里写明了来源）。清单是空的，没有需要你逐条确认的孤儿。
2. **内容混淆：0 条。** 没有发现"机器生成的东西混进你手写的区域"或反过来的情况；
   4 份回顾报告也都带着正确的"回顾"标记。
3. **复习计划：今天的、是最新的。** 系统每天早上 9:05 自动更新复习计划——今天 9:05 的更新已经跑过，
   所以检查时看到的就是今天的版本。（此前凌晨试跑时看到的是昨天的数据，也属正常：
   每天早上 9:05 之前，显示的都是昨天生成的版本。）

如果你在库里发现某张卡片明明没有任何来源却被系统认为"有来源"（或反过来），请告诉 Claude，
那说明检查规则有漏洞需要修。

## 5. 待你裁决（全部是**建议默认、待裁决**，不是已裁定）

| # | 事项 | 我的默认与理由 |
|---|---|---|
| ① | **退出码 3 的扩展**。卡文只规定 0/1/2，但同目录 check_vault_doc_roles.py 与 check_readme_claims.py 都用 **2 = 配置/环境错误**，与本卡「2 = 有 warn」直接冲突。若把"台账 SHA 不符/vault 路径不存在/参数用错"压进 1 或 2，调用方无法区分「库有问题」与「检查没跑成」（计划书 §4 第 4 条：空结果与系统故障必须分开）。round-1 HIGH-6 整改把 argparse 用法错误也归 3 | 建议保留 3 = 配置/环境错误（含用法错误），并在 --help 声明（已做） |
| ② | **orphan 口径的放宽与收紧**。已收紧（round-1 整改）：AUTO 哨兵段/围栏/行内 code/HTML 注释/跨行伪链全部不判定为入链。仍放宽（有意）：NFC 归一 + casefold（方向=少报孤儿，代价：仅差大小写/归一形态的两个同名节点会互吃入链）；frontmatter wikilink 一律不算入链（含别的文件指向本节点的） | 建议维持（live 14/14 无同名冲突；frontmatter 豁免由 source_board 条件独立承担） |
| ③ | **raw-derived 子集 = G1/G2/G3/G4/G9 + 回顾缺 recap**；走 `with_probe=False` → **G5/G6/G7（台账与真实准入函数对账）本次未验证** | 建议维持零写优先；G5-G7 对账属 G8-1 enforce 档的职责，可在后续卡以"可写临时目录"前提单独接线 |
| ④ | **freshness 分级**：stale/no_projection = warn、corrupt = fail；orphan/raw_derived 的 finding = warn（orphan 另有 fail 态 = `节点/` 目录不存在） | 建议维持（孤儿是治理信号不是故障；判 fail 会让真实库恒红=死门） |
| ⑤ | **每日 00:00–09:05 freshness 恒 stale**（launchd 9:05 首推前的结构性窗口）——夜间跑 lint 恒 rc=2 | 建议接受"夜间恒 warn"（诚实反映"投影不是今天的"）；替代方案=按"最近一个已排定 slot"对齐（会引入更复杂的口径），不推荐 |

## 6. 本卡未证明什么（必填段）

1. **orphan 不比什么**：NFC/casefold 归一的双向假阴（仅差归一/大小写的同名节点互吃入链）；
   frontmatter wikilink 一律不算入链；symlink 文件拒读只记盲区（盲区里的文件可能是孤儿也可能
   不是）；**AUTO 段与围栏交叉的对抗构造**（手改哨兵块再夹围栏，round-2 HIGH-4 末项）不处理——
   真实生成器不产出此形态、哨兵块明写"⛔ 请勿手改"，解析按 AUTO 段优先。
2. **检验白板入链支在 live 无正样本**（10 份考卷正文零 wikilink，probe-F 实测）——"三处入链源"
   里这一支只被 fixture 用例证明，live 上从未抓到过真链。
3. **recap 子检查在 live 恒绿**（4 份回顾全带 type: recap）——它不是死门由 fixture 反例 + 变异链
   证明，但它**在现网还没抓到过真问题**。
4. **今日复习.\* 排除**：live sha 门显式排除 `outputs/今日复习.*`（launchd 与按需刷新是它的
   合法写者）——该文件本身在取证窗口内是否被动过，本卡**不证明**；sha 门只覆盖其余全树，
   措辞全文统一为"排除后的全树"。
5. **freshness corrupt 面窄于 oracle**：oracle 的 `_summarize()` 有几百行 v3 形状门禁，本实现只
   复现四类（读不出/非 object/缺 generated_at/generated_at 非字符串）；形状垃圾输入两侧可能
   分歧；同源锁只在**合法 v3 投影**上锁等价。「抽 is_projection_stale() 公共函数」已登记为
   W6 合并后 micro。
6. **G5/G6/G7 未验证**（③ 的代价）：live 上"台账双列与真实准入函数一致"本轮没有对账。
7. **G8-1 门 119 的不回归只在 9af18b27 树验证**；V5 合入主干（改 ROLES_SHA256 常量 + yaml 5 行）
   后须 merge 主干复跑裁判 1（卡文要求，属合并流程）。
8. **import-as-library 的 .pyc 边界**（round-2 MEDIUM-4）：模块被当作库 import 时自身 .pyc 由
   Python 在执行前落盘，模块级开关管不到——只有调用方环境变量能挡；CLI 直跑入口已完全兜底。
9. **resolve_today 默认分支的时钟测试**用 patch 时区对象为 New York 的结构判别（环境无关），
   但它锁的是「经过 _TZ_SHANGHAI 换算」这一实现结构，不锁"墙上的真实今天"。
10. **Codex 审查终局**：round-1 FAIL（1B+7H+4M）→ 整改 → round-2 FAIL（0B+4H+4M）→ 整改 →
    **round-3（终轮）FAIL：0 BLOCKER + 4 HIGH**（存档 codex-review-CARD-G8-2-round3.md）。
    停轮条款到顶：**不合并，留台账 §一**。4 个 HIGH 的精确修复方案见本文件顶部「停轮裁定」表。
    Codex round-3 时点独立确认：176 passed / 15 mutant 全杀 / live sha 三轮一致 / 禁改零改动 /
    （round-5 终态 = 184 passed / 19 mutant 全杀 / live 五轮一致，见 §4-A）/
    重名防回归门有判别力——即**已完成的部分全部为真**，未清零的是四处边界缺口（symlink 四场景、
    不可读子树、code span 等长、MANIFEST 覆盖面），均非构造性前提。

## 7. 移交与后续

- ⛔ **依赖移交（r12 M1）**：`_wikilink_targets` 依赖 markdown-it-py 4.0.0（当前经
  fastapi-mcp→rich 传递依赖提供，非直接声明；mdit 版本随 Python 矩阵可能漂移至 3.0.0）——
  **移交独立 DEBT 卡**：requirements.txt 显式声明 `markdown-it-py` + 生产 clean install 验证。
  注：总账 DEBT-1 实为「全量测试超时」——本移交**不挂在 DEBT-1 名下**，独立登记。
- ⛔ **停轮移交（历史，r3 时点）**：r3 曾判停轮移交（4 HIGH 修复方案表），后经用户授权
  续轮 r4-r12 全部处置完毕——该表保留为历史记录，现行状态以顶部「终态裁定」为准。
- G8-3（第二批 lint：批注/DLQ/备份）挂接点 = `CHECKS` 注册表加行；skipped 语义已就位。
- W6 合并后 micro：抽 `is_projection_stale()` 公共函数替换本卡复制的 `_is_stale`（同源锁会自动
  变成直接锁公共函数）。
- 孤儿清单现网为 0：orphan 检查的价值要到第一个真孤儿出现才兑现；4-B 的勾选意义在"你确认
  0 是对的"。
- **本卡最大教训已入 MEMORY**：同名测试函数重复定义会被 pytest 静默覆盖（collect 只报一个），
  判别力无声丢失——`test_no_duplicate_test_names` 门 + MEMORY 条目双保险。
- live-sha 命令的 locale 依赖：`LC_ALL=C` 与 `en_US.UTF-8` 下 `shasum | sort` 排序不同 → 汇总
  sha 不同（前后相等的证据不受影响）；跨环境复跑须固定 `LC_ALL`。

## 附 A：round-1 审查整改对照（逐条）

| Codex round-1 | 内容摘要 | 整改 | 复验 |
|---|---|---|---|
| BLOCKER-1 | 无环境变量时 `--help` 也写 .pyc；验收单零写声明过宽 | `sys.dont_write_bytecode=True` 先于一切 import；零写陈述诚实化 | Codex round-2 复测 rc=0/0 pyc PASS + `test_cli_help_writes_no_pyc_without_env` |
| HIGH-1 | 文件 symlink 跟随 vault 外 | round-2 升级为 `_scan_block_reason` 统一边界守卫（见附 B） | 附 B |
| HIGH-2 | AUTO-GENERATED 哨兵段当入链 | 段级剥离（BEGIN→END 整段） | round-2 复核 PASS + live 复跑 0 孤儿 |
| HIGH-3 | `节点/` 不存在 → ok；不可读 → ok | 缺目录=FAIL；盲区去重 + ≥warn | round-2 复核 PASS（dangling 项并入 HIGH-1） |
| HIGH-4 | 围栏/行内 code/HTML/跨行豁免真孤儿 | 四级剥离（round-2 再升级，见附 B） | 附 B |
| HIGH-5 | frontmatter 排除门无判别力等 | 三判别用例（round-2 复核 2/3 PASS，空链项见附 B） | 附 B |
| HIGH-6 | argparse rc=2 撞 warn | `error()` 退 3 | round-2 复核 PASS |
| HIGH-7 | 变异判据过宽；无 transcript | 指定门 FAILED 行 + transcripts/ | round-2 复核 PASS |
| MEDIUM-1~4 | 见 round-1 存档 | 全落地（round-2 部分回退见附 B） | 附 B |

## 附 B：round-2 审查整改对照（逐条）

| Codex round-2 | 内容摘要 | 整改 | 复验 |
|---|---|---|---|
| HIGH-1 REGRESSED | symlink 三旁路：目录 symlink 后代 / dangling 静默消失 / recap 二次读取 | `_scan_block_reason` 统一守卫（复用 cvr `_resolves_inside_vault` realpath 整链判定）接入 orphan 两循环 + recap 循环；`_iter_md` 放宽 `is_file() or is_symlink()` 保 dangling 在列 | M12a/M12b 杀 + 四段 fixture 各配专属原因断言 |
| HIGH-4 REGRESSED | 四反引号栏 / 双反引号 span / 跨行 span / 未闭合 comment / AUTO-fence 交叉 | 两段式剥离（行级 AUTO+fence 带长度语义；文件级 span+注释含未闭合剥到 EOF）；**AUTO-fence 交叉不处理**，登记进「不比什么」§6.1 | M7/M13 杀 + 9 形态分组用例 |
| HIGH-5 REGRESSED | 空 `[[]]` 用例无判别力（同 fixture 有效链兜底） | 用例重写：板里**只有**空链，A 必须报 | 变异可杀（空链映射变异 → A 被豁免 → 红） |
| HIGH（新） | 存档未绑定当前字节 | evidence-g82/MANIFEST.txt 绑定源码/测试/全部证据 sha256 + 失效条款 | §4-A 首段 |
| MEDIUM-1 | 子目录同 basename 自贡献假阴；quoted-null | 入链豁免统一为「排除自身来源」；null 判定移到剥引号前（只认裸 null/Null/NULL/~，"none" 是字符串不吞） | M11 杀 + `test_orphan_quoted_null_is_string_not_yaml_null` |
| MEDIUM-2 | 时钟测试环境依赖 | patch vl.datetime 为固定钟 + 时区对象换 New York 的结构判别（与宿主 TZ/日期无关） | `test_resolve_today_default_is_shanghai_not_host_local` 重写 |
| MEDIUM-3 | UAT:89「live 零写已证」过宽 | 全文统一"排除 今日复习.\* 后的全树"；被排除文件显式不在承诺内 | §4-A/§6.4 |
| MEDIUM-4 | import-as-library pyc；门是测试自设 | docstring/--help/§4-A 如实声明 Python 机制边界；新增**行为门** `test_cli_help_writes_no_pyc_without_env`（tmp 副本无环境变量实测 0 pyc，生产 guard 被删必红） | 该门 + M 系列 |
| LOW | docstring :33 矛盾；symlink 注释；round-2 时间 06:5x | 三处措辞修正（含本条 §4-A 的 07:06/09:33 实时戳） | 本文 |
| （自查） | — | **重复定义真凶**：test_orphan_symlink_never_read 旧版残留覆盖新版 → 删 + `test_no_duplicate_test_names` 门 + MEMORY | M8/M12a/M12b 转 KILLED |

## 附 C：round-4/5 审查整改对照

| Codex 轮次 | 发现 | 整改 | 复验 |
|---|---|---|---|
| r4 H1a/H2 | 嵌套目录 symlink 与 chmod000 子树静默消失 | `_walk_md` 复用 `cvr._walk_vault`（os.walk onerror + dangling 单列） | r5 PASS |
| r4 H1b | 目录别名 realpath 绕过自身排除 | 入链/豁免统一 realpath 键 | r5 PASS |
| r4 H1c | recap 盲区只改特例漏 G8/G10/G11 | r5 状态判定纳入全部盲区 | r5 H1 PASS |
| r4 H1d | outputs 越界读外部投影 | `_projection_status` 前置 realpath+symlink 检查 → corrupt | r5 PASS（FIFO 探针证守卫先于读取） |
| r4 H4 | MANIFEST 未含 transcripts/G8-1 测试 | 改 `find -type f` 全覆盖 | r5 PASS（62/62 + comm -3 空） |
| r5 HIGH-1 | closer「≥ opener」是 fenced 规则；span 须**严格等长**（`` `x``[[A]]` `` 反例） | 配对条件 `!=` 跳过不等长 run；新增 1/2/1 形态用例 | 变异 M16 恢复承重，r6 待复核 |
| r5 HIGH-2 | span 剥除空串拼接制造伪 wikilink（「[`x`[A]]」→「[[A]]」） | 剥除改**空格占位**；新增伪链用例 | 变异 M21 承重，r6 待复核 |
| r5 M1 | M16 删除理由不成立（等长语义独立） | M16 恢复为新锚（closer 退回 ≥ 变异） | r6 待复核 |
| r5 M2 | UAT 多处终态陈旧 | 全文统一 round-6 终态 + 历史段标注时点快照 | 本文 |
| r5 M3 | --help 未同步盲区 warn 契约 | epilog 补「或存在扫描盲区」；help-full.txt 重存 | test_help_lists_checks_and_exit_semantics |
