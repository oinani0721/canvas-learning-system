> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-RV-G2-6 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-G2-6-r3.md)"`
> 审查绑定: `736eb490`（送审时 HEAD）。⚠️ **本轮之后代码又改了**（3 HIGH + 4 MEDIUM + 4 LOW 整改），故本存档**不绑合并态**；round-4 绑最终 HEAD。
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**本轮结论：0 BLOCKER / 3 HIGH / 4 MEDIUM / 4 LOW，整改尚未闭合。** 新引入的问题包括摘要碰撞、`ENOTDIR` 误报，以及提前 `continue` 丢失内容差异信息。

严格只读了指定五处材料。校验器全文的 Git blob 为 `238f62de…`，与 `736eb490` diff 对应。未修改工作树、运行安装脚本或访问 live vault；未运行会读取额外文件、创建夹具的 pytest。以下注明“实测”的结果来自纯内存探针、许可文件的 stat 或 `--help`；权限夹具与测试退化属于静态推演。

**BLOCKER：0。**

核对结果：未确认新的被审对象写入缺陷。核对了临时落点检查、`O_EXCL` 所有权标志、循环写满及 `os.replace` 的控制流；没有复跑需要落盘的验收，因此不将这一结论表述为全面证明“绝不会写穿”。

**HIGH：3。**

1. **【新引入】`backslashreplace` 不保持输入可区分性，会把真实差异变成相同摘要。**  
   位置：[scripts/verify_vault_install.py:616](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:616)，另见 `:670`。  
   复现思路：同名软链分别指向原始字节 `b"bad\xff-target"` 与 ASCII 字节 `b"bad\\udcff-target"`；前者经 surrogateescape 解码后，两者用当前编码方式得到完全相同的哈希输入，目录内文件名也有同类碰撞。**编码及 SHA 相等已实测**；因此“摘要只需确定性”不足以支撑内容比较。`:665` 同样有编码碰撞，但该分支已经登记 unreadable，不会单独造成假绿。

2. **【遗漏】普通条目、extra 和 hotkeys 仍有“查询失败即不存在／不扫描”的入口。**  
   位置：[scripts/verify_vault_install.py:832](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:832)、`:926`、`:994`、`:997`。  
   复现思路：让目标条目或扫描根的祖先不可搜索；目标 `exists()` 可把 unreadable 降为 missing、返回 1，extra 的 `is_dir()` 可直接跳过扫描，main.js 的 `is_file()` 可把无法查询误称“构建产物缺失”，后两者在其他桶为空时可返回 0。**这些是真漏，不属于作者登记的“main.js 确实不存在”例外。**

3. **【遗漏】叶子类型查询全部失败后仍返回 `("?:unknown", False)`，新 `continue` 根本接不到 unreadable。**  
   位置：[scripts/verify_vault_install.py:612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:612)，尤其 `:623`；类型过滤另见 `:543–547`。  
   复现思路：两个 copy 目录均可列目录但不可搜索（0444），其中同名文件内容不同；当 scandir 能提供目录项类型时，叶子 Path 谓词却因权限失败全部返回 False，两侧可得到相同 unknown 摘要并记 match。`_kind_ok()` 也可能把查询失败当成“不符合 dir/file”或“符合 nondir”，造成错误排除。这里需要能透传错误的**类型判断**，仅换存在性函数不够。

剩余入口不能一律判成同等缺陷：

| 位置（均为 `scripts/verify_vault_install.py`） | 判定 |
|---|---|
| `:834`、`:862` 源端 `exists()` | 不会因此变 match；`:862` 已归 unreadable、返回 2。三态主要纠正“模板源没有”的失实原因。 |
| `:847` skeleton `is_dir()` | 查询失败可能误记“不是目录／missing”；属于分类遗漏。 |
| `:521` `_iter_relative` 根类型 | 稳定状态下普通根已经通过 lstat；软链根原本就不遍历。机械替换没有同等收益。 |
| `:648` `_digest` 类型入口 | 应连同 HIGH-3 修；否则仍会落入 unknown、`bad=False`。 |
| `:698`、`:723`、`:1165` 身份／软链目标类型查询 | 仍会丢失失败原因，尤其 `:723` 可能漏记扫描失败并跳过递归；本轮未证明它能越过其余守卫造成写穿。 |
| `:1152`、`:1215` CLI 根目录／报告父目录检查 | 无法确认即拒绝、返回 3；换三态主要改善原因说明。 |
| `:1220` 报告 `exists()` | 可能漏硬链接预检，但后续换新 inode 保护旧 inode；不能仅据此判写穿。 |

**MEDIUM：4。**

1. **【新引入】`_entry_state()` 把确定不存在的 `ENOTDIR` 错归 unreadable。**  
   位置：[scripts/verify_vault_install.py:496](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:496)。  
   复现思路：已有普通文件 `a`，查询 `a/b`；`NotADirectoryError` 落入通用 OSError 分支，exact/glob exclude 均误阻断。**已用许可文件 `verify_vault_install.py/child` 实测该误分类及登记行为。**

2. **【新引入】`unreadable_here` 的提前 `continue` 同时遮掉同一 copy 项中已有的真实内容差异。**  
   位置：[scripts/verify_vault_install.py:889](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:889)。  
   复现思路：一个 copy 目录内，两侧同一叶子不可读，另一个可读叶子字节不同；原先为 unreadable＋content-drift，现在只剩 unreadable，报告显示 content-drift 为 0。退出仍为 2，但分类信息退化。  
   **原问题核对结果：无问题**——两侧不可读且摘要相等的项现在进入 unreadable，不再进入 match，也没有退出阻断集合。

3. **【遗留】stdout 编码、写入及退出时 flush 失败仍脱离四档契约。**  
   位置：[scripts/verify_vault_install.py:1275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1275)，help 出口见 `:1229`。  
   复现思路：`PYTHONIOENCODING=ascii python3 -B scripts/verify_vault_install.py --help` **实测 UnicodeEncodeError、退出 1**；把 stdout 接到读端已关闭的内存管道，**实测 flush 失败、退出 120**。UTF-8 可编码不等于 stdout 可写，故退出码契约仍不完全自洽。

4. **【遗留】hotkeys 的假拦下不限于 JS 转义，普通拼接表达式还能同时制造假放行。**  
   位置：[scripts/verify_vault_install.py:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:87)、`:1019`、`:1033`。  
   复现思路：`this.addCommand({id:"canvas:open-"+"dashboard"});this.addCommand({id:"canvas:other"});` 实际正则提取 `canvas:open-` 和 `canvas:other`，真实 `canvas:open-dashboard` 被报 orphan，未注册的 `canvas:open-` 反被放行。**提取结果已实测**；注释、普通文案中的同形字面量也仍可假放行。源码数量门同样不能证明运行时注册数。

**LOW：4。以下测试幸存均指单门，不代表全套测试幸存。**

1. **新增入口门能锁两个错误入口，但不能独立证明三态没有退化。**  
   位置：[backend/tests/unit/test_vault_install_manifest.py:1668](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1668)。  
   复现思路：仅让 `_entry_state()` 恒返 unreadable，两条指定路径仍在、rc 仍为 2，本门通过；缺正常／不存在对照。反过来，分别取消 glob 或精确入口登记，会分别破坏对应路径断言，**这部分承重已成立**。

2. **去重门锁住了一条输出，尚未锁住两个扫描来源确实都到达。**  
   位置：[backend/tests/unit/test_vault_install_manifest.py:1688](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1688)。  
   复现思路：跳过 `pending_archives*.jsonl` 那条扫描，另一规则仍产生 `.claude/hooks`，`len(hits)==1` 照样通过；少扫入口可以表现成去重成功。直接删除去重判断则会被当前计数断言发现，**此前“允许重复”的缺口已修**。

3. **新编码门没有覆盖三处编码修改，路径展开门也没有覆盖四个调用点。**  
   位置：[backend/tests/unit/test_vault_install_manifest.py:1714](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1714)、`:1729`。  
   复现思路：恢复校验器 `:665` 或 `:670` 的严格编码，现有 `odd-link` 文件名仍是 ASCII，该门继续通过；另将 `--report` 恢复直接 expanduser，当前仅测 vault／manifest 的门仍会通过。

4. **结论表仍有错误例子、旧口径遗漏及超出证据的断言。**  
   位置：[review-c4e6b165.md:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md:124)、`:126`、`:130`。  
   复现思路：`:124` 的“转义不影响可比性”被 HIGH-1 推翻；`:126` 的例子 `"canvas:a"` 没有转义、实际能提取；`:130` 称旧档已全部清除，但校验器 `:264` 仍写“不是承诺的 2”。§一已经限定为开工快照，其历史 rc 不应误当当前缺陷。

其余明确核对结果：

- **四档桶优先级：无问题。** 128 种组合实测全部符合契约；参数缺失、缺值、未知参数返回 3，正常编码环境下 help 返回 0。
- **`_expanduser()` 四处调用位置：无问题。** vault/source 经 `_resolve_dir`，report/manifest 直接检查错误，均在依赖操作前归用法错 3；这是控制流核对，测试覆盖缺口见 LOW-3。
- **三种完整、无转义的引号字面量及零命令阻断：无问题。** 前者实际提取通过，后者仍登记 unreadable；main.js 确实缺失时不计 rc 是已声明边界。
- **7 文件＋1 目录负控、generate 重叠行为门、hotkeys 行定位、其他阻断桶排除：无问题。** 从输入和断言核对，分别消除了此前指出的替代原因。
- **历史绑定、R3-2 碰撞证据收窄、grep 降为辅助检查：无问题。** 表述已纠正；未超出五处材料重新验证其引用的外部证据。
