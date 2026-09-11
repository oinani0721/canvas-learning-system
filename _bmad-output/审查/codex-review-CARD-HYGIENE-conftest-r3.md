> 批次: BATCH-2026-09-07-第十三批 · 车道 U10 (`card-u10-red-a`) · 卡 CARD-HYGIENE-conftest round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HYGIENE-conftest-r3.md)"`
> 审查绑定: `459190f0`（= 本轮送审时的 HEAD）
> 会话头自证（抄 .stderr 实测行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

## 结论

**不建议 `459190f0` 原样合并：BLOCKER 0 / HIGH 2 / MEDIUM 1。** 三态路径判定和三类失败出口未发现新增假绿；三个遗漏目录确实补跑，红 nodeid 多重集 **202 → 203 → 202** 成立。剩余问题主要是：**诊断仍推断了证据无法证明的写入，验收单仍保留已经接受撤回的归属结论，r3 清理对账判据再次假红。**

已核对完整 HEAD 为 `459190f05b4fe3b356f19b56c39fad7d03688b99`；工作区 conftest 与该提交逐字节一致，SHA256 为 `09161adc…c48b23b9b`，与 r3 存档抬头一致（`E/negctl-n1-after-20260908T081952.txt:2`）。

下文简写：

- **C**：[backend/tests/unit/conftest.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py)
- **U**：[验收单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md)
- **R1**：[round-1 意见](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/codex-review-CARD-HYGIENE-conftest.md)
- **E/**：[_bmad-output/审查/evidence-hyg-conftest/](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-hyg-conftest)

## 发现

### [HIGH] 分段已经隔开，但分段内部仍把观测结果推断为确定写入

- **位置**：[C:338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py:338)，C:324–325、345–348。
- **问题**：源码段将“不表示本次写入”接成了“**将来会往全机共享 /tmp 写**”。常量扫描不能证明未来写入。另一个确定性断言是污染段的“**即本次运行确实写了东西**”：快照差异本身不能证明写者，而且既有 `None ↔ hash` 分支甚至不一定表示内容变化。
- **依据**：
  - `E/negctl-p1-red-20260908T081208.txt:7` 仅添加常量；同档 **:24–28** 实际输出了“将来会……写”。这不是假设场景。
  - C:225–227 只检查字符串子串，没有执行或数据流判断。
  - C:86–91 将读取失败记为 `None`；C:280–285 把它与 hash 的差异加入 `pollution`，最后进入上述确定性标题。U:611–614 已承认这一既有边界。
  - C:345 的“既没通过也没违规”也应是“**是否违规尚不能判定**”；无法检查不能证明没有违规。
- **影响**：round-2 HIGH #1 **只部分闭环**。三类信号不会串段，但各段仍可能给出超出证据的结论。
- **建议**：源码段只说“命中禁止的硬编码常量”；快照段只说“检测到快照差异，写入及归属需结合具体条目核查”；无法检查段保留未知状态。**无需修改本卡明确移交的 sha 比较算法**，也无需降低硬失败。

### [HIGH] 验收单仍将“未发现写者／归属未知”写成已经排除本树回归

- **位置**：[U:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md:107)，U:42–46、772–774。
- **问题**：已经接受撤回的强结论仍出现在当前验收和方案依据里：
  - U:42：“本树已无 `/tmp` 根写者”；
  - U:107–108：“本树自身写者由源码字面量门守……**不是本次运行新增的回归**”；
  - U:772–774：再次把“本树已无 `/tmp` 根写者”用作方案论证前提。
- **依据**：U:142–146、608–610 明确承认源码门及文本搜索不能证明没有写者，与上述表述冲突。R1:58–64 已指出同一问题。U:21–24 的历史说明只列出 **(c)(f)(g)(h)(i)**，未把 **(d)** 标成已失效的旧文案；U:772–774 也仍在当前方案依据中。
- **影响**：读者仍可能据此把本 session 的真实 `/tmp` 写入排除为环境噪音。修改 4-B 和代码告警，尚未完成整份验收单的语义整改。
- **建议**：把搜索结论限定为“这些搜索命中中未发现写者”；将旧告警说明更新或明确标记为已撤回；方案依据采用实际差集机制与双树证据，不再依赖“本树没有写者”。

### [MEDIUM] r3 清理对账再次把通配符文本抽成目录，已修过的判据错误复发

- **位置**：[E/treeB-cleanup-20260908T082507.txt:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-hyg-conftest/treeB-cleanup-20260908T082507.txt:75)，U:354–358。
- **问题**：r3 清理存档再次记录：

  ```text
  13d12
  < /tmp/test-vault*
  tmp_listing_diff_rc=1
  ```

  没有随后的更正记录。
- **依据**：U:354–358 已说明同样错误曾通过“只抽取目录行”修正。我独立抽取 `E/tmp-listing-open-20260908T064505.txt:3–14` 与本轮清理档 **:62–73** 的目录行，得到**相同的 12 项，双向差为空**。
- **影响**：这是清理判据和存档闭环的问题，**不能据此判定目录未归位**。它也是七次登记之外可以明确指出的又一次同型复发。
- **建议**：保留原始失败记录，追加正确抽取后的对账结果及验伪锚，并登记这次复发。

## 作者自述逐条核对

| # | 主张 | 成立? | 依据 |
|---|---|---|---|
| 1 | round-2 HIGH #1 三分段已彻底分清语义 | **部分成立** | 三个 `sections.append` 独立，写者推定位于 pollution 段内部，组合命中不会串到其他段（C:322–350）；分段内部越界见 HIGH #1。 |
| 2 | round-2 HIGH #2 缺失的三个目录已经补跑 | **成立，具体缺跑已闭环** | r3 api **268 passed/rc=0**（`E/api-after-r3-20260908T081114.txt:102–103`）；regression **1464 passed+6 skipped+10 xfailed/rc=0**（对应档 :190–191）；skills **369 passed/rc=0**（对应档 :66–67）。独立提取三者红项均为 0，环境串也均为 0。 |
| 3 | “全部裁判重跑”现在已有完整证据 | **仍只能部分确认** | 主要 r3 控制均有新档；但允许存档没有 **7a/7d/ruff 的 r3 原始结果**，U:449、451 仍在 r2 表内。U:21–24 仍称 r2 为末轮，U:439–451 的总表也未更新。不能说实际没跑，也不能独立确认“全部”。 |
| 4 | r3 P1 red/green 都已验证 | **行为有支持，映射应补齐** | P1 red 与还原见 `E/negctl-p1-red-20260908T081208.txt:24–28、72–78`。没有独立命名的 r3 P1-green 档，但后续 N1′ 用最终 conftest 跑同一文件八项全过（`E/negctl-n1-after-20260908T081952.txt:2、14–16、74–77`），可明确登记兼任；不据文件名缺失判“没有跑绿”。 |
| 5 | HIGH #3 时刻更正且区间论证成立 | **内部纠错成立；真实端点未独立证实** | U:323–334、511–517 已消除算术矛盾；进程窗口无交集确为 fixture 窗口无交集的充分条件。但全部 E 档没有 U8-B 的原始起止记录，不能独立确认 `06:56:28` 的来源。 |
| 6 | `_hygiene_within_root()` 修复大小写假红，没有引入假绿或死循环 | **当前调用约束下未发现反例** | 调用前 resolve（C:193–205）；逐级只与扫描根本体比较，词法父路径到根即终止（C:122–131）。别名及反向锚见 `E/probe-case-alias-20260908T081030.txt:2–14`。结论限于稳定路径布局。 |
| 7 | `None` 不会被当成通过 | **成立** | C:209–211 → `unchecked`，C:291–292 → `cannot_check`，C:343–357 → fail。另需收窄 C:112 的注释：目标文件消失不一定让 helper 返回 None；若其父目录存在，后续读取失败才负责收进 unchecked（C:213–217）。 |
| 8 | N3c 的前提 rc 已修正并有第二源 | **成立** | `E/negctl-n3c-enum-e2e-20260908T081124.txt:11–13` 为 `ls_rc=1`、Python `PermissionError`；:30–33 正确进入检查段，:76–83 记录 ERROR/rc=1、hash 恢复和无残留。 |
| 9 | round-1 枚举假绿已修复 | **成立** | C:182–186 将枚举错误收入列表；r3 N3b 两版正常均 hits=2，拒绝枚举时旧版 `(0,0)`、新版 `(0,1)`（`E/negctl-n3b-enum-denied-samefixture-20260908T081124.txt:13–24`）；N3c 证明出口承重。 |
| 10 | r3 三端点为 0/29/0、1/30/0、0/29/1，rc 均 1 | **成立** | 独立重算红 nodeid **多重集**：开工 202（`E/unit-open-20260908T064551.txt:2843–3047`）；N2 203，仅多末项 teardown（`E/unit-n2-20260908T070034.txt:2850–3055`）；r3 N2′ 202，双向差空（`E/unit-n2p-20260908T082024.txt:2843、2860–3064`）。 |
| 11 | N2′ 真双树并发且命中快照窗口 | **成立** | B 的独立 rootdir、建目录记录见 `E/treeB-probe-n2p-20260908T082024.txt:19、25、84–87`；A 的同名新增差集见 `E/unit-n2p-20260908T082024.txt:2843`。后者才是命中快照窗口的直接证据，进程时刻为辅助。 |
| 12 | r3 无新增文件副作用、cwd 依赖、app 导入或遗漏出口 | **静态检查成立** | 根来自 `__file__`（C:66–73、176–177）；三类收集 C:276–292、出口 C:322–357；r3 diff 无新增导入。warning 被外部过滤策略升级时仍可能提前抛出、遮蔽合并诊断，但仍为红，这是 R1:36 已记录的边界。 |
| 13 | “红 nodeid 集”措辞已全部落实 | **部分成立** | U:629–632 已明确不能证明全部通过用例集合相同；但 U:569 仍只写“nodeid 口径逐个 diff”。实际对账结论按红多重集成立。 |
| 14 | 加入 pytest.ini 后，“告警不会升级”的问题已经解决 | **当前默认配置及实跑成立；普遍保证仍不成立** | `backend/pytest.ini:19–21` 只有 `-v --tb=short`，全文件无过滤配置；N1′ r3 :58–77 告警可见、rc=0。但 R1:78 同时指出外部启动参数及动态过滤器问题，**不是仅因 ini 未获准读取**。这里仍有对前意见原因的收窄理解。 |
| 15 | 七次之外没有更多同型问题 | **不能成立，也不能穷尽计数** | 本轮清理伪差集是明确新增实例，见 MEDIUM；HIGH #1/#2 也表明同型语义尚有残留。U:707–719 的 U6 事故属作者登记，对方原始日志不在读取面内。 |
| 16 | 不修既有 sha/None 问题没有新增真假红路径 | **未发现新增路径** | 快照与比较条件保持原样（C:76–98、280–286；基线 diff）。本轮指出的是**新增诊断的确定性措辞**，不要求扩面修复既有算法。 |

## 我没有检查的面

- 未运行 pytest、创建探针、修改权限或写入文件；本轮为代码静态审查、提交绑定及 **80 份 `.txt`** 的存档对账。
- 未读取白名单外的其他测试源码、生产代码、W4 支持代码、contract 属性输入链，也未分析 202 条既有红的原因。
- 未读取未获授权的 round-2 外审全文；其五条意见只能对照本次请求与 U:463–554 的转述，不能认证转述完整性。
- 未独立核验 U8-B、U6 的原始运行日志或协作消息；未检查实际符号链接布局、并发换链、xdist 和外部 warning 过滤配置。
