# 独立复核请求 — CARD-DEADLETTER-PATH-ANCHOR（BATCH-2026-09-18-第十五批 / 车道 P2-A）

你是独立审查者。只读，不要改任何文件，不要连任何数据库或网络服务。

## ① 背景与最小读取面（只读这些，不要扩散到别处）

本卡把 episode worker 的死信文件默认落点，从 **cwd 相对**的字面量默认参数
`"data/dead_letter_episodes.jsonl"`，锚定成 backend 绝对常量
`app.core.failure_counters.DEAD_LETTER_EPISODES_PATH`，并让读侧 `/traces` 直接
import 同一个常量。

缺陷成因：生产单例工厂 `get_episode_worker()` 是**无参**实例化，所以默认值就是
生产行为。进程从哪个目录启动，死信就落到哪个目录的 `data/` 下；读侧用的却是
backend 绝对锚，两侧只有在 cwd=backend 时才偶然对得上 —— 死信写了，`/traces`
读不到。

请只读以下内容：

1. `git diff 9c4e7e82 bfeefadd -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
2. `backend/app/services/episode_worker.py:196-245`（`DeadLetterStore` 类 docstring + `__init__` + `store` 开头）
3. `backend/app/services/episode_worker.py:305-320`（`GraphitiEpisodeWorker.__init__`）
4. `backend/app/services/episode_worker.py:668-688`（单例工厂 `get_episode_worker` / `cleanup_episode_worker`）
5. `backend/app/core/failure_counters.py:28-50`（三条锚常量：EDGE_SYNC / DUAL_WRITE / 本卡新增 DEAD_LETTER_EPISODES_PATH）
6. `backend/app/api/v1/endpoints/traces.py:36-105`（`_BACKEND_DIR` / `DATA_DIR` / `LOG_FILES` / `BACKLOG_FILES` 与两段注释）
7. `backend/tests/unit/test_failure_observability.py:170-250`（本卡打桩的两条 + 作为同形参照的 :208 那条）
8. `backend/tests/unit/test_dead_letter_path_anchor.py`（本卡新增门，全文 126 行）
9. `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` 中提到 T6-C 与 T10-D 的段落（L79、L102）

## ② 作者自述 —— 请独立核对，不要采信

1. 默认路径是**运行时**解析同一常量（`file_path=None` + 体内 `else DEAD_LETTER_EPISODES_PATH`），
   不是把常量当 def 期默认值。作者的理由是：def 期默认值绑定在函数对象的
   `__defaults__` 上，模块属性打桩对它失效。
2. `get_episode_worker()` 的 8 处生产调用零改动、行为一致（tips.py:635 / main.py:274,:386 /
   memory_service.py:462,:1541,:1822,:1958 / question_generator.py:1047 均未被本卡触碰）。
3. 读侧与写侧是**同一个对象**：`traces.BACKLOG_FILES["dead_letter_episodes.jsonl"] is
   failure_counters.DEAD_LETTER_EPISODES_PATH`，`LOG_FILES["dead_letter_episodes"]` 同。
4. 写脏面：收工时 `tests/unit` 目录级跑前后，本树 `backend/data/` 四个 jsonl 的行数与 sha256
   逐字相同（改前同一判据下 `failed_edge_syncs.jsonl` 有增量）。
5. 既有 15 处显式传 `dead_letter_path=` / `file_path=` 的测试调用语义不变（全部传 `str(...)`，
   签名由 `str` 放宽为 `str | Path | None`）。

## ③ 请按重要性排序回答的问题

0. 运行时解析后，**显式传 `None`** 与**不传**是否语义一致？是否有任何调用方依赖
   `self._file_path` 或 `dead_letter_path` 仍是 `str`（例如做过字符串拼接 / `os.path.join` /
   `.startswith`），使得类型由 `str` 放宽为 `str | Path` 后出现未被类型检查拦下的输入？
   （pyright 报 0 errors —— 请判断这 0 是否掩盖了什么。）
1. 新门 `test_default_store_writes_to_anchor_not_cwd` 是否**真的**绑在「cwd 无关」这个性质上，
   而不是绑在夹具自己写出来的那个路径上？作者跑过一段负控输入（把 `else` 分支改回相对字面量，
   其余不动），报告该门转红。请判断这段负控输入是否足以支撑该门的主张，以及是否存在
   **门未覆盖的路径**（例如某条代码路径下默认值仍可能落到 cwd）。
2. 三层 `.parent` 的锚（`failure_counters.py` 在 `backend/app/core/`）在打包 / 容器布局下
   （生产镜像是 `python:3.11-slim`，应用装在 `/app`）是否仍指向 backend？它与 `traces.py` 的
   `Path(__file__).resolve().parents[4]` 是否在所有布局下都指向同一个目录？两者一个用了
   `resolve()` 一个没用 —— 在存在符号链接的部署下是否会分叉？
3. `test_failure_observability.py` 本卡打桩的两条，是否漏了同文件内其它会写到真实路径的分支？
   （同文件 :338 处的 `DUAL_WRITE_DEAD_LETTER_PATH` 已有打桩，请核对是否还有第三类写点。）
4. `traces.py` 两段注释改写后，是否又出现「注释说得比代码管用」的情况？特别是
   `bug_log` 仍是 cwd 相对（`bug_tracker.py:89`，本卡未修）这一点是否被如实写明。
5. 是否越出了地盘白名单？`backend/app/main.py`、`backend/app/services/memory_service.py`、
   `backend/app/core/bug_tracker.py`、`backend/openapi.json` 必须零改动。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` 与**一句话**说明
在什么输入下会出问题。请使用这些措辞：**负控输入 / 对照输入 / 未被拦下的输入 /
门未覆盖的路径**。不要给出分级之外的总评语。

## ⑤ 边界

- 只读。不要连 Neo4j（7691/7687/7692 一概不连），不要写任何文件。
- 不评死信文件的有界 / 轮转策略（那是同车道下一张卡 P2-B 的范围）。
- 不评死信回灌（P2-C 的范围）。
- 不评 `bug_tracker.py` 的归属（无车道 territory，待裁）。
- 不评 `DEAD_LETTER_STORE_FULL_BODY` 默认值（用户待裁，任何卡不得改）。
