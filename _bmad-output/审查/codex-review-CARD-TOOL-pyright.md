**结论：部分成立，未发现 BLOCKER。** 工具已可在本机运行，主要诊断数字能够重现；但安装链、运行版本结论和提交阻断率的表述需要修正。

审查绑定 `41470106 → d21b0bc4`，确认仅四文件变化，`lefthook.yml` 零改动。全程只读，未安装依赖、执行 Git hook 或修改文件。审查期间出现并持续变化的未跟踪 UAT，仅作为补充自述。

1. **HIGH｜`pyproject.toml:29`；`lefthook.yml:165–172`｜启用后确实会因存量错误阻断提交，但“约一半提交”没有被证明。**

   **判断依据：** hook 检查传入文件的全部内容，没有按新增行过滤诊断。我通过已安装的 Python 包入口检查未修改的 `backend/app/api/v1/endpoints/boards.py`，得到既有错误及退出码 **1**。因此“staged-only，所以旧债不阻断”不成立。

   两个比例复算正确：`111/263 = 42.21%`、`249/493 = 50.51%`，但它们是**含 error 的文件占比**。提交可能涉及多个文件，修改频次也不均匀，不能直接换算成提交被拦概率。

   **建议处置：** 明确接受“修改已有问题文件时，需要处理该文件诊断”的行为；将“一半提交”改成文件占比。实际提交阻断率**需要额外证据**：真实 staged 文件集合、修改频次和固定环境下的检查结果。

2. **MEDIUM｜`pyrightconfig.json:2–6`；`lefthook.yml:147`｜覆盖不对称属实，“门可达债约 1989”计算错误。**

   **判断依据：** 命令行文件参数覆盖配置的 include，故 `backend/tests` 可以被 hook 检查。根 `tests` 则在默认 include 内，却不在 hook glob 内。[Pyright CLI 说明](https://github.com/microsoft/pyright/blob/1.1.411/docs/command-line.md)

   本次复测：

   | 检查集合 | 文件数 | errors | warnings |
   |---|---:|---:|---:|
   | 默认 include | 304 | 592 | 86 |
   | `backend/app` | 263 | 424 | 85 |
   | `backend/tests` | 493 | 1396 | 107 |
   | 按当前 hook glob 构造的全部 tracked 文件集合 | **843** | **2089** | **207** |

   `1989 = 592 + 1396 + 1` 混入了 hook 不覆盖的根 `tests` 的 **168** 条错误及 backend 一级文件错误，又遗漏其他 **87** 个可达 backend 文件的 **269** 条错误。当前集合实际为 **424 + 1396 + 269 = 2089**。这仍是固定环境的集合扫描结果，不是未来提交的诊断上限。

   **建议处置：** 分别维护默认 include 与 hook 覆盖基线；修正汇总数字。一级两个文件的 glob 缺口属既有问题，可按本卡边界另卡处理。

3. **MEDIUM｜[requirements.txt:195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/requirements.txt:195)｜“根 requirements 没有安装方／声明从未生效”不成立。**

   **判断依据：** [scripts/deploy_epic12.py:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/scripts/deploy_epic12.py:168) 明确定位根 `requirements.txt`，第 175 行执行安装，第 298 行存在调用。CI 使用 backend 清单，不能证明仓库没有其它安装入口。

   当前受版本控制的配置及可执行入口中，**未发现 mypy 配置或命令调用方**；选择已有配置和 hook 的 pyright 有依据。但“以前从未安装过”属于历史断言，**需要额外证据**，不能从当前未安装推出。

   **建议处置：** 保留选择 pyright 的理由，删除绝对化历史断言。注释掉 requirement 对安装器没有歧义，等效取消依赖；人读层面的“已被替代”歧义见下一条。

4. **MEDIUM｜[pyproject.toml:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/pyproject.toml:25)；`requirements.txt:205、214`｜声明落点合法，但可重复安装链尚未闭合。**

   **判断依据：** 当前 `backend/.venv/bin/pyright` 可执行，hook 能找到它；但根开发安装说明仍只有 `pip install -r requirements.txt`，该清单既不装 mypy，也不装 pyright，随后却要求运行 pyright。

   `dev` optional extra 不会默认同步；uv 默认项目环境又是根 `.venv`，与 hook 优先查找的 `backend/.venv` 不同。注释中的手工 pip 命令能装到正确位置，但不消费 `uv.lock`，且 `>=` 不保证重现本次版本。[uv extras 文档](https://docs.astral.sh/uv/concepts/projects/sync/#syncing-optional-dependencies)、[环境路径文档](https://docs.astral.sh/uv/concepts/projects/config/#project-environment-path)

   **建议处置：** 补充消费声明／锁文件、安装到 hook 可见环境的明确步骤，并同步根安装说明。两条停用 mypy 声明可以删除，仅留一处迁移说明。无需因此强迫本卡扩展到 CI。

5. **MEDIUM｜[pyrightconfig.json:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool/pyrightconfig.json:21)｜3.11 目标合理，但“整仓真实下限”和“零代价”结论过强。**

   **判断依据：** 五组 error 数 **656／605／592／592／592** 全部重现；3.11、3.12、3.14 的诊断集合也确实逐条相同。差集为 **51 条 union、12 条 `context` 参数、1 条 `asyncio.timeout`**。

   源码确有无兼容分支的 `asyncio.create_task(..., context=ctx)`，例如 `backend/app/services/background_task_manager.py:208`；这些路径要求 3.11 API。它能证明旧版本不满足相关路径要求，不能证明整仓及依赖已经在 3.11 正常运行。[Python asyncio 文档](https://docs.python.org/3.11/library/asyncio-task.html)

   `requires-python >=3.9` 与这些 backend 路径存在实际冲突；但 union 诊断本身最多指向 3.10，还需考虑注解求值上下文。Ruff 的 `target-version` 控制规则及格式化目标，不能把它当成已经完成的兼容性验证。[Ruff 配置说明](https://docs.astral.sh/ruff/settings/#target-version)

   **建议处置：** 保留 3.11，改述为“对齐 CI 最低目标，当前诊断集合不变”。完整运行兼容性**需要额外证据**：3.11 环境的依赖安装、入口及关键流程验证。版本目标还会影响 stub 和条件分支分析，因此不宜承诺一般性的“零副作用”。

6. **MEDIUM｜`lefthook.yml:165`；`pyrightconfig.json:32`｜`--skipunannotated` 确实削弱职责，并非只消除旧债。**

   **判断依据：** `backend/tests` 的 **1396 → 343** 能重现；该选项跳过无注解函数的类型分析，新写入的无注解函数也同样受影响。降幅不能解释为误报率或已修复比例。[Pyright CLI 说明](https://github.com/microsoft/pyright/blob/1.1.411/docs/command-line.md)

   **建议处置：** 若采用，应明确记录覆盖削减，并验证新增错误的检出能力。当前 diff 未加入此选项，因此这是缓解方案的代价，尚不是已经发生的检查回退。

7. **LOW｜`backend/requirements.txt:14`；`pyrightconfig.json:13`｜文档漂移应修；JSONC 未发现实际消费方回归。**

   **判断依据：** `[tool.uv]` 应为 `[project.optional-dependencies]`，这是既有说明错误，不影响本次依赖解析。Pyright 1.1.411 正式使用 JSONC 解析，因此 `//` 合法；严格 JSON 解析器会失败，但仓内未找到实际这样读取该文件的消费方。[Pyright 解析源码](https://github.com/microsoft/pyright/blob/1.1.411/packages/pyright-internal/src/analyzer/service.ts)

   **建议处置：** 修正段名说明；若保持四文件边界，可另卡处理。JSONC 无需仅为 Pyright 修复；其它消费方影响标为**需要额外证据**，提供具体工具、配置或失败日志后再判断。

8. **LOW｜`requirements.txt:195`；`backend/.venv`｜安装历史及“新增 4 个 bin”缺少可复核证据。**

   **判断依据：** 共享 symlink 现状属实。当前包入口声明中，pyright 提供 **4 个**命令，nodeenv 另提供 **1 个**，合计 **5 个**。因此“两个包新增 4 个 bin”至少需要解释口径。现状与锁文件不能证明装前 227 包未动，也不能证明安装期间其它车道未受影响。

   **建议处置：** **需要额外证据**：带时间的装前／装后包与 bin 清单、安装日志；若判断并发影响或授权范围，还需当时占用记录及共享环境授权。不能据当前 diff 指控越权，也不能追认历史安装完全无副作用。

其余数字核验通过：

- `uv.lock` 确为 **+24／−0**；语义比较仅新增 pyright、nodeenv 两个包，既有外部包条目不变，根项目增加相应 dev 依赖关系。
- `type: ignore` 在 **`backend/app` 范围**两个提交均为 **22**，增量 **0**；不应省略这个统计范围。
- `typeCheckingMode` 未改，`reportMissingImports` 仍为 `true`。
- 所报 top-10 条数均一致：

| 规则码 | errors |
|---|---:|
| `reportUnusedImport` | 170 |
| `reportAttributeAccessIssue` | 103 |
| `reportArgumentType` | 72 |
| `reportMissingImports` | 69 |
| `reportCallIssue` | 54 |
| `reportUnusedVariable` | 48 |
| `reportOptionalMemberAccess` | 39 |
| `reportGeneralTypeIssues` | 12 |
| `reportOptionalOperand` | 5 |
| `reportReturnType` | 4 |

第十名存在并列：`reportOptionalCall` 也是 **4**。warning 分布 **60／14／12** 同样吻合。这些是检查器诊断计数，不代表逐条确认的真实缺陷数。

**本次四文件改动未发现数据丢失／安全／越权写入级别的问题；此前共享 venv 安装是否超出授权，需要额外证据才能判断。**


