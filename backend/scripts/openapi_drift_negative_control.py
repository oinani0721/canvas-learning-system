#!/usr/bin/env python3
"""OpenAPI 漂移门负控 — CARD-DEBT-openapi-sync [BATCH-2026-09-01-第八批]

问的问题: `check-openapi-drift.py --snapshot` 报 `DRIFT: none` 时, 它究竟是
「真的没漂移」, 还是「门空转/被归一化吞掉了」?

做法(串行, 只动 tmp 副本, 正本 backend/openapi.json 全程不写)
  M1 删一个 path          → 期望 exit 1 且摘要**点名该 path**
  M2 改一个 enum 取值      → 期望 exit 1 且摘要**点名该 schema**(enum 保序不排序,
                            所以取值变化必须暴露)
  M3 删一个 required 字段  → 期望 exit 1 且摘要**点名该 schema**(required 虽按集合
                            排序, 但集合内容变化必须暴露)
  M4 只改 info.x-generated-at → 期望 exit 0(归一化把易变键吃掉, 门不因时间戳恒红)

判据是「**指定的那一条**变红且摘要点名**指定的那个对象**」, 不是「某处有失败」:
  - 只看 exit 1 会把「脚本崩了」「文件读不出」也算成门在工作;
  - 只看「有 DRIFT」会让 M2 因为别的原因红也算过。
M4 是放行门, 单独看它 PASS 不证明任何事(一个恒返回 0 的门也能过) —— 它只有
和 M1-M3 三条红门放在一起才有意义: 三红一绿共同说明「门对真差异敏感、对时间戳不敏感」。

⚠️ 前提: 正本 backend/openapi.json 当前必须**无漂移**(否则 M4 会因为「正本本来
就旧」而红, 错误却指向门)。脚本开跑先验证这个前提, 不满足则 exit 2 报「前提不
满足」而不是 FAIL —— 把「基线不对」和「门坏了」分开, 是这类脚本最容易出的假信号。

本负控证明什么: 门能对这三类真实差异翻红并点名对象, 且不被时间戳噪音带红。
本负控不证明什么: 不穷举 OpenAPI 的所有差异形态(未覆盖 anyOf 顺序、parameters
  顺序、description 文案变化等); 不证明 CI 上的 workflow 会因此变红(那需要 push
  后 GitHub 实跑, 是本卡已知证据缺口); 不证明归一化的五条规则在语义上「应该」如此
  (那是设计裁决, 见 check-openapi-drift.py 模块 docstring)。
"""

import json
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DRIFT_TOOL = REPO_ROOT / "scripts" / "spec-tools" / "check-openapi-drift.py"
PRISTINE_SNAPSHOT = BACKEND_DIR / "openapi.json"


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def run_gate(snapshot_path: Path) -> tuple[int, str]:
    """跑真实 CLI 入口(不是复刻比对逻辑 —— 复刻等于测自己的副本)。"""
    proc = subprocess.run(
        [sys.executable, str(DRIFT_TOOL), "--snapshot", str(snapshot_path)],
        capture_output=True,
        text=True,
        cwd=str(BACKEND_DIR),
    )
    return proc.returncode, proc.stdout + proc.stderr


def pick_path(spec: dict) -> str:
    """挑最长(并列取字典序最小)的 path —— 点名断言的子串必须有区分度,
    挑到 `/` 这种单字符路径时 `named in output` 对 import 噪音恒真, 断言空转。"""
    return sorted(spec["paths"], key=lambda p: (-len(p), p))[0]


def pick_enum_schema(spec: dict) -> tuple[str, list]:
    """找一个 components.schemas 下直接带字符串 enum 的 schema。"""
    for name in sorted(spec["components"]["schemas"]):
        node = spec["components"]["schemas"][name]
        found: list[list[str]] = []

        def walk(sub):
            if isinstance(sub, dict):
                enum = sub.get("enum")
                if isinstance(enum, list) and enum and all(isinstance(x, str) for x in enum):
                    found.append(enum)
                for value in sub.values():
                    walk(value)
            elif isinstance(sub, list):
                for value in sub:
                    walk(value)

        walk(node)
        if found:
            return name, found[0]
    raise SystemExit("FATAL: 快照中找不到带字符串 enum 的 schema — 负控无法构造 M2")


def pick_required_schema(spec: dict) -> tuple[str, list]:
    for name in sorted(spec["components"]["schemas"]):
        node = spec["components"]["schemas"][name]
        required = node.get("required")
        if isinstance(required, list) and len(required) >= 2 and all(isinstance(x, str) for x in required):
            return name, required
    raise SystemExit("FATAL: 快照中找不到 required≥2 的 schema — 负控无法构造 M3")


def mutate_and_check(
    label: str,
    tmp_dir: Path,
    mutator,
    expect_exit: int,
    expect_named: str | None,
    index: int,
    expect_marker: str | None = None,
) -> tuple[bool, str]:
    spec = json.loads(PRISTINE_SNAPSHOT.read_text(encoding="utf-8"))
    described = mutator(spec)
    target = tmp_dir / f"mutant-{index}.json"
    target.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 变异必须真的改到了东西 —— 否则「门没红」会被误读成门坏了(实际是变异空转)
    if digest(target) == digest(PRISTINE_SNAPSHOT):
        return False, f"{label}: 变异未生效(tmp 与正本同 sha) — 判据无效, 不是门的问题"

    code, output = run_gate(target)
    if code != expect_exit:
        return False, f"{label}: 期望 exit {expect_exit}, 实得 {code} | {described}"
    if expect_named and expect_named not in output:
        return False, f"{label}: exit 对但摘要未点名 `{expect_named}` | {described}"
    if expect_marker and expect_marker not in output:
        return (
            False,
            f"{label}: exit/点名都对, 但差异行缺标记 {expect_marker!r} | {described}",
        )
    if expect_exit == 0 and "DRIFT: none" not in output:
        return False, f"{label}: exit 0 但未打印 `DRIFT: none` | {described}"
    return True, f"{label}: OK ({described})"


def main() -> int:
    if not DRIFT_TOOL.is_file():
        print(f"FATAL: 找不到被测门 {DRIFT_TOOL}", file=sys.stderr)
        return 2
    if not PRISTINE_SNAPSHOT.is_file():
        print(f"FATAL: 找不到正本快照 {PRISTINE_SNAPSHOT}", file=sys.stderr)
        return 2

    baseline_code, baseline_output = run_gate(PRISTINE_SNAPSHOT)
    if baseline_code != 0:
        print(
            "PREREQUISITE NOT MET: 正本快照当前已漂移, 负控需要一个无漂移的基线才能\n"
            "  判断 M4(只改时间戳应放行)。先跑:\n"
            "  cd backend && .venv/bin/python ../scripts/spec-tools/check-openapi-drift.py "
            "--write openapi.json\n"
            f"  (门的原始输出 exit={baseline_code})\n{baseline_output}",
            file=sys.stderr,
        )
        return 2
    baseline_line = next(
        (line for line in baseline_output.splitlines() if line.startswith("DRIFT:")),
        "(门输出无 DRIFT 行)",
    )
    print(f"  PASS  前提: 正本无漂移 ({baseline_line})")

    before = digest(PRISTINE_SNAPSHOT)
    base = json.loads(PRISTINE_SNAPSHOT.read_text(encoding="utf-8"))
    doomed_path = pick_path(base)
    enum_schema, enum_values = pick_enum_schema(base)
    required_schema, required_fields = pick_required_schema(base)

    def m1(spec):
        del spec["paths"][doomed_path]
        return f"删除 path {doomed_path}"

    def m2(spec):
        replaced = {"was": None}

        def walk(sub):
            if replaced["was"] is not None:
                return
            if isinstance(sub, dict):
                enum = sub.get("enum")
                if isinstance(enum, list) and enum == enum_values:
                    replaced["was"] = enum[0]
                    sub["enum"] = ["__MUTANT_ENUM_VALUE__", *enum[1:]]
                    return
                for value in sub.values():
                    walk(value)
            elif isinstance(sub, list):
                for value in sub:
                    walk(value)

        walk(spec["components"]["schemas"][enum_schema])
        return f"schema {enum_schema} 的 enum 首值 {replaced['was']!r} → __MUTANT_ENUM_VALUE__"

    def m3(spec):
        node = spec["components"]["schemas"][required_schema]
        dropped = node["required"][0]
        node["required"] = node["required"][1:]
        return f"schema {required_schema} 的 required 删除字段 {dropped!r}"

    def m4(spec):
        spec.setdefault("info", {})["x-generated-at"] = "1999-01-01T00:00:00+00:00"
        return "只改 info.x-generated-at(易变键)"

    cases = [
        # 负控删的是**快照侧**的 path, 所以差异方向是「snapshot 缺失」
        # (镜像场景——app 侧删了 path——才会打「仅在 snapshot(已从 app 移除)」)
        ("M1 删 path", m1, 1, doomed_path, "snapshot 缺失"),
        ("M2 改 enum 取值", m2, 1, enum_schema, None),
        ("M3 删 required 字段", m3, 1, required_schema, None),
        ("M4 只改 x-generated-at", m4, 0, None, None),
    ]

    results = []
    with tempfile.TemporaryDirectory(prefix="openapi-drift-negctl-") as raw_tmp:
        tmp_dir = Path(raw_tmp)
        for index, (
            label,
            mutator,
            expect_exit,
            expect_named,
            expect_marker,
        ) in enumerate(cases, start=1):
            ok, message = mutate_and_check(label, tmp_dir, mutator, expect_exit, expect_named, index, expect_marker)
            results.append((ok, message))
            print(("  PASS  " if ok else "  FAIL  ") + message)

    after = digest(PRISTINE_SNAPSHOT)
    if before != after:
        print(
            f"FAIL  正本快照被改动! before={before[:16]} after={after[:16]} — 负控必须只动 tmp",
            file=sys.stderr,
        )
        return 1
    print(f"  PASS  正本 {PRISTINE_SNAPSHOT.name} 全程未变 (sha256 {before[:16]}…)")

    if all(ok for ok, _ in results):
        print("NEGATIVE-CONTROL: PASS (3 mutants → exit 1 with named diff; timestamp-only → exit 0)")
        return 0
    print("NEGATIVE-CONTROL: FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
