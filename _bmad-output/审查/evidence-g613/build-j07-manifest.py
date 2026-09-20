#!/usr/bin/env python3
"""CARD-G6-13 J07 manifest 构建器 (未授权窗口路径 · E2/partial/reconstructed)。

运行: python3 build-j07-manifest.py <J07 目录> <lane HEAD 40位> <started_at iso> <finished_at iso>
产物: 覆盖写 <J07>/manifest.json (artifacts = 目录内除 manifest.json 外全部文件, 自动算 sha256/bytes)。
所有文本不含绝对路径 (脱敏门: 七类前缀 /Users/ /private/ /home/ /opt/homebrew/ /tmp/ /var/ /Volumes/ == 0)。
"""

import hashlib
import json
import sys
from pathlib import Path

J07 = Path(sys.argv[1])
LANE_SHA = sys.argv[2]
STARTED = sys.argv[3]
FINISHED = sys.argv[4]

artifacts = []
for f in sorted(J07.iterdir()):
    if not f.is_file() or f.name == "manifest.json":
        continue
    data = f.read_bytes()
    # 收编前逐件自证 (Codex r1 MEDIUM-3 / r2 MEDIUM-2 处置): 不许空件、不许残留绝对路径前缀 ——
    # 否则 redacted=true 的声明会变成"自洽但不实"的元数据。检查面按前缀清单做, 不假装能拦正文。
    if len(data) == 0:
        raise SystemExit(f"artifact 为空, 拒绝收编: {f.name}")
    for prefix in (b"/Users/", b"/private/", b"/home/", b"/opt/homebrew/", b"/tmp/", b"/var/", b"/Volumes/"):
        if prefix in data:
            raise SystemExit(f"artifact 含绝对路径前缀 {prefix.decode()}, 拒绝收编 (先脱敏): {f.name}")
    artifacts.append(
        {
            "path": f.name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "redacted": True,
            "redaction_note": "已脱敏: 机械核查通过 (无 /Users/、/private/、/home/、/opt/homebrew/、/tmp/、/var/、/Volumes/ 七类前缀); 收录件经人工检视无私人笔记正文; md-final.md 为全量脱敏版 (路径类值已替换占位)。",
        }
    )

manifest = {
    "schema_version": "1.0.0",
    "journey_id": "J07",
    "journey_title": "J07 次日复习旅程（开发门 · 未授权窗口：用户步骤 not_run + fixture 半边机器证据）",
    "rc": "dev-b15-p5",
    "provenance": {
        "mode": "reconstructed",
        "reconstructed_from": "车道 card-p5-review 本会话执行期实录 (真实命令当场产出; 收集于 _bmad-output/审查/evidence-g613/, 存档于同批 commit A)。未授权窗口 ⇒ 用户旅程 (c) 整段 SKIP。『reconstructed』按卡文口径使用: 非全部字段有执行期证据。",
        "unproven_fields": [
            "旅程 (c): 用户 UI 步骤 (Day0 作答 / Day1 四桶巡查 / 回炉 / snooze / 完成 / 深链) 全部未执行 (not_run); live-before.txt / live-after-check.txt 不存在。",
            "candidate.sha: 未开窗 ⇒ 无 8011 执行期代码树 HEAD 可公布; 本值钉为**执行期起手时** (00:54 PDT) 本车道树 checkout `f0cacff6` (P5-B 末 commit, 40 位)。与 8011 服务树 / 最终候选树的关系未证。⚠️ SHA 演变如实登记: A/B/C 三版 manifest 重建时曾一度取 build 时刻 HEAD (00553b4e / 28bd74a4 / 1c355c3a —— 其中 1c355c3a 是外部 session 的 docs-only commit), 终态已钉回执行期 checkout; f0cacff6..a3103a49 之间 backend/frontend/scripts 逐文件零 diff (见 execution.commands 佐证条)。",
            "execution.operator: 未记录会话指纹 (无稳定标识)。",
            "environment: host_os 具体版本与 backend/.env 取值未记录。",
            "slo.manifest_revision: 本树无 R-SLO 锁版件 ⇒ null (S9 亦据此把等级钳在 E2)。",
            "signoff: 未授权窗口 ⇒ pending (S10 亦禁止回填件 approved)。",
        ],
        "note": "fixture 半边 (五面契约 ×4 / 三面对账 / 校验器 / 点名套件 / 目录级) 为本卡当次现场执行, 不是从旧归档回填。",
    },
    "candidate": {
        "sha": LANE_SHA,
        "branch": "card/p5-review",
        "dirty": False,
        "worktree": ".claude/worktrees/card-p5-review",
    },
    "environment": {
        "host_os": "darwin (macOS, Apple Silicon; 具体版本未记录)",
        "runtimes": {"python": "3.14.4 (backend/.venv)"},
        "models": [],
        "index_sha": None,
        "index_sha_null_reason": "复习链 (picker / review_overview / runner) 不经检索索引; 无 index 参与。",
        "services": {"8011": "未使用 (未授权窗口: 车道只在 tmp 副本上跑, 不 import app.main、不 POST /overview/*)"},
    },
    "execution": {
        "started_at": STARTED,
        "finished_at": FINISHED,
        "operator": "车道 card-p5-review (AI 执行; 未记录会话指纹)",
        "commands": [
            {
                "cmd": "backend/.venv/bin/python backend/scripts/validate_release_manifest.py --all",
                "cwd": "<tree>",
                "exit_code": 0,
                "note": "先红对照: 加 J07 前 --all 只见 J08 一份。",
            },
            {"cmd": "cd backend && .venv/bin/python scripts/g68_five_view_contract.py --now <ts> --json <EV>/g68-pre.json", "cwd": "<tree>/backend", "exit_code": 0},
            {
                "cmd": "cd backend && for NOW in 2026-09-19T03:00:00Z 2026-09-19T13:00:00Z; for TZ in Asia/Shanghai America/Los_Angeles; .venv/bin/python scripts/g68_five_view_contract.py --now $NOW --tz $TZ --json <EV>/g68-...json",
                "cwd": "<tree>/backend",
                "exit_code": 0,
                "note": "四档 (2 时刻 × 2 时区); 03Z×LA 档 declared=6 = skill_inbox 固定 +08:00 已登记分歧按设计现形, undeclared=0 全档。",
            },
            {
                "cmd": "cd backend && .venv/bin/python ../scripts/daily_review_pick.py --vault <tmp>/vaults/canvas-vault --state <tmp>/backups/daily-review.canvas-vault.state.json --now <now> --write",
                "cwd": "<tree>/backend",
                "exit_code": 0,
                "note": "写只落 tmp 副本 outputs/; live 只读复制。",
            },
            {
                "cmd": "cd backend && (python - <<'PY' ... runner.BACKUPS=<tmp>/backups; reload_settings(VAULTS_ROOT=<tmp>/vaults); review_overview._collect(); 时钟 pin ... PY)",
                "cwd": "<tree>/backend",
                "exit_code": 0,
                "note": "API 面: g68 同款注入; 不 import app.main。",
            },
            {"cmd": "python3 <EV>/three-face-compare.py <tmp>/.../今日复习.json <EV>/three-face-api.json <tmp>/.../今日复习.md", "cwd": "<tree>", "exit_code": 0},
            {"cmd": "cd backend && .venv/bin/pytest -q -rfE -p no:cacheprovider tests/regression/test_g68_five_view_contract.py", "cwd": "<tree>/backend", "exit_code": 0, "note": "34 passed (参数化展开; 卡文写 24 = def test_ 数)。"},
            {"cmd": "cd backend && .venv/bin/pytest tests/regression -q -p no:cacheprovider -rfE", "cwd": "<tree>/backend", "exit_code": 0},
            {"cmd": "cd backend && .venv/bin/pytest -q -rfE -p no:cacheprovider <9 点名文件>", "cwd": "<tree>/backend", "exit_code": 0},
            {
                "cmd": "git --no-pager diff --name-only --no-color f0cacff6 a3103a49 -- backend/ frontend/ scripts/",
                "cwd": "<tree>",
                "exit_code": 0,
                "note": "零输出 = 执行期 checkout 与终态之间代码树逐文件零 diff (candidate.sha 绑定佐证)。",
            },
            {
                "cmd": "cd backend && .venv/bin/pytest tests/unit -q -p no:cacheprovider -rfE",
                "cwd": "<tree>/backend",
                "exit_code": 1,
                "expected_failure": True,
                "note": "32 failed = 既有红基线 (BASE 33 − 1 条已知 flaky 本轮转绿); 非本卡引入 (diff 只 <)。",
            },
        ],
        "skips_or_mocks": {
            "declared": True,
            "items": [
                {
                    "what": "用户 UI 全步骤 (Day0 作答 / Day1 四桶 / 回炉 / snooze / 完成 / 深链)",
                    "why": "未授权 (口令「G6-13 授权 J07 窗口」未给出) + 主 session 尚未完成 P5-A/P5-B 合入部署与 launchd 一档核的前置; 按卡文 (c) 整段 SKIP, 用户步骤全部 not_run。",
                },
                {
                    "what": "10 分钟回炉的实际计时与 FSRS 步长核对",
                    "why": "同上未执行; 本卡只旁证 learning_queue 桶机制。",
                },
                {
                    "what": "live-before / live-after-check 原库 hash 门",
                    "why": "无用户作答 ⇒ 无关节点集合可对照; 未执行 (not_run), 不代跑。",
                },
            ],
        },
    },
    "assertions": [
        {
            "id": "J07-1",
            "statement": "次日总览四桶展示（产品口径五桶: relearning 并入 learning_queue「重学中」）",
            "method": "未执行 —— 需用户经浏览器打开 /overview/page 与 /app 查看",
            "result": "not_run",
            "note": "旁证 (非本断言的通过依据): fixture 侧五桶机制产出 new=5 / learning_queue=1 (见 three-face-api.json 的 bucket_counts)。",
        },
        {
            "id": "J07-2",
            "statement": "答错回炉 → 该节点落 learning_queue「重学中」（10 分钟步长）",
            "method": "未执行 —— 需用户对错题节点再作答触发 relearning",
            "result": "not_run",
            "note": "旁证: live 副本中已逾期节点 csm-tutoring-unit-credit 即在 learning_queue 桶 (见 three-face-compare.txt)。步长未验 (fsrs_bridge 零写者)。",
        },
        {"id": "J07-3", "statement": "snooze 让位（推迟到今晚/明天 → 该板在排序中让位）", "method": "未执行 —— 需用户经页面点选 (车道禁 POST)", "result": "not_run"},
        {"id": "J07-4", "statement": "完成让位与打勾（今天做完了 → 退后并标记）", "method": "未执行 —— 需用户经页面点选 (车道禁 POST)", "result": "not_run"},
        {"id": "J07-5", "statement": "深链精确开板/开节点 (obsidian://)", "method": "未执行 —— 需用户点击深链", "result": "not_run"},
        {
            "id": "J07-6",
            "statement": "三面排序一致: picker JSON / API _collect / Markdown 的 (板,节点,桶) 集合与 ranked 板序一致",
            "method": "tmp 副本上同刻重算三面, 逐项比对",
            "result": "pass",
            "evidence": "three-face-compare.txt",
            "note": "范围: 同一份数据、同一时刻的『副本三面』 (集合 6=6=6; ranked picker 3 前缀 = api/md 4 全长)。不证 live 8011 进程内存态; picker 与 API 投影同源耦合见 known_limitations。",
        },
        {
            "id": "J07-7",
            "statement": "G6-8 五面契约 0 未登记分歧（2 时刻 × 2 时区四档 verdict=PASS）",
            "method": "g68_five_view_contract.py 四档 + 契约门 34 passed",
            "result": "pass",
            "evidence": "g68-2026-09-19T03:00:00Z-Asia_Shanghai.json",
            "note": "四份 json 全为 artifact。03Z×LA 档 declared=6 (skill_inbox 固定 +08:00 的已登记分歧, 谓词通过); P5-B 按默认未改 inbox tz —— T3-B 待裁现状如实抄。",
        },
        {
            "id": "J07-8",
            "statement": "原库 hash 门: 仅被作答节点的 frontmatter 变化, 其余全 OK",
            "method": "未执行 —— 需用户作答后才有关键集合可核 (live-before/after 不产生)",
            "result": "not_run",
        },
    ],
    "rollback": {
        "performed": False,
        "result": "not_applicable",
        "reason": "本卡未发起任何 live 写入 (车道只 GET/cp/rsync/shasum); 产品路径的 snooze/done/undo 未执行, 无状态可回滚。",
    },
    "artifacts": artifacts,
    "slo": {"manifest_revision": None, "measurements": []},
    "signoff": {
        "status": "pending",
        "note": "未授权窗口 ⇒ E2/partial; 签字位待 J07 窗口执行后由用户签署 (S10: 回填件不得 approved)。",
    },
    "evidence_level": "E2",
    "result": "partial",
    "known_limitations": [
        "未授权/未跨日: 用户 UI 步骤全部 not_run; 本卡只证明机器半边 (五面契约 + tmp 副本三面对账 + 校验器 + 套件), 旅程本身未在真实 UI 上走过。",
        "即授权, 也只证明一块 vault / 4 板 / 6 节点的一次跨日; live 副本 14 节点里仅 1 个 fsrs_due ⇒ 集合小; 不证明多 vault / 多板并发或 14 天 dogfood (G8-6)。",
        "candidate.sha = 本车道树 HEAD, 非 8011 执行期服务树, 也非最终候选树 (RC 复跑归 R-J07)。",
        "三面对账在 tmp 副本上重算; 且 API 面读的就是 picker 输出 (outputs/今日复习.json) 再自行派生 ⇒ 两面同源, 对账无法排除共享数据缺陷; 独立渲染面只有 Markdown 链。不证 live 8011 进程当时内存里的投影与副本一致 (进程缓存/刷新时序未覆盖)。",
        "「10 分钟回炉」只验到『逾期节点落在 learning_queue (重学中)』的桶机制旁证, 未验 FSRS 步长恰为 10 分钟 (fsrs_bridge.py 零写者, 本卡不读其运行期配置)。",
        "深链 obsidian:// 的降级文案未测 (未开窗)。",
        "E3+ 所需 SLO revision 本树不存在 ⇒ evidence_level 停在 E2 (S9/S13); 这不代表旅程质量低于 E3。",
        "g68 契约的 boards=6 是 fixture 输入面, 与 live 库的 4 板/6 节点是两回事。",
    ],
    "notes": "candidate.sha 钉执行期 checkout f0cacff6; 其后 A/B/C 与外部 docs-only commit 1c355c3a 仅动 J07 证据面与 _bmad-output ⇒ `git --no-pager diff --name-only f0cacff6 a3103a49 -- backend/ frontend/ scripts/` 为空 (命令见 execution.commands)。rc='dev-b15-p5' 为本卡自命名开发门 rc (非 RC; 形态同 example-backfill-d5)。集成期主 session 如需并入 R-RC 冻结 rc, 只改目录名 + rc 字段 (纯文档)。candidate.dirty 口径: `git status --porcelain -- . ':(exclude)docs/release-evidence' ':(exclude)_bmad-output'` 为空 ⇒ false。候选双树现象: 本仓存在主仓 live tree 与车道树两份 canvas-vault, 本卡读 live 只经 cp/rsync。P5-B 按默认未改 inbox_preview.py:430 的 +08:00 ⇒ skill_inbox 已登记分歧仍在 (待 T3-B 用户裁)。",
}

out = J07 / "manifest.json"
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out} ({len(artifacts)} artifacts)")
