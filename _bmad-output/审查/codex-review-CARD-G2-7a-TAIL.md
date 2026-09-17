> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 skills-writer · 卡 CARD-G2-7a-TAIL round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-TAIL.md)"`
> 审查绑定: `b3baf7d967692db0b172f5ebb4de9e4ae6357923`（该轮跑完时 HEAD 与之相同；本轮 MEDIUM 整改后 HEAD 前进到 `1946e40d`，故需 round-2 重绑）
> 会话头自证（抄 .stderr 中含 codex 版本 / `model:` / `reasoning effort:` 的三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

审查绑定 `b3baf7d967692db0b172f5ebb4de9e4ae6357923`。**hotkeys 无写端 FIFO 主修成立，发现一项新增 MEDIUM。**以下计数针对本卡新增问题，既有缺口另作说明。

- **BLOCKER：无。**
- **HIGH：无。**
- **MEDIUM：只读豁免会把展开后的写入旗标误判为只读。**
  - 位置：[backend/tests/unit/test_vault_install_manifest.py:806](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:806)。
  - 未被拦下的输入：`os.open(*[p, os.O_WRONLY | os.O_TRUNC], os.O_RDONLY)`。
  - 实际参数绑定为 `flags=O_WRONLY|O_TRUNC`、`mode=O_RDONLY`；helper 却把 AST 的 `args[1]` 当作 flags，返回 `True`，使零写门放行可截断文件的调用。
  - **纯内存核验已确认**，没有执行该打开调用；现有十条锚均通过，仍抓不到此输入。旧分支会拒绝 `Starred`，因此属于本卡新增缺口。建议拒绝无法确定位置绑定的参数展开，并补此负控。
- **LOW：无。**

对五个问题的核对：

1. **普通文件读取等价。** `verify_vault_install.py:1354` 两边均使用 UTF-8、严格解码和 `newline=None`：CRLF、CR 都归一为 LF；非法编码仍由 `:1356` 捕获。空文件仍读成空串，随后报 JSON 非法。对于内容稳定的普通磁盘文件，`O_NONBLOCK` 不会使无参数 `.read()` 截断大文件。

2. **非普通 hotkeys 有阻断分支。** `:1328-1346` 中，FIFO、字符／块设备、目录若打开成功，均由同 fd 的 `fstat` 拒绝；socket 等若打开失败，则进入 `OSError` 分支。软链跟随目标，悬空链或循环链走打开失败。均归 `unreadable`，没有新增仅写 note 的放行分支。但不能由 `O_NONBLOCK` 推出任意设备驱动的 open 都必定立即返回。

3. **60 秒合理但偏保守。** `test_vault_install_manifest.py:3170,3226` 给小型夹具充足余量，缺陷回归约一分钟后变红；五次本机计时不能保证所有慢机、冷启动环境都不误红。正常超时路径会由 `subprocess.run` 杀死并等待子进程，随后 `:3250-3253` 的 `finally` 删除 FIFO，未见该路径造成残留。

4. **稳定 FIFO 被拦住；并发替换仍有既有路径。** main.js 稳定为 FIFO 时，`:1384-1386` 提前返回，`:1388` 不可达。`_collect_extra`／`_walk` 只遍历目录；源、目标摘要最终由 `_leaf_digest` 重新验形态，稳定 FIFO 不读内容。  
   但若普通文件通过路径形态检查后被换成无写端 FIFO，`:719 read_bytes()`、`:756 open()`、`:1388 read_text()` 仍可能阻塞。尤其 `--source` 摘要在 `:1125-1126` 执行，早于新 hotkeys 门。这些是**既有并发替换缺口**，本卡没有消除。

5. **新增归桶及常规 fd 生命周期正确。** 打开失败没有取得 fd；`fstat` 失败和非普通文件早退各关闭一次；成功交给 `with os.fdopen` 后，正常返回及读取／解码异常均关闭。未发现当前固定参数的这些路径漏关或双关。hotkeys 的 note 如实说明未核对。main.js 非普通文件仅写 note、不贡献 rc=2，仍是已声明的既有 MEDIUM-3。

本次未运行 pytest、FIFO 落盘探针、hook、网络或数据库；未改动工作树。动态核验仅限纯内存 AST 与参数绑定。

BLOCKER=0 HIGH=0 MEDIUM=1 LOW=0
