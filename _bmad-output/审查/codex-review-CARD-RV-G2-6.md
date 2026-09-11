> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-RV-G2-6 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-G2-6.md)"`
> 审查绑定: `523c10f0`（送审时 HEAD）。⚠️ **本轮之后代码又改了**（2 HIGH + 4 MEDIUM + 4 LOW 整改），故本存档**不绑合并态**；round-2 绑最终 HEAD。
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库；:2/:5/:9）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：8 条历史整改均成立，但仍有漏报、退出码契约和测试门缺口。** 本轮未发现已声明竞态边界之外的新写穿路径。

仅使用指定四处材料；完成了 15 个历史整改隔离样例及退出码全部 128 种桶组合验证。未修改工作树、访问 live vault、运行安装脚本或连接数据库。

以下路径均相对当前 worktree。

- **HIGH — 给了 `--source`，源端 copy 项缺失时，未比较的目标仍会被记为 match。**  
  位置：`scripts/verify_vault_install.py:783`、`:809`。  
  复现：目标存在 `payload.txt`，源目录存在但没有该文件；实测 `match=["payload.txt"]`、`drift_evaluated=True`、`content_drift=[]`、`rc=0`。这是既有残留，不是本次 rc 聚合引入的问题。

- **HIGH — exclude 扫描失败仍可能静默返回 0。**  
  位置：`scripts/verify_vault_install.py:478`、`:537`。  
  复现：声明骨架 `outputs` 和 exclude `outputs/*.txt`，其中存在文件，但目录权限为 `0111`；实测 `unreadable=[]`、`intentionally_excluded=[]`、`rc=0`。指定 `--report` 后安全扫描会拒写并返回 3，但默认 stdout 路径没有这层保护。复审表 `:67` 已登记此残留，不能把它解释为整个校验器已满足“读不动必阻断”。

- **MEDIUM — `main.js` 未评估仍可返回 0，部署核验确实留下盲区。**  
  位置：`scripts/verify_vault_install.py:901`。  
  复现：保留插件目录和 hotkeys，删除 `main.js`，或把它改为目录；均实测 `rc=0`。同时损坏 hotkeys JSON，也因提前返回而不记 unreadable。作者确实明写了 `not evaluated`，因此没有伪造文字结果，但 **rc=0 不能表示热键核验已完成**。

- **MEDIUM — 命令字面量法存在实际假放行和假拦下，源码数量门不能补足注册语义。**  
  位置：`scripts/verify_vault_install.py:84`、`:923`；`backend/tests/unit/test_vault_install_manifest.py:1207`。  
  复现：产物只有注释 `// "canvas:gone"`，对应绑定实测通过；改成单引号注册 `this.addCommand({id:'canvas:gone'})`，反而实测 orphan、`rc=2`。源码门同样只提取文本：把合成的 10 个 `addCommand` 全改成 `console.log`，仍提取相同 10 项。数量锚能防空集，不能证明实际注册了十个命令。

- **MEDIUM — 新 hotkeys 输入重新打开了未捕获的 UTF-8 编码异常路径。**  
  位置：`scripts/verify_vault_install.py:911`、`:929`、`:681`。  
  复现：合法 JSON 中使用键 `canvas-learning-system:canvas:\ud800`，并提供正常 main.js；真实 CLI 实测抛 `UnicodeEncodeError`、退出 **1**、没有报告。它被误归到“只有 missing”的数字档，但没有改动被审对象或留下临时报告。

- **MEDIUM — 参数语法错误仍返回 2，没有进入新增的用法错误档 3。**  
  位置：`scripts/verify_vault_install.py:1081`。  
  复现：`python3 -B scripts/verify_vault_install.py --vault` 实测返回 **2**；`argparse` 默认错误出口未调整。这会混淆 mismatch 与“根本没有执行校验”。

- **MEDIUM — skills 自检仍把没有入口文件的半成品计为完成。**  
  位置：`scripts/install-vault.sh:117`；对应测试 `backend/tests/unit/test_vault_install_manifest.py:1424`。  
  复现：8 个 skill 子目录各放一个名为 `SKILL.md` 的空目录；仅执行该行计数表达式，实测得到 **8**，普通入口文件数为 **0**。测试只检查命令字符串；给判据增加 `|| true` 后，那些断言仍全部通过。

新增测试另有以下 **LOW** 缺口，不能声称都已证明“各自只拆一层”：

| 位置 | 问题与复现思路 |
|---|---|
| `backend/tests/unit/test_vault_install_manifest.py:1334` | **重叠门未锁住反向覆盖。** 删除实现中两处 `or _pattern_covers(path, allow)`，四个参数仍全部通过；但 literal allow `outputs/cache.md` 对 exclude `outputs/**` 已漏拒。已以内存变异实证。 |
| `backend/tests/unit/test_vault_install_manifest.py:1390` | **未评估文字断言会借用别的报告段。** 仅删 hotkeys 提示中的 `not evaluated`，整份报告仍因 content-drift 段含该词而通过。已实证。 |
| `backend/tests/unit/test_vault_install_manifest.py:1364`、`:1409` | **orphan／非法 JSON 门没有排除其他阻断桶。** 若对应分支额外误报 extra，现有目标桶断言和 `rc=2` 仍满足；头注“其余各类为空”比断言更宽。 |
| `backend/tests/unit/test_vault_install_manifest.py:1153` | **方括号门对所述 `GLOB_CHARS` 变异不可区分。** 精确分支与 glob 分支对该输入结果相同；作者对此及未覆盖摘要过滤的登记准确，不能据此宣称该门机械承重。 |

**LOW — 复审表的 HEAD 绑定和一条证据表述过宽。**  
位置：`_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md:4`、`:25`。  
复现思路：对照本卡 diff，即可看到最终文件已不再与 `c4e6b165` 逐字节相同，表中旧 rc 和行号应限定为 minute0 快照；R3-2 所引 `rc=0` 也没有证明发生过 O_EXCL 碰撞。不过，其新增碰撞测试形态正确，本轮独立碰撞实测也通过，所以这是证据表述问题，不是否定修复。

其余重点的核对结果如下：

- **历史 8 条整改：核对结果：无问题。** 15 个隔离代表例覆盖大小写身份、两跳软链、扫描失败拒写、O_EXCL 碰撞保留陌生文件、真实短写、顶层及目录叶子读取失败、四类 manifest 编码字段、三种根路径写法和精确悬空 exclude，全部通过。
- **rc 桶聚合：核对结果：无问题。** 128 种组合均符合 mismatch 优先、其次 missing、最后 0；已进入 unreadable 的发现不会被豁免桶压掉。问题发生在前面的漏归档和异常出口。
- **extra_allow 的执行优先级：核对结果：无问题。** `:851` 先处理 declared／exclude，`:854` 才查白名单；白名单也不参与 copy 摘要。交叉模式 `a/*x` 与 `a/y*` 虽漏过加载拒绝，但共同命中的 `a/yx` 仍归 exclude，没有被白名单夺走。
- **extra_allow 自身不扩大读取面。** 它只匹配已列出的路径；不过既有扫描路径及新增 hotkeys 读取会跟随软链，不能把整个校验器描述为“绝不读取树外”。隔离样例中的树外 main.js 软链确实被读取。
- **“任何原先 1 都不会变 0”必须加限定。** 对旧清单、空白名单及相同已归档桶成立；新增授权白名单后，原 extra 从阻断变为 0 正是设计行为，新翻转用例也明确验证了这个变化。
