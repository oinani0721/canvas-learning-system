> 批次: BATCH-2026-09-18-第十五批 · 车道 P2-A · 卡 CARD-DEADLETTER-PATH-ANCHOR round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEADLETTER-PATH-ANCHOR.md)"`
> 审查绑定: `bfeefadd`（车道 HEAD，代码面定稿；`git cat-file -t bfeefadd` = commit）
> 会话头自证（抄 .stderr 中含 codex 版本 / `model:` / `reasoning effort` 的三行，按内容 grep 定位、括注行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: gpt-6-astra` / `(L9) reasoning effort: ultra`

---
- **MEDIUM — `backend/tests/unit/test_dead_letter_path_anchor.py:44`**：以 `/app/app/core/failure_counters.py` 为**对照输入**时，两种父目录算法都正确得到 `/app`，但测试硬编码目录名 `backend`，会误拒正确的 `/app/data/dead_letter_episodes.jsonl`。

- **MEDIUM — `backend/tests/unit/test_dead_letter_path_anchor.py:82,113`、`backend/app/services/episode_worker.py:677`**：单例工厂是**门未覆盖的路径**，若工厂改为显式传入 `"data/dead_letter_episodes.jsonl"`，五条新门仍可通过，因为既不调用工厂、AST 也只检查默认参数，这是**未被拦下的输入**，但当前工厂确实无参构造。

- **LOW — `backend/app/services/episode_worker.py:230-231`、`backend/tests/unit/test_dead_letter_path_anchor.py:70-74`**：若作者的**负控输入**确实只是将 `else` 换成字符串字面量，转红会来自 `.parent` 的 `AttributeError`，不足以证明检测到 cwd 回归；保持类型的 `else Path("data/dead_letter_episodes.jsonl")` 才能验证该性质，而现有门确实检查真实写出及 cwd 下无 `data/`，并非夹具自行创建目标文件。

- **LOW — `backend/app/core/failure_counters.py:48`、`backend/app/api/v1/endpoints/traces.py:51,58,65`**：当 `/app/app -> /release/app` 时，词法锚落到 `/app/data`、解析符号链接后的锚落到 `/release/data`，使既有 `failed_edge_syncs` 项仍可能读写分叉，但 episode 两张表直接引用共同常量，不受此差异影响。

- **LOW — `backend/tests/unit/test_dead_letter_path_anchor.py:46`、`backend/app/services/episode_worker.py:231`**：以真实 `backend/data` 尚不存在为**对照输入**时，未打桩的默认构造器会创建真实目录，因此文件头“全部落 tmp_path”的声明不成立，四份 JSONL 哈希不变也不能排除这种目录写入。

- **LOW（核验边界）— `backend/app/services/episode_worker.py:226,230,311,316`**：显式 `None` 与不传参数当前语义一致，旧实现也已经把 `_file_path` 转成 `Path`，但允许读取面没有覆盖全部调用方，因此自报 pyright 零错误不能证明十五处调用或动态输入均已独立核验。

- **LOW（核验边界）— `backend/tests/unit/test_failure_observability.py:196,220,250,338`**：三条 EDGE_SYNC 用例的打桩可由片段和 diff 确认，但 `:338` 仅见测试签名，限定读取面不足以确认 DUAL_WRITE 方法体、排除第三类真实写点或验证目录级运行前后的行数与哈希自述。

- **LOW（注释与范围核验，无新增问题）— `backend/app/api/v1/endpoints/traces.py:55,82`**：`bug_log` 仍依赖 cwd 已如实说明，“每一条都是导入常量”限定于 `BACKLOG_FILES` 且与代码相符，指定 diff 中 `main.py`、`memory_service.py`、`bug_tracker.py`、`openapi.json` 均零改动。
