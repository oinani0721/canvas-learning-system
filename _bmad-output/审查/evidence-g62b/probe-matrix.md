# CARD-G6-2b · AST 门探针红绿矩阵

- 「改前」门 = `1f249b33:backend/tests/unit/test_review_app.py` 里 `test_review_app_module_imports_are_closed` 的函数体本体 (git 取出后原样编译, 只注入假 `_ENDPOINTS_DIR`; 本脚本不抄写任何一份门逻辑)
- 「改后」门 = 当前 `_assert_module_closed()`
- 期望: 改前 **放行**(门瞎) / 改后 **被拒且拒因是「受保护名…」**(门抓住且抓对了原因)

| 探针 | 改前 (基线门) | 改后 (本卡门) |
|---|---|---|
| `<真实源码·未注入>` | ✅ 放行 | ✅ 放行 |
| `async-for-目标` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被for 目标绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `async-with-as` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被with…as 绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `class-名遮蔽` | ✅ 放行 | 🔴 拒: `受保护名 'list' 被def/class 名遮蔽 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `def-名遮蔽` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被def/class 名遮蔽 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `except-as` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被except…as 绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `for-目标` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被for 目标绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `lambda-kwarg` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被参数遮蔽 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `lambda-kwonly` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被参数遮蔽 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `lambda-posonly` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被参数遮蔽 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `lambda-vararg` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被参数遮蔽 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `match-rest` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被match **rest 绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `match-捕获` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被match 捕获绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `match-星号` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被match 星号捕获绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `with-as` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被with…as 绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `嵌套-自有定义遮蔽` | ✅ 放行 | 🔴 拒: `受保护名 '_js_json' 被def/class 名遮蔽 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `推导式目标` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被推导式目标绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |
| `海象` | ✅ 放行 | 🔴 拒: `受保护名 'json' 被海象绑定 — 调用点/接收者拼写检查会被架空 (round-4 HIGH-4b)` |

## 自检

- ✅ 全部探针具鉴别力 (旧放行→新拒绝), 验伪锚成立
