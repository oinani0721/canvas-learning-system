# Bug → Story Reverse Index

Map BugIDs to their originating Stories.

```dataview
TABLE story_id, trace.bugs as "Bug IDs", trace.decisions as "Decision IDs", status
FROM "stories" OR "_bmad-output/implementation-artifacts"
WHERE doc_type = "story" AND length(trace.bugs) > 0
SORT story_id ASC
```
