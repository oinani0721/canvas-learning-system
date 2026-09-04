# Codex 对抗性审查 Round-4 — CARD-DEBT-openapi-sync-R1 [BATCH-2026-09-04-第十批]

你是独立对抗审查者。LANE = 你的当前工作目录（`--cd` 已设为本卡车道 `card/x8-openapi`）。
本轮**只审一个面**：`scripts/spec-tools/check-openapi-drift.py` 的 `_normalize` /
`_tag_leaf` / `canonicalize` 三个函数的归一化策略，以及
`backend/tests/contract/test_openapi_snapshot_drift.py` 中与之对应的门。

背景（round-3 终裁为 FAIL，2 BLOCKER + 1 HIGH + 1 MEDIUM）：
- B1 = 语境切分（`VALUE_CONTEXT_KEYS`）把 x-extension / Link Object requestBody 内
  合法字面 `required` 误当 Schema 关键字排序 → 假绿；
- HIGH = 属性名恰为 `enum`/`const`/`default`/`example`/`value` 的**合法 Schema 子树**
  被反向误判成实例数据；
- B3 = 双命令抢 `.git/index.lock`（已由 `parallel: false` 处置，不在本轮审查面）。

round-3 的整改选择了**移除机制**：`_normalize` 现在不做任何 `required` 排序，
只做「dict 按 key 排序 / 数组一律保序 / 标量打 JSON 类型标签」。该整改**未经第四轮
确认**，本轮补上。

## 验证清单（每项 PASS / FAIL + 证据）

1. **B1 是否随机制一并消失。** 现实现里已无 `VALUE_CONTEXT_KEYS`、无任何按语境
   切分的分支。请确认：不存在任何输入能让 `_normalize` 改变某个 `required` 数组的
   元素顺序。若你认为存在，给出该输入与实际输出。

2. **HIGH 是否随机制一并消失。** 属性名为 `enum`/`const`/`default`/`example`/`value`
   的合法 Schema 子树，现在是否与其他子树受完全相同的处理。给出一个这种形态的
   最小输入与归一化结果。

3. **新代价是否如实声明且可接受。** 移除排序后，`required` 数组**顺序变化会被判为
   漂移**（门只严不松）。请判断：
   a) 这个方向是否只可能产生误红（多报），不可能产生漏报（少报）；
   b) FastAPI/Pydantic 在同一份代码上重复导出时，`required` 顺序是否稳定——若不稳定，
      这个门会在无代码改动时随机变红。请以 LANE 的实际导出实测（连续多次
      `--write` 到不同临时路径后逐次 `--snapshot` 比对），不要凭印象判断；
   c) docstring 里「误红的代价 = 开发者跑一次 FIX 命令」的说法与实际输出是否一致。

4. **`_normalize` / `_tag_leaf` 自身的新缺陷。** 重点看：
   a) `bool` 先于 `int` 判定的顺序是否在所有分支成立；
   b) `int`/`float` 同归 `"number"` 是否会吸收真实漂移（例：`1` → `1.0`）——这是
      有意为之还是缺陷；
   c) `("raw", value)` 分支在什么输入下可达，可达时是否会让不相等的两个值比较为相等；
   d) `canonicalize` 的 `deepcopy` 与 `VOLATILE_INFO_KEYS` 剔除是否覆盖全部易变字段。

5. **回归面**（只需确认，不必深挖）：`tests/contract/test_openapi_snapshot_drift.py`
   23 passed、`backend/scripts/openapi_drift_negative_control.py` 输出
   `NEGATIVE-CONTROL: PASS`、`--snapshot backend/openapi.json` 输出 `DRIFT: none`。

## 纪律

- **只读**。用 `LANE/backend/.venv/bin/python` 复现（禁连 7691 / 7687，禁 TestClient）。
- 每条结论给 `file:line` 或命令输出原文。新发现按 BLOCKER / HIGH / MEDIUM / LOW 分级。
- 判断不出来就写「未找到」，不要硬造。
- 末行必须给：`BLOCKER/HIGH 清零: 是|否`。
