> 批次: BATCH-2026-09-18-第十五批 · 车道 P6 · 卡 CARD-SEB-WRITER-SUBSTRING-TMP round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SEB-WRITER-SUBSTRING-TMP.md)"`
> 审查绑定: `13ab1b37bd7840a26e568a71a5c77bd3e6d30b13`（= 本轮 HEAD，Codex 正文首段已自行核实该 SHA）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`(L2) / `model: gpt-6-astra`(L5) / `reasoning effort: ultra`(L9)

---

**已读实现未发现 BLOCKER/HIGH；发现 1 项 MEDIUM 测试覆盖缺口。整卡暂不能判完整 PASS：④的独立重算、⑤的全文计数、⑥的原文核对需要超出限定读取面，额外读取请求尚未获答复。**

HEAD 已核实为 `13ab1b37bd7840a26e568a71a5c77bd3e6d30b13`。本轮没有运行 pytest 或真实写盘块，只执行了提取出的纯内存查重片段。以下 `SEB` 指 `canvas-vault/.claude/skills/start-exam-board/SKILL.md`。

- **[MEDIUM] 五门绑定了真实写规，但没有充分约束“字段精确等值”。**  
  `backend/tests/skills/test_seb_writer_exact_match.py:175、233、267`；`SEB:501`  
  **复现思路：**负控输入仅将 `_rec.get("event_id") == evid` 改成 `evid in _rec.get("event_id", "")`，五门现有输入的查重结果全部不变，但历史 ID 为 `exam:测试节点-检验-另一场` 时，会误拦新增 `exam:测试节点-检验`。  
  内存核验确认：这个对照输入在当前实现中 `seen=False`，变异版为 `True`。**当前代码正确；缺口在门，不能据此声称当前实现仍有子串缺陷。**两段原负控证明了各自对指定回退敏感，不能证明完整语义。

- **[LOW] 五门没有验证历史保留，也没有证明真重复时确实不写。**  
  `backend/tests/skills/test_seb_writer_exact_match.py:183、241、267`；`SEB:447`  
  **复现思路：**负控输入给 `os.open` 增加 `O_TRUNC`，清空历史后重新写一条目标事件，现有计数断言仍可全部满足。  
  这是**门未覆盖的路径**；当前 flags 没有 `O_TRUNC`，不计为本次实现缺陷。

- **[LOW] 当前验收单仍把函数内替换误归为导入期，并扩大了负控③的证明范围。**  
  `_bmad-output/验收单/UAT-CARD-SEB-WRITER-SUBSTRING-TMP-20260918.md:254`，另见 `:159`  
  **复现思路：**负控输入只回退 `test_g3_3_cas.py:144` 的替换字面量，模块级提取仍可通过；它不会造成所述 collect-time ERROR，也没有验证宿主的 `mkdir → Write`。  
  验收单当前有未提交改动，此项针对读到的工作树文档。

- **[LOW] 指定台账锚点不存在，无法核实两条来源登记。**  
  `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:293`  
  **复现思路：**按物理行读取，该文件当前只有 **225 行**；没有扩读其他位置寻找替代条目。

其余问题的结论：

| 问题 | 独立核对结果 |
|---|---|
| **⓪ 是否真绑写规** | **是。**测试 `:63–79` 提取 SKILL 块且仅替换 `P`，`:93–100` 启动子进程。门①夹具没有目标 `event_id`；门②夹具的非法字节行被计数器严格排除，因此目标记录不能由夹具冒充。直接删除查重虽能使①②通过，但③④会拦截。 |
| **① 异常捕获** | `SEB:491–500` 的 `try` 只有解码与 `json.loads`；字段比较、I/O、锁均不在其中，未发现吞掉这些操作错误的问题。但“捕到异常＝语法坏行”并不严格成立：解释器资源限制也能触发异常。本机实测 **5000 位合法 JSON 整数触发 `ValueError`**；递归限制也可能使合法深嵌套内容触发 `RecursionError`。它们都会按“本解释器无法解析的行”跳过。`MemoryError` 不被这个内层捕获，会进入既有外层失败处理。 |
| **② 目录顺序** | `SEB:430` 明确无条件先 `mkdir -p`，再 `Write`，不依赖 Step 3。该块未发现因普通 `node` 输入而绕过建目录的分支。**宿主是否实际执行成功没有端到端证据**；建目录失败或目录随后被删除也不在五门覆盖内，不能把 prose 正确等同于运行已证实。 |
| **③ 锁/CAS** | **未见漂移。**`:447` 打开账本，`:452` 加锁，`:461/:464` seek/read，`:509` write，`:516` close，全部同一 `fd`。`:436` 打开的是参数文件。准确说，危险的是同进程**关闭**指向同一账本的其他 fd，不是第二次 `open()` 本身。四处路径锚均改齐：cas `:49/:144`，schema `:1018/:1022`。 |
| **④ 四张基线** | diff 中能核对到 `577→603`、新增 `604` 和对应指纹更新，**但没有独立重算，不能确认不存在遗漏**。原读取面只提供表，没有提供判据函数及完整输入。另：`ESCAPING_TMP_BASELINE` 是路径多重集，并非行号表。digest 实测和作者“先实测后贴入”的过程也未独立证明。 |
| **⑤ 变更记录** | diff 中新增条目含卡号，没有重新写入旧裸字面量；两个原路径均已替换。**全文件旧字面量计数为 0 尚未独立测得。** |
| **⑥ quiz-answer 同族登记** | 原读取清单未包含其 `:3087–3095`，因此只看到 UAT 的登记，**不能把作者陈述当作独立确认**。 |
| **⑦ 其他未覆盖路径** | 五门还未覆盖：多历史行及不同 JSON 编码形态、参数文件损坏/缺键/类型错误、固定参数文件的并发覆盖与删除竞争、锁超时及 I/O/短写/清理失败。这里只能断言“**五门未覆盖**”，不能断言其他既有回归门也未覆盖。LF 和 event_id 形态仍按你的边界视为**相邻面、已登记**。 |

⑦“一增一减”改靶仍保持原语义：单处迁入命名空间使 `ns +1`，新增裸路径使 `all +1`，差值不变，同时要求 `tmp_all` 端报红；操作对象是 sandbox 副本。九份 SKILL 的普查结论未在本轮独立复验。
