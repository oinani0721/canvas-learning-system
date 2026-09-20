> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-DEBT-10 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-10.md)"`
> 审查绑定: `4cc6a78c..390f25cf`（⚠️ **不绑最终 HEAD `8fe610bd`** —— r1 之后又整改了两轮; r2 因 Codex 配额耗尽未能产出, 见验收单 §9）
> 会话头自证（抄 `.stderr` 中含 codex 版本行 + `model:` 行 + reasoning 行, 括注行号; codex 0.153.3 把 `model:` 排在会话头第 5 行, 字面抄前三行会漏自证字段 —— 协议 §2.1, 本卡实测确认。stderr 本身不入库）:
> `(:2) OpenAI Codex v0.153.3` / `(:5) model: gpt-6-astra` / `(:9) reasoning effort: ultra`

---

**结论：目前不宜通过。确认 4 项 HIGH、6 项 MEDIUM。** 当前脚本和新测试均与 `390f25cf` 一致；未修改文件、未执行真机 `--apply`。

1. **HIGH — 两道门没有锁住 `verify()` 的调用链零写。**  
   [test_verify_install_manifest.py:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/backend/tests/unit/test_verify_install_manifest.py:244)、`:644`、`:893`。  
   **负控输入：** 在 `verify()` 中增加 `_write_report(harness.parent / "verify.log", "ran")`。内存 AST 实测仍为 **10 个写调用、相同的两个白名单 owner**；HOME 快照也看不到该树外写入。另实测漏判 `from builtins import open as fopen`、函数变量别名、`io.FileIO`；`:302` 还会把模块级 `class _write_report: open(...,"w")` 错当允许 owner。当前实现未发现这次写入，但“已被门锁死”的声明不成立。

2. **HIGH — 报告门可被大小写别名绕过，覆盖受管源文件。**  
   [verify_install_manifest.py:181](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/verify_install_manifest.py:181)、`:828`、`:690`。  
   **负控输入：** `--report <harness>/SCRIPTS/launchd/com.canvas.daily-review.plist`。本机只读实测 `scripts` 与 `SCRIPTS` inode 相同，但后者的报告检查返回 `None`；随后写报告会覆盖仓内 plist。`resolve()` 未消除大小写别名，`<home>/library` 同理。

3. **HIGH — HOME 确认门只检查根目录相等，漏掉实际写入 HOME 的祖先根配置。**  
   [verify_install_manifest.py:883](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/verify_install_manifest.py:883)、`:630`。  
   **负控输入：** `--home /`，自定义 manifest 的 wrapper 安装路径为 `~/Users/Heishing/Library/Application Support/CanvasReview/bin/daily-review-wrapper.sh`，执行非空重装计划。该路径通过 schema；`/` 不等于真实 HOME，且目标在 `/` 内，因此不带确认标志也能写真实安装副本。已验证解析与边界判定，未执行写入。

4. **HIGH — 报告会输出 plist 中的凭据内容。**  
   [verify_install_manifest.py:431](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/verify_install_manifest.py:431)、`:468`、`:744`、`:752`。  
   **负控输入：** `ProgramArguments=["/bin/bash","/safe/script","--api-key","SYNTHETIC_SECRET",7]` → 错误原因原样输出整组参数。合法的 `["/usr/bin/env","API_KEY=SYNTHETIC_SECRET",...]` 也会把赋值当作 `program_path` 输出；非法 `<integer>` 的异常还能携带原值。合成凭据进入最终报告已在内存实测。

5. **MEDIUM — 无法遍历安装路径被误报成 MISSING，退出码降为 1。**  
   [verify_install_manifest.py:534](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/verify_install_manifest.py:534)、`:449`、`:554`。  
   **复现思路：** `<home>/Library` 存在但不可遍历 → `lexists()` 吞掉错误返回 False，repo 件报 `MISSING`、程序体报 `SKIPPED`，external 件报缺失，最终退出 1。只读 `ENOTDIR` 对照输入已复现；这不是承诺的“读不动 → 2”。

6. **MEDIUM — 祖先目录检查与写入之间仍有软链竞态。**  
   [verify_install_manifest.py:630](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/verify_install_manifest.py:630)、`:645`、`:656`。  
   **复现思路：** 包含检查通过后，并行进程将 `<home>/Library` 换成指向树外的软链 → 后续临时文件创建和替换重新按路径解析，写入树外。这里没有固定父目录身份；此项依据代码路径，未执行磁盘竞态负控。

7. **MEDIUM — 不存在的解释器仍可得到 PROGRAM-MATCH。**  
   [verify_install_manifest.py:436](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/verify_install_manifest.py:436)。  
   **负控输入：** `Program="/does-not-exist/bash"`，`ProgramArguments=["/bin/bash","<内容正确的脚本>"]` → 仅凭 basename 认定解释器，直接校验第二个参数，external 件可以退出 0；真正执行的 `Program` 不存在却未被检查。

8. **MEDIUM — binary plist 的 NUL 程序路径逃出四档退出码。**  
   [verify_install_manifest.py:162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/verify_install_manifest.py:162)、`:493`。  
   **负控输入：** binary plist 中程序路径为 `/tmp/a\0b` → plist 解析成功，`os.stat()` 抛 `ValueError`，只捕获 `OSError` 的代码无法处理，最终 traceback、退出 1，而非解析／程序体错误档 2。解析与异常已在内存实测。

9. **MEDIUM — 三件 external 的程序体检查消失，相关测试仍可保持绿。**  
   [test_verify_install_manifest.py:490](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/backend/tests/unit/test_verify_install_manifest.py:490)。  
   **对照输入：** 将生产代码 `:569` 限制为只检查 daily-review、memory-health → neo4j-backup、qwen、reranker 的检查全部消失，但这里仅比较状态值集合，仍得到 `{"PROGRAM-MATCH"}`；其余程序体负控也未覆盖这三个 label。

10. **MEDIUM — “全量软链目标快照”漏掉目录软链。**  
    [test_verify_install_manifest.py:459](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/backend/tests/unit/test_verify_install_manifest.py:459)。  
    **负控文件系统状态：** `home/link -> A目录` 改成 `home/link -> B目录`，权限位相同 → `os.walk()` 将其列入 `dirnames`，该分支只记录 mode，前后快照相等。目录软链目标属于门未覆盖的路径。

其余关键判断：

- 当前 `verify()` 调用链未发现写入；默认 `UNREADABLE` 正确。四个现有 external 的直接读取失败还会触发程序体 `UNPARSEABLE`，不是 MATCH。
- 禁止判定取“字面 ∪ 物理”、允许判定只取物理，方向正确。报告范围缩至安装根与 `scripts` 的取舍本身可成立；**第 2 项才是让⑦实际失效的问题**。
- 稳定目录下，写满后 `os.replace` 能避免发布截断副本；叶子软链换入不会沿链覆盖目标。多件中途失败可能留下部分更新，但会返回 2，不能称为无信号。
- 旧程序内容不同会报 DRIFT；两侧源缺失可由 reason 区分。四个 external 真缺失在正文和摘要可见，退出 0 符合裁定。
- `_statuses()` 已拒绝空结果；`_program_statuses()` 全空也会被现有调用方拦下。**没有确认“空对空仍绿”；确认的是第 9 项漏核条目集合。**

本次采用源码核对、纯内存负控和只读路径验证；未运行会扩大读取面或创建夹具的完整 pytest。
