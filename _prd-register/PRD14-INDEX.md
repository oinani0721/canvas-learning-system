# PRD14 Section Index

> **PRD v5 根文档 read-only** (pretool-guard.js 硬挡)
> 影子层 `_prd-register/` 允许 Claude 和用户批注，零改动原文。

## Section Overview

```dataview
TABLE section_title, status, length(links_frs) as "FR Count", length(file.inlinks) as "References"
FROM "_prd-register"
WHERE doc_type = "prd-section"
SORT section ASC
```

## Dual-Source Reference

| Source | Role | Path |
|---|---|---|
| **PRD v5** (真相源) | 人类可读完整产品愿景，永远 read-only | `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` |
| **BMAD PRD** (工作流输入) | 供 BMAD V6 CE/CA/IR/correct-course 消费 | `_bmad-output/planning-artifacts/prd.md` (Phase 0.5 生成) |

## Decision Lock Status

See [[PRD14-decisions]] for D1-D14 lock status.
