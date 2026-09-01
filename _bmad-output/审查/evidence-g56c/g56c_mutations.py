#!/usr/bin/env python3
"""CARD-G5-6c 负控：三条回退变异，各须由**指定的那道门**杀死。

判据（逐条硬门，缺一即 FAIL）：
  1. 指定 nodeid 必须出现在 FAILED 列表里 —— 「某处有失败」不算，
     必须是那道门红（reference_gate_design_pitfalls）。
  2. rc=5（no tests collected）不算红 —— 那是没跑，不是抓到了。
  3. 每条变异串行执行，跑完立刻还原并**逐字节**比对 sha256
     （reference_mutation_script_serial_only + temp_file_swap_needs_exit_trap）。
  4. 每条变异回退**该缺陷的全部防线层**，不只一层 ——
     只改一层会被纵深兜住，误判门不承重（reference_mutation_must_disable_all_layers）。

⛔ 本脚本原地修改 checkout 源码，必须串行、必须独占运行。
"""

from __future__ import annotations

import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
SRC = ROOT / "canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py"
TESTFILE = "tests/skills/test_g5_6_clear_inbox.py"
BACKEND = ROOT / "backend"
PYTEST = [str(BACKEND / ".venv/bin/pytest"), TESTFILE, "-q", "-p", "no:cacheprovider"]

# ── 三条变异：(名字, 指定必杀门, [(old, new), ...] 全部防线层) ──
MUTATIONS = [
    (
        "M-NBSP  井号后分隔回退到 Unicode \\s",
        "test_nbsp_after_hash_is_not_an_atx_heading",
        [
            (
                r'_HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")',
                r'_HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:\s|$)")',
            )
        ],
    ),
    (
        "M-AI    生成断言结构 + 生成器键两层全回退",
        "test_model_version_generation_claim_is_undigested_signal",
        [
            ("    gen_claim = find_generation_claim(text)\n", "    gen_claim = None\n"),
            (
                "    generator_keys = [k for k in fm if _norm_fm_key(k) in _GENERATOR_DECL_KEYS]\n",
                "    generator_keys = []\n",
            ),
        ],
    ),
    (
        "M-DOI   来源键名归一 + DOI 值形态两层全回退",
        "test_doi_source_identifier_blocks_deletion",
        [
            (
                "    source_alias_keys = [k for k in fm if _norm_fm_key(k) in _SOURCE_DECL_KEYS]\n",
                '    source_alias_keys = [k for k in fm if k == "source"]\n',
            ),
            (
                "    doi_bearing_keys = [k for k, v in fm.items() if _looks_like_doi_value(v)]\n",
                "    doi_bearing_keys = []\n",
            ),
        ],
    ),
]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_suite() -> tuple[int, list[str], str]:
    r = subprocess.run(
        PYTEST,
        cwd=BACKEND,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": str(pathlib.Path.home()),
            "LC_ALL": "C.UTF-8",
        },
    )
    out = r.stdout + r.stderr
    failed = [
        ln.split("::")[1].split(" ")[0].strip()
        for ln in out.splitlines()
        if ln.startswith("FAILED ") and "::" in ln
    ]
    tail = [
        ln
        for ln in out.splitlines()
        if "passed" in ln or "failed" in ln or "error" in ln
    ]
    return r.returncode, failed, (tail[-1] if tail else "<no summary>")


original = SRC.read_bytes()
base_sha = sha(SRC)
print(f"源码基线 sha256 = {base_sha}\n")

results: list[tuple[str, bool, str]] = []
try:
    for name, target_gate, layers in MUTATIONS:
        text = original.decode("utf-8")
        for old, new in layers:
            n = text.count(old)
            if n != 1:
                raise SystemExit(f"[{name}] 变异锚点出现 {n} 次（须 1）：{old!r}")
            text = text.replace(old, new)
        SRC.write_text(text, encoding="utf-8")
        assert sha(SRC) != base_sha, f"[{name}] 变异没有真的改到字节"

        rc, failed, summary = run_suite()

        # 还原 + 逐字节比对（每条变异跑完立刻还原，串行不重叠）
        SRC.write_bytes(original)
        restored = sha(SRC)

        killed = target_gate in failed
        ok = killed and rc not in (0, 5) and restored == base_sha
        detail = (
            f"rc={rc} | {summary} | 指定门{'已' if killed else '未'}被杀"
            f" | 连带红 {len(failed)} 门 | 还原 sha {'一致' if restored == base_sha else '⛔不一致'}"
        )
        results.append((name, ok, detail))
        print(
            f"{'✅' if ok else '❌'} {name}\n   目标门 {target_gate}\n   {detail}\n"
            f"   FAILED: {failed}\n"
        )
finally:
    SRC.write_bytes(original)
    final = sha(SRC)
    print(
        f"finally 还原后 sha256 = {final} "
        f"({'与基线逐字节相同' if final == base_sha else '⛔ 漂移'})"
    )

print("\n" + "=" * 70)
allok = (
    all(ok for _, ok, _ in results)
    and sha(SRC) == base_sha
    and len(results) == len(MUTATIONS)
)
print(
    f"G56C_NEGATIVE_CONTROL: {'PASS' if allok else 'FAIL'} "
    f"（{sum(1 for _, ok, _ in results if ok)}/{len(MUTATIONS)} 变异各由指定门杀死）"
)
sys.exit(0 if allok else 1)
