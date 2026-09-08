> 批次: BATCH-2026-09-07-第十三批 · 车道 U10 (`card-u10-red-a`) · 卡 CARD-HYGIENE-conftest round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HYGIENE-conftest.md)"`
> 审查绑定: `13a138c9`（= 本轮送审时的 HEAD）
> 会话头自证（抄 .stderr 实测行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

## 结论

**不建议 `13a138c9` 原样合并。**降级机制的正负控、双树并发和 202 条红基线对账成立；但新增源码门存在**目录枚举失败后静默通过**的 HIGH 问题，而且漏检范围超过已登记的“运行期拼接”，不能据此断言告警“不是本次新增回归”。另有文件符号链接越界读取的健壮性问题。依据见下列发现。

已确认当前 HEAD 为 `13a138c98ead1e4e8d2a23536486b2f6c97930d3`，指定文件与提交一致，其 SHA256 与修后存档 `E/unit-n2p-20260908T071312.txt:2` 一致。

下文路径简写：

- **C**：[backend/tests/unit/conftest.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py)
- **U**：[验收单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md)
- **E/**：[evidence-hyg-conftest/](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-hyg-conftest)

## 发现

### [HIGH] 目录枚举失败不会进入 `unchecked`，新增硬门可以静默通过

- **位置**：[C:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py:127)，C:128–146、201–205。
- **问题**：`unchecked` 只处理**已经枚举出来**的文件；`rglob` 没能枚举的目录没有记录。“读不了不算通过”没有覆盖目录遍历阶段。
- **依据**：我在对应的 Python **3.14.4** 中，仅提取并执行本文件的实际 `_hygiene_scan_tmp_literals()`，使用进程内审计钩子，在实际目录访问前让 `os.scandir` 抛出 `PermissionError`。结果为：
  ```text
  actual_helper_return=([], [])
  ```
  两次枚举均被拒绝，异常却被 `rglob` 抑制；函数把“未检查”返回成“无命中、无检查失败”。没有改权限或文件。代码中的异常捕获始于 C:128，覆盖不到这种失败。
- **影响**：例如运行单个文件时，另一个未被收集的子目录不可枚举，源码门会遗漏其中的违规常量。这是本卡新增的假绿路径，与已移交的旧 sha/`None` 问题不同。
- **建议**：使用能显式报告目录枚举错误的只读遍历，将失败目录加入 `unchecked`，并补充目录枚举拒绝的承重验证；仅在 `rglob` 外面加 `try` 不够，因为异常已经被抑制。

对**成功枚举出的文件**，现有处理正确：读取的 `OSError`、解析的 `SyntaxError/ValueError` 均进入 `unchecked`（C:132–140），最终进入硬失败（C:201–205、229–237）。`tmp is None` 不会绕过这个出口。另一个控制流边界是：若 warning 被配置成 error，C:212 会先于 C:229 抛异常，遮蔽已有违规的合并诊断；**仍然是红，不是假绿**。

### [HIGH] 漏检不只运行期拼接，却把“归属未知”写成“已排除本树回归”

- **位置**：[C:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py:143)，C:164–165、223–224；U:37–41、346–361。
- **问题**：判据只是“某个 `str` 类型的 `ast.Constant` 含连续子串”。已登记盲区不完整，补偿门也不能证明本树没有 `/tmp` 写者。
- **依据**：按 C:143 的实际判据做内存 AST 验算，下列形态均无命中：

  | 未拦输入 | 漏检原因 |
  |---|---|
  | `Path("/tmp//test-vault-x").mkdir()` | **单个字符串**，路径等价但子串不匹配 |
  | `Path("/tmp/./test-vault-x").mkdir()` | 同上，并非运行期拼接 |
  | `os.mkdir(b"/tmp/test-vault-x")` | `bytes` 被 `isinstance(..., str)` 排除 |
  | `Path("/tmp") / "test-vault-x"` | 路径运算分段 |
  | `tempfile.mkdtemp(prefix="test-vault-", dir="/tmp")` | API 分参数产生目标 |
  | cwd 为 `/tmp` 时使用 `"test-vault-x"` | 相对路径本身没有绝对前缀 |
  | 从环境、配置、扫描范围外模块取得路径 | 值不在本次扫描的字符串常量中 |

  此外，C:129–130 排除的是**整个 conftest 文件**，其中其他 fixture 将来出现完整硬编码路径也会漏检；这些其他 fixture 确实存在于 C:240–318。

  允许材料里已有一种**真实执行过**的漏检写法：`E/treeB-probe-source.py.txt:35–38` 使用 `Path("/tmp") / ("test-vault-treeB-" + str(os.getpid()))` 并创建目录，执行记录见两个 `treeB-probe-n2*.txt:25`。它是树 B 的临时探针，不能据此声称树 A 当前存在同样写者。

- **影响**：本树通过上述形态写入新目录时，可以只收到 warning；但 C:224 写“不是本次运行新增的回归”，U:347 更解释成“这是别人弄的”。这些结论超出了证据。U:37–41 的文本搜索也不足以证明“本树已无 `/tmp` 根写者”。
- **建议**：补齐盲区登记，评估覆盖字节路径、路径规范化及整文件排除边界；剩余风险可以明确保留，但告警必须改成“**共享目录发生变化，归属未知，可能来自本 session 或其他进程，需要核查／重跑**”。无需把本卡扩成完整数据流分析。

两个精度补充：

- `f"/tmp/test-vault-{name}"` **会命中**，只有完整前缀被拆开的 f-string 才漏；`"/private/tmp/test-vault-x"`、转义后得到完整前缀的字符串、相邻字面量也会命中。依据是 C:143；相邻字面量另有 `E/selfprobe-const-premise-20260908T071236.txt:1–12`。
- 该门也会命中文档字符串、未使用常量及含该子串的其他路径；P1 本身就是未执行写入的常量（`E/negctl-p1-red-20260908T070947.txt:7、23–24`）。它证明的是**源码规则承重**，不是写入归属。

### [MEDIUM] 文件符号链接可以让“树内扫描”读取树外源码

- **位置**：[C:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py:121)，C:127–131。
- **问题**：`py.resolve()` 只用来判断是否为 conftest 自身，没有校验目标是否仍位于扫描根内。
- **依据**：树内一个 `*.py` 文件链接若指向树外，C:129 不会排除它，C:131 的 `read_bytes()` 会读取链接目标。
- **影响**：外部内容可以触发本树硬红，“三个信号都在本 worktree 内、天然唯一”（C:157–158）不再成立。这不产生文件写入，但违反声明的读取范围。
- **建议**：明确符号链接策略，在读取前验证解析后目标的包含关系；越界目标应报告边界不符，不能当作普通树内源码读取或静默跳过。本轮没有检查实际是否存在此类链接。

## 作者自述逐条核对

| # | 主张 | 成立? | 依据 |
|---|---|---|---|
| 1 | 告警不会升级，且可见 | **本次存档成立；普遍保证不成立** | `E/negctl-n1-after-20260908T070910.txt:57–73` 确有 warnings summary、`rc=0`。`pytest.ini` 不在允许读取面，未直接核验。C:212 没有固定过滤策略，不能排除其他启动参数或运行期过滤器升级／隐藏 warning。 |
| 2 | 排除自身；grep 判据确实翻转 | **成立，但证明范围有限** | C:62、129–130；独立比较基线与提交，完整子串计数确为 1→0。`E/selfprobe-const-20260908T071249.txt:7、61–67` 支持自身排除与恢复。grep 翻转只证明文本变化，不能单独证明排除逻辑；注释探针也因整个文件被排除，不能单独证明其他文件注释的行为。 |
| 3 | N1 修前红、修后不红且告警可见 | **成立** | 修前 `E/negctl-n1-before-20260908T065914.txt:19–25、72–76`；修后 `E/negctl-n1-after-20260908T070910.txt:57–73`。确为 1 error／rc=1 → warning／rc=0。 |
| 4 | P1 指名 file:line，恢复后转绿 | **成立** | `E/negctl-p1-red-20260908T070947.txt:23–24、75–78` 指向 `test_vault_init_service.py:140`，恢复 hash 相同、diff rc=0；green 存档 `:2、54–55` 同 hash、8 passed、rc=0。 |
| 5 | 骨架与 tracked sha 硬失败未回退 | **代码成立；P2 实测覆盖骨架** | 基线 diff 未改 C:75–97 的快照和 C:181–191 的两个比较分支。`E/negctl-p2-red-20260908T071051.txt:21–23、70–77` 确报 `backend/raw`。没有单独 tracked sha 正控；warning 升级时的诊断遮蔽边界见前文。 |
| 6 | 卫生 fixture 无文件副作用、不依赖 cwd | **成立；树内读取保证不完整** | C:65–237 无创建、删除、写入、`chdir` 或 `app.*` 导入；根分别由 C:72、121–122 的 `__file__` 确定。其他 fixture 的导入不能混算。枚举错误与符号链接问题见发现。 |
| 7 | N2/N2′ 真双树并发且命中窗口 | **成立** | 两个 B 存档 `:19、25、31` 有独立 rootdir、创建打印及旧门同名差集；事后目录分别在 `:87`／`:88`。A 同名结果在 `E/unit-n2-20260908T070034.txt:540` 和 `E/unit-n2p-20260908T071312.txt:2837`；两份 `window-n2*.txt:1–5` 记录交叠。 |
| 8 | 四目录实跑，nodeid diff 为空 | **红 nodeid 口径成立** | 直接重算 unit 原始 summary：open `:2843–3044` 与 n2p `:2850–3051` 均为相同的 173 FAILED＋29 ERROR，与 `E/red-baseline-202.txt:1–202` 一致。非 unit 两轮均无红项；但存档只有文件级进度，不能证明**全部用例 nodeid** 集相同。API 汇总见 open `:103–104`／after `:102–103`，regression 见 `:191–192`／`:190–191`，skills 见 `:67–68`／`:66–67`。U:170–172、380–381 宜明确写“红 nodeid 集”。 |

关于第 7 条的时序精度：`date` 记录的是**进程起止**，不是 fixture 快照时刻。真正补足“命中两次快照之间”的证据，是树 A 正文中的同名新增差集，结合 C:174–176、209–211；所以本次不只是依据预计启动耗时推演。

关于临时探针的证明力：对本卡修改的“新增目录名称差集 → fail／warning”机制，空目录探针足够。它没有证明真实车道测试写者及实际调度频率，而 U:236–239、373–379 **已经如实登记**，没有冒充完成。U:374 将“运行期拼接”整体列为未验证稍不准确，因为探针本身就在拼接；宜收窄为其他尚未覆盖的写法。

## 我没有检查的面

- 未读取白名单外的 `pytest.ini`、其他单测源码、生产代码或库源码，因此不能确认树 A 当前是否已有上述漏检写者，也不能确认实际符号链接／权限布局。
- 未重新运行 pytest、并发建目录或恢复探针；本轮完成的是存档对账、提交绑定、内存 AST 验算，以及拒绝实际目录访问的枚举失败探针。
- 未评 contract 属性输入链、W4 端口门或 202 条既有红的原因。
- 旧 MEDIUM #5 的 sha／`None` 和 `/tmp` 不可读处理在本卡未变（C:85–95、185–186、209；U:362–365），没有发现因“本卡不修它”新增的这类真假红路径。**新增源码枚举失败属于本卡自己的问题，不能由该移交覆盖。**
