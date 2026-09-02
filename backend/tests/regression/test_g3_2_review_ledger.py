"""CARD-G3-2 per-vault 复习事件账本落地 — write-ahead 写序 + 单写者语义行为门。

[BATCH-2026-09-01-第八批 / CARD-G3-2]

锁的是 schema v1 §6.2 落进 quiz-answer 静态块 + fsrs_bridge 后的**行为**:
  1. A1 write-ahead (先 durable append 后 apply/发布) — 由耐久序列 spy 门证明
     调用序列, **不**证明掉电后数据存活 (那需要真实断电/故障注入, 不在本卡);
  2. A2 恢复先于新写 (pending 增量重放, 基线=当前 frontmatter; dup 自身的
     FSRS 应用走重放, restore 只补评分链其余副作用, 绝不二次 apply);
  3. A3 等时唯一口径 = 写侧推进 W+1s (bridge 内实现);
  4. A5 整秒 (bridge 入口截断; review_time 与 W 同一瞬间);
  5. A6 UTC 归一 + naive 拒收 (bridge);
  6. A4.5 parsed-field 查重 + LF 守卫 + 短写校验 + envelope 冲突门;
  7. 裁决② degraded: fsrs 不可用 → 事件仍落账、两键成对哨兵、W 不推进;
  8. 裁决③ 残缺卡 fail-closed 零写;
  9. 写点普查不新增第三套实现 (全仓 grep 门)。

fixture 与生产同源 (MEMORY: fixture 形态 ≠ 生产形态):
  - 被测静态块从 SKILL.md **逐字提取** (仅 P 常量重定向, 同 G3-1 范式);
  - 节点 frontmatter 逐字仿 live 真实形态 (裸值/字段顺序/calibration_log 缩进);
  - validator/bridge/decay_beta 经 symlink 引真文件 (漂移即测到);
  - vault_id 故意带连字符+中文 (`canvas-vault-测试`) — 写侧若漏 sanitize
    (事件写原始连字符形式) 校验器绑定比对当场翻红;
  - backend/.venv 必须是**目录** symlink: 文件级 symlink 启动 venv python
    会丢 pyvenv.cfg 探测 (2026-09-01 实测) → fsrs_unavailable 假降级。

契约文档: docs/learning-events-schema-v1.md §6.1-6.3
"""

import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

WT = Path(__file__).resolve().parents[3]
VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
VAULT_SCRIPTS = WT / "canvas-vault" / ".claude" / "scripts"

_SKILL_TEXT = SKILL.read_text(encoding="utf-8")
_MAIN_BLOCKS = [
    b
    for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", _SKILL_TEXT, re.DOTALL)
    if 'P = "/tmp/quiz-answer-payload.json"' in b
]
assert len(_MAIN_BLOCKS) == 1, f"SKILL.md 应恰有 1 个主写点 PYEOF 块, 实见 {len(_MAIN_BLOCKS)}"
#: 逐字提取的主写点 (运行时按 P 常量重定向到 tmp fixture)
CODE = _MAIN_BLOCKS[0]

NODE_REL = "节点/测试节点.md"
EID = "测试检验-2026-08-01-1000#q1"
TS1 = "2026-08-01T10:00:00Z"

#: 逐字仿 live 真实节点形态 (裸值; 裸词键第 0 列; calibration_log 条目缩进两格)
NODE_V0 = (
    '---\ntype: concept\nmastery_score: 0.5\ntitle: 测试节点\nsource_board: "[[原白板/CS 61B]]"\n---\n测试节点正文。\n'
)
#: canonical Review 态 (classify_card_state → normal), W = 10:00:00Z
NODE_REVIEW_W10 = (
    "---\n"
    "type: concept\n"
    "mastery_score: 0.5\n"
    "fsrs_due: 2026-08-11T13:56:58Z\n"
    "fsrs_state: 2\n"
    "fsrs_stability: 10.0\n"
    "fsrs_difficulty: 5.0\n"
    "fsrs_last_review: 2026-08-01T10:00:00Z\n"
    "title: 测试节点\n"
    "---\n"
    "测试节点正文。\n"
)


#: R4 字节对拍用: canonical Review 态 + last_examined + W **远晚于**本次评分
#: 时刻 ⇒ A3 把 review_time 推到 W+1s (与 payload ts 差 4 个月)。含 idle 状态
#: 才能让 mastery 的闲置折旧基准差异显形 (门②的新卡无 last_examined, 测不到)。
NODE_IDLE_A3 = (
    "---\n"
    "type: concept\n"
    "mastery_score: 0.5\n"
    "mastery_a: 3.0\n"
    "mastery_b: 3.0\n"
    "attempt_count: 2\n"
    'last_examined: "2026-07-01T00:00:00Z"\n'
    "fsrs_due: 2026-12-11T13:56:58Z\n"
    "fsrs_state: 2\n"
    "fsrs_stability: 10.0\n"
    "fsrs_difficulty: 5.0\n"
    "fsrs_last_review: 2026-12-01T10:00:00Z\n"
    "title: 测试节点\n"
    "---\n"
    "测试节点正文。\n"
)


def _review_row(**over):
    """一条 canonical review/1 durable 行 (与生产写点键集逐字同形)。"""
    row = {
        "event_id": "quiz:板A#q1",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": {
            "schema_ext": "review/1",
            "vault_id": "canvas_vault_测试",
            "concept_id": "测试节点",
            "rating": 3,
            "grade_norm": 0.75,
            "review_time": TS1,
            "fsrs_library_version": "degraded:historic-run",
            "fsrs_params_hash": "degraded:historic-run",
            "exam_board": "检验白板/板A.md",
            "attempt_count": 1,
        },
    }
    for k, v in over.items():
        if k.startswith("payload."):
            row["payload"][k.split(".", 1)[1]] = v
        else:
            row[k] = v
    return row


def _write_ledger(vault: Path, *rows, trailing_lf=True):
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    if not trailing_lf and text.endswith("\n"):
        text = text[:-1]
    (vault / "learning_events.jsonl").write_text(text, encoding="utf-8")


def _payload(**kw):
    base = {
        "node": NODE_REL,
        "grade_norm": 0.752,
        "ts": TS1,
        "event_id": EID,
        "exam_board": "检验白板/测试检验-2026-08-01-1000.md",
        "question_id": "q1",
        "source_board": "[[原白板/CS 61B]]",
        "self_confidence_raw": "半懂",
        "self_confidence_norm": 0.5,
        "abandoned": False,
        "callout": "",
    }
    base.update(kw)
    return base


@pytest.fixture()
def vault(tmp_path):
    """完整镜像布局: REPO=tmp_path, VAULT=tmp_path/canvas-vault。

    被测代码 (validator/bridge/decay_beta) 全部 symlink 引真文件 —
    主树漂移即被本文件测到, fsrs 真实参与。
    ⚠️ Codex round-1 MEDIUM 如实声明: bridge 是 symlink, 其 `_venv_python()`
    对 `__file__` 调 resolve() 会穿回 WT — re-exec 实际命中 **WT 的 venv**
    (与 fixture 同一解释器, 结果等价), tmp 的目录级 backend/.venv symlink
    **不参与** re-exec 选路 (保留它是为了 bridge 若改为 copy 布局仍可达,
    及文件级 symlink 会丢 pyvenv.cfg 的实测教训)。本 fixture 证明的是
    「bridge re-exec 链可达且 fsrs 真实参与」, 不是「tmp candidate 被选中」。
    """
    repo = tmp_path
    v = repo / "canvas-vault"
    (v / "节点").mkdir(parents=True)
    (v / ".claude" / "scripts").mkdir(parents=True)
    (repo / "backend" / "scripts").mkdir(parents=True)
    (repo / "backend" / ".venv").symlink_to(WT / "backend" / ".venv", target_is_directory=True)
    (repo / "backend" / "scripts" / "validate_learning_events.py").symlink_to(VALIDATOR)
    (v / ".claude" / "scripts" / "fsrs_bridge.py").symlink_to(VAULT_SCRIPTS / "fsrs_bridge.py")
    (v / ".claude" / "scripts" / "decay_beta.py").symlink_to(VAULT_SCRIPTS / "decay_beta.py")
    # 故意连字符+中文: 校验器绑定的是 sanitize 后的 canvas_vault_测试;
    # 写侧漏 sanitize (写原始形式) 会在 validator 绑定比对处翻红
    (v / ".canvas-config.yaml").write_text(
        '# 测试 config\nvault_id: "canvas-vault-测试"\nsubject: cs-61b\n', encoding="utf-8"
    )
    (v / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    return v


def _writer_code(vault: Path, payload: dict) -> str:
    pfile = vault.parent / "payload.json"
    pfile.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return CODE.replace('"/tmp/quiz-answer-payload.json"', json.dumps(str(pfile)))


def _run_writer(vault: Path, payload: dict, env_extra: dict | None = None):
    """生产形态执行: 子进程 + cwd=vault (NODE 相对路径与生产一致)。"""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **(env_extra or {}))
    return subprocess.run(
        [sys.executable, "-c", _writer_code(vault, payload)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(vault),
        env=env,
    )


def _sha(p: Path) -> str:
    import hashlib

    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_face(vault: Path):
    """整个写入面的快照：节点 + 账本。零写断言比这个。

    只比节点 sha 对「账本被追加」失明；只比账本行数对「行内容被改」失明。
    审查实测：在 fail-closed 分支里插一行账本追加，只比节点 sha 的门全绿。
    """
    lp = vault / "learning_events.jsonl"
    return (_sha(vault / NODE_REL), _sha(lp) if lp.exists() else None)


def _run_writer_settled(vault: Path, payload: dict, env_extra: dict | None = None):
    """跑写点；若因「A2 恢复先落定」被要求重跑，就再跑一次并返回合并结果。

    存在 foreign pending 时写点会先把恢复结果原子发布、再以非零码退出要求重跑
    （Codex round-3 BLOCKER 的修法：恢复与新写不在同一次运行里混做，否则被恢复
    事件的 mastery/校准会连同「多 pending 攒在一起」一起变得不可证）。
    只关心「最终有没有写成」的门用这个；专门验证两阶段语义的门直接用 _run_writer。
    """
    r = _run_writer(vault, payload, env_extra)
    if r.returncode != 0 and "恢复已落定" in r.stderr:
        r2 = _run_writer(vault, payload, env_extra)
        return subprocess.CompletedProcess(r2.args, r2.returncode, r.stdout + r2.stdout, r.stderr + r2.stderr)
    return r


def _ledger_lines(vault: Path) -> list[dict]:
    ledger = vault / "learning_events.jsonl"
    if not ledger.exists():
        return []
    return [json.loads(ln) for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _fm(vault: Path) -> str:
    import yaml

    text = (vault / NODE_REL).read_text(encoding="utf-8")
    return text.split("---\n")[1]


def _fm_fields(vault: Path) -> dict:
    """按 bridge 同款正则抽 fsrs_* 行 (值+冒号后文本)。"""
    fm = _fm(vault)
    out = {}
    for key in ("fsrs_due", "fsrs_state", "fsrs_step", "fsrs_stability", "fsrs_difficulty", "fsrs_last_review"):
        m = re.search(rf"^{key}:\s*\"?([^\"\n]+?)\"?\s*$", fm, re.M)
        if m:
            out[key] = m.group(1)
    return out


def _run_validator(vault: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(vault / "learning_events.jsonl")],
        capture_output=True,
        text=True,
        timeout=60,
    )


# ── 门① 同 event_id 重放两次 → frontmatter 不二次推进、账本一行 ──


def test_same_event_id_replay_no_double_advance(vault):
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    w1 = _fm_fields(vault)["fsrs_last_review"]
    ledger = vault / "learning_events.jsonl"
    n1 = len(_ledger_lines(vault))
    # 二跑: recorded_at 变化不构成事实差异 (envelope 显式排除), 必须 no-op
    r2 = _run_writer(vault, _payload(ts="2026-09-01T09:00:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == w1, "同 event_id 重放不得二次推进 W"
    assert len(_ledger_lines(vault)) == n1 == 1, "账本必须恰 1 行"
    assert "幂等跳过" in r2.stdout


# ── 门② 中断注入: 事件已落账、frontmatter 未推进 → A2 重放恢复 ──


def test_crash_window_ledger_without_frontmatter_recovers(vault):
    """卡文 (c)② 字面判据: 恢复产物与直接应用**逐字节相同** (round-2 HIGH:
    旧版只比 FSRS 子集; 现全部副作用 last_examined/calibration.ts 以 durable
    业务时刻为基准, 整节点字节对拍)。"""
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    golden_bytes = (vault / NODE_REL).read_bytes()
    # 模拟崩溃窗口①: 回滚 frontmatter 到评分前 (账本保留该事件)
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    r2 = _run_writer(vault, _payload(ts="2026-09-01T09:30:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert len(_ledger_lines(vault)) == 1, "恢复路径不得二次 append"
    assert (vault / NODE_REL).read_bytes() == golden_bytes, (
        "恢复产物必须与直接应用逐字节相同 (side effects 以 durable review_time 为基准)"
    )
    assert "A2 重放已应用" in r2.stdout or "崩溃窗口" in r2.stdout


# ── 门③ 追加即崩 (事件未落账) → 账本与 frontmatter 一致 (零写) ──


def test_fail_before_append_keeps_ledger_and_node_consistent(vault):
    """bridge exit 2 (naive ts) 在 append 之前 fail-closed — 系统保持评分前
    一致态, 重跑即可 (scored_pending_node_update 续跑语义)。"""
    _face_node = _write_face(vault)
    r = _run_writer(vault, _payload(ts="2026-08-01T10:00:00"))
    assert r.returncode != 0, "naive ts 必须拒绝"
    assert _write_face(vault) == _face_node, "fail-closed 必须零写（节点 + 账本）"
    assert not (vault / "learning_events.jsonl").exists(), "fail-closed 必须零写账本"


# ── 门④ 等时 → W+1s (A3 推进口径) ──


def test_equal_timestamp_advances_w_plus_one_second(vault):
    (vault / NODE_REL).write_text(NODE_REVIEW_W10, encoding="utf-8")
    r = _run_writer(vault, _payload(ts="2026-08-01T10:00:00Z"))
    assert r.returncode == 0, r.stdout + r.stderr
    rec = _ledger_lines(vault)[0]
    assert rec["payload"]["review_time"] == "2026-08-01T10:00:01Z", "等时必须推进 W+1s"
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-01T10:00:01Z"
    assert rec["payload"]["review_time"] == rec["effective_at"], "review_time 与 effective_at 同一瞬间"
    assert _run_validator(vault).returncode == 0


# ── 门⑤ 小数秒输入 → 整秒 (A5) ──


def test_fractional_second_input_truncated_to_whole_second(vault):
    r = _run_writer(vault, _payload(ts="2026-08-01T10:00:00.731Z"))
    assert r.returncode == 0, r.stdout + r.stderr
    rec = _ledger_lines(vault)[0]
    assert rec["payload"]["review_time"] == "2026-08-01T10:00:00Z", "小数秒必须入口截断"
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-01T10:00:00Z"
    assert _run_validator(vault).returncode == 0, "整秒产物必须过校验器"


# ── 门⑥ 残缺卡 → fail-closed 零写 (裁决③) ──


def test_degraded_card_fail_closed_zero_write(vault):
    broken = NODE_V0.replace(
        "mastery_score: 0.5\n",
        "mastery_score: 0.5\nfsrs_last_review: 2026-08-01T10:00:00Z\n",
    )  # 只有 W 缺 due/state → classify degraded
    (vault / NODE_REL).write_text(broken, encoding="utf-8")
    _face_deg = _write_face(vault)
    sha = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload())
    assert r.returncode != 0, "残缺卡必须 fail-closed"
    assert "残缺" in r.stderr or "fail-closed" in r.stderr, r.stderr
    assert _write_face(vault) == _face_deg, "残缺卡必须零写（节点 + 账本）"
    assert not (vault / "learning_events.jsonl").exists(), "残缺卡必须零写账本"


# ── 门⑦ 截断尾行无 LF → 后续追加不粘连 (LF 守卫) ──


def test_truncated_tail_line_without_lf_guard(vault):
    """§二 截断自愈: 真实崩溃产物是 **半个 JSON** 且无尾 LF — 读取时跳过
    留痕, 追加前 LF 守卫隔离, 新事件必须独立可解析 (Codex round-1 HIGH:
    旧版只测「完整 JSON 缺 LF」, partial-JSON 在读取阶段就 fail-closed,
    自愈路径不可达)。"""
    ledger = vault / "learning_events.jsonl"
    full = json.dumps(
        {
            "event_id": "exam:旧板",
            "event_version": 1,
            "event_type": "exam_created",
            "node_id": "旧节点",
            "recorded_at": TS1,
            "effective_at": TS1,
            "payload": {"exam_board": "检验白板/旧板.md"},
        },
        ensure_ascii=False,
    )
    torn = '{"event_id": "quiz:被截断的事件", "event_version": 1, "event_ty'
    ledger.write_text(full + "\n" + torn, encoding="utf-8")  # 第二行为 partial JSON, 无尾 LF
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    assert "截断尾行" in r.stdout, "截断尾行必须留痕"
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 3, f"新事件必须独立成行 (LF 守卫隔离截断行), 实得 {len(lines)} 行"
    assert json.loads(lines[0])["event_id"] == "exam:旧板", "完整旧行必须原样保留"
    assert json.loads(lines[2])["event_id"] == "quiz:" + EID, "新事件行必须独立可解析"
    # 校验器如实把坏行报 FAIL (审计暴露损坏), 但坏行不连坐新行
    v = _run_validator(vault)
    assert v.returncode == 1 and "JSON 解析失败" in v.stdout, "坏行必须被校验器如实暴露"


# ── 门⑧ envelope 冲突 (同 id 不同 event_type) → 拒绝; 同 envelope → no-op ──


def test_envelope_conflict_rejected_and_same_envelope_noop(vault):
    # ①同 id 同 envelope: 完整成功后再跑, 绝不二次 apply (W 不动即证明)
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    sha = _sha(vault / NODE_REL)
    r2 = _run_writer(vault, _payload(ts="2026-09-01T08:00:00Z"))
    assert r2.returncode == 0
    assert _sha(vault / NODE_REL) == sha, "同 id 同 envelope 重放不得二次 apply"
    # ②同 id 不同事实 (abandoned 翻转 event_type) → fail-closed 拒写
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 回到崩溃窗口①前置态
    _sha_pre_conflict = _sha(vault / NODE_REL)
    r3 = _run_writer(vault, _payload(abandoned=True))
    assert r3.returncode != 0, "同 id 不同 event_type 必须 envelope 冲突拒绝"
    assert "envelope 冲突" in r3.stderr, r3.stderr
    assert len(_ledger_lines(vault)) == 1, "冲突拒绝不得追加"
    assert _sha(vault / NODE_REL) == _sha_pre_conflict, "冲突拒绝必须整节点零写（不只是 fsrs 字段）"
    # ③Codex round-1 BLOCKER: 五字段局部比对抓不到的篡改 — durable 行被
    # 改动 payload 事实键 (exam_board) / 顶层 event_version 后, 恢复必须拒。
    base_event = _ledger_lines(vault)[0]
    for tweak, desc in (
        ({"payload.exam_board": "检验白板/被篡改.md"}, "payload 事实键 exam_board"),
        ({"event_version": 2}, "顶层 event_version"),
    ):
        tampered = json.loads(json.dumps(base_event))
        key, val = next(iter(tweak.items()))
        if "." in key:
            tampered["payload"][key.split(".")[1]] = val
        else:
            tampered[key] = val
        ledger = vault / "learning_events.jsonl"
        ledger.write_text(json.dumps(tampered, ensure_ascii=False) + "\n", encoding="utf-8")
        rt = _run_writer(vault, _payload())
        assert rt.returncode != 0, f"篡改 {desc} 后恢复必须拒绝"
        # event_version 篡改现被更早的**版本门**接管（未知版本不得按 v1 应用，
        # 也不能跳过——跳过就漏算了）；payload 事实键仍走 envelope。
        assert ("envelope 冲突" in rt.stderr) or ("非 v1" in rt.stderr), rt.stderr
    # 恢复正常 durable 行后 (原样回写), 同一续跑必须成功 (崩溃窗口①恢复)
    (vault / "learning_events.jsonl").write_text(json.dumps(base_event, ensure_ascii=False) + "\n", encoding="utf-8")
    r4 = _run_writer(vault, _payload())
    assert r4.returncode == 0, r4.stdout + r4.stderr
    assert "恢复" in r4.stdout and "崩溃窗口" in r4.stdout


# ── 门⑨ 产物过校验器 (含 golden 绑定) + vault_id 规范化 ──


def test_ledger_passes_validator_with_golden_binding(vault):
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    v = _run_validator(vault)
    assert v.returncode == 0, v.stdout + v.stderr
    rec = _ledger_lines(vault)[0]
    pl = rec["payload"]
    assert pl["schema_ext"] == "review/1"
    assert pl["vault_id"] == "canvas_vault_测试", "vault_id 必须是 sanitize 规范化形式"
    assert pl["concept_id"] == rec["node_id"]
    assert pl["review_time"] == rec["effective_at"]
    # golden 绑定: 非 degraded 时与 manifest 真值相等 (校验器已查, 这里锁键存在)
    manifest = json.loads((WT / "backend" / "tests" / "regression" / "fsrs_golden_manifest.json").read_text())
    assert pl["fsrs_library_version"] == manifest["library_version"]
    assert pl["fsrs_params_hash"] == manifest["params_hash"]
    # rating 与 grade_norm 同源 (bridge rating_from_grade 口径, 档界 GN2=0.75→3)
    assert pl["rating"] == 3 and pl["grade_norm"] == 0.75
    assert _fm_fields(vault)["fsrs_last_review"] == pl["review_time"], "W 必须等于 review_time"


# ── 门⑩ 节点除 frontmatter 外 body 逐字节不变 ──


def test_node_body_byte_identical(vault):
    before = (vault / NODE_REL).read_text(encoding="utf-8")
    body_before = before.split("---\n", 2)[2]
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    after = (vault / NODE_REL).read_text(encoding="utf-8")
    body_after = after.split("---\n", 2)[2]
    assert body_after == body_before, "正文必须逐字节不变 (callout 为空时)"


# ── 门⑪ 全仓写点普查: 无第三套实现 ──


def test_write_point_survey_no_third_implementation():
    cmd = (
        "grep -rn 'learning_events.jsonl' backend/app canvas-vault/.claude "
        "--include='*.py' --include='*.md' | grep -v tests | cut -d: -f1 | sort -u"
    )
    r = subprocess.run(["bash", "-c", cmd], cwd=str(WT), capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    files = {ln for ln in r.stdout.strip().splitlines() if ln}
    assert files == {
        "backend/app/services/learning_event_log.py",
        "canvas-vault/.claude/skills/ai-linked-doc/SKILL.md",
        "canvas-vault/.claude/skills/quiz-answer/SKILL.md",
        "canvas-vault/.claude/skills/start-exam-board/SKILL.md",
    }, f"写点普查漂移 (新写点必须先登记 schema 文档 §五): {files}"


# ── 门⑫ 裁决② degraded: 事件仍落账 + 哨兵成对 + W 不推进 ──


def test_fsrs_unavailable_degraded_sentinels_pair_and_w_frozen(vault):
    """FSRS_BRIDGE_REEXEC=1 阻断 re-exec; bridge 子进程用系统 python3
    (无 fsrs, 本机实证) → 诚实 exit 3 → 裁决②路径。"""
    r = _run_writer(vault, _payload(), env_extra={"FSRS_BRIDGE_REEXEC": "1"})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "degraded" in r.stdout
    rec = _ledger_lines(vault)[0]
    pl = rec["payload"]
    assert pl["fsrs_library_version"].startswith("degraded:"), "库版本必须填哨兵"
    assert pl["fsrs_params_hash"].startswith("degraded:"), "参数 hash 必须填哨兵"
    assert pl["fsrs_library_version"] == pl["fsrs_params_hash"], "两键哨兵必须成对 (同因)"
    assert pl["fsrs_library_version"][len("degraded:") :].strip(), "哨兵原因必须非空"
    assert not _fm_fields(vault), "degraded 不得写任何 fsrs_* 字段 (W 不推进)"
    assert "mastery_score" in _fm(vault), "衰减 Beta 照常写"
    assert _run_validator(vault).returncode == 0, "哨兵成对产物必须过校验器"
    # degraded 事件 review_time > W(无 W = -inf) → 留 pending; fsrs 恢复后
    # 下次评分的 A2 会自动补应用 (write-ahead 的价值, 产品可见)


# ── 门⑬ 耐久序列 + 写序 (A4.3/A4.4): spy 调用序列 ──
# ⚠️ 本门证明耐久序列**被调用** (fsync 覆盖账本/temp/父目录, append fsync 先于
# os.replace), 不证明掉电后数据存活 — 后者需真实断电, 不在本卡。


def test_durable_sequence_and_write_ahead_order(vault, monkeypatch):
    events: list[tuple] = []
    real_fsync, real_replace, real_open = os.fsync, os.replace, os.open

    def spy_fsync(fd):
        try:
            st = os.fstat(fd)
            kind = "dir" if stat.S_ISDIR(st.st_mode) else "file"
            events.append(("fsync", kind, st.st_ino))
        except OSError:
            events.append(("fsync", "unknown", -1))
        return real_fsync(fd)

    def spy_replace(src, dst):
        events.append(("replace", str(src), str(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "fsync", spy_fsync)
    monkeypatch.setattr(os, "replace", spy_replace)
    monkeypatch.chdir(vault)
    saved_path = list(sys.path)
    saved_modules = {
        k: sys.modules.pop(k) for k in ("fsrs_bridge", "decay_beta", "validate_learning_events") if k in sys.modules
    }
    try:
        exec(compile(_writer_code(vault, _payload()), "quiz-answer-SKILL-extract", "exec"), {})
    except SystemExit as e:
        assert e.code in (0, None), f"静态块异常退出: {e.code}"
    finally:
        sys.path[:] = saved_path
        sys.modules.pop("fsrs_bridge", None)
        sys.modules.pop("decay_beta", None)
        sys.modules.pop("validate_learning_events", None)
        sys.modules.update(saved_modules)

    ledger, node = vault / "learning_events.jsonl", vault / NODE_REL
    ledger_ino, node_ino = ledger.stat().st_ino, node.stat().st_ino
    fsyncs = [e for e in events if e[0] == "fsync"]
    replaces = [e for e in events if e[0] == "replace"]
    assert len(replaces) == 1, f"恰一次原子发布, 实得 {len(replaces)}"
    replace_idx = events.index(replaces[0])
    # 账本 fsync (file) 与 temp fsync (temp inode == 发布后节点 inode)
    fsynced_files = {e[2] for e in fsyncs if e[1] == "file"}
    assert ledger_ino in fsynced_files, "账本 fd 必须 fsync (A4.3)"
    assert node_ino in fsynced_files, "temp fd 必须 fsync (A4.4; replace 保留 inode)"
    dir_count = sum(1 for e in fsyncs if e[1] == "dir")
    assert dir_count >= 2, f"首建账本父目录 + 节点父目录均须 fsync, 实得 dir fsync {dir_count} 次"
    # Codex round-1 验证限制: dir fsync 必须绑定两个**不同**目录 inode
    # (VAULT 根 = 账本父目录, 节点/ = 节点父目录), 不是同一目录刷两次
    dir_inodes = {e[2] for e in fsyncs if e[1] == "dir"}
    assert len(dir_inodes) >= 2, f"两个不同父目录都要 fsync, 实得 {len(dir_inodes)} 个 inode"
    assert vault.stat().st_ino in dir_inodes, "账本父目录 (VAULT 根) 必须 fsync"
    assert (vault / "节点").stat().st_ino in dir_inodes, "节点父目录必须 fsync"
    # 写序: 账本 durable 必须先于 os.replace (真 write-ahead, 非改名)
    ledger_fsync_idx = max(i for i, e in enumerate(events) if e[0] == "fsync" and e[1] == "file" and e[2] == ledger_ino)
    temp_fsync_idx = max(i for i, e in enumerate(events) if e[0] == "fsync" and e[1] == "file" and e[2] == node_ino)
    assert ledger_fsync_idx < replace_idx, "账本 fsync 必须先于 frontmatter 发布 (A1 write-ahead)"
    assert temp_fsync_idx < replace_idx, "temp fsync 必须先于 os.replace (A4.4)"


# ── 门⑭ 历史行 (无 review/1 扩展) 不进 pending (§6.3) ──


def test_legacy_rows_never_replayed(vault):
    legacy = json.dumps(
        {
            "event_id": "quiz:旧事件",
            "event_version": 1,
            "event_type": "answer_scored",
            "node_id": "测试节点",
            "recorded_at": "2026-07-01T10:00:00Z",
            "effective_at": "2026-07-01T10:00:00Z",
            "payload": {"grade_norm": 1.0, "exam_board": "x", "attempt_count": 1},
        },
        ensure_ascii=False,
    )
    (vault / "learning_events.jsonl").write_text(legacy + "\n", encoding="utf-8")
    r = _run_writer(vault, _payload(ts="2026-08-02T10:00:00Z"))
    assert r.returncode == 0, r.stdout + r.stderr
    # 无 fsrs_* 字段的新卡: 旧事件不可重放 (无 review_time, 视为已应用),
    # W 恰为新事件时刻 — 若旧行被误重放 W 会先落到 2026-07-01
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-02T10:00:00Z"
    assert len(_ledger_lines(vault)) == 2
    assert _run_validator(vault).returncode == 0


# ── 门⑮ 跨事件 A2: 别的事件落账未应用 → 本次评分前重放至空 ──


def test_pending_foreign_event_replayed_before_new_write(vault):
    """run1 为事件 A 落账未应用 (崩溃), run2 换一张板考同一节点 (事件 B):
    A2 必须先重放 A 再计算 B — 单写者下交错窗口由 A2 消灭。"""
    event_a = {
        "event_id": "quiz:板A#q1",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": {
            "schema_ext": "review/1",
            "vault_id": "canvas_vault_测试",
            "concept_id": "测试节点",
            "rating": 3,
            "grade_norm": 0.75,
            "review_time": TS1,
            "fsrs_library_version": "degraded:historic-run",  # 哨兵行
            "fsrs_params_hash": "degraded:historic-run",
            "exam_board": "检验白板/板A.md",
            "attempt_count": 1,
        },
    }
    (vault / "learning_events.jsonl").write_text(json.dumps(event_a, ensure_ascii=False) + "\n", encoding="utf-8")
    # 两阶段（Codex round-3 BLOCKER 的修法）：第一次跑只把 A 的恢复结果原子
    # 发布下去并要求重跑；第二次跑 pending 已空，B 在干净基线上写入。
    r0 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md"))
    assert r0.returncode != 0, "存在 foreign pending 时不得在同一次运行里既恢复又追加"
    assert "A2 重放已应用" in r0.stdout, "事件 A 必须被重放"
    assert "恢复已落定" in r0.stderr, r0.stderr
    # ⚠️ 此处原断言是「必须如实告知**永久丢失**」—— 门锁住了那句错误声明。
    # 载荷其实都在 payload 里，现在逐项复放，提示也随之改成「已复放」。
    assert "已按各自的账本载荷复放" in r0.stdout, "被恢复事件的评分链副作用必须逐项复放"
    assert "question_id 与理解自评" in r0.stdout, "唯一补不回的两项要如实说明"
    assert _fm_fields(vault)["fsrs_last_review"] == TS1, "恢复结果必须已落盘（W = A 的时刻）"
    assert len(_ledger_lines(vault)) == 1, "第一阶段不得追加本次事件"
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-02T10:00:00Z", "W 反映 B"
    recs = _ledger_lines(vault)
    assert [x["event_id"] for x in recs] == ["quiz:板A#q1", "quiz:板B#q1"]
    assert _run_validator(vault).returncode == 0
    # A2 重放 A 后 W=TS1; 若跳过重放直接算 B, B 会从新卡基线出发 — 与正确
    # 基线 (A 已应用) 的 FSRS 六字段必然不同; 对拍 bridge 直调两次的结果:
    sys.path.insert(0, str(VAULT_SCRIPTS))
    try:
        import fsrs_bridge as fb

        base = fb.review({}, 0.75, False, TS1)  # A (rating 3)
        got = _fm_fields(vault)
        expect2 = fb.review({k: v for k, v in base.items() if k != "fm_block"}, 0.75, False, "2026-08-02T10:00:00Z")
        assert float(got["fsrs_stability"]) == expect2["fsrs_stability"], (
            f"A2 重放未生效或基线错: {got['fsrs_stability']} != {expect2['fsrs_stability']}"
        )
    finally:
        sys.path.remove(str(VAULT_SCRIPTS))
        sys.modules.pop("fsrs_bridge", None)


# ── 门⑯ 子串查重陷阱: payload 文本含 JSON 串形不得误判 duplicate ──
# Codex round-1 MEDIUM: 中文 EID + 转义 note 形态下旧子串谓词实测不命中
# (杀不掉旧实现) — 陷阱必须用 ASCII event_id 且 payload 字段值**直接等于**
# 该 event_id 文本, 让 `json.dumps(eid) in line` (旧实现) 确定命中。

TRAP_EID = "trap-eid-123"


def test_substring_dedup_trap(vault):
    """A4.5 parsed-field equality: 预置行的 payload 文本里恰好含
    `"quiz:<新eid>"` 的 JSON 串形时, 子串查重会误判 duplicate 而**零次落账**
    (旧实现的真实缺陷, schema §九登记)。正确行为 = 正常追加第 2 行。
    陷阱载体 = payload **键名** (键名引号不被 JSON 转义, 值内引号恒转义为
    \\" 导致 needle 尾引号匹配不上 — 首版陷阱因此被验伪断言自己抓出)。
    验伪: 该陷阱对旧子串谓词 `json.dumps(evid) in line` 必须命中。"""
    trap_needle = json.dumps("quiz:" + TRAP_EID, ensure_ascii=False)  # "quiz:trap-eid-123"
    other = {
        "event_id": "quiz:另一事件",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": {"quiz:" + TRAP_EID: "字段名恰好等于新事件 id 的 JSON 串形"},  # 不含 schema_ext
    }
    line_text = json.dumps(other, ensure_ascii=False)
    assert trap_needle in line_text, "陷阱行必须真的命中旧子串谓词 (否则本门为假门)"
    (vault / "learning_events.jsonl").write_text(line_text + "\n", encoding="utf-8")
    r = _run_writer(vault, _payload(event_id=TRAP_EID))
    assert r.returncode == 0, r.stdout + r.stderr
    recs = _ledger_lines(vault)
    assert len(recs) == 2, f"parsed 查重不得被子串误判, 实得 {len(recs)} 行: {[x['event_id'] for x in recs]}"
    assert recs[1]["event_id"] == "quiz:" + TRAP_EID


# ── 门⑰ A2 重放失败 → 一律 fail-closed 零写 (Codex round-1 BLOCKER) ──


def test_pending_replay_failure_blocks_everything(vault):
    """存在 pending 且重放失败 (fsrs 不可用) 时: 既不 degraded 落账、也不
    发布 frontmatter — A2 「追加前重放至空」无例外。"""
    event_a = {
        "event_id": "quiz:板A#q1",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": TS1,
        "effective_at": TS1,
        "payload": {
            "schema_ext": "review/1",
            "vault_id": "canvas_vault_测试",
            "concept_id": "测试节点",
            "rating": 3,
            "grade_norm": 0.75,
            "review_time": TS1,
            "fsrs_library_version": "degraded:historic-run",
            "fsrs_params_hash": "degraded:historic-run",
            "exam_board": "检验白板/板A.md",
            "attempt_count": 1,
        },
    }
    (vault / "learning_events.jsonl").write_text(json.dumps(event_a, ensure_ascii=False) + "\n", encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r = _run_writer(
        vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"), env_extra={"FSRS_BRIDGE_REEXEC": "1"}
    )
    assert r.returncode != 0, "pending 重放失败必须 fail-closed"
    assert "重放失败" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha, "零写节点"
    assert len(_ledger_lines(vault)) == 1, "零写账本 (不得 degraded 追加)"
    # 变体: pending 行 rating 非法 (float 1.5) → bridge 严格 int 拒 → 同 fail-closed
    bad_rating = json.loads(json.dumps(event_a))
    bad_rating["payload"]["rating"] = 1.5
    (vault / "learning_events.jsonl").write_text(json.dumps(bad_rating, ensure_ascii=False) + "\n", encoding="utf-8")
    r2 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r2.returncode != 0, "非法 rating 的 pending 行必须被 bridge 拒绝并 fail-closed"
    assert len(_ledger_lines(vault)) == 1
    # 变体 (round-2 HIGH): abandoned 行 rating=1.5 — abandoned 分支不得绕过类型门
    bad_ab = json.loads(json.dumps(event_a))
    bad_ab["event_type"] = "answer_abandoned"
    bad_ab["payload"]["rating"] = 1.5
    (vault / "learning_events.jsonl").write_text(json.dumps(bad_ab, ensure_ascii=False) + "\n", encoding="utf-8")
    r3 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r3.returncode != 0, "abandoned 行的非法 rating 同样必须被拒"
    # 变体 (round-2 HIGH 自洽): abandoned 行 rating=3 (类型合法但弃答恒 1)
    bad_ab2 = json.loads(json.dumps(bad_ab))
    bad_ab2["payload"]["rating"] = 3
    (vault / "learning_events.jsonl").write_text(json.dumps(bad_ab2, ensure_ascii=False) + "\n", encoding="utf-8")
    r4 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r4.returncode != 0, "abandoned=true 且 rating!=1 必须拒绝 (弃答一票否决)"
    assert len(_ledger_lines(vault)) == 1


# ── 门⑱ degraded 本地 A3 推进的 A7 上界 (Codex round-1 HIGH) ──


def test_degraded_a3_bump_respects_a7_bound(vault):
    """W=8999-12-31T23:59:59Z + fsrs 不可用 + 同秒评分: 本地 W+1s 会推出
    9000-01-01 (A7 排他上界) — 必须零写退出, 不制造非法孤儿事件。"""
    edge = NODE_V0.replace(
        "mastery_score: 0.5\n",
        "mastery_score: 0.5\nfsrs_due: 8999-12-31T23:59:59Z\nfsrs_state: 2\n"
        "fsrs_stability: 10.0\nfsrs_difficulty: 5.0\nfsrs_last_review: 8999-12-31T23:59:59Z\n",
    )
    (vault / NODE_REL).write_text(edge, encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload(ts="8999-12-31T23:59:59Z"), env_extra={"FSRS_BRIDGE_REEXEC": "1"})
    assert r.returncode != 0, "A7 上界越界必须 fail-closed"
    assert "A7" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha, "零写节点"
    assert not (vault / "learning_events.jsonl").exists(), "零写账本"


# ── 门⑲ F1 判定在 Obsidian 规范化形态下仍命中 (live 实证: 引号会被剥掉) ──


def test_f1_detection_survives_obsidian_renormalization(vault):
    """live 实证: Obsidian Properties 面板会把 calibration_log 的引号值规范化
    成裸词形态 — 旧守卫 `json.dumps(eid) in fm` 因此恒不命中 (假幂等)。
    解析层 F1 判定必须在裸词形态下同样命中。"""
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    # 模拟 Obsidian 规范化: 引号值 → 裸词
    text = (vault / NODE_REL).read_text(encoding="utf-8")
    # round-6 后校准存**完整**账本 event_id（带 `quiz:` 前缀）—— 正常路径与
    # foreign 路径此前写的键不是同一个东西，那是 round-6 的 BLOCKER。
    normalized = text.replace(
        'event_id: "quiz:测试检验-2026-08-01-1000#q1"', "event_id: quiz:测试检验-2026-08-01-1000#q1"
    )
    assert normalized != text, f"fixture 预置必须与规范化形态可区分: {text[:400]}"
    (vault / NODE_REL).write_text(normalized, encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r2 = _run_writer(vault, _payload(ts="2026-09-01T07:00:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "幂等跳过" in r2.stdout, "裸词形态的 calibration_log 必须仍被解析层 F1 命中"
    assert _sha(vault / NODE_REL) == sha, "规范化形态重跑必须零写"
    assert len(_ledger_lines(vault)) == 1


# ── 门⑳ append_event 的 LF 守卫 (Codex round-1 HIGH: 坏尾行连坐新行) ──


def test_append_event_lf_guard_isolates_torn_tail(monkeypatch, tmp_path):
    """backend append_event 在 partial-JSON 无 LF 尾行后追加: 新行必须独立
    可解析、函数返回 True (新行确实落盘) — 不得把两个 JSON 粘成一行。"""
    from app.services import learning_event_log as ev

    ledger = tmp_path / "learning_events.jsonl"
    monkeypatch.setattr(ev, "_log_path", lambda: ledger)
    ledger.write_text('{"event_id": "quiz:被截断", "event_vers', encoding="utf-8")  # partial, 无 LF
    assert ev.append_event("answer_scored", event_id="quiz:fresh-1")
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2, f"新行必须独立成行, 实得 {len(lines)} 行"
    assert json.loads(lines[1])["event_id"] == "quiz:fresh-1"
    assert ev.append_event("answer_scored", event_id="quiz:fresh-1") is False  # 幂等不因守卫破坏
    # 变体 (round-2 HIGH): 零字节空文件首写 — seek(-1) 守卫必须跳过, 不能炸
    empty = tmp_path / "empty" / "learning_events.jsonl"
    empty.parent.mkdir(parents=True)
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(ev, "_log_path", lambda: empty)
    assert ev.append_event("answer_scored", event_id="quiz:first-in-empty"), "空文件首写必须成功"
    assert json.loads(empty.read_text(encoding="utf-8").strip())["event_id"] == "quiz:first-in-empty"


# ── 门㉑ degraded 遗留重试 (round-2 B-1②): F1=T 但 W 未推进 → 恢复只补 FSRS ──


def test_degraded_legacy_retry_restores_fsrs_without_double_ema(vault):
    """首评 fsrs 不可用 → 事件落账(哨兵)+EMA/校准已应用+W 未推进。fsrs 恢复后
    同 ID 重试必须: 补齐 FSRS、**不再吃一次 EMA**、账本仍 1 行。"""
    r1 = _run_writer(vault, _payload(), env_extra={"FSRS_BRIDGE_REEXEC": "1"})
    assert r1.returncode == 0, r1.stdout + r1.stderr
    ema_after_degraded = _fm(vault)
    assert not _fm_fields(vault), "degraded 后 W 必须未推进"
    # fsrs 恢复 (不加 REEXEC env) → 同 ID 重试
    r2 = _run_writer(vault, _payload(ts="2026-09-01T06:00:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "degraded 遗留" in r2.stdout, r2.stdout + r2.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-01T10:00:00Z", "FSRS 必须补齐推进"
    fm_now = _fm(vault)
    for key in ("mastery_score", "mastery_a", "mastery_b"):
        assert re.search(rf"^{key}:.*", fm_now, re.M).group(0) == re.search(
            rf"^{key}:.*", ema_after_degraded, re.M
        ).group(0), f"{key} 不得二次吸收成绩 (EMA 双吃)"
    assert len(_ledger_lines(vault)) == 1, "恢复不得二次 append"
    assert _run_validator(vault).returncode == 0


# ── 门㉒ 已完整应用 + 冲突事实 → 拒 (round-2 B-1①: F1 不得吞冲突) ──


def test_conflicting_facts_after_full_apply_rejected(vault):
    r1 = _run_writer(vault, _payload())
    assert r1.returncode == 0
    sha = _sha(vault / NODE_REL)
    # 完整应用态 (不回滚 frontmatter) 直接换事实重跑 → envelope 冲突拒绝
    r2 = _run_writer(vault, _payload(abandoned=True))
    assert r2.returncode != 0, "已应用态的冲突事实必须拒绝 (F1 不得吞)"
    assert "envelope 冲突" in r2.stderr
    assert _sha(vault / NODE_REL) == sha and len(_ledger_lines(vault)) == 1


# ── 门㉓ 账本 event_id 重复 → fail-closed (round-2 B-3: 双 pending 行会二次 apply) ──


def test_duplicate_event_id_in_ledger_fail_closed(vault):
    ev_row = json.dumps(
        {
            "event_id": "quiz:重复行",
            "event_version": 1,
            "event_type": "answer_scored",
            "node_id": "测试节点",
            "recorded_at": TS1,
            "effective_at": TS1,
            "payload": {
                "schema_ext": "review/1",
                "vault_id": "canvas_vault_测试",
                "concept_id": "测试节点",
                "rating": 3,
                "grade_norm": 0.75,
                "review_time": TS1,
                "fsrs_library_version": "degraded:x",
                "fsrs_params_hash": "degraded:x",
                "exam_board": "x",
                "attempt_count": 1,
            },
        },
        ensure_ascii=False,
    )
    (vault / "learning_events.jsonl").write_text(ev_row + "\n" + ev_row + "\n", encoding="utf-8")
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r.returncode != 0, "全文件 event_id 重复必须 fail-closed (A2 会双 apply)"
    assert "event_id 重复" in r.stderr, r.stderr
    assert not _fm_fields(vault), "零写节点"


# ── 门㉔ 含转义引号的 event_id 幂等 (round-2 HIGH: F1 读取须同源反解) ──


def test_f1_detection_handles_escaped_quotes(vault):
    eid_quoted = '板"引号#q1'
    r = _run_writer(vault, _payload(event_id=eid_quoted))
    assert r.returncode == 0, r.stdout + r.stderr
    # 写侧 json.dumps 落盘为转义形态: event_id: "板\"引号#q1"
    text = (vault / NODE_REL).read_text(encoding="utf-8")
    assert '\\"' in text, "fixture 预置应含转义引号形态"
    sha = _sha(vault / NODE_REL)
    r2 = _run_writer(vault, _payload(event_id=eid_quoted, ts="2026-09-01T05:00:00Z"))
    assert r2.returncode == 0 and "幂等跳过" in r2.stdout, "转义引号 eid 必须经同源反解命中 F1"
    assert _sha(vault / NODE_REL) == sha, "不得重复副作用 (attempt/calibration)"


# ── 门㉕ fsrs 身份键篡改 → envelope 放行 + validator 拦 (分层防线声明) ──


def test_identity_tampering_caught_by_validator_not_envelope(vault):
    """fsrs_library_version/params_hash 是环境快照, 排除在 envelope 等价面外
    (验收单声明); 其完整性由校验器 golden 绑定门承担 — 本门锁这个分层。"""
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    base = _ledger_lines(vault)[0]
    # 回滚 frontmatter → 崩溃窗口① + 身份键被篡改的 durable 行
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    tampered = json.loads(json.dumps(base))
    tampered["payload"]["fsrs_library_version"] = "tampered-library"
    (vault / "learning_events.jsonl").write_text(json.dumps(tampered, ensure_ascii=False) + "\n", encoding="utf-8")
    r2 = _run_writer(vault, _payload())
    # ⚠️ 分层的准确表述（round-4 后收紧）：`fsrs_library_version` / `fsrs_params_hash`
    # 仍**不在 envelope 等价面**里（等价面只管评分事实，库升级不该让历史重放变冲突）；
    # 但消费前会复用校验器本体的 `validate_record_full` 做完整 v1 记录校验，
    # 而它绑定 golden manifest —— 所以被篡改的身份**在写点侧就被拦下**，不再等到
    # 事后跑校验器。两句话都成立，别把「不在等价面」读成「写点不管它」。
    assert r2.returncode != 0, "被篡改的身份键必须在消费前就被拦下"
    assert "未通过校验器的 v1 记录校验" in r2.stderr, r2.stderr
    assert _run_validator(vault).returncode == 1, "校验器同样拦下（两侧同口径）"


# ══ CARD-G3-2b: Codex round-3 残留 R1-R7 的生产入口反例门 (㉖-㉜) ══
# 全部用**逐字提取的生产 PYEOF 块**驱动 (CODE), 反例态由账本/节点预置构造 —
# 测试内不重写任何一套判定逻辑。


# ── 门㉖ R1 (BLOCKER): durable payload 的未知额外键必须冲突, 不得被自抄放行 ──


def test_r1_unknown_durable_payload_key_conflicts(vault):
    """旧实现的 candidate 以 durable payload 为底 spread (`{**_dpl, ...}`),
    未知额外键被原样抄进 candidate ⇒ 比较退化成「自己比自己」。
    实测穿透链: 给崩溃窗口①的 durable 行加 payload.out_of_order=true →
    envelope 放行, 而 A2 适用集按定义排除该行 ⇒ FSRS 永不应用, writer 仍
    rc=0 写下 calibration/mastery, 节点 fsrs_* 全空、账本仍一行。
    正确行为: 键集本身是等价面的一部分 — 多一键/少一键一律冲突。"""
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    base = _ledger_lines(vault)[0]
    # ⚠️ round-1 后续: `out_of_order` 现被更早的语义门接管 (见门㉞ N1) —— 只有
    # **合法乱序形态**(review_time ≤ W) 的该键才会走到 envelope 门。这里保 W
    # 不回滚地测它, 保证 R1 的原始穿透链仍被本门覆盖: 本次评分事实里没有这个
    # 键, 键集不等即冲突。
    base_oo = json.loads(json.dumps(base))
    base_oo["payload"]["out_of_order"] = True  # review_time == W ⇒ 合法乱序
    _write_ledger(vault, base_oo)
    r_oo = _run_writer(vault, _payload(ts="2026-09-01T07:00:00Z"))
    assert r_oo.returncode != 0, "合法乱序形态的 out_of_order 键仍须 envelope 冲突"
    assert "envelope 冲突" in r_oo.stderr, r_oo.stderr
    assert len(_ledger_lines(vault)) == 1
    for tweak, desc in (
        ({"note": "外部工具注入的备注"}, "任意未知额外键"),
        ({"vault_id": "canvas_vault_测试", "extra_nested": {"a": 1}}, "未知嵌套键"),
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 回到崩溃窗口①前置态
        _sha_v0 = _sha(vault / NODE_REL)
        tampered = json.loads(json.dumps(base))
        tampered["payload"].update(tweak)
        _write_ledger(vault, tampered)
        rt = _run_writer(vault, _payload())
        assert rt.returncode != 0, f"{desc}: 必须 envelope 冲突 (旧实现 rc=0 且 fsrs_* 全空)"
        assert "envelope 冲突" in rt.stderr, rt.stderr
        assert _sha(vault / NODE_REL) == _sha_v0, f"{desc}: 冲突拒绝必须整节点零写"
        assert len(_ledger_lines(vault)) == 1, f"{desc}: 冲突拒绝不得追加"
    # 反向: durable 行**缺**一个固定生产键 — 旧实现会被 candidate 的覆盖补回,
    # 同样穿透。少键必须与多键同等冲突。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    short = json.loads(json.dumps(base))
    short["payload"].pop("exam_board")
    _write_ledger(vault, short)
    rs = _run_writer(vault, _payload())
    assert rs.returncode != 0 and "envelope 冲突" in rs.stderr, rs.stderr
    # 对照 (验伪): 原样 durable 行必须照常恢复 — 本门不是「恒拒」的假门
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    _write_ledger(vault, base)
    rok = _run_writer(vault, _payload())
    assert rok.returncode == 0, rok.stdout + rok.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == TS1, "未被篡改的 durable 行必须正常恢复"


# ── 门㉗ R2 (BLOCKER): 小数秒 / 非 UTC durable review_time 不得被消费 ──


def test_r2_non_whole_second_durable_review_time_fail_closed(vault):
    """bridge 入口 _whole_second 会把 10:00:00.500Z 截成 10:00:00Z 写进 W,
    而账本那行仍是 .500Z ⇒ 「.500 > .000」恒真, 同一行**每次重跑都判 pending
    并再推进一次 FSRS** (实测: 账本始终一行, W 逐次 +1s = §6.2 A5 禁止的二次
    apply)。修复方向必须是 apply 前只验不改 — 消费时归一化会把损坏行洗成
    合法行, 把缺陷从写入面挪进不可见面。"""
    # 判据必须落在**字面**上, 不是解析后的值 (自查补): '.000000Z' 的
    # microsecond 恰为 0, 只看值会放行它, 而校验器的 _WHOLE_SECOND_RE 按字面
    # 判 FAIL ⇒ 写点放行、validator 拒, 实现与契约又成两个口径。
    # ⚠️ 按**拦截层**分组, 而不是笼统断言「随便哪层拒都行」——后者会让
    # 「整秒门被删、靠校验器语法门兜住」这种回归无声通过 (round-4 后消费前
    # 复用 validate_record_full, 语法畸形会先被它拦, 理由串与整秒门不同)。
    for rt_bad, why in (
        # 第一组: §三 受理语法合法, 被**写点自己的整秒/UTC 门**拦
        ("2026-08-01T10:00:00.500Z", "小数秒"),
        ("2026-08-01T10:00:00.000000Z", "小数秒"),  # 零值小数秒字面: 值合规、字面不合规
        ("2026-08-01T10:00:00.0Z", "小数秒"),
        ("2026-08-01T18:00:00+08:00", "非 UTC"),  # 字面合规但偏移非零
        # 第二组: 连 §三 受理语法都不合法, 被**校验器本体**先拦 (两侧同口径)
        ("2026-08-01T10:00:00+00:00:00", "未通过校验器的 v1 记录校验"),  # 非 canonical 偏移
        ("2026-08-01T10:00+00:00", "未通过校验器的 v1 记录校验"),  # 省略秒段 (§6.2 round-4 HIGH#1)
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        _write_ledger(vault, _review_row(**{"payload.review_time": rt_bad, "effective_at": rt_bad}))
        sha = _sha(vault / NODE_REL)
        # ①该行即本次事件 (dup 路径)
        r = _run_writer(vault, _payload(event_id="板A#q1"))
        assert r.returncode != 0, f"{why} durable 行 (dup 路径) 必须 fail-closed"
        assert why in r.stderr, r.stderr
        assert _sha(vault / NODE_REL) == sha and len(_ledger_lines(vault)) == 1, "零写"
        # ②该行是别的事件 (foreign pending 路径) — 同样在重放前拒
        r2 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r2.returncode != 0, f"{why} durable 行 (foreign pending 路径) 必须 fail-closed"
        assert why in r2.stderr, r2.stderr
        assert _sha(vault / NODE_REL) == sha and len(_ledger_lines(vault)) == 1, "零写"
    # 对照 (验伪): 整秒 UTC 的两种 canonical 字面都必须照常重放 —— 本门不是
    # 「凡带偏移就拒」的假门, Z 与 +00:00 是同一瞬间的两种合法写法。
    for rt_ok in ("2026-08-01T10:00:00Z", "2026-08-01T10:00:00+00:00"):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        _write_ledger(vault, _review_row(**{"payload.review_time": rt_ok, "effective_at": rt_ok}))
        rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rok.returncode == 0, f"{rt_ok} 必须照常重放: " + rok.stdout + rok.stderr
        assert "A2 重放已应用" in rok.stdout


# ── 门㉘ R3 (HIGH): 历史事件重跑 (E1→E2→重跑 E1) 必须 no-op, 不得误报冲突 ──


def test_r3_historical_event_replay_is_noop_not_conflict(vault):
    """§6.2:187 要求同 canonical envelope 必须 no-op。旧实现的 attempt 复算
    在已应用态直接取 frontmatter 当前值 (tip), 于是重跑 E1 时把 E2 的计数当
    成 E1 的 ⇒ 合法历史重放被误报 envelope 冲突 (用户翻旧检验白板重跑旧评分
    即触发)。正确口径: 沿账本回推 ordinal。"""
    r1 = _run_writer(vault, _payload())  # E1 @ 10:00
    assert r1.returncode == 0, r1.stdout + r1.stderr
    r2 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    recs = _ledger_lines(vault)
    assert [x["payload"]["attempt_count"] for x in recs] == [1, 2], "durable attempts 应为 [1,2]"
    assert re.search(r"^attempt_count:\s*(\d+)", _fm(vault), re.M).group(1) == "2"
    sha = _sha(vault / NODE_REL)
    # 原样重跑 E1 (仅 recorded_at 变化 — envelope 显式排除)
    r3 = _run_writer(vault, _payload(ts="2026-09-01T12:00:00Z"))
    assert r3.returncode == 0, "历史事件原样重跑必须 no-op, 不得报冲突: " + r3.stdout + r3.stderr
    assert "幂等跳过" in r3.stdout, r3.stdout
    assert _sha(vault / NODE_REL) == sha, "no-op 不得改动节点"
    assert len(_ledger_lines(vault)) == 2, "no-op 不得追加"
    # 验伪: 同一历史事件**换事实**重跑仍必须冲突 (本门不是「恒放行」的假门)
    r4 = _run_writer(vault, _payload(ts="2026-09-01T12:00:00Z", abandoned=True))
    assert r4.returncode != 0 and "envelope 冲突" in r4.stderr, r4.stderr


# ── 门㉙ R4 (HIGH): 含 idle 状态且触发 A3 时, 正常与恢复产物逐字节相同 ──


def test_r4_recovery_byte_identical_with_idle_and_a3_bump(vault):
    """卡文 (d)。旧实现正常路径的 mastery 闲置折旧基准用 payload ts, 恢复路径
    用 durable review_time — 门②的新卡无 last_examined, days_idle 恒 0, 测不
    出差异。本门的节点 W=2026-12-01 远晚于评分时刻 2026-08-01 ⇒ A3 把
    review_time 推到 W+1s, 两个基准相差约 4 个月, mastery_a/b 与整节点 SHA
    必然分叉 (round-3 实测两次 SHA 不同)。"""
    (vault / NODE_REL).write_text(NODE_IDLE_A3, encoding="utf-8")
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    golden = (vault / NODE_REL).read_bytes()
    rec = _ledger_lines(vault)[0]
    assert rec["payload"]["review_time"] == "2026-12-01T10:00:01Z", (
        "fixture 前提: A3 必须把 review_time 推到 W+1s, 实为 " + rec["payload"]["review_time"]
    )
    assert rec["payload"]["review_time"] != TS1, "fixture 前提: review_time 必须 != payload ts"
    # 崩溃窗口①: 回滚 frontmatter 到评分前 (账本保留该事件) → 恢复路径
    (vault / NODE_REL).write_text(NODE_IDLE_A3, encoding="utf-8")
    r2 = _run_writer(vault, _payload(ts="2026-09-15T09:30:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert len(_ledger_lines(vault)) == 1, "恢复路径不得二次 append"
    assert (vault / NODE_REL).read_bytes() == golden, "含 idle 状态 + A3 bump 时, 恢复产物必须与直接应用逐字节相同"


# ── 门㉚ R5 (HIGH): scored rating 与 grade_norm 不自洽 → apply 前拒绝 ──


def test_r5_inconsistent_scored_rating_rejected_before_apply(vault):
    """answer_scored + grade_norm=0.75 + rating=4: 类型 int、范围 1-4 都合法,
    但 [Decision-FSRS-1] 下 0.75 的契约值是 3。旧实现照单全收 — writer rc=0、
    输出「A2 重放已应用」并追加下一事件, 事后才由 validator 判 rc=1 (损坏基线
    上已叠加一次真实调度)。必须在 apply 前拒绝。"""
    sha = _sha(vault / NODE_REL)
    for bad_rating in (4, 2, 1):
        _write_ledger(vault, _review_row(**{"payload.rating": bad_rating}))
        r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r.returncode != 0, f"rating={bad_rating} 与 grade_norm=0.75 不自洽, 必须 apply 前拒绝"
        assert "不自洽" in r.stderr, r.stderr
        assert _sha(vault / NODE_REL) == sha, "零写节点"
        assert len(_ledger_lines(vault)) == 1, "零写账本 (不得追加下一事件)"
    # 验伪: 契约值 3 必须照常重放 (本门不是「恒拒」的假门)
    _write_ledger(vault, _review_row())
    rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert rok.returncode == 0, rok.stdout + rok.stderr
    assert len(_ledger_lines(vault)) == 2


# ── 门㉛ R7 (MEDIUM): 带终止 LF 的坏末行 = 完整损坏, 不是截断 ──


def test_r7_corrupt_tail_line_with_lf_is_not_truncation(vault):
    """旧实现只看「最后一行解析失败」, 于是**带终止 LF** 的损坏末行也被当
    截断容忍 — 实测 writer 仍 rc=0、自称「截断尾行」、继续追加并推进节点。
    EOF 的 LF 状态是区分「被腰斩的半行」与「完整写入后损坏」的唯一机械证据。"""
    good = _review_row(event_id="quiz:旧板", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"  # 不进本节点适用集, 隔离本门的判定面
    bad = '{"event_id": "quiz:损坏行", "event_version": 1, "event_type": "answer_sc'
    ledger = vault / "learning_events.jsonl"
    # ①带终止 LF 的坏末行 → fail-closed 零写
    ledger.write_text(json.dumps(good, ensure_ascii=False) + "\n" + bad + "\n", encoding="utf-8")
    sha = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload())
    assert r.returncode != 0, "带终止 LF 的坏末行必须 fail-closed (旧实现 rc=0 当截断容忍)"
    assert "完整写入的损坏行" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha, "零写节点"
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 2, "零写账本"
    # ②同一坏行去掉终止 LF → 仍按截断自愈容忍 (对照, 防本门变成「坏行恒拒」)
    ledger.write_text(json.dumps(good, ensure_ascii=False) + "\n" + bad, encoding="utf-8")
    r2 = _run_writer(vault, _payload())
    assert r2.returncode == 0, "无 LF 的坏末行仍应按截断隔离: " + r2.stdout + r2.stderr
    assert "截断尾行" in r2.stdout
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 3 and json.loads(lines[2])["event_id"] == "quiz:" + EID


# ── 门㉜ R6 (MEDIUM): 身份键归属与 candidate 构造裁决必须回写冻结 schema ──


def test_r6_schema_declares_identity_key_integrity_owner():
    """round-3 MEDIUM: 门㉕锁定的「两个身份键排除出 envelope 等价面」此前只
    活在实现与测试里, 契约 §6.2 原文仍只排除 recorded_at — 实现与契约两个
    口径。本门锁定回写: 归属方 (validator golden manifest 绑定门) 与 candidate
    独立构造的禁令都必须在冻结契约里可查。"""
    doc = (WT / "docs" / "learning-events-schema-v1.md").read_text(encoding="utf-8")
    seg = doc[doc.index("duplicate 命中后的状态推进门") : doc.index("**A5 整秒精度")]
    for needle in (
        "fsrs_library_version",
        "fsrs_params_hash",
        "排除出 envelope 等价面",
        "golden manifest 绑定门",
        "candidate 必须独立字面构造",
        "多一键、少一键或值不同",
    ):
        assert needle in seg, f"§6.2 duplicate 门段落缺「{needle}」— 契约未同步实现裁决"
    # A5 段必须写明 A2 消费侧的机械强制 (R2 的契约面)
    a5 = doc[doc.index("**A5 整秒精度") : doc.index("**三态语义")]
    assert "A2 消费侧同样机械强制" in a5 and "禁止消费时顺手归一化" in a5, a5[:400]
    # A4.5 短写段必须写明「截断 vs 完整损坏」的 LF 判据 (R7 的契约面)
    assert "可容忍的截断 vs 完整损坏" in doc and "不以 LF 结尾" in doc
    # round-4 HIGH 的契约面: A8 必须写明「先过校验器本体、再叠加更严的」,
    # 否则「比校验器严」那句会被读成「消费侧可以另起一套判据」——本卡正是
    # 这么读的, 于是手写的第二套判据在 4 个形态上比校验器**松**。
    a8 = doc[doc.index("**A8 消费侧准入") : doc.index("**A9 恢复先落定")]
    for needle in (
        "validate_record_full",
        "先过校验器本体",
        "顶层必须是 JSON object",
        "归属判断必须排在",
        "不得越权阻塞",
    ):
        assert needle in a8, f"§6.2 A8 段缺「{needle}」— round-4 裁决未回写契约"
    # 三态语义段必须写明 out_of_order 的**写点侧** fail-closed 口径 (N1 的契约面)
    # —— proof 侧是「报违规仍计入」, 在线写路径不能照搬, 两个口径必须分开写清楚。
    oo = doc[doc.index("**`out_of_order` 字段冻结") : doc.index("**迟到事件的入账通道**")]
    for needle in ("写点（在线 A2）侧同款语义门", "fail-closed", "被伪装成乱序的真实后继", "唯一合法值布尔 `true`"):
        assert needle in oo, f"§6.2 三态语义段缺「{needle}」— 写点侧口径未回写契约"


# ── 门㉝ write-ahead 六格状态机逐格闭合 (卡文标题判据) ──
# 分诊的自由度是 (dup 有无) × (f1) × (fsrs_applied); fsrs_applied 只在 dup=有
# 时有定义 ⇒ 2 + 4 = 6 格 (Codex round-3 §六格状态机)。round-3 判定 3 格 FAIL
# (历史 attempt 误拒 / 小数秒重复推进 / 额外键跳过 A2 且字节不等) + 1 格
# PARTIAL (foreign pending 输入门不完整)。本门逐格构造并断言终态。


def _strip_calibration(vault: Path) -> None:
    """删掉 frontmatter 的 calibration_log 块 (制造 f1=False 而其余副作用已在)。"""
    text = (vault / NODE_REL).read_text(encoding="utf-8")
    head, fm, body = text.split("---\n", 2)
    lines, out, skipping = fm.split("\n"), [], False
    for ln in lines:
        if ln.startswith("calibration_log:"):
            skipping = True
            continue
        if skipping and (ln.startswith("  ") or ln == ""):
            continue
        skipping = False
        out.append(ln)
    # calibration_log 通常是 frontmatter 最后一个键, 其块尾的空串元素会被上面的
    # skipping 分支吃掉 ⇒ 直接 join 会丢掉收尾换行、把 `---` 粘到末行上。
    new_fm = "\n".join(out).rstrip("\n") + "\n"
    (vault / NODE_REL).write_text(head + "---\n" + new_fm + "---\n" + body, encoding="utf-8")


def test_six_cell_state_machine_closed(vault):
    # ── 格1 dup=None, f1=F: 正常新写 (A2 先把 foreign pending 重放至空)
    foreign = _review_row(event_id="quiz:板A#q1")
    _write_ledger(vault, foreign)
    r1 = _run_writer_settled(vault, _payload(ts="2026-08-02T10:00:00Z"))
    assert r1.returncode == 0, r1.stdout + r1.stderr
    assert "A2 重放已应用" in r1.stdout, "格1: foreign pending 必须在新写前重放"
    assert "恢复已落定" in r1.stderr, "格1: 恢复必须先独立落盘再要求重跑（两阶段）"
    assert len(_ledger_lines(vault)) == 2 and _fm_fields(vault)["fsrs_last_review"] == "2026-08-02T10:00:00Z"

    # ── 格2 dup=None, f1=T: 旧写序孤儿 (frontmatter 已应用而账本无该事件) → 整体 no-op
    _write_ledger(vault, foreign)  # 抹掉本次事件行, calibration 仍在 frontmatter
    sha_before = _sha(vault / NODE_REL)
    r2 = _run_writer(vault, _payload(ts="2026-09-01T08:00:00Z"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "旧写序" in r2.stdout and "不补录" in r2.stdout, r2.stdout
    assert _sha(vault / NODE_REL) == sha_before and len(_ledger_lines(vault)) == 1, "格2: 必须零改动"

    # ── 格3 dup=有, f1=T, applied=T: 完整成功后重放 → envelope 通过 + no-op
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    sha_full = _sha(vault / NODE_REL)
    r3 = _run_writer(vault, _payload(ts="2026-09-01T08:30:00Z"))
    assert r3.returncode == 0 and "幂等跳过" in r3.stdout, r3.stdout + r3.stderr
    assert _sha(vault / NODE_REL) == sha_full and len(_ledger_lines(vault)) == 1

    # ── 格4 dup=有, f1=F, applied=T: FSRS 已被吸收但校准缺失 → 停下人工裁定
    _strip_calibration(vault)
    sha_stripped = _sha(vault / NODE_REL)
    r4 = _run_writer(vault, _payload(ts="2026-09-01T09:00:00Z"))
    assert r4.returncode != 0, "格4: 顺序错乱无机械判据, 必须 fail-closed"
    assert "缺校准记录" in r4.stderr and "人工核对" in r4.stderr, r4.stderr
    assert _sha(vault / NODE_REL) == sha_stripped and len(_ledger_lines(vault)) == 1, "格4: 零写"

    # ── 格5 dup=有, f1=T, applied=F: degraded 遗留 → 只补 FSRS, 不再吃 EMA
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload(), env_extra={"FSRS_BRIDGE_REEXEC": "1"}).returncode == 0
    assert not _fm_fields(vault), "格5 前置: degraded 后 W 未推进"
    ema_before = {
        k: re.search(rf"^{k}:.*", _fm(vault), re.M).group(0)
        for k in ("mastery_score", "mastery_a", "mastery_b", "attempt_count")
    }
    r5 = _run_writer(vault, _payload(ts="2026-09-01T09:30:00Z"))
    assert r5.returncode == 0 and "degraded 遗留" in r5.stdout, r5.stdout + r5.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == TS1, "格5: FSRS 必须补齐"
    for k, v in ema_before.items():
        assert re.search(rf"^{k}:.*", _fm(vault), re.M).group(0) == v, f"格5: {k} 不得二次吸收"
    assert len(_ledger_lines(vault)) == 1

    # ── 格6 dup=有, f1=F, applied=F: 崩溃窗口① → 全套补齐且与直接应用字节相同
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    golden = (vault / NODE_REL).read_bytes()
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    r6 = _run_writer(vault, _payload(ts="2026-09-01T10:00:00Z"))
    assert r6.returncode == 0 and "崩溃窗口" in r6.stdout, r6.stdout + r6.stderr
    assert (vault / NODE_REL).read_bytes() == golden, "格6: 恢复产物必须与直接应用逐字节相同"
    assert len(_ledger_lines(vault)) == 1
    assert _run_validator(vault).returncode == 0, "六格走完后账本仍须过校验器"


# ── 门㉞ round-1 后续 N1-N5：审查线索指向的五个残留面 ──
# Codex round-1 正文被内容过滤器拦下（stderr 保留完整推理标题序列），按其
# 标题线索逐条实测，5 条中 4 条复现为真缺陷 + 1 条诊断不精确。本门锁全部五条。


def test_round1_followups_n1_to_n5(vault):
    # ── N1 (BLOCKER) 被伪装成乱序的真实后继：标 out_of_order 但 review_time > W
    # 旧实现无条件排除标记行 ⇒ 该事件的 FSRS 永久丢失且 writer 照常 rc=0
    # （实测 rc=0、W 只反映本次事件、账本 2 行）。§6.2 三态语义 round-17 已冻结
    # 「标记行 review_time 必须不晚于此前适用事件的最大时刻」，本卡补进写点侧。
    late = _review_row(**{"payload.out_of_order": True, "payload.review_time": "2026-08-05T10:00:00Z"})
    late["effective_at"] = "2026-08-05T10:00:00Z"
    _write_ledger(vault, late)
    sha0 = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r.returncode != 0, "标 out_of_order 但晚于水位线的行必须 fail-closed（否则静默丢一次评分）"
    assert "伪装成乱序的真实后继" in r.stderr, r.stderr
    assert _sha(vault / NODE_REL) == sha0 and len(_ledger_lines(vault)) == 1, "零写"
    # N1 形态门：唯一合法值是布尔 true（§6.2 冻结），false/"true" 等形态歧义
    for bad_shape in (False, "true", 1, {"v": True}):
        _write_ledger(vault, _review_row(**{"payload.out_of_order": bad_shape}))
        rb = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rb.returncode != 0, f"out_of_order={bad_shape!r} 形态非法必须拒"
        # round-5 后完整校验前移到乱序分流之前 ⇒ 坏形态先被**校验器本体**拦
        # （两侧同口径），写点自己的形态门成了其后的第二道。两种拒因都算达标，
        # 但必须点名是这两者之一 —— 不能退化成「随便什么理由拒了都行」。
        assert ("形态非法" in rb.stderr) or ("out_of_order 唯一合法值" in rb.stderr), rb.stderr
    # N1 验伪：合法乱序（review_time ≤ W）必须放行且不进 pending
    (vault / "learning_events.jsonl").unlink()  # 清掉上面留下的坏形态行
    assert _run_writer(vault, _payload()).returncode == 0  # 先把 W 推到 TS1
    w_before = _fm_fields(vault)["fsrs_last_review"]
    early = _review_row(**{"payload.out_of_order": True, "payload.review_time": "2026-07-01T10:00:00Z"})
    early["effective_at"] = "2026-07-01T10:00:00Z"
    early["event_id"] = "quiz:补录旧事件"
    _write_ledger(vault, _ledger_lines(vault)[0], early)
    ro = _run_writer(vault, _payload(event_id="板C#q1", ts="2026-08-03T10:00:00Z"))
    assert ro.returncode == 0, "合法乱序行必须放行: " + ro.stdout + ro.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-03T10:00:00Z", "乱序行不得推进 W 到 07-01"
    assert w_before == TS1

    # ── N2 (HIGH) EOF 的 LF 判据必须落在**字节**上
    # 文本模式的 universal newlines 把裸 \r 读成 \n ⇒ 以裸 \r 结尾的截断文件
    # 被误判成「完整写入的损坏行」而 fail-closed（实测 rc=1）。
    v2 = vault
    (v2 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    good = _review_row(event_id="quiz:旧板", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"
    torn = '{"event_id": "quiz:损坏行", "event_ty'
    (v2 / "learning_events.jsonl").write_bytes(
        (json.dumps(good, ensure_ascii=False) + "\n").encode("utf-8") + torn.encode("utf-8") + b"\r"
    )
    r2 = _run_writer(v2, _payload())
    assert r2.returncode == 0, "裸 \\r 结尾在字节上无 LF ⇒ 应按截断隔离: " + r2.stdout + r2.stderr
    assert "截断尾行" in r2.stdout, r2.stdout
    # 对照：同一坏行改成真正带 LF 结尾 → 仍须 fail-closed（判据没被放松）
    (v2 / "learning_events.jsonl").write_bytes(
        (json.dumps(good, ensure_ascii=False) + "\n").encode("utf-8") + torn.encode("utf-8") + b"\r\n"
    )
    r2b = _run_writer(v2, _payload(event_id="板D#q1", ts="2026-08-04T10:00:00Z"))
    assert r2b.returncode != 0 and "完整写入的损坏行" in r2b.stderr, r2b.stderr

    # ── N3 (MEDIUM) 账本行 JSON 重复键：loads 静默取最后一个，歧义不可证
    (v2 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    row = _review_row(event_id="quiz:" + EID)
    text = json.dumps(row, ensure_ascii=False)
    dup_text = text.replace('"grade_norm": 0.75', '"grade_norm": 0.11, "grade_norm": 0.75', 1)
    assert dup_text.count('"grade_norm"') == 2, "fixture 前提：必须真有两个同名键"
    (v2 / "learning_events.jsonl").write_text(dup_text + "\n", encoding="utf-8")
    _face_n3 = _write_face(v2)
    r3 = _run_writer(v2, _payload())
    assert r3.returncode != 0, "含重复键的账本行必须 fail-closed"
    assert "重复键" in r3.stderr, r3.stderr
    assert _write_face(v2) == _face_n3, "零写（节点 + 账本）"

    # ── N4 (MEDIUM) 非法 UTF-8 字节：必须 clean fail-closed，不是 traceback
    (v2 / "learning_events.jsonl").write_bytes(b'{"event_id": "quiz:x"}\n\xff\xfe bad\n')
    r4 = _run_writer(v2, _payload())
    assert r4.returncode != 0
    assert "非 UTF-8 字节" in r4.stderr, r4.stderr
    assert "Traceback" not in r4.stderr, "必须是 clean fail-closed，不得抛 traceback"

    # ── N5 (MEDIUM) 多 pending 并存 → attempt 序数不可从账本边界确证
    # A2 保证单写者下至多一个 pending，故此态只可能来自外部写入。旧实现会硬算
    # 一个期望值，碰巧相等就放行 = 在不可证的基线上继续。
    (v2 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    e1 = _review_row(event_id="quiz:板A#q1", **{"payload.review_time": "2026-08-03T10:00:00Z"})
    e1["effective_at"] = "2026-08-03T10:00:00Z"
    e2 = _review_row(
        event_id="quiz:" + EID,
        **{
            "payload.review_time": "2026-08-04T10:00:00Z",
            "payload.attempt_count": 2,
            "payload.exam_board": "检验白板/测试检验-2026-08-01-1000.md",
        },
    )
    e2["effective_at"] = "2026-08-04T10:00:00Z"
    _write_ledger(v2, e1, e2)
    _face_n5 = _write_face(v2)
    r5 = _run_writer(v2, _payload())
    assert r5.returncode != 0, "多 pending 并存时必须 fail-closed，不得硬算 attempt 期望值"
    assert "A2「追加前重放至空」不变量已被破坏" in r5.stderr, r5.stderr
    assert _write_face(v2) == _face_n5, "零写（节点 + 账本）"


# ── 门㉟ 自测覆盖缺口（round-2 等待期自查，6 条全部实测过）──
# 这些不是新缺陷，是**已有门没覆盖到的面**。补成门，防止后续改动把它们打破。


def test_self_audit_coverage_gaps(vault):
    import subprocess
    import unicodedata

    # ① 分层防线的另一半：门㉕ 只测「篡改身份键的值」，没测「删掉整个键」。
    # 删键后 envelope 照样放行（两键排除出等价面 = 有意），必须由 validator 兜住。
    r = _run_writer(vault, _payload())
    assert r.returncode == 0, r.stdout + r.stderr
    base = _ledger_lines(vault)[0]
    assert _run_validator(vault).returncode == 0, "基线：完整行必须过校验器"
    for key in ("fsrs_library_version", "fsrs_params_hash"):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        dropped = json.loads(json.dumps(base))
        dropped["payload"].pop(key)
        _write_ledger(vault, dropped)
        rw = _run_writer(vault, _payload())
        # round-4 后：消费前复用校验器本体做完整 v1 校验，所以缺键在**写点侧**
        # 就被拦，两侧同口径（此前是「写点放行 + 校验器兜底」的分层）。
        assert rw.returncode != 0, f"删 {key} 后必须在消费前拒"
        assert "未通过校验器的 v1 记录校验" in rw.stderr, rw.stderr
        v = _run_validator(vault)
        assert v.returncode != 0, f"校验器同样拦下 {key}（两侧同口径）"
        assert key in v.stdout, v.stdout[:300]

    # ② Unicode 归一化差异必须构成冲突。
    # ⚠️ 首版探针用汉字节点名做 NFD 变异，结果「放行」——那是**假阴性**：
    # 汉字没有分解形式，NFD(s) == s，变异根本没改字节。必须用有分解形式的字符。
    assert unicodedata.normalize("NFD", "测试节点") == "测试节点", "汉字无分解形式（本断言防后人重蹈）"
    nfc_name = "café笔记"
    assert unicodedata.normalize("NFD", nfc_name) != nfc_name, "fixture 前提：该名字必须真有分解形式"
    node2 = f"节点/{nfc_name}.md"
    (vault / node2).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    r2 = _run_writer(vault, _payload(node=node2, event_id="nfd#q1"))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    base2 = _ledger_lines(vault)[0]
    (vault / node2).write_text(NODE_V0, encoding="utf-8")  # 崩溃窗口①
    nfd = json.loads(json.dumps(base2))
    nfd["node_id"] = unicodedata.normalize("NFD", nfd["node_id"])
    nfd["payload"]["concept_id"] = unicodedata.normalize("NFD", nfd["payload"]["concept_id"])
    assert nfd["node_id"] != base2["node_id"], "变异必须真的改变了字节"
    _write_ledger(vault, nfd)
    r3 = _run_writer(vault, _payload(node=node2, event_id="nfd#q1"))
    assert r3.returncode != 0 and "envelope 冲突" in r3.stderr, r3.stderr

    # ③ payload 键顺序不同**不得**构成冲突（canonical 用 sort_keys，顺序不是事实差异）
    (vault / node2).write_text(NODE_V0, encoding="utf-8")
    reordered = json.loads(json.dumps(base2))
    reordered["payload"] = dict(reversed(list(reordered["payload"].items())))
    assert list(reordered["payload"]) != list(base2["payload"]), "fixture 前提：顺序必须真的变了"
    _write_ledger(vault, reordered)
    r4 = _run_writer(vault, _payload(node=node2, event_id="nfd#q1"))
    assert r4.returncode == 0, "键顺序不是事实差异，不得误报冲突: " + r4.stderr

    # ④ attempt 序数复算成负值时必须 fail-closed（f1=T 但 attempt_count 被人手删）
    v3 = vault
    (v3 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (v3 / "learning_events.jsonl").unlink()
    assert _run_writer(v3, _payload()).returncode == 0
    assert (
        _run_writer(v3, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md")).returncode
        == 0
    )
    text = (v3 / NODE_REL).read_text(encoding="utf-8")
    (v3 / NODE_REL).write_text(re.sub(r"^attempt_count:.*\n", "", text, flags=re.M), encoding="utf-8")
    _face_neg = _write_face(v3)
    r5 = _run_writer(v3, _payload(ts="2026-09-01T12:00:00Z"))
    assert r5.returncode != 0, "attempt 期望值算成负数时必须 fail-closed，不得放行"
    assert _write_face(v3) == _face_neg, "零写（节点 + 账本）"

    # ⑤ 同节点两个适用事件 review_time 完全相同 → 按行号稳定全序，两条都重放
    v4 = vault
    (v4 / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    a = _review_row(event_id="quiz:板A#q1", **{"payload.review_time": TS1})
    b = _review_row(event_id="quiz:板B#q1", **{"payload.review_time": TS1, "payload.attempt_count": 2})
    _write_ledger(v4, a, b)
    r6 = _run_writer_settled(v4, _payload(event_id="板C#q1", ts="2026-08-05T10:00:00Z"))
    assert r6.returncode == 0, r6.stdout + r6.stderr
    replayed = [ln for ln in r6.stdout.splitlines() if "A2 重放已应用" in ln]
    assert len(replayed) == 2, f"同时刻两事件都应被重放，实得 {len(replayed)}: {replayed}"
    assert "板A" in replayed[0] and "板B" in replayed[1], f"全序必须按行号稳定: {replayed}"

    # ⑥ 整秒门放行的宽松字面量必须都归一到**同一个** UTC 整秒瞬间
    # （小写 t / 空格分隔 / -00:00 都是合法 ISO 写法，语义等价，放行无害）
    sys.path.insert(0, str(WT / "backend" / "scripts"))
    try:
        from validate_learning_events import _WHOLE_SECOND_RE
    finally:
        sys.path.remove(str(WT / "backend" / "scripts"))
    from datetime import datetime, timedelta, timezone

    target = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    for lit in (
        "2026-08-01T10:00:00Z",
        "2026-08-01T10:00:00+00:00",
        "2026-08-01T10:00:00-00:00",
        "2026-08-01t10:00:00Z",
        "2026-08-01 10:00:00Z",
    ):
        assert _WHOLE_SECOND_RE.match(lit.strip()), f"{lit!r} 应过字面门"
        d = datetime.fromisoformat(lit.strip().replace("Z", "+00:00"))
        assert d.utcoffset() == timedelta(0) and d.astimezone(timezone.utc) == target, (
            f"{lit!r} 被放行但不是目标瞬间 —— 宽松字面量必须语义等价才无害"
        )
    for lit in ("2026-08-01T10:00:00.000000Z", "2026-08-01T10:00+00:00", "2026-08-01T10:00:00+00:00:00"):
        assert not _WHOLE_SECOND_RE.match(lit.strip()), f"{lit!r} 不应过字面门"


# ── 门㊱ round-2 线索复核（Codex round-2 正文同样被内容过滤器拦，按 stderr 保留的
# 推理标题逐条实测）。1 条真缺陷（R7-blank）+ 3 条「分层成立」需锁住。


def test_round2_lead_followups(vault):
    import subprocess

    # ① R7-blank（真缺陷，本卡修）：截断的判据是「**最后一个非空行**有没有终止 LF」，
    # 不是「文件末尾有没有 LF」。反例：`坏行\n   `（坏行后跟一个纯空白行、文件不以
    # LF 收尾）——旧判据看文件末尾说「无 LF ⇒ 截断」，可那个坏行后面明明还跟着东西。
    good = _review_row(event_id="quiz:旧板", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"
    G = (json.dumps(good, ensure_ascii=False) + "\n").encode("utf-8")
    good2 = dict(good, event_id="quiz:旧板2")
    G2 = (json.dumps(good2, ensure_ascii=False) + "\n").encode("utf-8")
    BAD = b'{"event_id": "quiz:x", "event_ty'
    ledger = vault / "learning_events.jsonl"
    CASES = [
        (G + BAD, True, "坏行无 LF = 真截断"),
        (G + BAD + b"\n", False, "坏行带 LF = 完整损坏"),
        # ⚠️ round-6 口径变更: 空行现在与校验器同口径**拒收**（校验器
        # VALIDATOR:737/:1571 判「append-only JSONL 不应出现空行」，写点此前静默
        # 忽略 ⇒ 写点 rc=0 而校验器 rc=1）。所以这一例的拒因从「坏行带 LF」变成
        # 「第 3 行是空行」—— 两者都是 fail-closed，本门只判必须拒。
        (G + BAD + b"\n   ", False, "坏行带 LF + 末尾空白行 —— 空行门先拦（round-6 口径）"),
        (G + BAD + b"\n   \n", False, "坏行带 LF + 末尾空白行(带 LF)"),
        (G + BAD + b"\r\n", False, "坏行带 CRLF"),
        (G + BAD + b"   ", True, "坏行无 LF 但有尾随空格 = 仍是截断"),
        (BAD, True, "坏行是唯一行且无 LF"),
        (BAD + b"\n", False, "坏行是唯一行但带 LF"),
        # ⚠️ round-6 起空行与校验器同口径拒收，本例的构造本身含空白行 ⇒ 改判为拒。
        (G + b"\n   \n" + BAD, False, "坏行前有空白行 —— round-6 起空行门先拦"),
        # 但原本要验的性质（**前置内容不得让末行的截断判据失真**）不能丢，
        # 用不含空行的等价构造补回来：两条**不同 id** 的合法行 + 无 LF 的坏末行，
        # 仍须按截断隔离。（两条相同的 G 会撞 event_id 全文件唯一门，那是另一回事。）
        (G + G2 + BAD, True, "坏行无 LF，前面有多条合法行（截断判据不得失真）"),
    ]
    for i, (content, tolerate, desc) in enumerate(CASES):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        ledger.write_bytes(content)
        # ⚠️ 用例数超过 9 后 f"2026-08-0{i+1}" 会生成 `2026-08-010` 这种非法日期
        # —— 那是**测试自己的** bug，被 round-6 新加的输入 ts 字面门当场抓住。
        # 用 02d 补零，日期恒合法。
        r = _run_writer(vault, _payload(event_id=f"blank{i}#q1", ts=f"2026-08-{i + 1:02d}T10:00:00Z"))
        if tolerate:
            assert r.returncode == 0, f"[{desc}] 应按截断隔离: {r.stdout}{r.stderr}"
            assert "截断尾行" in r.stdout, f"[{desc}] 应留痕: {r.stdout}"
        else:
            assert r.returncode != 0, f"[{desc}] 应 fail-closed（该行是完整落盘后损坏）"
            # round-6 起空行与校验器同口径拒收，含空白行的用例会先撞空行门。
            # 两种拒因都算达标，但必须点名是这两者之一 —— 不退化成「随便拒了都行」。
            assert ("完整写入的损坏行" in r.stderr) or ("是空行" in r.stderr), f"[{desc}] {r.stderr}"

    # ② 分层成立（非缺陷，锁住）：写点只重放 node_id 匹配的行，故 node_id 缺失/拼错、
    # schema_ext 非法的 review 行**不会被任何节点重放**。写点放行它们是对的（不越权），
    # 但校验器必须全部拦下——否则这些行就成了无人认领的静默丢失面。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    # ⚠️ 分两类，别混（Codex round-3 HIGH 指出前一版把违约锁成了正确）：
    #   - **缺少可用 node_id** ⇒ schema §一「路由信封冻结」的读方义务明文要求
    #     **fail-closed**：不能因为「它看起来不属于本节点」就跳过，因为恰恰
    #     无法判定归属；
    #   - node_id 拼成**别的合法字符串** / schema_ext 非法 ⇒ 写点放行是对的
    #     （不越权管别的节点的行），由校验器兜底。
    for mut, desc in (
        (lambda r: r.pop("node_id"), "node_id 缺失"),
        (lambda r: r.__setitem__("node_id", None), "node_id 为 null"),
        (lambda r: r.__setitem__("node_id", 123), "node_id 非字符串"),
    ):
        row = _review_row(event_id="quiz:孤儿", **{"payload.review_time": "2026-08-05T10:00:00Z"})
        row["effective_at"] = "2026-08-05T10:00:00Z"
        mut(row)
        _write_ledger(vault, row)
        _face_route = _write_face(vault)
        rw = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rw.returncode != 0, f"[{desc}] 不可路由的行必须 fail-closed（§一 路由信封读方义务）"
        assert "不可路由" in rw.stderr or "路由信封" in rw.stderr, rw.stderr
        assert _write_face(vault) == _face_route, f"[{desc}] 零写（节点 + 账本）"
    for mut, desc in (
        # ⚠️ schema_ext 非法的两条已移出本组：它们是**本节点**的行，现在由写点
        # 在适用集构造时直接 fail-closed（§6.1 降级绕过封堵），不再是「写点放行 +
        # 校验器兜底」。见门㊳⑪。本组只留「指向别的节点」这一条 —— 那确实不该
        # 由写点越权管。
        (lambda r: r.__setitem__("node_id", "不存在的节点"), "node_id 指向别的合法名"),
    ):
        row = _review_row(event_id="quiz:孤儿", **{"payload.review_time": "2026-08-05T10:00:00Z"})
        row["effective_at"] = "2026-08-05T10:00:00Z"
        mut(row)
        _write_ledger(vault, row)
        rw = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rw.returncode == 0, f"[{desc}] 写点不该越权拒别的节点的行: {rw.stderr}"
        v = _run_validator(vault)
        assert v.returncode != 0, f"[{desc}] 必须被校验器拦下 —— 否则是无人认领的静默丢失面"
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")

    # ②b 分层成立：envelope 只比 5 个顶层键，多出来的顶层键不进比较 —— 写点放行，
    # 校验器按「v1 冻结恰好 7 键」拦下。而 recorded_at 变化被 envelope **显式排除**
    # （重试时自然变化，§6.2:183），两侧都放行，那是设计不是漏网。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    base_top = _ledger_lines(vault)[0]
    for key, value, validator_must_reject in (
        ("extra_top", "外部注入", True),
        ("recorded_at", "2099-01-01T00:00:00Z", False),
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        row = json.loads(json.dumps(base_top))
        row[key] = value
        _write_ledger(vault, row)
        rw = _run_writer(vault, _payload())
        if validator_must_reject:
            # round-4 后：消费前完整 v1 校验 ⇒ 未知顶层键在写点侧就被拦（两侧同口径）
            assert rw.returncode != 0, f"顶层 {key} 必须在消费前拒: {rw.stderr}"
            assert "未通过校验器的 v1 记录校验" in rw.stderr, rw.stderr
            assert _run_validator(vault).returncode != 0, f"校验器同样拦 {key}"
        else:
            # recorded_at 变化被 envelope 显式排除，且它是合法 v1 字段 ⇒ 两侧都放行
            assert rw.returncode == 0, f"{key} 变化是设计内的，不得误拒: {rw.stderr}"
            assert _run_validator(vault).returncode == 0, f"{key} 不得被误拦"

    # ②c **未标 out_of_order 的迟到/同秒行必须 fail-closed**（Codex round-3
    # BLOCKER①，本卡最后一条）。契约 §6.2 三态语义说「review_time ≤ W 的事件
    # 一律不推进 current state」——那句话的前提是它**要么已应用、要么已标
    # out_of_order 走补录通道**。既没标、校准记录里又找不到它，就无法判定它是
    # 「已应用」还是「被漏掉的真实复习」，而两者对用户的意义完全相反。
    # 实测漏算链：E1@10:00 正常写入（W=10:00）→ 外部追加同节点 E2@**同一秒**
    # 未标 out_of_order（validator rc=0 放行）→ 再写 E3 时 E2 既不进 pending 也
    # 无人过问，账本 attempts 变成 [1,2,2]（E3 复用了 E2 的序数），E2 那次复习
    # 永久消失。判据用 F1（校准记录有无）：它与 mastery/attempt 同一次原子写，
    # 是「已应用」的凭据；「≤ W」只说明不该推进 W，不说明已经算过。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload(event_id="E1#q1")).returncode == 0
    _w = _fm_fields(vault)["fsrs_last_review"]
    for rt_late, desc in ((_w, "同秒"), ("2026-07-01T10:00:00Z", "更早")):
        late = _review_row(event_id="quiz:迟到事件", **{"payload.review_time": rt_late})
        late["effective_at"] = rt_late
        _write_ledger(vault, _ledger_lines(vault)[0], late)
        face = _write_face(vault)
        rl = _run_writer(vault, _payload(event_id="E3#q1", ts="2026-08-03T10:00:00Z"))
        assert rl.returncode != 0, f"[{desc}] 未标 out_of_order 的迟到行不得被静默放过"
        assert "既没标 out_of_order 也不在校准记录里" in rl.stderr, rl.stderr
        assert _write_face(vault) == face, f"[{desc}] 零写（节点 + 账本）"
        _write_ledger(vault, _ledger_lines(vault)[0])  # 复原为只剩 E1
    # 验伪①：**标了** out_of_order 的合法补录行必须放行，且不推进 W
    oo = _review_row(
        event_id="quiz:补录#q1",
        **{"payload.review_time": "2026-07-01T10:00:00Z", "payload.out_of_order": True, "payload.attempt_count": 1},
    )
    oo["effective_at"] = "2026-07-01T10:00:00Z"
    _write_ledger(vault, _ledger_lines(vault)[0], oo)
    ro = _run_writer(vault, _payload(event_id="E3#q1", ts="2026-08-03T10:00:00Z"))
    assert ro.returncode == 0, "标了 out_of_order 的补录行必须放行: " + ro.stderr
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-03T10:00:00Z", "补录行不得推进 W 到 07-01"
    # 验伪②：**已应用**的历史行（校准记录在 frontmatter）必须放行
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload(event_id="E1#q1")).returncode == 0
    assert _run_writer(vault, _payload(event_id="E2#q1", ts="2026-08-02T10:00:00Z")).returncode == 0
    r_ok = _run_writer(vault, _payload(event_id="E3#q1", ts="2026-08-03T10:00:00Z"))
    assert r_ok.returncode == 0, "已应用的历史行必须放行: " + r_ok.stderr
    assert len(_ledger_lines(vault)) == 3

    # ③ 分层成立（非缺陷，锁住）：rating 自洽门不会误拒任何**旧版合法写入**的行。
    # grade_norm 落盘的是 round(GN,2)，分档边界要 gn = 1/6、1/2、5/6，只有 1/2 是精确
    # 两位小数，而 1.0+3.0*0.5 == 2.5 走 `g < 2.5` 为 False ⇒ 稳定落在 3。
    sys.path.insert(0, str(VAULT_SCRIPTS))
    try:
        import fsrs_bridge as fb

        # ⚠️ 原写法是「同一函数对 json 往返前后的同一个值给出相同结果」——
        # CPython 的 float repr 是最短往返, 两侧实参**逐比特相同**, 于是该断言
        # 恒真: 把 rating_from_grade 换成「恒返回 1」或「二值化」都照样绿
        # (实测三个实现全通过)。期望值必须有**独立来源**: 这里直接写 §6.1
        # [Decision-FSRS-1] 的分档契约值 (g = 1 + 3·gn, 按 1.5/2.5/3.5 落四档)。
        for gn, expect in ((0.0, 1), (0.16, 1), (0.17, 2), (0.49, 2), (0.5, 3), (0.83, 3), (0.84, 4), (1.0, 4)):
            got = fb.rating_from_grade(gn, False)
            assert got == expect, f"grade_norm {gn} 的契约档位是 {expect}, 实为 {got}"
        assert fb.rating_from_grade(0.5, False) == 3, "边界 gn=0.5 必须稳定落 3（1+3*0.5 恰为 2.5，走 g<2.5 为假）"
        # 往返稳定性单独验一次（这一条本身不承担分档正确性）
        for cents in (0, 17, 50, 84, 100):
            gn = cents / 100.0
            assert float(json.loads(json.dumps(gn))) == gn, f"{gn} JSON 往返不精确"
    finally:
        sys.path.remove(str(VAULT_SCRIPTS))
        sys.modules.pop("fsrs_bridge", None)

    # ④ 分层成立（非缺陷，锁住）：fixture 脚本的写入面守卫不被 symlink 劫持。
    # ⚠️ 原写法是「源码里有 resolve() 和 MARKER 这两个词」—— 审查实测：把
    # _guard_target() 函数体整体挖空、连调用点一起删掉，两条断言**仍全真**
    # （resolve() 在该文件另有无关出现：WT = Path(__file__).resolve()...）。
    # 断言必须绑定被审对象本身：直接**调用守卫**，看它在两种攻击形态下是否拒。
    import importlib.util as _ilu

    _spec = _ilu.spec_from_file_location(
        "g32b_build_fixture_gate", WT / "backend" / "scripts" / "g32b_build_fixture.py"
    )
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    probe = Path("/private/tmp/g32b-gate-toctou-probe")
    victim = Path("/private/tmp/g32b-gate-toctou-victim")
    for p in (probe, victim):
        if p.is_symlink():
            p.unlink()
        elif p.exists():
            subprocess.run(["rm", "-rf", str(p)], check=True)
    victim.mkdir()
    _orig_root = _mod.FIXTURE_ROOT
    try:
        # ① symlink 劫持：目标是指向别处的软链 ⇒ 守卫必须拒
        probe.symlink_to(victim, target_is_directory=True)
        _mod.FIXTURE_ROOT = probe
        with pytest.raises(SystemExit) as ei:
            _mod._guard_target()
        assert "resolve" in str(ei.value) or "拒跑" in str(ei.value), str(ei.value)
        probe.unlink()
        # ② 陌生目录（无 marker）⇒ 守卫必须拒，绝不 rmtree 别人的目录
        probe.mkdir()
        (probe / "别人的重要文件.txt").write_text("不该被删", encoding="utf-8")
        _mod.FIXTURE_ROOT = probe
        with pytest.raises(SystemExit) as ei2:
            _mod._guard_target()
        assert "标记文件" in str(ei2.value) or "拒绝删除" in str(ei2.value), str(ei2.value)
        assert (probe / "别人的重要文件.txt").exists(), "守卫拒跑时不得动目标目录"
        # ③ 验伪：带 marker 的自己的目录必须放行（否则这门是「恒拒」的假门）
        (probe / _mod.MARKER).write_text("x", encoding="utf-8")
        _mod._guard_target()
    finally:
        _mod.FIXTURE_ROOT = _orig_root
        if probe.is_symlink():
            probe.unlink()
        else:
            subprocess.run(["rm", "-rf", str(probe)], check=True)
        subprocess.run(["rm", "-rf", str(victim)], check=True)


# ── 门㊲ 内部对抗审查（8 个核查面并行探测 + 每条 3 票独立复现）找出的 7 条 ──
# 两轮 Codex 正文都被内容过滤器拦下后补跑的内部审查。7 条全部实测复现过。


def test_internal_audit_findings(vault):
    import unicodedata

    # ① BLOCKER：A2 重放的 pending 行必须**评分事实完整**。
    # R5 只挡住「显式 rating 与 grade_norm 不自洽」，挡不住「rating 干脆没有」——
    # 缺 rating 时 bridge 回落到推导，grade_norm 也缺时用默认 0.0 ⇒ 一次可能是
    # 「答对」的评分被当成 Rating.Again（完全忘记）静默应用（实测 rc=0、W 照常推进）。
    for bad, desc in (
        ({"payload.rating": None}, "rating=null"),
        ({"payload.rating": 3.0}, "rating 是 float"),
        ({"payload.grade_norm": 1.5}, "grade_norm 越界"),
        ({"payload.grade_norm": "0.75"}, "grade_norm 是字符串"),
    ):
        _write_ledger(vault, _review_row(event_id="quiz:板A#q1", **bad))
        r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r.returncode != 0, f"[{desc}] 评分事实不完整的行不得被重放"
        assert len(_ledger_lines(vault)) == 1, f"[{desc}] 零写"
    # 缺键（而非 null）同样拒
    row = _review_row(event_id="quiz:板A#q1")
    row["payload"].pop("rating")
    _write_ledger(vault, row)
    assert _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z")).returncode != 0
    # 验伪：合法行照常重放
    _write_ledger(vault, _review_row(event_id="quiz:板A#q1"))
    rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert rok.returncode == 0 and "A2 重放已应用" in rok.stdout, rok.stdout + rok.stderr

    # ② BLOCKER：A2 重放必须同步 attempt_count，否则写点自己破坏 ordinal 回推的前提。
    # E1 崩溃 → 先答 E2 → 重放 E1 不推进 attempt ⇒ E2 以同一基数写出 attempt=1，
    # durable 变成 [1,1]；此后原样重跑 E1，ordinal 回推算出 0 而 durable 是 1 ⇒
    # 合法历史重放被误报冲突（实测复现）。attempt 与 mastery 不同：它**有事件载荷**。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload()).returncode == 0
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 崩溃窗口①
    # 两阶段（恢复先落定 → 重跑写本次）；attempt 的不变量在**最终**状态上验。
    r2 = _run_writer_settled(
        vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z", exam_board="检验白板/板B.md")
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "A2 重放已应用" in r2.stdout
    assert [x["payload"]["attempt_count"] for x in _ledger_lines(vault)] == [1, 2], (
        "A2 重放必须把 attempt 推到 durable 值，否则下一个事件会复用同一序数"
    )
    assert re.search(r'^attempt_count:\s*"?(\d+)"?\s*$', _fm(vault), re.M).group(1) == "2"

    # ③ BLOCKER：账本按**字节**切行再逐行 decode。
    # BOM 首行（别的编辑器存过）整文件 decode 时会让一条**完整合法**的事件行解析
    # 失败、被当截断跳过、那次评分静默丢失；而腰斩一个多字节字符恰恰是最典型的
    # 崩溃产物——整文件 decode 一失败就全盘拒，自愈路径反而对它不可达。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    row = _review_row(event_id="quiz:板A#q1")
    RJ = json.dumps(row, ensure_ascii=False).encode("utf-8")
    good = _review_row(event_id="quiz:旧板", **{"payload.review_time": "2026-07-01T10:00:00Z"})
    good["effective_at"] = "2026-07-01T10:00:00Z"
    good["node_id"] = "别的节点"
    G = json.dumps(good, ensure_ascii=False).encode("utf-8") + b"\n"
    half_cjk = '{"event_id": "quiz:损'.encode("utf-8")[:-1]  # 腰斩「损」字
    for content, expect, desc in (
        # ⚠️ round-6 口径变更: BOM 现在与校验器同口径**拒收**。实测校验器对
        # BOM 无特例（"Unexpected UTF-8 BOM" 判整个文件不合规），而写点此前用
        # utf-8-sig 剥掉首行 BOM 静默放行 —— 又一处「写点比校验器宽容」的分叉。
        # 写点恒不产出 BOM，出现即外部写入。
        (b"\xef\xbb\xbf" + RJ, "reject", "BOM + 完整合法行（round-6 起与校验器同口径拒收）"),
        (b"\xef\xbb\xbf" + RJ + b"\n", "reject", "BOM + 完整合法行（带 LF）—— 同上，round-6 起拒收"),
        (G + half_cjk, "tolerate", "腰斩 CJK 的末行（无 LF）= 真截断"),
        (G + half_cjk + b"\n", "reject", "腰斩 CJK 的末行（带 LF）= 完整损坏"),
        (b"\xff\xfe bad\n" + RJ, "reject", "首行非 UTF-8 且不是末行"),
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        (vault / "learning_events.jsonl").write_bytes(content)
        # 合法行会成为 foreign pending ⇒ 走「恢复先落定」两阶段，用 settled 取最终态
        r = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        if expect == "reject":
            assert r.returncode != 0, f"[{desc}] 应 fail-closed"
        else:
            assert r.returncode == 0, f"[{desc}] 应放行: {r.stdout}{r.stderr}"
            if expect == "replay":
                assert "A2 重放已应用" in r.stdout, f"[{desc}] 合法行必须被重放，不得当截断跳过"
            else:
                assert "截断尾行" in r.stdout, f"[{desc}] 应按截断隔离: {r.stdout}"

    # ④ HIGH：适用集必须校验挂载点与身份键。只看 schema_ext + node_id 不够——
    # event_type=session_archived / node_derived、concept_id 指向别节点、
    # vault_id 指向别的 vault 的行都会被当成本节点的一次复习照常重放并推进 FSRS
    # （validator 事后判 FAIL，但拦不回已推进的水位线）。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    for bad, desc in (
        ({"event_type": "session_archived"}, "非评分事件类型"),
        ({"event_type": "node_derived"}, "派生事件类型"),
        ({"payload.concept_id": "别的节点"}, "concept_id 错位"),
        ({"payload.vault_id": "别的_vault"}, "vault_id 错位"),
    ):
        _write_ledger(vault, _review_row(event_id="quiz:板A#q1", **bad))
        _face_mount = _write_face(vault)
        r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        # 这些 fixture 都**带着 `schema_ext=review/1`**，所以三种坏行都必须拒：
        # 带 review marker 的非评分事件正是校验器要拦的（"marker 只许挂在评分
        # 事件上"），身份错位同理。两侧同口径。
        assert r.returncode != 0, f"[{desc}] 不得被当成本节点的一次复习重放"
        assert _run_validator(vault).returncode != 0, f"[{desc}] 校验器同样拒（两侧同口径）"
        assert _write_face(vault) == _face_mount, f"[{desc}] 零写（节点 + 账本，尤其不得推进 W）"
    # ⚠️ round-5 MEDIUM 的真实形态：**纯**非评分事件（无任何 review 扩展键）
    # 是合法记录，正确处置是**跳过**。此前 `_looks_like_review_ext()` 对它们也
    # 生效，把「归档了一次会话」误判成「一次被降级绕过的复习」而拒写 ——
    # 校验器 rc=0 而写点 rc=1，误拒方向。
    for etype in ("session_archived", "node_derived"):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        _write_ledger(
            vault,
            {
                "event_id": f"quiz:纯{etype}",
                "event_version": 1,
                "event_type": etype,
                "node_id": "测试节点",
                "recorded_at": TS1,
                "effective_at": TS1,
                "payload": {"vault_id": "canvas_vault_测试"},  # 与 _review_row 同源
            },
        )
        rp = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rp.returncode == 0, f"纯 {etype} 是合法记录，必须跳过而不是拒: {rp.stderr[:250]}"
        assert _run_validator(vault).returncode == 0, f"纯 {etype} 校验器也放行（两侧同口径）"

    # 验伪：合法的两种评分事件类型都必须照常重放
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink(missing_ok=True)
    for etype, rating, gn in (("answer_scored", 3, 0.75), ("answer_abandoned", 1, 0.0)):
        row = _review_row(event_id="quiz:板A#q1", **{"payload.rating": rating, "payload.grade_norm": gn})
        row["event_type"] = etype
        _write_ledger(vault, row)
        rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rok.returncode == 0, f"[{etype}] 合法评分事件必须照常重放: {rok.stderr}"
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")

    # ⑤ HIGH：event_id 首尾空白 ⇒ 同一次评分的两种写法各算一遍（双写账本 + 双吃
    # mastery + attempt 多加一次），而 validator 看不出问题（两个不同的 id 本来合法）。
    # ⛔ 拒绝而不是静默 strip —— strip 会把上游两个本来不同的 id 撞成一个。
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload(event_id="板X#q1")).returncode == 0
    r5 = _run_writer(vault, _payload(event_id="板X#q1 ", ts="2026-08-02T10:00:00Z"))
    assert r5.returncode != 0 and "首尾含空白" in r5.stderr, r5.stderr
    assert len(_ledger_lines(vault)) == 1, "零写"

    # ⑥ MEDIUM：attempt_count 读取正则须容引号。Obsidian Properties 面板会把数值
    # 写成 "3"，原正则不匹配 ⇒ 计数被当 0、序数倒退，还把一个**已被占用的序数**
    # 写进 append-only 账本。
    (vault / NODE_REL).write_text(
        NODE_V0.replace("mastery_score: 0.5\n", 'mastery_score: 0.5\nattempt_count: "3"\n'), encoding="utf-8"
    )
    (vault / "learning_events.jsonl").unlink()
    r6 = _run_writer(vault, _payload(event_id="板Q#q1"))
    assert r6.returncode == 0, r6.stdout + r6.stderr
    assert _ledger_lines(vault)[0]["payload"]["attempt_count"] == 4, (
        "引号形态的 attempt_count 必须被承接为 3 并写出 4，而不是重置为 1"
    )

    # ⑦ MEDIUM：mastery 的业务量必须取 durable 锁定的 round(GN,2)，不是未舍入的 GN。
    # 否则「首跑 gn=0.752」与「恢复重试 gn=0.7549」被 envelope 判为同一件事
    # （两侧 GN2 都是 0.75），产出的 mastery_a 却不同。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink()
    assert _run_writer(vault, _payload(grade_norm=0.752)).returncode == 0
    golden = (vault / NODE_REL).read_bytes()
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    r7 = _run_writer(vault, _payload(grade_norm=0.7549, ts="2026-09-01T10:00:00Z"))
    assert r7.returncode == 0, r7.stdout + r7.stderr
    assert (vault / NODE_REL).read_bytes() == golden, (
        "同一 durable 事件（GN2 相同）在两次不同的未舍入输入下必须产出相同的 mastery"
    )


# ── 门㊳ Codex round-3（第一份拿到正文的独立审查）的 BLOCKER/HIGH 修复 ──
# round-1/2 正文都被内容过滤器拦下；round-3 换中性化措辞后拿到 17993 字节正文，
# 判「需整改」：4 BLOCKER + 多条 HIGH。以下逐条锁住修复。


def test_round3_findings(vault):
    # ① HIGH：未知 event_version 的行不得按 v1 语义 apply。
    # §一 说 v2 出现前读方要「跳过并告警，不炸」——但那是对**别的节点**的行；
    # 本节点的未知版本行若被跳过，那次评分就静默漏算了，所以这里 fail-closed。
    row = _review_row(event_id="quiz:板A#q1")
    row["event_version"] = 2
    _write_ledger(vault, row)
    _face_ver = _write_face(vault)
    r = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r.returncode != 0 and "非 v1" in r.stderr, r.stderr
    assert _write_face(vault) == _face_ver, "零写（节点 + 账本）"

    # ② HIGH：effective_at 与 payload.review_time 必须是同一绝对瞬间。
    # 两者脱钩的行在 dup 路径会被 envelope 拦，但走 foreign pending 时没人管
    # （实测 writer rc=0 而 validator rc=1，两侧口径分叉）。
    bad = _review_row(event_id="quiz:板A#q1")
    bad["effective_at"] = "2026-08-01T11:00:00Z"  # payload.review_time 仍是 10:00
    _write_ledger(vault, bad)
    r2 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r2.returncode != 0 and "不是同一瞬间" in r2.stderr, r2.stderr
    # 验伪 + **写点↔校验器口径对照**：契约 §6.1:106 对 effective_at 只要求「与
    # review_time 同一瞬间（按绝对时刻比较——Z 与 +00:00 是同一瞬间的两种写法，
    # **不按原字符串比**）」，整秒只约束 review_time。
    # ⚠️ 自查抓到的错：这里原本套了 _durable_instant 的严格字面门，于是
    # `+08:00`（同一瞬间但非 UTC 字面）会被写点拒而校验器放行 —— 又一次实现比
    # 契约严的口径分叉（本卡第三次同类错，前两次是 R2 的整秒字面与 R6 的身份键）。
    # 现改用 _instant_only（只比瞬间）。本断言锁的是**两侧结论必须一致**。
    for ea, expect_ok in (
        ("2026-08-01T10:00:00Z", True),
        ("2026-08-01T10:00:00+00:00", True),
        ("2026-08-01T18:00:00+08:00", True),  # 同一瞬间，非 UTC 字面
        ("2026-08-01T11:00:00Z", False),  # 不同瞬间
        ("2026-08-01T10:00:00", False),  # naive
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        ok = _review_row(event_id="quiz:板A#q1")
        ok["effective_at"] = ea
        _write_ledger(vault, ok)
        rok = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        writer_ok = rok.returncode == 0
        assert writer_ok is expect_ok, f"effective_at={ea!r} 写点结论应为 {expect_ok}: {rok.stderr}"
        # 只在写点放行时对照校验器（拒了就没有产物可校验）
        if writer_ok:
            assert _run_validator(vault).returncode == 0, f"effective_at={ea!r} 写点放行但校验器拒 —— 两侧口径分叉"

    # ③ BLOCKER：attempt_count 是 ordinal 回推与恢复的权威值，缺了/非法就无法
    # 证明「这是第几次评分」。旧实现缺键时静默跳过同步（实测 writer rc=0、
    # validator 也 rc=0，账本 attempts=[null,1]：两次评分而笔记计数只有 1）。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    for bad_att, desc in ((None, "缺失"), (0, "为 0"), (-1, "负数"), (True, "bool 伪装"), ("2", "字符串")):
        row = _review_row(event_id="quiz:板A#q1")
        if bad_att is None:
            row["payload"].pop("attempt_count")
        else:
            row["payload"]["attempt_count"] = bad_att
        _write_ledger(vault, row)
        r3 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r3.returncode != 0, f"[attempt_count {desc}] 必须 fail-closed"
        assert "attempt_count 缺失或非法" in r3.stderr, r3.stderr

    # ④ payload 不是 object 时必须 clean fail-closed，不是裸 AttributeError
    for bad_pl in ("字符串 payload", 123, ["a"]):
        row = _review_row(event_id="quiz:板A#q1")
        row["payload"] = bad_pl
        _write_ledger(vault, row)
        r4 = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert r4.returncode != 0, f"payload={bad_pl!r} 必须拒"
        # round-5 后 payload 类型门移到**归属判断之后**（此前排在前面，会误拒
        # 合法的别节点 v2 记录 —— v2 允许 payload 是别的类型）。本节点的行走
        # 「缺 payload 或类型不对」这一支，拒因串因此不同、语义一致。
        assert ("payload 不是 object" in r4.stderr) or ("缺 payload 或其类型不是 object" in r4.stderr), r4.stderr
        assert "Traceback" not in r4.stderr, "必须是 clean fail-closed"

    # ⑤ BLOCKER：恢复与新写必须分成两次原子发布。
    # 旧实现在同一次运行里既重放 foreign pending 又追加本次事件，两个后果：
    # 被重放事件的 mastery/校准无载荷可复放而永久丢失（rc=0 无信号）；
    # 「连续两次发布前崩溃」在**单进程**下就能攒出 2 条 pending，此时 attempt
    # 序数与 mastery 基线都不可证。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    a = _review_row(event_id="quiz:板A#q1", **{"payload.review_time": "2026-08-03T10:00:00Z"})
    a["effective_at"] = "2026-08-03T10:00:00Z"
    b = _review_row(
        event_id="quiz:板B#q1",
        **{"payload.review_time": "2026-08-04T10:00:00Z", "payload.attempt_count": 2},
    )
    b["effective_at"] = "2026-08-04T10:00:00Z"
    _write_ledger(vault, a, b)
    r5 = _run_writer(vault, _payload(event_id="板C#q1", ts="2026-08-05T10:00:00Z"))
    assert r5.returncode != 0, "两条 pending 时不得在同一次运行里既恢复又追加"
    assert "恢复已落定" in r5.stderr, r5.stderr
    assert len([ln for ln in r5.stdout.splitlines() if "A2 重放已应用" in ln]) == 2, "两条都要重放"
    assert "已按各自的账本载荷复放" in r5.stdout, "两条被恢复事件的评分链副作用都要复放"
    assert len(_ledger_lines(vault)) == 2, "第一阶段不得追加本次事件"
    assert _fm_fields(vault)["fsrs_last_review"] == "2026-08-04T10:00:00Z", "恢复结果必须已落盘"
    # 第二阶段：pending 已空，本次评分在干净基线上写入
    r6 = _run_writer(vault, _payload(event_id="板C#q1", ts="2026-08-05T10:00:00Z"))
    assert r6.returncode == 0, r6.stdout + r6.stderr
    assert [x["payload"]["attempt_count"] for x in _ledger_lines(vault)] == [1, 2, 3]
    assert _run_validator(vault).returncode == 0

    # ⑥ 两阶段必须在 2 轮内收敛，且 payload 临时文件要留着让用户能重跑。
    # 「先恢复、再要求重跑」这个结构最大的风险是**不收敛**——每跑一次都说
    # 「恢复已落定请重跑」却永远跑不完。三种时刻关系都要验：被恢复事件的时刻
    # 晚于 / 等于 / 早于本次评分（晚于那档尤其要紧：第二轮里 A3 得把本次时刻
    # 推到 W+1s 才写得进去）。
    for i, (pending_rt, desc) in enumerate(
        (
            ("2026-08-10T10:00:00Z", "被恢复事件晚于本次评分"),
            ("2026-08-02T10:00:00Z", "被恢复事件与本次评分同刻"),
            ("2026-08-01T10:00:00Z", "被恢复事件早于本次评分"),
        )
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        row = _review_row(event_id="quiz:板A#q1", **{"payload.review_time": pending_rt})
        row["effective_at"] = pending_rt
        _write_ledger(vault, row)
        rounds, last = 0, None
        for _ in range(5):
            rounds += 1
            last = _run_writer(vault, _payload(event_id=f"收敛{i}#q1", ts="2026-08-02T10:00:00Z"))
            if not (last.returncode != 0 and "恢复已落定" in last.stderr):
                break
        assert rounds == 2, f"[{desc}] 必须恰好 2 轮收敛，实为 {rounds}: {last.stderr}"
        assert last.returncode == 0, f"[{desc}] 第二轮必须写成: {last.stdout}{last.stderr}"
        assert len(_ledger_lines(vault)) == 2, f"[{desc}] 最终账本 2 行"
    # payload 临时文件必须在第一阶段退出时保留 —— 删了用户就无法重跑，两阶段
    # 结构会把人卡死在中间态。
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    _write_ledger(vault, _review_row(event_id="quiz:板A#q1"))
    rp = _run_writer(vault, _payload(event_id="板P#q1", ts="2026-08-02T10:00:00Z"))
    assert rp.returncode != 0 and "恢复已落定" in rp.stderr
    assert (vault.parent / "payload.json").exists(), "第一阶段退出必须保留 payload，否则无法重跑"

    # ⑦ 复放后必须追平基准（「载荷都在 payload 里」的正面证据）。
    # 我曾反复声明「被恢复事件的 mastery/校准没有事件载荷可复放」并据此不修 ——
    # 那是错的：grade_norm 与 review_time 都在 payload 里，_apply_mastery 要的
    # 正是这两个。实测掌握度：没崩溃连答三次 = 0.59；崩溃后先答下一题，复放前
    # 0.65、复放后 0.59。本门锁住「两条路径的最终掌握度一致」。
    E = [
        (0.75, "2026-08-01T10:00:00Z", "板1"),
        (0.31, "2026-08-02T10:00:00Z", "板2"),
        (0.9, "2026-08-03T10:00:00Z", "板3"),
    ]

    def _mastery(v):
        return re.search(r'^mastery_score:\s*"?([0-9.]+)"?\s*$', _fm(v), re.M).group(1)

    va = vault
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (va / "learning_events.jsonl").unlink()
    for gn, ts, b in E:
        assert (
            _run_writer(
                va, _payload(grade_norm=gn, ts=ts, event_id=b + "#q1", exam_board=f"检验白板/{b}.md")
            ).returncode
            == 0
        )
    baseline = _mastery(va)

    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (va / "learning_events.jsonl").unlink()
    assert (
        _run_writer(
            va, _payload(grade_norm=E[0][0], ts=E[0][1], event_id="板1#q1", exam_board="检验白板/板1.md")
        ).returncode
        == 0
    )
    after1 = (va / NODE_REL).read_bytes()
    assert (
        _run_writer(
            va, _payload(grade_norm=E[1][0], ts=E[1][1], event_id="板2#q1", exam_board="检验白板/板2.md")
        ).returncode
        == 0
    )
    (va / NODE_REL).write_bytes(after1)  # 第 2 次「写完日志但改笔记前退出」
    r7 = _run_writer_settled(
        va, _payload(grade_norm=E[2][0], ts=E[2][1], event_id="板3#q1", exam_board="检验白板/板3.md")
    )
    assert r7.returncode == 0, r7.stdout + r7.stderr
    assert _mastery(va) == baseline, (
        f"复放后掌握度必须追平基准：崩溃路径 {_mastery(va)} vs 基准 {baseline}"
        "（不一致说明第 2 次评分的 mastery 没被复放）"
    )
    assert _run_validator(va).returncode == 0

    # ⑧ attempt 同步的期望值必须**可证**，不能用 max() 抹平差异。
    # 我先写成 max(durable, current)（"单调不减，绝不把更大的计数改小"）——
    # 审查一句话推翻：「不要以 max() 修复事实」。max 会把**非法低序数**伪装成
    # 单调不减而放过去：实测笔记 99 + durable 序数 1，两次评分后笔记只到 100、
    # 账本 [1,100]，中间漏加了一次。
    # 正确判据按「这个事件的副作用应用过没有」分两档：没应用过 ⇒ durable 应恰为
    # 笔记值 + 1（它被写出来时的定义）；应用过 ⇒ 笔记里已经是 durable 值本身
    # （degraded 落账那一档）。两档都不满足 = 序数关系不可证 ⇒ 停下。
    (va / NODE_REL).write_text(
        NODE_V0.replace("mastery_score: 0.5\n", "mastery_score: 0.5\nattempt_count: 99\n"), encoding="utf-8"
    )
    _write_ledger(va, _review_row(event_id="quiz:板A#q1"))
    face8 = _write_face(va)
    r8 = _run_writer(va, _payload(event_id="板Z#q1", ts="2026-08-05T10:00:00Z"))
    assert r8.returncode != 0, "durable 序数与笔记对不上时必须停下，不得用 max() 抹平"
    assert "序数关系不可证" in r8.stderr, r8.stderr
    assert _write_face(va) == face8, "零写（节点 + 账本）"
    # 验伪：序数**对得上**时必须照常重放（本门不是「凡有 pending 就拒」的假门）
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (va / "learning_events.jsonl").unlink()
    assert _run_writer(va, _payload(event_id="正常A#q1")).returncode == 0
    ok_bytes = (va / NODE_REL).read_bytes()
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 崩溃窗口①：durable=1、笔记=0
    r8b = _run_writer(va, _payload(event_id="正常A#q1", ts="2026-09-01T10:00:00Z"))
    assert r8b.returncode == 0, "序数对得上时必须照常恢复: " + r8b.stderr
    assert (va / NODE_REL).read_bytes() == ok_bytes

    # ⑧b **变异照出的死门补强**：⑧ 的场景（durable 1 < 期望 100）在 max() 变异下
    # 仍然会拒，所以杀不掉那个变异。真正只有 max() 才放过的是**反方向**：
    # durable **大于**期望值时 `_n_ != max(_n_, _exp_n_)` 恒假 ⇒ 静默放行。
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (va / "learning_events.jsonl").unlink()
    _write_ledger(va, _review_row(event_id="quiz:超前#q1", **{"payload.attempt_count": 5}))
    face8b = _write_face(va)
    r8b2 = _run_writer(va, _payload(event_id="板Y#q1", ts="2026-08-05T10:00:00Z"))
    assert r8b2.returncode != 0, "durable 序数**大于**期望值时同样不可证，必须停下（max() 会放过它）"
    assert "序数关系不可证" in r8b2.stderr, r8b2.stderr
    assert _write_face(va) == face8b, "零写"

    # ⑪b **marker 被整个抹掉、只留扩展键**必须拒（复用校验器的 _looks_like_review_ext）。
    # ⚠️ 我一度把这条登记成「两侧都放过、属契约缺口、移交不修」——那个判断是错的：
    # 校验器一直在拒（"复习事件 payload 含扩展键但缺 schema_ext 标记"），落后的是
    # 写点。而我手写的键集（含 grade_norm/attempt_count）还误伤过合法历史行；
    # 校验器的 REVIEW_EXT_KEYS 不含那三个键，对 §6.3 存量零误报。
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    row_nm = _review_row(event_id="quiz:抹掉marker#q1")
    row_nm["payload"].pop("schema_ext")
    _write_ledger(va, row_nm)
    face11b = _write_face(va)
    r11b = _run_writer(va, _payload(event_id="板W#q1", ts="2026-08-05T10:00:00Z"))
    assert r11b.returncode != 0, "抹掉 marker 但留扩展键 = 把完整评分伪装成历史行，必须拒"
    assert "降级绕过" in r11b.stderr or "扩展键" in r11b.stderr, r11b.stderr
    assert _write_face(va) == face11b, "零写"

    # ⑫ **本次事件与别人的事件同处待恢复队列**必须停（两阶段无法同时正确处理两者）。
    # 实测（current 在前、foreign 在后）：第一轮发布后水位线与校准只反映 foreign，
    # 第二轮起本次事件恒落进「FSRS 已应用但缺校准记录」的人工裁定 —— **永久不收敛**。
    # dup 行必须是**真实的** durable 行（否则先被 envelope 门拦下，走不到这道门）：
    # 正常写一次 → 回滚节点造崩溃窗口① → 再追加一条别人的未完成事件。
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (va / "learning_events.jsonl").unlink()
    assert _run_writer(va, _payload()).returncode == 0
    cur = _ledger_lines(va)[0]
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")  # 崩溃窗口①：dup 变 pending
    frn = _review_row(
        event_id="quiz:板F#q1", **{"payload.review_time": "2026-08-02T10:00:00Z", "payload.attempt_count": 2}
    )
    frn["effective_at"] = "2026-08-02T10:00:00Z"
    _write_ledger(va, cur, frn)
    face12 = _write_face(va)
    r12 = _run_writer(va, _payload())
    assert r12.returncode != 0, "本次事件与 foreign 同处待恢复队列时必须停下"
    assert "同处待恢复队列" in r12.stderr, r12.stderr
    assert _write_face(va) == face12, "零写"

    # ⑬ **YAML 单引号标量的 '' 转义**必须还原（Obsidian 规范化后的形态）。
    # 不还原就把 'O''Brien#q1' 读成 O''Brien#q1，F1 假阴性 ⇒ 同一次评分的
    # mastery/校准被算第二遍。
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (va / "learning_events.jsonl").unlink()
    eid_q = "O'Brien#q1"
    assert _run_writer(va, _payload(event_id=eid_q)).returncode == 0
    # 模拟 Obsidian 把双引号标量规范化成单引号标量（'' 表示一个字面单引号）
    text_q = (va / NODE_REL).read_text(encoding="utf-8")
    # round-6 后落盘的是完整 id（`quiz:` + 本地 id）
    assert f'- event_id: "quiz:{eid_q}"' in text_q, f"fixture 前提：写点落盘应为双引号形态: {text_q[:400]}"
    # ⚠️ 替换的源串必须是**落盘的完整 id**（`quiz:` 前缀）。round-6 改存完整 id 后
    # 这里仍用裸 eid_q，替换**静默不生效** ⇒ 单引号形态根本没构造出来，
    # 门也就走不到被测的那条分支（M46 SURVIVED 的真因：门与变异不匹配）。
    _norm_q = text_q.replace(f'- event_id: "quiz:{eid_q}"', "- event_id: 'quiz:O''Brien#q1'")
    assert _norm_q != text_q, f"fixture 预置必须真的换成单引号形态: {text_q[:300]}"
    (va / NODE_REL).write_text(_norm_q, encoding="utf-8")
    sha_q = _sha(va / NODE_REL)
    rq = _run_writer(va, _payload(event_id=eid_q, ts="2026-09-01T10:00:00Z"))
    assert rq.returncode == 0 and "幂等跳过" in rq.stdout, (
        "YAML 单引号 '' 转义形态下 F1 必须命中，否则副作用被算第二遍: " + rq.stdout + rq.stderr
    )
    assert _sha(va / NODE_REL) == sha_q, "幂等跳过不得改动节点"

    # ⑨ attempt 读取正则必须容 YAML 的单引号标量（Obsidian Properties 会写引号）
    for lit, expect in (('"7"', 8), ("'7'", 8), ("7", 8)):
        (va / NODE_REL).write_text(
            NODE_V0.replace("mastery_score: 0.5\n", f"mastery_score: 0.5\nattempt_count: {lit}\n"),
            encoding="utf-8",
        )
        (va / "learning_events.jsonl").unlink()
        r9 = _run_writer(va, _payload(event_id=f"引号{lit.strip(chr(34)).strip(chr(39))}#q1"))
        assert r9.returncode == 0, r9.stderr
        got = _ledger_lines(va)[0]["payload"]["attempt_count"]
        assert got == expect, f"attempt_count: {lit} 应承接为 {expect}，实为 {got}"

    # ⑩ **degraded 落账过的 foreign 事件被重放时不得双吃 EMA**（复放修复自己
    # 引入的 BLOCKER）。裁决② 下 fsrs 不可用时事件仍落账，且 mastery/校准
    # **已经写过**，只是没写 W。此后它作为 foreign pending 被重放，若无条件
    # 重算 mastery 就是吃第二遍 —— 而账本与校准日志看上去完全正常，缺陷不可见。
    # 判据：「A 在 degraded 下落账 → 评 B」的最终掌握度，必须等于
    #       「A 正常落账 → 评 B」的最终掌握度。
    def _run_pair(degraded_first):
        (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        lp = va / "learning_events.jsonl"
        if lp.exists():
            lp.unlink()
        env = {"FSRS_BRIDGE_REEXEC": "1"} if degraded_first else None
        assert (
            _run_writer(
                va, _payload(grade_norm=0.75, ts=TS1, event_id="双吃A#q1", exam_board="检验白板/A.md"), env_extra=env
            ).returncode
            == 0
        )
        r = _run_writer_settled(
            va, _payload(grade_norm=0.31, ts="2026-08-02T10:00:00Z", event_id="双吃B#q1", exam_board="检验白板/B.md")
        )
        assert r.returncode == 0, r.stdout + r.stderr
        return re.search(r'^mastery_score:\s*"?([0-9.]+)"?\s*$', _fm(va), re.M).group(1)

    normal_path = _run_pair(degraded_first=False)
    degraded_path = _run_pair(degraded_first=True)
    assert degraded_path == normal_path, (
        f"degraded 落账过的事件被重放时不得再吃一次 EMA：degraded 路径 {degraded_path} vs 正常路径 {normal_path}"
    )

    # ⑪ **marker 降级绕过**（§6.1「降级绕过封堵」，写点侧此前缺这道门）。
    # 本节点的行只有在既没有 schema_ext、也没有任何扩展键时才是真·历史行
    # （§6.3，旧写点产物）。marker 拼错或被抹掉却带着扩展键 —— 那是一次真实
    # 复习被伪装成历史行，静默跳过它就是永久漏算。实测：把 schema_ext 改成
    # "review/01"，writer 照常 rc=0、账本两行，而那次复习完全消失
    # （fsrs_state 1 而非 2，due 差一周）；同一种坏行带**本次** id 会被 dup
    # 分支拦下，带别人的 id 就静默丢 —— 同一份数据两种命运。
    for bad_marker, desc in (
        ("review/01", "marker 拼错"),
        ("review/2", "未来版本 marker"),
        (1, "marker 非字符串"),
        # ⚠️ 不含「marker 被抹掉」：只留扩展键、marker 整个消失的行，写点与校验器
        # **两侧都**当历史行放过（§6.3 对无 marker 行不判 payload 键集）。要堵它
        # 得先改契约，单侧收紧就是又一次口径分叉 —— 已登记移交，不在本卡修。
    ):
        (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        row = _review_row(event_id="quiz:降级#q1")
        if bad_marker is None:
            row["payload"].pop("schema_ext")
        else:
            row["payload"]["schema_ext"] = bad_marker
        _write_ledger(va, row)
        face = _write_face(va)
        rd = _run_writer(va, _payload(event_id="降级B#q1", ts="2026-08-02T10:00:00Z"))
        assert rd.returncode != 0, f"[{desc}] 带扩展键却 marker 不合规的本节点行不得被当历史行跳过"
        assert "降级绕过" in rd.stderr or "schema_ext" in rd.stderr, rd.stderr
        assert _write_face(va) == face, f"[{desc}] 零写（节点 + 账本）"
    # 验伪：**真·历史行**（无 marker 也无任何扩展键，§6.3）必须照常跳过而不报错
    (va / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    legacy = {
        "event_id": "quiz:真历史行",
        "event_version": 1,
        "event_type": "answer_scored",
        "node_id": "测试节点",
        "recorded_at": "2026-07-01T10:00:00Z",
        "effective_at": "2026-07-01T10:00:00Z",
        "payload": {"exam_board": "旧板", "note": "旧写点产物"},
    }
    _write_ledger(va, legacy)
    rl2 = _run_writer(va, _payload(event_id="历史B#q1", ts="2026-08-02T10:00:00Z"))
    assert rl2.returncode == 0, "真·历史行（§6.3）必须照常跳过: " + rl2.stderr
    assert len(_ledger_lines(va)) == 2


# ── 门㊴ round-4 HIGH/MEDIUM: 消费侧与校验器的**结论对照**（不是单侧断言）──


def test_round4_writer_validator_verdict_parity(vault):
    """同一条账本行, 写点与校验器必须给出**相同结论**。

    单侧断言（「写点应该拒 X」）只能证明「我按我想的做了」; 两侧对照才能抓出
    口径分叉——round-4 报的 HIGH「消费侧 v1 准入不完整」与 MEDIUM「词法接收集
    分叉」都是这类: 顶层 `[]` / 缺 payload / `event_version: true`
    (`True == 1` 在 Python 里成立) / 时刻首尾带空白, 四种形态**写点 rc=0 而
    校验器 rc=1**, 全是**漏网**方向。

    修法是消费前复用校验器本体的 `validate_record_full`, 而不是在写点里手写
    第二套判据 (DD-03/DD-13 同一条理由; 见 §6.2 A8)。

    ⚠️ 对照的**适用范围是本节点的行**: 写点只对自己要消费的行负责, 别的节点
    的不合规行由校验器兜底, 写点不得越权阻塞 (末尾两条验伪守着这条边界)。

    ⚠️ **这道门的鉴别力边界**(如实写明, 免得后人高估它): 它证明的是「两侧结论
    一致」, 不是「写点自己那几道手写门有用」。写点里排在 validate_record_full
    **之前**的几道手写准入 (顶层是 object / event_version 非 bool / 归属判断
    位置) 与校验器**功能重合** —— 单独删掉其中一道, 校验器仍拦住, 本门照样绿。
    实测: M49/M50 两条变异在只删手写门时 SURVIVED, 挂上「同时禁掉校验器那层」
    后才 KILLED。**门的鉴别力要靠变异去量, 不能靠读断言想当然。**
    """
    base = _review_row()

    def _mutate(fn):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        row = json.loads(json.dumps(base))
        raw = fn(row)
        if raw is None:
            _write_ledger(vault, row)
        else:
            (vault / "learning_events.jsonl").write_text(raw, encoding="utf-8")
        # 合法行会触发两阶段发布（恢复先落定 + 要求重跑）——那是设计内的续跑
        # 信号, 不是拒绝, 所以用会自动续跑的 settled 版本判"最终写成没有"。
        w = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        return w.returncode == 0, _run_validator(vault).returncode == 0, w

    CASES = (
        # round-5 线索: `\x0c`(换页) 是 **Python** 眼里的空白但**不是 JSON 空白**
        # (RFC 8259 只认 space/tab/CR/LF)。写点曾用 `_line.strip()` 洗掉它再解析 ⇒
        # 解析成功、放行; 校验器不 strip、判 `Extra data` ⇒ 拒。又一次「洗值」分叉,
        # 与 MEDIUM「时刻首尾空白」同源 —— 我修了字段级的 strip, 漏了**行级**的。
        ("行尾裸换页 \\x0c", lambda r: json.dumps(r) + "\x0c\n"),
        ("行尾裸垂直制表 \\x0b", lambda r: json.dumps(r) + "\x0b\n"),
        ("顶层是 JSON 数组", lambda r: "[]\n"),
        ("顶层是 JSON 数字", lambda r: "12345\n"),
        ("本节点行缺 payload", lambda r: r.pop("payload") and None),
        ("event_version 为 true", lambda r: r.__setitem__("event_version", True)),
        ("review_time 首尾空白", lambda r: r["payload"].__setitem__("review_time", " 2026-08-01T10:00:00Z ")),
        ("未知顶层字段", lambda r: r.__setitem__("未知顶层", 1)),
        ("缺 fsrs_library_version", lambda r: r["payload"].pop("fsrs_library_version") and None),
        ("rating 越界为 9", lambda r: r["payload"].__setitem__("rating", 9)),
    )
    for desc, fn in CASES:
        wok, vok, w = _mutate(fn)
        assert wok == vok, f"[{desc}] 写点 ok={wok} 校验器 ok={vok} — 口径分叉: {w.stderr[:200]}"
        assert not wok, f"[{desc}] 两侧应当都拒（本例是不合规输入）"

    # 验伪①: 完全合法的行两侧都必须放行 —— 否则「写点恒拒」也能骗过上面的对照
    wok, vok, w = _mutate(lambda r: None)
    assert wok and vok, f"合法行两侧都必须放行: writer={w.stderr[:200]}"

    # 验伪①b: **JSON 自己允许的空白**(CR) 不得被误拒 —— 去掉 .strip() 的修法
    # 若改成「任何尾随字节都拒」就会误伤 CRLF 账本, 那是从漏网翻到误拒的另一侧。
    wok, vok, w = _mutate(lambda r: json.dumps(r) + "\r\n")
    assert wok and vok, f"尾随 CR 是 RFC 8259 允许的空白, 两侧都必须放行: {w.stderr[:200]}"

    # 验伪②: **别节点**的不合规行不得阻塞本次写入（写点只管自己消费的行）
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    other = json.loads(json.dumps(base))
    other["node_id"] = "别的节点"
    other["event_id"] = "quiz:别节点坏行"
    del other["payload"]
    _write_ledger(vault, other)
    r2 = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r2.returncode == 0, f"别节点的坏行不得越权阻塞本节点写入: {r2.stderr[:300]}"
    assert _run_validator(vault).returncode != 0, "但它仍应被校验器兜住（分层边界成立）"


# ── 门㊵ round-5 BLOCKER: 校准键剥前缀导致 ID 碰撞 ⇒ 一次复习静默消失 ──


def test_round5_calibration_key_prefix_collision(vault):
    """校准记录曾存**剥掉 `quiz:` 前缀**的 event_id, 于是账本里的 `quiz:K` 与
    `K` 落到同一个键上, F1 判定无法区分。

    ⚠️ 实测漏算链: 账本 3 次评分 (`quiz:K` / `K` / 本次), 第二条因剥前缀后与第一条
    同名而被误判「已应用」⇒ 跳过复放 ⇒ 校准只记 2 条、attempt 停在 2,
    **那次复习永久消失且 rc=0 无任何提示**。

    ⚠️ 另两种 attempt 排列恰好被序数门顶住而 fail-closed —— 那是**巧合不是设计**。
    「被别的门兜住」不等于缺陷不存在: 只要换一个排列 (第二行 attempt 恰等于误判
    分支算出的期望值) 就穿过去了。这正是本门要锁住的那一个排列。

    修法: 写入存**完整** event_id; F1 查询完整形态优先, 剥前缀形态**仅作历史
    兼容回落** (回落不能反向做 —— 拿剥前缀的键去撞完整记录正是碰撞的来源)。
    """

    def _three_scored(id1, id2, n2):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        rows = []
        for eid, rt, n in ((id1, TS1, 1), (id2, "2026-08-01T10:00:01Z", n2)):
            row = _review_row(**{"payload.review_time": rt, "effective_at": rt})
            row["event_id"] = eid
            row["payload"]["attempt_count"] = n
            rows.append(row)
        _write_ledger(vault, *rows)
        r = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        fm = (vault / NODE_REL).read_text(encoding="utf-8")
        # _fm_fields 只抽 fsrs_*，attempt_count 直接读（容 YAML 引号标量）
        _m = re.search(r"^attempt_count:\s*[\"']?(\d+)[\"']?\s*$", fm, re.M)
        return r, re.findall(r"^  - event_id: (.+)$", fm, re.M), (int(_m.group(1)) if _m else None)

    # ① 碰撞 + attempt 恰好对上误判期望 —— 修复前正是这个排列穿过了序数门
    r, cal, att = _three_scored("quiz:K", "K", 1)
    assert not (r.returncode == 0 and len(cal) < 3), (
        f"碰撞键不得静默漏算: rc={r.returncode} 校准{len(cal)}条 attempt={att}"
    )
    # ② 碰撞 + 序数自洽 ⇒ **歧义即停**（round-5 修订的口径）。
    # ⚠️ 我一度把期望写成「都能正常复放」——那是错的：历史校准条目存的是**剥前缀**
    # 形态，遇到 `K` 与 `quiz:K` 并存时，一条裸键条目到底对应哪一个**无法证明**。
    # 猜一个就会让另一个静默不入账（正是本门开头那条漏算链）。可证的处置只有停下。
    r, cal, att = _three_scored("quiz:K", "K", 2)
    assert r.returncode != 0, f"裸形态相同的两个 event_id 并存时必须 fail-closed: {cal}"
    assert "裸形态相同的多个 event_id" in r.stderr, r.stderr
    assert "请人工统一这些 id" in r.stderr, "拒因必须给出可执行的处置方式"

    # 验伪①: 不碰撞的正常场景不得回归
    r, cal, att = _three_scored("quiz:甲", "quiz:乙", 2)
    assert r.returncode == 0 and len(cal) == 3 and att == 3, f"正常场景回归: {cal} {att}"

    # 验伪②: **历史**剥前缀形态的校准记录必须仍被认出（否则旧笔记会被重复复放）
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    row = _review_row()
    row["event_id"] = "quiz:老键"
    _write_ledger(vault, row)
    assert _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z")).returncode == 0
    t = (vault / NODE_REL).read_text(encoding="utf-8")
    t2 = t.replace('event_id: "quiz:老键"', 'event_id: "老键"')
    assert t2 != t, "预置必须与旧形态可区分"
    (vault / NODE_REL).write_text(t2, encoding="utf-8")
    r2 = _run_writer_settled(vault, _payload(event_id="板C#q1", ts="2026-08-03T10:00:00Z"))
    assert r2.returncode == 0, r2.stderr[:300]
    t3 = (vault / NODE_REL).read_text(encoding="utf-8")
    assert t3.count('event_id: "quiz:老键"') + t3.count('event_id: "老键"') == 1, (
        "历史剥前缀形态的校准记录必须被回落命中，否则旧笔记会被重复复放（双吃 EMA）"
    )


# ── 门㊶ round-5: 路由顺序 + 输入字面校验 ──


def test_round5_routing_order_and_input_literal(vault):
    """round-5 的路由顺序与输入校验三条，逐条锁住。

    ① **完整校验必须排在 marker/乱序分流之前**：那两条分支都以 `continue` 结束，
       排在校验后面等于「先放行再校验」——实测一条标了 `out_of_order`、时刻带
       首尾空白的行，校验器 rc=1 而写点 rc=0 并照常写入下一次评分。
    ② **必须传 golden manifest**：不传等于**没执行**算法身份真值绑定——实测
       `fsrs_library_version="999.999"` + 全零 hash 时校验器 CLI rc=1 而写点放行。
    ③ **本次输入 ts 按字面校验且拒而不洗**：它会**原样**写进账本 `recorded_at`，
       而 bridge 入口的 `.strip()` 只洗自己那份拷贝 ⇒ 写点 rc=0 而账本落库带空白、
       校验器 rc=1。**写点自己产出了不合规的行**，比消费侧漏网更糟。
    """
    # ① 乱序分流之前必须已完整校验
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    _write_ledger(vault, _review_row())
    assert _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z")).returncode == 0
    bad = _review_row(**{"payload.review_time": " 2026-07-01T10:00:00Z ", "effective_at": " 2026-07-01T10:00:00Z "})
    bad["event_id"] = "quiz:乱序空白"
    bad["payload"]["out_of_order"] = True
    with (vault / "learning_events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(bad, ensure_ascii=False) + "\n")
    face = _write_face(vault)
    r = _run_writer_settled(vault, _payload(event_id="板C#q1", ts="2026-08-03T10:00:00Z"))
    assert r.returncode != 0, "标了 out_of_order 但时刻带空白的行必须在分流前被校验拦下"
    assert _run_validator(vault).returncode != 0, "校验器同样拒（两侧同口径）"
    assert _write_face(vault) == face, "零写（节点 + 账本）"

    # ② golden manifest 必须真正传进去
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    forged = _review_row(**{"payload.fsrs_library_version": "999.999", "payload.fsrs_params_hash": "0" * 64})
    _write_ledger(vault, forged)
    r2 = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert r2.returncode != 0, "伪造的 fsrs 身份键必须被 manifest 绑定门拦下"
    assert _run_validator(vault).returncode != 0, "校验器同样拒（两侧同口径）"

    # ③ 输入 ts 字面校验：拒而不洗
    for bad_ts, why in ((" 2026-08-02T10:00:00Z ", "首尾空白"), ("2026-08-02T10:00:00+00:00:00", "畸形偏移")):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        (vault / "learning_events.jsonl").unlink(missing_ok=True)
        r3 = _run_writer_settled(vault, _payload(event_id="板A#q1", ts=bad_ts))
        assert r3.returncode != 0, f"输入 ts {why} 必须拒: {r3.stderr[:200]}"
        assert "不符 §三 受理语法" in r3.stderr, r3.stderr
        assert not (vault / "learning_events.jsonl").exists() or not _ledger_lines(vault), (
            f"{why} 的输入不得产出任何账本行"
        )
    # 验伪：两种合法写法（Z 与 +08:00 偏移）都不得被误拒
    for good_ts in ("2026-08-02T10:00:00Z", "2026-08-02T18:00:00+08:00"):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        (vault / "learning_events.jsonl").unlink(missing_ok=True)
        rg = _run_writer_settled(vault, _payload(event_id="板A#q1", ts=good_ts))
        assert rg.returncode == 0, f"合法 ts {good_ts} 不得被误拒: {rg.stderr[:200]}"
        assert _run_validator(vault).returncode == 0, f"{good_ts} 产出的账本必须合规"


# ── 门㊷ round-5 HIGH: §6.3 历史评分行被序数回推漏计 ──


def test_round5_legacy_scored_rows_break_ordinal_proof(vault):
    """§6.3 历史评分行（旧写点产物，**没有 attempt_count**）同样推进过 attempt，
    但它们不在适用集里，序数回推把它们漏计。

    ⚠️ 实测：正常写 E1、L 两次评分后，把 L 转成合法的历史形态（去 marker 与全部
    review 扩展键，validator `rc=0`），原样重跑 E1 被报「**envelope 冲突**」。
    那个诊断是**错的** —— 评分事实并无不一致，不一致的是算出的期望序数。

    处置按审查者口径「不伪造期望值」：报真因停下，而不是硬算一个数再以 envelope
    冲突的名义拒绝。⛔ 本门锁的是**诊断的正确性**，不只是"拒了就行"——
    一个错的拒因会把用户引去查根本没错的地方。
    """
    for eid, ts in (("E1#q1", TS1), ("L#q1", "2026-08-01T11:00:00Z")):
        assert _run_writer_settled(vault, _payload(event_id=eid, ts=ts)).returncode == 0
    rows = list(_ledger_lines(vault))  # 已是解析好的 dict
    assert len(rows) == 2
    # 把第二条转成合法 §6.3 历史行（无 marker、无任何 review 扩展键）
    rows[1]["payload"] = {"exam_board": "旧板", "note": "旧写点产物"}
    (vault / "learning_events.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8"
    )
    assert _run_validator(vault).returncode == 0, "改造后的账本本身必须合规（§6.3 允许该形态）"

    face = _write_face(vault)
    r = _run_writer(vault, _payload(event_id="E1#q1", ts=TS1))
    assert r.returncode != 0, "序数不可证时必须停下"
    assert "§6.3 历史评分行" in r.stderr, f"拒因必须点名真因，而不是 envelope 冲突: {r.stderr[:300]}"
    # ⚠️ 不能写成 `"envelope 冲突" not in r.stderr` —— 修复后的拒因文案里**自带**
    # 「不以 envelope 冲突的名义拒绝」这句话，那样断言恒假。要判的是它没有被
    # **报成** envelope 冲突，即那条错误诊断的原句不出现。
    assert "与本次评分事实不一致" not in r.stderr, f"不得把序数不可证伪装成评分事实不一致: {r.stderr[:300]}"
    # round-6 后拒因更具体了：直接指名**哪几行**要补**什么字段**，
    # 而不是笼统的「请人工核对」。判据跟着收紧，不退回宽松匹配。
    assert "补上 attempt_count" in r.stderr, f"拒因必须指名要补的字段: {r.stderr[:300]}"
    assert re.search(r"第 \[\d+", r.stderr), f"拒因必须指名具体行号: {r.stderr[:300]}"
    assert _write_face(vault) == face, "零写（节点 + 账本）"

    # 验伪：没有历史行时，正常的幂等重跑不得被这条新分支误伤
    v2 = vault / "_"  # 同一 fixture 内重置
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    (vault / "learning_events.jsonl").unlink(missing_ok=True)
    for eid, ts in (("E1#q1", TS1), ("E2#q1", "2026-08-01T11:00:00Z")):
        assert _run_writer_settled(vault, _payload(event_id=eid, ts=ts)).returncode == 0
    sha = _sha(vault / NODE_REL)
    rg = _run_writer(vault, _payload(event_id="E1#q1", ts=TS1))
    assert rg.returncode == 0, f"无历史行时幂等重跑不得被误拒: {rg.stderr[:250]}"
    assert "幂等跳过" in rg.stdout, rg.stdout[:200]
    assert _sha(vault / NODE_REL) == sha, "幂等重跑必须零写"


# ── 门㊸ round-6: 3 BLOCKER + 4 HIGH + 1 MEDIUM ──


def test_round6_findings(vault):
    """round-6 的问题逐条锁住。

    ⛔ **B①是我 round-5 修复引入的**：我只把 foreign 分支改成存完整 event_id，
       正常分支仍存裸 `eid` —— 两条路径写进 calibration_log 的键**不是同一个
       东西**。修一半比不修更危险：它把不一致藏进了「已经修过」的地方。
    """
    LED = vault / "learning_events.jsonl"

    # B① 正常路径也必须存完整 evid（否则 quiz:K 与 K 互相别名）
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    LED.unlink(missing_ok=True)
    assert _run_writer_settled(vault, _payload(event_id="quiz:K", ts=TS1)).returncode == 0
    fm = (vault / NODE_REL).read_text(encoding="utf-8")
    assert '- event_id: "quiz:quiz:K"' in fm, f"正常路径必须存完整账本 id: {fm[:400]}"
    r2 = _run_writer_settled(vault, _payload(event_id="K", ts="2026-08-02T10:00:00Z"))
    assert r2.returncode == 0, r2.stderr[:300]
    assert len(_ledger_lines(vault)) == 2, "两次不同评分必须各自入账"
    assert len(re.findall(r"^  - event_id: ", (vault / NODE_REL).read_text(encoding="utf-8"), re.M)) == 2

    # B② durable event_id 首尾空白必须全账本扫描（不只本次输入）
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    row = _review_row()
    row["event_id"] = " quiz:same#q1 "
    _write_ledger(vault, row)
    face = _write_face(vault)
    rb = _run_writer(vault, _payload(event_id="same#q1", ts="2026-08-02T10:00:00Z"))
    assert rb.returncode != 0, "带空白的 durable id 会与不带的各算一遍，必须拒"
    assert "首尾含空白的 event_id" in rb.stderr, rb.stderr
    assert _write_face(vault) == face, "零写"

    # B③ 空串 / 纯空白 node_id 是「无法路由」，不是「属于别人」
    for nid in ("", "   "):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        row = _review_row()
        row["node_id"] = nid
        row["event_id"] = "quiz:空路由"
        _write_ledger(vault, row)
        face = _write_face(vault)
        rn = _run_writer(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rn.returncode != 0, f"node_id={nid!r} 无法路由，静默跳过等于漏算"
        assert "不可用" in rn.stderr, rn.stderr
        assert _write_face(vault) == face, "零写"
    # 验伪：合法的别节点行不得被这条门误伤
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    row = _review_row()
    row["node_id"] = "别的节点"
    row["event_id"] = "quiz:别节点"
    _write_ledger(vault, row)
    assert _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z")).returncode == 0

    # H① 输入 ts 用 fullmatch（末尾换行不得穿透）
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    LED.unlink(missing_ok=True)
    rt = _run_writer(vault, _payload(event_id="板A#q1", ts="2026-08-02T10:00:00Z\n"))
    assert rt.returncode != 0, "末尾换行能穿透 match()，必须用 fullmatch"
    assert not LED.exists() or not _ledger_lines(vault), "不得产出任何账本行"

    # H② NaN/Infinity：输入侧与读取侧都要与严格校验器同口径
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    LED.unlink(missing_ok=True)
    rn2 = _run_writer(vault, _payload(event_id="板A#q1", ts=TS1, exam_board=float("nan")))
    assert rn2.returncode != 0, "NaN 会被 json.dumps 原样写成字面量，而校验器拒收"
    assert not LED.exists() or "NaN" not in LED.read_text(encoding="utf-8"), "不得落库 NaN"

    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    _write_ledger(vault, _review_row())
    raw = LED.read_text(encoding="utf-8")
    LED.write_text(re.sub(r'"grade_norm":\s*[0-9.]+', '"grade_norm": NaN', raw), encoding="utf-8")
    face_nan = _write_face(vault)
    rn3 = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
    assert rn3.returncode != 0, "账本里的 NaN 必须被 strict loader 拒（默认 json.loads 会接受）"
    # 同上：点名拒因 + 零写，否则「恢复已落定」的续跑信号会让门抓不住变异
    assert ("NaN" in rn3.stderr) or ("非标准" in rn3.stderr) or ("解析" in rn3.stderr), rn3.stderr[:250]
    assert _write_face(vault) == face_nan, "零写（节点 + 账本）"
    assert _run_validator(vault).returncode != 0, "校验器同样拒（两侧同口径）"

    # H③ 同 ID 的合法 §6.3 历史行按 A4.5 幂等 no-op，不是拒
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    LED.unlink(missing_ok=True)
    assert _run_writer_settled(vault, _payload(event_id="板A#q1", ts=TS1)).returncode == 0
    rows = list(_ledger_lines(vault))
    rows[0]["payload"] = {"exam_board": "旧板", "note": "旧写点产物"}
    LED.write_text(json.dumps(rows[0], ensure_ascii=False) + "\n", encoding="utf-8")
    assert _run_validator(vault).returncode == 0, "该形态本身是 §6.3 允许的"
    sha = _sha(vault / NODE_REL)
    rh = _run_writer(vault, _payload(event_id="板A#q1", ts=TS1))
    assert rh.returncode == 0, f"同 ID 的合法历史行必须幂等 no-op（A4.5）: {rh.stderr[:250]}"
    assert _sha(vault / NODE_REL) == sha, "幂等必须零写"
    # 验伪：无 marker 却带着 review 扩展键的行仍必须拒（那是被伪装的复习）
    rows[0]["payload"] = {"vault_id": "canvas_vault_测试", "rating": 3, "review_time": TS1}
    LED.write_text(json.dumps(rows[0], ensure_ascii=False) + "\n", encoding="utf-8")
    assert _run_writer(vault, _payload(event_id="板A#q1", ts=TS1)).returncode != 0

    # H④ inline `calibration_log: []` 必须先规范成 block，否则产出非法 YAML 且不收敛
    (vault / NODE_REL).write_text(
        NODE_V0.replace("mastery_score:", "calibration_log: []\nmastery_score:", 1), encoding="utf-8"
    )
    LED.unlink(missing_ok=True)
    ri = _run_writer_settled(vault, _payload(event_id="板A#q1", ts=TS1))
    assert ri.returncode == 0, ri.stderr[:300]
    after = (vault / NODE_REL).read_text(encoding="utf-8")
    assert not ("calibration_log: []" in after and "  - event_id:" in after), f"产出了非法 YAML: {after[:400]}"
    ri2 = _run_writer(vault, _payload(event_id="板A#q1", ts=TS1))
    assert ri2.returncode == 0, f"同事件重跑必须收敛（此前永久卡在「已应用但缺校准」）: {ri2.stderr[:250]}"

    # M① 空行与 BOM 与校验器同口径拒收
    # ⚠️ BOM 用 \ufeff 转义写，不直接敲 —— 不可见字符会被工具链静默改掉
    #    (MEMORY: reference_invisible_chars_must_be_escaped_in_source)
    for desc, mk in (
        ("物理空行", lambda b: b.rstrip("\n") + "\n\n"),
        ("首行 BOM", lambda b: "\ufeff" + b),
    ):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        _write_ledger(vault, _review_row())
        LED.write_text(mk(LED.read_text(encoding="utf-8")), encoding="utf-8")
        # ⚠️ 必须用 settled + 点名拒因：`_run_writer` 的 rc!=0 里混着
        # 「恢复已落定，请重跑」这个**续跑信号**——它不是拒绝。实测禁掉空行/BOM
        # 门后，写点走的正是那条续跑分支、rc 同样非 0，于是单看 rc 的门**抓不住
        # 变异**（M68/M69 SURVIVED 的真因）。判据落在「最终写入没有」+ 拒因串上。
        face = _write_face(vault)
        rm = _run_writer_settled(vault, _payload(event_id="板B#q1", ts="2026-08-02T10:00:00Z"))
        assert rm.returncode != 0, f"[{desc}] 校验器拒，写点也必须拒"
        assert ("是空行" in rm.stderr) or ("BOM" in rm.stderr), f"[{desc}] 拒因须点名该形态: {rm.stderr[:200]}"
        assert _write_face(vault) == face, f"[{desc}] 零写（节点 + 账本）"
        assert _run_validator(vault).returncode != 0, f"[{desc}] 校验器确实拒（口径来源）"


# ── 门㊹ round-6 后续: H⑤ 序数判据 + M③ 账本可证序数 ──


def test_round6_ordinal_evidence(vault):
    """⛔ 这两条我一度登记为「不处置」，理由是「改判据整个维度风险高于收益」——
    **那是判断不是事实**，而且审查者给了具体修法。险些又犯「拿错误声明当不修
    理由」那个错。

    H⑤：序数把 `review_time <= W` 当成「后续事件已贡献 attempt」的证明。
        但 **degraded 落账写 attempt + 校准却不写 W**，两者会分道 ——
        重跑前一个事件时被误报「envelope 冲突」，而它是合法的历史重试。
        判据改用 **calibration 证据**（与 attempt/mastery 同一次原子写）。

    M③：历史行明明**带着合法 attempt_count**（validator rc=0），拒因却写死
        「无 attempt_count」——拒因本身是错的。改为先用账本自身能证明的序数回推。
    """
    LED = vault / "learning_events.jsonl"

    # ── H⑤：W 停在 E1，而 E2 已贡献 attempt + 校准 ⇒ 重跑 E1 必须幂等
    (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
    LED.unlink(missing_ok=True)
    for eid, ts in (("E1#q1", TS1), ("E2#q1", "2026-08-01T11:00:00Z")):
        assert _run_writer_settled(vault, _payload(event_id=eid, ts=ts)).returncode == 0
    node = (vault / NODE_REL).read_text(encoding="utf-8")
    rolled = re.sub(r"^fsrs_last_review:.*$", f'fsrs_last_review: "{TS1}"', node, count=1, flags=re.M)
    assert rolled != node, "预置必须真的把 W 回退（str 替换失败会静默返回原串）"
    (vault / NODE_REL).write_text(rolled, encoding="utf-8")
    assert _run_validator(vault).returncode == 0, "该状态本身合规（degraded 落账的产物形态）"
    sha = _sha(vault / NODE_REL)
    r = _run_writer(vault, _payload(event_id="E1#q1", ts=TS1))
    assert r.returncode == 0, f"E2 已贡献 attempt（校准里有它），重跑 E1 必须幂等: {r.stderr[:300]}"
    assert "幂等跳过" in r.stdout, r.stdout[:200]
    assert _sha(vault / NODE_REL) == sha, "幂等必须零写"

    # H⑤ 验伪：**真**的 envelope 冲突（改了分数）仍必须拒
    r2 = _run_writer(vault, _payload(event_id="E1#q1", ts=TS1, grade_norm=0.11))
    assert r2.returncode != 0, "评分事实真不一致时仍须拒 —— 否则这条修复把冲突门也放宽了"
    assert "envelope 冲突" in r2.stderr, r2.stderr[:200]

    # ── M③：历史行带合法 attempt_count ⇒ 账本可证，放行
    def _with_legacy(payload):
        (vault / NODE_REL).write_text(NODE_V0, encoding="utf-8")
        LED.unlink(missing_ok=True)
        for eid, ts in (("E1#q1", TS1), ("L#q1", "2026-08-01T11:00:00Z")):
            assert _run_writer_settled(vault, _payload(event_id=eid, ts=ts)).returncode == 0
        rows = list(_ledger_lines(vault))
        rows[1]["payload"] = payload
        LED.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")
        assert _run_validator(vault).returncode == 0, "改造后的账本本身必须合规"
        return _run_writer(vault, _payload(event_id="E1#q1", ts=TS1))

    rp = _with_legacy({"exam_board": "旧板", "note": "旧写点产物", "attempt_count": 2})
    assert rp.returncode == 0, f"历史行带合法 attempt_count ⇒ 账本可证，必须放行: {rp.stderr[:300]}"

    # M③ 验伪：历史行**不带** attempt_count ⇒ 不可证，停下且拒因指名行号与字段
    rn = _with_legacy({"exam_board": "旧板", "note": "旧写点产物"})
    assert rn.returncode != 0, "不可证时必须停下（不得伪造期望值）"
    assert "都没有可用的 attempt_count" in rn.stderr, rn.stderr[:300]
    assert "补上 attempt_count" in rn.stderr and re.search(r"第 \[\d+", rn.stderr), (
        f"拒因必须指名哪几行要补什么: {rn.stderr[:300]}"
    )
