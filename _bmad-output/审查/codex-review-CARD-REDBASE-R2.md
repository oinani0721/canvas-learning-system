> 批次: BATCH-2026-09-05-第十一批 · Z4-B · CARD-REDBASE-R2 round-1（首部由主 session 2026-09-05 按协议 §2.1 补记，正文一字未改）
> 模型: `gpt-6-astra`（stderr 实测） · reasoning_effort: `ultra`（stderr 实测） · codex: 未自证（stderr 无版本行）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`（第十一批手册规定形态；实参见车道 stderr）
> 审查绑定: `7283a8df..a5e0ce79d9a70e711934b827d7f62c052d281895`（正文首段自证）；（审后 c8611a89 +31 行零外审 → 第十二批 Y5-A 复审）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase` / `model: gpt-6-astra`

---

结论：**六处修改本身成立，但 E“全仓裸格式归零”不成立，仍有现行公开契约漏项。未找到本轮 BLOCKER/HIGH。**

审查绑定 `7283a8df..a5e0ce79d9a70e711934b827d7f62c052d281895`。未修改仓库文件；审查期间外部进程补写的 UAT 内容未纳入结论。

1. **A：PASS——零业务逻辑改动。**

   逐行检查三个 Python 文件，只有指定六处字符串变化。精确还原这六处文本后，三个文件的 AST 均与基线一致：

   ```text
   AST_EQUAL_AFTER_EXACT_TEXT_NORMALIZATION=True（3/3）
   DOCTEST_CODE_ASTS_EQUAL=True
   ```

   未找到业务代码读取这些 description/example 并参与判断。三个模型对旧值、新值以及任意字符串的校验结果相同。`backend/pytest.ini:8,19` 未启用源码 doctest 收集；即使解析该 Usage，改动也只是 `>>> print(...)` 后面的注释，可执行代码和预期输出均未改变。

   限定：OpenAPI 文档输出确实改变，不能把“零业务逻辑改动”理解成所有运行时元数据不变。

2. **B：PASS——当前内容与生成器输出一致；历史编辑方式无法据此证明。**

   使用指定 venv，通过原脚本 `--write` 生成至临时目录。比较结果：

   ```text
   JSON_DIFFERENCE_PATHS=["/info/x-generated-at"]
   ALIGNED_BYTES_EQUAL=True
   DRIFT: none (paths=193 schemas=353)
   ```

   对齐时间戳后，生成物与提交快照逐字节一致，SHA-256 均为：

   ```text
   33ca8ff6b6ef91ac7b1b689dff99af161b3a8089fd2e8289e42761c39d851ecf
   ```

   时间戳由 `scripts/spec-tools/check-openapi-drift.py:276` 每次刷新。**未找到只能由手工编辑解释的差异**；但相同内容和 `x-generator` 标记不能证明作者历史上从未手改。[复现日志](/private/tmp/redbase-r2-validation-5wmx2nb5/validation.log)

3. **C：PASS——六处源码对应四处 OpenAPI 契约变化，解释正确。**

   独立检查完整 schema 和 `$ref` 树：

   ```text
   SUBJECTINFO_SCHEMA_PRESENT=False
   SUBJECTINFO_REFS=[]
   SUBJECTINFO_DIRECT_ROUTE_FIELDS=[]
   ```

   `metadata.py:148` 将内部 `SubjectInfo` 字段转换为 `CanvasMetadataResponse`；未找到它作为任何端点的直接或嵌套 request/response schema。

   补充：`scripts/spec-tools/export-json-schemas.py:75,91,129` 的通用导出器确实能发现 `SubjectInfo`，但实跑导出的 example 已是新值；未找到独立遗留的 `SubjectInfo` 快照。因此这里没有额外漏改证据。

4. **D：PASS——保留“离散数学”的裁定更合理。**

   a) `metadata_models.py:59,172` 的路径，以及 `subject_resolver.py:46` 的输入都是“离散数学”。实际拼接逻辑在 `subject_resolver.py:201–205`。只把末段换成“线性代数”会制造输入与输出示例矛盾。

   b) 第三种可行方案是把整组请求路径、响应和 Usage 全部统一为“线性代数”；它没有明显收益，需要扩大文档修改范围。

   c) 未找到 `cs_61b` 与同一 example 其他字段的新矛盾。vault ID 与 subject 是独立维度；对应请求示例本来就同时写着 `vault_id="cs_61b"`、`subject="math54"`，见 `metadata_models.py:139–143`。Usage 可补充“当前 vault 为 cs_61b”这一前提。

   **溯源应精确化**：D16 原文是 `vault:<vault_id>[:<sub>]`，四段来自 resolver 后续组合逻辑；不能据此要求全仓合法 group_id 一律四段。依据：`_bmad-output/决策批注/D15-D16-用户主权与隔离方案-2026-05-04.md:209`、`subject_resolver.py:194–205`。

5. **E：FAIL——已找到明确反例。**

   全部逐处原文、行号及分类见[完整扫描清单：197 个相关命中行、74 个文件](/tmp/card-redbase-r2-E-complete-5bich1p7.md)。其中包含历史引用、兼容测试和两行非最终 group_id 的构造上下文，**不能当作 197 个缺陷**。

   | 位置 | 残留及裁定 |
   |---|---|
   | `backend/app/models/intelligent_parallel_models.py:286,287`；`backend/openapi.json:5880,5882` | **MEDIUM／既有、本卡遗漏**：公开 `subject_group_id` 仍说明 `{subject}:{canvas_name}`，示例为 `数学:离散数学`。实际生成已使用 vault 格式，见 `intelligent_grouping_service.py:198–214`；活动响应入口在 `intelligent_parallel.py:205`。 |
   | `frontend/src/stores/chat-store.ts:625`；`frontend/sidecar/sidecar.js:503` | **LOW／既有**：仍把实际 Graphiti group_id 描述为 `subject:canvasName`。 |
   | `openspec/specs/algo-memory/spec.md:13,14,15` | **LOW／既有**：现行主规格仍使用 `数学:微积分`。 |
   | `backend/app/api/v1/endpoints/errors.py:248`；`error_rebuild_service.py:149`；`backend/openapi.json:20387` | 保留 `cs_61b:main`。端点明确接受并归一化 legacy 输入，不能仅据字符串判成安全缺陷。 |
   | `canvas-vault/节点/UAT-2.5.X-test.md:35,63` | 既有 UAT fixture：`group_id: cs_61b:main`。 |
   | 目标提交 UAT 的 `:65,81` | **LOW／本卡引入的证据表述问题**：两种 `math54` 字面量的筛查不足以支持未限定的“裸格式归零”。 |

   扫描覆盖 6050 个 tracked 路径、5550 个文本，包括指定的 `frontend/`、`canvas-vault/`、`docs/`、`scripts/`、`.claude/`。其他文档、归档、迁移器和测试命中均已逐处列入附件。历史及兼容证据应保留其性质，不应为了“清零”统一替换。

6. **消费方：PASS——完成仓内检查，未找到旧两段误解析。**

   二次检查了 245 个包含 group 字段的源码文件。关键拆分的实际行为如下：

   | 位置 | 四段输入的处理 |
   |---|---|
   | `subject_config.py:336`；`group_id_migration_service.py:82` | `vault:` 输入直接返回，不进入旧格式拆分。 |
   | `vault_scope.py:97,315` | `[1]` 得到 `cs_61b`，用于 vault ID。 |
   | `backend/lib/agentic_rag/clients/lancedb_client.py:719–729` | 先剥离 `vault:`，再取首段，得到 `cs_61b`。 |
   | `backend/lib/agentic_rag/nodes.py:83–90` | `[2]` 得到 `math54`，用于 subject 比较。 |
   | `vault_scope.py:526` | 校验剩余各段非空，没有固定两段上限。 |
   | `backend/app/graphiti/group_id_compat.py:84–105` | 逐段编码及还原，四段无损。 |

   `review_service.py:1347` 拆的是 concept/card key，不是 group_id。上述实现均未被本卡修改。仓外消费方仍未验证。

7. **门处置：PASS——两项红点均为存量，但 215 的统计口径需纠正。**

   Ruff **0.15.9**，用 Git 原文和真实路径 `--stdin-filename` 复算：

   | 文件 | 基线／本卡完整 diff 行数 | 基线／本卡实际 `+/-` 内容行 |
   |---|---:|---:|
   | `metadata.py` | 0／0 | 0／0 |
   | `metadata_models.py` | 121／121 | 53／53 |
   | `subject_resolver.py` | 94／94 | 36／36 |
   | 合计 | **215／215** | **89／89** |

   全部增删内容逐行比较，仅 Field description 在格式化前后两行的字符串不同。`ruff check` 为 rc=0；`ruff format --check` 两边均 rc=1。**零新增格式漂移成立。**

   Pyright **1.1.411**：在临时项目导出基线源码和配置，共用同一 venv，分别检查基线及目标三文件：

   ```text
   BASELINE: rc=1, filesAnalyzed=3, errorCount=5
   TARGET:   rc=1, filesAnalyzed=3, errorCount=5
   BASELINE_MINUS_TARGET=[]
   TARGET_MINUS_BASELINE=[]
   ```

   五条均为既有：

   | 位置 | 诊断 |
   |---|---|
   | `metadata.py:76:16` | 未使用的 `os` |
   | `metadata.py:78:14` | 无法解析 `agentic_rag.clients.lancedb_client` |
   | `metadata.py:464:34` | 缺少 `subject`、`category` 参数 |
   | `metadata.py:673:40` | `None` 没有 `open_table` 属性 |
   | `subject_resolver.py:18:8` | 未使用的 `logging` |

额外复验指定三组测试：**81 passed，rc=0**；仓库写入尝试为零，Neo4j 禁连账本 `blocked=0 / unaccounted=0`。[测试日志](/private/tmp/redbase-r2-pytest-final-ze4_rh90/pytest.log)、[端口账本](/private/tmp/redbase-r2-pytest-final-ze4_rh90/guard-ledger.json)。

BLOCKER/HIGH 清零: 是

