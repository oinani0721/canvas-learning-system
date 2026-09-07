> 批次: BATCH-2026-09-07-第十三批 · 车道 U9 · 卡 CARD-RV-G3-7 round-1（零代码卡 ⇒ D-15 下 1 轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-G3-7.md)"`
> 审查绑定: `da690bf8817adc4a84b20d59a1b8d8db4a578969`（= 开跑 HEAD `da690bf8`；**零代码卡**，复审对象 = `ecfcc3f1..08fed737` 补丁 + HEAD 六文件逐字节同态；终审绑定 `git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 恒空）
> 会话头自证（抄 .stderr 第 2/4/5 行含 model 行，stderr 本身不入库；本机 codex 0.153.3 的 model 行在第 5 行、不在前三行）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery` / `model: gpt-6-astra`

---

**结论：PARTIAL。未发现可确认的 BLOCKER／HIGH，但不能认可“5 条全部闭合”或“两处阻断级为 0 的论证已经完成”。**

已核实：HEAD 为 `da690bf8817adc4a84b20d59a1b8d8db4a578969`；指定补丁与 Git 实际差分完全一致；六文件在 `08fed737`、HEAD、当前工作区逐字节一致。本轮未修改文件、运行测试或连接服务。以下“必红”均指源码静态推演。

**MEDIUM**

1. **存在条件明确的反向误锁，普通缺失节点正控不能覆盖它。**  
   [review_service.py:210](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:210)

   当末级文件名超过目标文件系统限制、根本不可能存在对应节点，而系统返回 `ENAMETOOLONG` 时，代码仍判 `blinded=True`。相同输入会持续被门锁拦截。

   复审表 `:109` 将其仅列为“待验覆盖缺口”偏轻：**在返回该 errno 的目标文件系统上，这是 MEDIUM 功能缺陷**。本轮没有复现当前 Mac 的该现象，也不把 Linux 预期结果冒充实测。

   其他分流需区别看待：

   | 输入／异常 | 判断 |
   |---|---|
   | `ENOENT`、`ENOTDIR` | 继续找下一前缀，合理 |
   | NUL、不可编码的 `U+D800` | 无对应普通文件名，判 absent 合理 |
   | `EACCES`、`EIO`、`ELOOP` 等 | 无法可靠确认内容，保守拦截合理 |
   | 单个文件名超限产生 `ENAMETOOLONG` | 当前实现会误锁 |

   “目录不可见，但实际恰好没有节点”被保守拦截，是既定 fail-closed 的代价，不宜另判反向缺陷。

2. **新增探针已经看见文件，却仍返回“没有文件”。**  
   [review_service.py:213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/review_service.py:213)，同文件 `:277–287`。

   初次定位返回 `None` 后，复核 `os.stat` 如果成功，helper 返回 `False`；reader 随即返回初始化的 `found=False/governed=False/no_node_file`，没有读取已经发现的文件。

   这是**定位内部仍存在的 TOCTOU**，外部文件写者即可触发，不需要跨 `await`。应补入整改边界；不应称为一个全新独立 HIGH，因为旧逻辑也存在相近的文件创建窗口。

3. **“不覆盖任何既有数据”不足以支撑完整的零阻断定级。**  
   [review-08fed737.md:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-rv-g37/review-08fed737.md:218)；`review_service.py:2469、2473、595–598`。

   缓存 miss 是锁外观察。等待写锁期间，同 concept 的另一写者可以先写入；GET 取得锁后仍无条件写默认卡。因此，**检查时不存在，不等于写入时不存在**。

   五问应分别裁定：

   | 项目 | 本轮结论 |
   |---|---|
   | 数据丢失 | frontmatter 未被改；但投影中的并发覆盖没有排除，不能笼统写“否” |
   | live vault／Neo4j 写入 | 指定保存函数的直接写面确实只有投影 JSON |
   | 安全 | 指定路径未发现越权或外发行为 |
   | 指定裁判红 | 历史通过记录不能证明未覆盖的并发场景 |
   | 负控假绿 | 普通门锁正负控承重，但不能据此证明竞态无害 |

   **不能据此升级为已经证实的 BLOCKER；同样不能认证五问全部闭合。**另外，§5.3 的“无真相源 GET 仍写盘”是单线程也存在的写副作用，本身不属于第二处 TOCTOU。延期登记可以成立。

4. **pyright／格式“零新增”的独立证明仍未闭合。**  
   [review-08fed737.md:146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-rv-g37/review-08fed737.md:146)，同文件 `:65–66、283`。

   - `evidence-g37/pyright-baseline-vs-final.txt:1–7` 只有结果和方法摘要，没有两侧诊断集合、归一化及比较过程、同环境命令和最终树绑定。
   - 本卡 inventory 只有文件计数，不能重新计算新增诊断。
   - `(文件, rule, 归一化 message)` 多重集确实解决“新错落在未改行”的盲点；但同签名旧错消失、新位置出现仍可能抵消，不能无限推广为“每条最终诊断都是存量”。
   - 格式差分总行数 `702→608` 只证明净减少，**不能推出零新增**。旧格式证据同样只有多重集结果摘要。

   应改为：**方法方向成立，实际零新增的存档证明为 PARTIAL**。这不等于已发现新增类型错误。并且，不能一边拒绝无 rc 旧证据承担“通过”，一边用同类汇总认证本项闭合。

**LOW**

- **r2 LOW-4 仍有字段说明残留。**  
  [schemas.py:1079](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/models/schemas.py:1079) 仍将 `degraded_reason` 描述为 `card_state_persisted=false` 时产生，且只列两个原因；`:1067–1071` 在另一字段补充反例，不能消除本字段的错误限定。应判“成立但有残留”。

- **“下一次 GET 必然报分歧”过宽。**  
  复审表 `:228–232` 应限定为：manager 可用、节点仍存在且读取解析成功时，外层 due 采用 frontmatter；**确实不一致才报分歧**。一致测试本来就要求不报警。  
  缓存命中实际位于 `review_service.py:2513–2522`，不是文档所写的 `2570/2577/2579`。

- **部分证据锚点或解释有误。**  
  复审表 `:5` 称 r2 无 SHA，但原审查 `:4、10–11` 明确绑定 `ecfcc3f1`；`:54` 将 helper 的 `except ValueError` 引到 `:257`，实际为 `:200`。  
  `:222` 所引 reader 正控只能证明分类，真实写盘正控应引用测试 `:252–266`。

- **文档残留的两项判断应区别处理。**  
  `review_service.py:234–235` 漏列 `node_lookup_unreadable`，判 LOW 恰当。  
  但仅因 `except ValueError` 没注明“当前不可达”便判“新引入 LOW”，依据不足，**建议降为观察**：防御性捕获及其既有放行语义本身没有因此出错。

**已核实成立的部分**

1. **r2 五条整改逐项裁定：**

   | r2 项目 | 本轮裁定 |
   |---|---|
   | HIGH：目录定位失败放行 | 普通权限失败路径整改成立；保留上述输入及竞态边界 |
   | MEDIUM-2：承认 TOCTOU、收紧“一律” | 文档整改成立，窗口仍在 |
   | MEDIUM-3：类型／格式归因 | 条件收窄、显式 `None` 改动成立；零新增证明未闭合 |
   | LOW-4：公开字段说明 | 信息已补充，但本字段仍有残留 |
   | LOW-5：census／计数漂移 | 未全部闭合；20 仍错，UAT `:146、148` 仍写“四个目录” |

2. **作者对 r2 成因归属的纠正成立。**  
   本机 Python 3.14.4 标准库中，默认 `Path.exists()` 调用 `os.path.exists()`，后者捕获 `OSError/ValueError` 返回 False。目录权限失败实际走 `path is None`；仅修改外层 `except OSError` 不够。

3. **两个重点测试确实承重，但范围有限。**  
   [test_g3_7_truth_source.py:430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/regression/test_g3_7_truth_source.py:430)：helper 恒 True 会使 `:441` 失败。helper 恒 False 会使目录权限测试 chmod 后的 `:393` 失败。它们不能证明所有 errno 和并发时序正确。强制非零微秒的补强也成立，消除了原一致分支断言的退化。

4. **没有发现外层 `except ValueError` 导致合法 concept_id 永久放行。**  
   当前调用链的底层该异常已被 `exists()` 吞掉；helper 对 NUL／`U+D800` 判 absent 合理。可通过 surrogateescape 编码的低 surrogate 不会因“也是 surrogate”就一律走该异常分支。

5. **缓存及 dirty 链路的核心判断成立。**  
   缓存命中不再次保存；成功保存在 `:610` 清空 `_unpersisted_concepts`，不会把成功写入变成永久 dirty。磁盘失败则保留内存并标脏，后续其他成功全量保存可以清标。  
   **卡本身会留下，`card_state` 仍来自投影。**因此区分“不会固化”和“不会静默固化”必要；后一句仍需附上成功读取及实际 due 分歧的条件。

6. **18／20／21 的版本归因成立。**  
   Git 核数为 `18 → 21 → 21 → 21`，没有参数化放大。净增三条，改签名不算新增测试。两份 docs 在 `08fed737` 当场写成 20，判**同提交引入的 LOW 文档错误**准确；r2 的 18 在其绑定版本准确。

7. **rc 核数和 OpenAPI 来源归因成立。**  
   27 份 txt 中有效末行 rc 为 0 份、空 `rc=` 为 2 份，核数正确。应表述为“不能**单独**承担整条命令通过的正式证明”，日志内容仍有旁证价值；有 rc 也不自动证明绑定和增量正确。  
   OpenAPI 的单处描述漂移来自 `d209622d` 修改另一端点说明而未同步快照，归为**当前 HEAD 既有、非此次整改引入**成立；这不改变该检查仍为红的事实。


