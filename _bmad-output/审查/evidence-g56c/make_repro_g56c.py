#!/usr/bin/env python3
"""CARD-G5-6c round-8 三条新反例的 tmp fixture 落盘 + 字节自证。

不可见字符一律走 \\uXXXX 转义写，禁止在源码里直接敲 —— 编辑器/工具链
会把 NBSP 与普通空格互换，肉眼与 diff 都看不出来。
"""

import pathlib
import sys

REPRO = pathlib.Path(sys.argv[1])

CASES = {
    # round-8 BLOCKER-1：`#` + U+00A0 + `keep` + 换行，权威字节 23c2a06b6565700a
    "NEW_HEADING": ("hash-NBSP.md", "#\u00a0keep\n"),
    # round-8 BLOCKER-2：带模型版本的真实生成声明
    "NEW_AI": ("GPT4声明.md", "---\ngenerator: 由 GPT-4 生成\n---\n"),
    # round-8 HIGH：大写 Source 键 + DOI 来源标识
    "NEW_SOURCE": ("DOI来源.md", "---\nSource: DOI:10.1000/xyz\n---\n"),
}

EXPECTED_HEX = {"NEW_HEADING": "23c2a06b6565700a"}

for key, (name, body) in CASES.items():
    p = REPRO / key / "vault" / "_待处理" / name
    # ⛔ round-2 审查 MEDIUM：原先只 write_bytes，在**全新目标目录**下必然
    # FileNotFoundError —— 取证脚本只在我自己那次已经手工建好目录的环境里能跑，
    # 复现者拿到手是坏的。取证包必须自足。
    p.parent.mkdir(parents=True, exist_ok=True)
    (REPRO / key / "out").mkdir(parents=True, exist_ok=True)
    raw = body.encode("utf-8")
    p.write_bytes(raw)
    print(f"{key:12s} {name:16s} {len(raw):3d} bytes  hex={raw.hex()}")
    want = EXPECTED_HEX.get(key)
    if want is not None and raw.hex() != want:
        raise SystemExit(f"字节不符权威取证值：{key} 期望 {want} 实得 {raw.hex()}")
