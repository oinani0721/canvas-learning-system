#!/bin/sh
# nodeid 提取: 必须是 `FAILED|ERROR <tests/...路径>::...` 形态。
# ⛔ 只写 '^(FAILED|ERROR) ' 会把 pytest 捕获的 logging 输出行(`ERROR    app.main:...`)
#    一并吃进来 —— 红基线头注释已写明「日志噪音行不计」。
grep -E '^(FAILED|ERROR) (backend/)?tests/[A-Za-z0-9_/.-]+\.py::' "$1" | sed -E 's/ - .*//' | sort -u
