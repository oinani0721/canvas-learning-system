#!/usr/bin/env python3
"""CARD-G2-7a-TAIL 补充探针: 新读法与原 `Path.read_text(encoding="utf-8")` 是否逐字等价。

用法: python3 probe_read_equivalence.py

对同一批样本文件, 两条路各读一次并逐字符比对; 抛异常的样本比对**异常类型**。
新读法与生产代码同形: `os.open(p, O_RDONLY|O_NONBLOCK)` -> `os.fstat` 判 `S_ISREG`
-> `os.fdopen(fd, "r", encoding="utf-8").read()`。
"""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
from pathlib import Path


def _new_read(p: Path) -> str:
    fd = os.open(p, os.O_RDONLY | os.O_NONBLOCK)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise AssertionError("样本应当是普通文件")
    with os.fdopen(fd, "r", encoding="utf-8") as fh:
        return fh.read()


SAMPLES: dict[str, bytes] = {
    "empty": b"",
    "lf-only": b'{"a": 1}\n',
    "crlf": b'{\r\n  "a": 1\r\n}\r\n',
    "cr-only": b'{\r  "a": 1\r}\r',
    "mixed-newlines": b'{\n  "a": 1\r\n}\r',
    "no-trailing-newline": b'{"a": 1}',
    "utf8-cjk": '{"键": "值 — 破折号"}\n'.encode(),
    "utf8-bom": b"\xef\xbb\xbf" + b'{"a": 1}\n',
    "embedded-nul": b'{"a": "\x00"}\n',
    "lone-surrogate-bytes": b"\xed\xa0\x80",          # 非法 UTF-8
    "invalid-utf8-tail": b'{"a": 1}\n\xff\xfe',       # 非法 UTF-8
    "u2028-line-sep": '{"a": "x y"}\n'.encode(),
    "large-5mib": (b'{"a": "' + b"x" * (5 * 1024 * 1024) + b'"}\n'),
    "many-crlf-lines": b"".join(b'{"i": %d}\r\n' % i for i in range(20000)),
}


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="g27a-equiv-")
    same = 0
    diff = []
    try:
        for name, payload in SAMPLES.items():
            p = Path(tmp) / name
            p.write_bytes(payload)

            def _try(fn):
                try:
                    return ("ok", fn(p))
                except Exception as exc:  # noqa: BLE001 — 探针要对比异常类型本身
                    return ("raise", type(exc).__name__)

            old_kind, old_val = _try(lambda q: q.read_text(encoding="utf-8"))
            new_kind, new_val = _try(_new_read)
            equal = old_kind == new_kind and old_val == new_val
            if equal:
                same += 1
            else:
                diff.append((name, old_kind, new_kind))
            shown_old = old_val if old_kind == "raise" else f"{len(old_val)} 字符"
            shown_new = new_val if new_kind == "raise" else f"{len(new_val)} 字符"
            print(
                f"{name:<22} bytes={len(payload):<9} "
                f"read_text={old_kind}/{shown_old:<22} "
                f"新读法={new_kind}/{shown_new:<22} "
                f"{'逐字同' if equal else '★ 不同 ★'}"
            )
        print("-" * 118)
        print(f"样本 {len(SAMPLES)} 个: 逐字同 {same} / 不同 {len(diff)}")
        if diff:
            print("不同的样本:", diff)
        return 0 if not diff else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
