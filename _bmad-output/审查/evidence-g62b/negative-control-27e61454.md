# CARD-CX-G6-2b-R1 · 负控: 真实上一版 `27e61454` 换入（完成条件 b）

> 负控体是**真实的上一版实现**（时间戳锚），不是手工变异体。手工变异体只能证明
> 「我造的这个坏法会被抓」；换真实上一版证明的是「这道门相对**它实际取代的那个**
> 实现有独有承重」—— 后者才是「新门值不值得存在」的判据。

`27e61454 → HEAD` 的 review_app.py 差异只有代际锚这一件事（5 个耦合点全覆盖，无夹带），
所以门的红绿变化可以唯一归因到锚的实现。

## 一 三段 sha256

| 阶段 | sha256 |
|---|---|
| 换入前（当前版，`92734207` 后） | `b7e4a8d94f82b1a6a8e9b07ff636690801d5d1b53c071d21273562def1224a77` |
| 换入后（`27e61454` 版） | `4ff348f19d6082908ca19aa66f2016292a611a58233dd2bdccc5d74a9e432b73` |
| 还原后 | `b7e4a8d94f82b1a6a8e9b07ff636690801d5d1b53c071d21273562def1224a77` |

- 换入体校验：`git show 27e614541a3f4d14ca6cf9b8693e66015db566a9:backend/app/api/v1/endpoints/review_app.py` 的 sha = `4ff348f19d6082908ca19aa66f2016292a611a58233dd2bdccc5d74a9e432b73` → 与「换入后」**相同** ✅（确实换成了那一版，不是别的东西）
- 还原校验：换入前 vs 还原后 → **逐字节相同** ✅
- 换入前 vs 换入后 → **不同** ✅（换入真的生效了；相同则整个负控是空跑）

## 二 三条点名门的红绿

### 换入前（当前版）
```
PASSED test_review_app_module_imports_are_closed
PASSED test_js_stale_get_cannot_settle_rebuild
PASSED test_js_causal_anchor_survives_same_millisecond
======================== 3 passed, 10 warnings in 0.66s ========================
```

### 换入 `27e61454` 后
```
PASSED test_review_app_module_imports_are_closed
PASSED test_js_stale_get_cannot_settle_rebuild
FAILED test_js_causal_anchor_survives_same_millisecond
=================== 1 failed, 2 passed, 10 warnings in 0.65s ===================
```

同毫秒门的失败断言原文（拒因身份——只断言「红了」会把「因为别的原因而红」也算成绿）：
```
E   AssertionError: node --test 失败:
E     ✖ 冻结时钟 → 旧 GET 与 rebuild 同毫秒, 仍无权结算 (9.590208ms)
E     ℹ tests 1
E     ℹ suites 0
--
E       AssertionError [ERR_ASSERTION]: 同毫秒不是「更晚」— pending 必须留着
E           at TestContext.<anonymous> (file:///private/var/folders/vq/gssw8vy54671lh9nlqc_ft2w0000gn/T/pytest-of-Heishing/pytest-16932/test_js_causal_anchor_survives0/case.test.mjs:34:12)
E           at async Test.run (node:internal/test_runner/test:1313:7)
E           at async startSubtestAfterBootstrap (node:internal/test_runner/harness:385:3) {
```

### 还原后
```
PASSED test_review_app_module_imports_are_closed
PASSED test_js_stale_get_cannot_settle_rebuild
PASSED test_js_causal_anchor_survives_same_millisecond
======================== 3 passed, 10 warnings in 0.62s ========================
```
