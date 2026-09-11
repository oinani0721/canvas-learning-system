> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-RV-G2-6 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-G2-6-r4.md)"`
> 审查绑定: `977d1e6d`（送审时 HEAD）。⚠️ **本轮之后代码又改了**（4 HIGH + 3 MEDIUM + 2 LOW 整改），故本存档**不绑合并态**；round-5 绑最终 HEAD。
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：0 BLOCKER / 4 HIGH / 3 MEDIUM / 2 LOW。round-4 尚未闭合，其中 `_kind_ok` 的整改仍可新引入假绿。**

校验器全文已与 `977d1e6d` 的 diff 后像逐字核对一致。未修改工作树、运行安装脚本或访问 live vault；运行验证使用内存字符串和匿名管道等隔离输入，未跑完整 pytest。

下文位置缩写：

- `V`：[scripts/verify_vault_install.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py)
- `T`：[backend/tests/unit/test_vault_install_manifest.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py)
- `R`：[_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md)

**BLOCKER：未确认。** 没有实证新的写穿被审对象问题；下述安全扫描遗漏不能据此升级成“已经证明会写穿”。

**HIGH**

1. **【遗留】软链目标在编码前经过 `Path` 规范化，仍可把不同目标判等。**  
   位置：`V:631`，`str(path.readlink())`。  
   复现思路：同名软链分别指向 `payload` 与 `payload/`；两者规范化后的哈希输入相同，而 `payload` 为普通文件时，后者不能正常访问。  
   已实测字符串规范化及哈希输入；`a//b`、`a/./b` 也会丢失区别。`surrogatepass` 无法恢复此前丢掉的信息。

2. **【遗漏】查询成功但类型不支持的条目，仍统一返回 `("?:unknown", False)`，可以假绿。**  
   位置：`V:638`；调用链 `V:479`、`V:682`、`V:941`。  
   复现思路：两棵 copy 目录的同名位置分别放 FIFO 与 Unix socket，摘要记录相同，且不会登记 unreadable。  
   已用匿名管道与匿名 Unix socket 实测 `_leaf_digest`、`_digest`：不同类型均返回 `?:unknown`，`bad=False`。新增的 `lstat` 探测没有覆盖这个入口。

3. **【新引入】`_kind_ok` 返回 False 后丢失查询失败原因，调用方没有兑现“另行登记 unreadable”。**  
   位置：`V:544`、`V:605`、`V:995`。  
   复现思路：可列名字但不可搜索的 `0444` 目录 `g` 含 `x`，声明 exclude `g/*`；目录枚举若能直接提供类型信息，失败只发生在 `_kind_ok`，最终可以得到 `unreadable=[]`、rc=0；增加同范围 extra 扫描后，`x` 又会被误报 extra。  
   这是静态调用链复核，未修改磁盘权限。**因此“一律 False”既可能漏报失败，也确实会造成你担心的误报 extra，空 kind 同样受影响。**

4. **【遗漏】`lstat` 成功之后，跟随软链的类型查询仍可能失败并被当作“不扫描／产物不存在”。**  
   位置：`V:974`、`V:1057`；安全扫描还有 `V:738`、`V:1246`。  
   复现思路：让扫描根或 `main.js` 成为软链，指向不可搜索目录中的对象；链接自身是 present，但后续 `is_dir()`／`is_file()` 返回 False，extra 扫描被跳过或 hotkeys 被记成产物缺失。  
   安全扫描中，同类失败也可能不进入 `failures`，随后身份查询的 None 又被忽略。这里确认的是**未完成扫描却允许通过检查**，未实证写穿。

**MEDIUM**

1. **【新引入】先比较总摘要，会把读取能力的差异误报成已确认的字节差异。**  
   位置：`V:925`、`V:932`。  
   复现思路：两侧文件内容完全相同，只让一侧不可读；正常摘要与 `U:unreadable` 不同，于是报告“与模板源字节不一致”。  
   新顺序恢复了“可见差异与 unreadable 并存”的正例，但缺少“不因 unreadable 单独制造 drift”的负例。

2. **【遗漏】目标缺失时，源端查询失败只写入 missing 的说明，没有进入 unreadable 桶。**  
   位置：`V:864`、`V:867`、`V:869`。  
   复现思路：目标确实没有该 copy 项，源端对应路径因祖先权限无法查询；没有其他问题时仍为 `unreadable=0`、rc=1。  
   目标 missing 的判断正确，也没有报 match；问题在于已经发生的源端查询失败没有进入四档分类。

3. **【整改不完整】断管保护只覆盖最后的 stdout flush，没有覆盖 `main()` 内直接写失败，也没有收住 stderr 失败。**  
   位置：`V:1335`、`V:1352`、`V:1357`；测试 `T:1916`。  
   复现思路：关闭 stdout 管道并启用无缓冲输出；另关闭 stderr 后触发参数错误。  
   本机实际结果：

   | 输入／输出条件 | 实际退出码 |
   |---|---:|
   | 正常报告，同一隔离输入 | 0 |
   | 同一输入，无缓冲 stdout 断管 | **1，附 BrokenPipeError traceback** |
   | stderr 断管后触发参数错误 | **120** |
   | 默认缓冲的 `--help`，stdout 断管 | 3 |

   因此 `--help` 那道门只证明了其中一种输出路径，`R:156` 的完整收口表述不成立。

**LOW**

1. **摘要新门仍能放过另一种有损编码，未锁住单射性质。**  
   位置：`T:1783`、`T:1794`、`T:1804`；对应表述 `R:151`。  
   复现思路：仅把三处 `surrogatepass` 改成 `ignore` 或 `replace`；AST 仍看到三处 encode，现有行为样例仍不同，但 `bad\xfe-target` 与 `bad\xff-target` 又会碰撞。  
   已完成内存验算。准确的证据范围是“拒绝直接使用 `backslashreplace`，并阻止这一对已知碰撞”，不是证明所有摘要编码单射。

2. **去重门仍只证明有两条配置，没有证明两个失败来源都实际到达。**  
   位置：`T:1691`、`T:1697`；对应表述 `R:158`。  
   复现思路：仅把 `_iter_relative` 的空相对路径早退移到 unreadable 登记之前；以 `.claude/hooks` 为根的一路漏报，以 `.claude` 为根的一路仍登记一次，前缀数量与最终“一次”断言都通过。  
   这是单门的静态变异推演；其他入口门可能变红，**不声称整个测试集仍绿**。

你要求的 `_entry_state` 同类入口清单如下：

| 真漏／仍需保留失败原因 | 换了也没意义，或不能靠机械替换解决 |
|---|---|
| `V:544–605`：类型失败只变 False，排除调用链无错误通道 | `V:663`：普通查询失败会进入 `_leaf_digest` 并登记；软链摘要本来只比较链接文本 |
| `V:974`、`V:1057`：链接 present 不代表目标类型可查询 | `V:523`：稳定状态下，普通目录已有入口检查；软链本就不递归 |
| `V:880`：skeleton 的软链目标不可查询，仍可能被说成“不是目录”并归 missing | `V:895`：源端 `exists()` 查询失败已经进入 unreadable；换三态主要修正文案和悬空软链处理的不对称 |
| `V:864–878`：源查询失败仅进 missing.detail | `V:1212`、`V:1275`：查询失败已经拒绝，归 usage；替换主要改善错误说明 |
| `V:738`、`V:1246`：目标类型／禁写根身份失败没有完整登记 | `V:1280`：不能仅凭 exists 吞错推导写穿；独立创建新 inode 再 replace 的保护仍在 |
| `V:1258`：报告祖先身份查询未区分不存在与查询失败 | 此处不能把所有 None 都拒绝；尚不存在的报告路径本来需要向上查找 |

其余明确核对结果：

- **`surrogatepass` 编码本身：无问题。** 遍历了全部 1,114,112 个 Python 字符，包括孤立代理字符，均能编码且单字符编码各异；代理对与对应非 BMP 字符也不同。就字符串内容而言，没有新增 Unicode 编码异常出口。问题在编码前的转换及未知类型合并。
- **摘要记录分隔与 `_printable()`：无问题。** 未发现合法 POSIX 文件名能利用当前 NUL 分隔制造新的记录歧义；报告转义没有回流进摘要。
- **ENOTDIR→absent：无问题。** 属于确定的不存在；新增测试也包含正常存在与普通不存在对照。
- **哑 stdout 对正常路径：无问题。** 只在最终 flush 失败后替换；正常成功路径未受该替换影响。问题是保护范围不足。
- **四档桶优先级：无问题，128 种组合全部通过。** 不能据此推导真实 CLI 的全部异常出口符合契约。
- **四处 `expanduser` 门：无问题。** 已逐一覆盖 vault、source、manifest、report。
- **结论表的历史绑定、O_EXCL 证据收窄及 hotkeys 已知限制登记：无问题，限于文证核对。** 但 `R:151–158` 的“已修／全部已修”必须按上述遗漏收窄；`R:26` 的历史样例通过，也不能外推为全部安全扫描失败入口均已覆盖。未读取表外日志，不替其独立真实性背书。
