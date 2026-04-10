---
doc_type: dashboard
updated: 2026-04-10
---

# Plan Dashboard

> 全局状态一览。Dataview 自动聚合 `_plans/`、`_verification/`、`_feedback/` 数据。

## Plan 状态汇总

```dataview
TABLE title AS "标题", status AS "状态", prd_sections AS "PRD §", current_step AS "当前步骤"
FROM "_plans"
WHERE doc_type = "plan"
SORT plan_id ASC
```

## 待验收

```dataview
TABLE plan_id AS "关联 Plan", status AS "状态", date AS "日期"
FROM "_verification"
WHERE doc_type = "verification" AND status = "pending"
SORT date DESC
```

## 未关闭反馈

```dataview
TABLE source_plan AS "来源 Plan", severity AS "严重程度", status AS "状态"
FROM "_feedback"
WHERE doc_type = "feedback" AND status = "open"
SORT severity ASC
```

## PRD § 覆盖率

```dataview
TABLE prd_title AS "标题", length(related_frs) AS "FRs", status AS "状态"
FROM "_prd-register"
WHERE doc_type = "prd-section"
SORT file.name ASC
```
