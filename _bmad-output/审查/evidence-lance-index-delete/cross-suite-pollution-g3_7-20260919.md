# 既有跨测试污染：tests/unit 先跑会让 tests/regression/test_g3_7_truth_source.py 全族变红

> 绑定 HEAD `698641ec` · 2026-09-19 · 车道 P1 · **非本卡引入**（本卡改动面与该文件零交集）

## 三组实测（同一 HEAD，只差跑法）

| 跑法 | failed | 存档 |
|---|---|---|
| `pytest tests/unit -q -p no:cacheprovider -rfE`（基线跑法） | **32** | `unit-close-20260919T045830.raw.txt` |
| `pytest tests/regression -q -p no:cacheprovider -rfE` | **0**（1913 passed, rc=0） | `regression-close-20260919T050431.raw.txt` |
| `pytest tests/unit tests/regression -q -p no:cacheprovider -p no:randomly` | **45** | `unit-regression-at-head-20260919T044425.txt`（⛔ 已标作废，口径另有两处错误） |

32 + 0 = 32，合跑 45 ⇒ **多出的 13 条全部落在 `tests/regression/test_g3_7_truth_source.py`**：

```
test_body_line_is_not_mistaken_for_truth_source
test_gate_blocks_write_on_malformed_fsrs_due
test_gate_blocks_write_when_truth_source_exists
test_get_fsrs_state_agreement_is_not_reported_as_divergence
test_get_fsrs_state_frontmatter_wins_on_divergence
test_http_get_forwards_truth_source_and_degraded
test_production_reader_reads_seeded_frontmatter
test_record_review_degraded_reasons_are_additive
test_record_review_flags_divergence_but_keeps_computed_schedule
test_record_review_reports_unparsable_truth_source
test_record_review_reports_unreadable_truth_source
test_unreadable_node_dir_fails_closed
test_unreadable_node_file_fails_closed
```

## 归属：非本卡

本卡 `5e0f87b7..HEAD` 改过的代码文件与该测试面**零交集**：
`index.py` / `group_id_compat.py` / `episode_worker.py` / `memory_service.py` /
`lancedb_client.py` + 5 个 unit 测试文件。`test_g3_7_truth_source.py` 测的是 FSRS
真相源（frontmatter vs 事件账），与 LanceDB 删索引、组族 builder 均无调用关系。

## 未证明（⛔ 不要把本文件当成根因诊断）

1. **未证明污染源是谁**：只证明了「先跑 tests/unit 会让它们红」，没有二分定位到具体是哪个
   unit 测试（候选方向：进程级缓存 / ContextVar / monkeypatch 未还原 / lru_cache 未 clear /
   cwd 变更）。
2. **未证明 `-p no:randomly` 不是共同因**：合跑那次带了该参数，两次单跑都没带。
   严格归因需要「合跑 + 不带 no:randomly」与「单跑 + 带 no:randomly」两组对照，本次未做。
3. **未证明它在别的 HEAD 上同样成立**（未在 `5e0f87b7` 或 B15_BASE 上复现）。

⇒ 登记移交，建议单开卡做 2×2 对照定位。本卡只按协议 §3 口径确认「目录级各自 rc 正常、
本卡零引入红」。
