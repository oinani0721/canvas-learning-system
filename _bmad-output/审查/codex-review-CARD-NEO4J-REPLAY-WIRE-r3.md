> 批次: BATCH-2026-09-11-第十四批 · 车道 T6 · 卡 CARD-NEO4J-REPLAY-WIRE round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-NEO4J-REPLAY-WIRE-r3.md)"`
> 审查绑定: `d90f5a6723c91709c864cf42ab0c317ada217c46`（该轮 B0/H0 曾满足 D-15，但本轮整改在 r4 被查出引入回归）
> 会话头自证（抄 .stderr 第 4 / 7 / 11 行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**旧 HIGH-1 的初始目标端口绕过已关闭；本轮发现 MEDIUM 2、LOW 2。** 满足所引 D-15 的 B/H 数量条件，但启动接线的验收缺口仍未关闭。

审查绑定 `d90f5a6723c91709c864cf42ab0c317ada217c46`；未改文件、未连接数据库。以下区分纯内存复现与静态结论。

1. **MEDIUM — 清理身份仍会跨门匹配。**  
   [test_neo4j_replay_wire_t6b.py:142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:142)，同文件 `:129–132`。  
   **对照输入／复现思路：**另一 canvas 的无边 `Episode {type:'scoring', group_id:'vault__other__other_t6bgate_canvas'}` 同样满足新尾缀条件；前四条也匹配 `t6bgate2_*`，或同门并行另一 UUID 的节点。整改缩小了删除范围，但没有建立精确身份约束。已核对字符串匹配，未执行删除。

2. **MEDIUM — 启动接线仍有被跳过的路径，现门无法检出。**  
   [main.py:416](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:416)、[test_neo4j_replay_wire_t6b.py:255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/tests/integration/test_neo4j_replay_wire_t6b.py:255)。  
   **负控输入／复现思路：**`:392` 的 `backfill_vault()` 抛异常，控制流直接进入 `:462`，暂存回灌不会执行；摘掉 `:416` 的调用，当前管理端点测试也不能检出，因为它不运行 lifespan，且在 `:228` 替换生产单例。保留 round-2 MEDIUM-3；登记为**门未覆盖的路径**不能算验收通过。

3. **LOW — `exists()` 仍使读取失败静默变成零积压。**  
   [fallback_sync_service.py:152](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:152)，另见 `:171`。  
   **对照输入／复现思路：**按题述 Python 3.14 行为，父目录权限错误使 `exists()` 返回 `False`，函数直接返回零，绕过 warning。这与代码承诺的“读取失败可通过日志区别于真空”冲突。登记准确，但仍是 LOW 缺陷；本轮未制造权限目录，仅核对该控制流。

4. **LOW — JSONL 计数把合法字符串中的 Unicode 分隔符当成额外记录。**  
   [fallback_sync_service.py:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/services/fallback_sync_service.py:161)。  
   **负控输入／复现思路：**`json.dumps({"concept":"a\u2028b"}, ensure_ascii=False) + "\n"` 是一条合法 JSONL 记录，但当前 `splitlines()` 计为 **2**；对照输入 `"ab"` 计为 **1**。已在工作树 Python 3.14.4 中用实际计数表达式纯内存复现，U+0085、U+2029 同样如此。这是全量 diff 中新增发现。

对其余问题的判断如下：

- **⓪ 端口修复成立，证明范围是初始目标地址。**  
  探针 `:78–85` 与契约 `:314–317` 都先拒绝空结果，再要求所有端口属于实际白名单 `{7692}`。实际调用 helper，并对照 Neo4j 6.1.0 的解析入口，确认前导零、默认端口、IPv6、大小写／空白及 routing 多地址中的现网端口均被拒绝；非支持 scheme、非空 userinfo 也被拒绝。空 userinfo `bolt://@127.0.0.1:7692` 被驱动接受，但目标仍为 7692。
  
  准确说法是：helper **使用驱动的 `Address.parse/parse_list`，手动复现 URI 检查与分流**，没有直接调用完整 `parse_neo4j_uri`。空 routing URI 存在更保守的解析差异，调用方仍拒绝。`:326` 剩余字符串判断只是旧判据的负控自证，不是第三处保护判据。routing 服务器随后返回的地址属于此次纯解析复核**未覆盖的路径**。

- **① 空异常文本问题已修；不能据此确认所有内部失败。**  
  [main.py:433](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j/backend/app/main.py:433) 正确识别 `error=""`，覆盖允许片段中展示的三个外层捕获分支。三个子同步主体在限定读取面之外，因此“内部吞异常后返回不含 `error` 的普通 stats”仍未核实，不计成已证明的缺陷，也不宣称全部关闭。

- **② Punycode 的实际行为仍未核实。**  
  物理 group 转换实现未在允许读取面中展开。若转换改变字面尾缀，当前兜底查询就漏删；不能仅凭注释确认尾缀随环境保持不变。上面的 MEDIUM 已有无需该假设的明确对照输入。

- **③ 捕获集本身可以接受。**  
  `ValueError` 覆盖 JSON 解码、UTF-8 解码和整数位数限制异常；`data.get()` 位于 `:190`、在 `try` 外，不会被该捕获集吞掉。没有依据要求把 `MemoryError` 等资源失败也一并吞掉。需要保留的是上述 `exists()` 缺口。

- **⑤ 接受不改，但限定证明范围。**  
  首轮四项绝对值确实挡住“完整重复回放产生两个关联 Episode”的负控输入。`count(e)` 不去重还会使重复 `SCORED` 边触发失败，不能单独视为放行漏洞。  
  **门未覆盖的路径：**第二次额外生成随机 ID 的孤立 Episode，或只连接 `othergate_node` 的 Episode，计数仍可保持四项各一；多标签也受 `labels(n)[0]` 限制。因此该门不能证明全图无重复，但目前没有生产路径证据支持另加一条幂等缺陷。

端点 description 已消除“三链第二次计数一律归零”的文本冲突。

**计数汇总：BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 2。**


