## 终裁

本轮审查面 **PASS**：BLOCKER 0、HIGH 0、MEDIUM 0、LOW 4。绑定 `card/x8-openapi@c99e37eabfe60a2bfc572ea76beb396653f4e1a6`。

## 验证清单

1. **B1：PASS**

   [_normalize](<repo>/scripts/spec-tools/check-openapi-drift.py:120) 只有 dict 排 key、list 原序递归、scalar 打标签三条路径；搜索 `VALUE_CONTEXT_KEYS/value_context/required sort` 为 exit 1、零命中。

   实测原序保持：

   ```text
   X_EXTENSION= {'x-literal': {'required': [('string', 'b'), ('string', 'a')]}}
   LINK_REQUEST_BODY= {'components': {'links': {'L': {'requestBody':
     {'required': [('string', 'b'), ('string', 'a')]}}}}}
   ```

   交换元素后 `compare=False` 并逐下标报差异。真实两端分别经过 JSON round-trip 与 `json.loads`，所以在生产 JSON 输入域内不存在改变 `required` 元素顺序的路径，见 [live 边界](<repo>/scripts/spec-tools/check-openapi-drift.py:91) 和 [snapshot 边界](<repo>/scripts/spec-tools/check-openapi-drift.py:219)。

2. **Round-3 HIGH：PASS**

   dict key 只参与排序，不参与策略选择。最小实测：

   ```text
   {"properties":{"enum":{"type":"object","required":["z","a"]}}}
   →
   {"properties":{"enum":{
     "required":[("string","z"),("string","a")],
     "type":("string","object")
   }}}
   ```

   `enum/const/default/example/value` 五种属性名全部得到相同子树处理，证据仍是 [_normalize:130-134](<repo>/scripts/spec-tools/check-openapi-drift.py:130)。

3. **移除排序的代价**

   - **3a PASS**：相对旧排序机制，保序只能扩大“不相等”集合，因此只会增加误红，不会新增漏报。此结论仅针对移除 `required` 排序，不涵盖另行声明的 number 等价策略。
   - **3b PASS**：使用字面路径 `backend/.venv/bin/python`，连续 5 个独立 `--write` 进程写不同临时文件，再用 5 个新进程逐份 `--snapshot`：
     - 5 次均 `WROTE: ... (paths=193 schemas=353, ...)`
     - 剔除两个 info 键后，5 份 SHA-256 均为 `389b8b671b7457a1bede3c81354d7766e85849a02e653b65399987da3a53b2f7`
     - 654 个 `required` 成员中有 281 个数组；路径和值顺序签名五次均为 `b2309581ba6a2137083389bb0a2c39178a1273438ae07efd6af398a58d056fcf`
     - 5 次比对均为 `DRIFT: none (paths=193 schemas=353)`
     
     当前车道共享 venv/Python 3.14.4 下未复现随机顺序。此证据不外推到 CI Python 3.11 或跨机器，脚本也在 [47-52 行](<repo>/scripts/spec-tools/check-openapi-drift.py:47) 如实声明。
   - **3c PASS，附 LOW**：受控反序产生 exit 1、4 条逐位差异，并实际打印：
   
     ```text
     FIX: python scripts/spec-tools/check-openapi-drift.py --write backend/openapi.json  (禁手改快照)
     ```
   
     对临时文件执行一次等价 `--write` 后即恢复 `DRIFT: none`，所以核心说法成立。输出实现在 [257-262 行](<repo>/scripts/spec-tools/check-openapi-drift.py:257)。

4. **函数自身**

   - **4a PASS**：bool 在 int/float 前判定，且所有嵌套标量最终都走该分支，见 [_tag_leaf:103-117](<repo>/scripts/spec-tools/check-openapi-drift.py:103)。实测 `True → ("boolean", True)`、`1 → ("number", 1)`，比较为漂移。
   - **4b PASS（有意策略）**：`1` 与 `1.0` 比较 clean，是明确选择且由 [测试:306-315](<repo>/backend/tests/contract/test_openapi_snapshot_drift.py:306) 钉死。它吞掉词法/Python 类型差异，但不会吞 `1 → 1.5`，也不会吞 Schema `"type": "integer" → "number"`；按本门声明的 JSON 数值语义，不定为缺陷。
   - **4c 生产 PASS，非 JSON helper 域有 LOW**：`raw` 仅在直接传入 bytes、自定义对象等非 JSON scalar 时可达。生产 CLI 两端不会产生这些类型。普通 `a != b` 经 raw 包装仍不等；但非 JSON 类型依赖 Python 自身相等规则，例如 `bytes` 与同内容 `bytearray` 实测 `compare=(True, [])`。带自定义 `__deepcopy__` 的敌意对象还可得到：
   
     ```text
     ORIGINAL_EQUAL=False
     DIRECT_TAG_EQUAL=False
     COMPARE=(True, [])
     ```
   
     这是 CLI 不可达的 helper 健壮性缺口，不影响本轮 B/H。
   - **4d PASS（当前车道）**：[canonicalize](<repo>/scripts/spec-tools/check-openapi-drift.py:137) 先 deepcopy，再仅删除顶层 `info.x-generated-at/x-generator`；嵌套同名键及其他扩展保留。输入不变测试见 [349-353 行](<repo>/backend/tests/contract/test_openapi_snapshot_drift.py:349)。当前快照全树扫描仅发现这两个生成器扩展；5 次 canonical hash 相同，未发现其他易变字段。

5. **回归面：全部 PASS**

   - `test_openapi_snapshot_drift.py`：`23 passed, 10 warnings in 0.85s`
   - 端口证据：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`
   - [negative control](<repo>/backend/scripts/openapi_drift_negative_control.py:197)：`NEGATIVE-CONTROL: PASS (3 mutants → exit 1 with named diff; timestamp-only → exit 0)`
   - 基线：`DRIFT: none (paths=193 schemas=353)`
   - 未构造 TestClient，未连接 7691/7687。以上是定向门，不代表 whole-suite/CI。

## LOW 新发现

- **LOW-1**：`raw` 对非 JSON 输入不做 fail-closed 类型验证，存在上述类型/自定义 deepcopy 碰撞；生产不可达。
- **LOW-2**：FIX 使用裸 `python` 且依赖仓库根 cwd；在 `backend/` 下打印路径不存在，也未钉定 lane venv。测试给出的 backend-cwd 命令实际是 [.venv/bin/python ../scripts/…](<repo>/backend/tests/contract/test_openapi_snapshot_drift.py:74)。
- **LOW-3**：23-test 门没有直接 fixture 钉住 Round-3 的 x-extension、Link `requestBody`、特殊属性名原形；当前全局保序实现足以通过本轮，但未来选择性分支回归可能绕过现有测试。
- **LOW-4**：仍有陈旧文字：测试 [175-179 行](<repo>/backend/tests/contract/test_openapi_snapshot_drift.py:175) 称 “sorted 而非 set”、[212-228 行](<repo>/backend/tests/contract/test_openapi_snapshot_drift.py:212) 仍称“语境切分”；负控 [11-12 行](<repo>/backend/scripts/openapi_drift_negative_control.py:11) 仍写 required 按集合排序；模块列四条规则但 [103、137 行](<repo>/scripts/spec-tools/check-openapi-drift.py:103) 写“规则 5/五条”。

只读完整性：四个被审/回归文件与 `backend/openapi.json` 的 working-tree blob 均与 HEAD 完全一致。审查期间另有 `_bmad-output/验收单/UAT-CARD-DEBT-openapi-sync-R1-2026-09-05.md` 并发变为 `M`；来源未判定，本轮未触碰或还原，不影响上述目标文件绑定。

BLOCKER/HIGH 清零: 是


