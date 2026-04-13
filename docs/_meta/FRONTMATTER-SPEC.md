# Frontmatter Field Specification

All Story, Epic, and PRD files in this vault use YAML frontmatter for structured metadata.

## Story Files

```yaml
---
doc_type: story
story_id: "30.23"
epic_id: "EPIC-30"
prd_id: "PRD14"          # optional
status: ready-for-dev    # BMAD status enum
priority: P1
estimate_hours: 4
depends_on: []           # Story IDs this story depends on
blocks: []               # Story IDs this story blocks
trace:
  decisions: []          # DECN-XXXXXXXX IDs
  bugs: []               # BUG-XXXXXXXX IDs
---
```

## Epic Files

```yaml
---
doc_type: epic
epic_id: "EPIC-30"
prd_id: "PRD14"
child_stories: []        # auto-filled by sync_links.py
status: in-progress
---
```

## PRD Section Files (_prd-register/)

```yaml
---
doc_type: prd-section
prd_id: PRD14
section: "S02"
section_title: "..."
source_lines: "L905-2739"
links_frs: []
links_skills: []
status: ready-for-phase-1
---
```

## Code Path Tracking

Code paths are tracked via BMAD native `### File List` section in Story files,
NOT via frontmatter `trace.code_paths` field (removed per L997 调研).
External index: `docs/_meta/indices/story-file-map.yaml`.
