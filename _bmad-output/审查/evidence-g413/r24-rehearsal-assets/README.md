# r24 用户 session 全量彩排资产（自包含）

- `full_rehearsal.py`：把四份金集 + manifest + 真清单复制到 `/tmp/g413-r3/rehearse-{A,B}`，
  在副本上跑「勾满 → apply-verdicts → build --bump-revision → approve → verify」两场景：
  - A：103/103 全标（60 relevant / 8 irrelevant / 7 ambiguous）→ approve rc=0、verify rc=0；
  - B：102/103（留 `mem-x03` pending）→ approve rc=1 且 adjudication 保持 pending。
- 复跑：`PYTHONDONTWRITEBYTECODE=1 backend/.venv/bin/python <此文件>`（只读真车道文件）。
- 输出存档：`../r24-full-rehearsal-*.txt`。
