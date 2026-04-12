# UAT Queue

Stories ready for user acceptance testing.

```dataview
TABLE story_id, priority, status, estimate_hours
FROM "stories" OR "_bmad-output/implementation-artifacts"
WHERE doc_type = "story" AND status = "ready-for-uat"
SORT priority ASC, story_id ASC
```
