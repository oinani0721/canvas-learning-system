# tests/unit 目录级（沙箱内跑）伪红说明 — 2026-09-20

- 跑法：`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit -q -p no:cacheprovider -rfE`
  （与基线同口径）→ 结末 `= 33 failed, 6251 passed, 45 skipped, 13 xfailed, 341 warnings in 454.65s =`
  （`unit-20260920T132728.txt`）。
- 与基线 `evidence-b15/unit-red-baseline-9c4e7e82.txt`（33 条）做 nodeid 差集：
  - **+1**：`tests/unit/test_vault_install_manifest.py::test_digest_is_injective_over_adversarial_leaves`
    —— 在**沙箱内**报 `PermissionError: [Errno 1] Operation not permitted`（`sock.bind("node")`，AF_UNIX）；
    该测试在基线树 `9c4e7e82` 即存在（`grep -c def test_digest_is_injective...` = 1）。
  - **-1**：`tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`
    （基线注释自记 flaky，本跑为绿）。
- 归因验证（**沙箱外**）：同测试单跑 **1 passed**（rc=0）。⇒ 该红 = 执行沙箱拦 AF_UNIX bind 的伪红，
  非本批引入回归；有效差集 = 只减（修 1 flaky / 引入 0）。
- 收口终跑（判据用）：unit 目录级**须在沙箱外**执行并留档，再与基线做 nodeid 差集。
