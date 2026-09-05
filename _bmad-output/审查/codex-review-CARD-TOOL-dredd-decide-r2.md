**证据链仍未闭合；暂不把整份测试原样接入现有 CI 是合理处置，但“只能因为慢”“根因已定位”“全套约 12 小时”均不能按已证实结论登记。**

审查绑定 `46ed18f1..4cf0a3ba`，两个 workflow 确实零改动。UAT 为未跟踪文件，读取版本 SHA-256 为 `df18d1115f8355fd28a1bc0572b1c64dd5212ae9086298e18f54c93946378712`。审查期间出现的裁决页 §6.2 未提交更正已单独核对。全程未修改文件、启动应用或执行 pytest。

1. **HIGH｜自我更正没有覆盖仍在生效的表述。**

   **位置：**[裁决页](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md:86) `:86、151–171`；[UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:19) `:19–22、378–385、409`；[pyproject.toml:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/pyproject.toml:20)。

   **问题：**仍有“任何 3.x 都会 AttributeError”“4.x 上碎了”“装哪个版本都跑不起来”“也不是应用本身”“4.14.3 在交叠区外”等现行断言。UAT 首页甚至仍把“每次都跳过”当成历史事实。

   **判断依据：**这些文字直接违背 UAT 后文的真实 pytest 更正；4.14.3 的[动态属性实现](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.14.3/src/schemathesis/checks.py)与[收集插件](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.14.3/src/schemathesis/pytest/plugin.py)也支持更正后的结论。另有两处旧结果未同步：UAT `:238` 仍说 requirements 不写版本，实际已经是 `>=4.0`；`:409` 仍称“未被任何自动流程执行过”，但仓库存在 [contract-test.sh:18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/scripts/contract-test.sh:18) 等调用入口，历史是否执行不能由此断言。

   **建议处置：**直接修正当前摘要、表格、标题、注释和待登记条目；历史错误只作为明确标注的撤回记录保留。**无需为了完成更正而改写 `e6f9aebc` 历史**，因为 `4cf0a3ba` message 已明确引用并撤回它；当前树继续陈述错误才是未闭合之处。四项检查选择代码本身未发现削弱。

2. **HIGH｜“单 operation 209s，因此全套约 12 小时”不是可靠的性能预测。**

   **位置：**[UAT:196](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:196)、`:204、408`；裁决页 `:236`。

   **问题：**换成真实 pytest 入口，解决了入口代表性问题，却没有解决计时口径和总体代表性问题。

   **判断依据：**`in 208.70s` 是整个 pytest session 的耗时，包含收集、fixture、执行及报告，乘以 206 会重复计算一次性成本。该次输出是 `1 failed, 186 deselected`，与 206 operations 的分母差异尚未解释。“8 other explicit examples”代表九个显式 example 失败；显式 example 不计入 `max_examples`，且失败后不进入随机生成阶段，不能将它当成完整生成阶段的代表。[Hypothesis 文档](https://hypothesis.readthedocs.io/en/latest/reference/api.html#explicit-inputs)

   单个 health operation、个位数样本和 22s／49s 方差，也不足以建立所有端点的耗时下界；本机 Python 3.14 与 CI Ubuntu／Python 3.11–3.12 的环境差异仍未控制。

   **建议处置：**保留“本机选中一个 operation 的该次 pytest session 耗时 208.70s，并失败”。“70 分钟／12 小时”只能作为附带全部假设的情景算术，不能证明“必然跑不完”。**需要额外证据：**一致的收集清单、运行环境、分阶段耗时，以及代表性 operation 的重复测量。

3. **HIGH｜“不落地的真正理由只剩慢”遗漏了已经触发的独立失败门。**

   **位置：**[UAT:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:143)、`:200–207`；[conftest.py:141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/tests/conftest.py:141)。

   **问题：**`blocked=19` 被当成性能归因的旁证，却没有计入测试为何不能绿。

   **判断依据：**`pytest_runtest_makereport` 会把被拦截连接转换为测试失败；`:175–197` 的总账还保证非豁免 `blocked>0` 不能返回零。因此，**即使消除 DeadlineExceeded，只要这些连接仍发生，测试仍会失败**。复用客户端减少初始化次数，也不等于消除了被禁止的连接。

   **建议处置：**把“启动及存储隔离、符合现有规则的测试资源配置”列为独立接入条件。**需要额外证据：**在保留安全门的真实消费路径上，证明连接账符合要求，再验证耗时和契约断言；不能只调 deadline 或复用客户端便宣称问题解决。

4. **MEDIUM｜重复 lifespan 的机制成立；“应用初始化是主要耗时／根因已定位”仍未证明。**

   **位置：**裁决页 `:224–234`；[UAT:180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:180)、`:408`。

   **问题：**从“调用包含 lifespan”又扩大到了“主要耗时就是初始化”。

   **判断依据：**已核实安装源码：4.14.3 的 ASGI 路径每次新建 `starlette_testclient.TestClient`，进入和退出上下文确实运行 startup／shutdown。[ASGI transport 源码](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.14.3/src/schemathesis/transport/asgi.py) 但独立测得的 7.1s，不能直接解释另一次 20–50s 的主要构成。

   对照仍不匹配：HTTPX 的 `ASGITransport` **自身不触发 lifespan**；没有原探针中的显式生命周期管理代码，不能改口为“只跑一次”。[HTTPX 文档](https://www.python-httpx.org/advanced/transports/#asgi-startup-and-shutdown) `case.call()` 也包含 hooks、请求序列化和响应转换；schema 数据生成通常发生在 Case 交给测试体之前，不能凭猜测把全部时间归给生成请求体。

   **建议处置：**改成“已确认重复生命周期机制，耗时瓶颈尚未定位”。**需要额外证据：**固定 Case、同一客户端实现及生命周期条件，对同一次调用拆分 startup、序列化／hooks、请求、shutdown；对代理和连接重试也须保留未排除状态。

5. **MEDIUM｜Dredd 的新更正混淆了步骤失败和整个 job 失败。**

   **位置：**裁决页 `:51–54`；[UAT:275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:275)、`:391–393`。

   **问题：**`continue-on-error` 被写成 job 级，并据此认定“历史 24/24 全红与当前命令矛盾”。

   **判断依据：**实际 [api-spec-sync.yml:390](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/.github/workflows/api-spec-sync.yml:390) 将它设置在 **Run Dredd contract tests 步骤**；依赖安装、artifact 下载、服务容器等仍能使 job 失败。步骤级与 job 级具有不同范围。[GitHub workflow 语法](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepscontinue-on-error)

   **建议处置：**保留“Dredd 命令只列名称，没有形成契约执行失败门”；撤回“整个 job 不会失败”及所谓历史矛盾。**需要额外证据：**历史 run 的失败步骤和对应 workflow 版本，才能解释历史全红。

6. **MEDIUM｜不退役的处置合理，但当前覆盖保护的理由仍有残留。**

   **位置：**提交版裁决页 `:96–105、252–254`；[UAT:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:28)、`:262–263`。

   **问题：**仍称删除旧 job 是“白白少一层保护”，并将 middleware／鉴权覆盖独占地归给 Dredd。

   **判断依据：**job 已 `if: false`，删除不会再次减少当前执行覆盖，且可从 Git 恢复；ASGI 调用仍进入应用中间件及适用鉴权链。审查期间的未提交补丁修正了裁决页 §6.2，但没有同步其他现行表述。

   **建议处置：**保留“按用户重裁，替代方案未验收前保留代码资产和恢复选项”。第三条路成立：先建立少量关键 operation 的确定性检查，生成式测试另设预算逐步扩面；无需把退役绑定于一次接入全部 operation。

7. **MEDIUM｜三份快照真实一致，但不足以证明全部实验“未污染”。**

   **位置：**[UAT:318](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:318)。

   **问题：**对账遗漏真实写入目录，而且末次快照没有覆盖后续实验窗口。

   **判断依据：**我独立核对了三份原始文件，均为 342 行，SHA-256 均为 `f96c12450f4c1e47f37eea631237bb10130d59863bd6f58212ad3ba11915cdd7`。但它们只覆盖根 `data/`。

   应用 startup 调用的 [cost_tracker.py:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/app/middleware/cost_tracker.py:35) 默认写 `backend/data/llm_call_logs.db`；该文件出生及修改时间为 **08:15:47（北京时间）**，位于 before **08:15:07** 与 after **08:46:09** 之间，且被 Git 忽略。另一默认状态目录为 [backend/app/data](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/app/services/vault_index_orchestrator.py:127)，其中 pending 文件出生于 **09:26:12**，晚于最后快照 **08:47:36**。

   **建议处置：**收窄为“三个时点根 `data/` 的普通文件内容及目录清单一致”。**需要额外证据：**全部实验的时间绑定、有效存储路径以及遗漏目录／外部存储的前后证据。文件元数据支持存在遗漏生成物，但不能单凭时间认定创建进程，更不能推出数据丢失或越权；缺少历史基线时也不能事后补拍冒充对账。

8. **LOW｜importorskip 的条件性假绿机制成立，但演示不是实际 CI 负控。**

   **位置：**裁决页 `:181–191`；[UAT:145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md:145)、`:256`。

   **问题：**裁决页仍无条件写“整步就是 rc=0”“无声吸收”，负控说明仍称已证明硬前置的必要性。

   **判断依据：**模块级 skip 与其他通过用例混跑，且没有其他测试或 session 钩子失败时，可以得到 rc=0；skip 仍可见于统计和 JUnit。这个一般机制不要求完整混跑才能推理成立。[pytest 退出码](https://docs.pytest.org/en/stable/reference/exit-codes.html) 但真实 workflow 已有不吞错的 schemathesis 安装步骤，目标文件又尚未接入，因此不能据探针认定当前 GitHub 曾发生该假绿，也没有验收“硬前置缺包时变红”。

   **建议处置：**统一采用 UAT 更正后的条件性表述，负控标为“机制演示”。硬 import 是合理防御方案，但不是唯一方案；未来接入时需用实际安装链、白名单及原始退出码完成负控验收。

（1）这次指定代码 diff 中，**未发现数据丢失／安全漏洞／越权写入级别的新问题**，但现有对账不能证明此前所有实验均未产生持久化副作用。

（2）“不把合约测试接进 CI”的结论，我判为 **证据不足但方向对**，限定为“本卡暂不将现有整份测试原样接入”，不能扩大为合约测试无法进入 CI。


