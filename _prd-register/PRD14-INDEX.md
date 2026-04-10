---
doc_type: prd-index
prd_version: v5
total_sections: 14
---

# PRD v5 Section 索引

> **PRD**: `14-scheme-a-implementation-prd.md` (v5, 7594 行)
> **Status**: 只读锚定文档，Claude 不可编辑

## S 覆盖率

```dataview
TABLE prd_title AS "标题", prd_lines AS "行号", length(related_frs) AS "FRs", status AS "状态"
FROM "_prd-register"
WHERE doc_type = "prd-section"
SORT file.name ASC
```

## 状态汇总

```dataview
TABLE length(rows) AS "数量"
FROM "_prd-register"
WHERE doc_type = "prd-section"
GROUP BY status
```
