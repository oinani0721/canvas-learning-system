# Sprint Progress

Story completion by Epic.

```dataview
TABLE epic_id, status, length(file.inlinks) as "References"
FROM "stories" OR "_bmad-output/implementation-artifacts"
WHERE doc_type = "story"
GROUP BY epic_id
SORT epic_id ASC
```
