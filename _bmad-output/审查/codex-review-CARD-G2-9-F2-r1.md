> 批次: BATCH-2026-09-11-第十四批 · 车道 T1 · 卡 CARD-G2-9-F2 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F2.md)"`
> 审查绑定: `08100483..ddd0251c`（该轮送审时的 HEAD；本卡末轮 r5 绑最终 HEAD `647ef77f`）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `L4: OpenAI Codex v0.153.3` / `L7: model: gpt-6-astra` / `L11: reasoning effort: ultra`

---

复核结论：**不通过，4 项 HIGH、3 项 MEDIUM。** 绑定 `08100483..ddd0251c`，HEAD 已核实。证据来自差异、调用链及原函数的纯内存求值；未修改文件、连接数据库或网络，也未运行 pytest、canary 或原负控脚本。

BLOCKER：该级别无。

**[HIGH] ① 指纹表不是所有已建表 vault 的必备记录，目录来源失效后仍会误删其他 vault。**  
定位：[lancedb_client.py:987](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:987)、同文件 `939、1990`。  
复现思路：`a_b` 通过 `index_canvas` 建立 `a_b_canvas_nodes`——该路径不写指纹；移走目录或使 `VAULTS_ROOT` 不可达，再由 active `a` 删除索引，V 缺少 `a_b`，其表重新归 `a`。等待 TTL 过期也不能补全。

**[HIGH] ② 初始化前生成的缺项缓存会跨数据库连接复用，使已经存在的指纹表也无法提供保护。**  
定位：[lancedb_client.py:1006](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1006)、同文件 `979、1258、1262、1928`。  
复现思路：根目录不可达、库内已有 `a_b` 数据表及指纹表；未连接的 active `a` 客户端调用 `index_canvas`，初始化前的解析先缓存 `V={a}`，随后连接并在五秒内运行自愈，仍错误认领 `a_b` 的漂移表。

这不需要新建 vault 或完成索引。模型加载还发生在自愈之后，因此作者的索引耗时论证不能保证窗口安全；旧目录恢复可见后继续沿用缺项缓存，也是另一条到达路径。

**[HIGH] ③ 新增 `name == v` 扩大了认领范围，并使与逻辑表同名的合法 vault 漏加前缀。**  
定位：[lancedb_client.py:1043](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1043)、同文件 `830、1036`。  
复现思路：`vault_id="vault_notes"` 解析逻辑名 `vault_notes`，改前得到 `vault_notes_vault_notes`，改后得到裸 `vault_notes`；另调用 `drop_vault_tables("file_fingerprints")` 会认领并删除 default 的裸指纹表，即使没有这个 vault 的目录。

纯内存求值确认，裸 `file_fingerprints` 同时被 default 和显式 `"file_fingerprints"` 认领；后者在旧规则下为假。因此“本卡只减少认领”并不成立。

**[HIGH] ④ 生产内部确实传递已解析名，新幂等守卫会造成双前缀及读、删、写目标分裂。**  
定位：[lancedb_client.py:830](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/lib/agentic_rag/clients/lancedb_client.py:830)、同文件 `2034、2253、2256、4068`。  
复现思路：V 为 `{a,a_vault}`，active 为 `a`；正常索引 `vault_notes` 首次解析为 `a_vault_notes`，删除旧行使用此名，而 `add_documents` 再次解析后写入 `a_a_vault_notes`。

搜索只解析一次，仍读原表；指纹却继续更新，后续增量索引可能跳过该文件。`index_single_file`、`index_canvas` 也存在二次解析。仅新增一个尚无表的 `a_vault` 目录即可触发，因此存量表确实会失去原有归属；拼接侧只告警不能解决这个回归。

**[MEDIUM] ⑤ drop 门缺少页外“自己的表必须被删”的对照，指纹读回的默认分页又被夹具掩盖。**  
定位：[test_lancedb_cross_vault_drop_g29f1.py:512](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:512)、同文件 `645、655`；客户端 `1382`。  
复现思路：仅把 `list_vault_tables` 恢复为默认十张枚举，现有 drop 断言仍可全部满足：前十张 `a_00..a_09` 被删，第十一张本来就应保留的指纹表进入首页，随后读回成功。

若前十张换成会保留的其他 vault 表，`_fingerprint_table_exists` 的默认分页会漏看指纹，`:656` 返回空基线而变红。门⑥、⑦分别只有三、四张表，没有覆盖这一形态。

**[MEDIUM] ⑥ 题述负控的首个红点可以区分，但不能据此宣称三个层次均被独立验证。**  
定位：[test_lancedb_cross_vault_drop_g29f1.py:707](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:707)、同文件 `596、716、825、830`。  
复现思路：按题述变异推演，朴素前缀在前提门 `596`、双向门 `716` 红；V 打空或仅含 active 时，前提门仍在 `596` 红，双向门却先在集合断言 `707` 停住；完整恢复“吞异常＋返回尝试数”则先在计数断言 `825` 停住，尚未到记账断言 `830`。

所以 traceback 可区分；负控③实际先测到计数，负控②在双向门中先测到集合。其他独立消费门仍能捕获 V 缺失后的误删，不能说负控②完全没有行为证据。这里是源码推演，未核实作者原负控的运行记录。

**[MEDIUM] ⑦ DELETE 消费方把删除失败解释成不存在，失败记录也没有进入响应，需移交 API 契约处理。**  
定位：[index.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t1-lance/backend/app/api/v1/endpoints/index.py:107)、同文件 `108、120`。  
复现思路：让所有目标表删除失败，客户端返回 `0`，接口返回声称“No tables found”的 404；若仅部分失败，接口仍返回 200，响应没有失败清单。

全仓符号检索未发现题述 endpoint 和 canary 之外的生产消费方，另有测试调用。canary 的整数接收方式不受类型变化影响，但旧“尝试数”注释已过时。**本条属于本卡之外的移交建议。**

其余核对：V=`{a,a_b}` 时题述三条归属结果正确；哨兵三态和 default 裸表分支保持原样，不会因 V 变成全表可见或恒空。跳过 `"default"` 没有新增孤儿表问题；裸 `canvas_nodes`、`default_*` 不被该分支认领属于原有口径。

正常可读的 YAML 显式 id 已按配置优先级纳入；读取失败则回退目录名，旧显式 id 没有指纹保护时仍可能遗漏。符合目录候选规则的空 vault 也会进入 V。固定被问 id 时，单纯扩大 V 的确只会减少认领，但这不能推出真实归属正确或不会丢数据。双向门的自身漂移表、实际删除数量对照足以排除“恒 False／删除完全没运行”，其证明范围不包括上述遗漏和命名碰撞。

LOW：该级别无。


