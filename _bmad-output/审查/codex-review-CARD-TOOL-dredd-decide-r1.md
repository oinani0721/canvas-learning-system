**结论：检查选择代码没有发现削弱；但“任何版本都跑不通”和性能归因存在 HIGH 级证据问题，依赖归一也未形成实际安装约束。未发现 BLOCKER。**

已核对 `46ed18f1..e6f9aebc`：确实只有四个文件变化，两个 workflow 的 blob 完全相同。以下行号均以 **`e6f9aebc` 提交内容**为准；审查期间出现的未提交改动不纳入结论。全程未修改文件、启动应用或运行整套测试。

1. **HIGH｜问题 1：“任何版本都跑不通”的推理不成立。**

   **位置：**[test_openapi_contract.py:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/tests/contract/test_openapi_contract.py:59)、[裁决页:130](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md:130)。

   **判断依据：**官方 **3.39.16** 同时提供 `schemathesis.openapi.from_asgi`、四个 `schemathesis.checks.*_conformance` 属性，以及接受 `checks=` 的 `call_and_validate()`。这已经反驳“两种 API 不可能共存”。它不代表整套业务断言一定通过。[3.39.16 OpenAPI 导出](https://raw.githubusercontent.com/schemathesis/schemathesis/v3.39.16/src/schemathesis/specs/openapi/__init__.py)、[checks 导出](https://raw.githubusercontent.com/schemathesis/schemathesis/v3.39.16/src/schemathesis/checks.py)。

   对 **4.14.3** 的推断也有问题：`checks` 实现了动态 `__getattr__`；本机独立进程验证，四属性在加载前不存在，`load_all_checks()` 后全部存在。更关键的是，标准 Schemathesis pytest 插件在**收集阶段就自动加载检查**。因此裸导入后的 `dir()` 不能证明该文件在真实 pytest 入口下“每例必然 AttributeError”。[动态属性源码](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.14.3/src/schemathesis/checks.py)、[pytest 收集源码](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.14.3/src/schemathesis/pytest/plugin.py)。

   **建议处置：**删除“所有 3.x”“任何版本”“从未真正执行过”等断言。**需要额外证据：**改前实际命令、解释器及插件版本、插件启用情况、完整 traceback，才能认定本次修改确实改变了真实测试入口的失败形态。

2. **LOW｜问题 2：修法本身可接受，未发现检查削弱。**

   **位置：**[test_openapi_contract.py:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/tests/contract/test_openapi_contract.py:70)。

   **判断依据：**`get_by_names()` 按传入顺序逐名取值，缺名抛 `KeyError`，不会悄悄少取检查。本机验证返回四个函数均来自 `schemathesis.specs.openapi.checks`，与加载后的四个模块属性逐一为**同一对象**。[注册表源码](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.14.3/src/schemathesis/core/registries.py)。

   `load_all_checks()` 首次调用会注册内建检查；之后使用 Python 导入缓存。虽然注册全部检查，这次 `checks=` 仍只选择四项。函数体内重复调用没有发现显著性能问题，更没有证据能解释 20–50 秒耗时。

   **建议处置：**可以保留代码；改正其解释。这里证明的是**同一版本内检查选择等价**，不能扩写成跨大版本实现细节完全不变。

3. **MEDIUM｜问题 3：下限选择成立，但裸包名没有实现依赖归一。**

   **位置：**[pyproject.toml:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/pyproject.toml:20)、[requirements.txt:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/tests/contract/requirements.txt:16)。

   **判断依据：**4.0.0 已具备本次使用的注册表接口，因此 `>=4.0` 可以作为新写法的最低版本政策；理由应是统一使用这些接口，而非“所有 3.x 没有 `openapi.from_asgi`”。[4.0.0 checks 源码](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.0.0/src/schemathesis/checks.py)。

   但 requirements 中的注释**不会让 pip 读取 pyproject 约束**。按文件第 2 行执行 `pip install -r ...`，裸 `schemathesis` 可以接受已安装的 3.x；原来的 `>=3.19.0` 下限也被实际移除了。[pip 安装规则](https://pip.pypa.io/en/stable/cli/pip_install/)。

   “没有安装方”只能收窄为：**当前受版本控制的自动化中未找到消费方**。不能排除用户按第 2 行手动安装或外部脚本使用。现有 CI 也仍独立安装无版本包。另有 `uv.lock:107` 保留旧声明，但锁定版本满足新下限，不能据此宣称锁文件必然失效。

   **建议处置：**让可安装清单实际消费统一约束，或明确停止把它作为独立安装入口；不要用注释代替约束。

4. **MEDIUM｜问题 3 补充：新注释虚称 CI 已配置硬前置。**

   **位置：**[pyproject.toml:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/pyproject.toml:27)。

   **判断依据：**当前 [test.yml:72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/.github/workflows/test.yml:72) 只有包安装，没有 `python -c 'import schemathesis'`；目标测试也不在白名单。该注释与裁决页 §6.2“不动 test.yml”直接矛盾。

   **建议处置：**改为“原方案计划添加，重裁后未实施”。无需为迎合错误注释而修改 workflow。

5. **LOW｜问题 4(a)：假绿机制成立，但返回码和“无声”描述需要限定。**

   **位置：**[裁决页:145](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md:145)。

   **判断依据：**模块级 `importorskip` 后没有任何测试被收集，可得到 rc=5；与其他成功用例混跑且没有失败时，可以得到 rc=0。但 skip 仍存在于统计和 JUnit 中，准确说法是“未阻止步骤成功”。[pytest 退出码](https://docs.pytest.org/en/stable/reference/exit-codes.html)。

   “版本不对 → 1 failed / rc=1”并不通用：模块加载时的 `AttributeError` 通常是收集错误、rc=2；测试体中的错误才是运行期失败、rc=1。

   **建议处置：**保留机制说明，区分收集与执行阶段。**需要额外证据：**若声称已完成那 17 个文件的混跑复现，应提供完整命令、收集及 skip 清单、原始退出码；不能据现有材料认定 GitHub 已发生该假绿。

6. **HIGH｜问题 4(b)：不能把慢调用归因为“不是应用，是 ASGI 传输层”。**

   **位置：**[裁决页:157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md:157)。

   **判断依据：**4.14.3 的 ASGI 发送路径每次执行 `with asgi.get_client(application)`，使用的是 **`starlette_testclient.TestClient`**，进入和退出时执行应用 startup/shutdown。因此 `case.call()` 包含完整 lifespan，不能直接与普通端点直调比较。[ASGI 发送源码](https://github.com/schemathesis/schemathesis/blob/v4.14.3/src/schemathesis/transport/asgi.py)、[客户端选择](https://raw.githubusercontent.com/schemathesis/schemathesis/v4.14.3/src/schemathesis/python/asgi.py)。

   应用 lifespan 本身包含 MemoryService、Graphiti 等初始化和清理。一次“TestClient lifespan 7.1s”对照，未说明客户端完整导入名、退出阶段及冷暖状态，仍不足以排除应用耗时。

   **Hypothesis 也不能直接替罪：**若计时确实只包裹已生成 Case 的 `call()`，前置数据生成不在该计时内。真正缺失的是计时边界与分段证据。

   **建议处置：**改为“本机样本显示该调用路径较慢，瓶颈未定位”。**需要额外证据：**固定 Case、完整计时脚本、startup／请求准备／应用调用／shutdown 分段 profile，以及条件一致的重复对照。`206×20s` 只能标为假设性估算，不能证明全套必然耗时或“跑不完”。

7. **MEDIUM｜问题 4(c)：两个排除结论都超出证据。**

   **位置：**[裁决页:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md:171)。

   **判断依据：**端口 closed 不排除连接尝试、重试退避、其他地址或初始化等待；[health.py:142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/backend/app/api/v1/endpoints/health.py:142) 也存在按运行状态执行 Neo4j ping 的分支。

   在已知大方差下，22s 与 49s 的单组结果不能排除代理相关开销。`NO_PROXY='*'` 也不等于所有客户端配置均已受控。另一方面，ASGI 请求直接进入应用，继承 `RequestsTransport` 本身也不能证明存在真实 HTTP 代理超时。

   **建议处置：**改成“这些试验未支持该解释，尚不能排除”。**需要额外证据：**实际连接目标、重试事件、有效代理配置和交错重复对照。

8. **MEDIUM｜问题 5 的裁决依据：文档高估了现存 Dredd 覆盖，并误述 ASGI 边界。**

   **位置：**[裁决页:36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md:36)、同页 `:81–84`。

   **判断依据：**实际 [Dredd 命令:394](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/.github/workflows/api-spec-sync.yml:394) 带 `--method GET --names`。官方说明 `--names` 只列名称、**不发送请求**；GET 限制也不会执行 RAG POST。因此 payload 缺 `vault_id` 是潜在恢复问题，不能推出这条命令必然获得 422。[Dredd CLI](https://dredd.org/en/latest/usage-cli.html#names-n)。

   `from_asgi(app)` 会经过应用中间件及适用的鉴权依赖；“不过真实网络栈”不意味着“不覆盖中间件/鉴权”。是否充分验证鉴权场景，需要具体用例；现存 Dredd 配置也没有证明这一点。

   **建议处置：**按实际命令和用例描述覆盖，保留“两者不等价”的结论，撤回未经证明的覆盖归属。

9. **MEDIUM｜问题 5：不退役的处置恰当，但“单向覆盖面减法”不准确。**

   **位置：**[裁决页:176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md:176)。

   **判断依据：**用户已重裁，替代接入尚未验收，因此保持现状、另立诊断卡合理。但 Dredd 已 `if: false`，保留它保存的是**恢复选项和代码资产**；删除停用代码不会再次减少当前执行覆盖，也可从 Git 恢复。

   **建议处置：**将理由改为“替代方案尚未满足接入条件，按重裁保留恢复选项”。

   **第三条路：**后续独立卡可以先建立少量关键 operation 的确定性 HTTP/schema 检查，再把生成测试放入独立预算逐步扩面；不必把退役决策绑定于“206 个 operation 一次全部接入”。这只是后续候选方案，不要求本卡改 workflow。

**这次指定 diff 中未发现数据丢失、安全漏洞或越权写入级别的新问题。**


