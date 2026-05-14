#!/usr/bin/env python3
"""Pack research files for ChatGPT Deep Research — User Core Loop Feasibility."""
import os
import sys
from datetime import datetime

WORKTREE = "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev"
CANVAS = "/Users/Heishing/Desktop/canvas/canvas-learning-system"
EXTERNAL_PRD = "/Users/Heishing/Desktop/spring course 2026/CS 61B"
VENV_GRAPHITI = f"{CANVAS}/backend/.venv/lib/python3.14/site-packages/graphiti_core"

FILES = [
    ("A. 用户批注 & ChatGPT 任务",
     WORKTREE, [
        "_bmad-output/验收单/批注回复/2026-05-13-设计可行性评估-用户核心闭环.md",
        "_bmad-output/research/2026-05-13-chatgpt-对抗审查-核心闭环可行性.md",
        "_bmad-output/research/round-23-chatgpt-dr-result-and-synthesis-2026-05-08.md",
    ]),
    ("B. Sprint 状态 & Epic 规划",
     WORKTREE, [
        "_bmad-output/implementation-artifacts/sprint-status.yaml",
        "_bmad-output/planning-artifacts/epics.md",
    ]),
    ("C. Story spec (Epic 2/4/5/7 全部相关)",
     WORKTREE, [
        "_bmad-output/implementation-artifacts/epic-2/2-4-callout-annotation-tips.md",
        "_bmad-output/implementation-artifacts/epic-4/4-1-exam-isolation-anti-nesting.md",
        "_bmad-output/implementation-artifacts/epic-4/4-2-weak-node-selection.md",
        "_bmad-output/implementation-artifacts/epic-4/4-3-triple-fusion-question-gen.md",
        "_bmad-output/implementation-artifacts/epic-4/4-4-exam-mode-selection.md",
        "_bmad-output/implementation-artifacts/epic-4/4-5-md-editor-answer-submit.md",
        "_bmad-output/implementation-artifacts/epic-4/4-6-silent-scoring-autoscore.md",
        "_bmad-output/implementation-artifacts/epic-4/4-7-progressive-hints-skip.md",
        "_bmad-output/implementation-artifacts/epic-4/4-8-bookmark-concept-extraction.md",
        "_bmad-output/implementation-artifacts/epic-4/4-9-calibration-vote-data-sync.md",
        "_bmad-output/implementation-artifacts/epic-4/4-10-exam-record-persistence.md",
        "_bmad-output/implementation-artifacts/epic-4/4-11-irt-difficulty-callout-exam.md",
        "_bmad-output/implementation-artifacts/epic-5/5-1-bkt-mastery-update.md",
        "_bmad-output/implementation-artifacts/epic-5/5-2-fsrs-review-interval.md",
        "_bmad-output/implementation-artifacts/epic-5/5-3-five-signal-fusion.md",
        "_bmad-output/implementation-artifacts/epic-5/5-4-scoring-chain-integrity.md",
        "_bmad-output/implementation-artifacts/epic-5/5-5-error-classification-dual-write.md",
        "_bmad-output/implementation-artifacts/epic-5/5-6-calibration-data-voting.md",
        "_bmad-output/implementation-artifacts/epic-5/5-7-three-layer-memory-retrieval.md",
        "_bmad-output/implementation-artifacts/epic-5/5-8-async-write-hot-warm-cold.md",
        "_bmad-output/implementation-artifacts/epic-7/7-3-misconception-context-injection.md",
    ]),
    ("D. 致命代码 — 后端 services + lib + 前端 plugin",
     CANVAS, [
        "backend/lib/agentic_rag/clients/lancedb_client.py",
        "backend/app/services/memory_service.py",
        "backend/app/services/question_generator.py",
        "backend/app/services/mastery_engine.py",
        "backend/app/services/wikilink_graph_service.py",
        "frontend/obsidian-plugin/src/main.ts",
    ]),
    ("E. 锚定 PRD (D14/D16 决策源)",
     EXTERNAL_PRD, [
        "14-scheme-a-implementation-prd.md",
    ]),
    ("F. 项目脉络 — CLAUDE.md / 决策 / 已知坑",
     WORKTREE, [
        "CLAUDE.md",
        "_bmad-output/.claude/CLAUDE.md",
        "CURRENT_TASK.md",
        "_decisions/decision-log.md",
        "docs/known-gotchas.md",
    ]),
    ("G. 历史调研 — Round 15/21 决策依据",
     WORKTREE, [
        "_bmad-output/research/round-21-canvas-five-core-deeptutor-integration-2026-05-06.md",
        "_bmad-output/research/round-15-bkt-fsrs-multihop-tauri-prd-deep-explore-2026-05-05.md",
    ]),
    ("H. 后端补充 — endpoint / schema / mcp tools",
     CANVAS, [
        "backend/app/api/v1/endpoints/tips.py",
        "backend/app/graphiti/entity_types.py",
        "backend/app/mcp/tools/exam_tools.py",
    ]),
    ("I. Graphiti core 外部包 — 维度 C 内容层失效证据",
     VENV_GRAPHITI, [
        "prompts/extract_nodes.py",
        "prompts/dedupe_nodes.py",
        "edges.py",
    ]),
]

OUTPUT = f"{WORKTREE}/.gdr/research-pack-core-loop-feasibility.xml"

parts = []
parts.append('<?xml version="1.0" encoding="UTF-8"?>')
parts.append(f'<research_pack topic="user_core_loop_feasibility" generated="{datetime.now().isoformat()}">')

parts.append('  <directory_structure>')
all_files_list = []
for section, root, rels in FILES:
    parts.append(f'    <!-- {section} -->')
    for rel in rels:
        display = f"{os.path.basename(root.rstrip('/'))}/{rel}" if root != WORKTREE else rel
        if root == VENV_GRAPHITI:
            display = f"graphiti_core/{rel}"
        if root == EXTERNAL_PRD:
            display = f"external/spring-course-2026-cs61b/{rel}"
        parts.append(f'    {display}')
        all_files_list.append((section, root, rel, display))
parts.append('  </directory_structure>')

parts.append('  <files>')
total_chars = 0
missing = []
sections_summary = {}

for section, root, rel, display in all_files_list:
    abs_path = os.path.join(root, rel)
    if not os.path.exists(abs_path):
        missing.append((section, abs_path))
        parts.append(f'    <file path="{display}" status="MISSING"><![CDATA[FILE NOT FOUND: {abs_path}]]></file>')
        continue
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        missing.append((section, f"{abs_path} (read error: {e})"))
        continue
    chars = len(content)
    total_chars += chars
    sections_summary.setdefault(section, {"count": 0, "chars": 0})
    sections_summary[section]["count"] += 1
    sections_summary[section]["chars"] += chars
    # CDATA boundary sanitization
    content = content.replace(']]>', ']]]]><![CDATA[>')
    parts.append(f'    <file path="{display}" section="{section.split(".")[0]}">')
    parts.append('<![CDATA[')
    parts.append(content)
    parts.append(']]>')
    parts.append('    </file>')

parts.append('  </files>')

# Footer summary
parts.append('  <pack_metadata>')
parts.append(f'    <total_files>{len(all_files_list) - len(missing)}</total_files>')
parts.append(f'    <total_chars>{total_chars}</total_chars>')
parts.append(f'    <approx_tokens>{total_chars // 4}</approx_tokens>')
parts.append(f'    <missing_count>{len(missing)}</missing_count>')
parts.append('    <section_breakdown>')
for sec, info in sections_summary.items():
    parts.append(f'      {sec}: {info["count"]} files, ~{info["chars"]//4} tokens')
parts.append('    </section_breakdown>')
parts.append('  </pack_metadata>')

parts.append('</research_pack>')

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(parts))

# Console report
print(f"=" * 60)
print(f"Pack output: {OUTPUT}")
print(f"Total files included: {len(all_files_list) - len(missing)}")
print(f"Total chars: {total_chars:,}")
print(f"Approx tokens: {total_chars // 4:,}")
print(f"File size: {os.path.getsize(OUTPUT):,} bytes")
print(f"=" * 60)
print("\nSection breakdown:")
for sec, info in sections_summary.items():
    print(f"  {sec}: {info['count']} files, ~{info['chars']//4:,} tokens")
if missing:
    print(f"\nMissing ({len(missing)}):")
    for sec, p in missing:
        print(f"  [{sec.split('.')[0]}] {p}")
