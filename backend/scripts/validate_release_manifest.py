#!/usr/bin/env python3
"""CARD-R-EVD — Release 旅程证据 manifest 机械校验器。

被校验物: docs/release-evidence/<rc>/journeys/<Jxx>/manifest.json
结构契约: docs/release-evidence/manifest.schema.json (JSON Schema draft 2020-12)
规范文档: docs/release-evidence/README.md (含与计划书 §12.6 L596 的裁剪对照)

三层校验:
  1. 结构层 — jsonschema 对 schema 文件求值 (字段存在性/类型/枚举/正则/const/if-then)
  2. 语义层 — 本文件的 S1..S16 跨字段规则 (JSON Schema 表达不了或表达得很难看的部分)
  3. 产物层 — A0 路径安全 + A1..A3 存在性/checksum/字节数真验 (**默认开启**,
     `--skip-artifact-verify` 显式弃权 —— opt-in 会让文档给的单文件命令根本不看产物)

配置面指纹钉死 (沿用 CARD-G1-5 的双文件契约先例): schema 文件全文 SHA-256 由
SCHEMA_SHA256 常量钉死, 先于解析比对。放宽 schema 必须同 commit 改本文件常量,
schema 单边放水拿不到绿。

⚠️ 诚实边界: 本校验器只裁决 manifest **自身的机械自洽**——字段齐、格式对、跨字段
不自相矛盾、(可选) artifact checksum 与磁盘一致。它**不裁决旅程真的跑过、断言真的
成立、证据内容真实**。E 级真伪由 G1-3 能力证据台账与 G1-6 逐声明审计链负责; 本器
唯一能挡的是"manifest 自己就说不圆"的那类失实。

安全边界 (Codex round-1 BLOCKER 整改): artifacts[].path 经 schema 正则 + A0 解析后
越界检查双重约束——绝对路径 / .. 上跳 / symlink / 解析后逃出 manifest 目录或仓库根
一律拒绝。--verify-artifacts 会读取被指的文件, 无此约束即为任意文件读取与 hash oracle。

退出码 (与 check_readme_claims.py 同口径):
  0 = 全部通过
  1 = 校验失败 (结构 / 语义 / 产物层 —— 包括 JSON 合法但形状不对, 如顶层是数组)
  2 = 配置/环境错误 (schema 指纹不符、缺依赖、文件不存在、JSON 语法错、编码/权限错)

本文件的规则集经一轮 Codex 静态审查 + 一轮 5 轴红队实测对抗加固, 逐条来源见
_bmad-output/审查/codex-review-CARD-R-EVD-rounds.md 与 revd-redteam-2026-08-28.md。
核心教训: **凡是由 manifest 作者自己填的「标准」都不是标准** —— dogfood 天数、
skip 与否、达标与否, 都必须与其他字段交叉核对或钉死下限。

用法:
  python backend/scripts/validate_release_manifest.py <manifest.json> [...]
  python backend/scripts/validate_release_manifest.py --all
  python backend/scripts/validate_release_manifest.py --all --skip-artifact-verify
  python backend/scripts/validate_release_manifest.py --require-complete <rc>
        RC 发布门: 该 rc 下 J01-J10 齐全、全为 live 实录、同一候选 SHA、全部 E3+ 且通过
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "docs" / "release-evidence"
SCHEMA_PATH = EVIDENCE_ROOT / "manifest.schema.json"

# docs/release-evidence/manifest.schema.json 全文 SHA-256 (v1.0.0)。
# 改 schema 必须同 commit 更新此常量 —— 见模块 docstring「配置面指纹钉死」。
SCHEMA_SHA256 = "4456e1ad629108d618284d6bd5b717f484a712aa8685615e31f940327922c547"

SUPPORTED_SCHEMA_MAJOR = 1

ALL_JOURNEYS = tuple(f"J{i:02d}" for i in range(1, 11))

# §12.6 的协议名即「14-day dogfood protocol」——天数下限不由 manifest 作者自定
DOGFOOD_MIN_DAYS = 14
# 空文件的 sha256, 用于 S8 的元数据算术自洽检查
_EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
# rc 必须是证据树内的目录名, 不能是任意路径 (红队 BLOCKER)
_RC_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

_E3_PLUS = {"E3", "E4", "E5"}
_E4_PLUS = {"E4", "E5"}
_RECONSTRUCTED_MAX = {"E0", "E1", "E2"}
_REPO_PREFIX = "repo://"


class ConfigError(RuntimeError):
    """配置/环境错误 —— 退出码 2, 与"内容不合格"(退出码 1) 严格区分。"""


# ─────────────────────────────────────────────────────────────
# schema 装载 (指纹先于解析)
# ─────────────────────────────────────────────────────────────


def load_schema(schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    if not schema_path.is_file():
        raise ConfigError(f"schema 文件不存在: {schema_path}")
    try:
        raw = schema_path.read_bytes()
    except OSError as exc:
        raise ConfigError(f"schema 文件读取失败: {exc}") from exc
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SCHEMA_SHA256:
        raise ConfigError(
            "schema 指纹与脚本 SCHEMA_SHA256 不一致 — schema 单边改动被拒绝。"
            f"\n  实际: {digest}\n  契约: {SCHEMA_SHA256}"
            "\n  放宽 schema 必须同 commit 更新 validate_release_manifest.py::SCHEMA_SHA256。"
        )
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:  # pragma: no cover
        raise ConfigError(f"schema 不是合法 UTF-8 JSON: {exc}") from exc


def _get_validator(schema: dict[str, Any]):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ConfigError(
            "缺少 jsonschema 依赖 —— 本校验器的结构层由它实施, 不做降级放行。\n  安装: pip install jsonschema"
        ) from exc
    return Draft202012Validator(schema)


# ─────────────────────────────────────────────────────────────
# JSON 装载 (重复 key 拒收 + 编码/权限错归位)
# ─────────────────────────────────────────────────────────────


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """JSON 允许重复 key 且标准库静默取后值 —— 那意味着 {"dirty": true, "dirty": false}
    能骗过一切校验。这里直接拒收。"""
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"重复的 JSON key: {key!r}")
        seen.add(key)
    return dict(pairs)


def _load_json_document(path: Path) -> Any:
    if not path.is_file():
        raise ConfigError(f"manifest 不存在: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{path}: 不是合法 UTF-8 文本 — {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"{path}: 读取失败 — {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path}: 不是合法 JSON — {exc}") from exc
    except ValueError as exc:  # 重复 key —— 内容问题, 但装载期才发现
        raise _DuplicateKeyError(str(exc)) from exc


class _DuplicateKeyError(RuntimeError):
    """重复 JSON key: 属"内容不合格"(退出码 1), 不是环境错误。"""


# ─────────────────────────────────────────────────────────────
# 语义规则 S1..S13
# ─────────────────────────────────────────────────────────────


def _parse_dt(value: Any) -> datetime | None:
    """解析 ISO 8601; 必须带时区偏移 (naive 视为不合格)。

    jsonschema 的 "format": "date-time" 默认只是注解、不校验, 故日期时间一律在此手验。
    """
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _parse_date(value: Any) -> date | None:
    """解析 YYYY-MM-DD (dogfood 窗口用)。"""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


_NUM_UNIT = r"(-?\d+(?:\.\d+)?)\s*([A-Za-z%µ]*)"


def _threshold_value(text: str) -> tuple[float, str] | None:
    """从阈值文本里抠出**紧跟比较符**的数值与单位。

    必须锚在比较符上: `"p95 ≤ 2.5s"` 里的第一个数字是 metric 名的一部分 (95),
    取它会得出 95≤95 这种荒谬对比而放过真正的超标 (本卡自查抓到的实现缺陷)。
    """
    m = re.search(r"(?:≤|<=|<|≥|>=|>)\s*" + _NUM_UNIT, text.replace(",", ""))
    return (float(m.group(1)), m.group(2).lower()) if m else None


def _measured_value(text: str) -> tuple[float, str] | None:
    """从实测文本里抠数值与单位: 优先取 `=` 之后的, 否则取最后一个。"""
    cleaned = text.replace(",", "")
    m = re.search(r"=\s*" + _NUM_UNIT, cleaned)
    if m:
        return float(m.group(1)), m.group(2).lower()
    hits = re.findall(_NUM_UNIT, cleaned)
    return (float(hits[-1][0]), hits[-1][1].lower()) if hits else None


def _threshold_direction(text: str) -> str | None:
    """判断阈值方向: "≤"/"<=" → 上界; "≥"/">=" → 下界。判不出返回 None。"""
    if any(sym in text for sym in ("≤", "<=", "<", "至多", "不超过")):
        return "max"
    if any(sym in text for sym in ("≥", ">=", ">", "至少", "不少于")):
        return "min"
    return None


# 已知的 skip/mock 开关模式 (S16 启发式)。措辞换写法即可躲开 —— 这是有意接受的边界,
# 它拦的是"命令里明摆着写了 mock 却声明零 mock"这种自相矛盾, 不是所有 mock。
_SKIP_MOCK_PATTERNS = (
    re.compile(r"\b[A-Z0-9_]*MOCK[A-Z0-9_]*\s*=\s*[1-9]"),
    re.compile(r"\b[A-Z0-9_]*FAKE[A-Z0-9_]*\s*=\s*[1-9]"),
    re.compile(r"\bSKIP_[A-Z0-9_]+\s*=\s*[1-9]"),
    re.compile(r"--mock\b"),
    re.compile(r"--ignore="),
    re.compile(r"--deselect\b"),
    re.compile(r"-m\s+['\"]?not\s"),
    re.compile(r"\bmock(?:ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\bstub(?:bed)?\b", re.IGNORECASE),
    re.compile(r"(被)?跳过"),
    re.compile(r"假的?(数据|客户端|服务)"),
)


def _scan_skip_mock_markers(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    """在自由文本里找 skip/mock 痕迹。返回 [(字段路径, 命中片段)]。"""
    hits: list[tuple[str, str]] = []
    fields: list[tuple[str, str]] = []
    for idx, cmd in enumerate(manifest["execution"]["commands"]):
        fields.append((f"execution.commands[{idx}].cmd", cmd["cmd"]))
        if cmd.get("note"):
            fields.append((f"execution.commands[{idx}].note", cmd["note"]))
    for idx, assertion in enumerate(manifest["assertions"]):
        fields.append((f"assertions[{idx}].method", assertion["method"]))
        if assertion.get("note"):
            fields.append((f"assertions[{idx}].note", assertion["note"]))
    if manifest.get("notes"):
        fields.append(("notes", manifest["notes"]))
    for idx, lim in enumerate(manifest.get("known_limitations", [])):
        fields.append((f"known_limitations[{idx}]", lim))
    for where, text in fields:
        for pattern in _SKIP_MOCK_PATTERNS:
            m = pattern.search(text)
            if m:
                hits.append((where, m.group(0)))
                break
    return hits


def _semantic_checks(manifest: dict[str, Any], manifest_path: Path, *, now: datetime | None = None) -> list[str]:
    """跨字段语义规则 S1..S16。返回失败描述列表 (空 = 通过)。

    仅在结构层通过后调用 —— 这里假定字段存在且类型正确。
    `now` 仅供测试注入; 默认取当前时刻 (用于"事件不能发生在未来"的检查)。
    """
    problems: list[str] = []
    now = now or datetime.now(timezone.utc)

    level = manifest["evidence_level"]
    result = manifest["result"]
    execution = manifest["execution"]
    assertions = manifest["assertions"]
    provenance = manifest["provenance"]
    signoff = manifest["signoff"]
    slo = manifest["slo"]
    gates = manifest.get("release_gates")
    is_e3_plus = level in _E3_PLUS

    # ── S1 — schema_version major 必须被本校验器支持 ──
    raw_version = manifest["schema_version"]
    if not raw_version.isascii():
        # Python re 的 \d 匹配 Unicode 数字, int() 也吃全角/阿拉伯-印度数字 ——
        # "１.٠.٠" 会被当成 1.0.0 而与任何下游文本比较都不相等 (红队 R-LOW)。
        problems.append(f"[S1] schema_version ({raw_version!r}) 含非 ASCII 字符 — 版本号必须是 ASCII 数字")
    else:
        major = int(raw_version.split(".", 1)[0])
        if major != SUPPORTED_SCHEMA_MAJOR:
            problems.append(
                f"[S1] schema_version major={major} 超出本校验器支持范围 "
                f"(支持 {SUPPORTED_SCHEMA_MAJOR}.x) — 校验器需先升级, 不做尽力而为解析。"
            )

    # ── S2 — 时间: 带时区 / 先后有序 / 不在未来 / 签字不早于收工 ──
    started = _parse_dt(execution["started_at"])
    finished = _parse_dt(execution["finished_at"])
    if started is None:
        problems.append("[S2] execution.started_at 不是带时区偏移的 ISO 8601")
    if finished is None:
        problems.append("[S2] execution.finished_at 不是带时区偏移的 ISO 8601")
    if started is not None and finished is not None:
        if finished < started:
            problems.append(
                f"[S2] execution.finished_at ({execution['finished_at']}) 早于 started_at ({execution['started_at']})"
            )
        elif finished == started and is_e3_plus:
            problems.append(
                f"[S2] evidence_level={level} 的旅程耗时为 0 "
                f"({execution['started_at']}) — 一条完整黑盒 E2E 不可能零耗时。"
            )

    signed_at = _parse_dt(signoff["at"]) if "at" in signoff else None
    if "at" in signoff and signed_at is None:
        problems.append(f"[S2] signoff.at ({signoff['at']!r}) 不是带时区偏移的 ISO 8601 — 签字时间必须可核对")
    if signed_at is not None and finished is not None and signed_at < finished:
        problems.append(
            f"[S2] signoff.at ({signoff['at']}) 早于 execution.finished_at "
            f"({execution['finished_at']}) — 用户不可能在旅程结束前就验收了它的结果。"
        )

    for m_idx, meas in enumerate(slo["measurements"]):
        waiver = meas.get("waiver")
        if waiver and _parse_dt(waiver["at"]) is None:
            problems.append(f"[S2] slo.measurements[{m_idx}].waiver.at ({waiver['at']!r}) 不是带时区偏移的 ISO 8601")
    if gates and _parse_dt(gates["recovery_drill"]["at"]) is None:
        problems.append("[S2] release_gates.recovery_drill.at 不是带时区偏移的 ISO 8601")

    # 未来时间: 已完成并已签字的证据不可能记录尚未发生的事
    future_fields: list[tuple[str, datetime | None]] = [
        ("execution.started_at", started),
        ("execution.finished_at", finished),
        ("signoff.at", signed_at),
    ]
    if gates:
        future_fields.append(("release_gates.recovery_drill.at", _parse_dt(gates["recovery_drill"]["at"])))
    for m_idx, meas in enumerate(slo["measurements"]):
        waiver = meas.get("waiver")
        if waiver:
            future_fields.append((f"slo.measurements[{m_idx}].waiver.at", _parse_dt(waiver["at"])))
    for where, value in future_fields:
        if value is not None and value > now:
            problems.append(f"[S2] {where} ({value.isoformat()}) 在未来 — 证据不能记录尚未发生的事。")

    # ── S3 — 断言/回滚实况与整体判定不得矛盾 ──
    bad = [a["id"] for a in assertions if a["result"] != "pass"]
    if bad and result == "pass":
        problems.append(f"[S3] result=pass 与断言实况矛盾 — 非 pass 断言: {', '.join(bad)}")
    if manifest["rollback"]["result"] == "fail" and result == "pass":
        problems.append("[S3] rollback.result=fail 却宣称整体 result=pass")

    # ── S4 — skip/mock 声明自洽 + E3 及以上不得有 skip/mock ──
    skips = execution["skips_or_mocks"]
    if skips["declared"] and not skips["items"]:
        problems.append("[S4] skips_or_mocks.declared=true 但 items 为空 — 必须逐条列出")
    if not skips["declared"] and skips["items"]:
        problems.append("[S4] skips_or_mocks.items 非空但 declared=false — 自相矛盾")
    if is_e3_plus and (skips["declared"] or skips["items"]):
        problems.append(
            f"[S4] evidence_level={level} 要求无 skip/mock 的黑盒 E2E (§12.5), 但 manifest 自陈存在 skip/mock"
        )

    # ── S5 — E4/E5 必须有用户签字 (schema if/then 已强制 approved 带 user+at) ──
    if level in _E4_PLUS and signoff["status"] != "approved":
        problems.append(
            f"[S5] evidence_level={level} (User-verified 及以上) 要求 signoff.status=approved, 实际 {signoff['status']}"
        )

    # ── S6 — 路径一致性: journey_id / rc 必须与目录结构吻合 ──
    parent = manifest_path.resolve().parent
    if parent.name != manifest["journey_id"]:
        problems.append(f"[S6] journey_id={manifest['journey_id']} 与所在目录名 {parent.name} 不一致")
    journeys_dir = parent.parent
    if journeys_dir.name != "journeys":
        problems.append(f"[S6] manifest 不在 <rc>/journeys/<Jxx>/ 结构下 (实际父级: {journeys_dir.name})")
    elif journeys_dir.parent.name != manifest["rc"]:
        problems.append(f"[S6] rc={manifest['rc']} 与目录名 {journeys_dir.parent.name} 不一致")

    # ── S7 — 命令退出码与 expected_failure 必须自洽 ──
    for idx, cmd in enumerate(execution["commands"]):
        expected = cmd.get("expected_failure", False)
        if cmd["exit_code"] != 0 and not expected:
            problems.append(
                f"[S7] commands[{idx}] exit_code={cmd['exit_code']} 非零但未标 expected_failure=true: {cmd['cmd']}"
            )
        if cmd["exit_code"] == 0 and expected:
            problems.append(
                f"[S7] commands[{idx}] 标了 expected_failure=true 却 exit_code=0 — "
                f"要么标记是假的, 要么退出码是假的: {cmd['cmd']}"
            )

    # ── S8 — 字段间自洽: index_sha / artifacts 元数据 / rollback ──
    env = manifest["environment"]
    if env["index_sha"] is None and not env.get("index_sha_null_reason"):
        problems.append("[S8] environment.index_sha=null 时必须给 index_sha_null_reason")

    # 去重按**解析后的真实路径**, 不按原始字符串 —— "run.log" 与 "./run.log" 是同一份
    seen_paths: set[str] = {a["path"] for a in manifest["artifacts"]}
    resolved_seen: dict[str, str] = {}
    for art in manifest["artifacts"]:
        try:
            key = str(resolve_artifact_path(art["path"], manifest_path))
        except _ArtifactPathError:
            continue  # A0 会单独报
        key = unicodedata.normalize("NFC", key)
        if key in resolved_seen:
            problems.append(
                f"[S8] artifacts 指向同一份文件却登记为两件: {resolved_seen[key]!r} "
                f"与 {art['path']!r} — 一份产物撑不起两条独立断言。"
            )
        else:
            resolved_seen[key] = art["path"]
        if art["bytes"] == 0 and art["sha256"] != _EMPTY_SHA256:
            problems.append(
                f"[S8] artifacts {art['path']!r} 声明 bytes=0 但 sha256 不是空串摘要 "
                f"({_EMPTY_SHA256[:16]}…) — 这组元数据在算术上不可能同时成立。"
            )

    rollback = manifest["rollback"]
    if rollback["performed"] and rollback["result"] == "not_applicable":
        problems.append("[S8] rollback.performed=true 与 result=not_applicable 矛盾")
    if not rollback["performed"] and rollback["result"] in {"pass", "fail"}:
        problems.append(f"[S8] rollback.performed=false 却宣称 result={rollback['result']}")
    if rollback["result"] == "not_applicable" and not rollback.get("reason"):
        problems.append("[S8] rollback.result=not_applicable 时必须给 reason")
    if rollback["performed"] and not rollback.get("method"):
        problems.append("[S8] rollback.performed=true 时必须给 method")

    # ── S9 — SLO: E3+ 锁版 + 阈值实测; 未达标须用户 waiver 且落账为已知限制 ──
    if is_e3_plus:
        if not slo["manifest_revision"]:
            problems.append(
                f"[S9] evidence_level={level} 要求 slo.manifest_revision 非 null "
                "(§12.5 L592: E3 前必须锁定用户批准的 SLO, 不得事后降门槛; owner = CARD-R-SLO)"
            )
        if not slo["measurements"]:
            problems.append(
                f"[S9] evidence_level={level} 要求 slo.measurements 至少一条 "
                "(§12.5 L592: J manifest 必须记录阈值与实测)"
            )
    for m_idx, meas in enumerate(slo["measurements"]):
        # 尽力而为的数值核对: 阈值/实测都能抠出数字、**单位一致**、方向可判时才比对。
        # 单位不一致 (如 "≤ 15min" vs "11m42s") 一律闭嘴 —— 宁可漏报也不误杀。
        thr = _threshold_value(meas["threshold"])
        mea = _measured_value(meas["measured"])
        direction = _threshold_direction(meas["threshold"])
        if thr and mea and direction and thr[1] == mea[1]:
            actually_meets = mea[0] <= thr[0] if direction == "max" else mea[0] >= thr[0]
            if actually_meets != meas["meets"]:
                problems.append(
                    f"[S9] slo.measurements[{m_idx}] ({meas['metric']}) 的 meets="
                    f"{meas['meets']} 与自带数字矛盾: 阈值 {meas['threshold']!r} vs "
                    f"实测 {meas['measured']!r} (按{'上界' if direction == 'max' else '下界'}判应为 "
                    f"{actually_meets})。"
                )
        if meas["meets"]:
            continue
        waiver = meas.get("waiver")
        if result != "fail" and not waiver:
            problems.append(
                f"[S9] slo.measurements[{m_idx}] ({meas['metric']}) 未达标 "
                f"(阈值 {meas['threshold']} vs 实测 {meas['measured']}), "
                f"而整体 result={result} 且无用户 waiver — §12.5: 未达标只能判失败, "
                "或经用户事前/书面接受后降级为限制。"
            )
        if result != "fail" and not manifest.get("known_limitations"):
            problems.append(
                f"[S9] slo.measurements[{m_idx}] ({meas['metric']}) 未达标而整体未判 fail, "
                "但 known_limitations 为空 — §12.5 要求降级后写入已知限制。"
            )
        if waiver and waiver["accepted_by"] == execution["operator"]:
            problems.append(
                f"[S9] slo.measurements[{m_idx}] 的 waiver.accepted_by "
                f"({waiver['accepted_by']!r}) 与 execution.operator 同一 — "
                "执行者不能给自己开免责。"
            )

    # ── S10 — provenance: 回填件不得冒充发布证据; 实录不得带推定字段 ──
    if provenance["mode"] == "reconstructed":
        if level not in _RECONSTRUCTED_MAX:
            problems.append(
                f"[S10] provenance.mode=reconstructed (事后回填) 不得标 "
                f"evidence_level={level} — 回填件最高 E2, E3+ 须在冻结 RC 上实跑。"
            )
        if signoff["status"] == "approved":
            problems.append(
                "[S10] provenance.mode=reconstructed 的回填件不得带 signoff=approved "
                "— 用户签的应是实跑证据, 不是事后重建的记述。"
            )
        if not provenance["unproven_fields"]:
            problems.append(
                "[S10] provenance.mode=reconstructed 但 unproven_fields 为空 — "
                "回填必然存在无原始证据支撑的字段, 逐条列出才算诚实。"
            )
    else:
        if provenance["unproven_fields"]:
            problems.append(
                "[S10] provenance.mode=live 却列出 unproven_fields "
                f"({', '.join(provenance['unproven_fields'])}) — 实录不该有推定字段; "
                "确有推定则本 manifest 属 reconstructed。"
            )
        if provenance.get("reconstructed_from"):
            problems.append("[S10] provenance.mode=live 却给了 reconstructed_from — 一边宣称实录一边承认是回填件。")

    # ── S11 — E5 硬门: 14 天 dogfood + 活动量 + 恢复演练 (§12.5 / §12.6) ──
    if level == "E5":
        if not gates:
            problems.append(
                "[S11] evidence_level=E5 (Personal production candidate) 要求 "
                "release_gates (14 天 dogfood + 恢复演练), 当前缺失 — §12.5/§12.6。"
            )
        else:
            dogfood = gates["dogfood"]
            if dogfood["days_completed"] < DOGFOOD_MIN_DAYS:
                problems.append(
                    f"[S11] dogfood 实跑 {dogfood['days_completed']} 天, 不足协议下限 "
                    f"{DOGFOOD_MIN_DAYS} 天 (§12.6 14-day dogfood protocol)。"
                )
            if dogfood["days_completed"] < dogfood["days_required"]:
                problems.append(
                    f"[S11] dogfood 未跑满: {dogfood['days_completed']}/"
                    f"{dogfood['days_required']} 天 — 漏日即窗口未完成。"
                )
            if dogfood.get("missed_days", 0) > 0:
                problems.append(
                    f"[S11] dogfood 有漏日 ({dogfood['missed_days']} 天) — §12.6: 漏日或漏覆盖则窗口未完成。"
                )
            if dogfood["rc_sha"] != manifest["candidate"]["sha"]:
                problems.append(
                    f"[S11] dogfood.rc_sha ({dogfood['rc_sha'][:12]}…) 与 candidate.sha "
                    f"({manifest['candidate']['sha'][:12]}…) 不一致 — "
                    "§12.6: 影响产品行为的修改须从新 SHA 重开 14 天。"
                )
            # 日期窗口必须真的装得下所报天数
            d_start, d_end = _parse_date(dogfood["start_date"]), _parse_date(dogfood["end_date"])
            if d_start is None or d_end is None:
                problems.append(
                    f"[S11] dogfood 起止日期无法解析 (start={dogfood['start_date']!r}, end={dogfood['end_date']!r})"
                )
            else:
                if d_end < d_start:
                    problems.append(f"[S11] dogfood end_date ({d_end}) 早于 start_date ({d_start})")
                else:
                    span = (d_end - d_start).days + 1  # 含首尾
                    if span < dogfood["days_completed"]:
                        problems.append(
                            f"[S11] dogfood 窗口只有 {span} 个日历日 "
                            f"({d_start}→{d_end}), 装不下所报的 "
                            f"{dogfood['days_completed']} 天。"
                        )
                if d_end > now.date():
                    problems.append(f"[S11] dogfood end_date ({d_end}) 在未来 — 窗口尚未结束。")
            # 活动量: key 集必须一致, 且逐项达标 (防全零)
            counts = dogfood["activity_counts"]
            minimums = dogfood["activity_minimums"]
            if set(counts) != set(minimums):
                problems.append(
                    f"[S11] dogfood activity_counts 与 activity_minimums 的项目不一致 "
                    f"(counts={sorted(counts)}, minimums={sorted(minimums)}) — "
                    "只报达标项等于自选考卷。"
                )
            for key in sorted(set(counts) & set(minimums)):
                if counts[key] < minimums[key]:
                    problems.append(
                        f"[S11] dogfood 活动量 {key} 未达标: {counts[key]} < {minimums[key]} (运行前锁定的下限)。"
                    )
            drill = gates["recovery_drill"]
            if not drill["performed"] or drill["result"] != "pass":
                problems.append(
                    f"[S11] E5 要求恢复演练已执行且通过, 实际 performed={drill['performed']} result={drill['result']}"
                )
    elif gates is not None:
        problems.append(f"[S11] release_gates 只属 E5, 但 evidence_level={level} — 别用 E5 字段给低等级镀金。")

    # ── S12 — 断言的 evidence 必须解析到已登记且非空的 artifact ──
    by_path = {a["path"]: a for a in manifest["artifacts"]}
    for a_idx, assertion in enumerate(assertions):
        ev = assertion.get("evidence")
        if ev is None:
            continue
        if ev not in seen_paths:
            problems.append(
                f"[S12] assertions[{a_idx}] ({assertion['id']}) 的 evidence={ev!r} "
                "不在 artifacts[].path 中 — 悬空引用无法核对。"
            )
        elif by_path[ev]["bytes"] == 0:
            problems.append(
                f"[S12] assertions[{a_idx}] ({assertion['id']}) 拿一个 0 字节文件 "
                f"({ev!r}) 当证据 — 空文件证明不了任何断言。"
            )

    # ── S13 — E3+ 必须是 live 实录 (与 S10 互为正反面, 单独报以便定位) ──
    if is_e3_plus and provenance["mode"] != "live":
        problems.append(f"[S13] evidence_level={level} 要求 provenance.mode=live, 实际 {provenance['mode']}")

    # ── S14 — E3+ 必须整体通过 ("Verified" 蕴含通过) ──
    if is_e3_plus and result != "pass":
        problems.append(
            f"[S14] evidence_level={level} 与 result={result} 矛盾 — "
            "§12.5 的 E3 是「已在参考环境验证」, 一条没跑通的旅程不构成验证。"
        )

    # ── S15 — 签字身份: 执行者不能给自己签用户验收 ──
    if signoff["status"] == "approved" and signoff.get("user"):
        user = signoff["user"]
        if user == execution["operator"]:
            problems.append(
                f"[S15] signoff.user 与 execution.operator 同为 {user!r} — "
                "E4 的定义是「用户按真实场景完成 UAT」, 执行者不能自己签发。"
            )
        model_names = {m["name"] for m in manifest["environment"]["models"]}
        if user in model_names:
            problems.append(f"[S15] signoff.user ({user!r}) 是本次旅程使用的模型之一 — 模型不能替用户验收。")

    # ── S17 — dirty 树只允许出现在 ≤E2 的回填件里 (L596: 发布证据须 dirty=false) ──
    # schema 曾把 dirty 写死 const false, 结果是一份如实回填的 manifest 只能在这里
    # 写假话 (红队 example-fidelity O4)。现在 schema 放开为 boolean, 由本规则把住
    # 发布线: live 实录与 E3+ 一律 false, 回填件可以承认当时树是脏的 —— 代价是
    # 它永远升不到 E3+, 这正是应有的代价。
    if manifest["candidate"]["dirty"]:
        if provenance["mode"] != "reconstructed":
            problems.append(
                "[S17] candidate.dirty=true 只允许出现在 provenance.mode=reconstructed "
                "的回填件里 —— 实录证据必须跑在干净树上 (L596)。"
            )
        if level not in _RECONSTRUCTED_MAX:
            problems.append(
                f"[S17] candidate.dirty=true 与 evidence_level={level} 不相容 —— "
                "脏树上跑出来的东西最高只能是 E2, 不构成发布证据。"
            )

    # ── S16 — E3+ 的 skip/mock 文本痕迹 (启发式, 见 README 已知边界) ──
    if is_e3_plus and not skips["declared"]:
        hits = _scan_skip_mock_markers(manifest)
        for where, snippet in hits:
            problems.append(
                f"[S16] {where} 出现 skip/mock 痕迹 ({snippet!r}), 而 "
                "skips_or_mocks.declared=false 且等级为 "
                f"{level} — 二者不能同时为真。如确非 skip/mock, 改写措辞; "
                "如确是, 本旅程不能标 E3+。"
            )

    return problems


# ─────────────────────────────────────────────────────────────
# 产物层 A0..A3
# ─────────────────────────────────────────────────────────────


def resolve_artifact_path(path_value: str, manifest_path: Path) -> Path:
    """把 artifact 路径解析为绝对路径, 并做越界/symlink 检查。

    A0 安全约束 (Codex round-1 BLOCKER): --verify-artifacts 会读取被指文件, 若不约束
    则 `repo://../../../../etc/passwd` 可造成任意文件读取 + checksum 不符时回显实际
    摘要形成 hash oracle。四重防线: schema 正则 (禁绝对/../反斜杠) → 控制字符拒绝 →
    解析后 containment 检查 → symlink 拒绝。另禁 repo:// 指向证据树内部 (红队 R25:
    否则可以拿别的 RC 的产物当自己的证据)。
    """
    if path_value.startswith(_REPO_PREFIX):
        rel = path_value[len(_REPO_PREFIX) :]
        base = REPO_ROOT
        via_repo = True
    else:
        rel = path_value
        base = manifest_path.resolve().parent
        via_repo = False

    # 控制字符 (含换行): schema 正则的 `.*` 不跨行, 换行能让 `..` 藏在第二行躲过
    # 那道 lookahead (实测: 'ok.txt\n../../etc/passwd' 过正则)。此处兜住 —— 且行式
    # 清单 (shasum -c 之类) 遇到带换行的路径本就会错位, 直接拒最省事。
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in rel):
        raise _ArtifactPathError(f"artifact 路径含控制字符: {path_value!r}")

    candidate = Path(rel)
    if candidate.is_absolute() or rel.startswith("~"):
        raise _ArtifactPathError(f"artifact 路径必须相对: {path_value}")
    if ".." in candidate.parts:
        raise _ArtifactPathError(f"artifact 路径禁止 .. 上跳: {path_value}")

    target = (base / candidate).resolve()
    base_resolved = base.resolve()
    if not target.is_relative_to(base_resolved):
        raise _ArtifactPathError(f"artifact 路径解析后逃出 {base_resolved}: {path_value} → {target}")
    if via_repo and target.is_relative_to(EVIDENCE_ROOT.resolve()):
        raise _ArtifactPathError(
            f"repo:// 不得指向证据树内部 ({path_value}) — "
            "本旅程的产物应放在自己目录里; 引用别处的证据目录会让一份产物同时给多个 RC 背书。"
        )
    # symlink 可绕过 containment (指向外部) —— 逐级拒绝
    probe = base_resolved / candidate
    for part in [probe, *probe.parents]:
        if part == base_resolved:
            break
        if part.is_symlink():
            raise _ArtifactPathError(f"artifact 路径含 symlink, 拒绝跟随: {path_value}")
    return target


class _ArtifactPathError(RuntimeError):
    """artifact 路径越界 —— 属"内容不合格"(退出码 1)。"""


def _verify_artifacts(manifest: dict[str, Any], manifest_path: Path) -> list[str]:
    """重算 artifacts[].sha256 与磁盘比对。文件缺失即失败 (不静默跳过)。

    路径越界的条目在 _check_artifact_paths 已报过 A0, 这里静默跳过不重复上报
    —— 也不能读它 (那正是 A0 要拦的事)。
    """
    problems: list[str] = []
    for art in manifest["artifacts"]:
        via_repo = art["path"].startswith(_REPO_PREFIX)
        try:
            target = resolve_artifact_path(art["path"], manifest_path)
        except _ArtifactPathError:
            continue
        if not target.is_file():
            what = "是目录不是文件" if target.is_dir() else "不存在"
            problems.append(f"[A1] artifact {what}: {art['path']} → {target}")
            continue
        try:
            raw = target.read_bytes()
        except OSError as exc:
            problems.append(f"[A1] artifact 读取失败: {art['path']} — {exc}")
            continue
        digest = hashlib.sha256(raw).hexdigest()
        if digest != art["sha256"]:
            if via_repo:
                # repo:// 指向证据目录之外的仓内文件; 回显实际摘要会把 CI 日志变成
                # 任意仓内文件的 hash/size oracle (红队 R29)。只报不符, 不报数值。
                problems.append(f"[A2] artifact checksum 与磁盘不符: {art['path']} (repo:// 目标的实际摘要不回显)")
            else:
                problems.append(
                    f"[A2] artifact checksum 不符: {art['path']}"
                    f"\n      manifest: {art['sha256']}\n      实际:     {digest}"
                )
        if len(raw) != art["bytes"]:
            if via_repo:
                problems.append(f"[A3] artifact 字节数与磁盘不符: {art['path']} (实际值不回显)")
            else:
                problems.append(f"[A3] artifact 字节数不符: {art['path']} (manifest {art['bytes']} vs 实际 {len(raw)})")
    return problems


def _check_artifact_paths(manifest: dict[str, Any], manifest_path: Path) -> list[str]:
    """不读文件, 只做 A0 路径安全检查 —— 默认档也跑, 越界路径本身即不合格。"""
    problems: list[str] = []
    for art in manifest["artifacts"]:
        try:
            resolve_artifact_path(art["path"], manifest_path)
        except _ArtifactPathError as exc:
            problems.append(f"[A0] {exc}")
    return problems


# ─────────────────────────────────────────────────────────────
# 单文件校验
# ─────────────────────────────────────────────────────────────


def validate_manifest(
    manifest_path: Path,
    schema: dict[str, Any],
    *,
    verify_artifacts: bool = True,
    now: datetime | None = None,
) -> list[str]:
    """校验单个 manifest。返回问题列表 (空 = 通过)。

    产物校验**默认开启** (红队 R26: opt-in 意味着文档给的单文件命令根本不看产物存不存在);
    `--skip-artifact-verify` 是显式弃权。

    文件不存在 / JSON 语法错 / 编码错按 ConfigError 抛出 (退出码 2);
    JSON 合法但形状不对 (顶层非对象、重复 key) 归"内容不合格"(退出码 1)。
    """
    try:
        manifest = _load_json_document(manifest_path)
    except _DuplicateKeyError as exc:
        return [f"[json] {exc} — 重复 key 会让后值静默覆盖前值, 直接拒收。"]
    if not isinstance(manifest, dict):
        return [f"[json] 顶层必须是 JSON 对象, 实际 {type(manifest).__name__} — manifest 形状不对, 不是环境问题。"]

    validator = _get_validator(schema)
    structural = [
        "[schema] " + ("/".join(str(p) for p in err.absolute_path) or "<root>") + f": {err.message}"
        for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path))
    ]
    if structural:
        # 结构层不过就不跑语义层 —— 后者假定字段存在, 硬跑只会得到 KeyError 噪声
        return structural

    problems = _semantic_checks(manifest, manifest_path, now=now)
    problems.extend(_check_artifact_paths(manifest, manifest_path))
    if verify_artifacts:
        problems.extend(_verify_artifacts(manifest, manifest_path))
    return problems


def discover_manifests(root: Path = EVIDENCE_ROOT) -> list[Path]:
    """递归找出证据树下所有 manifest.json。

    红队 R28: 单层 glob 只看 `<rc>/journeys/<Jxx>/`, 而 S6 接受任意嵌套深度 ——
    一份放在 `<team>/<rc>/journeys/<Jxx>/` 的合法 manifest 对 CI 全扫永久隐形。
    改递归后由 S6 负责判定形状, 发现不再漏。
    """
    if not root.is_dir():
        raise ConfigError(f"证据根目录不存在: {root}")
    return sorted(p for p in root.rglob("manifest.json") if p.is_file())


def check_rc_completeness(rc: str, root: Path = EVIDENCE_ROOT, *, schema: dict[str, Any] | None = None) -> list[str]:
    """RC 发布门: 该 rc 下 J01-J10 齐全、全为 live 实录、同一候选 SHA、全部 E3+ 且通过。

    存在理由 (Codex round-1 MEDIUM): `--all` 只 lint 已存在的文件, 一份格式演示件就能
    让 CI 长绿 —— 那证明不了"这个 RC 的证据齐了"。发布前须显式跑本门。

    红队整改: rc 必须是**名字**不是路径 (否则 `--require-complete ../../tmp/x` 能用仓外
    伪造件满足发布门); 拒绝 symlink 目录 (否则一条真旅程软链九次即可"齐全"); 并按
    §12.6「J01–J10 全部达到 E3」核对等级、结果与同一 RC SHA。
    """
    problems: list[str] = []
    if not _RC_NAME_RE.fullmatch(rc):
        return [
            f"[RC] {rc!r} 不是合法的 rc 名 (须匹配 {_RC_NAME_RE.pattern}) — "
            "本门只接受证据树内的 rc 目录名, 不接受任意路径。"
        ]
    rc_dir = root / rc / "journeys"
    if not rc_dir.is_dir():
        return [f"[RC] {rc} 下没有 journeys/ 目录 — 该 RC 无任何证据。"]

    shas: dict[str, str] = {}
    for jid in ALL_JOURNEYS:
        jdir = rc_dir / jid
        path = jdir / "manifest.json"
        if jdir.is_symlink() or path.is_symlink():
            problems.append(f"[RC] {jid} 的目录或 manifest 是 symlink — 同一份证据软链多次冒充多条旅程。")
            continue
        if not path.is_file():
            problems.append(f"[RC] 缺 {rc}/journeys/{jid}/manifest.json")
            continue
        try:
            doc = _load_json_document(path)
        except (ConfigError, _DuplicateKeyError) as exc:
            problems.append(f"[RC] {jid} 装载失败: {exc}")
            continue
        if not isinstance(doc, dict):
            problems.append(f"[RC] {jid} 顶层不是对象")
            continue
        mode = (doc.get("provenance") or {}).get("mode")
        if mode != "live":
            problems.append(f"[RC] {jid} 的 provenance.mode={mode!r} — RC 门只认 live 实录, 回填/演示件不计入完整性。")
        level = doc.get("evidence_level")
        if level not in _E3_PLUS:
            problems.append(f"[RC] {jid} 的 evidence_level={level!r} — §12.6 要求 J01-J10 全部达到 E3。")
        outcome = doc.get("result")
        if outcome != "pass":
            problems.append(f"[RC] {jid} 的 result={outcome!r} — 未通过的旅程不构成发布证据。")
        sha = (doc.get("candidate") or {}).get("sha")
        if isinstance(sha, str):
            shas[jid] = sha
    if len({*shas.values()}) > 1:
        detail = ", ".join(f"{j}={s[:12]}…" for j, s in sorted(shas.items()))
        problems.append(
            f"[RC] 十条旅程不在同一个候选 SHA 上 ({detail}) — RC 是一个冻结的 SHA, 不是十次不同构建的拼盘。"
        )
    return problems


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────


def _rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def _run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Release 旅程证据 manifest 校验器 (CARD-R-EVD)",
    )
    parser.add_argument("manifests", nargs="*", type=Path, help="待校验的 manifest.json")
    parser.add_argument(
        "--all",
        action="store_true",
        help="递归扫 docs/release-evidence 下全部 manifest.json",
    )
    parser.add_argument(
        "--skip-artifact-verify",
        action="store_true",
        help="弃权: 不重算 artifacts[].sha256 与磁盘比对 (默认是要算的)",
    )
    parser.add_argument(
        "--verify-artifacts",
        action="store_true",
        help="(已是默认行为, 保留以兼容既有命令行)",
    )
    parser.add_argument(
        "--require-complete",
        metavar="RC",
        help="RC 发布门: 该 rc 下 J01-J10 齐全、全 live 实录、同一候选 SHA、全部 E3+ 且通过",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=SCHEMA_PATH,
        help="schema 文件路径 (默认 docs/release-evidence/manifest.schema.json)",
    )
    args = parser.parse_args(argv)

    if not args.manifests and not args.all and not args.require_complete:
        parser.error("需要至少一个 manifest 路径, 或 --all / --require-complete")

    verify_artifacts = not args.skip_artifact_verify

    try:
        schema = load_schema(args.schema)
    except ConfigError as exc:
        print(f"❌ 配置错误: {exc}", file=sys.stderr)
        return 2

    targets: list[Path] = list(args.manifests)
    try:
        if args.all:
            discovered = discover_manifests()
            if not discovered:
                print(
                    "⚠️  docs/release-evidence 下没有任何 manifest — 空证据目录不算通过, 按配置错误处理。",
                    file=sys.stderr,
                )
                return 2
            targets.extend(p for p in discovered if p not in targets)
    except ConfigError as exc:
        print(f"❌ 配置错误: {exc}", file=sys.stderr)
        return 2

    if args.require_complete and _RC_NAME_RE.fullmatch(args.require_complete):
        rc_dir = EVIDENCE_ROOT / args.require_complete / "journeys"
        for jid in ALL_JOURNEYS:
            path = rc_dir / jid / "manifest.json"
            if path.is_file() and path not in targets:
                targets.append(path)

    failed = 0
    for target in targets:
        try:
            problems = validate_manifest(target, schema, verify_artifacts=verify_artifacts)
        except ConfigError as exc:
            # 单份文件装载失败不再中断整批 —— 否则一个手抖的逗号会把后面所有 manifest
            # 的违规一起藏起来, 还被报成"环境错误"(红队 R-LOW)。退出码 2 只留给
            # schema 指纹/依赖缺失这类真正的环境问题。
            failed += 1
            print(f"❌ FAIL {_rel(target)}")
            print(f"    [load] {exc}")
            continue
        if problems:
            failed += 1
            print(f"❌ FAIL {_rel(target)}")
            for problem in problems:
                print(f"    {problem}")
        else:
            print(f"✅ PASS {_rel(target)}")

    if targets:
        print(f"\n合计 {len(targets)} 份 manifest, 失败 {failed} 份。")
        if not verify_artifacts:
            print("⚠️  已弃权 artifact checksum 真验 (--skip-artifact-verify)。")

    if args.require_complete:
        rc_problems = check_rc_completeness(args.require_complete)
        if rc_problems:
            failed += 1
            print(f"\n❌ RC 完整性门 FAIL ({args.require_complete}):")
            for problem in rc_problems:
                print(f"    {problem}")
        else:
            print(
                f"\n✅ RC 完整性门 PASS ({args.require_complete}): "
                "J01-J10 齐全、均为 live 实录、同一候选 SHA、全部 E3+ 且通过。"
            )

    return 1 if failed else 0


def main() -> int:  # pragma: no cover - 薄封装
    return _run()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
