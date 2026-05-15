#!/usr/bin/env python3
"""Pack Plan B (Story 2.4) adversarial review for ChatGPT independent audit."""
import os
from datetime import datetime

SRC = "/Users/Heishing/Desktop/canvas/canvas-learning-system"
WT = f"{SRC}/.claude/worktrees/feature-obsidian-hybrid-dev"
GC = f"{SRC}/backend/.venv/lib/python3.14/site-packages/graphiti_core"

FILES = [
    ("A. Plan B Plugin",
     SRC, [
        "frontend/obsidian-plugin/src/callout.ts",
        "frontend/obsidian-plugin/src/callout-sync.ts",
        "frontend/obsidian-plugin/src/main.ts",
    ]),
    ("B. Plan B Backend",
     SRC, [
        "backend/app/api/v1/endpoints/tips.py",
        "backend/app/services/memory_service.py",
        "backend/app/services/question_generator.py",
        "backend/app/core/memory_format.py",
        "backend/app/graphiti/entity_types.py",
        "backend/app/graphiti/group_id_compat.py",
        "backend/app/services/episode_worker.py",
    ]),
    ("C. Backend Consumers",
     SRC, [
        "backend/app/services/context_enrichment_service.py",
        "backend/app/services/learning_context_service.py",
    ]),
    ("D. Graphiti Core Constraints",
     GC, [
        "prompts/dedupe_nodes.py",
        "models/nodes/node_db_queries.py",
        "nodes.py",
        "graphiti.py",
    ]),
    ("E. Story 2.4 Spec (Plan A)",
     WT, [
        "_bmad-output/implementation-artifacts/epic-2/2-4-callout-annotation-tips.md",
    ]),
    ("F. History - Claude FAIL + ChatGPT review",
     WT, [
        "_bmad-output/验收单/批注回复/2026-05-13-设计可行性评估-用户核心闭环.md",
        "_bmad-output/research/2026-05-13-chatgpt-dr-response-core-loop-second-opinion.md",
    ]),
    ("G. Project Context",
     WT, [
        "CLAUDE.md",
        "_bmad-output/.claude/CLAUDE.md",
    ]),
]

OUT = f"{WT}/.gdr/research-pack-plan-b-adversarial-review.xml"

parts = []
parts.append('<?xml version="1.0" encoding="UTF-8"?>')
parts.append(f'<research_pack topic="plan_b_adversarial_review" generated="{datetime.now().isoformat()}">')

all_files = []
parts.append('  <directory_structure>')
for section, root, rels in FILES:
    parts.append(f'    <!-- {section} -->')
    for rel in rels:
        if root == SRC:
            display = rel
        elif root == GC:
            display = f"graphiti_core/{rel}"
        else:
            display = f"worktree/{rel}"
        parts.append(f'    {display}')
        all_files.append((section, root, rel, display))
parts.append('  </directory_structure>')

parts.append('  <files>')
total_chars = 0
missing = []
secs = {}

for section, root, rel, display in all_files:
    abs_path = os.path.join(root, rel)
    if not os.path.exists(abs_path):
        missing.append(abs_path)
        parts.append(f'    <file path="{display}" status="MISSING"><![CDATA[NOT FOUND]]></file>')
        continue
    with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    total_chars += len(content)
    secs.setdefault(section, {"count": 0, "chars": 0})
    secs[section]["count"] += 1
    secs[section]["chars"] += len(content)
    content = content.replace(']]>', ']]]]><![CDATA[>')
    parts.append(f'    <file path="{display}" section="{section.split(".")[0]}">')
    parts.append('<![CDATA[')
    parts.append(content)
    parts.append(']]>')
    parts.append('    </file>')

parts.append('  </files>')

# 4 Agent inline summary + ChatGPT instruction — read from external files
AGENT_SUMMARY_PATH = f"{WT}/.gdr/plan-b-agent-summary.md"
INSTRUCTION_PATH = f"{WT}/.gdr/plan-b-chatgpt-instruction.md"

for label, path, tag in [
    ("Agent Research Summary", AGENT_SUMMARY_PATH, "agent_research_summary"),
    ("ChatGPT Instruction", INSTRUCTION_PATH, "instruction"),
]:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace(']]>', ']]]]><![CDATA[>')
        parts.append(f'  <{tag}>')
        parts.append('<![CDATA[')
        parts.append(content)
        parts.append(']]>')
        parts.append(f'  </{tag}>')
        print(f"Embedded {label}: {len(content)} chars")
    else:
        print(f"WARN: {label} file missing at {path}")

parts.append('  <pack_metadata>')
parts.append(f'    <total_files>{len(all_files) - len(missing)}</total_files>')
parts.append(f'    <total_chars>{total_chars}</total_chars>')
parts.append(f'    <approx_tokens>{total_chars // 4}</approx_tokens>')
parts.append('  </pack_metadata>')
parts.append('</research_pack>')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(parts))

print(f"\n{'='*60}")
print(f"Output: {OUT}")
print(f"Files: {len(all_files) - len(missing)} / Chars: {total_chars:,} / Tokens: {total_chars//4:,}")
print(f"Size: {os.path.getsize(OUT):,} bytes")
print(f"{'='*60}")
for sec, info in secs.items():
    print(f"  {sec}: {info['count']} files / ~{info['chars']//4:,} tok")
if missing:
    print(f"\nMissing ({len(missing)}):")
    for p in missing: print(f"  - {p}")
